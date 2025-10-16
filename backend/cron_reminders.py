#!/usr/bin/env python3
"""
Cron Job: Send Appointment Reminders
Run this script every 15 minutes via cron to check for upcoming appointments
and send reminders

Crontab entry:
*/15 * * * * cd /home/ubuntu/purposeful-ai-backend && /usr/bin/python3 backend/cron_reminders.py >> /var/log/purposeful-reminders.log 2>&1
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.notification_scheduler import get_notification_scheduler

def main():
    """Main cron job function"""
    print(f"\n{'='*60}")
    print(f"Reminder Check Started: {datetime.utcnow().isoformat()}")
    print(f"{'='*60}")
    
    app = create_app()
    
    with app.app_context():
        scheduler = get_notification_scheduler()
        
        # Check and send reminders
        print("\nChecking for appointments needing reminders...")
        reminder_stats = scheduler.check_and_send_reminders()
        
        print(f"\nReminder Statistics:")
        print(f"  24-hour reminders sent: {reminder_stats.get('24h_reminders_sent', 0)}")
        print(f"  1-hour reminders sent: {reminder_stats.get('1h_reminders_sent', 0)}")
        print(f"  Errors: {reminder_stats.get('errors', 0)}")
        
        # Check and send follow-ups
        print("\nChecking for completed sessions needing follow-up...")
        followup_stats = scheduler.check_and_send_followups()
        
        print(f"\nFollow-up Statistics:")
        print(f"  Follow-ups sent: {followup_stats.get('followups_sent', 0)}")
        print(f"  Errors: {followup_stats.get('errors', 0)}")
    
    print(f"\n{'='*60}")
    print(f"Reminder Check Completed: {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

