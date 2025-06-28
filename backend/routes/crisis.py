from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, CrisisAlert, CrisisSeverity, Session, Client, User, Coach
from auth import get_current_user, log_audit_action, role_required, UserRole
from diagnostic_engine import calculate_crisis_score, analyze_behavioral_patterns
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

crisis_bp = Blueprint('crisis', __name__)

def send_crisis_alert_email(client, crisis_alert, escalation_contacts):
    try:
        if not current_app.config.get('MAIL_SERVER'):
            return False
        
        msg = MIMEMultipart()
        msg['From'] = current_app.config['MAIL_USERNAME']
        msg['Subject'] = f"CRISIS ALERT - {crisis_alert.severity.name} - Client {client.user.first_name} {client.user.last_name}"
        
        body = f"""
        CRISIS ALERT - IMMEDIATE ATTENTION REQUIRED

        Severity: {crisis_alert.severity.name}
        Client: {client.user.first_name} {client.user.last_name}
        Email: {client.user.email}
        Phone: {client.user.phone or 'Not provided'}
        
        Emergency Contact: {client.emergency_contact_name or 'Not provided'}
        Emergency Phone: {client.emergency_contact_phone or 'Not provided'}
        
        Crisis Message:
        {crisis_alert.message}
        
        Trigger Flags:
        {', '.join(crisis_alert.trigger_flags) if crisis_alert.trigger_flags else 'None'}
        
        Alert Time: {crisis_alert.created_at}
        Alert ID: {crisis_alert.id}
        
        IMMEDIATE ACTION REQUIRED:
        - Contact client immediately
        - Assess safety and risk level
        - Consider emergency services if necessary
        - Document all interventions
        
        This is an automated alert from the Purposeful Live Crisis Detection System.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        if current_app.config['MAIL_USE_TLS']:
            server.starttls()
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
        
        for contact in escalation_contacts:
            msg['To'] = contact
            server.send_message(msg)
            del msg['To']
        
        server.quit()
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send crisis alert email: {str(e)}")
        return False

@crisis_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_crisis_risk():
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data.get('text'):
            return jsonify({'error': 'Text input is required'}), 400
        
        text_input = data['text']
        session_id = data.get('session_id')
        
        crisis_analysis = calculate_crisis_score(text_input)
        
        if user.role == UserRole.CLIENT:
            client = Client.query.get(user.id)
            if not client:
                return jsonify({'error': 'Client profile not found'}), 404
            
            session_history = []
            if client.sessions:
                session_history = [s.to_dict() for s in client.sessions.limit(10).all()]
            
            behavioral_patterns = analyze_behavioral_patterns(session_history)
            
            if crisis_analysis['requires_escalation']:
                crisis_alert = CrisisAlert(
                    client_id=client.id,
                    session_id=session_id,
                    severity=crisis_analysis['severity'],
                    trigger_flags=crisis_analysis['indicators'],
                    message=f"Crisis detected in client input: {text_input[:200]}..."
                )
                
                db.session.add(crisis_alert)
                db.session.flush()
                
                escalation_contacts = []
                if current_app.config.get('CRISIS_ALERT_EMAIL'):
                    escalation_contacts.append(current_app.config['CRISIS_ALERT_EMAIL'])
                
                if client.assigned_coach:
                    escalation_contacts.append(client.assigned_coach.user.email)
                
                if escalation_contacts:
                    email_sent = send_crisis_alert_email(client, crisis_alert, escalation_contacts)
                    crisis_alert.escalated_to = ', '.join(escalation_contacts)
                    crisis_alert.escalation_method = 'email' if email_sent else 'failed'
                
                db.session.commit()
                
                log_audit_action('crisis_alert_created', 'crisis_alert', crisis_alert.id, {
                    'severity': crisis_analysis['severity'].name,
                    'score': crisis_analysis['score']
                })
                
                return jsonify({
                    'crisis_analysis': {
                        'score': crisis_analysis['score'],
                        'severity': crisis_analysis['severity'].name,
                        'indicators': crisis_analysis['indicators'],
                        'requires_escalation': crisis_analysis['requires_escalation']
                    },
                    'behavioral_patterns': behavioral_patterns,
                    'alert_created': True,
                    'alert_id': crisis_alert.id
                }), 200
            
            return jsonify({
                'crisis_analysis': {
                    'score': crisis_analysis['score'],
                    'severity': crisis_analysis['severity'].name,
                    'indicators': crisis_analysis['indicators'],
                    'requires_escalation': crisis_analysis['requires_escalation']
                },
                'behavioral_patterns': behavioral_patterns,
                'alert_created': False
            }), 200
        
        else:
            return jsonify({
                'crisis_analysis': {
                    'score': crisis_analysis['score'],
                    'severity': crisis_analysis['severity'].name,
                    'indicators': crisis_analysis['indicators'],
                    'requires_escalation': crisis_analysis['requires_escalation']
                }
            }), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Crisis analysis failed'}), 500

@crisis_bp.route('/alerts', methods=['GET'])
@role_required(UserRole.COACH, UserRole.ADMIN)
def get_crisis_alerts():
    try:
        user = get_current_user()
        
        query = CrisisAlert.query
        
        if user.role == UserRole.COACH:
            coach = Coach.query.get(user.id)
            if coach:
                client_ids = [c.id for c in coach.assigned_clients]
                query = query.filter(CrisisAlert.client_id.in_(client_ids))
        
        status = request.args.get('status', 'active')
        if status == 'active':
            query = query.filter(CrisisAlert.resolved_at.is_(None))
        elif status == 'resolved':
            query = query.filter(CrisisAlert.resolved_at.isnot(None))
        
        severity = request.args.get('severity')
        if severity:
            try:
                severity_enum = CrisisSeverity(int(severity))
                query = query.filter(CrisisAlert.severity == severity_enum)
            except ValueError:
                pass
        
        alerts = query.order_by(CrisisAlert.created_at.desc()).limit(50).all()
        
        alerts_data = []
        for alert in alerts:
            alert_dict = alert.to_dict()
            alert_dict['client_name'] = f"{alert.client.user.first_name} {alert.client.user.last_name}"
            alert_dict['client_email'] = alert.client.user.email
            alerts_data.append(alert_dict)
        
        return jsonify({'alerts': alerts_data}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch crisis alerts'}), 500

@crisis_bp.route('/alerts/<alert_id>/resolve', methods=['POST'])
@role_required(UserRole.COACH, UserRole.ADMIN)
def resolve_crisis_alert(alert_id):
    try:
        user = get_current_user()
        data = request.get_json()
        
        alert = CrisisAlert.query.get(alert_id)
        if not alert:
            return jsonify({'error': 'Crisis alert not found'}), 404
        
        if alert.resolved_at:
            return jsonify({'error': 'Alert already resolved'}), 400
        
        if user.role == UserRole.COACH:
            coach = Coach.query.get(user.id)
            if not coach or alert.client_id not in [c.id for c in coach.assigned_clients]:
                return jsonify({'error': 'Unauthorized to resolve this alert'}), 403
        
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user.id
        alert.resolution_notes = data.get('resolution_notes', '').strip() or None
        
        db.session.commit()
        
        log_audit_action('crisis_alert_resolved', 'crisis_alert', alert_id, {
            'resolution_notes': alert.resolution_notes
        })
        
        return jsonify({
            'message': 'Crisis alert resolved successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to resolve crisis alert'}), 500

@crisis_bp.route('/emergency-contacts', methods=['GET'])
@role_required(UserRole.ADMIN)
def get_emergency_contacts():
    try:
        contacts = {
            'crisis_alert_email': current_app.config.get('CRISIS_ALERT_EMAIL'),
            'crisis_alert_phone': current_app.config.get('CRISIS_ALERT_PHONE'),
            'national_suicide_prevention': '988',
            'emergency_services': '911'
        }
        
        return jsonify({'contacts': contacts}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch emergency contacts'}), 500

@crisis_bp.route('/statistics', methods=['GET'])
@role_required(UserRole.COACH, UserRole.ADMIN)
def get_crisis_statistics():
    try:
        user = get_current_user()
        
        query = CrisisAlert.query
        
        if user.role == UserRole.COACH:
            coach = Coach.query.get(user.id)
            if coach:
                client_ids = [c.id for c in coach.assigned_clients]
                query = query.filter(CrisisAlert.client_id.in_(client_ids))
        
        total_alerts = query.count()
        active_alerts = query.filter(CrisisAlert.resolved_at.is_(None)).count()
        resolved_alerts = query.filter(CrisisAlert.resolved_at.isnot(None)).count()
        
        severity_counts = {}
        for severity in CrisisSeverity:
            count = query.filter(CrisisAlert.severity == severity).count()
            severity_counts[severity.name] = count
        
        recent_alerts = query.filter(
            CrisisAlert.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        return jsonify({
            'statistics': {
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'resolved_alerts': resolved_alerts,
                'recent_alerts_today': recent_alerts,
                'severity_breakdown': severity_counts
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch crisis statistics'}), 500
