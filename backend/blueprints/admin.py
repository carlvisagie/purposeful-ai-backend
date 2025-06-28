from flask import Blueprint, request, jsonify, render_template_string
from flask_jwt_extended import jwt_required, get_jwt_identity
from blueprints.auth import role_required
from models import db, User, Session, CrisisAlert, Payment, UserRole, CrisisLevel
from datetime import datetime, timedelta, timezone
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

ADMIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Purposeful Live</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .header { background: #34495e; color: white; padding: 1rem 2rem; }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 2rem; font-weight: bold; color: #2980b9; }
        .stat-label { color: #7f8c8d; margin-top: 0.5rem; }
        .section { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .section h2 { margin-bottom: 1rem; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #ecf0f1; }
        .table th { background: #f8f9fa; font-weight: 600; }
        .badge { padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: 500; }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .btn { padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; font-size: 0.9rem; }
        .btn-primary { background: #3498db; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-success { background: #27ae60; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Admin Dashboard</h1>
        <p>System administration and business analytics</p>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_users }}</div>
                <div class="stat-label">Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.active_subscriptions }}</div>
                <div class="stat-label">Active Subscriptions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${{ stats.monthly_revenue }}</div>
                <div class="stat-label">Monthly Revenue</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.crisis_alerts }}</div>
                <div class="stat-label">Crisis Alerts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_sessions }}</div>
                <div class="stat-label">Total Sessions</div>
            </div>
        </div>
        
        <div class="section">
            <h2>User Management</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Subscription</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user.name }}</td>
                        <td>{{ user.email }}</td>
                        <td><span class="badge badge-{{ 'success' if user.role == 'admin' else 'warning' }}">{{ user.role }}</span></td>
                        <td>{{ user.subscription_tier or 'None' }}</td>
                        <td><span class="badge badge-{{ 'success' if user.is_active else 'danger' }}">{{ 'Active' if user.is_active else 'Inactive' }}</span></td>
                        <td>
                            <a href="/admin/api/user/{{ user.id }}" class="btn btn-primary">View</a>
                            {% if not user.is_active %}
                            <a href="/admin/api/user/{{ user.id }}/activate" class="btn btn-success">Activate</a>
                            {% else %}
                            <a href="/admin/api/user/{{ user.id }}/deactivate" class="btn btn-danger">Deactivate</a>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Recent Payments</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>User</th>
                        <th>Amount</th>
                        <th>Tier</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for payment in recent_payments %}
                    <tr>
                        <td>{{ payment.created_at }}</td>
                        <td>{{ payment.user_name }}</td>
                        <td>${{ payment.amount }}</td>
                        <td>{{ payment.subscription_tier }}</td>
                        <td><span class="badge badge-{{ 'success' if payment.status == 'succeeded' else 'warning' }}">{{ payment.status }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Crisis Alerts</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>User</th>
                        <th>Level</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for alert in crisis_alerts %}
                    <tr>
                        <td>{{ alert.created_at }}</td>
                        <td>{{ alert.user_name }}</td>
                        <td><span class="badge badge-{{ 'danger' if alert.crisis_level == 'critical' else 'warning' }}">{{ alert.crisis_level }}</span></td>
                        <td><span class="badge badge-{{ 'success' if alert.resolved else 'danger' }}">{{ 'Resolved' if alert.resolved else 'Active' }}</span></td>
                        <td>
                            <a href="/admin/api/alert/{{ alert.id }}" class="btn btn-primary">View</a>
                            {% if not alert.resolved %}
                            <a href="/admin/api/alert/{{ alert.id }}/resolve" class="btn btn-success">Resolve</a>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@admin_bp.route('/')
