#!/usr/bin/env python3
"""
Test API endpoints to debug the issue
"""

import requests
import json

def test_api():
    """Test API endpoints"""
    base_url = "http://localhost:5000"
    
    # Login first
    session = requests.Session()
    login_data = {
        'username': 'admin',
        'password': 'admin'
    }
    
    print("🔑 Logging in...")
    login_response = session.post(f"{base_url}/login", data=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    print("✅ Logged in successfully")
    
    # Test /api/buttons
    print("\n🔘 Testing /api/buttons...")
    buttons_response = session.get(f"{base_url}/api/buttons")
    
    if buttons_response.status_code == 200:
        buttons = buttons_response.json()
        print(f"✅ Got {len(buttons)} buttons:")
        for button in buttons:
            print(f"  - {button}")
    else:
        print(f"❌ Buttons API failed: {buttons_response.status_code}")
        print(f"Response: {buttons_response.text}")
    
    # Test /api/rooms
    print("\n🏠 Testing /api/rooms...")
    rooms_response = session.get(f"{base_url}/api/rooms")
    
    if rooms_response.status_code == 200:
        rooms = rooms_response.json()
        print(f"✅ Got {len(rooms)} rooms:")
        for room in rooms:
            print(f"  - {room}")
    else:
        print(f"❌ Rooms API failed: {rooms_response.status_code}")
        print(f"Response: {rooms_response.text}")
    
    # Test /api/temperature_controls
    print("\n🌡️ Testing /api/temperature_controls...")
    temp_response = session.get(f"{base_url}/api/temperature_controls")
    
    if temp_response.status_code == 200:
        temp_data = temp_response.json()
        print(f"✅ Got temperature controls:")
        print(f"  - {temp_data}")
    else:
        print(f"❌ Temperature API failed: {temp_response.status_code}")
        print(f"Response: {temp_response.text}")

if __name__ == "__main__":
    test_api()