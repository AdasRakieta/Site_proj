#!/usr/bin/env python3
"""
Reset Admin Password for JSON Fallback Mode
===========================================

This script allows you to reset the sys-admin password when using JSON fallback mode.
Use this when you don't have access to the database and forgot the admin password.

Usage:
    python reset_admin_password.py
"""

import sys
import os
import json
from getpass import getpass
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """Reset sys-admin password in JSON configuration file"""
    
    config_file = 'app/smart_home_config.json'
    
    # Check if config file exists
    if not os.path.exists(config_file):
        print(f"✗ Configuration file not found: {config_file}")
        print("  The system is not in JSON fallback mode.")
        return False
    
    print("\n" + "="*70)
    print("🔐 Reset Admin Password - JSON Fallback Mode")
    print("="*70 + "\n")
    
    # Load current config
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False
    
    # Check if sys-admin exists
    if 'users' not in config or 'sys-admin' not in config['users']:
        print("✗ sys-admin user not found in configuration")
        return False
    
    admin_user = config['users']['sys-admin']
    print(f"Found admin user:")
    print(f"  Username: {admin_user['username']}")
    print(f"  Email: {admin_user['email']}")
    print(f"  User ID: {admin_user['id']}\n")
    
    # Get new password
    while True:
        new_password = getpass("Enter new password for sys-admin: ")
        if len(new_password) < 8:
            print("✗ Password must be at least 8 characters long")
            continue
        
        confirm_password = getpass("Confirm new password: ")
        if new_password != confirm_password:
            print("✗ Passwords don't match, try again\n")
            continue
        
        break
    
    # Update password
    try:
        config['users']['sys-admin']['password'] = generate_password_hash(new_password)
        
        # Save updated config
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print("\n" + "="*70)
        print("✓ Password successfully updated!")
        print("="*70)
        print(f"\nYou can now login with:")
        print(f"  Username: sys-admin")
        print(f"  Password: {new_password}")
        print(f"\n⚠️  IMPORTANT: Save this password securely!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to update password: {e}")
        return False

if __name__ == '__main__':
    success = reset_admin_password()
    sys.exit(0 if success else 1)
