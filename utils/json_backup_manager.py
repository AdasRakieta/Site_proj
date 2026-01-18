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
import uuid
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
        
        # Generate admin user ID
        admin_user_id = str(uuid.uuid4())
        
        # Create default home for admin user
        default_home_id = str(uuid.uuid4())
        
        # Create default configuration
        default_config = {
            'users': {
                'sys-admin': {
                    'id': admin_user_id,
                    'username': 'sys-admin',
                    'password': hashed_password,
                    'role': 'admin',
                    'name': 'System Administrator',
                    'email': 'admin@localhost',
                    'created_at': datetime.now().isoformat(),
                    'is_system_user': True
                }
            },
            'homes': {
                default_home_id: {
                    'id': default_home_id,
                    'name': 'My Home',
                    'description': 'Default home created with system',
                    'owner_id': admin_user_id,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            },
            'user_homes': {
                # Mapping: {home_id: [{user_id, role, permissions, joined_at}]}
                default_home_id: [
                    {
                        'user_id': admin_user_id,
                        'role': 'admin',
                        'permissions': ['read', 'write', 'admin'],
                        'joined_at': datetime.now().isoformat()
                    }
                ]
            },
            'user_current_home': {
                # Mapping: {user_id: home_id}
                admin_user_id: default_home_id
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
    
    def get_user_homes(self, user_id: str) -> list:
        """Get all homes a user has access to in JSON mode"""
        config = self.get_config()
        user_homes_data = config.get('user_homes', {})
        homes_data = config.get('homes', {})
        
        result = []
        for home_id, users_list in user_homes_data.items():
            # Check if this user is in the users_list for this home
            for user_entry in users_list:
                if user_entry.get('user_id') == user_id:
                    home_info = homes_data.get(home_id)
                    if home_info:
                        result.append({
                            'id': home_id,
                            'name': home_info.get('name', 'Unknown'),
                            'description': home_info.get('description', ''),
                            'owner_id': home_info.get('owner_id'),
                            'role': user_entry.get('role'),
                            'permissions': user_entry.get('permissions', []),
                            'joined_at': user_entry.get('joined_at'),
                            'is_owner': home_info.get('owner_id') == user_id,
                            # Location fields so the settings form is prefilled after refresh
                            'address': home_info.get('address'),
                            'city': home_info.get('city'),
                            'country': home_info.get('country'),
                            'country_code': home_info.get('country_code'),
                            'street': home_info.get('street'),
                            'house_number': home_info.get('house_number'),
                            'apartment_number': home_info.get('apartment_number'),
                            'postal_code': home_info.get('postal_code'),
                            'latitude': home_info.get('latitude'),
                            'longitude': home_info.get('longitude'),
                            'created_at': home_info.get('created_at'),
                            'updated_at': home_info.get('updated_at')
                        })
                    break
        
        return result
    
    def get_user_current_home(self, user_id: str) -> Optional[str]:
        """Get the current home ID for a user in JSON mode"""
        config = self.get_config()
        user_current_home = config.get('user_current_home', {})
        return user_current_home.get(user_id)
    
    def set_user_current_home(self, user_id: str, home_id: str) -> bool:
        """Set the current home for a user in JSON mode"""
        config = self.get_config()
        if 'user_current_home' not in config:
            config['user_current_home'] = {}
        config['user_current_home'][user_id] = home_id
        return self.save_config(config)
    
    def get_home_rooms(self, home_id: str) -> list:
        """Get all rooms in a home in JSON mode"""
        config = self.get_config()
        rooms = config.get('rooms', [])
        return [room for room in rooms if room.get('home_id') == home_id]
    
    def get_home_devices(self, home_id: str) -> list:
        """Get all devices in a home in JSON mode"""
        config = self.get_config()
        devices = []
        
        # Get buttons for this home
        for button in config.get('buttons', []):
            if button.get('home_id') == home_id:
                devices.append({**button, 'device_type': 'button'})
        
        # Get temperature controls for this home
        for temp_control in config.get('temperature_controls', []):
            if temp_control.get('home_id') == home_id:
                devices.append({**temp_control, 'device_type': 'temperature_control'})
        
        return devices
    
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