@role_required(UserRole.ADMIN)
def dashboard():
    try:
        total_users = User.query.count()
        active_subscriptions = User.query.filter_by(subscription_active=True).count()
        
        monthly_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.status == 'succeeded',
            Payment.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ).scalar() or 0
        monthly_revenue = monthly_revenue / 100
        
        crisis_alerts_count = CrisisAlert.query.filter_by(resolved=False).count()
        total_sessions = Session.query.count()
        
        stats = {
            'total_users': total_users,
            'active_subscriptions': active_subscriptions,
            'monthly_revenue': round(monthly_revenue, 2),
            'crisis_alerts': crisis_alerts_count,
            'total_sessions': total_sessions
        }
        
        users = db.session.query(User).order_by(User.created_at.desc()).limit(20).all()
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}",
                'email': user.email,
                'role': user.role.value,
                'subscription_tier': user.subscription_tier.value if user.subscription_tier else None,
                'is_active': user.is_active
            })
        
        recent_payments = db.session.query(
            Payment.id,
            Payment.created_at,
            Payment.amount,
            Payment.subscription_tier,
            Payment.status,
            User.first_name,
            User.last_name
        ).join(User).order_by(Payment.created_at.desc()).limit(10).all()
        
        payments_data = []
        for payment in recent_payments:
            payments_data.append({
                'id': payment.id,
                'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M'),
                'user_name': f"{payment.first_name} {payment.last_name}",
                'amount': payment.amount / 100,
                'subscription_tier': payment.subscription_tier.value,
                'status': payment.status
            })
        
        crisis_alerts = db.session.query(
            CrisisAlert.id,
            CrisisAlert.created_at,
            CrisisAlert.crisis_level,
            CrisisAlert.resolved,
            User.first_name,
            User.last_name
        ).join(User).order_by(CrisisAlert.created_at.desc()).limit(10).all()
        
        alerts_data = []
        for alert in crisis_alerts:
            alerts_data.append({
                'id': alert.id,
                'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M'),
                'user_name': f"{alert.first_name} {alert.last_name}",
                'crisis_level': alert.crisis_level.value,
                'resolved': alert.resolved
            })
        
        return render_template_string(ADMIN_DASHBOARD_HTML,
                                    stats=stats,
                                    users=users_data,
                                    recent_payments=payments_data,
                                    crisis_alerts=alerts_data)
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return jsonify({'error': 'Dashboard loading failed'}), 500

@admin_bp.route('/api/users', methods=['GET'])
@role_required(UserRole.ADMIN)
def get_all_users():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        users = User.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Users retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

@admin_bp.route('/api/user/<int:user_id>', methods=['GET'])
@role_required(UserRole.ADMIN)
def get_user_details(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        sessions = Session.query.filter_by(user_id=user_id).order_by(
            Session.created_at.desc()
        ).limit(10).all()
        
        payments = Payment.query.filter_by(user_id=user_id).order_by(
            Payment.created_at.desc()
        ).all()
        
        alerts = CrisisAlert.query.filter_by(user_id=user_id).order_by(
            CrisisAlert.created_at.desc()
        ).all()
        
        return jsonify({
            'user': user.to_dict(),
            'sessions': [session.to_dict() for session in sessions],
            'payments': [payment.to_dict() for payment in payments],
            'crisis_alerts': [alert.to_dict() for alert in alerts]
        }), 200
        
    except Exception as e:
        logger.error(f"User details error: {e}")
        return jsonify({'error': 'Failed to retrieve user details'}), 500

@admin_bp.route('/api/user/<int:user_id>/deactivate', methods=['POST'])
@role_required(UserRole.ADMIN)
def deactivate_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = False
        db.session.commit()
        
        logger.info(f"User {user_id} deactivated by admin")
        
        return jsonify({'message': 'User deactivated successfully'}), 200
        
    except Exception as e:
        logger.error(f"User deactivation error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to deactivate user'}), 500

@admin_bp.route('/api/user/<int:user_id>/activate', methods=['POST'])
@role_required(UserRole.ADMIN)
def activate_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = True
        db.session.commit()
        
        logger.info(f"User {user_id} activated by admin")
        
        return jsonify({'message': 'User activated successfully'}), 200
        
    except Exception as e:
        logger.error(f"User activation error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to activate user'}), 500

@admin_bp.route('/api/analytics', methods=['GET'])
@role_required(UserRole.ADMIN)
def get_analytics():
    try:
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        new_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        revenue_by_tier = db.session.query(
            Payment.subscription_tier,
            db.func.sum(Payment.amount).label('total')
        ).filter(
            Payment.status == 'succeeded',
            Payment.created_at >= thirty_days_ago
        ).group_by(Payment.subscription_tier).all()
        
        session_stats = db.session.query(
            db.func.count(Session.id).label('total_sessions'),
            db.func.avg(Session.client_rating).label('avg_rating')
        ).filter(Session.created_at >= thirty_days_ago).first()
        
        crisis_stats = db.session.query(
            CrisisAlert.crisis_level,
            db.func.count(CrisisAlert.id).label('count')
        ).filter(CrisisAlert.created_at >= thirty_days_ago).group_by(CrisisAlert.crisis_level).all()
        
        return jsonify({
            'new_users_30_days': new_users,
            'revenue_by_tier': [{'tier': r.subscription_tier.value, 'revenue': r.total / 100} for r in revenue_by_tier],
            'session_stats': {
                'total_sessions': session_stats.total_sessions or 0,
                'avg_rating': round(float(session_stats.avg_rating or 0), 2)
            },
            'crisis_stats': [{'level': c.crisis_level.value, 'count': c.count} for c in crisis_stats]
        }), 200
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500
