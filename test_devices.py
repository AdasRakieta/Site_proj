#!/usr/bin/env python3
"""
Quick test to check device types in Admin Home
"""

from utils.multi_home_db_manager import MultiHomeDBManager

def test_devices():
    """Test what devices we have in Admin Home"""
    multi_db = MultiHomeDBManager()
    
    # Admin Home ID and user ID from logs
    admin_home_id = '40a67bc7-6b5d-4a88-bce1-f7ef6d06432c'
    user_id = '727a5147-14e6-405d-921b-931fbc0397ed'
    
    print("🔍 Checking devices in Admin Home...")
    
    # Get all devices
    devices = multi_db.get_home_devices(admin_home_id, user_id)
    print(f"\n📱 Found {len(devices)} devices:")
    for device in devices:
        print(f"  - {device['name']} (type: {device['type']}, room: {device.get('room_name', 'N/A')}, state: {device.get('state', 'N/A')})")
    
    # Get buttons specifically
    buttons = multi_db.get_buttons(admin_home_id, user_id)
    print(f"\n🔘 Found {len(buttons)} buttons:")
    for button in buttons:
        print(f"  - {button['name']} (room: {button.get('room_name', 'N/A')}, state: {button.get('state', 'N/A')})")
    
    # Get lights specifically
    lights = multi_db.get_lights(admin_home_id, user_id)
    print(f"\n💡 Found {len(lights)} lights:")
    for light in lights:
        print(f"  - {light['name']} (room: {light.get('room_name', 'N/A')}, state: {light.get('state', 'N/A')})")
    
    # Get temperature controls specifically
    temp_controls = multi_db.get_temperature_controls(admin_home_id, user_id)
    print(f"\n🌡️ Found {len(temp_controls)} temperature controls:")
    for temp in temp_controls:
        print(f"  - {temp['name']} (room: {temp.get('room_name', 'N/A')}, temp: {temp.get('temperature', 'N/A')})")

if __name__ == "__main__":
    test_devices()