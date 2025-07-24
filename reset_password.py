#!/usr/bin/env python3
"""
Reset admin password for testing
"""

import psycopg2
from werkzeug.security import generate_password_hash

def reset_admin_password():
    try:
        # Connect to database
        conn = psycopg2.connect(
            host='192.168.1.219',
            database='admin',
            user='admin',
            password='Qwuizzy123.'
        )
        cur = conn.cursor()
        
        # Check current users
        cur.execute("SELECT id, name, email, role FROM users")
        users = cur.fetchall()
        
        print("Current users in database:")
        for user in users:
            print(f"  ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Role: {user[3]}")
        
        # Reset admin password to 'admin123' - use the UUID as username that was wrongly migrated
        new_password = 'admin123'
        password_hash = generate_password_hash(new_password)
        
        # First user with admin role is the admin
        cur.execute("""
            UPDATE users 
            SET password_hash = %s, name = 'admin'
            WHERE role = 'admin'
        """, (password_hash,))
        
        if cur.rowcount > 0:
            conn.commit()
            print(f"\n✅ Admin password reset to: {new_password}")
        else:
            print("\n❌ No admin user found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    reset_admin_password()
