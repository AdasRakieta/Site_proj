"""
Encryption Application Routes
==============================

This module provides routes for the encryption/cryptography application.
It handles various encryption algorithms and cryptographic operations.
"""

from flask import Blueprint, render_template, request, jsonify, session
from utils.encryption_algorithms import (
    ClassicalCiphers,
    ModernEncryption,
    HashingFunctions,
    EncodingFunctions
)
import logging

logger = logging.getLogger(__name__)

encryption_bp = Blueprint('encryption', __name__, url_prefix='/encryption')


@encryption_bp.route('/')
def index():
    """Render the main encryption application page"""
    return render_template('encryption.html')


@encryption_bp.route('/api/caesar', methods=['POST'])
def caesar_cipher():
    """Handle Caesar cipher encryption/decryption"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        shift = int(data.get('shift', 3))
        operation = data.get('operation', 'encrypt')
        
        if operation == 'encrypt':
            result = ClassicalCiphers.caesar_encrypt(text, shift)
        else:
            result = ClassicalCiphers.caesar_decrypt(text, shift)
        
        return jsonify({
            'success': True,
            'result': result,
            'algorithm': 'Caesar Cipher',
            'shift': shift
        })
    except Exception as e:
        logger.error(f"Caesar cipher error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@encryption_bp.route('/api/vigenere', methods=['POST'])
def vigenere_cipher():
    """Handle Vigenère cipher encryption/decryption"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        key = data.get('key', '')
        operation = data.get('operation', 'encrypt')
        
        if not key:
            return jsonify({
                'success': False,
                'error': 'Key is required'
            }), 400
        
        if operation == 'encrypt':
            result = ClassicalCiphers.vigenere_encrypt(text, key)
        else:
            result = ClassicalCiphers.vigenere_decrypt(text, key)
        
        return jsonify({
            'success': True,
            'result': result,
            'algorithm': 'Vigenère Cipher',
            'key': key
        })
    except Exception as e:
        logger.error(f"Vigenère cipher error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@encryption_bp.route('/api/substitution', methods=['POST'])
def substitution_cipher():
    """Handle Substitution cipher encryption/decryption"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        key = data.get('key', '')
        operation = data.get('operation', 'encrypt')
        
        if not key or len(key) != 26:
            return jsonify({
                'success': False,
                'error': 'Key must be exactly 26 alphabetic characters'
            }), 400
        
        if operation == 'encrypt':
            result = ClassicalCiphers.substitution_encrypt(text, key)
        else:
            result = ClassicalCiphers.substitution_decrypt(text, key)
        
        return jsonify({
            'success': True,
            'result': result,
            'algorithm': 'Substitution Cipher',
            'key': key
        })
    except Exception as e:
        logger.error(f"Substitution cipher error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@encryption_bp.route('/api/railfence', methods=['POST'])
def rail_fence_cipher():
    """Handle Rail Fence cipher encryption/decryption"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        rails = int(data.get('rails', 3))
        operation = data.get('operation', 'encrypt')
        
        if rails < 2:
            return jsonify({
                'success': False,
                'error': 'Number of rails must be at least 2'
            }), 400
        
        if operation == 'encrypt':
            result = ClassicalCiphers.rail_fence_encrypt(text, rails)
        else:
            result = ClassicalCiphers.rail_fence_decrypt(text, rails)
        
        return jsonify({
            'success': True,
            'result': result,
            'algorithm': 'Rail Fence Cipher',
            'rails': rails
        })
    except Exception as e:
        logger.error(f"Rail Fence cipher error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@encryption_bp.route('/api/aes', methods=['POST'])
def aes_encryption():
    """Handle AES encryption/decryption"""
    try:
        data = request.get_json()
        operation = data.get('operation', 'encrypt')
        
        if operation == 'encrypt':
            text = data.get('text', '')
            key = data.get('key', '')
            
            if not key:
                return jsonify({
                    'success': False,
                    'error': 'Key is required'
                }), 400
            
            result = ModernEncryption.aes_encrypt(text, key)
            
            return jsonify({
                'success': True,
                'result': result['ciphertext'],
                'iv': result['iv'],
                'algorithm': 'AES-256'
            })
        else:
            ciphertext = data.get('text', '')
            key = data.get('key', '')
            iv = data.get('iv', '')
            
            if not key or not iv:
                return jsonify({
                    'success': False,
                    'error': 'Key and IV are required for decryption'
                }), 400
            
            result = ModernEncryption.aes_decrypt(ciphertext, key, iv)
            
            return jsonify({
                'success': True,
                'result': result,
                'algorithm': 'AES-256'
            })
    except Exception as e:
        logger.error(f"AES encryption error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@encryption_bp.route('/api/rsa/generate', methods=['POST'])
def generate_rsa_keys():
    """Generate RSA key pair"""
    try:
        data = request.get_json()
        key_size = int(data.get('key_size', 2048))
        
        keys = ModernEncryption.generate_rsa_keypair(key_size)
        
        return jsonify({
            'success': True,
            'public_key': keys['public_key'],
            'private_key': keys['private_key'],
            'algorithm': f'RSA-{key_size}'
        })
    except Exception as e:
        logger.error(f"RSA key generation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@encryption_bp.route('/api/rsa', methods=['POST'])
def rsa_encryption():
    """Handle RSA encryption/decryption"""
    try:
        data = request.get_json()
        operation = data.get('operation', 'encrypt')
        
        if operation == 'encrypt':
            text = data.get('text', '')
            public_key = data.get('public_key', '')
            
            if not public_key:
                return jsonify({
                    'success': False,
                    'error': 'Public key is required'
                }), 400
            
            result = ModernEncryption.rsa_encrypt(text, public_key)
            
            return jsonify({
                'success': True,
                'result': result,
                'algorithm': 'RSA'
            })
        else:
            ciphertext = data.get('text', '')
            private_key = data.get('private_key', '')
            
            if not private_key:
                return jsonify({
                    'success': False,
                    'error': 'Private key is required for decryption'
                }), 400
            
            result = ModernEncryption.rsa_decrypt(ciphertext, private_key)
            
            return jsonify({
                'success': True,
                'result': result,
                'algorithm': 'RSA'
            })
    except Exception as e:
        logger.error(f"RSA encryption error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@encryption_bp.route('/api/hash', methods=['POST'])
def hashing():
    """Calculate various hashes"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        hash_type = data.get('hash_type', 'all')
        
        if hash_type == 'all':
            result = HashingFunctions.all_hashes(text)
        elif hash_type == 'md5':
            result = {'md5': HashingFunctions.md5_hash(text)}
        elif hash_type == 'sha1':
            result = {'sha1': HashingFunctions.sha1_hash(text)}
        elif hash_type == 'sha256':
            result = {'sha256': HashingFunctions.sha256_hash(text)}
        elif hash_type == 'sha512':
            result = {'sha512': HashingFunctions.sha512_hash(text)}
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid hash type'
            }), 400
        
        return jsonify({
            'success': True,
            'result': result,
            'algorithm': 'Hashing Functions'
        })
    except Exception as e:
        logger.error(f"Hashing error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@encryption_bp.route('/api/encode', methods=['POST'])
def encoding():
    """Handle encoding/decoding operations"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        encoding_type = data.get('encoding_type', 'base64')
        operation = data.get('operation', 'encode')
        
        if encoding_type == 'base64':
            if operation == 'encode':
                result = EncodingFunctions.base64_encode(text)
            else:
                result = EncodingFunctions.base64_decode(text)
        elif encoding_type == 'hex':
            if operation == 'encode':
                result = EncodingFunctions.hex_encode(text)
            else:
                result = EncodingFunctions.hex_decode(text)
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid encoding type'
            }), 400
        
        return jsonify({
            'success': True,
            'result': result,
            'algorithm': f'{encoding_type.upper()} {operation.title()}'
        })
    except Exception as e:
        logger.error(f"Encoding error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
