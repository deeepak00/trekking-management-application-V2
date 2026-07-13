import csv
import io
import time
import uuid
import queue
import calendar
import threading
from datetime import datetime, date, timedelta
from flask import current_app
from extensions import db, mail
from models.models import User, Trek, Booking, Notification
from flask_mail import Message
from config import Config

# Thread-safe queue for background tasks
task_queue = queue.Queue()

# Thread-safe dictionary for task statuses
# Format: { task_id: { "status": "PENDING" | "PROCESSING" | "SUCCESS" | "FAILURE", "result": str } }
task_statuses = {}

# Track last runs to prevent duplicate execution of daily and monthly tasks
last_runs = {
    'daily': None,   # Stores date string, e.g., '2026-07-03'
    'monthly': None  # Stores month string, e.g., '2026-07'
}

def log_email_fallback(subject, recipients, body=None, html=None, attachment_name=None):
    """
    Logs emails to a local file in case Flask-Mail is not configured
    or fails to connect to an SMTP server.
    """
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, 'sent_emails.log')
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"========================================\n"
    log_entry += f"Timestamp: {timestamp}\n"
    log_entry += f"Subject: {subject}\n"
    log_entry += f"Recipients: {', '.join(recipients) if isinstance(recipients, list) else recipients}\n"
    if attachment_name:
        log_entry += f"Attachment: {attachment_name}\n"
    if body:
        log_entry += f"Body:\n{body}\n"
    if html:
        log_entry += f"HTML Body:\n{html}\n"
    log_entry += "========================================\n\n"
    
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        print(f"[TMA Jobs] Logged email fallback to {log_path}")
    except Exception as e:
        print(f"[TMA Jobs] Failed to write fallback email log: {e}")


