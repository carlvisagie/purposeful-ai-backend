from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, User, Session, Diagnostic, CrisisEvent
from sqlalchemy import desc, func

admin = Blueprint('admin', __name__)

@admin.route('/users', methods=['GET'])
@login_required
def get_all_users():
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat(),
        'is_active': user.is_active
    } for user in users])

@admin.route('/users/<int:user_id>/role', methods=['PUT'])
@login_required
def update_user_role(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    new_role = data.get('role')
    
    if new_role not in ['client', 'coach', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400
    
    user = User.query.get_or_404(user_id)
    user.role = new_role
    db.session.commit()
    
    return jsonify({'message': 'User role updated successfully'}), 200

@admin.route('/users/<int:user_id>/deactivate', methods=['POST'])
@login_required
def deactivate_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'User deactivated successfully'}), 200

@admin.route('/system-stats', methods=['GET'])
@login_required
def get_system_stats():
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    total_users = User.query.count()
    total_clients = User.query.filter_by(role='client').count()
    total_coaches = User.query.filter_by(role='coach').count()
    total_sessions = Session.query.count()
    total_crises = CrisisEvent.query.count()
    unresolved_crises = CrisisEvent.query.filter_by(resolved=False).count()
    
    revenue_stats = db.session.query(
        Session.payment_status,
        func.count(Session.id).label('count')
    ).group_by(Session.payment_status).all()
    
    return jsonify({
        'users': {
            'total': total_users,
            'clients': total_clients,
            'coaches': total_coaches,
            'admins': total_users - total_clients - total_coaches
        },
        'sessions': {
            'total': total_sessions
        },
        'crises': {
            'total': total_crises,
            'unresolved': unresolved_crises
        },
        'revenue': {status: count for status, count in revenue_stats}
    })

@admin.route('/crisis-events/all', methods=['GET'])
@login_required
def get_all_crisis_events():
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    events = CrisisEvent.query.order_by(desc(CrisisEvent.created_at)).limit(100).all()
    return jsonify([{
        'id': event.id,
        'user_id': event.user_id,
        'severity': event.severity,
        'flags': event.flags,
        'escalated': event.escalated,
        'resolved': event.resolved,
        'created_at': event.created_at.isoformat()
    } for event in events])
