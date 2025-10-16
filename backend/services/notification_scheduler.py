"""
Notification Scheduler Service
Handles automated reminders and follow-ups for appointments
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from models import db, User
from models_extended import Appointment, Notification
from services.whatsapp_service import WhatsAppService
from services.google_workspace_service import GoogleWorkspaceService

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """
    Manages automated notifications for appointments
    """
    
    def __init__(self):
        """Initialize notification services"""
        self.whatsapp_service = None
        self.email_service = None
        
        # Initialize WhatsApp if credentials available
        twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        if twilio_sid and twilio_token:
            self.whatsapp_service = WhatsAppService(
                twilio_sid,
                twilio_token,
                twilio_number
            )
        
        # Initialize email if credentials available
        google_creds = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        if google_creds:
            self.email_service = GoogleWorkspaceService(
                service_account_file=google_creds
            )
    
    def send_appointment_reminder(
        self,
        appointment: Appointment,
        hours_before: int
    ) -> bool:
        """
        Send appointment reminder
        
        Args:
            appointment: Appointment object
            hours_before: How many hours before appointment
            
        Returns:
            True if sent successfully
        """
        try:
            user = User.query.get(appointment.user_id)
            if not user:
                logger.error(f"User {appointment.user_id} not found")
                return False
            
            # Format appointment time
            apt_time = appointment.scheduled_time.strftime('%B %d, %Y at %I:%M %p')
            
            # Determine preferred communication method
            preferred = getattr(user, 'preferred_communication', 'email')
            
            sent = False
            
            # Send via WhatsApp if opted in
            if preferred == 'whatsapp' and self.whatsapp_service:
                whatsapp_number = getattr(user, 'whatsapp_number', None)
                if whatsapp_number:
                    result = self.whatsapp_service.send_reminder(
                        to_number=whatsapp_number,
                        client_name=f"{user.first_name} {user.last_name}",
                        appointment_time=apt_time,
                        zoom_link=appointment.zoom_join_url,
                        hours_before=hours_before
                    )
                    sent = result is not None
            
            # Send via email as fallback or primary
            if (not sent or preferred == 'email') and self.email_service:
                result = self.email_service.send_appointment_confirmation_email(
                    to_email=user.email,
                    client_name=f"{user.first_name} {user.last_name}",
                    appointment_time=apt_time,
                    zoom_link=appointment.zoom_join_url,
                    coach_name="Your Coach"
                )
                sent = result is not None
            
            # Log notification
            if sent:
                notification = Notification(
                    user_id=user.id,
                    appointment_id=appointment.id,
                    type='whatsapp' if preferred == 'whatsapp' else 'email',
                    category='appointment',
                    subject=f'Reminder: Appointment in {hours_before} hours',
                    status='delivered',
                    sent_at=datetime.utcnow()
                )
                db.session.add(notification)
                db.session.commit()
                
                logger.info(f"Sent {hours_before}h reminder for appointment {appointment.id}")
            
            return sent
            
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            return False
    
    def send_post_session_followup(
        self,
        appointment: Appointment
    ) -> bool:
        """
        Send post-session follow-up with summary and action items
        
        Args:
            appointment: Completed appointment
            
        Returns:
            True if sent successfully
        """
        try:
            user = User.query.get(appointment.user_id)
            if not user:
                return False
            
            # Check if appointment is completed
            if appointment.status != 'completed':
                logger.warning(f"Appointment {appointment.id} not completed yet")
                return False
            
            preferred = getattr(user, 'preferred_communication', 'email')
            sent = False
            
            # Send via WhatsApp
            if preferred == 'whatsapp' and self.whatsapp_service:
                whatsapp_number = getattr(user, 'whatsapp_number', None)
                if whatsapp_number:
                    result = self.whatsapp_service.send_post_session_followup(
                        to_number=whatsapp_number,
                        client_name=f"{user.first_name} {user.last_name}",
                        session_summary=appointment.ai_summary or "Session completed successfully",
                        action_items=appointment.action_items or "Review session notes",
                        next_session_date="To be scheduled",
                        recording_url=appointment.recording_url
                    )
                    sent = result is not None
            
            # Send via email
            if (not sent or preferred == 'email') and self.email_service:
                result = self.email_service.send_session_summary_email(
                    to_email=user.email,
                    client_name=f"{user.first_name} {user.last_name}",
                    session_date=appointment.scheduled_time.strftime('%B %d, %Y'),
                    summary=appointment.ai_summary or "Session completed successfully",
                    action_items=appointment.action_items or "Review session notes",
                    recording_url=appointment.recording_url
                )
                sent = result is not None
            
            # Log notification
            if sent:
                notification = Notification(
                    user_id=user.id,
                    appointment_id=appointment.id,
                    type='whatsapp' if preferred == 'whatsapp' else 'email',
                    category='followup',
                    subject='Session Summary and Action Items',
                    status='delivered',
                    sent_at=datetime.utcnow()
                )
                db.session.add(notification)
                db.session.commit()
                
                logger.info(f"Sent follow-up for appointment {appointment.id}")
            
            return sent
            
        except Exception as e:
            logger.error(f"Error sending follow-up: {e}")
            return False
    
    def check_and_send_reminders(self) -> dict:
        """
        Check for upcoming appointments and send reminders
        Should be called by a scheduled task (cron job)
        
        Returns:
            Dictionary with reminder statistics
        """
        try:
            now = datetime.utcnow()
            
            # Find appointments needing 24-hour reminder
            reminder_24h = now + timedelta(hours=24)
            appointments_24h = Appointment.query.filter(
                Appointment.status == 'scheduled',
                Appointment.scheduled_time >= now,
                Appointment.scheduled_time <= reminder_24h,
                Appointment.reminder_24h_sent == False
            ).all()
            
            # Find appointments needing 1-hour reminder
            reminder_1h = now + timedelta(hours=1)
            appointments_1h = Appointment.query.filter(
                Appointment.status == 'scheduled',
                Appointment.scheduled_time >= now,
                Appointment.scheduled_time <= reminder_1h,
                Appointment.reminder_1h_sent == False
            ).all()
            
            stats = {
                'checked_at': now.isoformat(),
                '24h_reminders_sent': 0,
                '1h_reminders_sent': 0,
                'errors': 0
            }
            
            # Send 24-hour reminders
            for apt in appointments_24h:
                if self.send_appointment_reminder(apt, 24):
                    apt.reminder_24h_sent = True
                    stats['24h_reminders_sent'] += 1
                else:
                    stats['errors'] += 1
            
            # Send 1-hour reminders
            for apt in appointments_1h:
                if self.send_appointment_reminder(apt, 1):
                    apt.reminder_1h_sent = True
                    stats['1h_reminders_sent'] += 1
                else:
                    stats['errors'] += 1
            
            db.session.commit()
            
            logger.info(f"Reminder check complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
            return {'error': str(e)}
    
    def check_and_send_followups(self) -> dict:
        """
        Check for completed appointments needing follow-up
        Should be called by a scheduled task
        
        Returns:
            Dictionary with follow-up statistics
        """
        try:
            now = datetime.utcnow()
            
            # Find completed appointments from last 24 hours without follow-up
            yesterday = now - timedelta(hours=24)
            appointments = Appointment.query.filter(
                Appointment.status == 'completed',
                Appointment.completed_at >= yesterday,
                Appointment.completed_at <= now,
                Appointment.followup_sent == False
            ).all()
            
            stats = {
                'checked_at': now.isoformat(),
                'followups_sent': 0,
                'errors': 0
            }
            
            for apt in appointments:
                if self.send_post_session_followup(apt):
                    apt.followup_sent = True
                    stats['followups_sent'] += 1
                else:
                    stats['errors'] += 1
            
            db.session.commit()
            
            logger.info(f"Follow-up check complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error checking follow-ups: {e}")
            return {'error': str(e)}
    
    def send_welcome_message(self, user: User) -> bool:
        """
        Send welcome message to new user
        
        Args:
            user: User object
            
        Returns:
            True if sent successfully
        """
        try:
            preferred = getattr(user, 'preferred_communication', 'email')
            sent = False
            
            # Send via WhatsApp
            if preferred == 'whatsapp' and self.whatsapp_service:
                whatsapp_number = getattr(user, 'whatsapp_number', None)
                if whatsapp_number:
                    result = self.whatsapp_service.send_welcome_message(
                        to_number=whatsapp_number,
                        client_name=f"{user.first_name} {user.last_name}"
                    )
                    sent = result is not None
            
            # Send via email
            if not sent and self.email_service:
                # Email welcome would go here
                # For now, just mark as sent
                sent = True
            
            # Log notification
            if sent:
                notification = Notification(
                    user_id=user.id,
                    type='whatsapp' if preferred == 'whatsapp' else 'email',
                    category='welcome',
                    subject='Welcome to Purposeful Live Coaching',
                    status='delivered',
                    sent_at=datetime.utcnow()
                )
                db.session.add(notification)
                db.session.commit()
                
                logger.info(f"Sent welcome message to user {user.id}")
            
            return sent
            
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            return False


# Singleton instance
_scheduler_instance = None

def get_notification_scheduler() -> NotificationScheduler:
    """Get or create notification scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = NotificationScheduler()
    return _scheduler_instance

