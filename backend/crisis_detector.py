from models import db, CrisisEvent, User
from flag_config import FLAG_MATRIX, CRISIS_FLAGS
import re
from datetime import datetime

class CrisisDetector:
    def __init__(self):
        self.suicide_keywords = CRISIS_FLAGS["suicide_keywords"]
        self.self_harm_keywords = CRISIS_FLAGS["self_harm_keywords"]
        self.severe_depression_keywords = CRISIS_FLAGS["severe_depression_keywords"]
        self.substance_abuse_keywords = CRISIS_FLAGS["substance_abuse_keywords"]
    
    def analyze_text(self, text, user_id=None):
        text_lower = text.lower()
        crisis_flags = []
        severity = 0
        
        for keyword in self.suicide_keywords:
            if keyword in text_lower:
                crisis_flags.append(f"Suicide ideation: {keyword}")
                severity = max(severity, 5)
        
        for keyword in self.self_harm_keywords:
            if keyword in text_lower:
                crisis_flags.append(f"Self-harm indicator: {keyword}")
                severity = max(severity, 4)
        
        for keyword in self.severe_depression_keywords:
            if keyword in text_lower:
                crisis_flags.append(f"Severe depression: {keyword}")
                severity = max(severity, 3)
        
        for keyword in self.substance_abuse_keywords:
            if keyword in text_lower:
                crisis_flags.append(f"Substance abuse: {keyword}")
                severity = max(severity, 3)
        
        for category, flags in FLAG_MATRIX.items():
            if category in ['mental_health', 'emotional']:
                for flag in flags:
                    if flag.lower() in text_lower:
                        crisis_flags.append(f"{category}: {flag}")
                        severity = max(severity, 2)
        
        if severity >= 3 and user_id:
            self.log_crisis_event(user_id, severity, crisis_flags)
        
        return {
            'severity': severity,
            'flags': crisis_flags,
            'requires_escalation': severity >= 4,
            'immediate_intervention': severity >= 5,
            'crisis_resources': self.get_crisis_resources(severity)
        }
    
    def log_crisis_event(self, user_id, severity, flags):
        crisis_event = CrisisEvent(
            user_id=user_id,
            severity=severity,
            flags=flags,
            escalated=severity >= 4
        )
        db.session.add(crisis_event)
        db.session.commit()
        
        if severity >= 4:
            self.escalate_crisis(crisis_event)
        
        return crisis_event
    
    def escalate_crisis(self, crisis_event):
        print(f"CRISIS ESCALATION: User {crisis_event.user_id}, Severity {crisis_event.severity}")
        return True
    
    def get_crisis_resources(self, severity):
        if severity >= 5:
            return {
                "immediate_help": "988 Suicide & Crisis Lifeline",
                "text_line": "Text HOME to 741741",
                "emergency": "Call 911 if in immediate danger"
            }
        elif severity >= 4:
            return {
                "crisis_line": "988 Suicide & Crisis Lifeline",
                "text_support": "Text HOME to 741741"
            }
        elif severity >= 3:
            return {
                "support_line": "SAMHSA National Helpline: 1-800-662-4357"
            }
        return {}
