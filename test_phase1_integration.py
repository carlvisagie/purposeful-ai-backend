#!/usr/bin/env python3
"""
Comprehensive test script to verify Phase 1 implementation
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_flag_matrix_consistency():
    print("=== Testing FLAG_MATRIX Consistency ===")
    try:
        from flag_config import FLAG_MATRIX
        print("✅ FLAG_MATRIX imported successfully")
        
        inconsistent_types = []
        for key, value in FLAG_MATRIX.items():
            if not isinstance(value, list):
                inconsistent_types.append((key, type(value).__name__))
        
        if inconsistent_types:
            print(f"❌ CRITICAL: FLAG_MATRIX has inconsistent data types:")
            for key, type_name in inconsistent_types:
                print(f"  - {key}: {type_name} (should be list)")
            return False
        else:
            print("✅ FLAG_MATRIX data types are consistent")
            print(f"Categories: {list(FLAG_MATRIX.keys())}")
            return True
            
    except Exception as e:
        print(f"❌ CRITICAL: Failed to import FLAG_MATRIX: {e}")
        return False

def test_diagnostic_engine():
    print("\n=== Testing Diagnostic Engine ===")
    try:
        from diagnostic_engine import diagnose_client_responses
        
        test_text = "I feel anxious and have poor sleep, dealing with debt stress and lack of purpose"
        result = diagnose_client_responses(test_text)
        print(f"✅ Diagnostic engine works: {result}")
        
        expected_categories = ['mental_health', 'physical', 'financial', 'spiritual']
        found_flags = any(result.get(cat) for cat in expected_categories)
        
        if found_flags:
            print("✅ Diagnostic engine correctly identifies flags")
            return True
        else:
            print("❌ Diagnostic engine not detecting expected flags")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL: Diagnostic engine failed: {e}")
        return False

def test_crisis_detection():
    print("\n=== Testing Crisis Detection ===")
    try:
        from services.crisis_service import CrisisDetectionService
        
        crisis_text = "I want to end it all, feeling suicidal and hopeless"
        crisis_result = CrisisDetectionService.analyze_text(crisis_text)
        print(f"✅ Crisis detection works: {crisis_result}")
        
        if crisis_result['requires_immediate_attention']:
            print("✅ Crisis detection correctly identifies critical situation")
            return True
        else:
            print("❌ Crisis detection not flagging critical text")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL: Crisis detection failed: {e}")
        return False

def test_mortality_risk():
    print("\n=== Testing Mortality Risk Calculation ===")
    try:
        from mortality_screen import calculate_mortality_risk
        
        risk = calculate_mortality_risk(age=63, chronic_conditions=["hypertension"], habits=["poor sleep"])
        print(f"✅ Mortality risk calculation works: {risk}")
        
        if risk in ['low', 'elevated', 'critical']:
            print("✅ Mortality risk returns valid level")
            return True
        else:
            print(f"❌ Invalid risk level returned: {risk}")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL: Mortality risk calculation failed: {e}")
        return False

def test_tier_validation():
    print("\n=== Testing Tier Validation ===")
    try:
        from tier_validator import is_tier_mismatch
        
        mismatch = is_tier_mismatch("critical", "Shift Session")
        print(f"✅ Tier validation works: mismatch={mismatch}")
        
        if isinstance(mismatch, bool):
            print("✅ Tier validation returns boolean")
            return True
        else:
            print(f"❌ Tier validation should return boolean, got: {type(mismatch)}")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL: Tier validation failed: {e}")
        return False

def test_missing_info_check():
    print("\n=== Testing Missing Info Check ===")
    try:
        from missing_info_warning import check_missing_info
        
        client_data = {
            "symptoms": "anxiety",
            "goals": "improve mood",
            "medications": None,
            "emergency_contact": ""
        }
        
        missing = check_missing_info(client_data)
        print(f"✅ Missing info check works: {missing}")
        
        if isinstance(missing, list):
            print("✅ Missing info check returns list")
            return True
        else:
            print(f"❌ Missing info check should return list, got: {type(missing)}")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL: Missing info check failed: {e}")
        return False

def test_flask_app_creation():
    print("\n=== Testing Flask App Creation ===")
    try:
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'
        os.environ['OPENAI_API_KEY'] = 'test-key'
        
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        
        with app.app_context():
            from models import db
            db.create_all()
            print("✅ Database tables created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL: Flask app creation failed: {e}")
        return False

def main():
    print("🔍 PHASE 1 INTEGRATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_flag_matrix_consistency,
        test_diagnostic_engine,
        test_crisis_detection,
        test_mortality_risk,
        test_tier_validation,
        test_missing_info_check,
        test_flask_app_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Phase 1 implementation is working correctly!")
        return True
    else:
        print(f"❌ {total - passed} tests failed - Phase 1 implementation has issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
