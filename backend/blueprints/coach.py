from flask import Blueprint, request, jsonify, render_template_string
from flask_jwt_extended import jwt_required, get_jwt_identity
from blueprints.auth import role_required
from models import db, User, Session, CrisisAlert, UserRole, CrisisLevel
from services.crisis_service import CrisisDetectionService
from datetime import datetime, timedelta, timezone
import logging

coach_bp = Blueprint('coach', __name__)
logger = logging.getLogger(__name__)

COACH_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coach Dashboard - Purposeful Live</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 1rem 2rem; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2rem; font-weight: bold; color: #3498db; }
        .stat-label { color: #7f8c8d; margin-top: 0.5rem; }
        .section { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .section h2 { margin-bottom: 1rem; color: #2c3e50; }
        .alert-critical { border-left: 4px solid #e74c3c; background: #fdf2f2; }
        .alert-elevated { border-left: 4px solid #f39c12; background: #fef9e7; }
        .client-list { list-style: none; }
        .client-item { padding: 1rem; border-bottom: 1px solid #ecf0f1; display: flex; justify-content: between; align-items: center; }
        .client-info { flex: 1; }
        .client-name { font-weight: bold; color: #2c3e50; }
        .client-status { color: #7f8c8d; font-size: 0.9rem; }
        .btn { padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-primary { background: #3498db; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-warning { background: #f39c12; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Coach Dashboard</h1>
        <p>Welcome back, Coach. Here's your client overview.</p>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_clients }}</div>
                <div class="stat-label">Total Clients</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.active_sessions }}</div>
                <div class="stat-label">Active Sessions Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.crisis_alerts }}</div>
                <div class="stat-label">Active Crisis Alerts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.avg_rating }}</div>
                <div class="stat-label">Average Session Rating</div>
            </div>
        </div>
        
        {% if crisis_alerts %}
        <div class="section alert-critical">
            <h2>🚨 Crisis Alerts Requiring Immediate Attention</h2>
            {% for alert in crisis_alerts %}
            <div class="client-item">
                <div class="client-info">
                    <div class="client-name">{{ alert.user_name }}</div>
                    <div class="client-status">{{ alert.crisis_level }} - {{ alert.created_at }}</div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem;">{{ alert.trigger_text[:100] }}...</div>
                </div>
                <a href="/coach/alert/{{ alert.id }}" class="btn btn-danger">View Alert</a>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <div class="section">
            <h2>Recent Client Sessions</h2>
            <ul class="client-list">
                {% for session in recent_sessions %}
                <li class="client-item">
                    <div class="client-info">
                        <div class="client-name">{{ session.user_name }}</div>
                        <div class="client-status">{{ session.created_at }} - Risk: {{ session.mortality_risk }}</div>
                    </div>
                    <a href="/coach/session/{{ session.id }}" class="btn btn-primary">View Session</a>
                </li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="section">
            <h2>Client Management</h2>
            <ul class="client-list">
                {% for client in clients %}
                <li class="client-item">
                    <div class="client-info">
                        <div class="client-name">{{ client.name }}</div>
                        <div class="client-status">{{ client.subscription_tier }} - Last session: {{ client.last_session }}</div>
                    </div>
                    <a href="/coach/client/{{ client.id }}" class="btn btn-primary">View Profile</a>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
"""

@coach_bp.route('/')
@role_required(UserRole.COACH)
def dashboard():
    try:
        today = datetime.now(timezone.utc).date()
        
        total_clients = User.query.filter_by(role=UserRole.CLIENT).count()
        
        active_sessions = Session.query.filter(
            Session.created_at >= datetime.combine(today, datetime.min.time().replace(tzinfo=timezone.utc))
        ).count()
        
        crisis_alerts = CrisisAlert.query.filter_by(resolved=False).all()
        
        avg_rating = db.session.query(db.func.avg(Session.client_rating)).filter(
            Session.client_rating.isnot(None)
        ).scalar() or 0
        
        recent_sessions = db.session.query(
            Session.id,
            Session.created_at,
            Session.mortality_risk,
            User.first_name,
            User.last_name
        ).join(User).order_by(Session.created_at.desc()).limit(10).all()
        
        clients = db.session.query(
            User.id,
            User.first_name,
            User.last_name,
            User.subscription_tier,
            db.func.max(Session.created_at).label('last_session')
        ).outerjoin(Session).filter(User.role == UserRole.CLIENT).group_by(User.id).all()
        
        stats = {
            'total_clients': total_clients,
            'active_sessions': active_sessions,
            'crisis_alerts': len(crisis_alerts),
            'avg_rating': round(float(avg_rating), 1) if avg_rating else 0
        }
        
        crisis_alerts_data = []
        for alert in crisis_alerts:
            user = User.query.get(alert.user_id)
            crisis_alerts_data.append({
                'id': alert.id,
                'user_name': f"{user.first_name} {user.last_name}",
                'crisis_level': alert.crisis_level.value.title(),
                'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M'),
                'trigger_text': alert.trigger_text
            })
        
        recent_sessions_data = []
        for session in recent_sessions:
            recent_sessions_data.append({
                'id': session.id,
                'user_name': f"{session.first_name} {session.last_name}",
                'created_at': session.created_at.strftime('%Y-%m-%d %H:%M'),
                'mortality_risk': session.mortality_risk.value if session.mortality_risk else 'Unknown'
            })
        
        clients_data = []
        for client in clients:
            clients_data.append({
                'id': client.id,
                'name': f"{client.first_name} {client.last_name}",
                'subscription_tier': client.subscription_tier.value if client.subscription_tier else 'None',
                'last_session': client.last_session.strftime('%Y-%m-%d') if client.last_session else 'Never'
            })
        
        return render_template_string(COACH_DASHBOARD_HTML, 
                                    stats=stats,
                                    crisis_alerts=crisis_alerts_data,
                                    recent_sessions=recent_sessions_data,
                                    clients=clients_data)
        
    except Exception as e:
        logger.error(f"Coach dashboard error: {e}")
        return jsonify({'error': 'Dashboard loading failed'}), 500

@coach_bp.route('/api/clients', methods=['GET'])
@role_required(UserRole.COACH)
def get_clients():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        clients = User.query.filter_by(role=UserRole.CLIENT).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'clients': [client.to_dict() for client in clients.items],
            'total': clients.total,
            'pages': clients.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Clients retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve clients'}), 500

@coach_bp.route('/api/client/<int:client_id>/sessions', methods=['GET'])
@role_required(UserRole.COACH)
def get_client_sessions(client_id):
    try:
        sessions = Session.query.filter_by(user_id=client_id).order_by(
            Session.created_at.desc()
        ).all()
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions]
        }), 200
        
    except Exception as e:
        logger.error(f"Client sessions retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve client sessions'}), 500

@coach_bp.route('/api/crisis_alerts', methods=['GET'])
@role_required(UserRole.COACH)
def get_crisis_alerts():
    try:
        alerts = CrisisDetectionService.get_active_alerts()
        return jsonify({'alerts': alerts}), 200
        
    except Exception as e:
        logger.error(f"Crisis alerts retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve crisis alerts'}), 500

@coach_bp.route('/api/crisis_alert/<int:alert_id>/resolve', methods=['POST'])
@role_required(UserRole.COACH)
def resolve_crisis_alert(alert_id):
    try:
        data = request.get_json()
        resolution_notes = data.get('resolution_notes', '')
        
        success = CrisisDetectionService.resolve_alert(alert_id, resolution_notes)
        
        if success:
            return jsonify({'message': 'Alert resolved successfully'}), 200
        else:
            return jsonify({'error': 'Alert not found'}), 404
            
    except Exception as e:
        logger.error(f"Crisis alert resolution error: {e}")
        return jsonify({'error': 'Failed to resolve alert'}), 500
