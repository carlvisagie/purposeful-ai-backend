from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
from enum import Enum

db = SQLAlchemy()

class UserRole(Enum):
    CLIENT = "client"
    COACH = "coach"
    ADMIN = "admin"

class SubscriptionTier(Enum):
    SHIFT_SESSION = "shift_session"
    CLARITY_PLUS = "clarity_plus"
    MASTERY = "mastery"

class CrisisSeverity(Enum):
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CLIENT)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role.value,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relationship = db.Column(db.String(50))
    medical_conditions = db.Column(db.Text)
    medications = db.Column(db.Text)
    allergies = db.Column(db.Text)
    subscription_tier = db.Column(db.Enum(SubscriptionTier))
    stripe_customer_id = db.Column(db.String(100))
    assigned_coach_id = db.Column(db.String(36), db.ForeignKey('coaches.id'))
    risk_level = db.Column(db.Integer, default=1)
    
    user = db.relationship('User', backref='client_profile')
    assigned_coach = db.relationship('Coach', backref='assigned_clients')
    sessions = db.relationship('Session', backref='client', lazy='dynamic')
    crisis_alerts = db.relationship('CrisisAlert', backref='client', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relationship': self.emergency_contact_relationship,
            'medical_conditions': self.medical_conditions,
            'medications': self.medications,
            'allergies': self.allergies,
            'subscription_tier': self.subscription_tier.value if self.subscription_tier else None,
            'assigned_coach_id': self.assigned_coach_id,
            'risk_level': self.risk_level
        }

class Coach(db.Model):
    __tablename__ = 'coaches'
    
    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    license_number = db.Column(db.String(50))
    specializations = db.Column(db.Text)
    bio = db.Column(db.Text)
    hourly_rate = db.Column(db.Decimal(10, 2))
    availability = db.Column(db.Text)
    max_clients = db.Column(db.Integer, default=20)
    
    user = db.relationship('User', backref='coach_profile')
    sessions = db.relationship('Session', backref='coach', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'license_number': self.license_number,
            'specializations': self.specializations,
            'bio': self.bio,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'availability': self.availability,
            'max_clients': self.max_clients,
            'current_client_count': len(self.assigned_clients)
        }

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    coach_id = db.Column(db.String(36), db.ForeignKey('coaches.id'))
    session_type = db.Column(db.String(50), nullable=False)
    scheduled_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)
    client_feedback = db.Column(db.Text)
    coach_feedback = db.Column(db.Text)
    diagnostic_flags = db.Column(db.JSON)
    risk_level = db.Column(db.Integer, default=1)
    session_rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'coach_id': self.coach_id,
            'session_type': self.session_type,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_minutes': self.duration_minutes,
            'notes': self.notes,
            'client_feedback': self.client_feedback,
            'coach_feedback': self.coach_feedback,
            'diagnostic_flags': self.diagnostic_flags,
            'risk_level': self.risk_level,
            'session_rating': self.session_rating,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    stripe_payment_intent_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    amount = db.Column(db.Decimal(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    status = db.Column(db.Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    subscription_tier = db.Column(db.Enum(SubscriptionTier))
    billing_period_start = db.Column(db.DateTime)
    billing_period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = db.relationship('User', backref='payments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status.value,
            'subscription_tier': self.subscription_tier.value if self.subscription_tier else None,
            'billing_period_start': self.billing_period_start.isoformat() if self.billing_period_start else None,
            'billing_period_end': self.billing_period_end.isoformat() if self.billing_period_end else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CrisisAlert(db.Model):
    __tablename__ = 'crisis_alerts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    session_id = db.Column(db.String(36), db.ForeignKey('sessions.id'))
    severity = db.Column(db.Enum(CrisisSeverity), nullable=False)
    trigger_flags = db.Column(db.JSON)
    message = db.Column(db.Text, nullable=False)
    escalated_to = db.Column(db.String(100))
    escalation_method = db.Column(db.String(50))
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    resolution_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    session = db.relationship('Session', backref='crisis_alerts')
    resolved_by_user = db.relationship('User', foreign_keys=[resolved_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'session_id': self.session_id,
            'severity': self.severity.value,
            'trigger_flags': self.trigger_flags,
            'message': self.message,
            'escalated_to': self.escalated_to,
            'escalation_method': self.escalation_method,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.String(36))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user = db.relationship('User', backref='audit_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat()
        }
