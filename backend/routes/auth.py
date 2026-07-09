from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_current_user
from extensions import db
from models.models import User, TrekkerInfo, StaffInfo, Booking, Trek

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/check', methods=['GET'])
def check():
    field = request.args.get('field')
    value = request.args.get('value').strip()
    if field not in ['username', 'email'] or not value:
        return jsonify({'error': 'Invalid field or value'}), 400
    taken = User.query.filter(getattr(User, field) == value).first() is not None
    return jsonify({'available': not taken, 'field':field}), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name').strip()
    username = data.get('username').strip()
    email = data.get('email').strip()
    password = data.get('password').strip()
    role = 'user'  # Only 'user' (Trekker) role can self-register. Admin and Staff must be created programmatically/by admin.
    phone = data.get('phone','')
    bio = data.get('bio','')

    if not all([name, username, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'Username or email already exists'}), 409
    try:
        new_user = User(name=name,username=username,email=email,role=role,phone=phone,bio=bio)
        new_user.set_password(password)

        trekker = TrekkerInfo(
            experience_level=data.get('experience_level', 'Beginner'),
            fitness_level=data.get('fitness_level', 'Medium'),
            preferred_difficulty=data.get('preferred_difficulty', 'Easy'),
            emergency_contact=data.get('emergency_contact', ''),
            emergency_phone=data.get('emergency_phone', ''),
            medical_notes=data.get('medical_notes', ''),
        )
        new_user.trekker_info = trekker
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error':'Invalid credentials'}), 401
    if user.status == 'blacklisted':
        return jsonify({'error': 'Account blacklisted. Contact admin'}), 403
    
    token = create_access_token(identity=user)

    return jsonify(
        {
            'message': 'Login successful', 
            'token': token, 
            'user': user.to_dict(full=True)
        }
    ), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user = get_current_user()
    return jsonify(user.to_dict(full=True)), 200



@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user = get_current_user()
    data = request.get_json()

    # Common profile fields
    if 'name'  in data and data['name']:  user.name  = data['name']
    if 'phone' in data:                user.phone = data['phone']
    if 'bio'   in data:                user.bio   = data['bio']
    if 'email' in data and data['email']:
        ex = User.query.filter_by(email=data['email']).first()
        if ex and ex.id != user.id: return jsonify({'error': 'Email in use'}), 409
        user.email = data['email']
    if 'password' in data and data['password']:
        user.set_password(data['password'])

    # Trekker-specific
    if user.trekker_info and user.role == 'user':
        t = user.trekker_info
        for f in ('experience_level', 'fitness_level', 'preferred_difficulty',
                  'emergency_contact', 'emergency_phone', 'medical_notes'):
            if f in data: setattr(t, f, data[f])

    # Staff-specific
    if user.staff_info and user.role == 'staff':
        s = user.staff_info
        if 'specialization' in data: s.specialization = data['specialization']
        if 'certifications' in data: s.certification = data['certifications']
        if 'certification' in data: s.certification = data['certification']
        if 'years_experience' in data: s.years_experience = int(data['years_experience'])
        if 'languages' in data: s.language = data['languages']
        if 'language' in data: s.language = data['language']

    db.session.commit()
    return jsonify({'message': 'Profile updated', 'user': user.to_dict(full=True)}), 200

    
