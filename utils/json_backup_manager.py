"""
JSON Backup Manager for SmartHome System
========================================

This module provides automatic fallback to JSON-based storage when PostgreSQL
database is unavailable. It creates and manages a JSON configuration file
with a default sys-admin user.
"""

import json
import os
import secrets
import string
from datetime import datetime
from werkzeug.security import generate_password_hash
from typing import Dict, Any, Optional
import threading


class JSONBackupManager:
    """
    Manages JSON-based fallback storage for SmartHome system.
    Automatically creates configuration file with default admin user.
    """
    
    def __init__(self, config_file: str = 'smart_home_config.json'):
        """
        Initialize JSON backup manager
        
        Args:
            config_file: Path to JSON configuration file
        """
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_file = os.path.join(self.base_dir, 'app', config_file)
        self._lock = threading.RLock()
        self.generated_password = None
        
        # Initialize or load configuration
        self._initialize_config()
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a secure random password
        
        Args:
            length: Length of the password (default: 16)
            
        Returns:
            Secure random password string
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def _initialize_config(self):
        """Initialize or load JSON configuration file"""
        with self._lock:
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # Validate configuration structure
                    if self._validate_config(config):
                        print(f"✓ Loaded existing JSON configuration from {self.config_file}")
                        return
                    else:
                        print(f"⚠ Invalid configuration structure, recreating...")
                        self._create_default_config()
                except Exception as e:
                    print(f"⚠ Failed to load JSON configuration: {e}")
                    print("Creating new configuration file...")
                    self._create_default_config()
            else:
                print(f"ℹ JSON configuration file not found, creating new one...")
                self._create_default_config()
    
    def _validate_config(self, config: Dict) -> bool:
        """
        Validate configuration structure
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_keys = ['users', 'temperature_states', 'security_state', 
                        'rooms', 'buttons', 'temperature_controls', 'automations']
        return all(key in config for key in required_keys)
    
    def _create_default_config(self):
        """Create default JSON configuration file with sys-admin user"""
        # Generate secure password for sys-admin
        self.generated_password = self._generate_secure_password()
        hashed_password = generate_password_hash(self.generated_password)
        
        # Create default configuration
        default_config = {
            'users': {
                'sys-admin': {
                    'id': 'sys-admin-uuid-' + secrets.token_hex(8),
                    'username': 'sys-admin',
                    'password': hashed_password,
                    'role': 'admin',
                    'name': 'System Administrator',
                    'email': 'admin@localhost',
                    'created_at': datetime.now().isoformat(),
                    'is_system_user': True
                }
            },
            'temperature_states': {},
            'security_state': 'Wyłączony',
            'rooms': [],
            'buttons': [],
            'temperature_controls': [],
            'automations': [],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'backup_mode': True,
                'version': '1.0'
            }
        }
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Write configuration file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            
            # Print credentials to console
            print("\n" + "="*70)
            print("🔧 JSON BACKUP MODE ACTIVATED")
            print("="*70)
            print(f"📄 Configuration file created: {self.config_file}")
            print(f"👤 Default admin user created:")
            print(f"   Username: sys-admin")
            print(f"   Password: {self.generated_password}")
            print("="*70)
            print("⚠️  IMPORTANT: Save these credentials! They will not be shown again.")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"✗ Failed to create JSON configuration: {e}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration
        
        Returns:
            Configuration dictionary
        """
        with self._lock:
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠ Failed to load configuration: {e}")
                return {}
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to file
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Create backup of current config
                if os.path.exists(self.config_file):
                    backup_file = self.config_file + '.backup'
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        backup_config = json.load(f)
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        json.dump(backup_config, f, indent=4, ensure_ascii=False)
                
                # Write new configuration
                temp_file = self.config_file + '.tmp'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                
                # Atomic replace
                os.replace(temp_file, self.config_file)
                
                return True
            except Exception as e:
                print(f"✗ Failed to save configuration: {e}")
                return False
    
    def update_metadata(self, key: str, value: Any) -> bool:
        """
        Update metadata in configuration
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            True if successful, False otherwise
        """
        config = self.get_config()
        if 'metadata' not in config:
            config['metadata'] = {}
        
        config['metadata'][key] = value
        config['metadata']['last_updated'] = datetime.now().isoformat()
        
        return self.save_config(config)
    
    def get_admin_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get sys-admin credentials (only if just generated)
        
        Returns:
            Dictionary with username and password, or None
        """
        if self.generated_password:
            return {
                'username': 'sys-admin',
                'password': self.generated_password
            }
        return None
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default state
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Backup current config
                if os.path.exists(self.config_file):
                    backup_file = f"{self.config_file}.reset-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    os.rename(self.config_file, backup_file)
                    print(f"✓ Current configuration backed up to: {backup_file}")
                
                # Create new default config
                self._create_default_config()
                return True
            except Exception as e:
                print(f"✗ Failed to reset configuration: {e}")
                return False


def ensure_json_backup() -> JSONBackupManager:
    """
    Ensure JSON backup is available and return manager instance
    
    Returns:
        JSONBackupManager instance
    """
    try:
        manager = JSONBackupManager()
        return manager
    except Exception as e:
        print(f"✗ Critical: Failed to initialize JSON backup: {e}")
        raise
