from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from extensions import db, cache
from models.models import Review, User, StaffInfo, Booking, Trek, Review
from functools import wraps
from datetime import date

admin_bp = Blueprint('admin', __name__)


def admin_required(fn):                
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = get_current_user()
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    statuses = ['Pending','Approved','Open','Closed','Started','Completed']
    trek_stats = {status: Trek.query.filter_by(status=status).count() for status in statuses}
    popular = (db.session.query(Trek, db.func.count(Booking.id).label('cnt'))
               .join(Booking, Trek.id==Booking.trek_id).filter(Booking.status=='Booked')
               .group_by(Trek.id).order_by(db.desc('cnt')).limit(5).all())
    revenue = db.session.query(db.func.sum(Booking.amount)).filter(Booking.status!='Cancelled').scalar() or 0

    return jsonify({
        'total_treks': Trek.query.count(),
        'total_users': User.query.filter_by(role='user').count(),
        'total_staff': User.query.filter_by(role='staff').count(),
        'total_bookings': Booking.query.count(),
        'active_bookings':Booking.query.filter_by(status='Booked').count(),
        'open_treks':Trek.query.filter_by(status='Open').count(),
        'total_revenue': round(revenue, 2),
        'trek_stats': trek_stats,
        'popular_treks': [{'trek':trek.to_dict(), 'bookings': cnt} for trek, cnt in popular]
    }), 200


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def admin_stats():
    monthly = db.session.query(
        db.func.strftime('%Y-%m', Booking.booking_date).label('month'),
        db.func.count(Booking.id).label('count'),
        db.func.sum(Booking.amount).label('revenue')
    ).group_by('month').order_by('month').limit(12).all()
    diff = db.session.query(Trek.difficulty, db.func.count(Booking.id)).join(Booking, Trek.id==Booking.trek_id).filter(Booking.status=='Booked').group_by(Trek.difficulty).all()

    return  jsonify({
        'monthly_stats': [{'month': month, 'count': count, 'revenue': round(revenue or 0, 2)} for month, count, revenue in monthly],
        'difficulty_stats': [{'difficulty': difficulty, 'bookings': count} for difficulty, count in diff]
    })


@admin_bp.route('/search', methods=['GET'])
@admin_required
def admin_search():
    query = request.args.get('q', '').strip()
    if len(query)<1:
        return jsonify({'treks': [], 'users': [], 'staff': []}), 200
    
    trek_filter = Trek.name.ilike(f'%{query}%') | Trek.location.ilike(f'%{query}%')
    if query.isdigit():
        trek_filter = trek_filter | (Trek.id==int(query))
    treks = Trek.query.filter(trek_filter).limit(5).all()

    userstaff_filter = User.name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%') | User.username.ilike(f'%{query}%')
    if query.isdigit():
         userstaff_filter = userstaff_filter | (User.id == int(query))
    users = User.query.filter(User.role =='user').filter(userstaff_filter).limit(5).all()
    staffs = User.query.filter(User.role =='staff').filter(userstaff_filter).limit(5).all()

    return jsonify({
        'treks':[trek.to_dict() for trek in treks],
        'users':[user.to_dict(full=True) for user in users],
        'staff':[staff.to_dict(full=True) for staff in staffs]
    })


@admin_bp.route('/treks', methods=['GET'])
@admin_required
def get_treks():
    query = request.args.get('q', '').strip()
    treks = Trek.query
    if query:
        treks = treks.filter(Trek.name.ilike(f'%{query}%') | Trek.location.ilike(f'%{query}%'))
    return jsonify([trek.to_dict() for trek in treks.order_by(Trek.created_at.desc()).all()]), 200

