"""
Encryption and Cryptography Algorithms Module
==============================================

This module contains various encryption algorithms and cryptographic functions
for educational purposes in computer security systems course.

Includes:
- Classical ciphers (Caesar, Vigenère, Substitution, Transposition)
- Modern encryption (AES, RSA)
- Hashing functions (MD5, SHA family)
- Encoding functions (Base64)
"""

import hashlib
import base64
import string
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import hashes, serialization
import os


class ClassicalCiphers:
    """Classical encryption ciphers for educational purposes"""
    
    @staticmethod
    def caesar_encrypt(text, shift):
        """
        Caesar cipher encryption
        Args:
            text: Plain text to encrypt
            shift: Number of positions to shift (0-25)
        Returns:
            Encrypted text
        """
        result = ""
        for char in text:
            if char.isalpha():
                ascii_offset = 65 if char.isupper() else 97
                result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
            else:
                result += char
        return result
    
    @staticmethod
    def caesar_decrypt(text, shift):
        """
        Caesar cipher decryption
        Args:
            text: Encrypted text
            shift: Number of positions to shift (0-25)
        Returns:
            Decrypted text
        """
        return ClassicalCiphers.caesar_encrypt(text, -shift)
    
    @staticmethod
    def vigenere_encrypt(text, key):
        """
        Vigenère cipher encryption
        Args:
            text: Plain text to encrypt
            key: Encryption key (alphabetic string)
        Returns:
            Encrypted text
        """
        if not key or not key.isalpha():
            raise ValueError("Key must contain only alphabetic characters")
        
        result = ""
        key = key.upper()
        key_index = 0
        
        for char in text:
            if char.isalpha():
                ascii_offset = 65 if char.isupper() else 97
                shift = ord(key[key_index % len(key)]) - 65
                result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
                key_index += 1
            else:
                result += char
        
        return result
    
    @staticmethod
    def vigenere_decrypt(text, key):
        """
        Vigenère cipher decryption
        Args:
            text: Encrypted text
            key: Decryption key (alphabetic string)
        Returns:
            Decrypted text
        """
        if not key or not key.isalpha():
            raise ValueError("Key must contain only alphabetic characters")
        
        result = ""
        key = key.upper()
        key_index = 0
        
        for char in text:
            if char.isalpha():
                ascii_offset = 65 if char.isupper() else 97
                shift = ord(key[key_index % len(key)]) - 65
                result += chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
                key_index += 1
            else:
                result += char
        
        return result
    
    @staticmethod
    def substitution_encrypt(text, key):
        """
        Substitution cipher encryption
        Args:
            text: Plain text to encrypt
            key: 26-character substitution alphabet
        Returns:
            Encrypted text
        """
        if len(key) != 26 or not key.isalpha():
            raise ValueError("Key must be a 26-character alphabetic string")
        
        alphabet = string.ascii_uppercase
        key = key.upper()
        trans_table = str.maketrans(alphabet + alphabet.lower(), 
                                     key + key.lower())
        return text.translate(trans_table)
    
    @staticmethod
    def substitution_decrypt(text, key):
        """
        Substitution cipher decryption
        Args:
            text: Encrypted text
            key: 26-character substitution alphabet
        Returns:
            Decrypted text
        """
        if len(key) != 26 or not key.isalpha():
            raise ValueError("Key must be a 26-character alphabetic string")
        
        alphabet = string.ascii_uppercase
        key = key.upper()
        trans_table = str.maketrans(key + key.lower(), 
                                     alphabet + alphabet.lower())
        return text.translate(trans_table)
    
    @staticmethod
    def rail_fence_encrypt(text, rails):
        """
        Rail Fence cipher encryption (transposition cipher)
        Args:
            text: Plain text to encrypt
            rails: Number of rails
        Returns:
            Encrypted text
        Note:
            Spaces are removed from the text before encryption as per traditional
            Rail Fence cipher implementation. This is expected behavior.
        """
        if rails < 2:
            raise ValueError("Number of rails must be at least 2")
        
        # Remove spaces for cleaner encryption (standard Rail Fence behavior)
        # The decryption will return text without spaces
        text = text.replace(" ", "")
        fence = [[] for _ in range(rails)]
        rail = 0
        direction = 1
        
        for char in text:
            fence[rail].append(char)
            rail += direction
            
            if rail == 0 or rail == rails - 1:
                direction = -direction
        
        return ''.join([''.join(rail) for rail in fence])
    
    @staticmethod
    def rail_fence_decrypt(text, rails):
        """
        Rail Fence cipher decryption
        Args:
            text: Encrypted text
            rails: Number of rails
        Returns:
            Decrypted text (without spaces - spaces are removed during encryption)
        Note:
            Since Rail Fence encryption removes spaces, the decrypted text will not
            contain spaces even if the original text had them. This is standard
            behavior for this cipher.
        """
        if rails < 2:
            raise ValueError("Number of rails must be at least 2")
        
        # Calculate the length of each rail
        fence_lengths = [0] * rails
        rail = 0
        direction = 1
        
        for _ in text:
            fence_lengths[rail] += 1
            rail += direction
            if rail == 0 or rail == rails - 1:
                direction = -direction
        
        # Build the fence
        fence = []
        idx = 0
        for length in fence_lengths:
            fence.append(list(text[idx:idx + length]))
            idx += length
        
        # Read the fence
        result = []
        rail = 0
        direction = 1
        for _ in text:
            result.append(fence[rail].pop(0))
            rail += direction
            if rail == 0 or rail == rails - 1:
                direction = -direction
        
        return ''.join(result)


