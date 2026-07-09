import csv, io, random, string
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_current_user
from extensions import db, cache
from functools import wraps
from models.models import User, TrekkerInfo, StaffInfo, Booking, Trek, Review, Notification, Wishlist

trekker_bp = Blueprint('user', __name__)


def trekker_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'user':
            return jsonify({'error': 'User access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


def __notify(user_id, title, message, ntype='info'):
    notification = Notification(user_id=user_id, title=title, message=message, type=ntype)
    db.session.add(notification)

def __tnx():
    return 'TNX'+"".join(random.choices(string.ascii_uppercase + string.digits, k=10))  


############ Public : Plateform stats and Browse Treks ############


@trekker_bp.route('/profile-stats', methods=['GET'])
@cache.cached(timeout=600, key_prefix='profile_stats_data')
def profile_stats():
    completed_treks = Trek.query.filter_by(status='Completed').count()
    open_treks = Trek.query.filter_by(status='Open').count()
    total_bookings = Booking.query.count()
    destinations = db.session.query(Trek.location).distinct().count()
    total_trekkers = User.query.filter_by(role='user').count()
    return jsonify({
        'completed_treks': completed_treks,
        'open_treks': open_treks,
        'total_bookings': total_bookings,
        'destinations': destinations,
        'total_trekkers': total_trekkers
    }), 200


@trekker_bp.route('/treks', methods=['GET'])
def get_treks():
    query = (request.args.get('query') or request.args.get('q') or '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip()
    min_duration = request.args.get('min_duration', type=int)
    max_duration = request.args.get('max_duration', type=int)   
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort = request.args.get('sort', 'date')

    cache_key = f"treks|{query}|{difficulty}|{location}|{min_duration}|{max_duration}|{min_price}|{max_price}|{sort}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached), 200
    
    from sqlalchemy.orm import joinedload
    treks = Trek.query.options(
        joinedload(Trek.assigned_staff).joinedload(User.staff_info)
    ).filter_by(status='Open')
    if difficulty: treks = treks.filter_by(difficulty=difficulty)
    if location:   treks = treks.filter(Trek.location.ilike(f'%{location}%'))
    if min_duration:    treks = treks.filter(Trek.duration >= min_duration)
    if max_duration:    treks = treks.filter(Trek.duration <= max_duration)
    if min_price:  treks = treks.filter(Trek.price >= min_price)
    if max_price:  treks = treks.filter(Trek.price <= max_price)
    if query:
        treks = treks.filter(
            Trek.name.ilike(f'%{query}%') |
            Trek.location.ilike(f'%{query}%') |
            Trek.description.ilike(f'%{query}%')
        )

    result = [t.to_dict() for t in treks.all()]
    if sort == 'price_asc':   result.sort(key=lambda x: x['price'])
    elif sort == 'price_desc': result.sort(key=lambda x: x['price'], reverse=True)
    elif sort == 'rating':     result.sort(key=lambda x: x['avg_rating'], reverse=True)
    else:                      result.sort(key=lambda x: x['start_date'] or '')

    cache.set(cache_key, result, timeout=180)  
    return jsonify(result), 200


@trekker_bp.route('/treks/<int:trek_id>', methods=['GET'])
def get_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    data = trek.to_dict()
    data['reviews'] = [r.to_dict() for r in trek.reviews]
    return jsonify(data), 200


@trekker_bp.route('/treks/<int:trek_id>/reviews', methods=['GET'])
def get_trek_reviews(trek_id):
    return jsonify([r.to_dict() for r in
                    Review.query.filter_by(trek_id=trek_id)
                    .order_by(Review.created_at.desc()).all()]), 200





#####################################################

@trekker_bp.route('/dashboard', methods=['GET'])
@trekker_required
def dashboard():
    from sqlalchemy.orm import joinedload
    user = get_current_user()
    bookings = Booking.query.options(
        joinedload(Booking.trek),
        joinedload(Booking.user)
    ).filter_by(user_id=user.id).order_by(Booking.booking_date.desc()).all()
    booked_trek_ids = {b.trek_id for b in bookings if b.status == 'Booked'}
    available = Trek.query.options(
        joinedload(Trek.assigned_staff).joinedload(User.staff_info)
    ).filter(Trek.status == 'Open', ~Trek.id.in_(booked_trek_ids)).order_by(Trek.start_date).limit(6).all()
    active_bookings = [b for b in bookings if b.status == 'Booked']
    total_spent = round(sum(b.amount for b in bookings if b.status != 'Cancelled'), 2)
    wishlist_count = Wishlist.query.filter_by(user_id=user.id).count()
    unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({
        'user':user.to_dict(full=True),
        'total_bookings': len(bookings),
        'active_bookings': len(active_bookings),
        'completed_bookings': sum([1 for b in bookings if b.status == 'Completed']),
        'cancelled_bookings': sum([1 for b in bookings if b.status == 'Cancelled']),
        'total_spent': round(total_spent, 2),
        'wishlist_count': wishlist_count,
        'unread_notifications': unread,
        'available_treks': [t.to_dict() for t in available],
        'active_boking_list': [b.to_dict() for b in active_bookings],
        'recent_bookings': [b.to_dict() for b in bookings[:5]]
    }), 200



@trekker_bp.route('/bookings', methods=['POST'])
@trekker_required
def create_booking():
    user = get_current_user()
    data = request.get_json()
    trek = Trek.query.get_or_404(data.get('trek_id'))

    if trek.status != 'Open':
        return jsonify({'error': 'Trek is not open for booking'}), 400
    if trek.available_slots <= 0:
        return jsonify({'error': 'No slots available - Trek is fully booked'}), 400
    if Booking.query.filter_by(user_id=user.id, trek_id=trek.id, status='Booked').first():
        return jsonify({'error': 'You have already booked this trek'}), 409
    
    tnx = __tnx()
    booking = Booking(
        user_id = user.id,
        trek_id = trek.id,
        amount = trek.price,
        payment_status = 'Paid',
        payment_method = data.get('payment_method', 'UPI'),
        transaction_id = tnx,
        notes = data.get('notes', '')

    )

    trek.available_slots -= 1
    db.session.add(booking)
    __notify(user.id, 'Booking Confirmed', f'Your booking for trek "{trek.name}" has been confirmed. Transaction ID: {tnx}', 'success')
    db.session.commit()
    cache.clear()
    return jsonify({
        'message': 'Trek booked!',
        'booking': booking.to_dict(),
        'transaction_id': tnx,
        'remaining_slots': trek.available_slots
    }), 201


@trekker_bp.route('/bookings', methods=['GET'])
@trekker_required
def get_bookings():
    user = get_current_user()
    status = request.args.get('status','')
    booking = Booking.query.filter_by(user_id=user.id)
    if status:
        booking = booking.filter_by(status=status)
    booking = booking.order_by(Booking.booking_date.desc()).all()
    return jsonify([b.to_dict() for b in booking]), 200




@trekker_bp.route('/bookings/<int:booking_id>/cancel', methods=['PUT'])
@trekker_required
def cancel_booking(booking_id):
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != user.id:
        return jsonify({'error': 'Not authorized to cancel this booking'}), 403
    if booking.status != 'Booked':
        return jsonify({'error': 'Booking cannot be cancelled'}), 400
    
    trek = Trek.query.get(booking.trek_id)
    booking.status = 'Cancelled'
    booking.payment_status = 'Refunded'
    if trek and trek.status == 'Open':
        trek.available_slots += 1
    __notify(user.id, 'Booking Cancelled', f'Your booking for trek "{trek.name}" has been cancelled.', 'warning')
    db.session.commit()
    cache.clear()
    return jsonify({
        'message': 'Booking cancelled',
        'booking': booking.to_dict(),
        'remaining_slots': trek.available_slots
    }), 200


@trekker_bp.route('/reviews', methods=['POST'])
@trekker_required
def create_review():
    user = get_current_user()
    data = request.get_json()

    trek_id = data.get('trek_id')
    rating = data.get('rating')

    if not trek_id or not rating or not (1 <= int(rating) <= 5):
        return jsonify({'error': 'Trek ID and rating (1-5) are required'}), 400
    if not Booking.query.filter_by(user_id=user.id, trek_id=trek_id, status='Completed').first():
        return jsonify({'error': 'You can only review treks you have completed'}), 403
    if Review.query.filter_by(user_id=user.id, trek_id=trek_id).first():
        return jsonify({'error': 'You have already reviewed this trek'}), 409
    
    review = Review(
        user_id = user.id,
        trek_id = trek_id,
        rating = int(rating),
        comment = data.get('comment', '')
    )
    db.session.add(review)
    db.session.commit()
    cache.clear()
    return jsonify({
        'message': 'Review submitted',
        'review': review.to_dict()
    }), 201
    


@trekker_bp.route('/wishlist', methods=['GET'])
@trekker_required
def get_wishlist():
    user = get_current_user()
    wishlist = Wishlist.query.filter_by(user_id=user.id).order_by(Wishlist.created_at.desc()).all()
    return jsonify([
        {
            'wishlist_id':w.id,
            'trek': w.trek.to_dict()
        } for w in wishlist if Trek.query.get(w.trek_id)
    ]), 200


@trekker_bp.route('/wishlist/ids', methods=['GET'])
@trekker_required
def wishlist_ids():
    user = get_current_user()
    wishlist_ids = [w.trek_id for w in Wishlist.query.filter_by(user_id=user.id).all()]
    return jsonify({'wishlist_ids': wishlist_ids}), 200



@trekker_bp.route('/wishlist/<int:trek_id>', methods=['POST'])
@trekker_required
def add_wishlist(trek_id):
    user = get_current_user()
    if Wishlist.query.filter_by(user_id=user.id, trek_id=trek_id).first():
        return jsonify({'error': 'Trek already in wishlist'}), 409
    wishlist_item = Wishlist(user_id=user.id, trek_id=trek_id)
    db.session.add(wishlist_item)
    db.session.commit()
    return jsonify({'message': 'Trek added to wishlist'}), 201

@trekker_bp.route('/wishlist/<int:trek_id>', methods=['DELETE'])
@trekker_required
def remove_wishlist(trek_id):
    user = get_current_user()
    wishlist_item = Wishlist.query.filter_by(user_id=user.id, trek_id=trek_id).first()
    if not wishlist_item:
        return jsonify({'error': 'Trek not in wishlist'}), 404
    db.session.delete(wishlist_item)
    db.session.commit()
    return jsonify({'message': 'Trek removed from wishlist'}), 200


@trekker_bp.route('/notifications', methods=['GET'])
@trekker_required
def get_notifications():
    user = get_current_user()
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(30).all()
    unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread': unread
    }), 200

@trekker_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@trekker_required
def mark_read(notification_id):
    user = get_current_user()
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user.id:
        return jsonify({'error': 'Not authorized to mark this notification'}), 403
    notification.is_read = True
    db.session.commit()
    return jsonify({'message': 'Notification marked as read'}), 200


@trekker_bp.route('/notifications/read-all', methods=['PUT'])
@trekker_required
def mark_all_read():
    user = get_current_user()
    notifications = Notification.query.filter_by(user_id=user.id, is_read=False).all()
    for n in notifications:
        n.is_read = True
    db.session.commit()
    return jsonify({'message': f'{len(notifications)} notifications marked as read'}), 200


@trekker_bp.route('/export-bookings', methods=['POST'])
@trekker_required
def export_bookings_async():
    user = get_current_user()
    try:
        from jobs import queue_export_job
        task_id = queue_export_job(user.id)
        return jsonify({
            'message': 'Export started! You will receive a notification when it is ready.',
            'task_id': task_id
        }), 202
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trekker_bp.route('/export-bookings/status/<task_id>', methods=['GET'])
@trekker_required
def export_status(task_id):
    from jobs import get_task_status
    status_info = get_task_status(task_id)
    return jsonify({
        'status': status_info['status'],
        'result': status_info['result']
    }), 200
