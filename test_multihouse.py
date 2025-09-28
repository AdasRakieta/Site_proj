#!/usr/bin/env python3
"""
Test script for MultiHomeDBManager
==================================

This script tests the multi-home database functionality.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.multi_home_db_manager import MultiHomeDBManager

def test_multi_home_db():
    """Test MultiHomeDBManager functionality"""
    
    print("🏠 Testing MultiHomeDBManager...")
    print("=" * 50)
    
    try:
        # Initialize the database manager
        db = MultiHomeDBManager(
            host="100.103.184.90",
            port=5432,
            user="admin",
            password="Qwuizzy123.",
            database="smarthome_multihouse"
        )
        print("✅ Database connection established")
        
        # Test 1: Get user homes
        print("\n📋 Test 1: Getting user homes...")
        user_jan_id = None
        user_anna_id = None
        
        # First get user IDs
        with db.get_cursor() as cursor:
            cursor.execute("SELECT id, name, email FROM users ORDER BY name")
            users = cursor.fetchall()
            for user in users:
                print(f"   User: {user[1]} ({user[2]}) - ID: {user[0]}")
                if user[2] == 'jan@test.pl':
                    user_jan_id = user[0]
                elif user[2] == 'anna@test.pl':
                    user_anna_id = user[0]
        
        if user_jan_id:
            jan_homes = db.get_user_homes(user_jan_id)
            print(f"\n🏠 Jan's homes ({len(jan_homes)}):")
            for home in jan_homes:
                print(f"   - {home['name']} ({home['role']}) - Owner: {home['is_owner']}")
        
        if user_anna_id:
            anna_homes = db.get_user_homes(user_anna_id)
            print(f"\n🏠 Anna's homes ({len(anna_homes)}):")
            for home in anna_homes:
                print(f"   - {home['name']} ({home['role']}) - Owner: {home['is_owner']}")
        
        # Test 2: Get home devices
        print("\n📱 Test 2: Getting devices per home...")
        if user_jan_id and jan_homes:
            for home in jan_homes:
                print(f"\n🏠 {home['name']} devices:")
                devices = db.get_home_devices(home['id'], user_jan_id)
                for device in devices:
                    print(f"   - {device['name']} ({device['type']}) in {device['room_name']} - Enabled: {device['enabled']}")
        
        # Test 3: Test home access permissions
        print("\n🔐 Test 3: Testing permissions...")
        if user_jan_id and user_anna_id and jan_homes:
            main_home = next((h for h in jan_homes if h['name'] == 'Dom Główny'), None)
            if main_home:
                print(f"\n🔑 Permissions for 'Dom Główny':")
                print(f"   Jan has access: {db.user_has_home_access(user_jan_id, main_home['id'])}")
                print(f"   Anna has access: {db.user_has_home_access(user_anna_id, main_home['id'])}")
                print(f"   Jan can manage devices: {db.user_has_home_permission(user_jan_id, main_home['id'], 'manage_devices')}")
                print(f"   Anna can control devices: {db.user_has_home_permission(user_anna_id, main_home['id'], 'control_devices')}")
        
        # Test 4: Test device filtering by type
        print("\n💡 Test 4: Getting devices by type...")
        if user_jan_id and jan_homes:
            main_home = next((h for h in jan_homes if h['name'] == 'Dom Główny'), None)
            if main_home:
                lights = db.get_lights(main_home['id'], user_jan_id)
                temp_controls = db.get_temperature_controls(main_home['id'], user_jan_id)
                
                print(f"\n💡 Lights in 'Dom Główny' ({len(lights)}):")
                for light in lights:
                    settings = light['settings'] if light['settings'] else {}  # Already parsed by psycopg2
                    brightness = settings.get('brightness', 'N/A')
                    color = settings.get('color', 'N/A')
                    print(f"   - {light['name']}: State={light['state']}, Brightness={brightness}, Color={color}")
                
                print(f"\n🌡️ Temperature controls in 'Dom Główny' ({len(temp_controls)}):")
                for temp in temp_controls:
                    settings = temp['settings'] if temp['settings'] else {}  # Already parsed by psycopg2
                    target_temp = settings.get('target_temperature', 'N/A')
                    mode = settings.get('mode', 'N/A')
                    print(f"   - {temp['name']}: Current={temp['temperature']}°C, Target={target_temp}°C, Mode={mode}")
        
        # Test 5: Create a new home
        print("\n🏠 Test 5: Creating a new home...")
        if user_anna_id:
            try:
                new_home_id = db.create_home("Dom Testowy", user_anna_id, "Testowy dom do sprawdzenia funkcjonalności")
                print(f"✅ Created new home with ID: {new_home_id}")
                
                # Create a room in the new home
                room_id = db.create_room(new_home_id, "Salon Testowy", user_anna_id, "Testowy salon")
                print(f"✅ Created room with ID: {room_id}")
                
                # Create a device in the new room
                device_id = db.create_device(
                    room_id, "Testowe Światło", "light", user_anna_id,
                    state=True, enabled=True
                )
                print(f"✅ Created device with ID: {device_id}")
                
            except Exception as e:
                print(f"❌ Error creating test home: {e}")
        
        # Test 6: Test current home management
        print("\n🏠 Test 6: Current home management...")
        if user_jan_id:
            current_home = db.get_user_current_home(user_jan_id)
            print(f"Jan's current home ID: {current_home}")
            
            if jan_homes and len(jan_homes) > 1:
                # Switch to different home
                new_current = jan_homes[1]['id']
                success = db.set_user_current_home(user_jan_id, new_current)
                print(f"Switched Jan's home: {success}")
                
                updated_current = db.get_user_current_home(user_jan_id)
                print(f"Jan's new current home ID: {updated_current}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close_connection()
            print("\n🔌 Database connection closed")

if __name__ == "__main__":
    test_multi_home_db()