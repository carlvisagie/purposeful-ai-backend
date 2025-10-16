"""
Google Workspace Service Integration
Handles calendar events, email notifications, and document management
"""

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GoogleWorkspaceService:
    """Service for integrating with Google Workspace (Calendar and Gmail)"""
    
    def __init__(self, credentials_json: Dict = None, service_account_file: str = None):
        """
        Initialize Google Workspace service
        
        Args:
            credentials_json: OAuth2 credentials dictionary
            service_account_file: Path to service account JSON file
        """
        if service_account_file:
            self.credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=[
                    'https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/gmail.send'
                ]
            )
        elif credentials_json:
            self.credentials = Credentials.from_authorized_user_info(credentials_json)
        else:
            raise ValueError("Must provide either credentials_json or service_account_file")
        
        self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
        self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
    
    def create_calendar_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        description: str = None,
        location: str = None,
        timezone: str = 'UTC',
        send_notifications: bool = True
    ) -> Optional[Dict]:
        """
        Create calendar event for coaching session
        
        Args:
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            attendees: List of attendee email addresses
            description: Event description
            location: Event location (can be Zoom link)
            timezone: Event timezone
            send_notifications: Send email notifications to attendees
            
        Returns:
            Event details dictionary or None if failed
        """
        try:
            event = {
                'summary': summary,
                'location': location or 'Virtual (Zoom)',
                'description': description or 'Purposeful Live Coaching Session',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                },
                'attendees': [{'email': email} for email in attendees],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'popup', 'minutes': 60},       # 1 hour before
                        {'method': 'email', 'minutes': 10},       # 10 minutes before
                    ],
                },
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
                'guestsCanSeeOtherGuests': False
            }
            
            created_event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
            
            logger.info(f"Successfully created calendar event: {created_event.get('id')}")
            
            return {
                'event_id': created_event.get('id'),
                'html_link': created_event.get('htmlLink'),
                'hangout_link': created_event.get('hangoutLink'),
                'created': created_event.get('created')
            }
            
        except HttpError as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None
    
    def update_calendar_event(
        self,
        event_id: str,
        updates: Dict,
        send_notifications: bool = True
    ) -> bool:
        """
        Update an existing calendar event
        
        Args:
            event_id: Google Calendar event ID
            updates: Dictionary of fields to update
            send_notifications: Send update notifications to attendees
            
        Returns:
            True if successful, False otherwise
        """
        try:
            event = self.calendar_service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update fields
            for key, value in updates.items():
                event[key] = value
            
            updated_event = self.calendar_service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
            
            logger.info(f"Successfully updated calendar event: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to update calendar event: {e}")
            return False
    
    def delete_calendar_event(
        self,
        event_id: str,
        send_notifications: bool = True
    ) -> bool:
        """
        Delete a calendar event
        
        Args:
            event_id: Google Calendar event ID
            send_notifications: Send cancellation notifications to attendees
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.calendar_service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
            
            logger.info(f"Successfully deleted calendar event: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to delete calendar event: {e}")
            return False
    
    def get_calendar_event(self, event_id: str) -> Optional[Dict]:
        """
        Get details of a calendar event
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Event details dictionary or None if failed
        """
        try:
            event = self.calendar_service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return event
        except HttpError as e:
            logger.error(f"Failed to get calendar event: {e}")
            return None
    
    def list_upcoming_events(
        self,
        max_results: int = 10,
        time_min: datetime = None
    ) -> List[Dict]:
        """
        List upcoming calendar events
        
        Args:
            max_results: Maximum number of events to return
            time_min: Minimum start time for events
            
        Returns:
            List of event dictionaries
        """
        try:
            if not time_min:
                time_min = datetime.utcnow()
            
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except HttpError as e:
            logger.error(f"Failed to list calendar events: {e}")
            return []
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str = None,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> Optional[Dict]:
        """
        Send email via Gmail API
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            
        Returns:
            Message details dictionary or None if failed
        """
        try:
            if html_body:
                message = MIMEMultipart('alternative')
                message.attach(MIMEText(body, 'plain'))
                message.attach(MIMEText(html_body, 'html'))
            else:
                message = MIMEText(body)
            
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"Successfully sent email to {to}")
            
            return {
                'message_id': sent_message.get('id'),
                'thread_id': sent_message.get('threadId')
            }
            
        except HttpError as e:
            logger.error(f"Failed to send email: {e}")
            return None
    
    def send_appointment_confirmation_email(
        self,
        to: str,
        client_name: str,
        appointment_time: datetime,
        zoom_link: str,
        coach_name: str,
        calendar_event_link: str = None
    ) -> Optional[Dict]:
        """
        Send appointment confirmation email
        
        Args:
            to: Client email address
            client_name: Client's name
            appointment_time: Scheduled appointment time
            zoom_link: Zoom meeting link
            coach_name: Coach's name
            calendar_event_link: Optional Google Calendar event link
            
        Returns:
            Message details dictionary or None if failed
        """
        subject = f"Your Coaching Session is Confirmed - {appointment_time.strftime('%B %d, %Y')}"
        
        body = f"""Hi {client_name},

