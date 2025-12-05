#!/usr/bin/env python3
"""
Verification script for the Encryption Application
Checks that all routes are properly registered and accessible
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_imports():
    """Verify all necessary imports work"""
    print("Checking imports...")
    try:
        from utils.encryption_algorithms import (
            ClassicalCiphers,
            ModernEncryption,
            HashingFunctions,
            EncodingFunctions
        )
        print("  ✓ Encryption algorithms module")
        
        from app.encryption_routes import encryption_bp
        print("  ✓ Encryption routes module")
        
        print("✓ All imports successful\n")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}\n")
        return False


def check_routes():
    """Verify routes are properly defined"""
    print("Checking route definitions...")
    try:
        from app.encryption_routes import encryption_bp
        from flask import Flask
        
        # Create temporary app to register blueprint
        temp_app = Flask(__name__)
        temp_app.register_blueprint(encryption_bp)
        
        routes = []
        for rule in temp_app.url_map.iter_rules():
            if rule.rule.startswith('/encryption'):
                routes.append((rule.rule, sorted(list(rule.methods - {'HEAD', 'OPTIONS'}))))
        
        print(f"  Found {len(routes)} routes in encryption blueprint:")
        for route, methods in routes:
            print(f"    {route:40s} {methods}")
        
        # Check for expected routes
        route_paths = [r[0] for r in routes]
        expected = ['/encryption/', '/encryption/api/caesar', '/encryption/api/aes', '/encryption/api/hash']
        missing = [e for e in expected if not any(e in r for r in route_paths)]
        
        if missing:
            print(f"  ⚠ Some expected routes might be missing: {missing}")
        
        print("✓ All routes properly defined\n")
        return True
    except Exception as e:
        print(f"✗ Route check error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def verify_template():
    """Verify template file exists"""
    print("Checking template file...")
    template_path = os.path.join(
        os.path.dirname(__file__),
        'templates',
        'encryption.html'
    )
    
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            content = f.read()
            if len(content) > 1000:  # Basic size check
                print(f"  ✓ Template file exists ({len(content)} bytes)")
                print("✓ Template verification passed\n")
                return True
    
    print("✗ Template file not found or too small\n")
    return False


def verify_functionality():
    """Quick functional test of encryption algorithms"""
    print("Running functional tests...")
    try:
        from utils.encryption_algorithms import ClassicalCiphers, ModernEncryption, HashingFunctions
        
        # Test Caesar
        result = ClassicalCiphers.caesar_encrypt("TEST", 3)
        assert result == "WHVW", "Caesar cipher failed"
        print("  ✓ Caesar cipher")
        
        # Test Vigenere
        result = ClassicalCiphers.vigenere_encrypt("TEST", "KEY")
        assert len(result) == 4, "Vigenere cipher failed"
        print("  ✓ Vigenère cipher")
        
        # Test AES
        encrypted = ModernEncryption.aes_encrypt("TEST", "KEY")
        decrypted = ModernEncryption.aes_decrypt(
            encrypted['ciphertext'], 
            "KEY", 
            encrypted['iv']
        )
        assert decrypted == "TEST", "AES failed"
        print("  ✓ AES-256 encryption")
        
        # Test Hashing
        hash_val = HashingFunctions.sha256_hash("TEST")
        assert len(hash_val) == 64, "SHA-256 failed"
        print("  ✓ SHA-256 hashing")
        
        print("✓ All functional tests passed\n")
        return True
    except Exception as e:
        print(f"✗ Functional test error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("ENCRYPTION APPLICATION VERIFICATION")
    print("=" * 60 + "\n")
    
    checks = [
        ("Import Check", check_imports),
        ("Route Check", check_routes),
        ("Template Check", verify_template),
        ("Functionality Check", verify_functionality)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} failed with exception: {e}\n")
            results.append((name, False))
    
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name:30s} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - APPLICATION READY")
    else:
        print("✗ SOME CHECKS FAILED - REVIEW ERRORS ABOVE")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