def run_daily_reminders():
    """
    Emails every trekker whose trek starts in 1, 2, or 3 days.
    Also creates an in-app notification.
    """
    today = date.today()
    total_sent = 0

    for days_ahead in [1, 2, 3]:
        target = today + timedelta(days=days_ahead)
        bookings = (
            Booking.query
            .join(Trek, Booking.trek_id == Trek.id)
            .filter(Trek.start_date == target, Booking.status == 'Booked')
            .all()
        )

        for booking in bookings:
            user = User.query.get(booking.user_id)
            trek = Trek.query.get(booking.trek_id)
            if not user or not trek:
                continue

            label = f'{days_ahead} day{"s" if days_ahead > 1 else ""}'
            guide_name = trek.assigned_staff.get_name() if trek.assigned_staff else 'TBD'

            # Create in-app notification
            db.session.add(Notification(
                user_id=booking.user_id,
                title=f'⛰️ Trek starts in {label}!',
                message=(
                    f'"{trek.name}" at {trek.location} starts on {trek.start_date}. '
                    f'Meeting point: {trek.meeting_point or "TBD"}. Guide: {guide_name}.'
                ),
                type='warning',
            ))

            # Email body
            html_body = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
              <div style="background:linear-gradient(135deg,#2c7a4b,#1a4f30);padding:28px;border-radius:12px 12px 0 0">
                <h1 style="color:#fff;margin:0;font-size:22px">⛰️ Trek Reminder — {label} to go!</h1>
              </div>
              <div style="background:#fff;padding:28px;border:1px solid #e0e0e0;border-radius:0 0 12px 12px">
                <p>Hi <strong>{user.get_name()}</strong>,</p>
                <p>Your upcoming trek is just <strong>{label} away</strong>. Here are your details:</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0">
                  <tr><td style="padding:8px 12px;background:#f5f5f5;color:#555;width:130px"><b>Trek</b></td><td style="padding:8px 12px">{trek.name}</td></tr>
                  <tr><td style="padding:8px 12px;color:#555"><b>Location</b></td><td style="padding:8px 12px">{trek.location}</td></tr>
                  <tr><td style="padding:8px 12px;background:#f5f5f5;color:#555"><b>Start Date</b></td><td style="padding:8px 12px">{trek.start_date}</td></tr>
                  <tr><td style="padding:8px 12px;color:#555"><b>Duration</b></td><td style="padding:8px 12px">{trek.duration} days</td></tr>
                  <tr><td style="padding:8px 12px;background:#f5f5f5;color:#555"><b>Meeting Point</b></td><td style="padding:8px 12px">{trek.meeting_point or 'TBD'}</td></tr>
                  <tr><td style="padding:8px 12px;color:#555"><b>Guide</b></td><td style="padding:8px 12px">{guide_name}</td></tr>
                  <tr><td style="padding:8px 12px;background:#f5f5f5;color:#555"><b>Difficulty</b></td><td style="padding:8px 12px">{trek.difficulty}</td></tr>
                </table>
                <div style="background:#e8f5e9;padding:14px;border-radius:8px;margin-top:16px">
                  <strong>🎒 Equipment Needed:</strong><br>
                  <span style="color:#555">{trek.equipment_needed or 'Standard trekking gear'}</span>
                </div>
                <p style="color:#888;font-size:12px;margin-top:24px">
                  — TMA: Trekking Management Application
                </p>
              </div>
            </div>"""

            try:
                msg = Message(
                    subject=f'⛰️ Reminder: "{trek.name}" starts in {label}!',
                    recipients=[user.email],
                    html=html_body,
                )
                mail.send(msg)
                total_sent += 1
            except Exception as exc:
                print(f'[TMA Jobs] Reminder email failed for {user.email}: {exc}. Using fallback log.')
                log_email_fallback(
                    subject=f'⛰️ Reminder: "{trek.name}" starts in {label}!',
                    recipients=[user.email],
                    html=html_body
                )
                total_sent += 1

    db.session.commit()
    return f'Daily reminders done — {total_sent} notifications created/sent'


def run_monthly_report():
    """
    Generates an HTML report covering the previous month and emails it to the admin.
    """
    now = datetime.utcnow()
    prev_month = now.month - 1 or 12
    prev_year = now.year if now.month > 1 else now.year - 1
    month_str = calendar.month_name[prev_month]
    ym = f'{prev_year:04d}-{prev_month:02d}'

    # Query stats
    month_bookings = Booking.query.filter(
        db.func.strftime('%Y-%m', Booking.booking_date) == ym
    ).all()
    total_bookings = len(month_bookings)
    total_revenue = sum(b.amount for b in month_bookings if b.status != 'Cancelled')
    unique_users = len(set(b.user_id for b in month_bookings))
    completed_treks = Trek.query.filter_by(status='Completed').count()
    all_users = User.query.filter_by(role='user').count()

    # Popular treks
    trek_counts = {}
    for b in month_bookings:
        if b.status != 'Cancelled':
            trek_counts[b.trek_id] = trek_counts.get(b.trek_id, 0) + 1

    popular_rows = ''
    sorted_treks = sorted(trek_counts.items(), key=lambda x: -x[1])[:5]
    for rank, (tid, cnt) in enumerate(sorted_treks, 1):
        t = Trek.query.get(tid)
        if t:
            bar = int(cnt / max(trek_counts.values(), default=1) * 100)
            popular_rows += f"""
            <tr>
              <td style="padding:10px;border-bottom:1px solid #eee;font-weight:bold;color:#2c7a4b">#{rank}</td>
              <td style="padding:10px;border-bottom:1px solid #eee">{t.name}</td>
              <td style="padding:10px;border-bottom:1px solid #eee;color:#666">{t.location}</td>
              <td style="padding:10px;border-bottom:1px solid #eee">
                <div style="background:#e8f5e9;border-radius:4px;margin-bottom:4px">
                  <div style="background:#2c7a4b;width:{bar}%;height:12px;border-radius:4px"></div>
                </div>
                <strong>{cnt}</strong> bookings
              </td>
            </tr>"""

    if not popular_rows:
        popular_rows = '<tr><td colspan="4" style="padding:12px;color:#999;text-align:center">No bookings this month</td></tr>'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>TMA Monthly Report</title></head>
<body style="font-family:Arial,sans-serif;background:#f4f6f4;margin:0;padding:20px">
  <div style="max-width:700px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1)">
    <div style="background:linear-gradient(135deg,#2c7a4b,#1a4f30);padding:36px">
      <h1 style="color:#fff;margin:0;font-size:26px">🏔️ TMA Monthly Activity Report</h1>
      <p style="color:rgba(255,255,255,.8);margin:6px 0 0;font-size:18px">{month_str} {prev_year}</p>
      <p style="color:rgba(255,255,255,.5);margin:4px 0 0;font-size:12px">Generated on {now.strftime('%d %b %Y at %H:%M')}</p>
    </div>
    <div style="padding:32px">
      <h2 style="color:#2c7a4b;border-bottom:2px solid #e8f5e9;padding-bottom:8px">📊 Monthly Summary</h2>
      <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px">
        <div style="flex:1;min-width:140px;background:#e8f5e9;border-radius:10px;padding:20px;text-align:center">
          <div style="font-size:36px;font-weight:bold;color:#2c7a4b">{total_bookings}</div>
          <div style="color:#555;margin-top:4px">Total Bookings</div>
        </div>
        <div style="flex:1;min-width:140px;background:#e3f2fd;border-radius:10px;padding:20px;text-align:center">
          <div style="font-size:36px;font-weight:bold;color:#0288d1">{unique_users}</div>
          <div style="color:#555;margin-top:4px">Trekkers Participated</div>
        </div>
        <div style="flex:1;min-width:140px;background:#f3e5f5;border-radius:10px;padding:20px;text-align:center">
          <div style="font-size:36px;font-weight:bold;color:#7b1fa2">₹{total_revenue:,.0f}</div>
          <div style="color:#555;margin-top:4px">Revenue</div>
        </div>
        <div style="flex:1;min-width:140px;background:#fff3e0;border-radius:10px;padding:20px;text-align:center">
          <div style="font-size:36px;font-weight:bold;color:#f57c00">{completed_treks}</div>
          <div style="color:#555;margin-top:4px">Treks Conducted</div>
        </div>
      </div>
      <p style="color:#555">Total registered trekkers on platform: <strong>{all_users}</strong></p>
      <h2 style="color:#2c7a4b;border-bottom:2px solid #e8f5e9;padding-bottom:8px">🔥 Popular Treks This Month</h2>
      <table style="width:100%;border-collapse:collapse">
        <thead>
          <tr style="background:#2c7a4b;color:#fff">
            <th style="padding:12px;text-align:left">#</th>
            <th style="padding:12px;text-align:left">Trek Name</th>
            <th style="padding:12px;text-align:left">Location</th>
            <th style="padding:12px;text-align:left">Bookings</th>
          </tr>
        </thead>
        <tbody>{popular_rows}</tbody>
      </table>
      <p style="color:#aaa;font-size:11px;margin-top:28px;text-align:center">
        © TMA — Trekking Management Application | Auto-generated on 1st of month
      </p>
    </div>
  </div>
</body></html>"""

    admin_email = getattr(Config, 'ADMIN_EMAIL', 'admin@gmail.com')
    try:
        msg = Message(
            subject=f'📊 TMA Monthly Report — {month_str} {prev_year}',
            recipients=[admin_email],
            html=html,
        )
        mail.send(msg)
        return f'Monthly report sent to {admin_email}'
    except Exception as exc:
        print(f'[TMA Jobs] Monthly report email failed: {exc}. Using fallback log.')
        log_email_fallback(
            subject=f'📊 TMA Monthly Report — {month_str} {prev_year}',
            recipients=[admin_email],
            html=html
        )
        return f'Monthly report logged to fallback file for {admin_email}'


