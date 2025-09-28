#!/usr/bin/env python3
"""
Test script for MultiHomeDBManager using psycopg2 directly
"""

import psycopg2
import json

def test_direct_connection():
    """Test direct psycopg2 connection using same params as VS Code extension"""
    
    print("🔍 Testing direct psycopg2 connection...")
    
    try:
        # Try connecting with the same parameters as VS Code PostgreSQL extension uses
        connection = psycopg2.connect(
            host="100.103.184.90",
            port=5432,
            user="admin",
            password="Qwuizzy123.",
            database="smarthome_multihouse"
        )
        
        print("✅ Direct connection successful!")
        
        cursor = connection.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM homes")
        home_count = cursor.fetchone()[0]
        print(f"📊 Found {home_count} homes in database")
        
        # Test getting users
        cursor.execute("SELECT id, name, email FROM users ORDER BY name")
        users = cursor.fetchall()
        print(f"👥 Found {len(users)} users:")
        for user in users:
            print(f"   - {user[1]} ({user[2]})")
        
        cursor.close()
        connection.close()
        
        print("✅ Direct connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return False

if __name__ == "__main__":
    test_direct_connection()