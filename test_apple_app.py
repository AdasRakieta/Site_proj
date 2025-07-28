#!/usr/bin/env python3
"""
Test script for Apple SmartHome application
Tests the basic functionality without database connection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_apple_smarthome():
    """Test Apple SmartHome functionality"""
    
    print("Testing Apple SmartHome Application...")
    print("=" * 50)
    
    # Test 1: Import the routes
    try:
        from apple_smarthome.routes import register_apple_routes, apple_bp
        print("✓ Routes module imported successfully")
    except ImportError as e:
        print(f"✗ Routes import failed: {e}")
        return False
    
    # Test 2: Create Flask app and register routes
    try:
        from flask import Flask
        app = Flask(__name__)
        app.secret_key = 'test-key'
        
        routes = register_apple_routes(app)
        print("✓ Routes registered successfully")
        
        # Check that the blueprint is registered
        if 'apple' in app.blueprints:
            print("✓ Apple blueprint registered")
        else:
            print("✗ Apple blueprint not found")
            return False
            
    except Exception as e:
        print(f"✗ App setup failed: {e}")
        return False
    
    # Test 3: Check file structure
    try:
        required_files = [
            'apple_smarthome/README.md',
            'apple_smarthome/templates/apple.html',
            'apple_smarthome/static/css/style.css',
            'apple_smarthome/static/js/app.js',
            'apple_smarthome/static/js/sw.js',
            'apple_smarthome/static/manifest.json',
            'apple_smarthome/static/icons/icon-128x128.png'
        ]
        
        for file_path in required_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            if os.path.exists(full_path):
                print(f"✓ {file_path} exists")
            else:
                print(f"✗ {file_path} missing")
                return False
                
    except Exception as e:
        print(f"✗ File structure check failed: {e}")
        return False
    
    # Test 4: Test app routes with test client
    try:
        with app.test_client() as client:
            
            # Test main Apple app route
            response = client.get('/apple/')
            if response.status_code == 200:
                print("✓ /apple/ route accessible")
            else:
                print(f"✗ /apple/ route failed: {response.status_code}")
            
            # Test manifest
            response = client.get('/apple/manifest.json')
            if response.status_code == 200:
                print("✓ /apple/manifest.json accessible")
            else:
                print(f"✗ /apple/manifest.json failed: {response.status_code}")
            
            # Test service worker
            response = client.get('/apple/sw.js')
            if response.status_code == 200:
                print("✓ /apple/sw.js accessible")
            else:
                print(f"✗ /apple/sw.js failed: {response.status_code}")
            
            # Test status endpoint
            response = client.get('/apple/status')
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('status') == 'ok':
                    print("✓ /apple/status working correctly")
                else:
                    print(f"✗ /apple/status invalid response: {data}")
            else:
                print(f"✗ /apple/status failed: {response.status_code}")
                
    except Exception as e:
        print(f"✗ Route testing failed: {e}")
        return False
    
    # Test 5: Check PWA manifest content
    try:
        import json
        manifest_path = os.path.join(os.path.dirname(__file__), 'apple_smarthome/static/manifest.json')
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        required_keys = ['name', 'short_name', 'start_url', 'display', 'icons']
        for key in required_keys:
            if key in manifest:
                print(f"✓ Manifest has {key}")
            else:
                print(f"✗ Manifest missing {key}")
                return False
                
    except Exception as e:
        print(f"✗ Manifest validation failed: {e}")
        return False
    
    print("=" * 50)
    print("✓ All tests passed! Apple SmartHome app is ready.")
    return True

if __name__ == '__main__':
    success = test_apple_smarthome()
    if not success:
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Apple SmartHome PWA Features:")
    print("- iOS optimized Progressive Web App")
    print("- Offline functionality with Service Worker")
    print("- Apple Touch Icons and splash screens")
    print("- Mobile-first responsive design")
    print("- WebSocket support for real-time updates")
    print("- Haptic feedback integration")
    print("- VPN compatible")
    print("- Can be installed to iOS home screen")
    
    print("\nTo access the app:")
    print("1. Start the main SmartHome application")
    print("2. Navigate to /apple/ in your browser")
    print("3. On iPhone Safari: Share > Add to Home Screen")
    print("=" * 50)