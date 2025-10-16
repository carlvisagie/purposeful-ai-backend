"""
Extended Admin API Blueprint
Administrative endpoints for monitoring, management, and analytics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import logging

from models import db, User, UserRole, Session, CrisisAlert, Payment
from models_extended import Appointment, Notification, OnboardingProgress, WebhookLog

logger = logging.getLogger(__name__)

admin_extended_bp = Blueprint('admin_extended', __name__, url_prefix='/api/admin')


def require_admin():
    """Decorator to require admin role"""
    def decorator(f):
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or user.role != UserRole.ADMIN:
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


@admin_extended_bp.route('/analytics/overview', methods=['GET'])
@require_admin()
def get_analytics_overview():
    """
    Get high-level analytics overview
    
    Returns:
        JSON response with key metrics
    """
    try:
        # Time ranges
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        # User metrics
        total_users = User.query.count()
        new_users_today = User.query.filter(User.created_at >= today_start).count()
        new_users_week = User.query.filter(User.created_at >= week_start).count()
        new_users_month = User.query.filter(User.created_at >= month_start).count()
        
        active_subscriptions = User.query.filter(User.subscription_active == True).count()
        
        # Onboarding metrics
        total_onboarding = OnboardingProgress.query.count()
        completed_onboarding = OnboardingProgress.query.filter(
            OnboardingProgress.is_completed == True
        ).count()
        onboarding_completion_rate = (
            (completed_onboarding / total_onboarding * 100)
            if total_onboarding > 0 else 0
        )
        
        # Appointment metrics
        total_appointments = Appointment.query.count()
        upcoming_appointments = Appointment.query.filter(
            Appointment.status == 'scheduled',
            Appointment.scheduled_time >= now
        ).count()
        completed_appointments = Appointment.query.filter(
            Appointment.status == 'completed'
        ).count()
        
        # Revenue metrics
        total_revenue = db.session.query(
            func.sum(Payment.amount)
        ).filter(Payment.status == 'succeeded').scalar() or 0
        
        revenue_today = db.session.query(
            func.sum(Payment.amount)
        ).filter(
            Payment.status == 'succeeded',
            Payment.paid_at >= today_start
        ).scalar() or 0
        
        revenue_week = db.session.query(
            func.sum(Payment.amount)
        ).filter(
            Payment.status == 'succeeded',
            Payment.paid_at >= week_start
        ).scalar() or 0
        
        revenue_month = db.session.query(
            func.sum(Payment.amount)
        ).filter(
            Payment.status == 'succeeded',
            Payment.paid_at >= month_start
        ).scalar() or 0
        
        # Crisis metrics
        total_crisis_alerts = CrisisAlert.query.count()
        unresolved_crisis = CrisisAlert.query.filter(
            CrisisAlert.resolved == False
        ).count()
        
        return jsonify({
            'users': {
                'total': total_users,
                'new_today': new_users_today,
                'new_this_week': new_users_week,
                'new_this_month': new_users_month,
                'active_subscriptions': active_subscriptions
            },
            'onboarding': {
                'total_started': total_onboarding,
                'total_completed': completed_onboarding,
                'completion_rate': round(onboarding_completion_rate, 2)
            },
            'appointments': {
                'total': total_appointments,
                'upcoming': upcoming_appointments,
                'completed': completed_appointments
            },
            'revenue': {
                'total': total_revenue / 100,  # Convert to dollars
                'today': revenue_today / 100,
                'this_week': revenue_week / 100,
                'this_month': revenue_month / 100
            },
            'crisis_alerts': {
                'total': total_crisis_alerts,
                'unresolved': unresolved_crisis
            },
            'generated_at': now.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        return jsonify({'error': 'Failed to get analytics'}), 500


@admin_extended_bp.route('/users', methods=['GET'])
@require_admin()
def list_users():
    """
    List all users with filtering and pagination
    
    Query params:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)
        role: Filter by role
        subscription_active: Filter by subscription status
        search: Search by name or email
    
    Returns:
        JSON response with user list
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = User.query
        
        # Filter by role
        role = request.args.get('role')
        if role:
            query = query.filter(User.role == UserRole[role.upper()])
        
        # Filter by subscription status
        subscription_active = request.args.get('subscription_active')
        if subscription_active:
            query = query.filter(
                User.subscription_active == (subscription_active.lower() == 'true')
            )
        
        # Search
        search = request.args.get('search')
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                db.or_(
                    User.email.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern)
                )
            )
        
        # Paginate
        pagination = query.order_by(desc(User.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({'error': 'Failed to list users'}), 500


@admin_extended_bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin()
def get_user_details(user_id):
    """
    Get detailed information about a specific user
    
    Args:
        user_id: User ID
    
    Returns:
        JSON response with user details
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get related data
        appointments = Appointment.query.filter_by(user_id=user_id).all()
        payments = Payment.query.filter_by(user_id=user_id).all()
        crisis_alerts = CrisisAlert.query.filter_by(user_id=user_id).all()
        onboarding = OnboardingProgress.query.filter_by(user_id=user_id).first()
        
        return jsonify({
            'user': user.to_dict(),
            'appointments': [apt.to_dict() for apt in appointments],
            'payments': [payment.to_dict() for payment in payments],
            'crisis_alerts': [alert.to_dict() for alert in crisis_alerts],
            'onboarding_progress': onboarding.to_dict() if onboarding else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return jsonify({'error': 'Failed to get user details'}), 500


@admin_extended_bp.route('/appointments', methods=['GET'])
@require_admin()
def list_appointments():
    """
    List all appointments with filtering
    
    Query params:
        status: Filter by status
        date_from: Start date (ISO format)
        date_to: End date (ISO format)
        page: Page number
        per_page: Items per page
    
    Returns:
        JSON response with appointment list
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = Appointment.query
        
        # Filter by status
        status = request.args.get('status')
        if status:
            query = query.filter(Appointment.status == status)
        
        # Filter by date range
        date_from = request.args.get('date_from')
        if date_from:
            query = query.filter(
                Appointment.scheduled_time >= datetime.fromisoformat(date_from)
            )
        
        date_to = request.args.get('date_to')
        if date_to:
            query = query.filter(
                Appointment.scheduled_time <= datetime.fromisoformat(date_to)
            )
        
        # Paginate
        pagination = query.order_by(desc(Appointment.scheduled_time)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'appointments': [apt.to_dict() for apt in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing appointments: {e}")
        return jsonify({'error': 'Failed to list appointments'}), 500


@admin_extended_bp.route('/crisis-alerts', methods=['GET'])
@require_admin()
def list_crisis_alerts():
    """
    List all crisis alerts with filtering
    
    Query params:
        resolved: Filter by resolved status
        crisis_level: Filter by crisis level
        page: Page number
    
    Returns:
        JSON response with crisis alert list
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = CrisisAlert.query
        
        # Filter by resolved status
        resolved = request.args.get('resolved')
        if resolved:
            query = query.filter(
                CrisisAlert.resolved == (resolved.lower() == 'true')
            )
        
        # Filter by crisis level
        crisis_level = request.args.get('crisis_level')
        if crisis_level:
            from models import CrisisLevel
            query = query.filter(
                CrisisAlert.crisis_level == CrisisLevel[crisis_level.upper()]
            )
        
        # Paginate
        pagination = query.order_by(desc(CrisisAlert.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'crisis_alerts': [alert.to_dict() for alert in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing crisis alerts: {e}")
        return jsonify({'error': 'Failed to list crisis alerts'}), 500


@admin_extended_bp.route('/crisis-alerts/<int:alert_id>/resolve', methods=['POST'])
@require_admin()
def resolve_crisis_alert(alert_id):
    """
    Mark a crisis alert as resolved
    
    Args:
        alert_id: Crisis alert ID
    
    Expected payload:
    {
        "resolution_notes": "Contacted client, situation stabilized"
    }
    
    Returns:
        JSON response with updated alert
    """
    try:
        alert = CrisisAlert.query.get(alert_id)
        
        if not alert:
            return jsonify({'error': 'Crisis alert not found'}), 404
        
        data = request.get_json() or {}
        
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = data.get('resolution_notes', '')
        
        db.session.commit()
        
        logger.info(f"Crisis alert {alert_id} resolved")
        
        return jsonify({
            'message': 'Crisis alert resolved',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error resolving crisis alert: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to resolve crisis alert'}), 500


@admin_extended_bp.route('/webhooks/logs', methods=['GET'])
@require_admin()
def get_webhook_logs():
    """
    Get webhook event logs
    
    Query params:
        source: Filter by source (calendly, zoom, stripe)
        processed: Filter by processed status
        limit: Number of logs to return
    
    Returns:
        JSON response with webhook logs
    """
    try:
        limit = int(request.args.get('limit', 50))
        
        query = WebhookLog.query
        
        # Filter by source
        source = request.args.get('source')
        if source:
            query = query.filter(WebhookLog.source == source)
        
        # Filter by processed status
        processed = request.args.get('processed')
        if processed:
            query = query.filter(
                WebhookLog.processed == (processed.lower() == 'true')
            )
        
        logs = query.order_by(desc(WebhookLog.created_at)).limit(limit).all()
        
        return jsonify({
            'webhook_logs': [log.to_dict() for log in logs],
            'total': len(logs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting webhook logs: {e}")
        return jsonify({'error': 'Failed to get webhook logs'}), 500


@admin_extended_bp.route('/system/stats', methods=['GET'])
@require_admin()
def get_system_stats():
    """
    Get system statistics and health metrics
    
    Returns:
        JSON response with system stats
    """
    try:
        # Database table counts
        table_counts = {
            'users': User.query.count(),
            'appointments': Appointment.query.count(),
            'payments': Payment.query.count(),
            'sessions': Session.query.count(),
            'crisis_alerts': CrisisAlert.query.count(),
            'notifications': Notification.query.count(),
            'webhook_logs': WebhookLog.query.count(),
            'onboarding_progress': OnboardingProgress.query.count()
        }
        
        # Recent activity
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        
        recent_activity = {
            'new_users_last_hour': User.query.filter(
                User.created_at >= last_hour
            ).count(),
            'appointments_last_hour': Appointment.query.filter(
                Appointment.created_at >= last_hour
            ).count(),
            'payments_last_hour': Payment.query.filter(
                Payment.created_at >= last_hour
            ).count(),
            'webhooks_last_hour': WebhookLog.query.filter(
                WebhookLog.created_at >= last_hour
            ).count()
        }
        
        return jsonify({
            'table_counts': table_counts,
            'recent_activity': recent_activity,
            'timestamp': now.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({'error': 'Failed to get system stats'}), 500

