from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import stripe
from models import db, User, Client, Payment, PaymentStatus, SubscriptionTier
from auth import log_audit_action, get_current_user
from datetime import datetime, timedelta

payments_bp = Blueprint('payments', __name__)

TIER_PRICES = {
    SubscriptionTier.SHIFT_SESSION: {'amount': 3500, 'name': 'Shift Session'},
    SubscriptionTier.CLARITY_PLUS: {'amount': 7500, 'name': 'Clarity+'},
    SubscriptionTier.MASTERY: {'amount': 19500, 'name': 'Mastery'}
}

def init_stripe():
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

@payments_bp.route('/create-payment-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    try:
        init_stripe()
        user = get_current_user()
        
        if not user or user.role.value != 'client':
            return jsonify({'error': 'Only clients can make payments'}), 403
        
        data = request.get_json()
        tier = data.get('tier')
        
        try:
            subscription_tier = SubscriptionTier(tier)
        except ValueError:
            return jsonify({'error': 'Invalid subscription tier'}), 400
        
        if subscription_tier not in TIER_PRICES:
            return jsonify({'error': 'Tier pricing not found'}), 400
        
        amount = TIER_PRICES[subscription_tier]['amount']
        
        client_profile = Client.query.get(user.id)
        if not client_profile:
            return jsonify({'error': 'Client profile not found'}), 404
        
        if not client_profile.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                phone=user.phone
            )
            client_profile.stripe_customer_id = customer.id
            db.session.commit()
        
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            customer=client_profile.stripe_customer_id,
            metadata={
                'user_id': user.id,
                'subscription_tier': subscription_tier.value
            }
        )
        
        payment = Payment(
            user_id=user.id,
            stripe_payment_intent_id=intent.id,
            amount=amount / 100,
            subscription_tier=subscription_tier,
            status=PaymentStatus.PENDING
        )
        
        db.session.add(payment)
        db.session.commit()
        
        log_audit_action('payment_intent_created', 'payment', payment.id, {
            'amount': amount / 100,
            'tier': subscription_tier.value
        })
        
        return jsonify({
            'client_secret': intent.client_secret,
            'payment_id': payment.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create payment intent'}), 500

@payments_bp.route('/create-subscription', methods=['POST'])
@jwt_required()
def create_subscription():
    try:
        init_stripe()
        user = get_current_user()
        
        if not user or user.role.value != 'client':
            return jsonify({'error': 'Only clients can create subscriptions'}), 403
        
        data = request.get_json()
        tier = data.get('tier')
        payment_method_id = data.get('payment_method_id')
        
        if not payment_method_id:
            return jsonify({'error': 'Payment method is required'}), 400
        
        try:
            subscription_tier = SubscriptionTier(tier)
        except ValueError:
            return jsonify({'error': 'Invalid subscription tier'}), 400
        
        client_profile = Client.query.get(user.id)
        if not client_profile:
            return jsonify({'error': 'Client profile not found'}), 404
        
        if not client_profile.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                phone=user.phone
            )
            client_profile.stripe_customer_id = customer.id
        
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=client_profile.stripe_customer_id
        )
        
        stripe.Customer.modify(
            client_profile.stripe_customer_id,
            invoice_settings={'default_payment_method': payment_method_id}
        )
        
        price_data = {
            'currency': 'usd',
            'product_data': {
                'name': TIER_PRICES[subscription_tier]['name']
            },
            'unit_amount': TIER_PRICES[subscription_tier]['amount'],
            'recurring': {'interval': 'month'}
        }
        
        subscription = stripe.Subscription.create(
            customer=client_profile.stripe_customer_id,
            items=[{'price_data': price_data}],
            expand=['latest_invoice.payment_intent']
        )
        
        client_profile.subscription_tier = subscription_tier
        
        payment = Payment(
            user_id=user.id,
            stripe_subscription_id=subscription.id,
            amount=TIER_PRICES[subscription_tier]['amount'] / 100,
            subscription_tier=subscription_tier,
            status=PaymentStatus.COMPLETED,
            billing_period_start=datetime.fromtimestamp(subscription.current_period_start),
            billing_period_end=datetime.fromtimestamp(subscription.current_period_end)
        )
        
        db.session.add(payment)
        db.session.commit()
        
        log_audit_action('subscription_created', 'payment', payment.id, {
            'subscription_id': subscription.id,
            'tier': subscription_tier.value
        })
        
        return jsonify({
            'subscription_id': subscription.id,
            'status': subscription.status,
            'payment_id': payment.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create subscription'}), 500

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    try:
        init_stripe()
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
            )
        except ValueError:
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            return jsonify({'error': 'Invalid signature'}), 400
        
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent['id']
            ).first()
            
            if payment:
                payment.status = PaymentStatus.COMPLETED
                
                client = Client.query.get(payment.user_id)
                if client and payment.subscription_tier:
                    client.subscription_tier = payment.subscription_tier
                
                db.session.commit()
                
                log_audit_action('payment_completed', 'payment', payment.id)
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent['id']
            ).first()
            
            if payment:
                payment.status = PaymentStatus.FAILED
                db.session.commit()
                
                log_audit_action('payment_failed', 'payment', payment.id)
        
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            subscription_id = invoice['subscription']
            
            payment = Payment.query.filter_by(
                stripe_subscription_id=subscription_id
            ).order_by(Payment.created_at.desc()).first()
            
            if payment:
                new_payment = Payment(
                    user_id=payment.user_id,
                    stripe_subscription_id=subscription_id,
                    amount=invoice['amount_paid'] / 100,
                    subscription_tier=payment.subscription_tier,
                    status=PaymentStatus.COMPLETED,
                    billing_period_start=datetime.fromtimestamp(invoice['period_start']),
                    billing_period_end=datetime.fromtimestamp(invoice['period_end'])
                )
                
                db.session.add(new_payment)
                db.session.commit()
                
                log_audit_action('subscription_payment_completed', 'payment', new_payment.id)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Webhook processing failed'}), 500

@payments_bp.route('/history', methods=['GET'])
@jwt_required()
def payment_history():
    try:
        user = get_current_user()
        
        payments = Payment.query.filter_by(user_id=user.id).order_by(
            Payment.created_at.desc()
        ).all()
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch payment history'}), 500

@payments_bp.route('/cancel-subscription', methods=['POST'])
@jwt_required()
def cancel_subscription():
    try:
        init_stripe()
        user = get_current_user()
        
        if not user or user.role.value != 'client':
            return jsonify({'error': 'Only clients can cancel subscriptions'}), 403
        
        client_profile = Client.query.get(user.id)
        if not client_profile:
            return jsonify({'error': 'Client profile not found'}), 404
        
        active_payment = Payment.query.filter_by(
            user_id=user.id,
            status=PaymentStatus.COMPLETED
        ).filter(
            Payment.stripe_subscription_id.isnot(None)
        ).order_by(Payment.created_at.desc()).first()
        
        if not active_payment:
            return jsonify({'error': 'No active subscription found'}), 404
        
        stripe.Subscription.delete(active_payment.stripe_subscription_id)
        
        client_profile.subscription_tier = None
        db.session.commit()
        
        log_audit_action('subscription_cancelled', 'payment', active_payment.id)
        
        return jsonify({'message': 'Subscription cancelled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel subscription'}), 500
