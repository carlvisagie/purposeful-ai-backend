"""
Calendly Service Integration
Handles appointment scheduling and calendar management
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CalendlyService:
    """Service for integrating with Calendly API"""
    
    def __init__(self, api_key: str):
        """
        Initialize Calendly service
        
        Args:
            api_key: Calendly Personal Access Token
        """
        self.api_key = api_key
        self.base_url = "https://api.calendly.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_current_user(self) -> Optional[Dict]:
        """
        Get current authenticated user information
        
        Returns:
            User data dictionary or None if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get current user: {e}")
            return None
    
    def get_user_event_types(self, user_uri: str) -> List[Dict]:
        """
        Get available event types for scheduling
        
        Args:
            user_uri: Calendly user URI
            
        Returns:
            List of event type dictionaries
        """
        try:
            response = requests.get(
                f"{self.base_url}/event_types",
                headers=self.headers,
                params={"user": user_uri, "active": True}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("collection", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get event types: {e}")
            return []
    
    def create_scheduling_link(
        self, 
        event_type_uri: str, 
        client_email: str, 
        client_name: str
    ) -> str:
        """
        Generate personalized scheduling link with prefilled client information
        
        Args:
            event_type_uri: URI of the event type
            client_email: Client's email address
            client_name: Client's full name
            
        Returns:
            Scheduling URL with prefilled parameters
        """
        # Extract scheduling URL from event type URI
        scheduling_url = event_type_uri.replace("/event_types/", "/")
        
        # Add query parameters for prefilled information
        params = f"?email={client_email}&name={client_name.replace(' ', '%20')}"
        
        return f"https://calendly.com{scheduling_url}{params}"
    
    def get_scheduled_event(self, event_uuid: str) -> Optional[Dict]:
        """
        Get details of a scheduled event
        
        Args:
            event_uuid: UUID of the scheduled event
            
        Returns:
            Event data dictionary or None if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/scheduled_events/{event_uuid}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get scheduled event: {e}")
            return None
    
    def get_event_invitees(self, event_uuid: str) -> List[Dict]:
        """
        Get invitees for a scheduled event
        
        Args:
            event_uuid: UUID of the scheduled event
            
        Returns:
            List of invitee dictionaries
        """
        try:
            response = requests.get(
                f"{self.base_url}/scheduled_events/{event_uuid}/invitees",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("collection", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get event invitees: {e}")
            return []
    
    def cancel_event(self, event_uuid: str, reason: str = None) -> bool:
        """
        Cancel a scheduled event
        
        Args:
            event_uuid: UUID of the scheduled event
            reason: Optional cancellation reason
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {}
            if reason:
                payload["reason"] = reason
            
            response = requests.post(
                f"{self.base_url}/scheduled_events/{event_uuid}/cancellation",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Successfully cancelled event {event_uuid}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to cancel event: {e}")
            return False
    
    def handle_webhook(self, payload: Dict) -> Dict:
        """
        Process Calendly webhook events
        
        Args:
            payload: Webhook payload from Calendly
            
        Returns:
            Dictionary with processing results
        """
        event_type = payload.get("event")
        
        if event_type == "invitee.created":
            return self._handle_invitee_created(payload)
        elif event_type == "invitee.canceled":
            return self._handle_invitee_canceled(payload)
        else:
            logger.warning(f"Unhandled webhook event type: {event_type}")
            return {"status": "ignored", "event_type": event_type}
    
    def _handle_invitee_created(self, payload: Dict) -> Dict:
        """
        Handle new appointment booking
        
        Args:
            payload: Webhook payload
            
        Returns:
            Processing result dictionary
        """
        try:
            event_data = payload.get("payload", {})
            event_uri = event_data.get("event")
            invitee_uri = event_data.get("uri")
            
            # Extract event UUID from URI
            event_uuid = event_uri.split("/")[-1] if event_uri else None
            
            if not event_uuid:
                return {"status": "error", "message": "Missing event UUID"}
            
            # Get full event details
            event_details = self.get_scheduled_event(event_uuid)
            
            if not event_details:
                return {"status": "error", "message": "Failed to fetch event details"}
            
            # Get invitee details
            invitees = self.get_event_invitees(event_uuid)
            
            return {
                "status": "success",
                "event_type": "invitee.created",
                "event_uuid": event_uuid,
                "event_details": event_details,
                "invitees": invitees,
                "action_required": "create_zoom_meeting_and_notify"
            }
        except Exception as e:
            logger.error(f"Error handling invitee.created webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_invitee_canceled(self, payload: Dict) -> Dict:
        """
        Handle appointment cancellation
        
        Args:
            payload: Webhook payload
            
        Returns:
            Processing result dictionary
        """
        try:
            event_data = payload.get("payload", {})
            event_uri = event_data.get("event")
            cancellation_reason = event_data.get("cancellation", {}).get("reason")
            
            event_uuid = event_uri.split("/")[-1] if event_uri else None
            
            return {
                "status": "success",
                "event_type": "invitee.canceled",
                "event_uuid": event_uuid,
                "reason": cancellation_reason,
                "action_required": "notify_cancellation_and_cleanup"
            }
        except Exception as e:
            logger.error(f"Error handling invitee.canceled webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_organization_memberships(self, user_uri: str) -> List[Dict]:
        """
        Get organization memberships for a user
        
        Args:
            user_uri: Calendly user URI
            
        Returns:
            List of organization membership dictionaries
        """
        try:
            response = requests.get(
                f"{self.base_url}/organization_memberships",
                headers=self.headers,
                params={"user": user_uri}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("collection", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get organization memberships: {e}")
            return []

