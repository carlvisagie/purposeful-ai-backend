"""
Health Check Blueprint
System health and status monitoring endpoints
"""

from flask import Blueprint, jsonify
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    
    Returns:
        JSON response with system status
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Purposeful Live Coaching API',
        'version': '1.0.0'
    }), 200


@health_bp.route('/status', methods=['GET'])
def detailed_status():
    """
    Detailed system status check
    
    Returns:
        JSON response with detailed system information
    """
    try:
        from models import db
        
        # Check database connection
        try:
            db.session.execute('SELECT 1')
            database_status = 'connected'
        except Exception as e:
            database_status = f'error: {str(e)}'
            logger.error(f"Database health check failed: {e}")
        
        # Check environment variables
        required_env_vars = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL',
            'OPENAI_API_KEY'
        ]
        
        env_status = {}
        for var in required_env_vars:
            env_status[var] = 'set' if os.getenv(var) else 'missing'
        
        # Check optional integrations
        integrations = {
            'stripe': 'configured' if os.getenv('STRIPE_SECRET_KEY') else 'not_configured',
            'calendly': 'configured' if os.getenv('CALENDLY_API_KEY') else 'not_configured',
            'zoom': 'configured' if os.getenv('ZOOM_API_KEY') and os.getenv('ZOOM_API_SECRET') else 'not_configured',
            'whatsapp': 'configured' if os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN') else 'not_configured',
            'google_workspace': 'configured' if os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE') else 'not_configured'
        }
        
        return jsonify({
            'status': 'healthy' if database_status == 'connected' else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'Purposeful Live Coaching API',
            'version': '1.0.0',
            'database': database_status,
            'environment': env_status,
            'integrations': integrations
        }), 200
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500


@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    Kubernetes-style readiness check
    
    Returns:
        200 if ready to serve traffic, 503 if not ready
    """
    try:
        from models import db
        
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check critical environment variables
        critical_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        for var in critical_vars:
            if not os.getenv(var):
                return jsonify({
                    'status': 'not_ready',
                    'reason': f'Missing {var}'
                }), 503
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'status': 'not_ready',
            'reason': str(e)
        }), 503


@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """
    Kubernetes-style liveness check
    
    Returns:
        200 if application is alive
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

