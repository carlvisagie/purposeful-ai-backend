"""
Enhanced Payment Service
Complete Stripe integration with subscription management and webhooks
"""

import stripe
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EnhancedPaymentService:
    """Enhanced Stripe payment service with full subscription support"""
    
    # Subscription tier pricing (in cents)
    TIER_PRICES = {
        "Shift Session": 3500,      # $35
        "Clarity+": 7500,            # $75
        "Mastery": 19500             # $195
    }
    
    def __init__(self, stripe_secret_key: str):
        """
        Initialize payment service
        
        Args:
            stripe_secret_key: Stripe secret API key
        """
        stripe.api_key = stripe_secret_key
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    def create_customer(self, email: str, name: str, metadata: Dict = None) -> Optional[str]:
        """
        Create a Stripe customer
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Optional metadata dictionary
            
        Returns:
            Stripe customer ID or None if failed
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created Stripe customer: {customer.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            return None
    
    def create_payment_intent(
        self,
        customer_id: str,
        amount: int,
        currency: str = 'usd',
        metadata: Dict = None
    ) -> Optional[Dict]:
        """
        Create a payment intent for one-time payment
        
        Args:
            customer_id: Stripe customer ID
            amount: Amount in cents
            currency: Currency code
            metadata: Optional metadata
            
        Returns:
            Payment intent details or None if failed
        """
        try:
            intent = stripe.PaymentIntent.create(
                customer=customer_id,
                amount=amount,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            
            return {
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'amount': intent.amount,
                'status': intent.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            return None
    
    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Dict = None,
        trial_days: int = 0
    ) -> Optional[Dict]:
        """
        Create a subscription for recurring payments
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            metadata: Optional metadata
            trial_days: Number of trial days (0 for no trial)
            
        Returns:
            Subscription details or None if failed
        """
        try:
            subscription_params = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'metadata': metadata or {},
                'payment_behavior': 'default_incomplete',
                'payment_settings': {'save_default_payment_method': 'on_subscription'},
                'expand': ['latest_invoice.payment_intent']
            }
            
            if trial_days > 0:
                subscription_params['trial_period_days'] = trial_days
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            return {
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> bool:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Stripe subscription ID
            immediately: Cancel immediately vs at period end
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if immediately:
                stripe.Subscription.delete(subscription_id)
            else:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            logger.info(f"Cancelled subscription: {subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False
    
    def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> bool:
        """
        Update subscription to a different tier
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New price ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price_id
                }],
                proration_behavior='create_prorations'
            )
            logger.info(f"Updated subscription: {subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {e}")
            return False
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """
        Get subscription details
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription details or None if failed
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get subscription: {e}")
            return None
    
    def create_customer_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Optional[str]:
        """
        Create a customer portal session for subscription management
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session
            
        Returns:
            Portal session URL or None if failed
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {e}")
            return None
    
    def construct_webhook_event(self, payload: bytes, sig_header: str) -> Optional[stripe.Event]:
        """
        Verify and construct webhook event
        
        Args:
            payload: Request body bytes
            sig_header: Stripe signature header
            
        Returns:
            Stripe Event object or None if verification failed
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return None
    
    def handle_webhook_event(self, event: stripe.Event) -> Dict:
        """
        Process Stripe webhook events
        
        Args:
            event: Stripe Event object
            
        Returns:
            Processing result dictionary
        """
        event_type = event['type']
        
        handlers = {
            'payment_intent.succeeded': self._handle_payment_succeeded,
            'payment_intent.payment_failed': self._handle_payment_failed,
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'invoice.paid': self._handle_invoice_paid,
            'invoice.payment_failed': self._handle_invoice_payment_failed
        }
        
        handler = handlers.get(event_type)
        if handler:
            return handler(event['data']['object'])
        else:
            logger.warning(f"Unhandled webhook event type: {event_type}")
            return {'status': 'ignored', 'event_type': event_type}
    
    def _handle_payment_succeeded(self, payment_intent: Dict) -> Dict:
        """Handle successful payment"""
        return {
            'status': 'success',
            'event_type': 'payment_succeeded',
            'payment_intent_id': payment_intent['id'],
            'amount': payment_intent['amount'],
            'customer_id': payment_intent.get('customer'),
            'action_required': 'update_user_payment_status'
        }
    
    def _handle_payment_failed(self, payment_intent: Dict) -> Dict:
        """Handle failed payment"""
        return {
            'status': 'failed',
            'event_type': 'payment_failed',
            'payment_intent_id': payment_intent['id'],
            'customer_id': payment_intent.get('customer'),
            'error': payment_intent.get('last_payment_error', {}).get('message'),
            'action_required': 'notify_payment_failure'
        }
    
    def _handle_subscription_created(self, subscription: Dict) -> Dict:
        """Handle new subscription"""
        return {
            'status': 'success',
            'event_type': 'subscription_created',
            'subscription_id': subscription['id'],
            'customer_id': subscription['customer'],
            'status_detail': subscription['status'],
            'action_required': 'activate_user_subscription'
        }
    
    def _handle_subscription_updated(self, subscription: Dict) -> Dict:
        """Handle subscription update"""
        return {
            'status': 'success',
            'event_type': 'subscription_updated',
            'subscription_id': subscription['id'],
            'customer_id': subscription['customer'],
            'status_detail': subscription['status'],
            'cancel_at_period_end': subscription.get('cancel_at_period_end', False),
            'action_required': 'update_user_subscription_status'
        }
    
    def _handle_subscription_deleted(self, subscription: Dict) -> Dict:
        """Handle subscription cancellation"""
        return {
            'status': 'success',
            'event_type': 'subscription_deleted',
            'subscription_id': subscription['id'],
            'customer_id': subscription['customer'],
            'action_required': 'deactivate_user_subscription'
        }
    
    def _handle_invoice_paid(self, invoice: Dict) -> Dict:
        """Handle successful invoice payment"""
        return {
            'status': 'success',
            'event_type': 'invoice_paid',
            'invoice_id': invoice['id'],
            'subscription_id': invoice.get('subscription'),
            'customer_id': invoice['customer'],
            'amount_paid': invoice['amount_paid'],
            'action_required': 'record_payment_and_extend_subscription'
        }
    
    def _handle_invoice_payment_failed(self, invoice: Dict) -> Dict:
        """Handle failed invoice payment"""
        return {
            'status': 'failed',
            'event_type': 'invoice_payment_failed',
            'invoice_id': invoice['id'],
            'subscription_id': invoice.get('subscription'),
            'customer_id': invoice['customer'],
            'action_required': 'notify_payment_failure_and_retry'
        }
    
    def get_tier_price(self, tier_name: str) -> int:
        """
        Get price for a subscription tier
        
        Args:
            tier_name: Name of the tier
            
        Returns:
            Price in cents
        """
        return self.TIER_PRICES.get(tier_name, 0)
    
    def list_customer_payments(self, customer_id: str, limit: int = 10) -> list:
        """
        List payment history for a customer
        
        Args:
            customer_id: Stripe customer ID
            limit: Number of payments to retrieve
            
        Returns:
            List of payment intent dictionaries
        """
        try:
            payment_intents = stripe.PaymentIntent.list(
                customer=customer_id,
                limit=limit
            )
            return payment_intents.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list customer payments: {e}")
            return []

