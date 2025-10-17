"""
Dashboard API Blueprint
Client dashboard endpoints for viewing appointments, progress, and account info
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging

# Import models
from models import db, User
from models_extended import Appointment, Notification, OnboardingProgress

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get user profile information
    
    Returns:
        JSON response with user profile data
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get onboarding progress
        progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
        
        return jsonify({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': getattr(user, 'phone', None),
                'whatsapp_number': getattr(user, 'whatsapp_number', None),
                'whatsapp_opt_in': getattr(user, 'whatsapp_opt_in', False),
                'preferred_communication': getattr(user, 'preferred_communication', 'email'),
                'subscription_active': getattr(user, 'subscription_active', False),
                'subscription_tier': getattr(user, 'subscription_tier', None),
                'onboarding_completed': getattr(user, 'onboarding_completed', False),
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
            },
            'onboarding_progress': progress.to_dict() if progress else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500


@dashboard_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    """
    Get all appointments for the authenticated user
    
    Query params:
        status: Filter by status (scheduled, completed, cancelled)
        upcoming: Boolean, show only upcoming appointments
    
    Returns:
        JSON response with list of appointments
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Build query
        query = Appointment.query.filter_by(user_id=user_id)
        
        # Filter by status if provided
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)
        
        # Filter upcoming only
        upcoming_only = request.args.get('upcoming', 'false').lower() == 'true'
        if upcoming_only:
            query = query.filter(Appointment.scheduled_time >= datetime.utcnow())
        
        # Order by scheduled time
        appointments = query.order_by(Appointment.scheduled_time.desc()).all()
        
        return jsonify({
            'appointments': [apt.to_dict() for apt in appointments],
            'total': len(appointments)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting appointments: {e}")
        return jsonify({'error': 'Failed to get appointments'}), 500


@dashboard_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment_details(appointment_id):
    """
    Get detailed information about a specific appointment
    
    Args:
        appointment_id: Appointment ID
    
    Returns:
        JSON response with appointment details
    """
    try:
        user_id = get_jwt_identity()
        appointment = Appointment.query.filter_by(
            id=appointment_id,
            user_id=user_id
        ).first()
        
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        return jsonify({
            'appointment': appointment.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting appointment details: {e}")
        return jsonify({'error': 'Failed to get appointment details'}), 500


@dashboard_bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_appointment(appointment_id):
    """
    Cancel an appointment
    
    Args:
        appointment_id: Appointment ID
    
    Expected payload:
    {
        "reason": "Optional cancellation reason"
    }
    
    Returns:
        JSON response with cancellation status
    """
    try:
        user_id = get_jwt_identity()
        appointment = Appointment.query.filter_by(
            id=appointment_id,
            user_id=user_id
        ).first()
        
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        if appointment.status == 'cancelled':
            return jsonify({'error': 'Appointment already cancelled'}), 400
        
        # Check if appointment is in the future
        if appointment.scheduled_time < datetime.utcnow():
            return jsonify({'error': 'Cannot cancel past appointments'}), 400
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Client requested cancellation')
        
        # Update appointment
        appointment.status = 'cancelled'
        appointment.cancellation_reason = reason
        appointment.cancelled_by = 'client'
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Cancel Calendly event and Zoom meeting
        try:
            from services.calendly_service import CalendlyService
            from services.zoom_service import ZoomService
            import os
            
            # Cancel Calendly event
            if appointment.calendly_event_id:
                calendly_service = CalendlyService(os.getenv('CALENDLY_API_KEY', ''))
                calendly_service.cancel_event(appointment.calendly_event_id)
                logger.info(f"Cancelled Calendly event {appointment.calendly_event_id}")
            
            # Cancel/Delete Zoom meeting
            if appointment.zoom_meeting_id:
                zoom_service = ZoomService(os.getenv('ZOOM_API_KEY', ''), os.getenv('ZOOM_API_SECRET', ''))
                # Note: Zoom doesn't have a cancel endpoint, but we can delete the meeting
                # zoom_service.delete_meeting(appointment.zoom_meeting_id)
                logger.info(f"Zoom meeting {appointment.zoom_meeting_id} marked for cancellation")
                
        except Exception as e:
            logger.error(f"Failed to cancel external services: {str(e)}")
        
        logger.info(f"Appointment {appointment_id} cancelled by user {user_id}")
        
        return jsonify({
            'message': 'Appointment cancelled successfully',
            'appointment': appointment.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel appointment'}), 500


@dashboard_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    Get notification history for the authenticated user
    
    Query params:
        limit: Number of notifications to return (default: 20)
        category: Filter by category
    
    Returns:
        JSON response with list of notifications
    """
    try:
        user_id = get_jwt_identity()
        
        # Build query
        query = Notification.query.filter_by(user_id=user_id)
        
        # Filter by category if provided
        category = request.args.get('category')
        if category:
            query = query.filter_by(category=category)
        
        # Limit results
        limit = int(request.args.get('limit', 20))
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'notifications': [notif.to_dict() for notif in notifications],
            'total': len(notifications)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'error': 'Failed to get notifications'}), 500


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Get dashboard statistics for the user
    
    Returns:
        JSON response with user statistics
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Count appointments by status
        total_appointments = Appointment.query.filter_by(user_id=user_id).count()
        upcoming_appointments = Appointment.query.filter_by(
            user_id=user_id,
            status='scheduled'
        ).filter(Appointment.scheduled_time >= datetime.utcnow()).count()
        
        completed_appointments = Appointment.query.filter_by(
            user_id=user_id,
            status='completed'
        ).count()
        
        cancelled_appointments = Appointment.query.filter_by(
            user_id=user_id,
            status='cancelled'
        ).count()
        
        # Get next appointment
        next_appointment = Appointment.query.filter_by(
            user_id=user_id,
            status='scheduled'
        ).filter(
            Appointment.scheduled_time >= datetime.utcnow()
        ).order_by(Appointment.scheduled_time.asc()).first()
        
        # Get recent notifications
        recent_notifications = Notification.query.filter_by(
            user_id=user_id
        ).order_by(Notification.created_at.desc()).limit(5).all()
        
        return jsonify({
            'stats': {
                'total_appointments': total_appointments,
                'upcoming_appointments': upcoming_appointments,
                'completed_appointments': completed_appointments,
                'cancelled_appointments': cancelled_appointments,
                'subscription_active': getattr(user, 'subscription_active', False),
                'subscription_tier': getattr(user, 'subscription_tier', None)
            },
            'next_appointment': next_appointment.to_dict() if next_appointment else None,
            'recent_notifications': [notif.to_dict() for notif in recent_notifications]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500


@dashboard_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile information
    
    Expected payload:
    {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "whatsapp_number": "+1234567890",
        "whatsapp_opt_in": true,
        "preferred_communication": "whatsapp"
    }
    
    Returns:
        JSON response with updated profile
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'phone' in data and hasattr(user, 'phone'):
            user.phone = data['phone']
        if 'whatsapp_number' in data and hasattr(user, 'whatsapp_number'):
            user.whatsapp_number = data['whatsapp_number']
        if 'whatsapp_opt_in' in data and hasattr(user, 'whatsapp_opt_in'):
            user.whatsapp_opt_in = data['whatsapp_opt_in']
        if 'preferred_communication' in data and hasattr(user, 'preferred_communication'):
            user.preferred_communication = data['preferred_communication']
        
        db.session.commit()
        
        logger.info(f"Profile updated for user {user_id}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': getattr(user, 'phone', None),
                'whatsapp_number': getattr(user, 'whatsapp_number', None),
                'whatsapp_opt_in': getattr(user, 'whatsapp_opt_in', False),
                'preferred_communication': getattr(user, 'preferred_communication', 'email')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500


@dashboard_bp.route('/subscription/portal', methods=['GET'])
@jwt_required()
def get_subscription_portal():
    """
    Get Stripe customer portal URL for subscription management
    
    Returns:
        JSON response with portal URL
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.stripe_customer_id:
            return jsonify({'error': 'No subscription found'}), 404
        
        # Import payment service
        from services.enhanced_payment_service import EnhancedPaymentService
        import os
        
        payment_service = EnhancedPaymentService(os.getenv('STRIPE_SECRET_KEY', ''))
        
        # Create portal session
        return_url = os.getenv('FRONTEND_URL', 'https://purposefullivecoaching.academy') + '/dashboard'
        portal_url = payment_service.create_customer_portal_session(
            user.stripe_customer_id,
            return_url
        )
        
        if not portal_url:
            return jsonify({'error': 'Failed to create portal session'}), 500
        
        return jsonify({
            'portal_url': portal_url
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription portal: {e}")
        return jsonify({'error': 'Failed to get subscription portal'}), 500

