"""
WhatsApp Business Service Integration
Handles client communication and notifications via WhatsApp
"""

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for integrating with WhatsApp Business API via Twilio"""
    
    def __init__(self, account_sid: str, auth_token: str, whatsapp_number: str):
        """
        Initialize WhatsApp service
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            whatsapp_number: WhatsApp Business number (format: +14155238886)
        """
        self.client = Client(account_sid, auth_token)
        self.from_number = f"whatsapp:{whatsapp_number}"
        self.crisis_hotlines = {
            "suicide_lifeline": "988",
            "crisis_text_line": "741741",
            "emergency": "911"
        }
    
    def send_message(self, to_number: str, message: str) -> Optional[Dict]:
        """
        Send a WhatsApp message
        
        Args:
            to_number: Recipient phone number (format: +1234567890)
            message: Message text to send
            
        Returns:
            Message details dictionary or None if failed
        """
        try:
            message_obj = self.client.messages.create(
                from_=self.from_number,
                body=message,
                to=f"whatsapp:{to_number}"
            )
            
            result = {
                "sid": message_obj.sid,
                "status": message_obj.status,
                "to": to_number,
                "sent_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"WhatsApp message sent successfully: {message_obj.sid}")
            return result
            
        except TwilioRestException as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return None
    
    def send_appointment_confirmation(
        self,
        to_number: str,
        client_name: str,
        appointment_time: datetime,
        zoom_link: str,
        coach_name: str = "Your Coach"
    ) -> Optional[Dict]:
        """
        Send appointment confirmation via WhatsApp
        
        Args:
            to_number: Client phone number
            client_name: Client's first name
            appointment_time: Scheduled appointment time
            zoom_link: Zoom meeting link
            coach_name: Name of assigned coach
            
        Returns:
            Message details dictionary or None if failed
        """
        message = f"""Hi {client_name}! 👋

Your coaching session is confirmed:

📅 Date: {appointment_time.strftime('%B %d, %Y')}
🕐 Time: {appointment_time.strftime('%I:%M %p %Z')}
👤 Coach: {coach_name}

🔗 Zoom Link: {zoom_link}

We're looking forward to supporting you on your wellness journey!

💡 Tip: Join 5 minutes early to test your audio/video.

Reply CANCEL to reschedule or contact support.""".strip()
        
        return self.send_message(to_number, message)
    
    def send_reminder(
        self,
        to_number: str,
        client_name: str,
        appointment_time: datetime,
        zoom_link: str,
        hours_before: int = 24
    ) -> Optional[Dict]:
        """
        Send appointment reminder
        
        Args:
            to_number: Client phone number
            client_name: Client's first name
            appointment_time: Scheduled appointment time
            zoom_link: Zoom meeting link
            hours_before: Hours before appointment (for message text)
            
        Returns:
            Message details dictionary or None if failed
        """
        time_text = "tomorrow" if hours_before == 24 else f"in {hours_before} hours"
        
        message = f"""Hi {client_name}! 

⏰ Reminder: Your coaching session is {time_text}.

📅 {appointment_time.strftime('%B %d at %I:%M %p %Z')}

🔗 Zoom Link: {zoom_link}

See you soon! 💪

