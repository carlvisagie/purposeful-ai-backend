import stripe
import os
from models import db, Payment, User, SubscriptionTier
from datetime import datetime, timedelta, timezone
import logging

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
logger = logging.getLogger(__name__)

TIER_PRICES = {
    SubscriptionTier.SHIFT_SESSION: 3500,
    SubscriptionTier.CLARITY_PLUS: 7500,
    SubscriptionTier.MASTERY: 19500
}

class PaymentService:
    @staticmethod
    def create_payment_intent(user_id, tier, amount=None):
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            if amount is None:
                amount = TIER_PRICES.get(tier)
            
            if not amount:
                raise ValueError("Invalid subscription tier")
            
            if not user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=f"{user.first_name} {user.last_name}"
                )
                user.stripe_customer_id = customer.id
                db.session.commit()
            
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                customer=user.stripe_customer_id,
                metadata={
                    'user_id': user_id,
                    'subscription_tier': tier.value
                }
            )
            
            payment = Payment(
                user_id=user_id,
                stripe_payment_intent_id=intent.id,
                amount=amount,
                subscription_tier=tier,
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            logger.info(f"Payment intent created for user {user_id}: {intent.id}")
            
            return intent
            
        except Exception as e:
            logger.error(f"Payment intent creation failed: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def handle_payment_success(payment_intent_id):
        try:
            payment = Payment.query.filter_by(stripe_payment_intent_id=payment_intent_id).first()
            if not payment:
                logger.error(f"Payment not found for intent: {payment_intent_id}")
                return False
            
            payment.status = 'succeeded'
            payment.paid_at = datetime.now(timezone.utc)
            
            user = payment.user
            user.subscription_tier = payment.subscription_tier
            user.subscription_active = True
            user.subscription_expires = datetime.now(timezone.utc) + timedelta(days=30)
            
            db.session.commit()
            
            logger.info(f"Payment successful for user {user.id}: {payment_intent_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Payment success handling failed: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def handle_payment_failure(payment_intent_id):
        try:
            payment = Payment.query.filter_by(stripe_payment_intent_id=payment_intent_id).first()
            if payment:
                payment.status = 'failed'
                db.session.commit()
                logger.info(f"Payment failed for user {payment.user_id}: {payment_intent_id}")
            
        except Exception as e:
            logger.error(f"Payment failure handling failed: {e}")
            db.session.rollback()
    
    @staticmethod
    def get_user_payments(user_id):
        try:
            payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()
            return [payment.to_dict() for payment in payments]
            
        except Exception as e:
            logger.error(f"Failed to get user payments: {e}")
            return []
