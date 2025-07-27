#!/usr/bin/env python3
"""
Test script to identify the security page error
"""

import sys
import os
import traceback

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test importing the necessary modules"""
    try:
        from app.configure_db import SmartHomeSystemDB
        print("✓ Successfully imported SmartHomeSystemDB")
        return True
    except Exception as e:
        print(f"✗ Failed to import SmartHomeSystemDB: {e}")
        traceback.print_exc()
        return False

def test_initialization():
    """Test initializing the SmartHome system"""
    try:
        from app.configure_db import SmartHomeSystemDB
        smart_home = SmartHomeSystemDB()
        print("✓ Successfully initialized SmartHomeSystemDB")
        return smart_home
    except Exception as e:
        print(f"✗ Failed to initialize SmartHomeSystemDB: {e}")
        traceback.print_exc()
        return None

def test_security_state(smart_home):
    """Test accessing the security state"""
    try:
        if smart_home is None:
            print("✗ Cannot test security state - smart_home is None")
            return False
        
        state = smart_home.security_state
        print(f"✓ Successfully accessed security state: {state}")
        return True
    except Exception as e:
        print(f"✗ Failed to access security state: {e}")
        traceback.print_exc()
        return False

def test_flask_route():
    """Test creating a minimal Flask route like the security route"""
    try:
        from flask import Flask, render_template
        from app.configure_db import SmartHomeSystemDB
        
        app = Flask(__name__, template_folder='templates')
        app.secret_key = 'test-key'
        smart_home = SmartHomeSystemDB()
        
        @app.route('/test-security')
        def test_security():
            # Simulate the security route logic
            user_data = None
            current_security_state = smart_home.security_state
            return f"Security state: {current_security_state}"
        
        with app.test_client() as client:
            response = client.get('/test-security')
            print(f"✓ Test route successful. Response: {response.get_data(as_text=True)}")
            return True
            
    except Exception as e:
        print(f"✗ Failed to test Flask route: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== SmartHome Security Page Error Diagnosis ===\n")
    
    print("1. Testing imports...")
    if not test_import():
        sys.exit(1)
    
    print("\n2. Testing initialization...")
    smart_home = test_initialization()
    if smart_home is None:
        sys.exit(1)
    
    print("\n3. Testing security state access...")
    if not test_security_state(smart_home):
        sys.exit(1)
    
    print("\n4. Testing Flask route simulation...")
    if not test_flask_route():
        sys.exit(1)
    
    print("\n✓ All tests passed! The issue might be elsewhere.")
