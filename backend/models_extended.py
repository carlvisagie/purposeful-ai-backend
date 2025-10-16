"""
Extended Database Models
Additional models for appointments, notifications, and onboarding tracking
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

# Import base db from models.py
from models import db


class Appointment(db.Model):
    """Model for coaching session appointments"""
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    coach_id = Column(Integer, ForeignKey('users.id'))
    
    # Integration IDs
    calendly_event_id = Column(String(100), unique=True)
    calendly_event_uri = Column(String(200))
    zoom_meeting_id = Column(String(100))
    zoom_meeting_uuid = Column(String(100))
    google_calendar_event_id = Column(String(200))
    
    # Appointment details
    scheduled_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    timezone = Column(String(50), default='UTC')
    status = Column(String(20), default='scheduled')  # scheduled, completed, cancelled, no_show
    
    # Meeting details
    zoom_join_url = Column(String(500))
    zoom_start_url = Column(String(500))
    zoom_password = Column(String(50))
    
    # Session data
    meeting_notes = Column(Text)
    recording_url = Column(String(500))
    recording_password = Column(String(50))
    ai_summary = Column(Text)
    action_items = Column(Text)
    
    # Attendance tracking
    client_joined_at = Column(DateTime)
    client_left_at = Column(DateTime)
    coach_joined_at = Column(DateTime)
    coach_left_at = Column(DateTime)
    actual_duration_minutes = Column(Integer)
    
    # Notifications
    confirmation_sent = Column(Boolean, default=False)
    confirmation_sent_at = Column(DateTime)
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_24h_sent_at = Column(DateTime)
    reminder_1h_sent = Column(Boolean, default=False)
    reminder_1h_sent_at = Column(DateTime)
    followup_sent = Column(Boolean, default=False)
    followup_sent_at = Column(DateTime)
    
    # Metadata
    cancellation_reason = Column(Text)
    cancelled_by = Column(String(20))  # client, coach, system
    rescheduled_from = Column(Integer, ForeignKey('appointments.id'))
    rescheduled_to = Column(Integer, ForeignKey('appointments.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship('User', foreign_keys=[user_id], backref='client_appointments')
    coach = relationship('User', foreign_keys=[coach_id], backref='coach_appointments')
    
    def to_dict(self):
        """Convert appointment to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'coach_id': self.coach_id,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'zoom_join_url': self.zoom_join_url,
            'recording_url': self.recording_url,
            'ai_summary': self.ai_summary,
            'action_items': self.action_items,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Notification(db.Model):
    """Model for tracking all notifications sent to users"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.id'))
    
    # Notification details
    type = Column(String(50), nullable=False)  # email, whatsapp, sms
    category = Column(String(50), nullable=False)  # appointment, crisis, payment, general, onboarding
    subject = Column(String(200))
    message = Column(Text, nullable=False)
    
    # Delivery tracking
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    status = Column(String(20), default='pending')  # pending, sent, delivered, failed, read
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # External IDs
    external_id = Column(String(100))  # Twilio message SID, SendGrid message ID, etc.
    
    # Metadata
    metadata = Column(Text)  # JSON string for additional data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='notifications')
    appointment = relationship('Appointment', backref='notifications')
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'category': self.category,
            'subject': self.subject,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class OnboardingProgress(db.Model):
    """Model for tracking user onboarding progress"""
    __tablename__ = 'onboarding_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Onboarding steps
    step_registration = Column(Boolean, default=False)
    step_registration_at = Column(DateTime)
    
    step_assessment = Column(Boolean, default=False)
    step_assessment_at = Column(DateTime)
    
    step_tier_selection = Column(Boolean, default=False)
    step_tier_selection_at = Column(DateTime)
    
    step_payment = Column(Boolean, default=False)
    step_payment_at = Column(DateTime)
    
    step_scheduling = Column(Boolean, default=False)
    step_scheduling_at = Column(DateTime)
    
    step_confirmation = Column(Boolean, default=False)
    step_confirmation_at = Column(DateTime)
    
    # Overall status
    current_step = Column(Integer, default=1)  # 1-6
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    # Assessment results
    recommended_tier = Column(String(50))
    assessment_score = Column(Integer)
    crisis_level = Column(String(20))
    
    # Metadata
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='onboarding_progress', uselist=False)
    
    def to_dict(self):
        """Convert onboarding progress to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'current_step': self.current_step,
            'is_completed': self.is_completed,
            'steps': {
                'registration': self.step_registration,
                'assessment': self.step_assessment,
                'tier_selection': self.step_tier_selection,
                'payment': self.step_payment,
                'scheduling': self.step_scheduling,
                'confirmation': self.step_confirmation
            },
            'recommended_tier': self.recommended_tier,
            'started_at': self.started_at.isoformat() if self.started_at else None
        }


class WebhookLog(db.Model):
    """Model for logging webhook events from external services"""
    __tablename__ = 'webhook_logs'
    
    id = Column(Integer, primary_key=True)
    
    # Webhook details
    source = Column(String(50), nullable=False)  # calendly, zoom, stripe
    event_type = Column(String(100), nullable=False)
    event_id = Column(String(200))
    
    # Payload
    payload = Column(Text, nullable=False)  # JSON string
    headers = Column(Text)  # JSON string
    
    # Processing
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    processing_result = Column(Text)  # JSON string
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert webhook log to dictionary"""
        return {
            'id': self.id,
            'source': self.source,
            'event_type': self.event_type,
            'processed': self.processed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Extension to existing User model (add these fields to models.py)
"""
Add these fields to the User model in models.py:

# Integration fields
calendly_user_uri = Column(String(200))
whatsapp_number = Column(String(20))
whatsapp_opt_in = Column(Boolean, default=False)
google_calendar_id = Column(String(200))
preferred_communication = Column(String(20), default='email')  # email, whatsapp, both

# Onboarding tracking
onboarding_completed = Column(Boolean, default=False)
onboarding_completed_at = Column(DateTime)
"""

