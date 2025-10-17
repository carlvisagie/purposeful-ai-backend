"""
Webhook Handlers Blueprint
Processes webhooks from Calendly, Zoom, and Stripe
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import json
import os

# Import services
from services.calendly_service import CalendlyService
from services.zoom_service import ZoomService
from services.whatsapp_service import WhatsAppService
from services.google_workspace_service import GoogleWorkspaceService
from services.enhanced_payment_service import EnhancedPaymentService

# Import models
from models import db, User
from models_extended import Appointment, Notification, WebhookLog, OnboardingProgress

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')

# Initialize services
calendly_service = CalendlyService(os.getenv('CALENDLY_API_KEY', ''))
zoom_service = ZoomService(os.getenv('ZOOM_API_KEY', ''), os.getenv('ZOOM_API_SECRET', ''))
whatsapp_service = WhatsAppService(
    os.getenv('TWILIO_ACCOUNT_SID', ''),
    os.getenv('TWILIO_AUTH_TOKEN', ''),
    os.getenv('TWILIO_WHATSAPP_NUMBER', '')
)
payment_service = EnhancedPaymentService(os.getenv('STRIPE_SECRET_KEY', ''))


@webhooks_bp.route('/calendly', methods=['POST'])
def handle_calendly_webhook():
    """
    Handle Calendly webhook events
    
    Events:
    - invitee.created: New appointment booked
    - invitee.canceled: Appointment cancelled
    """
    try:
        payload = request.get_json()
        
        # Log webhook
        webhook_log = WebhookLog(
            source='calendly',
            event_type=payload.get('event'),
            payload=json.dumps(payload),
            headers=json.dumps(dict(request.headers))
        )
        db.session.add(webhook_log)
        db.session.commit()
        
        # Process webhook
        result = calendly_service.handle_webhook(payload)
        
        if result['status'] == 'success':
            event_type = result['event_type']
            
            if event_type == 'invitee.created':
                # New appointment booked
                event_details = result['event_details']['resource']
                invitees = result['invitees']
                
                if invitees:
                    invitee = invitees[0]['resource']
                    invitee_email = invitee['email']
                    
                    # Find user by email
                    user = User.query.filter_by(email=invitee_email).first()
                    
                    if user:
                        # Create Zoom meeting
                        start_time = datetime.fromisoformat(event_details['start_time'].replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(event_details['end_time'].replace('Z', '+00:00'))
                        duration = int((end_time - start_time).total_seconds() / 60)
                        
                        zoom_meeting = zoom_service.create_meeting(
                            topic=f"Coaching Session - {user.first_name} {user.last_name}",
                            start_time=start_time,
                            duration=duration,
                            agenda=f"Purposeful Live Coaching Session for {user.first_name}"
                        )
                        
                        if zoom_meeting:
                            # Create appointment record
                            appointment = Appointment(
                                user_id=user.id,
                                calendly_event_id=result['event_uuid'],
                                calendly_event_uri=event_details['uri'],
                                zoom_meeting_id=zoom_meeting['meeting_id'],
                                zoom_meeting_uuid=zoom_meeting['meeting_uuid'],
                                scheduled_time=start_time,
                                duration_minutes=duration,
                                status='scheduled',
                                zoom_join_url=zoom_meeting['join_url'],
                                zoom_start_url=zoom_meeting['start_url'],
                                zoom_password=zoom_meeting['password']
                            )
                            db.session.add(appointment)
                            
                            # Update onboarding progress
                            progress = OnboardingProgress.query.filter_by(user_id=user.id).first()
                            if progress:
                                progress.step_scheduling = True
                                progress.step_scheduling_at = datetime.utcnow()
                                progress.current_step = 5
                                progress.last_activity_at = datetime.utcnow()
                            
                            db.session.commit()
                            
                            # Send confirmation notifications
                            _send_appointment_confirmations(user, appointment)
                            
                            logger.info(f"Appointment created for user {user.id}, appointment {appointment.id}")
            
            elif event_type == 'invitee.canceled':
                # Appointment cancelled
                event_uuid = result['event_uuid']
                appointment = Appointment.query.filter_by(calendly_event_id=event_uuid).first()
                
                if appointment:
                    appointment.status = 'cancelled'
                    appointment.cancellation_reason = result.get('reason', 'Client cancelled')
                    appointment.cancelled_by = 'client'
                    
                    # Delete Zoom meeting
                    if appointment.zoom_meeting_id:
                        zoom_service.delete_meeting(appointment.zoom_meeting_id)
                    
                    db.session.commit()
                    
                    # Send cancellation notification
                    user = User.query.get(appointment.user_id)
                    if user and user.whatsapp_opt_in and user.whatsapp_number:
                        whatsapp_service.send_message(
                            user.whatsapp_number,
                            f"Hi {user.first_name}, your coaching session on {appointment.scheduled_time.strftime('%B %d at %I:%M %p')} has been cancelled. You can reschedule anytime from your dashboard."
                        )
                    
                    logger.info(f"Appointment {appointment.id} cancelled")
        
        # Update webhook log
        webhook_log.processed = True
        webhook_log.processed_at = datetime.utcnow()
        webhook_log.processing_result = json.dumps(result)
        db.session.commit()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Error handling Calendly webhook: {e}")
        if 'webhook_log' in locals():
            webhook_log.error_message = str(e)
            db.session.commit()
        return jsonify({'error': 'Webhook processing failed'}), 500


@webhooks_bp.route('/zoom', methods=['POST'])
def handle_zoom_webhook():
    """
    Handle Zoom webhook events
    
    Events:
    - meeting.started: Meeting started
    - meeting.ended: Meeting ended
    - recording.completed: Recording ready
    """
    try:
        payload = request.get_json()
        
        # Log webhook
        webhook_log = WebhookLog(
            source='zoom',
            event_type=payload.get('event'),
            payload=json.dumps(payload),
            headers=json.dumps(dict(request.headers))
        )
        db.session.add(webhook_log)
        db.session.commit()
        
        # Process webhook
        result = zoom_service.handle_webhook(payload)
        
        if result['status'] == 'success':
            event_type = result['event_type']
            meeting_id = result.get('meeting_id')
            
            if meeting_id:
                appointment = Appointment.query.filter_by(zoom_meeting_id=str(meeting_id)).first()
                
                if appointment:
                    if event_type == 'meeting.started':
                        # Log meeting start
                        logger.info(f"Meeting started for appointment {appointment.id}")
                    
                    elif event_type == 'meeting.ended':
                        # Update appointment
                        appointment.status = 'completed'
                        appointment.actual_duration_minutes = result.get('duration')
                        db.session.commit()
                        
                        logger.info(f"Meeting ended for appointment {appointment.id}")
                    
                    elif event_type == 'recording.completed':
                        # Save recording URLs
                        recording_files = result.get('recording_files', [])
                        if recording_files:
                            # Get the first video file
                            video_file = next((f for f in recording_files if f['file_type'] == 'MP4'), None)
                            if video_file:
                                appointment.recording_url = video_file['download_url']
                                appointment.recording_password = video_file.get('password', '')
                                db.session.commit()
                                
                                # Send follow-up with recording
                                user = User.query.get(appointment.user_id)
                                if user and user.whatsapp_opt_in and user.whatsapp_number:
                                    whatsapp_service.send_post_session_followup(
                                        user.whatsapp_number,
                                        user.first_name,
                                        session_summary_link=appointment.recording_url
                                    )
                                
                                logger.info(f"Recording saved for appointment {appointment.id}")
        
        # Update webhook log
        webhook_log.processed = True
        webhook_log.processed_at = datetime.utcnow()
        webhook_log.processing_result = json.dumps(result)
        db.session.commit()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Error handling Zoom webhook: {e}")
        if 'webhook_log' in locals():
            webhook_log.error_message = str(e)
            db.session.commit()
        return jsonify({'error': 'Webhook processing failed'}), 500


@webhooks_bp.route('/stripe', methods=['POST'])
def handle_stripe_webhook():
    """
    Handle Stripe webhook events
    
    Events:
    - payment_intent.succeeded: Payment successful
    - payment_intent.payment_failed: Payment failed
    - customer.subscription.*: Subscription events
    - invoice.*: Invoice events
    """
    try:
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        # Verify webhook signature
        event = payment_service.construct_webhook_event(payload, sig_header)
        
        if not event:
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Log webhook
        webhook_log = WebhookLog(
            source='stripe',
            event_type=event['type'],
            event_id=event['id'],
            payload=payload.decode('utf-8'),
            headers=json.dumps(dict(request.headers))
        )
        db.session.add(webhook_log)
        db.session.commit()
        
        # Process webhook
        result = payment_service.handle_webhook_event(event)
        
        if result['status'] in ['success', 'failed']:
            customer_id = result.get('customer_id')
            
            if customer_id:
                user = User.query.filter_by(stripe_customer_id=customer_id).first()
                
                if user:
                    event_type = result['event_type']
                    
                    if event_type == 'payment_succeeded':
                        # Update onboarding progress
                        progress = OnboardingProgress.query.filter_by(user_id=user.id).first()
                        if progress:
                            progress.step_payment = True
                            progress.step_payment_at = datetime.utcnow()
                            progress.current_step = 4
                            progress.last_activity_at = datetime.utcnow()
                            db.session.commit()
                        
                        # Send payment confirmation
                        if user.whatsapp_opt_in and user.whatsapp_number:
                            amount = result['amount'] / 100  # Convert from cents
                            whatsapp_service.send_payment_confirmation(
                                user.whatsapp_number,
                                user.first_name,
                                amount,
                                'Coaching Session'
                            )
                        
                        logger.info(f"Payment succeeded for user {user.id}")
                    
                    elif event_type == 'payment_failed':
                        # Notify user of payment failure
                        if user.whatsapp_opt_in and user.whatsapp_number:
                            whatsapp_service.send_message(
                                user.whatsapp_number,
                                f"Hi {user.first_name}, we had trouble processing your payment. Please update your payment method in your account settings."
                            )
                        
                        logger.warning(f"Payment failed for user {user.id}")
                    
                    elif event_type == 'subscription_created':
                        # Activate subscription
                        user.subscription_active = True
                        user.subscription_tier = result.get('tier', 'Unknown')
                        db.session.commit()
                        
                        logger.info(f"Subscription created for user {user.id}")
                    
                    elif event_type == 'subscription_deleted':
                        # Deactivate subscription
                        user.subscription_active = False
                        db.session.commit()
                        
                        logger.info(f"Subscription cancelled for user {user.id}")
        
        # Update webhook log
        webhook_log.processed = True
        webhook_log.processed_at = datetime.utcnow()
        webhook_log.processing_result = json.dumps(result)
        db.session.commit()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Error handling Stripe webhook: {e}")
        if 'webhook_log' in locals():
            webhook_log.error_message = str(e)
            db.session.commit()
        return jsonify({'error': 'Webhook processing failed'}), 500


def _send_appointment_confirmations(user: User, appointment: Appointment):
    """
    Send appointment confirmation via email and WhatsApp
    
    Args:
        user: User object
        appointment: Appointment object
    """
    try:
        # Send WhatsApp confirmation
        if user.whatsapp_opt_in and user.whatsapp_number:
            whatsapp_service.send_appointment_confirmation(
                user.whatsapp_number,
                user.first_name,
                appointment.scheduled_time,
                appointment.zoom_join_url,
                coach_name="Your Coach"
            )
            
            appointment.confirmation_sent = True
            appointment.confirmation_sent_at = datetime.utcnow()
        
        # Send email confirmation
        try:
            google_service = GoogleWorkspaceService()
            google_service.send_email(
                to_email=user.email,
                subject="Appointment Confirmed - Purposeful Live Coaching",
                body=f"""Hi {user.first_name},\n\nYour coaching session has been confirmed!\n\nDate: {appointment.scheduled_at.strftime('%B %d, %Y')}\nTime: {appointment.scheduled_at.strftime('%I:%M %p')}\n\nZoom Link: {appointment.zoom_join_url}\n\nWe look forward to seeing you!\n\nBest regards,\nPurposeful Live Coaching Team"""
            )
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {str(e)}")
        
        db.session.commit()
        
        logger.info(f"Confirmations sent for appointment {appointment.id}")
        
    except Exception as e:
        logger.error(f"Error sending confirmations: {e}")

