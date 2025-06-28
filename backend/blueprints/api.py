from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Session, User, CrisisLevel
from services.crisis_service import CrisisDetectionService
from services.payment_service import PaymentService
from diagnostic_engine import diagnose_client_responses
from mortality_screen import calculate_mortality_risk
from tier_validator import is_tier_mismatch
from missing_info_warning import check_missing_info
from ai_engine import generate_ai_response
from datetime import datetime, timezone
import logging
import json

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/run_diagnostic', methods=['POST'])
@jwt_required()
def run_diagnostic():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data or "text" not in data:
            return jsonify({"error": "Missing or invalid JSON input."}), 400

        text_input = data["text"]
        age = data.get("age", 0)
        chronic = data.get("chronic", [])
        habits = data.get("habits", [])
        tier = data.get("tier", "")
        client_data = data.get("client_data", {})

        profile = diagnose_client_responses(text_input)
        risk = calculate_mortality_risk(age, chronic, habits)
        mismatch = is_tier_mismatch(risk, tier)
        missing = check_missing_info(client_data)
        
        crisis_analysis = CrisisDetectionService.analyze_text(text_input, current_user_id)
        
        ai_response = generate_ai_response(f"Provide supportive coaching response to: {text_input}")
        
        session = Session(
            user_id=current_user_id,
            input_text=text_input,
            diagnostic_results=json.dumps(profile),
            ai_response=ai_response,
            mortality_risk=CrisisLevel(risk) if risk in ['low', 'elevated', 'critical'] else CrisisLevel.LOW,
            tier_mismatch=mismatch,
            missing_info=json.dumps(missing)
        )
        
        db.session.add(session)
        db.session.commit()
        
        if crisis_analysis['crisis_level'] in [CrisisLevel.ELEVATED, CrisisLevel.CRITICAL]:
            CrisisDetectionService.create_alert(
                current_user_id, 
                session.id, 
                crisis_analysis, 
                text_input
            )

        return jsonify({
            "profile": profile,
            "mortality_risk": risk,
            "tier_mismatch": mismatch,
            "missing_info": missing,
            "ai_response": ai_response,
            "crisis_analysis": {
                "level": crisis_analysis['crisis_level'].value,
                "requires_attention": crisis_analysis['requires_immediate_attention']
            },
            "session_id": session.id
        })
        
    except Exception as e:
        logger.error(f"Diagnostic error: {e}")
        db.session.rollback()
        return jsonify({"error": "Diagnostic processing failed"}), 500

@api_bp.route('/create_payment_intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        tier_name = data.get('tier')
        if not tier_name:
            return jsonify({'error': 'Subscription tier required'}), 400
        
        from models import SubscriptionTier
        tier_map = {
            'Shift Session': SubscriptionTier.SHIFT_SESSION,
            'Clarity+': SubscriptionTier.CLARITY_PLUS,
            'Mastery': SubscriptionTier.MASTERY
        }
        
        tier = tier_map.get(tier_name)
        if not tier:
            return jsonify({'error': 'Invalid subscription tier'}), 400
        
        intent = PaymentService.create_payment_intent(current_user_id, tier)
        
        return jsonify({
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id
        }), 200
        
    except Exception as e:
        logger.error(f"Payment intent creation error: {e}")
        return jsonify({'error': 'Failed to create payment intent'}), 500

@api_bp.route('/payment_success', methods=['POST'])
@jwt_required()
def payment_success():
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return jsonify({'error': 'Payment intent ID required'}), 400
        
        success = PaymentService.handle_payment_success(payment_intent_id)
        
        if success:
            return jsonify({'message': 'Payment processed successfully'}), 200
        else:
            return jsonify({'error': 'Payment processing failed'}), 400
            
    except Exception as e:
        logger.error(f"Payment success handling error: {e}")
        return jsonify({'error': 'Payment processing failed'}), 500

@api_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_user_sessions():
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        sessions = Session.query.filter_by(user_id=current_user_id).order_by(
            Session.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions.items],
            'total': sessions.total,
            'pages': sessions.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f"Sessions retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve sessions'}), 500

@api_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_user_payments():
    try:
        current_user_id = get_jwt_identity()
        payments = PaymentService.get_user_payments(current_user_id)
        
        return jsonify({'payments': payments}), 200
        
    except Exception as e:
        logger.error(f"Payments retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve payments'}), 500
