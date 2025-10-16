"""
Onboarding API Blueprint
Handles complete client onboarding workflow
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
import json

# Import services
from services.calendly_service import CalendlyService
from services.zoom_service import ZoomService
from services.whatsapp_service import WhatsAppService
from services.enhanced_payment_service import EnhancedPaymentService

# Import models
from models import db, User
from models_extended import Appointment, Notification, OnboardingProgress

# Import existing diagnostic engine
from diagnostic_engine import run_full_diagnostic

import os

logger = logging.getLogger(__name__)

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/api/onboarding')

# Initialize services
calendly_service = CalendlyService(os.getenv('CALENDLY_API_KEY', ''))
zoom_service = ZoomService(os.getenv('ZOOM_API_KEY', ''), os.getenv('ZOOM_API_SECRET', ''))
whatsapp_service = WhatsAppService(
    os.getenv('TWILIO_ACCOUNT_SID', ''),
    os.getenv('TWILIO_AUTH_TOKEN', ''),
    os.getenv('TWILIO_WHATSAPP_NUMBER', '')
)
payment_service = EnhancedPaymentService(os.getenv('STRIPE_SECRET_KEY', ''))


@onboarding_bp.route('/start', methods=['POST'])
@jwt_required()
def start_onboarding():
    """
    Initialize onboarding process for authenticated user
    
    Returns:
        JSON response with onboarding status
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if onboarding already exists
        progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
        
        if not progress:
            # Create new onboarding progress
            progress = OnboardingProgress(
                user_id=user_id,
                step_registration=True,
                step_registration_at=datetime.utcnow(),
                current_step=2  # Registration is complete, move to assessment
            )
            db.session.add(progress)
            db.session.commit()
        
        logger.info(f"Onboarding started for user {user_id}")
        
        return jsonify({
            'message': 'Onboarding started',
            'progress': progress.to_dict(),
            'next_step': 'assessment'
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting onboarding: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to start onboarding'}), 500


@onboarding_bp.route('/assessment', methods=['POST'])
@jwt_required()
def complete_assessment():
    """
    Process initial assessment and recommend tier
    
    Expected payload:
    {
        "text": "Client description",
        "age": 35,
        "chronic": ["condition1"],
        "habits": ["habit1"],
        "client_data": {...}
    }
    
    Returns:
        JSON response with assessment results and tier recommendation
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        data = request.get_json()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Run diagnostic engine
        assessment_results = run_full_diagnostic(data)
        
        # Determine recommended tier based on results
        crisis_level = assessment_results.get('crisis_level', 'LOW')
        mortality_risk = assessment_results.get('mortality_risk', 'low')
        
        # Tier recommendation logic
        if crisis_level == 'CRITICAL' or mortality_risk == 'critical':
            recommended_tier = 'Mastery'
        elif crisis_level == 'ELEVATED' or mortality_risk == 'elevated':
            recommended_tier = 'Clarity+'
        else:
            recommended_tier = 'Shift Session'
        
        # Update onboarding progress
        progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
        if progress:
            progress.step_assessment = True
            progress.step_assessment_at = datetime.utcnow()
            progress.current_step = 3
            progress.recommended_tier = recommended_tier
            progress.crisis_level = crisis_level
            progress.last_activity_at = datetime.utcnow()
            db.session.commit()
        
        # If critical crisis, send immediate alert
        if crisis_level == 'CRITICAL' and user.whatsapp_opt_in and user.whatsapp_number:
            whatsapp_service.send_crisis_alert(
                user.whatsapp_number,
                user.first_name,
                crisis_level
            )
        
        logger.info(f"Assessment completed for user {user_id}, recommended tier: {recommended_tier}")
        
        return jsonify({
            'message': 'Assessment completed',
            'assessment_results': assessment_results,
            'recommended_tier': recommended_tier,
            'tier_prices': {
                'Shift Session': 35,
                'Clarity+': 75,
                'Mastery': 195
            },
            'next_step': 'payment'
        }), 200
        
    except Exception as e:
        logger.error(f"Error completing assessment: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to complete assessment'}), 500


@onboarding_bp.route('/payment/create-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    """
    Create Stripe payment intent for selected tier
    
    Expected payload:
    {
        "tier": "Clarity+",
        "payment_type": "one_time" or "subscription"
    }
    
    Returns:
        JSON response with payment intent client secret
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        data = request.get_json()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        tier = data.get('tier')
        payment_type = data.get('payment_type', 'one_time')
        
        if tier not in ['Shift Session', 'Clarity+', 'Mastery']:
            return jsonify({'error': 'Invalid tier'}), 400
        
        # Get or create Stripe customer
        if not user.stripe_customer_id:
            customer_id = payment_service.create_customer(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                metadata={'user_id': user_id}
            )
            if customer_id:
                user.stripe_customer_id = customer_id
                db.session.commit()
        else:
            customer_id = user.stripe_customer_id
        
        if not customer_id:
            return jsonify({'error': 'Failed to create customer'}), 500
        
        # Get tier price
        amount = payment_service.get_tier_price(tier)
        
        # Create payment intent or subscription
        if payment_type == 'subscription':
            # For subscription, we need price IDs from Stripe dashboard
            price_id = os.getenv(f'STRIPE_PRICE_ID_{tier.upper().replace(" ", "_").replace("+", "PLUS")}')
            
            if not price_id:
                return jsonify({'error': 'Subscription not configured for this tier'}), 500
            
            result = payment_service.create_subscription(
                customer_id=customer_id,
                price_id=price_id,
                metadata={'user_id': user_id, 'tier': tier}
            )
        else:
            result = payment_service.create_payment_intent(
                customer_id=customer_id,
                amount=amount,
                metadata={'user_id': user_id, 'tier': tier, 'payment_type': 'one_time'}
            )
        
        if not result:
            return jsonify({'error': 'Failed to create payment'}), 500
        
        # Update onboarding progress
        progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
        if progress:
            progress.step_tier_selection = True
            progress.step_tier_selection_at = datetime.utcnow()
            progress.current_step = 4
            progress.last_activity_at = datetime.utcnow()
            db.session.commit()
        
        logger.info(f"Payment intent created for user {user_id}, tier: {tier}")
        
        return jsonify({
            'message': 'Payment intent created',
            'client_secret': result['client_secret'],
            'amount': amount,
            'tier': tier
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create payment intent'}), 500


@onboarding_bp.route('/scheduling/get-link', methods=['GET'])
@jwt_required()
def get_scheduling_link():
    """
    Get personalized Calendly scheduling link
    
    Returns:
        JSON response with Calendly scheduling URL
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify payment is complete
        progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
        if not progress or not progress.step_payment:
            return jsonify({'error': 'Payment required before scheduling'}), 403
        
        # Get Calendly user and event types
        calendly_user = calendly_service.get_current_user()
        if not calendly_user:
            return jsonify({'error': 'Calendly not configured'}), 500
        
        user_uri = calendly_user['resource']['uri']
        event_types = calendly_service.get_user_event_types(user_uri)
        
        if not event_types:
            return jsonify({'error': 'No event types available'}), 500
        
        # Use first active event type
        event_type_uri = event_types[0]['uri']
        
        # Create personalized scheduling link
        scheduling_url = calendly_service.create_scheduling_link(
            event_type_uri=event_type_uri,
            client_email=user.email,
            client_name=f"{user.first_name} {user.last_name}"
        )
        
        logger.info(f"Scheduling link generated for user {user_id}")
        
        return jsonify({
            'message': 'Scheduling link generated',
            'scheduling_url': scheduling_url,
            'event_type': event_types[0]['name']
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating scheduling link: {e}")
        return jsonify({'error': 'Failed to generate scheduling link'}), 500


@onboarding_bp.route('/complete', methods=['POST'])
@jwt_required()
def complete_onboarding():
    """
    Mark onboarding as complete
    
    Returns:
        JSON response with completion status
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update onboarding progress
        progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
        if progress:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
            progress.step_confirmation = True
            progress.step_confirmation_at = datetime.utcnow()
            progress.current_step = 6
            progress.last_activity_at = datetime.utcnow()
            db.session.commit()
        
        # Update user record
        user.onboarding_completed = True
        user.onboarding_completed_at = datetime.utcnow()
        db.session.commit()
        
        # Send welcome message
        if user.whatsapp_opt_in and user.whatsapp_number:
            dashboard_url = os.getenv('FRONTEND_URL', 'https://purposefullivecoaching.academy') + '/dashboard'
            whatsapp_service.send_welcome_message(
                user.whatsapp_number,
                user.first_name,
                dashboard_url
            )
        
        logger.info(f"Onboarding completed for user {user_id}")
        
        return jsonify({
            'message': 'Onboarding completed',
            'user': user.to_dict(),
            'redirect_to': '/dashboard'
        }), 200
        
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to complete onboarding'}), 500


@onboarding_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_onboarding_progress():
    """
    Get current onboarding progress for user
    
    Returns:
        JSON response with progress details
    """
    try:
        user_id = get_jwt_identity()
        progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
        
        if not progress:
            return jsonify({'error': 'Onboarding not started'}), 404
        
        return jsonify({
            'progress': progress.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting onboarding progress: {e}")
        return jsonify({'error': 'Failed to get progress'}), 500