Your coaching session is confirmed!

Date: {appointment_time.strftime('%A, %B %d, %Y')}
Time: {appointment_time.strftime('%I:%M %p %Z')}
Coach: {coach_name}

Zoom Link: {zoom_link}

"""
        
        if calendar_event_link:
            body += f"""View in Calendar: {calendar_event_link}

"""
        
        body += """Tips for a great session:
- Join 5 minutes early to test your audio/video
- Find a quiet, private space
- Have a notebook ready for action items
- Come prepared with any questions or concerns

We're looking forward to supporting you on your wellness journey!

Best regards,
Purposeful Live Coaching Team

---
Need to reschedule? Reply to this email or contact support@purposefullivecoaching.academy"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #00a2ff; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #00a2ff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
        .details {{ background-color: white; padding: 15px; border-left: 4px solid #00a2ff; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Session Confirmed! 🎉</h1>
        </div>
        <div class="content">
            <p>Hi {client_name},</p>
            <p>Your coaching session is confirmed!</p>
            
            <div class="details">
                <p><strong>📅 Date:</strong> {appointment_time.strftime('%A, %B %d, %Y')}</p>
                <p><strong>🕐 Time:</strong> {appointment_time.strftime('%I:%M %p %Z')}</p>
                <p><strong>👤 Coach:</strong> {coach_name}</p>
            </div>
            
            <p style="text-align: center;">
                <a href="{zoom_link}" class="button">Join Zoom Meeting</a>
            </p>
            
            {'<p style="text-align: center;"><a href="' + calendar_event_link + '">View in Calendar</a></p>' if calendar_event_link else ''}
            
            <h3>Tips for a Great Session:</h3>
            <ul>
                <li>Join 5 minutes early to test your audio/video</li>
                <li>Find a quiet, private space</li>
                <li>Have a notebook ready for action items</li>
                <li>Come prepared with any questions or concerns</li>
            </ul>
            
            <p>We're looking forward to supporting you on your wellness journey! 💙</p>
        </div>
        <div class="footer">
            <p>Need to reschedule? Reply to this email or contact<br>
            support@purposefullivecoaching.academy</p>
            <p>&copy; 2025 Purposeful Live Coaching. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to, subject, body, html_body)
    
    def send_session_summary_email(
        self,
        to: str,
        client_name: str,
        session_date: datetime,
        summary: str,
        action_items: List[str],
        next_session_date: datetime = None,
        recording_link: str = None
    ) -> Optional[Dict]:
        """
        Send post-session summary email
        
        Args:
            to: Client email address
            client_name: Client's name
            session_date: Date of completed session
            summary: Session summary text
            action_items: List of action items
            next_session_date: Optional next session date
            recording_link: Optional session recording link
            
        Returns:
            Message details dictionary or None if failed
        """
        subject = f"Your Session Summary - {session_date.strftime('%B %d, %Y')}"
        
        action_items_text = "\n".join([f"- {item}" for item in action_items])
        
        body = f"""Hi {client_name},

Thank you for your coaching session on {session_date.strftime('%B %d, %Y')}!

SESSION SUMMARY:
{summary}

ACTION ITEMS:
{action_items_text}

"""
        
        if recording_link:
            body += f"""Session Recording: {recording_link}

"""
        
        if next_session_date:
            body += f"""Your next session is scheduled for {next_session_date.strftime('%A, %B %d, %Y at %I:%M %p %Z')}.

"""
        
        body += """Keep up the great work on your wellness journey!

Best regards,
Purposeful Live Coaching Team"""
        
        return self.send_email(to, subject, body)

