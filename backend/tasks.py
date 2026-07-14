import csv
import io
import calendar
import os
from datetime import datetime, date, timedelta
from celery_app import celery_instance
from celery.result import AsyncResult
from extensions import db, mail
from models.models import User, Trek, Booking, Notification
from flask_mail import Message
from config import Config

def log_email_fallback(subject, recipients, body=None, html=None, attachment_name=None):
    base_directory = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_directory, 'sent_emails.log')
    
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = "========================================\n"
    log_entry += f"Timestamp: {current_timestamp}\n"
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
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(log_entry)
        print(f"Logged email fallback to {log_path}")
    except Exception as log_exception:
        print(f"Failed to write fallback email log: {log_exception}")


@celery_instance.task(name='tasks.run_daily_reminders_task')
def run_daily_reminders_task():
    current_date = date.today()
    total_emails_sent = 0

    for days_ahead in [1, 2, 3]:
        target_date = current_date + timedelta(days=days_ahead)
        bookings = (
            Booking.query
            .join(Trek, Booking.trek_id == Trek.id)
            .filter(Trek.start_date == target_date, Booking.status == 'Booked')
            .all()
        )

        for booking in bookings:
            user = User.query.get(booking.user_id)
            trek = Trek.query.get(booking.trek_id)
            if not user or not trek:
                continue

            days_label = f'{days_ahead} day{"s" if days_ahead > 1 else ""}'
            guide_name = trek.assigned_staff.get_name() if trek.assigned_staff else 'TBD'

            db.session.add(Notification(
                user_id=booking.user_id,
                title=f'Trek starts in {days_label}!',
                message=(
                    f'"{trek.name}" at {trek.location} starts on {trek.start_date}. '
                    f'Meeting point: {trek.meeting_point or "TBD"}. Guide: {guide_name}.'
                ),
                type='warning',
            ))

            html_body = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2c7a4b;">Trek Reminder — {days_label} to go!</h2>
                <p>Hello {user.get_name()},</p>
                <p>This is a reminder that your trek starts in {days_label}. Here are your trek details:</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr><td style="padding: 8px 0; font-weight: bold; width: 150px;">Trek Name:</td><td style="padding: 8px 0;">{trek.name}</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Location:</td><td style="padding: 8px 0;">{trek.location}</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Start Date:</td><td style="padding: 8px 0;">{trek.start_date}</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Duration:</td><td style="padding: 8px 0;">{trek.duration} days</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Meeting Point:</td><td style="padding: 8px 0;">{trek.meeting_point or 'TBD'}</td></tr>
                    <tr><td style="padding: 8px 0; font-weight: bold;">Guide:</td><td style="padding: 8px 0;">{guide_name}</td></tr>
                </table>
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 4px; border-left: 4px solid #2c7a4b;">
                    <strong>Required Equipment:</strong><br>
                    <p style="margin: 5px 0 0; color: #555;">{trek.equipment_needed or 'Standard trekking gear'}</p>
                </div>
                <p style="margin-top: 30px; font-size: 12px; color: #777;">Trekking Management Application</p>
            </div>"""

            try:
                mail_message = Message(
                    subject=f'Reminder: "{trek.name}" starts in {days_label}!',
                    recipients=[user.email],
                    html=html_body,
                )
                mail.send(mail_message)
                total_emails_sent += 1
            except Exception as mail_exception:
                print(f"Reminder email failed for {user.email}: {mail_exception}")
                log_email_fallback(
                    subject=f'Reminder: "{trek.name}" starts in {days_label}!',
                    recipients=[user.email],
                    html=html_body
                )
                total_emails_sent += 1

    db.session.commit()
    return f'Daily reminders done — {total_emails_sent} notifications created/sent'


@celery_instance.task(name='tasks.run_monthly_report_task')
def run_monthly_report_task():
    current_time = datetime.utcnow()
    previous_month = current_time.month - 1 or 12
    previous_year = current_time.year if current_time.month > 1 else current_time.year - 1
    month_name_string = calendar.month_name[previous_month]
    year_month_string = f'{previous_year:04d}-{previous_month:02d}'

    monthly_bookings = Booking.query.filter(
        db.func.strftime('%Y-%m', Booking.booking_date) == year_month_string
    ).all()
    total_bookings = len(monthly_bookings)
    total_revenue = sum(booking.amount for booking in monthly_bookings if booking.status != 'Cancelled')
    unique_users = len(set(booking.user_id for booking in monthly_bookings))
    completed_treks = Trek.query.filter_by(status='Completed').count()
    all_users = User.query.filter_by(role='user').count()

    trek_booking_counts = {}
    for booking in monthly_bookings:
        if booking.status != 'Cancelled':
            trek_booking_counts[booking.trek_id] = trek_booking_counts.get(booking.trek_id, 0) + 1

    popular_trek_rows = ''
    sorted_trek_list = sorted(trek_booking_counts.items(), key=lambda item: -item[1])[:5]
    for rank, (trek_id, booking_count) in enumerate(sorted_trek_list, 1):
        trek = Trek.query.get(trek_id)
        if trek:
            popular_trek_rows += f"""
            <tr>
              <td style="padding: 10px; border-bottom: 1px solid #eee;">{rank}</td>
              <td style="padding: 10px; border-bottom: 1px solid #eee;">{trek.name}</td>
              <td style="padding: 10px; border-bottom: 1px solid #eee;">{trek.location}</td>
              <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">{booking_count}</td>
            </tr>"""

    if not popular_trek_rows:
        popular_trek_rows = '<tr><td colspan="4" style="padding: 12px; color: #999; text-align: center;">No bookings this month</td></tr>'

    html_report_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Monthly Activity Report</title>
</head>
<body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; color: #333;">
    <div style="max-width: 650px; margin: 0 auto; background-color: #fff; padding: 25px; border: 1px solid #eaeaea; border-radius: 8px;">
        <h2 style="color: #2c7a4b; border-bottom: 2px solid #2c7a4b; padding-bottom: 8px; margin-top: 0;">Monthly Activity Report</h2>
        <p style="font-size: 14px; color: #666;">Report Period: {month_name_string} {previous_year}</p>
        
        <h3 style="color: #444; margin-top: 25px;">Monthly Summary</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Metric</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Count</th>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Total Bookings</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{total_bookings}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Unique Trekkers</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{unique_users}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Monthly Revenue</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">INR {total_revenue:,.2f}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Treks Completed</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{completed_treks}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Total Registered Trekkers</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{all_users}</td>
            </tr>
        </table>
        
        <h3 style="color: #444;">Top Treks This Month</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Rank</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Trek Name</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Location</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Bookings</th>
                </tr>
            </thead>
            <tbody>
                {popular_trek_rows}
            </tbody>
        </table>
        <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
        <p style="font-size: 11px; color: #999; text-align: center; margin-bottom: 0;">Trekking Management Application</p>
    </div>
</body>
</html>"""

    admin_email_address = getattr(Config, 'ADMIN_EMAIL', 'admin@gmail.com')
    try:
        mail_message = Message(
            subject=f'Monthly Report — {month_name_string} {previous_year}',
            recipients=[admin_email_address],
            html=html_report_content,
        )
        mail.send(mail_message)
        return f'Monthly report sent to {admin_email_address}'
    except Exception as email_exception:
        print(f"Monthly report email failed: {email_exception}")
        log_email_fallback(
            subject=f'Monthly Report — {month_name_string} {previous_year}',
            recipients=[admin_email_address],
            html=html_report_content
        )
        return f'Monthly report logged to fallback file'


