#!/usr/bin/env python3
"""
Script to debug database system_settings table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_database():
    """Debug the system_settings table"""
    try:
        from utils.smart_home_db_manager import SmartHomeDatabaseManager
        
        db = SmartHomeDatabaseManager()
        
        # Check what's in the system_settings table
        query = "SELECT setting_key, setting_value, description FROM system_settings WHERE setting_key = 'security_state'"
        result = db._execute_query(query, fetch='one')
        
        print(f"Database query result: {result}")
        print(f"Type of result: {type(result)}")
        
        if result:
            # Handle both dict and list formats
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if isinstance(result, dict):
                setting_val = result.get('setting_value')
                print(f"Raw setting_value: {repr(setting_val)}")
                print(f"Type of setting_value: {type(setting_val)}")
                print(f"Length of setting_value: {len(setting_val) if setting_val else 'N/A'}")
            else:
                print(f"Unexpected result format: {result}")
        
        # Try to get via the method
        try:
            state = db.get_security_state()
            print(f"✓ Successfully got security state: {repr(state)}")
        except Exception as e:
            print(f"✗ Error getting security state: {e}")
        
    except Exception as e:
        print(f"Error debugging database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_database()
