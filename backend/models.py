from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()

class UserRole(enum.Enum):
    CLIENT = "client"
    COACH = "coach"
    ADMIN = "admin"

class SubscriptionTier(enum.Enum):
    SHIFT_SESSION = "Shift Session"
    CLARITY_PLUS = "Clarity+"
    MASTERY = "Mastery"

class CrisisLevel(enum.Enum):
    LOW = "low"
    ELEVATED = "elevated"
    CRITICAL = "critical"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CLIENT)
    
    age = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    
    subscription_tier = db.Column(db.Enum(SubscriptionTier))
    subscription_active = db.Column(db.Boolean, default=False)
    subscription_expires = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(100))
    
    chronic_conditions = db.Column(db.Text)  # JSON string
    medications = db.Column(db.Text)  # JSON string
    lifestyle_habits = db.Column(db.Text)  # JSON string
    
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    sessions = db.relationship('Session', backref='user', lazy=True, cascade='all, delete-orphan')
    crisis_alerts = db.relationship('CrisisAlert', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value,
            'subscription_tier': self.subscription_tier.value if self.subscription_tier else None,
            'subscription_active': self.subscription_active,
            'created_at': self.created_at.isoformat()
        }

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    input_text = db.Column(db.Text, nullable=False)
    diagnostic_results = db.Column(db.Text)  # JSON string
    ai_response = db.Column(db.Text)
    
    mortality_risk = db.Column(db.Enum(CrisisLevel))
    tier_mismatch = db.Column(db.Boolean)
    missing_info = db.Column(db.Text)  # JSON string
    
    session_duration = db.Column(db.Integer)  # seconds
    client_rating = db.Column(db.Float)  # 1-5 rating
    coach_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'mortality_risk': self.mortality_risk.value if self.mortality_risk else None,
            'tier_mismatch': self.tier_mismatch,
            'client_rating': self.client_rating,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class CrisisAlert(db.Model):
    __tablename__ = 'crisis_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'))
    
    crisis_level = db.Column(db.Enum(CrisisLevel), nullable=False)
    trigger_text = db.Column(db.Text)
    risk_factors = db.Column(db.Text)  # JSON string
    
    alert_sent = db.Column(db.Boolean, default=False)
    alert_sent_at = db.Column(db.DateTime)
    coach_notified = db.Column(db.Boolean, default=False)
    emergency_contacted = db.Column(db.Boolean, default=False)
    
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'crisis_level': self.crisis_level.value,
            'alert_sent': self.alert_sent,
            'resolved': self.resolved,
            'created_at': self.created_at.isoformat()
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    stripe_payment_intent_id = db.Column(db.String(100), unique=True)
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(3), default='USD')
    subscription_tier = db.Column(db.Enum(SubscriptionTier), nullable=False)
    
    status = db.Column(db.String(20), default='pending')  # pending, succeeded, failed
    payment_method = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='payments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount / 100,  # Convert cents to dollars
            'currency': self.currency,
            'subscription_tier': self.subscription_tier.value,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
