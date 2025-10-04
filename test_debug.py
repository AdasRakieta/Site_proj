#!/usr/bin/env python3

"""
Test script for debugging device states and management logs in SmartHome multihouse system.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.multi_home_db_manager import MultiHomeDBManager

def test_device_states():
    """Test device state retrieval"""
    print("=== Testing MultiHome DB Manager ===")
    
    # Initialize DB manager
    multi_db = MultiHomeDBManager()
    print(f"Connected to: {multi_db.host}:{multi_db.port}/{multi_db.database}")
    
    # Test user and home IDs from the database  
    admin_user_id = '727a5147-14e6-405d-921b-931fbc0397ed'  # admin user (correct ID)
    main_home_id = 'eb7490c1-1028-46c1-bd7c-1900980a964e'   # Main Home ID
    
    print(f"\nTesting with user_id: {admin_user_id}")
    print(f"Testing with home_id: {main_home_id}")
    
    # Test 1: Get home rooms
    print("\n--- Getting home rooms ---")
    try:
        rooms = multi_db.get_home_rooms(main_home_id, admin_user_id)
        print(f"Found {len(rooms)} rooms:")
        for room in rooms:
            print(f"  - {room['name']} (ID: {room['id']})")
    except Exception as e:
        print(f"Error getting rooms: {e}")
        return
    
    # Test 2: Get devices in each room
    print("\n--- Getting devices in rooms ---")
    for room in rooms:
        room_id = room['id']
        room_name = room['name']
        
        try:
            devices = multi_db.get_room_devices(room_id, admin_user_id)
            print(f"\nRoom '{room_name}' has {len(devices)} devices:")
            
            for device in devices:
                print(f"  - {device['name']} ({device['type']}) - State: {device['state']}")
                if device['type'] == 'temperature_control':
                    print(f"    Temperature: {device.get('temperature', 'N/A')}")
        except Exception as e:
            print(f"Error getting devices for room {room_name}: {e}")
    
    # Test 3: Get management logs
    print("\n--- Getting management logs ---")
    try:
        logs = multi_db.get_home_management_logs(main_home_id, admin_user_id, limit=5)
        print(f"Found {len(logs)} management logs:")
        for log in logs:
            print(f"  - {log['timestamp']}: {log['level']} - {log['message']}")
    except Exception as e:
        print(f"Error getting management logs: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_device_states()