class ModernEncryption:
    """Modern encryption algorithms using cryptography library"""
    
    @staticmethod
    def aes_encrypt(plaintext, key):
        """
        AES encryption (256-bit)
        Args:
            plaintext: Text to encrypt (string)
            key: 32-byte encryption key (or string to be hashed)
        Returns:
            Dictionary with 'ciphertext' and 'iv' in base64
        """
        # Generate key from string if necessary
        if isinstance(key, str):
            key = hashlib.sha256(key.encode()).digest()
        
        # Ensure key is 32 bytes
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        
        # Generate random IV
        iv = os.urandom(16)
        
        # Pad the plaintext
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'iv': base64.b64encode(iv).decode()
        }
    
    @staticmethod
    def aes_decrypt(ciphertext_b64, key, iv_b64):
        """
        AES decryption (256-bit)
        Args:
            ciphertext_b64: Base64 encoded ciphertext
            key: 32-byte decryption key (or string to be hashed)
            iv_b64: Base64 encoded initialization vector
        Returns:
            Decrypted plaintext
        """
        # Generate key from string if necessary
        if isinstance(key, str):
            key = hashlib.sha256(key.encode()).digest()
        
        # Ensure key is 32 bytes
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        
        # Decode base64
        ciphertext = base64.b64decode(ciphertext_b64)
        iv = base64.b64decode(iv_b64)
        
        # Decrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext.decode()
    
    @staticmethod
    def generate_rsa_keypair(key_size=2048):
        """
        Generate RSA key pair
        Args:
            key_size: Key size in bits (default 2048)
        Returns:
            Dictionary with 'private_key' and 'public_key' in PEM format
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Serialize keys to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        return {
            'private_key': private_pem,
            'public_key': public_pem
        }
    
    @staticmethod
    def rsa_encrypt(plaintext, public_key_pem):
        """
        RSA encryption
        Args:
            plaintext: Text to encrypt
            public_key_pem: Public key in PEM format
        Returns:
            Base64 encoded ciphertext
        """
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        ciphertext = public_key.encrypt(
            plaintext.encode(),
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(ciphertext).decode()
    
    @staticmethod
    def rsa_decrypt(ciphertext_b64, private_key_pem):
        """
        RSA decryption
        Args:
            ciphertext_b64: Base64 encoded ciphertext
            private_key_pem: Private key in PEM format
        Returns:
            Decrypted plaintext
        """
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        ciphertext = base64.b64decode(ciphertext_b64)
        
        plaintext = private_key.decrypt(
            ciphertext,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return plaintext.decode()


class HashingFunctions:
    """Cryptographic hashing functions"""
    
    @staticmethod
    def md5_hash(text):
        """Calculate MD5 hash"""
        return hashlib.md5(text.encode()).hexdigest()
    
    @staticmethod
    def sha1_hash(text):
        """Calculate SHA-1 hash"""
        return hashlib.sha1(text.encode()).hexdigest()
    
    @staticmethod
    def sha256_hash(text):
        """Calculate SHA-256 hash"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    @staticmethod
    def sha512_hash(text):
        """Calculate SHA-512 hash"""
        return hashlib.sha512(text.encode()).hexdigest()
    
    @staticmethod
    def all_hashes(text):
        """Calculate all common hashes"""
        return {
            'md5': HashingFunctions.md5_hash(text),
            'sha1': HashingFunctions.sha1_hash(text),
            'sha256': HashingFunctions.sha256_hash(text),
            'sha512': HashingFunctions.sha512_hash(text)
        }


class EncodingFunctions:
    """Encoding and decoding functions"""
    
    @staticmethod
    def base64_encode(text):
        """Encode text to Base64"""
        return base64.b64encode(text.encode()).decode()
    
    @staticmethod
    def base64_decode(encoded_text):
        """Decode Base64 to text"""
        return base64.b64decode(encoded_text.encode()).decode()
    
    @staticmethod
    def hex_encode(text):
        """Encode text to hexadecimal"""
        return text.encode().hex()
    
    @staticmethod
    def hex_decode(hex_text):
        """Decode hexadecimal to text"""
        return bytes.fromhex(hex_text).decode()
