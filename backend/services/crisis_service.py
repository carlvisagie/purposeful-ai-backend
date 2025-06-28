import re
import smtplib
from email.mime.text import MIMEText
from models import db, CrisisAlert, CrisisLevel, User, Session
from config import Config
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class CrisisDetectionService:
    CRISIS_PATTERNS = {
        'suicide': {'weight': 10, 'level': CrisisLevel.CRITICAL},
        'kill myself': {'weight': 10, 'level': CrisisLevel.CRITICAL},
        'end it all': {'weight': 9, 'level': CrisisLevel.CRITICAL},
        'not worth living': {'weight': 8, 'level': CrisisLevel.CRITICAL},
        'want to die': {'weight': 8, 'level': CrisisLevel.CRITICAL},
        'self harm': {'weight': 7, 'level': CrisisLevel.ELEVATED},
        'cutting myself': {'weight': 7, 'level': CrisisLevel.ELEVATED},
        'hopeless': {'weight': 5, 'level': CrisisLevel.ELEVATED},
        'can\'t go on': {'weight': 6, 'level': CrisisLevel.ELEVATED},
        'overwhelming': {'weight': 3, 'level': CrisisLevel.LOW},
        'panic attack': {'weight': 4, 'level': CrisisLevel.ELEVATED},
        'worthless': {'weight': 4, 'level': CrisisLevel.ELEVATED},
        'no point': {'weight': 5, 'level': CrisisLevel.ELEVATED},
        'give up': {'weight': 4, 'level': CrisisLevel.ELEVATED}
    }
    
    @classmethod
    def analyze_text(cls, text, user_id=None):
        try:
            text_lower = text.lower()
            total_score = 0
            detected_patterns = []
            highest_level = CrisisLevel.LOW
            
            for pattern, data in cls.CRISIS_PATTERNS.items():
                if pattern in text_lower:
                    total_score += data['weight']
                    detected_patterns.append(pattern)
                    if data['level'].value == 'critical':
                        highest_level = CrisisLevel.CRITICAL
                    elif data['level'].value == 'elevated' and highest_level != CrisisLevel.CRITICAL:
                        highest_level = CrisisLevel.ELEVATED
            
            if total_score >= 8 or highest_level == CrisisLevel.CRITICAL:
                crisis_level = CrisisLevel.CRITICAL
            elif total_score >= 4 or highest_level == CrisisLevel.ELEVATED:
                crisis_level = CrisisLevel.ELEVATED
            else:
                crisis_level = CrisisLevel.LOW
            
            return {
                'crisis_level': crisis_level,
                'score': total_score,
                'patterns': detected_patterns,
                'requires_immediate_attention': crisis_level == CrisisLevel.CRITICAL
            }
            
        except Exception as e:
            logger.error(f"Crisis analysis failed: {e}")
            return {
                'crisis_level': CrisisLevel.LOW,
                'score': 0,
                'patterns': [],
                'requires_immediate_attention': False
            }
    
    @classmethod
    def create_alert(cls, user_id, session_id, analysis_result, trigger_text):
        try:
            alert = CrisisAlert(
                user_id=user_id,
                session_id=session_id,
                crisis_level=analysis_result['crisis_level'],
                trigger_text=trigger_text,
                risk_factors=str(analysis_result['patterns'])
            )
            
            db.session.add(alert)
            db.session.commit()
            
            if analysis_result['crisis_level'] == CrisisLevel.CRITICAL:
                cls.escalate_crisis(alert)
            
            logger.info(f"Crisis alert created for user {user_id}: {analysis_result['crisis_level'].value}")
            
            return alert
            
        except Exception as e:
            logger.error(f"Crisis alert creation failed: {e}")
            db.session.rollback()
            return None
    
    @classmethod
    def escalate_crisis(cls, alert):
        try:
            user = User.query.get(alert.user_id)
            
            cls.send_crisis_email(user, alert)
            
            alert.alert_sent = True
            alert.alert_sent_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.critical(f"Crisis alert escalated for user {user.id}: {alert.crisis_level.value}")
            
        except Exception as e:
            logger.error(f"Failed to escalate crisis alert: {e}")
    
    @classmethod
    def send_crisis_email(cls, user, alert):
        try:
            config = Config.from_env()
            
            if not config.crisis_alert_email:
                logger.warning("No crisis alert email configured")
                return
            
            subject = f"URGENT: Crisis Alert for {user.first_name} {user.last_name}"
            body = f"""
CRISIS ALERT - IMMEDIATE ATTENTION REQUIRED

User: {user.first_name} {user.last_name} ({user.email})
Crisis Level: {alert.crisis_level.value.upper()}
Time: {alert.created_at}

Trigger Text: {alert.trigger_text}

Emergency Contact: {user.emergency_contact_name} - {user.emergency_contact_phone}

Please contact this user immediately.
            """
            
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = config.smtp_username
            msg['To'] = config.crisis_alert_email
            
            if config.smtp_server and config.smtp_username and config.smtp_password:
                with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                    server.starttls()
                    server.login(config.smtp_username, config.smtp_password)
                    server.send_message(msg)
                    logger.info(f"Crisis email sent for user {user.id}")
            else:
                logger.warning("SMTP configuration incomplete, crisis email not sent")
                
        except Exception as e:
            logger.error(f"Failed to send crisis email: {e}")
    
    @classmethod
    def get_active_alerts(cls, limit=50):
        try:
            alerts = CrisisAlert.query.filter_by(resolved=False).order_by(
                CrisisAlert.created_at.desc()
            ).limit(limit).all()
            return [alert.to_dict() for alert in alerts]
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    @classmethod
    def resolve_alert(cls, alert_id, resolution_notes=None):
        try:
            alert = CrisisAlert.query.get(alert_id)
            if alert:
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                if resolution_notes:
                    alert.resolution_notes = resolution_notes
                db.session.commit()
                logger.info(f"Crisis alert {alert_id} resolved")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            db.session.rollback()
            return False
