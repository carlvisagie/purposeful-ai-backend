from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, User, Client, Coach, Session, Payment, CrisisAlert, UserRole, PaymentStatus
from auth import get_current_user, role_required, log_audit_action
from datetime import datetime, timedelta
from sqlalchemy import func, desc

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/coach/overview', methods=['GET'])
@role_required(UserRole.COACH, UserRole.ADMIN)
def coach_overview():
    try:
        user = get_current_user()
        
        if user.role == UserRole.COACH:
            coach = Coach.query.get(user.id)
            if not coach:
                return jsonify({'error': 'Coach profile not found'}), 404
            
            assigned_clients = coach.assigned_clients
            client_ids = [c.id for c in assigned_clients]
        else:
            coach = None
            assigned_clients = Client.query.all()
            client_ids = [c.id for c in assigned_clients]
        
        total_clients = len(assigned_clients)
        
        active_sessions = Session.query.filter(
            Session.client_id.in_(client_ids),
            Session.ended_at.is_(None),
            Session.started_at.isnot(None)
        ).count()
        
        today = datetime.utcnow().date()
        sessions_today = Session.query.filter(
            Session.client_id.in_(client_ids),
            func.date(Session.created_at) == today
        ).count()
        
        active_crisis_alerts = CrisisAlert.query.filter(
            CrisisAlert.client_id.in_(client_ids),
            CrisisAlert.resolved_at.is_(None)
        ).count()
        
        recent_sessions = Session.query.filter(
            Session.client_id.in_(client_ids)
        ).order_by(desc(Session.created_at)).limit(5).all()
        
        client_risk_levels = db.session.query(
            Client.risk_level,
            func.count(Client.id).label('count')
        ).filter(Client.id.in_(client_ids)).group_by(Client.risk_level).all()
        
        risk_distribution = {level: count for level, count in client_risk_levels}
        
        return jsonify({
            'overview': {
                'total_clients': total_clients,
                'active_sessions': active_sessions,
                'sessions_today': sessions_today,
                'active_crisis_alerts': active_crisis_alerts,
                'risk_distribution': risk_distribution
            },
            'recent_sessions': [session.to_dict() for session in recent_sessions],
            'coach_info': coach.to_dict() if coach else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch coach overview'}), 500

@dashboard_bp.route('/coach/clients', methods=['GET'])
@role_required(UserRole.COACH, UserRole.ADMIN)
def get_coach_clients():
    try:
        user = get_current_user()
        
        if user.role == UserRole.COACH:
            coach = Coach.query.get(user.id)
            if not coach:
                return jsonify({'error': 'Coach profile not found'}), 404
            clients = coach.assigned_clients
        else:
            clients = Client.query.all()
        
        clients_data = []
        for client in clients:
            client_dict = client.to_dict()
            client_dict['user_info'] = client.user.to_dict()
            
            recent_session = Session.query.filter_by(
                client_id=client.id
            ).order_by(desc(Session.created_at)).first()
            
            client_dict['last_session'] = recent_session.to_dict() if recent_session else None
            
            active_alerts = CrisisAlert.query.filter_by(
                client_id=client.id
            ).filter(CrisisAlert.resolved_at.is_(None)).count()
            
            client_dict['active_crisis_alerts'] = active_alerts
            
            clients_data.append(client_dict)
        
        return jsonify({'clients': clients_data}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch clients'}), 500

@dashboard_bp.route('/coach/sessions', methods=['GET'])
@role_required(UserRole.COACH, UserRole.ADMIN)
def get_coach_sessions():
    try:
        user = get_current_user()
        
        query = Session.query
        
        if user.role == UserRole.COACH:
            coach = Coach.query.get(user.id)
            if not coach:
                return jsonify({'error': 'Coach profile not found'}), 404
            
            client_ids = [c.id for c in coach.assigned_clients]
            query = query.filter(Session.client_id.in_(client_ids))
        
        status = request.args.get('status')
        if status == 'active':
            query = query.filter(
                Session.started_at.isnot(None),
                Session.ended_at.is_(None)
            )
        elif status == 'completed':
            query = query.filter(Session.ended_at.isnot(None))
        elif status == 'scheduled':
            query = query.filter(
                Session.scheduled_at.isnot(None),
                Session.started_at.is_(None)
            )
        
        sessions = query.order_by(desc(Session.created_at)).limit(50).all()
        
        sessions_data = []
        for session in sessions:
            session_dict = session.to_dict()
            session_dict['client_name'] = f"{session.client.user.first_name} {session.client.user.last_name}"
            sessions_data.append(session_dict)
        
        return jsonify({'sessions': sessions_data}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch sessions'}), 500

@dashboard_bp.route('/admin/overview', methods=['GET'])
@role_required(UserRole.ADMIN)
def admin_overview():
    try:
        total_users = User.query.filter_by(is_active=True).count()
        total_clients = Client.query.count()
        total_coaches = Coach.query.count()
        
        today = datetime.utcnow().date()
        new_users_today = User.query.filter(
            func.date(User.created_at) == today
        ).count()
        
        active_sessions = Session.query.filter(
            Session.started_at.isnot(None),
            Session.ended_at.is_(None)
        ).count()
        
        total_revenue = db.session.query(
            func.sum(Payment.amount)
        ).filter_by(status=PaymentStatus.COMPLETED).scalar() or 0
        
        this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = db.session.query(
            func.sum(Payment.amount)
        ).filter(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.created_at >= this_month
        ).scalar() or 0
        
        active_crisis_alerts = CrisisAlert.query.filter(
            CrisisAlert.resolved_at.is_(None)
        ).count()
        
        user_growth = []
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=i)).date()
            count = User.query.filter(func.date(User.created_at) == date).count()
            user_growth.append({'date': date.isoformat(), 'count': count})
        
        user_growth.reverse()
        
        return jsonify({
            'overview': {
                'total_users': total_users,
                'total_clients': total_clients,
                'total_coaches': total_coaches,
                'new_users_today': new_users_today,
                'active_sessions': active_sessions,
                'total_revenue': float(total_revenue),
                'monthly_revenue': float(monthly_revenue),
                'active_crisis_alerts': active_crisis_alerts
            },
            'user_growth': user_growth
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch admin overview'}), 500

@dashboard_bp.route('/admin/users', methods=['GET'])
@role_required(UserRole.ADMIN)
def get_all_users():
    try:
        role_filter = request.args.get('role')
        status_filter = request.args.get('status', 'active')
        
        query = User.query
        
        if role_filter:
            try:
                role_enum = UserRole(role_filter)
                query = query.filter_by(role=role_enum)
            except ValueError:
                pass
        
        if status_filter == 'active':
            query = query.filter_by(is_active=True)
        elif status_filter == 'inactive':
            query = query.filter_by(is_active=False)
        
        users = query.order_by(desc(User.created_at)).limit(100).all()
        
        users_data = []
        for user in users:
            user_dict = user.to_dict()
            
            if user.role == UserRole.CLIENT and hasattr(user, 'client_profile'):
                user_dict['client_profile'] = user.client_profile.to_dict()
            elif user.role == UserRole.COACH and hasattr(user, 'coach_profile'):
                user_dict['coach_profile'] = user.coach_profile.to_dict()
            
            users_data.append(user_dict)
        
        return jsonify({'users': users_data}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch users'}), 500

@dashboard_bp.route('/admin/users/<user_id>/toggle-status', methods=['POST'])
@role_required(UserRole.ADMIN)
def toggle_user_status(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = not user.is_active
        db.session.commit()
        
        log_audit_action(
            'user_status_toggled',
            'user',
            user_id,
            {'new_status': 'active' if user.is_active else 'inactive'}
        )
        
        return jsonify({
            'message': f"User {'activated' if user.is_active else 'deactivated'} successfully",
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to toggle user status'}), 500

@dashboard_bp.route('/admin/analytics', methods=['GET'])
@role_required(UserRole.ADMIN)
def get_analytics():
    try:
        period = request.args.get('period', '30')
        try:
            days = int(period)
        except ValueError:
            days = 30
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        revenue_data = db.session.query(
            func.date(Payment.created_at).label('date'),
            func.sum(Payment.amount).label('revenue')
        ).filter(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.created_at >= start_date
        ).group_by(func.date(Payment.created_at)).all()
        
        session_data = db.session.query(
            func.date(Session.created_at).label('date'),
            func.count(Session.id).label('sessions')
        ).filter(
            Session.created_at >= start_date
        ).group_by(func.date(Session.created_at)).all()
        
        user_registration_data = db.session.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('registrations')
        ).filter(
            User.created_at >= start_date
        ).group_by(func.date(User.created_at)).all()
        
        crisis_data = db.session.query(
            func.date(CrisisAlert.created_at).label('date'),
            func.count(CrisisAlert.id).label('alerts')
        ).filter(
            CrisisAlert.created_at >= start_date
        ).group_by(func.date(CrisisAlert.created_at)).all()
        
        return jsonify({
            'analytics': {
                'revenue': [{'date': str(date), 'amount': float(revenue)} for date, revenue in revenue_data],
                'sessions': [{'date': str(date), 'count': sessions} for date, sessions in session_data],
                'registrations': [{'date': str(date), 'count': registrations} for date, registrations in user_registration_data],
                'crisis_alerts': [{'date': str(date), 'count': alerts} for date, alerts in crisis_data]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch analytics'}), 500
