from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_current_user
from extensions import db, cache
from models.models import User, TrekkerInfo, StaffInfo, Booking, Trek, Notification
from functools import wraps


staff_bp = Blueprint('staff', __name__ )


def staff_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'staff':
            return jsonify({'error': 'Staff access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


@staff_bp.routes('/dashboard', methods=['GET'])
@staff_required
def staff_dashboard():
    staff = get_current_user()
    treks = Trek.query.filter_by(staff_id=staff.id).all()
    data = []
    for trek in treks:
        trek_data = trek.to_dict()
        trek_data['participant_count'] = len([b for b in trek.bookings if b.status == 'Booked'])
        trek_data['revenue'] = round(sum(b.amount for b in trek.bookings if b.status!='Cancelled'), 2)
        data.append(trek_data)
    return jsonify({
        'staff': staff.to_dict(full=True),
        'assigned_treks': data,
        'total_assigned': len(treks),
        'total_participants': sum(t['participant_count'] for t in data),
        'total_revenue': round(sum(t['revenue'] for t in data), 2),
        'open_treks': sum(1 for t in data if t.status == 'Open'),
        'started_treks': sum(1 for t in data if t.status == 'Started'),
        'completed_treks': sum(1 for t in data if t.status == 'Completed')
    }), 200


@staff_bp.route('/treks', methods=['GET'])
@staff_required
def get_treks():
    staff = get_current_user()
    result = []
    for t in Trek.query.filter_by(staff_id=staff.id).all():
        trek_data = t.to_dict()
        trek_data['participant_count'] = len([b for b in t.bookings if b.status == 'Booked'])
        result.append(trek_data)
    return jsonify(result), 200

@staff_bp.route('/treks/<int:trek_id>', methods=['PUT'])



@staff_bp.route('/treks/<int:trek_id>', methods=['PUT'] )
@staff_required
def update_trek(trek_id):
    staff = get_current_user()
    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != staff.id and staff.role=='staff':
        return jsonify({'error': 'Not authorized to update this trek'}), 403
    
    data = request.get_json()
    if 'available_slots' in data:
        booked = len([b for b in trek.bookings if b.status == 'Booked'])
        new_slots = int(data['available_slots'])
        if new_slots < 0:
            return jsonify({'error': 'Available slots cannot be negative'}), 400
        if new_slots < booked:
            return jsonify({'error': f'Available slots cannot be less than booked participants ({booked})'}), 400
        trek.available_slots = new_slots
    if 'status' in data:
        allowed = ['Open', 'Started', 'Completed']
        if data['status'] not in allowed:
            return jsonify({'error': f'Status must be one of {allowed}'}), 400
        old_status = trek.status
        trek.status = data['status']

        if data['status'] == 'Started' and old_status != 'Started':
            # Notify participants that trek has started
            for booking in trek.bookings:
                if booking.status == 'Booked':
                    notif = Notification(
                        user_id=booking.user_id,
                        title='Trek Started',
                        message=f'Trek "{trek.name}" has officially started. Enjoy your adventure!',
                        type='info'
                    )
                    db.session.add(notif)
        
        if data['status'] == 'Completed' and old_status != 'Completed':
            # Notify participants that trek has completed
            for booking in trek.bookings:
                if booking.status == 'Booked':
                    booking.status = 'Completed'
                    notif = Notification(
                        user_id=booking.user_id,
                        title='Trek Completed',
                        message=f'Congratulations! "{trek.name}" is completed. Rate your experience in My Bookings.',
                        type='success'
                    )
                    db.session.add(notif)

    for f in ('description','meeting_point','equipment_needed'):
        if f in data: setattr(trek, f, data[f])

    db.session.commit()
    cache.clear()
    return jsonify({'message':'Updated','trek':trek.to_dict()}), 200


@staff_bp.route('/treks/<int:trek_id>/participants', methods=['GET'])
@staff_required
def get_participants(trek_id):
    staff = get_current_user()
    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != staff.id and staff.role=='staff':
        return jsonify({'error': 'Not authorized to view participants for this trek'}), 403
    
    bookings = Booking.query.filter_by(trek_id=trek.id).all()
    participants = []
    for b in bookings:
        booking_data = b.to_dict()
        user = User.query.get(b.user_id)
        if user and user.trekker_info:
            booking_data['user'] = user.to_dict(full=True)
        participants.append(booking_data)
    return jsonify({
        'trek': trek.to_dict(),
        'participants': participants,  
        'total': len(bookings),
        'booked': len([b for b in bookings if b.status == 'Booked']),
        'revenue': round(sum(b.amount for b in bookings if b.status!='Cancelled'), 2)
    }), 200