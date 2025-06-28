from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from models import User, UserRole, db

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                user = User.query.get(user_id)
                
                if not user or not user.is_active:
                    return jsonify({'error': 'User not found or inactive'}), 401
                
                if user.role not in allowed_roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Authentication required'}), 401
        return decorated_function
    return decorator

def admin_required(f):
    return role_required(UserRole.ADMIN)(f)

def coach_required(f):
    return role_required(UserRole.COACH, UserRole.ADMIN)(f)

def client_required(f):
    return role_required(UserRole.CLIENT, UserRole.COACH, UserRole.ADMIN)(f)

def get_current_user():
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        return User.query.get(user_id)
    except:
        return None

def log_audit_action(action, resource_type=None, resource_id=None, details=None):
    from models import AuditLog
    
    user = get_current_user()
    audit_log = AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    db.session.add(audit_log)
    db.session.commit()
