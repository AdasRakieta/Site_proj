#!/usr/bin/env python3
"""
Test password verification directly
"""

from utils.smart_home_db_manager import SmartHomeDatabaseManager
from werkzeug.security import check_password_hash

def test_login():
    db = SmartHomeDatabaseManager()
    
    # Test data
    username = 'admin'
    password = 'admin123'
    
    print(f"Testing login for: {username}")
    print(f"Password: {password}")
    
    # Get users
    users = db.get_users()
    print(f"\nFound {len(users)} users:")
    
    for user in users:
        print(f"  User: {user}")
        
    # Find user
    user = None
    user_id = None
    
    for u in users:
        print(f"Checking user: {u}")
        if isinstance(u, dict):
            if u.get('name') == username or u.get('email') == username:
                user = u
                user_id = u.get('id')
                break
        elif hasattr(u, 'get'):
            if u.get('name') == username or u.get('email') == username:
                user = u
                user_id = u.get('id')
                break
    
    if user:
        print(f"\n✅ User found: {user}")
        print(f"User ID: {user_id}")
        
        # Test password verification
        if user.get('password'):
            result = db.verify_password(user_id, password)
            print(f"Password verification result: {result}")
            
            # Test werkzeug directly
            stored_hash = user.get('password')
            if stored_hash:
                direct_result = check_password_hash(stored_hash, password)
                print(f"Direct werkzeug check: {direct_result}")
        else:
            print("❌ No password hash found")
    else:
        print(f"❌ User '{username}' not found")

if __name__ == '__main__':
    test_login()