def run_export_csv(task_id, user_id):
    """
    Performs the CSV export of user bookings, updates task status, 
    emails the CSV to the user, and triggers an in-app notification.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            task_statuses[task_id] = {'status': 'FAILURE', 'result': 'User not found'}
            return

        bookings = (
            Booking.query
            .filter_by(user_id=user_id)
            .order_by(Booking.booking_date.desc())
            .all()
        )

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Booking ID', 'User ID', 'Trek Name', 'Location', 'Difficulty',
            'Start Date', 'End Date', 'Booking Date', 'Status',
            'Payment Status', 'Transaction ID', 'Amount (INR)',
        ])
        for b in bookings:
            d = b.to_dict()
            writer.writerow([
                d['id'], d['user_id'], d['trek_name'], d['trek_location'],
                d['trek_difficulty'], d.get('start_date', ''), d.get('end_date', ''),
                (d['booking_date'] or '')[:10], d['status'], d['payment_status'],
                d.get('transaction_id', ''), d['amount'],
            ])

        csv_bytes = output.getvalue().encode('utf-8')
        
        # Store a copy of the export inside backend/exports folder
        try:
            import os
            exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
            os.makedirs(exports_dir, exist_ok=True)
            export_filename = f'booking_history_{user.username}_{task_id[:8]}.csv'
            export_path = os.path.join(exports_dir, export_filename)
            with open(export_path, 'wb') as f:
                f.write(csv_bytes)
            print(f'[TMA Jobs] Stored export copy at: {export_path}')
        except Exception as e:
            print(f'[TMA Jobs] Failed to store export copy: {e}')

        email_sent = False

        # Attempt to email CSV
        try:
            msg = Message(
                subject='📊 Your Booking History Export — TMA',
                recipients=[user.email],
                body=(
                    f'Hi {user.get_name()},\n\n'
                    f'Your booking history export ({len(bookings)} records) is attached.\n\n'
                    f'Happy Trekking! 🏔️\n— TMA Team'
                ),
            )
            msg.attach(
                f'booking_history_{user.username}.csv',
                'text/csv',
                csv_bytes,
            )
            mail.send(msg)
            email_sent = True
        except Exception as exc:
            print(f'[TMA Jobs] Export CSV email failed for {user.email}: {exc}. Using fallback log.')
            log_email_fallback(
                subject='📊 Your Booking History Export — TMA',
                recipients=[user.email],
                body=(
                    f'Hi {user.get_name()},\n\n'
                    f'Your booking history export ({len(bookings)} records) is attached.\n\n'
                    f'Happy Trekking! 🏔️\n— TMA Team'
                ),
                attachment_name=f'booking_history_{user.username}.csv'
            )
            email_sent = True

        # In-app notification
        notif_msg = (
            f'Your booking history ({len(bookings)} records) was emailed to {user.email}.'
            if email_sent
            else f'Your booking history ({len(bookings)} records) is ready. Check your email or download from the bookings page.'
        )
        
        db.session.add(Notification(
            user_id=user_id,
            title='📊 CSV Export Complete!',
            message=notif_msg,
            type='success',
        ))
        db.session.commit()

        task_statuses[task_id] = {
            'status': 'SUCCESS', 
            'result': f'CSV exported — {len(bookings)} records for {user.email}'
        }

    except Exception as e:
        db.session.rollback()
        task_statuses[task_id] = {'status': 'FAILURE', 'result': str(e)}


def scheduler_loop(app):
    """
    Main loop checking for daily reminders and monthly report times.
    """
    while True:
        with app.app_context():
            try:
                now = datetime.now()
                
                # Check Daily Reminders (Runs daily if hour is >= 8)
                today_str = now.strftime('%Y-%m-%d')
                if now.hour >= 8 and last_runs['daily'] != today_str:
                    print("[TMA Jobs] Running scheduled daily reminders...")
                    run_daily_reminders()
                    last_runs['daily'] = today_str
                
                # Check Monthly Report (Runs on 1st of month if hour is >= 6)
                month_str = now.strftime('%Y-%m')
                if now.day == 1 and now.hour >= 6 and last_runs['monthly'] != month_str:
                    print("[TMA Jobs] Running scheduled monthly activity report...")
                    run_monthly_report()
                    last_runs['monthly'] = month_str
            except Exception as e:
                print(f"[TMA Jobs] Error in background scheduler loop: {e}")
        
        # Check every 60 seconds
        time.sleep(60)


def worker_loop(app):
    """
    Pulls async tasks from the queue and executes them with application context.
    """
    while True:
        try:
            task = task_queue.get()
            task_id = task['task_id']
            user_id = task['user_id']
            
            task_statuses[task_id] = {'status': 'PROCESSING', 'result': None}
            
            with app.app_context():
                run_export_csv(task_id, user_id)
            
            task_queue.task_done()
        except Exception as e:
            print(f"[TMA Jobs] Error in background worker loop: {e}")
            time.sleep(1)


def queue_export_job(user_id):
    """
    Adds a new CSV export job to the queue and returns its task ID.
    """
    task_id = str(uuid.uuid4())
    task_statuses[task_id] = {'status': 'PENDING', 'result': None}
    task_queue.put({'task_id': task_id, 'user_id': user_id, 'type': 'export_csv'})
    return task_id


def get_task_status(task_id):
    """
    Returns the status and result of a task.
    """
    return task_statuses.get(task_id, {'status': 'PENDING', 'result': None})


def init_scheduler(app):
    """
    Spawns background worker and scheduler threads.
    """
    # Start the async worker thread
    worker_thread = threading.Thread(target=worker_loop, args=(app,), daemon=True)
    worker_thread.start()
    
    # Start the periodic scheduler thread
    scheduler_thread = threading.Thread(target=scheduler_loop, args=(app,), daemon=True)
    scheduler_thread.start()
    print("[TMA Jobs] Background scheduler and worker threads successfully initialized.")
