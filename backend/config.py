import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    secret_key: str
    debug: bool = False
    
    database_url: str = "sqlite:///purposeful.db"  # Default to SQLite for development
    
    openai_api_key: str = ""
    
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    
    jwt_secret_key: str = ""
    
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    crisis_alert_email: str = ""
    emergency_contact_phone: str = ""
    
    @classmethod
    def from_env(cls):
        return cls(
            secret_key=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
            debug=os.getenv("FLASK_ENV") == "development",
            database_url=os.getenv("DATABASE_URL", "sqlite:///purposeful.db"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            stripe_publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY", ""),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", ""),
            smtp_server=os.getenv("SMTP_SERVER", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            crisis_alert_email=os.getenv("CRISIS_ALERT_EMAIL", ""),
            emergency_contact_phone=os.getenv("EMERGENCY_CONTACT_PHONE", "")
        )
    
    def validate(self):
        """Validate required configuration"""
        errors = []
        
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        
        if not self.secret_key or self.secret_key == "dev-secret-key-change-in-production":
            if not self.debug:
                errors.append("SECRET_KEY must be set for production")
        
        if not self.jwt_secret_key:
            errors.append("JWT_SECRET_KEY is required for authentication")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