@admin_bp.route('/treks', methods=['POST'])
@admin_required
def create_trek():
    data = request.get_json()
    try:
        trek = Trek(
            name=data['name'],
            location=data['location'],
            difficulty=data['difficulty'],
            total_slots=int(data['total_slots']),
            available_slots=int(data['total_slots']),
            duration=int(data.get('duration', 1)),
            staff_id=data.get('staff_id') or None,
            status=data.get('status') or 'Pending',
            start_date=date.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=  date.fromisoformat(data['end_date']) if data.get('end_date')   else None,
            description=data.get('description',''), 
            highlights=data.get('highlights',''),
            included=data.get('included',''),
            not_included=data.get('not_included',''),
            altitude=data.get('altitude'), 
            price=float(data.get('price',0)),
            meeting_point=data.get('meeting_point',''), 
            equipment_needed=data.get('equipment_needed',''),
            min_age=int(data.get('min_age',10)), 
            max_age=int(data.get('max_age',65)),
        )
        db.session.add(trek); 
        db.session.commit(); 
        cache.clear()
        return jsonify({'message':'Trek created','trek':trek.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@admin_bp.route('/treks/<int:trek_id>', methods=['PUT'])
@admin_required
def update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    has_booking = any(b.status=='Booked' for b in trek.bookings)
    if has_booking and trek.status in ['Started','Completed']:
        return jsonify({'error':'Cannot modify trek with active bookings or if trek is already started or completed'}), 400
    data = request.get_json()
    for f in ('name','location','difficulty','description','highlights','included',
              'not_included','meeting_point','equipment_needed','status'):
        if f in data: setattr(trek, f, data[f])
    if 'duration' in data: trek.duration = int(data['duration'])
    if 'altitude' in data: trek.altitude = data['altitude']
    if 'price' in data: trek.price = float(data['price'])
    if 'min_age' in data: trek.min_age = int(data['min_age'])
    if 'max_age' in data: trek.max_age = int(data['max_age'])
    if 'staff_id' in data: trek.staff_id  = data['staff_id'] or None
    if 'total_slots' in data:
        booked = len([b for b in trek.bookings if b.status == 'Booked'])
        new_total = int(data['total_slots'])
        if new_total < booked: return jsonify({'error': f'Cannot reduce below {booked} booked'}), 400
        trek.total_slots = new_total; trek.available_slots = new_total - booked
    if data.get('start_date'): trek.start_date = date.fromisoformat(data['start_date'])
    if data.get('end_date'): trek.end_date   = date.fromisoformat(data['end_date'])

    db.session.commit(); 
    cache.clear()
    return jsonify({'message':'Updated','trek':trek.to_dict()}), 200

@admin_bp.route('/treks/<int:trek_id>', methods=['DELETE'])
@admin_required
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    has_booking = any(b.status=='Booked' for b in trek.bookings)
    if has_booking or trek.status in ['Started','Completed']:
        return jsonify({'error':'Cannot delete trek with active bookings or if trek is already started or completed'}), 400
    db.session.delete(trek); 
    db.session.commit(); 
    cache.clear()
    return jsonify({'message':'Trek deleted'}), 200


@admin_bp.route('/treks/<int:trek_id>/assign-staff', methods=['POST']) 
@admin_required
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    data = request.get_json()
    staff_id = data.get('staff_id')
    if not staff_id:
        return jsonify({'error':'Staff ID is required'}), 400
    else:
        staff = User.query.filter_by(id=staff_id, role='staff').first()
        if not staff:
            return jsonify({'error':'Staff not found'}), 404
        trek.staff_id = staff.id or None
        db.session.commit(); 
        cache.clear()
        return jsonify({'message':'Staff assigned','trek':trek.to_dict()}), 200
    

##################   Staff CRUD   ####################

@admin_bp.route('/staff', methods=['GET'])
@admin_required
def get_staff():
    query = request.args.get('q', '').strip()
    staffs = User.query.filter_by(role='staff')
    if query:
        staffs = staffs.filter(User.name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%') | User.username.ilike(f'%{query}%'))
    result = []
    for staff in staffs.all():
        staff_info = staff.to_dict(full=True)
        staff_info['assigned_treks'] = [trek.to_dict() for trek in staff.assigned_treks]
        result.append(staff_info)
    return jsonify(result), 200

@admin_bp.route('/staff', methods=['POST'])
@admin_required
def create_staff():
    data = request.get_json()
    name = data.get('name').strip()
    username = data.get('username').strip()
    email = data.get('email').strip()
    password = data.get('password').strip()
    role = data.get('role', 'staff')  # default role is 'staff'
    phone = data.get('phone','')
    bio = data.get('bio','')

    if not all([name, username, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'Username or email already exists'}), 409

    try:
        new_staff = User(name=name,username=username,email=email,role=role,phone=phone,bio=bio)
        new_staff.set_password(password)

        staff = StaffInfo(
            specialization=data.get('specialization',''),
            years_experience=int(data.get('years_experience',0)),
            certification=data.get('certifications') or data.get('certification', ''),
            language=data.get('languages') or data.get('language','Hindi, English')
        )
        new_staff.staff_info = staff
        db.session.add(new_staff)
        db.session.commit()
        return jsonify({'message':'Staff created','staff':new_staff.to_dict(full=True)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@admin_bp.route('/staff/<int:staff_id>', methods=['PUT'])
@admin_required
def update_staff(staff_id): 
    staff = User.query.filter_by(id=staff_id, role='staff').first_or_404()
    data = request.get_json()
    for f in ('name','email','phone','bio'):
        if f in data: setattr(staff, f, data[f])
    if 'password' in data and data['password'].strip():
        staff.set_password(data['password'].strip())
    if staff.staff_info:
        for f in ('specialization','years_experience','certification','language'):
            if f in data: setattr(staff.staff_info, f, data[f])
    db.session.commit(); 
    cache.clear()
    return jsonify({'message':'Staff updated','staff':staff.to_dict(full=True)}), 200

@admin_bp.route('/staff/<int:staff_id>', methods=['DELETE'])
@admin_required
def delete_staff(staff_id):
    staff = User.query.filter_by(id=staff_id, role='staff').first_or_404()
    Trek.query.filter_by(staff_id=staff.id).update({'staff_id': None})
    db.session.delete(staff)
    db.session.commit()
    cache.clear()
    return jsonify({'message':'Staff deleted'}), 200


##### User Management #####


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    query = request.args.get('q', '')
    role = request.args.get('role', 'user')
    status = request.args.get('status', '')

    users = User.query.filter_by(role=role)
    if status=='active':
        users = users.filter(User.status=='active')
    if status=='blacklisted':
        users = users.filter(User.status=='blacklisted')
    if query:
        users = users.filter(User.name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%') | User.username.ilike(f'%{query}%'))
    result = []
    for user in users.all():
        user_info = user.to_dict(full=True)
        user_info['booking_count'] = Booking.query.filter_by(user_id=user.id).count()
        user_info['treks_booked'] = [booking.trek.to_dict() for booking in user.bookings if booking.status=='Booked']   
        result.append(user_info)
    return jsonify(result), 200

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin': return jsonify({'error':'Cannot modify admin'}), 403
    data = request.get_json()
    status = data.get('status')
    if status not in ['active', 'blacklisted']:
        return jsonify({'error': 'Invalid status'}), 400
    user.status = status
    db.session.commit()
    return jsonify({'message': 'User status updated'}), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin': return jsonify({'error':'Cannot delete admin'}), 403
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message':'User deleted'}), 200


@admin_bp.route('/bookings', methods=['GET'])
@admin_required
def get_all_bookings():
    trek_id = request.args.get('trek_id'); 
    status = request.args.get('status')
    q = Booking.query
    if trek_id: q = q.filter_by(trek_id=int(trek_id))
    if status:  q = q.filter_by(status=status)
    return jsonify([b.to_dict() for b in q.order_by(Booking.booking_date.desc()).all()]), 200


@admin_bp.route('/reviews', methods=['GET'])
@admin_required
def get_reviews():
    return jsonify([r.to_dict() for r in Review.query.order_by(Review.created_at.desc()).all()]), 200

@admin_bp.route('/reviews/<int:rid>', methods=['DELETE'])
@admin_required
def delete_review(rid):
    r = Review.query.get_or_404(rid); 
    db.session.delete(r); 
    db.session.commit()
    return jsonify({'message':'Deleted'}), 200
