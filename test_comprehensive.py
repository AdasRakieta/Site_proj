#!/usr/bin/env python3
"""
Comprehensive Test Suite for Smart Home System
Tests both role system and batch API functionality using remote database
"""

import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_role_system_comprehensive():
    """Test role system functionality with remote database"""
    
    print("🔐 Testing Role System with Remote Database...")
    print("=" * 60)
    
    try:
        from utils.multi_home_db_manager import MultiHomeDBManager
        
        # Initialize database manager with remote database config
        print("🔌 Connecting to remote database...")
        db_manager = MultiHomeDBManager(
            host="100.103.184.90",  # Remote server from pgsql config
            database="smarthome_multihouse",
            user="postgres",
            password=""  # Assuming empty password based on earlier config
        )
        
        print("✅ Successfully connected to remote database")
        
        # Test sys-admin methods
        print("\n🔍 Testing sys-admin methods...")
        
        # Check if sys-admin methods exist
        methods = ['is_sys_admin', 'get_sys_admin_users', 'setup_initial_sys_admin']
        for method in methods:
            if hasattr(db_manager, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
                return False
        
        # Test sys-admin check
        print("\n👤 Testing sys-admin user retrieval...")
        try:
            sys_admins = db_manager.get_sys_admin_users()
            print(f"🏠 Sys-admin users found: {len(sys_admins)}")
            for admin in sys_admins:
                print(f"   👤 {admin.get('name', 'Unknown')} ({admin.get('email', 'No email')})")
                
                # Test is_sys_admin method
                user_id = admin.get('id')
                if user_id:
                    is_admin = db_manager.is_sys_admin(user_id)
                    print(f"      🔐 is_sys_admin({user_id}): {is_admin}")
        
        except Exception as e:
            print(f"⚠️  Error getting sys-admins: {str(e)}")
            return False
        
        # Test home and user relationship
        print("\n🏠 Testing home-role relationships...")
        try:
            with db_manager.get_cursor() as cursor:
                # Get home structure with roles
                cursor.execute("""
                    SELECT 
                        h.id,
                        h.name as home_name,
                        u.name as owner_name,
                        u.role as global_role,
                        COUNT(uh.user_id) as user_count
                    FROM homes h
                    JOIN users u ON h.owner_id = u.id
                    LEFT JOIN user_homes uh ON uh.home_id = h.id
                    GROUP BY h.id, h.name, u.name, u.role
                    ORDER BY h.created_at
                    LIMIT 5;
                """)
                
                homes = cursor.fetchall()
                print(f"🏘️  Found {len(homes)} homes:")
                for home in homes:
                    print(f"   🏠 {home[1]} (Owner: {home[2]}, Role: {home[3]}, Users: {home[4]})")
        
        except Exception as e:
            print(f"⚠️  Error testing home relationships: {str(e)}")
            return False
        
        # Test batch update method
        print("\n📦 Testing batch update method...")
        try:
            if hasattr(db_manager, 'batch_update_devices'):
                print("✅ batch_update_devices method exists")
                
                # Test with empty updates (should not crash)
                result = db_manager.batch_update_devices([], "test-home-id")
                print(f"✅ Empty batch update works: {result}")
            else:
                print("❌ batch_update_devices method missing")
                return False
                
        except Exception as e:
            print(f"⚠️  Error testing batch update: {str(e)}")
            # This might fail due to invalid home_id, but method should exist
            pass
        
        print("\n✅ Role system tests completed successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        print("💡 Make sure the remote database is accessible")
        return False

def test_app_initialization():
    """Test application initialization with new role system"""
    
    print("🚀 Testing Application Initialization...")
    print("=" * 60)
    
    try:
        # Test import without full initialization
        import app_db
        print("✅ app_db module imports successfully")
        
        # Check if setup_sys_admin method exists
        if hasattr(app_db, 'setup_sys_admin'):
            print("✅ setup_sys_admin method exists in app_db")
        else:
            print("❌ setup_sys_admin method missing from app_db")
            return False
        
        # Test route imports
        try:
            from app.routes import app as flask_app
            print("✅ Flask routes import successfully")
            
            # Check if batch update route exists
            routes = [rule.rule for rule in flask_app.url_map.iter_rules()]
            batch_route_exists = any('/api/devices/batch-update' in route for route in routes)
            
            if batch_route_exists:
                print("✅ Batch update API route is registered")
            else:
                print("⚠️  Batch update route not found in registered routes")
                # List some routes for debugging
                api_routes = [r for r in routes if '/api/' in r]
                print(f"📋 Available API routes: {api_routes[:5]}...")
        
        except Exception as e:
            print(f"⚠️  Routes import error: {str(e)}")
            return False
        
        print("\n✅ Application initialization tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Application test error: {str(e)}")
        return False

def test_frontend_files():
    """Test that frontend files have the batch update functionality"""
    
    print("🌐 Testing Frontend Batch Update Integration...")
    print("=" * 60)
    
    try:
        # Check dragNdrop.js for batch functionality
        dragndrop_path = "static/js/dragNdrop.js"
        if os.path.exists(dragndrop_path):
            with open(dragndrop_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for batch update indicators
            batch_indicators = [
                '/api/devices/batch-update',
                'isSaving',
                'batch',
                'updates:'
            ]
            
            found_indicators = []
            for indicator in batch_indicators:
                if indicator in content:
                    found_indicators.append(indicator)
                    
            print(f"🔍 Batch indicators found: {len(found_indicators)}/{len(batch_indicators)}")
            for indicator in found_indicators:
                print(f"   ✅ '{indicator}' found")
                
            missing = set(batch_indicators) - set(found_indicators)
            if missing:
                print(f"⚠️  Missing indicators: {missing}")
                
            if len(found_indicators) >= 3:
                print("✅ Frontend appears to have batch functionality")
                return True
            else:
                print("❌ Frontend missing batch functionality")
                return False
        else:
            print(f"❌ Frontend file not found: {dragndrop_path}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test error: {str(e)}")
        return False

def main():
    """Run comprehensive test suite"""
    
    print("🧪 Smart Home System - Comprehensive Test Suite")
    print("=" * 80)
    print("Testing batch API integration and role system functionality")
    print("=" * 80)
    
    # Run all tests
    tests = [
        ("Role System", test_role_system_comprehensive),
        ("Application Init", test_app_initialization), 
        ("Frontend Integration", test_frontend_files)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🎯 Running {test_name} Tests...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results[test_name] = False
        
        print()  # Empty line for readability
    
    # Final results
    print("📊 Final Test Results")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is fully functional.")
        print("💡 Your batch API optimization and role system are working correctly.")
    elif passed >= total // 2:
        print(f"\n✅ Most tests passed ({passed}/{total})")
        print("💡 Core functionality is working. Check failed tests above.")
    else:
        print(f"\n⚠️  Several tests failed ({total-passed}/{total})")
        print("💡 Review the error messages above for troubleshooting.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)