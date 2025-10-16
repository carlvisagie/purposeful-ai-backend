#!/usr/bin/env python3
"""
Complete End-to-End Testing Script
Tests the entire onboarding and appointment flow
"""

import os
import sys
import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')
TEST_EMAIL = f'test_{int(time.time())}@example.com'
TEST_PASSWORD = 'TestPassword123!'

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{title}")
    print(f"{'='*60}{Colors.END}\n")

# Global variables
auth_token = None
user_id = None

def test_health_check():
    """Test 1: Health Check"""
    print_section("Test 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            print_success(f"Health check passed: {response.json()}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_status_check():
    """Test 2: Status Check"""
    print_section("Test 2: Detailed Status Check")
    
    try:
        response = requests.get(f"{BASE_URL}/status")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Status check passed")
            print_info(f"Database: {data['database']}")
            print_info(f"Integrations: {json.dumps(data['integrations'], indent=2)}")
            return True
        else:
            print_error(f"Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Status check error: {e}")
        return False

def test_user_registration():
    """Test 3: User Registration"""
    print_section("Test 3: User Registration")
    
    global auth_token, user_id
    
    try:
        payload = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=payload
        )
        
        if response.status_code == 201:
            data = response.json()
            auth_token = data['access_token']
            user_id = data['user']['id']
            print_success(f"User registered: {TEST_EMAIL}")
            print_info(f"User ID: {user_id}")
            print_info(f"Token: {auth_token[:20]}...")
            return True
        else:
            print_error(f"Registration failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Registration error: {e}")
        return False

def test_user_login():
    """Test 4: User Login"""
    print_section("Test 4: User Login")
    
    global auth_token
    
    try:
        payload = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data['access_token']
            print_success("Login successful")
            print_info(f"Token: {auth_token[:20]}...")
            return True
        else:
            print_error(f"Login failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Login error: {e}")
        return False

def test_start_onboarding():
    """Test 5: Start Onboarding"""
    print_section("Test 5: Start Onboarding")
    
    try:
        response = requests.post(
            f"{BASE_URL}/onboarding/start",
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Onboarding started")
            print_info(f"Progress ID: {data['progress']['id']}")
            print_info(f"Current step: {data['progress']['current_step']}")
            return True
        else:
            print_error(f"Start onboarding failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Start onboarding error: {e}")
        return False

def test_submit_assessment():
    """Test 6: Submit Assessment"""
    print_section("Test 6: Submit Assessment")
    
    try:
        payload = {
            'text': 'I have been feeling anxious and stressed lately. Having trouble sleeping and feeling overwhelmed with work.',
            'age': 35,
            'chronic': ['anxiety'],
            'habits': ['poor_sleep']
        }
        
        response = requests.post(
            f"{BASE_URL}/onboarding/assessment",
            headers={'Authorization': f'Bearer {auth_token}'},
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Assessment submitted")
            print_info(f"Recommended tier: {data['recommended_tier']}")
            print_info(f"Crisis level: {data.get('crisis_level', 'None')}")
            print_info(f"AI response: {data['ai_response'][:100]}...")
            return True
        else:
            print_error(f"Assessment failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Assessment error: {e}")
        return False

def test_get_onboarding_progress():
    """Test 7: Get Onboarding Progress"""
    print_section("Test 7: Get Onboarding Progress")
    
    try:
        response = requests.get(
            f"{BASE_URL}/onboarding/progress",
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Progress retrieved")
            print_info(f"Current step: {data['progress']['current_step']}")
            print_info(f"Completed: {data['progress']['is_completed']}")
            return True
        else:
            print_error(f"Get progress failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get progress error: {e}")
        return False

def test_dashboard_profile():
    """Test 8: Dashboard Profile"""
    print_section("Test 8: Dashboard Profile")
    
    try:
        response = requests.get(
            f"{BASE_URL}/dashboard/profile",
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Profile retrieved")
            print_info(f"User: {data['user']['first_name']} {data['user']['last_name']}")
            print_info(f"Email: {data['user']['email']}")
            return True
        else:
            print_error(f"Get profile failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get profile error: {e}")
        return False

def test_dashboard_stats():
    """Test 9: Dashboard Stats"""
    print_section("Test 9: Dashboard Stats")
    
    try:
        response = requests.get(
            f"{BASE_URL}/dashboard/stats",
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Stats retrieved")
            print_info(f"Total appointments: {data['stats']['total_appointments']}")
            print_info(f"Upcoming: {data['stats']['upcoming_appointments']}")
            print_info(f"Completed: {data['stats']['completed_appointments']}")
            return True
        else:
            print_error(f"Get stats failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get stats error: {e}")
        return False

def test_dashboard_appointments():
    """Test 10: Dashboard Appointments"""
    print_section("Test 10: Dashboard Appointments")
    
    try:
        response = requests.get(
            f"{BASE_URL}/dashboard/appointments",
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Appointments retrieved")
            print_info(f"Count: {len(data['appointments'])}")
            return True
        else:
            print_error(f"Get appointments failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get appointments error: {e}")
        return False

def test_update_profile():
    """Test 11: Update Profile"""
    print_section("Test 11: Update Profile")
    
    try:
        payload = {
            'phone': '+1234567890',
            'whatsapp_number': '+1234567890',
            'preferred_communication': 'whatsapp'
        }
        
        response = requests.put(
            f"{BASE_URL}/dashboard/update-profile",
            headers={'Authorization': f'Bearer {auth_token}'},
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Profile updated")
            print_info(f"Phone: {data['user'].get('phone', 'N/A')}")
            return True
        else:
            print_error(f"Update profile failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Update profile error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}")
    print("PURPOSEFUL LIVE COACHING - END-TO-END TEST SUITE")
    print(f"{'='*60}{Colors.END}")
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test Email: {TEST_EMAIL}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    tests = [
        test_health_check,
        test_status_check,
        test_user_registration,
        test_user_login,
        test_start_onboarding,
        test_submit_assessment,
        test_get_onboarding_progress,
        test_dashboard_profile,
        test_dashboard_stats,
        test_dashboard_appointments,
        test_update_profile
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append((test.__doc__, result))
            time.sleep(0.5)  # Brief pause between tests
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((test.__doc__, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(test_name)
        else:
            print_error(test_name)
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Total: {total} tests")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {total - passed}{Colors.END}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    if passed == total:
        print_success("ALL TESTS PASSED! 🎉")
        return 0
    else:
        print_error(f"{total - passed} TEST(S) FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())

