#!/usr/bin/env python3
"""
Script to check users in database
"""

from utils.smart_home_db_manager import SmartHomeDatabaseManager

def main():
    db = SmartHomeDatabaseManager()
    users = db.get_users()
    
    print('Available users:')
    for user in users:
        user_id = user.get('id')
        name = user.get('name')
        email = user.get('email')
        role = user.get('role')
        password_hash = user.get('password', 'No password')[:20] + '...' if user.get('password') else 'No password'
        
        print(f'  - ID: {user_id}')
        print(f'    Name: {name}')
        print(f'    Email: {email}')
        print(f'    Role: {role}')
        print(f'    Password hash: {password_hash}')
        print()

if __name__ == '__main__':
    main()
