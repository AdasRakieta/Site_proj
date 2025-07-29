#!/usr/bin/env python3
"""
Test script dla API SmartHome - sprawdza funkcjonalność endpointów
"""

import requests
import json
import sys

def test_api_endpoints():
    """Test podstawowych endpointów API"""
    
    # Konfiguracja
    base_url = "http://100.126.230.74:5000"  # Zmień na swój URL serwera
    session = requests.Session()
    
    print("=== SmartHome API Test ===")
    print(f"Base URL: {base_url}")
    print()
    
    # 1. Test logowania
    print("1. Test logowania...")
    login_data = {
        "username": "admin",
        "password": "admin"  # Standard admin password
    }
    
    try:
        response = session.post(f"{base_url}/login", json=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            if data.get("status") == "success":
                print("   ✓ Login successful")
            else:
                print("   ✗ Login failed")
                return
        else:
            print(f"   ✗ Login request failed: {response.text}")
            return
            
    except Exception as e:
        print(f"   ✗ Login error: {e}")
        return
    
    print()
    
    # 2. Test temperatury
    print("2. Test API temperatury...")
    try:
        response = session.get(f"{base_url}/api/temperature_controls")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if data.get("status") == "success":
                controls = data.get("data", [])
                print(f"   ✓ Znaleziono {len(controls)} kontrolek temperatury")
                for control in controls:
                    print(f"      - {control.get('name')} w pokoju {control.get('room')}: {control.get('temperature')}°C")
            else:
                print("   ✗ API response indicates failure")
        else:
            print(f"   ✗ Temperature API failed: {response.text}")
            
    except Exception as e:
        print(f"   ✗ Temperature API error: {e}")
    
    print()
    
    # 3. Test zabezpieczeń
    print("3. Test API zabezpieczeń...")
    try:
        response = session.get(f"{base_url}/api/security")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if data.get("status") == "success":
                security_state = data.get("security_state")
                print(f"   ✓ Stan zabezpieczeń: {security_state}")
            else:
                print("   ✗ Security API response indicates failure")
        else:
            print(f"   ✗ Security API failed: {response.text}")
            
    except Exception as e:
        print(f"   ✗ Security API error: {e}")
    
    print()
    
    # 4. Test pokoi
    print("4. Test API pokoi...")
    try:
        response = session.get(f"{base_url}/api/rooms")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            rooms = data if isinstance(data, list) else data.get("data", [])
            print(f"   ✓ Znaleziono {len(rooms)} pokoi")
            for room in rooms:
                room_name = room if isinstance(room, str) else room.get('name', 'Unknown')
                print(f"      - {room_name}")
        else:
            print(f"   ✗ Rooms API failed: {response.text}")
            
    except Exception as e:
        print(f"   ✗ Rooms API error: {e}")
    
    print()
    print("=== Test zakończony ===")

if __name__ == "__main__":
    test_api_endpoints()
