from flag_config import FLAG_MATRIX
from models import CrisisSeverity
import re

def diagnose_client_responses(text_input):
    profile = {k: [] for k in FLAG_MATRIX if isinstance(FLAG_MATRIX[k], list)}
    lowered = text_input.lower()
    
    for category, flags in FLAG_MATRIX.items():
        if isinstance(flags, list):
            for flag in flags:
                words = flag.lower().split()
                if any(word in lowered for word in words):
                    profile[category].append(flag)
    
    return profile

def calculate_crisis_score(text_input, diagnostic_flags=None):
    if diagnostic_flags is None:
        diagnostic_flags = diagnose_client_responses(text_input)
    
    score = 0
    crisis_indicators = []
    
    suicide_keywords = [
        'kill myself', 'end it all', 'suicide', 'suicidal', 'want to die',
        'better off dead', 'no point living', 'end my life', 'harm myself'
    ]
    
    self_harm_keywords = [
        'cut myself', 'hurt myself', 'self harm', 'self-harm', 'cutting',
        'burning myself', 'hitting myself'
    ]
    
    severe_depression_keywords = [
        'hopeless', 'worthless', 'nothing matters', 'can\'t go on',
        'everything is pointless', 'no way out', 'trapped'
    ]
    
    substance_abuse_keywords = [
        'drinking too much', 'using drugs', 'overdose', 'pills to cope',
        'alcohol problem', 'substance abuse', 'getting high'
    ]
    
    text_lower = text_input.lower()
    
    for keyword in suicide_keywords:
        if keyword in text_lower:
            score += 5
            crisis_indicators.append(f"Suicide ideation: '{keyword}'")
    
    for keyword in self_harm_keywords:
        if keyword in text_lower:
            score += 4
            crisis_indicators.append(f"Self-harm indication: '{keyword}'")
    
    for keyword in severe_depression_keywords:
        if keyword in text_lower:
            score += 2
            crisis_indicators.append(f"Severe depression: '{keyword}'")
    
    for keyword in substance_abuse_keywords:
        if keyword in text_lower:
            score += 2
            crisis_indicators.append(f"Substance abuse: '{keyword}'")
    
    mental_health_flags = diagnostic_flags.get('mental_health', [])
    if len(mental_health_flags) >= 3:
        score += 2
        crisis_indicators.append(f"Multiple mental health flags: {mental_health_flags}")
    
    emotional_flags = diagnostic_flags.get('emotional', [])
    if len(emotional_flags) >= 2:
        score += 1
        crisis_indicators.append(f"Multiple emotional flags: {emotional_flags}")
    
    if score >= 5:
        severity = CrisisSeverity.EMERGENCY
    elif score >= 3:
        severity = CrisisSeverity.CRITICAL
    elif score >= 2:
        severity = CrisisSeverity.HIGH
    elif score >= 1:
        severity = CrisisSeverity.MODERATE
    else:
        severity = CrisisSeverity.LOW
    
    return {
        'score': score,
        'severity': severity,
        'indicators': crisis_indicators,
        'requires_escalation': score >= 3
    }

def analyze_behavioral_patterns(session_history):
    patterns = {
        'late_night_activity': False,
        'missed_sessions': 0,
        'sentiment_decline': False,
        'engagement_drop': False
    }
    
    if not session_history:
        return patterns
    
    recent_sessions = session_history[-5:] if len(session_history) >= 5 else session_history
    
    late_night_count = 0
    missed_count = 0
    
    for session in recent_sessions:
        if session.get('created_at'):
            from datetime import datetime
            session_time = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
            if session_time.hour >= 23 or session_time.hour <= 5:
                late_night_count += 1
        
        if session.get('status') == 'missed':
            missed_count += 1
    
    patterns['late_night_activity'] = late_night_count >= 2
    patterns['missed_sessions'] = missed_count
    patterns['engagement_drop'] = missed_count >= 2
    
    if len(recent_sessions) >= 3:
        ratings = [s.get('session_rating', 0) for s in recent_sessions if s.get('session_rating')]
        if len(ratings) >= 3:
            early_avg = sum(ratings[:2]) / 2
            recent_avg = sum(ratings[-2:]) / 2
            patterns['sentiment_decline'] = recent_avg < early_avg - 1
    
    return patterns
