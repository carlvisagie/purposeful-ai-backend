from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import re

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'client')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Registration successful', 'user_id': user.id}), 201

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    login_user(user)
    return jsonify({
        'message': 'Login successful',
        'user': {'id': user.id, 'email': user.email, 'role': user.role}
    }), 200

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

@auth.route('/profile', methods=['GET'])
@login_required
def profile():
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'role': current_user.role,
        'created_at': current_user.created_at.isoformat()
    }), 200

@auth.route('/update-profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    
    if 'age' in data:
        current_user.age = data['age']
    if 'chronic_conditions' in data:
        current_user.chronic_conditions = data['chronic_conditions']
    if 'habits' in data:
        current_user.habits = data['habits']
    if 'emergency_contact' in data:
        current_user.emergency_contact = data['emergency_contact']
    
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200
