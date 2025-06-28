from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, User, Session, Diagnostic, CrisisEvent
from sqlalchemy import desc

coach = Blueprint('coach', __name__)

@coach.route('/clients', methods=['GET'])
@login_required
def get_clients():
    if current_user.role not in ['coach', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    clients = User.query.filter_by(role='client').all()
    return jsonify([{
        'id': client.id,
        'email': client.email,
        'created_at': client.created_at.isoformat(),
        'is_active': client.is_active,
        'age': client.age,
        'emergency_contact': client.emergency_contact
    } for client in clients])

@coach.route('/crisis-events', methods=['GET'])
@login_required
def get_crisis_events():
    if current_user.role not in ['coach', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    events = CrisisEvent.query.filter_by(resolved=False).order_by(desc(CrisisEvent.severity)).all()
    return jsonify([{
        'id': event.id,
        'user_id': event.user_id,
        'severity': event.severity,
        'flags': event.flags,
        'escalated': event.escalated,
        'created_at': event.created_at.isoformat()
    } for event in events])

@coach.route('/sessions', methods=['GET'])
@login_required
def get_sessions():
    if current_user.role not in ['coach', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    sessions = Session.query.order_by(desc(Session.created_at)).limit(50).all()
    return jsonify([{
        'id': session.id,
        'user_id': session.user_id,
        'tier': session.tier,
        'payment_status': session.payment_status,
        'created_at': session.created_at.isoformat()
    } for session in sessions])

@coach.route('/crisis-events/<int:event_id>/resolve', methods=['POST'])
@login_required
def resolve_crisis_event(event_id):
    if current_user.role not in ['coach', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    event = CrisisEvent.query.get_or_404(event_id)
    event.resolved = True
    db.session.commit()
    
    return jsonify({'message': 'Crisis event resolved'}), 200

@coach.route('/analytics', methods=['GET'])
@login_required
def get_analytics():
    if current_user.role not in ['coach', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    total_clients = User.query.filter_by(role='client').count()
    active_crises = CrisisEvent.query.filter_by(resolved=False).count()
    total_sessions = Session.query.count()
    paid_sessions = Session.query.filter_by(payment_status='completed').count()
    
    return jsonify({
        'total_clients': total_clients,
        'active_crises': active_crises,
        'total_sessions': total_sessions,
        'paid_sessions': paid_sessions,
        'conversion_rate': (paid_sessions / total_sessions * 100) if total_sessions > 0 else 0
    })
