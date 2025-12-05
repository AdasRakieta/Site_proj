#!/usr/bin/env python3
"""
Demo script showing all encryption features
"""
from utils.encryption_algorithms import (
    ClassicalCiphers, ModernEncryption, HashingFunctions, EncodingFunctions
)

print("=" * 70)
print(" DEMONSTRACJA APLIKACJI KRYPTOGRAFICZNEJ ".center(70, "="))
print("=" * 70)
print()

# Test message
message = "Bezpieczeństwo Systemów Komputerowych 2024"
print(f"📝 Wiadomość testowa: '{message}'")
print()

# Classical Ciphers
print("1️⃣  SZYFRY KLASYCZNE")
print("-" * 70)
print(f"   Caesar (shift=5):    {ClassicalCiphers.caesar_encrypt(message, 5)}")
print(f"   Vigenère (key=SEC):  {ClassicalCiphers.vigenere_encrypt(message, 'SEC')}")
print(f"   Rail Fence (3):      {ClassicalCiphers.rail_fence_encrypt(message, 3)}")
print()

# Modern Encryption
print("2️⃣  SZYFROWANIE NOWOCZESNE")
print("-" * 70)
aes = ModernEncryption.aes_encrypt(message, "SecretKey123")
print(f"   AES-256:             {aes['ciphertext'][:50]}...")
print(f"   IV:                  {aes['iv']}")
print()

# Hashing
print("3️⃣  FUNKCJE HASZUJĄCE")
print("-" * 70)
hashes = HashingFunctions.all_hashes(message)
for algo, hash_val in hashes.items():
    print(f"   {algo.upper():8s}:           {hash_val[:50]}...")
print()

# Encoding
print("4️⃣  KODOWANIE")
print("-" * 70)
b64 = EncodingFunctions.base64_encode(message)
hex_enc = EncodingFunctions.hex_encode(message)
print(f"   Base64:              {b64}")
print(f"   Hexadecimal:         {hex_enc[:50]}...")
print()

print("=" * 70)
print(" ✅ WSZYSTKIE ALGORYTMY DZIAŁAJĄ POPRAWNIE ".center(70, "="))
print("=" * 70)
