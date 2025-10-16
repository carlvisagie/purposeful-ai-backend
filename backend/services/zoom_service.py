"""
Zoom Service Integration
Handles video meeting creation, management, and recording retrieval
"""

import requests
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ZoomService:
    """Service for integrating with Zoom Meeting API"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Zoom service
        
        Args:
            api_key: Zoom API Key
            api_secret: Zoom API Secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.zoom.us/v2"
        self.token = self._generate_jwt_token()
    
    def _generate_jwt_token(self, expiration_hours: int = 24) -> str:
        """
        Generate JWT token for Zoom API authentication
        
        Args:
            expiration_hours: Token expiration time in hours
            
        Returns:
            JWT token string
        """
        payload = {
            "iss": self.api_key,
            "exp": datetime.utcnow() + timedelta(hours=expiration_hours)
        }
        
        token = jwt.encode(payload, self.api_secret, algorithm="HS256")
        return token
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with authentication
        
        Returns:
            Headers dictionary
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def create_meeting(
        self,
        topic: str,
        start_time: datetime,
        duration: int = 60,
        timezone: str = "UTC",
        agenda: str = None,
        host_email: str = None
    ) -> Optional[Dict]:
        """
        Create a Zoom meeting for coaching session
        
        Args:
            topic: Meeting topic/title
            start_time: Meeting start time
            duration: Meeting duration in minutes
            timezone: Timezone for the meeting
            agenda: Optional meeting agenda
            host_email: Optional host email (uses 'me' if not provided)
            
        Returns:
            Meeting details dictionary or None if failed
        """
        try:
            user_id = host_email if host_email else "me"
            
            meeting_data = {
                "topic": topic,
                "type": 2,  # Scheduled meeting
                "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "duration": duration,
                "timezone": timezone,
                "agenda": agenda or f"Purposeful Live Coaching Session: {topic}",
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "join_before_host": False,
                    "waiting_room": True,
                    "audio": "both",
                    "auto_recording": "cloud",
                    "mute_upon_entry": True,
                    "approval_type": 2,  # No registration required
                    "registration_type": 1,
                    "meeting_authentication": False,
                    "watermark": False,
                    "use_pmi": False,
                    "alternative_hosts": "",
                    "close_registration": False,
                    "show_share_button": True,
                    "allow_multiple_devices": True,
                    "encryption_type": "enhanced_encryption",
                    "alternative_hosts_email_notification": True,
                    "breakout_room": {
                        "enable": False
                    },
                    "contact_name": "Purposeful Live Support",
                    "contact_email": "support@purposefullivecoaching.academy"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/users/{user_id}/meetings",
                headers=self._get_headers(),
                json=meeting_data
            )
            response.raise_for_status()
            
            meeting = response.json()
            
            result = {
                "meeting_id": meeting["id"],
                "meeting_uuid": meeting["uuid"],
                "join_url": meeting["join_url"],
                "start_url": meeting["start_url"],
                "password": meeting.get("password", ""),
                "encrypted_password": meeting.get("encrypted_password", ""),
                "h323_password": meeting.get("h323_password", ""),
                "pstn_password": meeting.get("pstn_password", ""),
                "host_id": meeting.get("host_id"),
                "created_at": meeting.get("created_at")
            }
            
            logger.info(f"Successfully created Zoom meeting: {meeting['id']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Zoom meeting: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def get_meeting(self, meeting_id: str) -> Optional[Dict]:
        """
        Get details of a Zoom meeting
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            Meeting details dictionary or None if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/meetings/{meeting_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get meeting details: {e}")
            return None
    
    def update_meeting(
        self,
        meeting_id: str,
        updates: Dict
    ) -> bool:
        """
        Update a Zoom meeting
        
        Args:
            meeting_id: Zoom meeting ID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.patch(
                f"{self.base_url}/meetings/{meeting_id}",
                headers=self._get_headers(),
                json=updates
            )
            response.raise_for_status()
            logger.info(f"Successfully updated meeting: {meeting_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update meeting: {e}")
            return False
    
    def delete_meeting(
        self,
        meeting_id: str,
        notify_hosts: bool = True,
        notify_registrants: bool = True
    ) -> bool:
        """
        Delete/cancel a Zoom meeting
        
        Args:
            meeting_id: Zoom meeting ID
            notify_hosts: Send notification to alternative hosts
            notify_registrants: Send notification to registrants
            
        Returns:
            True if successful, False otherwise
        """
        try:
            params = {
                "schedule_for_reminder": notify_hosts,
                "cancel_meeting_reminder": notify_registrants
            }
            
            response = requests.delete(
                f"{self.base_url}/meetings/{meeting_id}",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            logger.info(f"Successfully deleted meeting: {meeting_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete meeting: {e}")
            return False
    
    def get_recording(self, meeting_id: str) -> Optional[Dict]:
        """
        Retrieve recording after session
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            Recording details dictionary or None if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/meetings/{meeting_id}/recordings",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get recording: {e}")
            return None
    
    def list_recordings(
        self,
        user_id: str = "me",
        from_date: datetime = None,
        to_date: datetime = None
    ) -> List[Dict]:
        """
        List all recordings for a user
        
        Args:
            user_id: Zoom user ID (default: 'me')
            from_date: Start date for filtering
            to_date: End date for filtering
            
        Returns:
            List of recording dictionaries
        """
        try:
            params = {}
            if from_date:
                params["from"] = from_date.strftime("%Y-%m-%d")
            if to_date:
                params["to"] = to_date.strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{self.base_url}/users/{user_id}/recordings",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("meetings", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list recordings: {e}")
            return []
    
    def delete_recording(
        self,
        meeting_id: str,
        recording_id: str = None,
        delete_all: bool = False
    ) -> bool:
        """
        Delete meeting recording(s)
        
        Args:
            meeting_id: Zoom meeting ID
            recording_id: Specific recording ID to delete
            delete_all: Delete all recordings for the meeting
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if delete_all:
                url = f"{self.base_url}/meetings/{meeting_id}/recordings"
            elif recording_id:
                url = f"{self.base_url}/meetings/{meeting_id}/recordings/{recording_id}"
            else:
                logger.error("Must specify either recording_id or delete_all=True")
                return False
            
            response = requests.delete(
                url,
                headers=self._get_headers()
            )
            response.raise_for_status()
            logger.info(f"Successfully deleted recording(s) for meeting: {meeting_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete recording: {e}")
            return False
    
    def get_meeting_participants(self, meeting_id: str) -> List[Dict]:
        """
        Get list of participants who joined a meeting
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            List of participant dictionaries
        """
        try:
            response = requests.get(
                f"{self.base_url}/past_meetings/{meeting_id}/participants",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            return data.get("participants", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get meeting participants: {e}")
            return []
    
    def handle_webhook(self, payload: Dict) -> Dict:
        """
        Process Zoom webhook events
        
        Args:
            payload: Webhook payload from Zoom
            
        Returns:
            Dictionary with processing results
        """
        event_type = payload.get("event")
        
        if event_type == "meeting.started":
            return self._handle_meeting_started(payload)
        elif event_type == "meeting.ended":
            return self._handle_meeting_ended(payload)
        elif event_type == "recording.completed":
            return self._handle_recording_completed(payload)
        else:
            logger.warning(f"Unhandled webhook event type: {event_type}")
            return {"status": "ignored", "event_type": event_type}
    
    def _handle_meeting_started(self, payload: Dict) -> Dict:
        """Handle meeting started event"""
        try:
            meeting_data = payload.get("payload", {}).get("object", {})
            meeting_id = meeting_data.get("id")
            
            return {
                "status": "success",
                "event_type": "meeting.started",
                "meeting_id": meeting_id,
                "action_required": "log_meeting_start"
            }
        except Exception as e:
            logger.error(f"Error handling meeting.started webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_meeting_ended(self, payload: Dict) -> Dict:
        """Handle meeting ended event"""
        try:
            meeting_data = payload.get("payload", {}).get("object", {})
            meeting_id = meeting_data.get("id")
            duration = meeting_data.get("duration")
            
            return {
                "status": "success",
                "event_type": "meeting.ended",
                "meeting_id": meeting_id,
                "duration": duration,
                "action_required": "log_meeting_end_and_check_recording"
            }
        except Exception as e:
            logger.error(f"Error handling meeting.ended webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_recording_completed(self, payload: Dict) -> Dict:
        """Handle recording completed event"""
        try:
            recording_data = payload.get("payload", {}).get("object", {})
            meeting_id = recording_data.get("id")
            recording_files = recording_data.get("recording_files", [])
            
            return {
                "status": "success",
                "event_type": "recording.completed",
                "meeting_id": meeting_id,
                "recording_files": recording_files,
                "action_required": "store_recording_urls_and_notify_client"
            }
        except Exception as e:
            logger.error(f"Error handling recording.completed webhook: {e}")
            return {"status": "error", "message": str(e)}

