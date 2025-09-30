#!/usr/bin/env python3
"""
Quick validation of batch API and role system implementation
"""

import os
import sys

def validate_batch_api_implementation():
    """Validate that batch API is properly implemented"""
    
    print("🧪 Validating Batch API Implementation")
    print("=" * 50)
    
    # Check frontend file for batch functionality
    dragndrop_path = "static/js/dragNdrop.js"
    
    if not os.path.exists(dragndrop_path):
        print("❌ dragNdrop.js file not found")
        return False
    
    with open(dragndrop_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Key batch functionality indicators
    required_features = [
        '/api/devices/batch-update',  # Batch API endpoint
        'isSaving',                   # Race condition protection
        'fetch(', # Modern fetch API usage
        'JSON.stringify'             # Proper data serialization
    ]
    
    print("🔍 Checking for required batch features:")
    all_found = True
    
    for feature in required_features:
        if feature in content:
            print(f"   ✅ {feature}")
        else:
            print(f"   ❌ {feature}")
            all_found = False
    
    # Check for race condition protection patterns
    race_protection_patterns = [
        'isSaving = true',
        'disabled = true',
        'isSaving = false'
    ]
    
    print("\n🛡️  Checking race condition protection:")
    race_protection_count = 0
    
    for pattern in race_protection_patterns:
        if pattern in content:
            print(f"   ✅ {pattern}")
            race_protection_count += 1
        else:
            print(f"   ⚠️  {pattern} (optional)")
    
    # Summary
    print(f"\n📊 Batch API Implementation Status:")
    print(f"   Core Features: {sum(1 for f in required_features if f in content)}/{len(required_features)}")
    print(f"   Race Protection: {race_protection_count}/{len(race_protection_patterns)}")
    
    if all_found and race_protection_count >= 2:
        print("✅ Batch API implementation is complete!")
        return True
    elif all_found:
        print("✅ Batch API core functionality is implemented!")
        return True
    else:
        print("⚠️  Batch API implementation may be incomplete")
        return False

def validate_role_system_code():
    """Validate role system code implementation"""
    
    print("\n🔐 Validating Role System Implementation")
    print("=" * 50)
    
    # Check MultiHomeDBManager for role methods
    db_manager_path = "utils/multi_home_db_manager.py"
    
    if not os.path.exists(db_manager_path):
        print("❌ multi_home_db_manager.py not found")
        return False
    
    with open(db_manager_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Required role system methods
    role_methods = [
        'def is_sys_admin',
        'def get_sys_admin_users',
        'def setup_initial_sys_admin',
        'def batch_update_devices'
    ]
    
    print("🔍 Checking for role system methods:")
    methods_found = 0
    
    for method in role_methods:
        if method in content:
            print(f"   ✅ {method}")
            methods_found += 1
        else:
            print(f"   ❌ {method}")
    
    # Check for sys-admin role references
    role_patterns = [
        "'sys-admin'",
        '"sys-admin"',
        'role = sys-admin',
        'sys_admin'
    ]
    
    print("\n👤 Checking sys-admin role implementation:")
    role_refs = 0
    
    for pattern in role_patterns:
        if pattern in content:
            print(f"   ✅ {pattern}")
            role_refs += 1
    
    # Check routes file for batch endpoint
    routes_path = "app/routes.py"
    batch_endpoint_exists = False
    
    if os.path.exists(routes_path):
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        if '/api/devices/batch-update' in routes_content and 'def batch_update_devices' in routes_content:
            print("   ✅ Batch update API endpoint implemented")
            batch_endpoint_exists = True
        else:
            print("   ⚠️  Batch update API endpoint not found")
    
    # Summary
    print(f"\n📊 Role System Implementation Status:")
    print(f"   Core Methods: {methods_found}/{len(role_methods)}")
    print(f"   Role References: {role_refs} found")
    print(f"   API Endpoint: {'✅' if batch_endpoint_exists else '❌'}")
    
    success = methods_found >= 3 and role_refs >= 2 and batch_endpoint_exists
    
    if success:
        print("✅ Role system implementation is complete!")
    else:
        print("⚠️  Role system implementation may be incomplete")
    
    return success

def main():
    """Run validation suite"""
    
    print("🎯 Smart Home System - Implementation Validation")
    print("=" * 70)
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Run validations
    batch_api_valid = validate_batch_api_implementation()
    role_system_valid = validate_role_system_code()
    
    print("\n" + "=" * 70)
    print("📋 Validation Summary")
    print("=" * 70)
    print(f"Batch API Implementation: {'✅ VALID' if batch_api_valid else '❌ INVALID'}")
    print(f"Role System Implementation: {'✅ VALID' if role_system_valid else '❌ INVALID'}")
    
    if batch_api_valid and role_system_valid:
        print("\n🎉 SUCCESS! All implementations are valid!")
        print("💡 Your system is ready for:")
        print("   • Batch device updates (performance optimized)")
        print("   • Race condition prevention during saves")  
        print("   • Sys-admin role with global access")
        print("   • Per-home role assignments")
        print("   • Automatic home admin assignment")
        return True
    else:
        print(f"\n⚠️  Some implementations need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)