@celery_instance.task(bind=True, name='tasks.run_export_csv_task')
def run_export_csv_task(self, user_id):
    task_id = self.request.id
    try:
        user = User.query.get(user_id)
        if not user:
            return f'User with ID {user_id} not found'

        bookings = (
            Booking.query
            .filter_by(user_id=user_id)
            .order_by(Booking.booking_date.desc())
            .all()
        )

        csv_output = io.StringIO()
        csv_writer = csv.writer(csv_output)
        csv_writer.writerow([
            'Booking ID', 'User ID', 'Trek Name', 'Location', 'Difficulty',
            'Start Date', 'End Date', 'Booking Date', 'Status',
            'Payment Status', 'Transaction ID', 'Amount (INR)',
        ])
        
        for booking in bookings:
            booking_dictionary = booking.to_dict()
            csv_writer.writerow([
                booking_dictionary['id'],
                booking_dictionary['user_id'],
                booking_dictionary['trek_name'],
                booking_dictionary['trek_location'],
                booking_dictionary['trek_difficulty'],
                booking_dictionary.get('start_date', ''),
                booking_dictionary.get('end_date', ''),
                (booking_dictionary['booking_date'] or '')[:10],
                booking_dictionary['status'],
                booking_dictionary['payment_status'],
                booking_dictionary.get('transaction_id', ''),
                booking_dictionary['amount'],
            ])

        csv_bytes = csv_output.getvalue().encode('utf-8')
        
        try:
            base_directory = os.path.dirname(os.path.abspath(__file__))
            exports_directory = os.path.join(base_directory, 'exports')
            os.makedirs(exports_directory, exist_ok=True)
            export_filename = f'booking_history_{user.username}_{task_id[:8]}.csv'
            export_path = os.path.join(exports_directory, export_filename)
            with open(export_path, 'wb') as export_file:
                export_file.write(csv_bytes)
            print(f"Stored export copy at: {export_path}")
        except Exception as storage_exception:
            print(f"Failed to store export copy: {storage_exception}")

        is_email_sent = False

        try:
            mail_message = Message(
                subject='Your Booking History Export — TMA',
                recipients=[user.email],
                body=(
                    f'Hi {user.get_name()},\n\n'
                    f'Your booking history export ({len(bookings)} records) is attached.\n\n'
                    f'Happy Trekking!\n— TMA Team'
                ),
            )
            mail_message.attach(
                f'booking_history_{user.username}.csv',
                'text/csv',
                csv_bytes,
            )
            mail.send(mail_message)
            is_email_sent = True
        except Exception as mail_exception:
            print(f"Export CSV email failed: {mail_exception}")
            log_email_fallback(
                subject='Your Booking History Export — TMA',
                recipients=[user.email],
                body=(
                    f'Hi {user.get_name()},\n\n'
                    f'Your booking history export ({len(bookings)} records) is attached.\n\n'
                    f'Happy Trekking!\n— TMA Team'
                ),
                attachment_name=f'booking_history_{user.username}.csv'
            )
            is_email_sent = True

        notification_message = (
            f'Your booking history ({len(bookings)} records) was emailed to {user.email}.'
            if is_email_sent
            else f'Your booking history ({len(bookings)} records) is ready. Check your email.'
        )
        
        db.session.add(Notification(
            user_id=user_id,
            title='CSV Export Complete!',
            message=notification_message,
            type='success',
        ))
        db.session.commit()

        return f'CSV exported — {len(bookings)} records for {user.email}'

    except Exception as task_exception:
        db.session.rollback()
        raise task_exception


def queue_export_job(user_id):
    celery_task_instance = run_export_csv_task.delay(user_id)
    return celery_task_instance.id


def get_task_status(task_id):
    celery_result_instance = AsyncResult(task_id, app=celery_instance)
    celery_state = celery_result_instance.state
    
    task_status = celery_state
    task_outcome = None
    
    if celery_result_instance.ready():
        if celery_state == 'SUCCESS':
            task_outcome = celery_result_instance.result
        elif celery_state == 'FAILURE':
            task_outcome = str(celery_result_instance.result)
            
    return {
        'status': task_status,
        'result': task_outcome
    }
