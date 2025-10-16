"""
Database Migration: Create Onboarding Tables
Creates appointments, notifications, onboarding_progress, and webhook_logs tables
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db
from models_extended import Appointment, Notification, OnboardingProgress, WebhookLog


def create_tables():
    """Create all new tables for onboarding system"""
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            
            print("✓ Successfully created tables:")
            print("  - appointments")
            print("  - notifications")
            print("  - onboarding_progress")
            print("  - webhook_logs")
            
            # Verify tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("\n✓ Verified tables in database:")
            for table in tables:
                print(f"  - {table}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            return False


def add_user_fields():
    """
    Add new fields to User model
    Note: This requires manual SQL for existing databases
    """
    print("\n⚠ Manual SQL required to add fields to 'users' table:")
    print("""
    ALTER TABLE users ADD COLUMN calendly_user_uri VARCHAR(200);
    ALTER TABLE users ADD COLUMN whatsapp_number VARCHAR(20);
    ALTER TABLE users ADD COLUMN whatsapp_opt_in BOOLEAN DEFAULT FALSE;
    ALTER TABLE users ADD COLUMN google_calendar_id VARCHAR(200);
    ALTER TABLE users ADD COLUMN preferred_communication VARCHAR(20) DEFAULT 'email';
    ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE;
    ALTER TABLE users ADD COLUMN onboarding_completed_at TIMESTAMP;
    ALTER TABLE users ADD COLUMN subscription_active BOOLEAN DEFAULT FALSE;
    ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(50);
    """)


if __name__ == '__main__':
    print("Creating onboarding tables...\n")
    
    success = create_tables()
    
    if success:
        print("\n✓ Migration completed successfully!")
        add_user_fields()
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)

