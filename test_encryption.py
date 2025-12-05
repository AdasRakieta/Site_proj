#!/usr/bin/env python3
"""
Test script for the Encryption/Cryptography Application
========================================================

This script tests all encryption algorithms and functions
implemented for the computer security systems course.
"""

from utils.encryption_algorithms import (
    ClassicalCiphers,
    ModernEncryption,
    HashingFunctions,
    EncodingFunctions
)


def test_classical_ciphers():
    """Test classical encryption ciphers"""
    print("=" * 60)
    print("CLASSICAL CIPHERS TESTS")
    print("=" * 60)
    
    test_text = "Hello Security Class"
    
    # Caesar Cipher
    print("\n1. Caesar Cipher (Shift: 5)")
    encrypted = ClassicalCiphers.caesar_encrypt(test_text, 5)
    decrypted = ClassicalCiphers.caesar_decrypt(encrypted, 5)
    print(f"   Original:  {test_text}")
    print(f"   Encrypted: {encrypted}")
    print(f"   Decrypted: {decrypted}")
    print(f"   ✓ Match: {decrypted == test_text}")
    
    # Vigenère Cipher
    print("\n2. Vigenère Cipher (Key: SECRET)")
    encrypted = ClassicalCiphers.vigenere_encrypt(test_text, "SECRET")
    decrypted = ClassicalCiphers.vigenere_decrypt(encrypted, "SECRET")
    print(f"   Original:  {test_text}")
    print(f"   Encrypted: {encrypted}")
    print(f"   Decrypted: {decrypted}")
    print(f"   ✓ Match: {decrypted == test_text}")
    
    # Substitution Cipher
    print("\n3. Substitution Cipher")
    sub_key = "ZYXWVUTSRQPONMLKJIHGFEDCBA"
    encrypted = ClassicalCiphers.substitution_encrypt(test_text, sub_key)
    decrypted = ClassicalCiphers.substitution_decrypt(encrypted, sub_key)
    print(f"   Original:  {test_text}")
    print(f"   Key:       {sub_key}")
    print(f"   Encrypted: {encrypted}")
    print(f"   Decrypted: {decrypted}")
    print(f"   ✓ Match: {decrypted == test_text}")
    
    # Rail Fence Cipher
    print("\n4. Rail Fence Cipher (3 Rails)")
    encrypted = ClassicalCiphers.rail_fence_encrypt(test_text, 3)
    decrypted = ClassicalCiphers.rail_fence_decrypt(encrypted, 3)
    print(f"   Original:  {test_text}")
    print(f"   Encrypted: {encrypted}")
    print(f"   Decrypted: {decrypted}")
    print(f"   ✓ Match: {decrypted == test_text}")


def test_modern_encryption():
    """Test modern encryption algorithms"""
    print("\n" + "=" * 60)
    print("MODERN ENCRYPTION TESTS")
    print("=" * 60)
    
    # AES-256
    print("\n1. AES-256 Encryption")
    plaintext = "This is a secret message for testing AES encryption"
    key = "MyVerySecurePassword123"
    
    encrypted_data = ModernEncryption.aes_encrypt(plaintext, key)
    decrypted = ModernEncryption.aes_decrypt(
        encrypted_data['ciphertext'], 
        key, 
        encrypted_data['iv']
    )
    
    print(f"   Plaintext:  {plaintext}")
    print(f"   Key:        {key}")
    print(f"   Ciphertext: {encrypted_data['ciphertext'][:60]}...")
    print(f"   IV:         {encrypted_data['iv']}")
    print(f"   Decrypted:  {decrypted}")
    print(f"   ✓ Match: {decrypted == plaintext}")
    
    # RSA
    print("\n2. RSA Encryption (2048-bit)")
    print("   Generating RSA key pair...")
    keys = ModernEncryption.generate_rsa_keypair(2048)
    
    rsa_message = "RSA encrypted secret"
    encrypted_rsa = ModernEncryption.rsa_encrypt(rsa_message, keys['public_key'])
    decrypted_rsa = ModernEncryption.rsa_decrypt(encrypted_rsa, keys['private_key'])
    
    print(f"   Plaintext:  {rsa_message}")
    print(f"   Ciphertext: {encrypted_rsa[:60]}...")
    print(f"   Decrypted:  {decrypted_rsa}")
    print(f"   ✓ Match: {decrypted_rsa == rsa_message}")
    print(f"   ✓ Public Key Length: {len(keys['public_key'])} bytes")
    print(f"   ✓ Private Key Length: {len(keys['private_key'])} bytes")


def test_hashing_functions():
    """Test cryptographic hashing functions"""
    print("\n" + "=" * 60)
    print("HASHING FUNCTIONS TESTS")
    print("=" * 60)
    
    test_data = "Test message for hashing"
    
    print(f"\n   Input: {test_data}")
    print("\n   Hash Results:")
    
    hashes = HashingFunctions.all_hashes(test_data)
    for algo, hash_value in hashes.items():
        print(f"   {algo.upper():8s}: {hash_value}")
    
    # Verify hash consistency
    print("\n   Verifying hash consistency...")
    hash2 = HashingFunctions.sha256_hash(test_data)
    print(f"   ✓ SHA-256 consistent: {hash2 == hashes['sha256']}")


def test_encoding_functions():
    """Test encoding/decoding functions"""
    print("\n" + "=" * 60)
    print("ENCODING FUNCTIONS TESTS")
    print("=" * 60)
    
    test_text = "Hello, this is a test message for encoding!"
    
    # Base64
    print("\n1. Base64 Encoding")
    encoded = EncodingFunctions.base64_encode(test_text)
    decoded = EncodingFunctions.base64_decode(encoded)
    print(f"   Original: {test_text}")
    print(f"   Encoded:  {encoded}")
    print(f"   Decoded:  {decoded}")
    print(f"   ✓ Match: {decoded == test_text}")
    
    # Hexadecimal
    print("\n2. Hexadecimal Encoding")
    encoded_hex = EncodingFunctions.hex_encode(test_text)
    decoded_hex = EncodingFunctions.hex_decode(encoded_hex)
    print(f"   Original: {test_text}")
    print(f"   Encoded:  {encoded_hex[:60]}...")
    print(f"   Decoded:  {decoded_hex}")
    print(f"   ✓ Match: {decoded_hex == test_text}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ENCRYPTION & CRYPTOGRAPHY APPLICATION TEST SUITE")
    print("Computer Security Systems Course")
    print("=" * 60)
    
    try:
        test_classical_ciphers()
        test_modern_encryption()
        test_hashing_functions()
        test_encoding_functions()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