Reply READY when you're prepared for the session.""".strip()
        
        return self.send_message(to_number, message)
    
    def send_post_session_followup(
        self,
        to_number: str,
        client_name: str,
        session_summary_link: str = None,
        action_items: str = None
    ) -> Optional[Dict]:
        """
        Send post-session follow-up message
        
        Args:
            to_number: Client phone number
            client_name: Client's first name
            session_summary_link: Optional link to session summary
            action_items: Optional action items text
            
        Returns:
            Message details dictionary or None if failed
        """
        message = f"""Hi {client_name}! 

Thank you for your coaching session today! 🌟

"""
        
        if action_items:
            message += f"""📋 Your Action Items:
{action_items}

"""
        
        if session_summary_link:
            message += f"""📄 Session Summary: {session_summary_link}

"""
        
        message += """💬 How are you feeling after the session?

Your progress matters to us. Keep moving forward! 💙

Reply with any questions or concerns.""".strip()
        
        return self.send_message(to_number, message)
    
    def send_crisis_alert(
        self,
        to_number: str,
        client_name: str,
        crisis_level: str = "ELEVATED"
    ) -> Optional[Dict]:
        """
        Send immediate support message for crisis situations
        
        Args:
            to_number: Client phone number
            client_name: Client's first name
            crisis_level: Crisis severity level (LOW, ELEVATED, CRITICAL)
            
        Returns:
            Message details dictionary or None if failed
        """
        if crisis_level == "CRITICAL":
            message = f"""{client_name}, we're here for you. 🆘

If you're in immediate danger or having thoughts of self-harm:

📞 Call 988 (Suicide & Crisis Lifeline)
💬 Text HOME to 741741 (Crisis Text Line)
🚨 Call 911 for emergencies

Your coach will reach out within 1 hour.

You are not alone. We care about you. 💙"""
        else:
            message = f"""Hi {client_name},

We noticed you might be going through a difficult time. 💙

Remember, support is always available:

📞 988 - Suicide & Crisis Lifeline (24/7)
💬 Text HOME to 741741 - Crisis Text Line

Your coach is here for you. Reply URGENT if you need immediate assistance.

You matter. 🌟"""
        
        return self.send_message(to_number, message.strip())
    
    def send_payment_confirmation(
        self,
        to_number: str,
        client_name: str,
        amount: float,
        tier: str,
        receipt_url: str = None
    ) -> Optional[Dict]:
        """
        Send payment confirmation message
        
        Args:
            to_number: Client phone number
            client_name: Client's first name
            amount: Payment amount
            tier: Subscription tier name
            receipt_url: Optional receipt URL
            
        Returns:
            Message details dictionary or None if failed
        """
        message = f"""Hi {client_name}! ✅

Your payment has been confirmed!

💳 Amount: ${amount:.2f}
📦 Plan: {tier}
"""
        
        if receipt_url:
            message += f"""🧾 Receipt: {receipt_url}
"""
        
        message += """
Welcome to Purposeful Live Coaching! 🎉

Your wellness journey starts now. Schedule your first session to get started.

Questions? Reply to this message anytime.""".strip()
        
        return self.send_message(to_number, message)
    
    def send_subscription_renewal_reminder(
        self,
        to_number: str,
        client_name: str,
        renewal_date: datetime,
        amount: float,
        tier: str
    ) -> Optional[Dict]:
        """
        Send subscription renewal reminder
        
        Args:
            to_number: Client phone number
            client_name: Client's first name
            renewal_date: Subscription renewal date
            amount: Renewal amount
            tier: Subscription tier name
            
        Returns:
            Message details dictionary or None if failed
        """
        days_until = (renewal_date - datetime.utcnow()).days
        
        message = f"""Hi {client_name}! 

Your {tier} subscription will renew in {days_until} days.

📅 Renewal Date: {renewal_date.strftime('%B %d, %Y')}
💳 Amount: ${amount:.2f}

Your wellness journey continues! 🌟

To update payment method or cancel, visit your account settings.

Questions? Reply to this message.""".strip()
        
        return self.send_message(to_number, message)
    
    def send_welcome_message(
        self,
        to_number: str,
        client_name: str,
        dashboard_link: str = None
    ) -> Optional[Dict]:
        """
        Send welcome message to new clients
        
        Args:
            to_number: Client phone number
            client_name: Client's first name
            dashboard_link: Optional dashboard URL
            
        Returns:
            Message details dictionary or None if failed
        """
        message = f"""Welcome to Purposeful Live Coaching, {client_name}! 🎉

We're excited to support you on your wellness journey! 💙

Here's what happens next:
1️⃣ Complete your initial assessment
2️⃣ Schedule your first session
3️⃣ Meet your coach and start your transformation

"""
        
        if dashboard_link:
            message += f"""🔗 Access your dashboard: {dashboard_link}

"""
        
        message += """💬 You'll receive updates and reminders via WhatsApp.

Reply HELP anytime for assistance.

Let's get started! 🚀""".strip()
        
        return self.send_message(to_number, message)
    
    def send_opt_in_request(
        self,
        to_number: str,
        client_name: str
    ) -> Optional[Dict]:
        """
        Request WhatsApp opt-in from client
        
        Args:
            to_number: Client phone number
            client_name: Client's first name
            
        Returns:
            Message details dictionary or None if failed
        """
        message = f"""Hi {client_name}!

Would you like to receive coaching updates, reminders, and support via WhatsApp? 📱

Reply YES to opt in for WhatsApp notifications.
Reply NO to receive updates via email only.

You can change this preference anytime in your account settings.""".strip()
        
        return self.send_message(to_number, message)
    
    def handle_incoming_message(self, message_body: str, from_number: str) -> Dict:
        """
        Process incoming WhatsApp messages
        
        Args:
            message_body: Message text received
            from_number: Sender's phone number
            
        Returns:
            Dictionary with processing instructions
        """
        message_lower = message_body.strip().lower()
        
        # Handle common responses
        if message_lower in ["yes", "y", "ok", "okay"]:
            return {"action": "opt_in", "from": from_number}
        
        elif message_lower in ["no", "n", "stop", "unsubscribe"]:
            return {"action": "opt_out", "from": from_number}
        
        elif message_lower in ["cancel", "reschedule"]:
            return {"action": "reschedule_request", "from": from_number}
        
        elif message_lower in ["urgent", "crisis", "help"]:
            return {"action": "crisis_escalation", "from": from_number}
        
        elif message_lower in ["ready", "prepared"]:
            return {"action": "session_ready_confirmation", "from": from_number}
        
        else:
            return {"action": "forward_to_support", "from": from_number, "message": message_body}

