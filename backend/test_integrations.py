"""
Integration Test Script
Tests all service integrations with real or mock API calls
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import services
from services.calendly_service import CalendlyService
from services.zoom_service import ZoomService
from services.whatsapp_service import WhatsAppService
from services.google_workspace_service import GoogleWorkspaceService
from services.enhanced_payment_service import EnhancedPaymentService


def test_calendly():
    """Test Calendly service integration"""
    print("\n🔍 Testing Calendly Service...")
    
    api_key = os.getenv('CALENDLY_API_KEY')
    if not api_key:
        print("⚠️  CALENDLY_API_KEY not set - skipping")
        return False
    
    try:
        service = CalendlyService(api_key)
        
        # Test get current user
        user = service.get_current_user()
        if user:
            print(f"✅ Successfully connected to Calendly")
            print(f"   User: {user['resource']['name']}")
            print(f"   URI: {user['resource']['uri']}")
            
            # Test get event types
            event_types = service.get_user_event_types(user['resource']['uri'])
            if event_types:
                print(f"✅ Found {len(event_types)} event types")
                for et in event_types[:3]:
                    print(f"   - {et['name']} ({et['duration']} min)")
            
            return True
        else:
            print("❌ Failed to connect to Calendly")
            return False
            
    except Exception as e:
        print(f"❌ Calendly test failed: {e}")
        return False


def test_zoom():
    """Test Zoom service integration"""
    print("\n🔍 Testing Zoom Service...")
    
    api_key = os.getenv('ZOOM_API_KEY')
    api_secret = os.getenv('ZOOM_API_SECRET')
    
    if not api_key or not api_secret:
        print("⚠️  ZOOM_API_KEY or ZOOM_API_SECRET not set - skipping")
        return False
    
    try:
        service = ZoomService(api_key, api_secret)
        
        # Test JWT token generation
        token = service._generate_jwt_token()
        if token:
            print(f"✅ Successfully generated Zoom JWT token")
            print(f"   Token length: {len(token)} characters")
            
            # Note: Creating a test meeting would require a valid Zoom account
            # For now, we just verify the service initializes correctly
            print("✅ Zoom service initialized successfully")
            return True
        else:
            print("❌ Failed to generate JWT token")
            return False
            
    except Exception as e:
        print(f"❌ Zoom test failed: {e}")
        return False


def test_whatsapp():
    """Test WhatsApp service integration"""
    print("\n🔍 Testing WhatsApp Service...")
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    
    if not account_sid or not auth_token:
        print("⚠️  Twilio credentials not set - skipping")
        return False
    
    try:
        service = WhatsAppService(account_sid, auth_token, whatsapp_number)
        
        print(f"✅ WhatsApp service initialized successfully")
        print(f"   From number: {whatsapp_number}")
        print(f"   Account SID: {account_sid[:10]}...")
        
        # Note: Sending a test message would require a verified recipient
        # For now, we just verify the service initializes correctly
        return True
            
    except Exception as e:
        print(f"❌ WhatsApp test failed: {e}")
        return False


def test_stripe():
    """Test Stripe service integration"""
    print("\n🔍 Testing Stripe Service...")
    
    secret_key = os.getenv('STRIPE_SECRET_KEY')
    
    if not secret_key:
        print("⚠️  STRIPE_SECRET_KEY not set - skipping")
        return False
    
    try:
        service = EnhancedPaymentService(secret_key)
        
        print(f"✅ Stripe service initialized successfully")
        print(f"   Using key: {secret_key[:10]}...")
        
        # Test tier prices
        for tier, price in service.TIER_PRICES.items():
            print(f"   {tier}: ${price/100:.2f}")
        
        return True
            
    except Exception as e:
        print(f"❌ Stripe test failed: {e}")
        return False


def test_google_workspace():
    """Test Google Workspace service integration"""
    print("\n🔍 Testing Google Workspace Service...")
    
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    
    if not service_account_file or not os.path.exists(service_account_file):
        print("⚠️  GOOGLE_SERVICE_ACCOUNT_FILE not set or file not found - skipping")
        return False
    
    try:
        service = GoogleWorkspaceService(service_account_file=service_account_file)
        
        print(f"✅ Google Workspace service initialized successfully")
        print(f"   Using service account: {service_account_file}")
        
        return True
            
    except Exception as e:
        print(f"❌ Google Workspace test failed: {e}")
        return False


def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing Database Connection...")
    
    try:
        from app import create_app
        from models import db, User
        
        app = create_app()
        
        with app.app_context():
            # Try to query users table
            user_count = User.query.count()
            print(f"✅ Database connection successful")
            print(f"   Total users: {user_count}")
            
            # Check if new tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['users', 'appointments', 'notifications', 'onboarding_progress', 'webhook_logs']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
                print(f"   Run: python backend/migrations/create_onboarding_tables.py")
            else:
                print(f"✅ All required tables exist")
            
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("PURPOSEFUL LIVE COACHING - INTEGRATION TESTS")
    print("=" * 60)
    
    results = {
        'Database': test_database_connection(),
        'Calendly': test_calendly(),
        'Zoom': test_zoom(),
        'WhatsApp': test_whatsapp(),
        'Stripe': test_stripe(),
        'Google Workspace': test_google_workspace()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for service, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{service:20s} {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check configuration.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

