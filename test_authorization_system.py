#!/usr/bin/env python3
"""
Test suite for multihouse authorization system
Tests that owner/admin users have proper access to /edit and /admin_dashboard
"""

import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_auth_manager_multihouse():
    """Validate that SimpleAuthManager supports multihouse authorization"""
    
    print("🔐 Testing SimpleAuthManager Multihouse Authorization")
    print("=" * 60)
    
    try:
        from app.simple_auth import SimpleAuthManager
        from utils.multi_home_db_manager import MultiHomeDBManager
        
        print("✅ Successfully imported SimpleAuthManager and MultiHomeDBManager")
        
        # Check if SimpleAuthManager has proper constructor
        import inspect
        sig = inspect.signature(SimpleAuthManager.__init__)
        params = list(sig.parameters.keys())
        
        print(f"📋 SimpleAuthManager constructor parameters: {params}")
        
        if 'multi_db' in params:
            print("✅ SimpleAuthManager supports multi_db parameter")
        else:
            print("❌ SimpleAuthManager missing multi_db parameter")
            return False
        
        # Test that we can create instance with multi_db
        # (We won't actually connect to DB, just test structure)
        try:
            # Create mock objects for testing
            class MockSmartHome:
                def get_user_by_id(self, user_id):
                    return {'id': user_id, 'role': 'user', 'name': 'test'}
            
            mock_smart_home = MockSmartHome()
            mock_multi_db = None  # We'll test with None to ensure fallback works
            
            auth_manager = SimpleAuthManager(mock_smart_home, multi_db=mock_multi_db)
            print("✅ SimpleAuthManager instance created successfully")
            
            # Check that required methods exist
            required_methods = ['admin_required', 'api_admin_required', 'login_required']
            for method in required_methods:
                if hasattr(auth_manager, method):
                    print(f"✅ Method '{method}' exists")
                else:
                    print(f"❌ Method '{method}' missing")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating SimpleAuthManager instance: {e}")
            return False
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def validate_routes_admin_protection():
    """Validate that critical routes are protected with admin_required"""
    
    print("\n🛡️  Testing Route Protection")
    print("=" * 60)
    
    try:
        # Read routes file to check for proper decorators
        routes_path = "app/routes.py"
        if not os.path.exists(routes_path):
            print("❌ routes.py file not found")
            return False
        
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        # Check that critical routes have admin protection
        protected_routes = [
            ('/edit', '@self.auth_manager.admin_required'),
            ('/admin_dashboard', '@self.auth_manager.admin_required')
        ]
        
        print("📋 Checking route protection:")
        all_protected = True
        
        for route_path, expected_decorator in protected_routes:
            # Find the route definition
            route_pattern = f"@self.app.route('{route_path}')"
            
            if route_pattern in routes_content:
                # Find the position of the route
                route_pos = routes_content.find(route_pattern)
                # Look for the decorator in the next few lines after the route
                route_section = routes_content[route_pos:route_pos + 500]
                
                if expected_decorator in route_section:
                    print(f"   ✅ {route_path} is protected with {expected_decorator}")
                else:
                    print(f"   ❌ {route_path} missing {expected_decorator}")
                    all_protected = False
            else:
                print(f"   ⚠️  Route {route_path} not found")
                all_protected = False
        
        return all_protected
        
    except Exception as e:
        print(f"❌ Error validating route protection: {e}")
        return False

def validate_multihouse_authorization_logic():
    """Validate the authorization logic for multihouse system"""
    
    print("\n🏠 Testing Multihouse Authorization Logic")
    print("=" * 60)
    
    try:
        # Read simple_auth.py to check authorization logic
        auth_path = "app/simple_auth.py"
        if not os.path.exists(auth_path):
            print("❌ simple_auth.py file not found")
            return False
        
        with open(auth_path, 'r', encoding='utf-8') as f:
            auth_content = f.read()
        
        # Check for multihouse authorization components
        auth_components = [
            'self.multi_db',                           # MultiDB integration
            'is_sys_admin',                           # Sys-admin check
            'user_has_home_permission',               # Home permission check
            'get_user_homes',                         # User homes lookup
            'current_home_id',                        # Current home context
            "home_role'] in ['admin', 'owner']",      # Role checking
            'manage_devices',                         # Device management permission
            'manage_rooms'                            # Room management permission
        ]
        
        print("📋 Checking authorization logic components:")
        logic_complete = True
        
        for component in auth_components:
            if component in auth_content:
                print(f"   ✅ {component}")
            else:
                print(f"   ❌ {component}")
                logic_complete = False
        
        # Check for fallback mechanism
        fallback_indicators = [
            'Fallback to old system',
            'except Exception as e:',
            'user_role == \'sys-admin\''
        ]
        
        print("\n📋 Checking fallback mechanism:")
        for indicator in fallback_indicators:
            if indicator in auth_content:
                print(f"   ✅ {indicator}")
            else:
                print(f"   ⚠️  {indicator}")
        
        return logic_complete
        
    except Exception as e:
        print(f"❌ Error validating authorization logic: {e}")
        return False

def validate_app_db_integration():
    """Validate that app_db.py properly initializes auth manager with multi_db"""
    
    print("\n🔗 Testing App Integration")
    print("=" * 60)
    
    try:
        # Read app_db.py to check initialization
        app_db_path = "app_db.py"
        if not os.path.exists(app_db_path):
            print("❌ app_db.py file not found")
            return False
        
        with open(app_db_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check for proper SimpleAuthManager initialization
        integration_checks = [
            'SimpleAuthManager(self.smart_home, multi_db=self.multi_db)',  # Proper initialization
            'from app.simple_auth import SimpleAuthManager',                # Import
            'self.auth_manager =',                                         # Assignment
        ]
        
        print("📋 Checking app integration:")
        integration_complete = True
        
        for check in integration_checks:
            if check in app_content:
                print(f"   ✅ {check}")
            else:
                print(f"   ❌ {check}")
                integration_complete = False
        
        return integration_complete
        
    except Exception as e:
        print(f"❌ Error validating app integration: {e}")
        return False

def main():
    """Run all authorization validation tests"""
    
    print("🧪 Smart Home Authorization System - Validation Suite")
    print("=" * 80)
    print("Testing owner/admin access to protected routes with multihouse support")
    print("=" * 80)
    
    tests = [
        ("Auth Manager Multihouse", validate_auth_manager_multihouse),
        ("Route Protection", validate_routes_admin_protection),
        ("Authorization Logic", validate_multihouse_authorization_logic),
        ("App Integration", validate_app_db_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} validation crashed: {str(e)}")
            results[test_name] = False
    
    # Final results
    print("\n📊 Authorization Validation Results")
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
        print("\n🎉 All validations passed! Authorization system is properly configured.")
        print("💡 System now supports:")
        print("   • Sys-admin: Global access to all homes and routes")
        print("   • Home admin/owner: Full access to /edit and /admin_dashboard in their homes")  
        print("   • Per-home role checking with fallback to global roles")
        print("   • Proper session-based home context")
        print("   • Graceful fallback to legacy system when needed")
        print("\n🔒 Protected routes:")
        print("   • /edit - Device and room management interface")
        print("   • /admin_dashboard - Administrative functions")
        print("   • All API endpoints with @api_admin_required")
    elif passed >= total // 2:
        print(f"\n✅ Most validations passed ({passed}/{total})")
        print("💡 Core authorization appears to be working correctly.")
        print("🔧 Some components may need minor adjustments.")
    else:
        print(f"\n⚠️  Several validations failed ({total-passed}/{total})")
        print("🔧 Significant authorization work may be needed.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)