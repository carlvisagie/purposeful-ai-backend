from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import check_password_hash
from models import db, User, Client, Coach, UserRole
from auth import log_audit_action
import re
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        password = data['password']
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        try:
            role = UserRole(data['role'])
        except ValueError:
            return jsonify({'error': 'Invalid role'}), 400
        
        user = User(
            email=email,
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            role=role,
            phone=data.get('phone', '').strip() or None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        if role == UserRole.CLIENT:
            client = Client(
                id=user.id,
                emergency_contact_name=data.get('emergency_contact_name', '').strip() or None,
                emergency_contact_phone=data.get('emergency_contact_phone', '').strip() or None,
                emergency_contact_relationship=data.get('emergency_contact_relationship', '').strip() or None
            )
            db.session.add(client)
        elif role == UserRole.COACH:
            coach = Coach(
                id=user.id,
                license_number=data.get('license_number', '').strip() or None,
                specializations=data.get('specializations', '').strip() or None,
                bio=data.get('bio', '').strip() or None
            )
            db.session.add(coach)
        
        db.session.commit()
        
        log_audit_action('user_registered', 'user', user.id, {'role': role.value})
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(data['password']):
            log_audit_action('login_failed', 'user', None, {'email': email})
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        log_audit_action('login_success', 'user', user.id)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        access_token = create_access_token(identity=user_id)
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        user_id = get_jwt_identity()
        log_audit_action('logout', 'user', user_id)
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile_data = user.to_dict()
        
        if user.role == UserRole.CLIENT and hasattr(user, 'client_profile'):
            profile_data['client_profile'] = user.client_profile.to_dict()
        elif user.role == UserRole.COACH and hasattr(user, 'coach_profile'):
            profile_data['coach_profile'] = user.coach_profile.to_dict()
        
        return jsonify(profile_data), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip() or None
        
        if user.role == UserRole.CLIENT and hasattr(user, 'client_profile'):
            client = user.client_profile
            if 'emergency_contact_name' in data:
                client.emergency_contact_name = data['emergency_contact_name'].strip() or None
            if 'emergency_contact_phone' in data:
                client.emergency_contact_phone = data['emergency_contact_phone'].strip() or None
            if 'emergency_contact_relationship' in data:
                client.emergency_contact_relationship = data['emergency_contact_relationship'].strip() or None
            if 'medical_conditions' in data:
                client.medical_conditions = data['medical_conditions'].strip() or None
            if 'medications' in data:
                client.medications = data['medications'].strip() or None
            if 'allergies' in data:
                client.allergies = data['allergies'].strip() or None
        
        elif user.role == UserRole.COACH and hasattr(user, 'coach_profile'):
            coach = user.coach_profile
            if 'license_number' in data:
                coach.license_number = data['license_number'].strip() or None
            if 'specializations' in data:
                coach.specializations = data['specializations'].strip() or None
            if 'bio' in data:
                coach.bio = data['bio'].strip() or None
            if 'hourly_rate' in data:
                coach.hourly_rate = data['hourly_rate']
            if 'availability' in data:
                coach.availability = data['availability'].strip() or None
        
        db.session.commit()
        
        log_audit_action('profile_updated', 'user', user_id)
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500
