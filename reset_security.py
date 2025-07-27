#!/usr/bin/env python3
"""
Reset and test security state
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def reset_security_state():
    """Reset security state in database"""
    try:
        from utils.smart_home_db_manager import SmartHomeDatabaseManager
        
        db = SmartHomeDatabaseManager()
        
        # Delete existing security_state entry
        print("Deleting existing security_state...")
        delete_query = "DELETE FROM system_settings WHERE setting_key = 'security_state'"
        db._execute_query(delete_query)
        
        # Set new security state
        print("Setting new security state...")
        success = db.set_security_state('Wyłączony')
        print(f"Set security state success: {success}")
        
        # Retrieve it
        print("Retrieving security state...")
        state = db.get_security_state()
        print(f"Retrieved security state: {repr(state)}")
        
        # Test the configure_db wrapper
        print("Testing configure_db wrapper...")
        from app.configure_db import SmartHomeSystemDB
        config_db = SmartHomeSystemDB()
        wrapper_state = config_db.security_state
        print(f"Wrapper security state: {repr(wrapper_state)}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    reset_security_state()
