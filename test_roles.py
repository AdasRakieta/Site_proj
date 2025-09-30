#!/usr/bin/env python3
"""
Test script for the new role system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.multi_home_db_manager import MultiHomeDBManager

def test_role_system():
    """Test the new role system."""
    
    print("🔍 Testing role system...")
    
    # Initialize database manager
    multi_db = MultiHomeDBManager()
    
    print("\n=== Current Users and Roles ===")
    
    # Test users we know exist
    test_users = [
        '727a5147-14e6-405d-921b-931fbc0397ed',  # admin
        '07336a33-adea-4b69-bff3-a1dac12a1d4a'   # szym.przy
    ]
    
    for user_id in test_users:
        print(f"\n--- User ID: {user_id} ---")
        
        # Check if sys-admin
        is_sys_admin = multi_db.is_sys_admin(user_id)
        print(f"Is sys-admin: {is_sys_admin}")
        
        # Get user homes
        user_homes = multi_db.get_user_homes(user_id)
        print(f"Number of homes: {len(user_homes)}")
        
        for home in user_homes:
            home_id = home['id']
            home_name = home['name']
            home_role = home['role']
            
            print(f"  Home: {home_name} (ID: {home_id[:8]}...)")
            print(f"    Role: {home_role}")
            print(f"    Is owner: {home['is_owner']}")
            
            # Test admin access
            has_access = multi_db.has_admin_access(user_id, home_id)
            print(f"    Has admin access: {has_access}")
            
        # Test global admin access (without home context)
        global_access = multi_db.has_admin_access(user_id)
        print(f"Global admin access: {global_access}")
    
    print("\n✅ Role system test completed!")

if __name__ == "__main__":
    test_role_system()