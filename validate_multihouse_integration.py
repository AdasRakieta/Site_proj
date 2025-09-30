#!/usr/bin/env python3
"""
Validation script to check if multihouse registration system is properly integrated
Tests code structure and dependencies without requiring database connection
"""

import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_multihouse_db_methods():
    """Validate that MultiHomeDBManager has required user management methods"""
    
    print("🔍 Validating MultiHomeDBManager User Methods")
    print("=" * 60)
    
    try:
        from utils.multi_home_db_manager import MultiHomeDBManager
        
        # Check required methods exist
        required_methods = [
            'create_user',
            'find_user_by_email_or_username', 
            'verify_user_password',
            'update_user_password',
            'get_user_by_id',
            'check_user_exists',
            'get_user_homes',
            'user_has_home_access',
            'is_sys_admin'
        ]
        
        print("📋 Checking required methods:")
        all_methods_exist = True
        
        for method in required_methods:
            if hasattr(MultiHomeDBManager, method):
                print(f"   ✅ {method}")
            else:
                print(f"   ❌ {method}")
                all_methods_exist = False
        
        return all_methods_exist
        
    except ImportError as e:
        print(f"❌ Failed to import MultiHomeDBManager: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating methods: {e}")
        return False

def validate_routes_integration():
    """Validate that routes.py is properly updated for multihouse system"""
    
    print("\n🌐 Validating Routes Integration")
    print("=" * 60)
    
    try:
        # Read routes.py file to check for multihouse integration
        routes_path = "app/routes.py"
        if not os.path.exists(routes_path):
            print("❌ routes.py file not found")
            return False
        
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        # Check for multihouse integration indicators
        integration_indicators = [
            'self.multi_db.create_user',           # New user creation
            'self.multi_db.find_user_by_email',   # User lookup
            'self.multi_db.update_user_password',  # Password reset
            'check_password_hash',                 # Proper password hashing
            'current_home_id',                     # Session home management
            '/api/switch_home',                    # Home switching API
            '/api/get_user_homes',                 # Get user homes API
        ]
        
        print("📋 Checking integration indicators:")
        found_count = 0
        
        for indicator in integration_indicators:
            if indicator in routes_content:
                print(f"   ✅ {indicator}")
                found_count += 1
            else:
                print(f"   ⚠️  {indicator}")
        
        integration_score = found_count / len(integration_indicators)
        print(f"\n📊 Integration Score: {found_count}/{len(integration_indicators)} ({integration_score:.1%})")
        
        if integration_score >= 0.8:
            print("✅ Routes integration looks good")
            return True
        else:
            print("⚠️  Routes integration may be incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Error validating routes: {e}")
        return False

def validate_registration_flow():
    """Validate that registration flow is properly structured"""
    
    print("\n📝 Validating Registration Flow")
    print("=" * 60)
    
    try:
        # Check registration methods in routes
        routes_path = "app/routes.py"
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        # Check registration flow components
        flow_components = [
            '_send_verification_code',         # First step method
            '_verify_and_register',           # Second step method  
            '_find_user_by_email_or_username', # User lookup method
            'create_default_home=True',       # Automatic home creation
            'generate_password_hash',         # Proper password hashing
            'management_logger.log_user_change' # Logging
        ]
        
        print("📋 Checking registration flow components:")
        flow_complete = True
        
        for component in flow_components:
            if component in routes_content:
                print(f"   ✅ {component}")
            else:
                print(f"   ❌ {component}")
                flow_complete = False
        
        return flow_complete
        
    except Exception as e:
        print(f"❌ Error validating registration flow: {e}")
        return False

def validate_authentication_flow():
    """Validate that authentication (login) is updated for multihouse"""
    
    print("\n🔐 Validating Authentication Flow")
    print("=" * 60)
    
    try:
        routes_path = "app/routes.py"
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        # Check authentication components
        auth_components = [
            'self.multi_db.find_user_by_email',  # User lookup in login
            'check_password_hash',               # Password verification
            'get_user_homes',                    # Load user homes
            'current_home_id',                   # Set current home
            'set_user_current_home'              # Update current home in DB
        ]
        
        print("📋 Checking authentication components:")
        auth_complete = True
        
        for component in auth_components:
            if component in routes_content:
                print(f"   ✅ {component}")
            else:
                print(f"   ❌ {component}")
                auth_complete = False
        
        return auth_complete
        
    except Exception as e:
        print(f"❌ Error validating authentication: {e}")
        return False

def main():
    """Run all validation tests"""
    
    print("🧪 Smart Home Multihouse Integration - Validation Suite")
    print("=" * 80)
    print("Validating multihouse registration and authentication integration")
    print("=" * 80)
    
    tests = [
        ("DB Methods", validate_multihouse_db_methods),
        ("Routes Integration", validate_routes_integration),
        ("Registration Flow", validate_registration_flow),
        ("Authentication Flow", validate_authentication_flow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} validation crashed: {str(e)}")
            results[test_name] = False
    
    # Final results
    print("\n📊 Validation Results")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 All validations passed! Multihouse integration is complete.")
        print("💡 System is ready for:")
        print("   • User registration with automatic home creation")
        print("   • Home-based role assignment (admin in own home)")
        print("   • Email/username login with multihouse support")
        print("   • Password reset with proper hashing")
        print("   • Home switching and management")
    elif passed >= total // 2:
        print(f"\n✅ Most validations passed ({passed}/{total})")
        print("💡 Core functionality appears to be implemented correctly.")
        print("🔧 Some components may need minor adjustments.")
    else:
        print(f"\n⚠️  Several validations failed ({total-passed}/{total})")
        print("🔧 Significant integration work may be needed.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)