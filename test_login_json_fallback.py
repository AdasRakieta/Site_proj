#!/usr/bin/env python3
"""
Test Login Functionality with JSON Fallback Mode
================================================

Tests that login works correctly when database is unavailable.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import check_password_hash

def test_login_json_fallback():
    """Test login functionality in JSON fallback mode"""
    
    print("\n" + "="*70)
    print("🧪 Testing Login with JSON Fallback Mode")
    print("="*70)
    
    # Clean up old config
    config_file = 'app/smart_home_config.json'
    if os.path.exists(config_file):
        try:
            os.remove(config_file)
            print(f"\n✓ Cleaned up old config file")
        except:
            pass
    
    # Test 1: Initialize MultiHomeDBManager in JSON fallback mode
    print("\n[1/5] Initializing MultiHomeDBManager in JSON fallback mode...")
    try:
        from utils.multi_home_db_manager import MultiHomeDBManager
        
        multi_db = MultiHomeDBManager(
            host="invalid",
            port=5432,
            user="invalid",
            password="invalid",
            database="invalid",
            connection_timeout=1
        )
        
        assert multi_db.json_fallback_mode, "Should be in JSON fallback mode"
        print("✓ MultiHomeDBManager in JSON fallback mode")
        
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Get admin user credentials from JSON
    print("\n[2/5] Getting admin credentials from JSON config...")
    try:
        config = multi_db.json_backup.get_config()
        admin_data = config['users']['sys-admin']
        admin_username = admin_data['username']
        admin_id = admin_data['id']
        admin_password_hash = admin_data['password']
        
        print(f"✓ Found admin: {admin_username} (ID: {admin_id})")
        
    except Exception as e:
        print(f"✗ Failed to get admin credentials: {e}")
        return False
    
    # Test 3: Find user by email
    print("\n[3/5] Testing find_user_by_email_or_username...")
    try:
        # Try by email
        user = multi_db.find_user_by_email_or_username('admin@localhost')
        assert user is not None, "Should find user by email"
        assert user['id'] == admin_id, "Should return correct user ID"
        print(f"✓ Found user by email: {user['name']}")
        
        # Try by username
        user = multi_db.find_user_by_email_or_username('sys-admin')
        assert user is not None, "Should find user by username"
        assert user['id'] == admin_id, "Should return correct user ID"
        print(f"✓ Found user by username: {user['name']}")
        
        # Verify password_hash is returned
        assert 'password_hash' in user, "Should include password_hash"
        assert user['password_hash'] == admin_password_hash, "Should return correct password hash"
        print(f"✓ Password hash included in user data")
        
    except Exception as e:
        print(f"✗ Failed find_user_by_email_or_username test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Verify user password
    print("\n[4/5] Testing verify_user_password...")
    try:
        # Test with correct password hash
        is_valid = multi_db.verify_user_password(admin_id, admin_password_hash)
        assert is_valid, "Should verify correct password hash"
        print(f"✓ Verified correct password hash")
        
        # Test with incorrect password hash
        is_valid = multi_db.verify_user_password(admin_id, "wrong_hash")
        assert not is_valid, "Should reject incorrect password hash"
        print(f"✓ Rejected incorrect password hash")
        
    except Exception as e:
        print(f"✗ Failed verify_user_password test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Get user by ID
    print("\n[5/5] Testing get_user_by_id...")
    try:
        user = multi_db.get_user_by_id(admin_id)
        assert user is not None, "Should find user by ID"
        assert user['name'] == 'System Administrator', "Should return correct name"
        assert user['email'] == 'admin@localhost', "Should return correct email"
        assert user['role'] == 'admin', "Should return correct role"
        print(f"✓ Got user by ID: {user['name']}")
        
    except Exception as e:
        print(f"✗ Failed get_user_by_id test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Final test: Simulate complete login flow
    print("\n[BONUS] Testing complete login flow...")
    try:
        # Step 1: Find user
        login_name = 'sys-admin'
        user = multi_db.find_user_by_email_or_username(login_name)
        assert user is not None, f"User '{login_name}' not found"
        
        # Step 2: Verify password (simulated - we use the stored hash)
        # In real login, you'd use check_password_hash(user['password_hash'], entered_password)
        is_valid = multi_db.verify_user_password(user['id'], user['password_hash'])
        assert is_valid, "Password verification failed"
        
        # Step 3: Get full user data
        full_user = multi_db.get_user_by_id(user['id'])
        assert full_user is not None, "Failed to get full user data"
        
        print(f"✓ Complete login flow successful for '{full_user['name']}'")
        
    except Exception as e:
        print(f"✗ Complete login flow failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*70)
    print("✓ ALL LOGIN TESTS PASSED!")
    print("="*70)
    print("\nLogin functionality works correctly in JSON fallback mode:")
    print("✓ Users can be found by email or username")
    print("✓ Password verification works")
    print("✓ User data retrieval works")
    print("✓ Complete login flow is functional")
    print("\n")
    
    return True

if __name__ == '__main__':
    success = test_login_json_fallback()
    sys.exit(0 if success else 1)
