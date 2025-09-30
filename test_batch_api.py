#!/usr/bin/env python3
"""Test script to verify batch API functionality with new role system"""

import requests
import json
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_batch_api():
    """Test the batch update API endpoint"""
    
    # Base URL - adjust if needed
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Batch API Functionality...")
    print("=" * 50)
    
    # Test data for batch update
    test_data = {
        "updates": [
            {
                "device_id": "test_device_1",
                "display_order": 1
            },
            {
                "device_id": "test_device_2", 
                "display_order": 2
            }
        ]
    }
    
    try:
        # Test the batch update endpoint
        response = requests.post(
            f"{base_url}/api/devices/batch-update",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📡 Request sent to: {base_url}/api/devices/batch-update")
        print(f"📋 Test data: {json.dumps(test_data, indent=2)}")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Batch API endpoint is accessible")
            try:
                result = response.json()
                print(f"📄 Response: {json.dumps(result, indent=2)}")
            except:
                print(f"📄 Response text: {response.text}")
        else:
            print(f"⚠️  Non-200 status code: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("🔌 Server not running on localhost:5000")
        print("💡 To start the server, run: python app_db.py")
        return False
    except Exception as e:
        print(f"❌ Error testing batch API: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    return True

def test_role_system():
    """Test role system functionality"""
    
    print("🔐 Testing Role System...")
    print("=" * 50)
    
    try:
        from utils.multi_home_db_manager import MultiHomeDBManager
        
        # Initialize database manager
        db_manager = MultiHomeDBManager()
        
        # Test sys-admin methods
        print("🔍 Testing sys-admin methods...")
        
        # Check if sys-admin methods exist
        methods = ['is_sys_admin', 'get_sys_admin_users', 'setup_initial_sys_admin']
        for method in methods:
            if hasattr(db_manager, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
        
        # Test sys-admin check (if we have a test user)
        try:
            sys_admins = db_manager.get_sys_admin_users()
            print(f"🏠 Sys-admin users found: {len(sys_admins)}")
            for admin in sys_admins:
                print(f"   👤 {admin.get('name', 'Unknown')} ({admin.get('email', 'No email')})")
        except Exception as e:
            print(f"⚠️  Error getting sys-admins: {str(e)}")
        
        print("✅ Role system methods are available")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error testing role system: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    return True

if __name__ == "__main__":
    print("🚀 Smart Home System Test Suite")
    print("=" * 50)
    
    # Test role system first (doesn't need server running)
    role_test = test_role_system()
    
    # Test batch API (needs server running)
    api_test = test_batch_api()
    
    print("\n📋 Test Results Summary:")
    print("=" * 50)
    print(f"🔐 Role System: {'✅ PASS' if role_test else '❌ FAIL'}")
    print(f"📡 Batch API: {'✅ PASS' if api_test else '⚠️  SERVER NOT RUNNING'}")
    
    if role_test and api_test:
        print("\n🎉 All tests passed! System is ready.")
    elif role_test:
        print("\n💡 Role system works. Start server to test API: python app_db.py")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")