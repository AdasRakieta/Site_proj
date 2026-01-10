"""
SmartHome System with PostgreSQL Database Backend
================================================

This is a modified version of the SmartHomeSystem class that uses PostgreSQL
database instead of JSON files for data storage.

All methods maintain the same interface as the original SmartHomeSystem class
to ensure compatibility with existing code.
"""

import os
import uuid
import threading
import time
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from typing import Dict, List, Optional, Tuple, Any

# Import the new database manager
from utils.smart_home_db_manager import SmartHomeDatabaseManager, DatabaseError
from utils.weather_service import WeatherService

class SmartHomeSystemDB:
    """
    SmartHome System with PostgreSQL Database Backend
    
    This class provides the same interface as the original SmartHomeSystem
    but uses PostgreSQL database for data persistence instead of JSON files.
    Automatically falls back to JSON mode if database is unavailable.
    """
    
    def __init__(self, config_file=None, save_interval=3000):
        """
        Initialize SmartHome system with database backend or JSON fallback
        
        Args:
            config_file: Configuration file for JSON mode (default: smart_home_config.json)
            save_interval: Auto-save interval in seconds (kept for compatibility)
        """
        self.config_file = config_file or 'smart_home_config.json'
        self.save_interval = save_interval
        self.last_save_time = datetime.now()
        self.json_fallback = None
        self.db = None
        
        # Thread safety
        self._save_lock = threading.Lock()
        self._save_in_progress = False
        
        # Try to initialize database manager
        try:
            self.db = SmartHomeDatabaseManager()
            # Check if database manager itself is in JSON fallback mode
            if hasattr(self.db, 'json_fallback_mode') and self.db.json_fallback_mode:
                print("✓ Database manager activated JSON fallback mode")
                self.json_fallback = self.db.json_backup
                self.db = None
            else:
                print("✓ PostgreSQL database connected successfully")
                # Initialize default settings only if using database
                self._initialize_default_settings()
        except (DatabaseError, Exception) as e:
            print(f"⚠ Failed to initialize database: {e}")
            print("⚠ Activating JSON backup fallback...")
            
            # Import and initialize JSON backup
            from utils.json_backup_manager import ensure_json_backup
            try:
                self.json_fallback = ensure_json_backup()
                self.db = None
                print("✓ JSON backup mode activated - system fully operational")
            except Exception as fallback_error:
                print(f"✗ Critical: JSON backup initialization failed: {fallback_error}")
                raise DatabaseError(
                    "Both PostgreSQL and JSON backup systems failed to initialize. "
                    "Cannot start application."
                )
        
        if self.db:
            print("SmartHome System initialized with PostgreSQL database backend")
        else:
            print("SmartHome System initialized with JSON backup backend")
    
    def _initialize_default_settings(self):
        """Initialize default system settings if they don't exist"""
        try:
            # Check if security_state exists, if not set default
            current_security_state = self.db.get_system_setting('security_state')
            if current_security_state is None:
                # Set default security state to "Wyłączony" (Disabled)
                self.db.set_security_state('Wyłączony')
                print("✓ Initialized default security state: Wyłączony")
            else:
                print(f"✓ Security state loaded from database: {current_security_state}")
        except Exception as e:
            # Gracefully handle missing system_settings table (multihouse migration)
            print(f"⚠ Warning: Legacy security state initialization failed (multihouse migration): {e}")
            print("ℹ Security state will be handled by multihouse system per-home")
    
    
    # ========================================================================
    # PROPERTY METHODS (for compatibility with existing code)
    # ========================================================================
    
    @property
    def users(self) -> Dict[str, Dict]:
        """Get users dict (compatibility property)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            return config.get('users', {})
        return self.db.get_users()
    
    @users.setter
    def users(self, value: Dict[str, Dict]):
        """Set users dict (for compatibility, but discouraged)"""
        print("Warning: Direct assignment to users property is discouraged")
        if self.json_fallback:
            config = self.json_fallback.get_config()
            config['users'] = value
            self.json_fallback.save_config(config)
    
    @property
    def rooms(self) -> List[str]:
        """Get rooms list (compatibility property)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            return config.get('rooms', [])
        return self.db.get_rooms()
    
    @rooms.setter
    def rooms(self, value: List[str]):
        """Set rooms list (for compatibility, but discouraged)"""
        print("Warning: Direct assignment to rooms property is discouraged")
        if self.json_fallback:
            config = self.json_fallback.get_config()
            config['rooms'] = value
            self.json_fallback.save_config(config)
    
    @property
    def buttons(self) -> List[Dict]:
        """Get buttons list (compatibility property)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            return config.get('buttons', [])
        return self.db.get_buttons()
    
    @buttons.setter
    def buttons(self, value: List[Dict]):
        """Set buttons list (for compatibility, but discouraged)"""
        print("Warning: Direct assignment to buttons property is discouraged")
        if self.json_fallback:
            config = self.json_fallback.get_config()
            config['buttons'] = value
            self.json_fallback.save_config(config)
    
    @property
    def temperature_controls(self) -> List[Dict]:
        """Get temperature controls list (compatibility property)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            return config.get('temperature_controls', [])
        return self.db.get_temperature_controls()
    
    @temperature_controls.setter
    def temperature_controls(self, value: List[Dict]):
        """Set temperature controls list (for compatibility, but discouraged)"""
        print("Warning: Direct assignment to temperature_controls property is discouraged")
        if self.json_fallback:
            config = self.json_fallback.get_config()
            config['temperature_controls'] = value
            self.json_fallback.save_config(config)
    
    @property
    def automations(self) -> List[Dict]:
        """Get automations list (compatibility property)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            return config.get('automations', [])
        return self.db.get_automations()
    
    @automations.setter
    def automations(self, value: List[Dict]):
        """Set automations list (for compatibility, but discouraged)"""
        print("Warning: Direct assignment to automations property is discouraged")
        if self.json_fallback:
            config = self.json_fallback.get_config()
            config['automations'] = value
            self.json_fallback.save_config(config)
    
    @property
    def temperature_states(self) -> Dict[str, float]:
        """Get temperature states dict (compatibility property)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            return config.get('temperature_states', {})
        return self.db.get_temperature_states()
    
    @temperature_states.setter
    def temperature_states(self, value: Dict[str, float]):
        """Set temperature states dict (for compatibility, but discouraged)"""
        print("Warning: Direct assignment to temperature_states property is discouraged")
        if self.json_fallback:
            config = self.json_fallback.get_config()
            config['temperature_states'] = value
            self.json_fallback.save_config(config)
    
    @property
    def security_state(self) -> str:
        """Get security state (compatibility property)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            return config.get('security_state', 'Wyłączony')
        try:
            return self.db.get_security_state()
        except Exception:
            # Fallback for multihouse migration - return default
            return "Wyłączony"
    
    @security_state.setter
    def security_state(self, value: str):
        """Set security state (compatibility property)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            config['security_state'] = value
            self.json_fallback.save_config(config)
        else:
            try:
                self.db.set_security_state(value)
            except Exception as e:
                # Gracefully handle system_settings table not existing
                print(f"⚠ Warning: Could not set security state (multihouse migration): {e}")
    
    # ========================================================================
    # USER MANAGEMENT METHODS (compatible with original interface)
    # ========================================================================
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID (compatible method)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            users = config.get('users', {})
            for username, user_data in users.items():
                if user_data.get('id') == user_id or user_data.get('user_id') == user_id:
                    return user_data
            return None
        return self.db.get_user_by_id(user_id)
    
    def get_user_data(self, user_id: str) -> Dict:
        """Get user data without password (compatible method)"""
        if self.json_fallback:
            user = self.get_user_by_id(user_id)
            if user:
                return {
                    'user_id': user.get('id') or user.get('user_id'),
                    'name': user.get('name', ''),
                    'email': user.get('email', ''),
                    'role': user.get('role', 'user'),
                    'profile_picture': user.get('profile_picture', '')
                }
            return {
                'user_id': user_id,
                'name': user_id,
                'email': '',
                'role': 'user',
                'profile_picture': ''
            }
        
        user = self.db.get_user_by_id(user_id)
        if user:
            return {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'profile_picture': user['profile_picture']
            }
        
        return {
            'user_id': user_id,
            'name': user_id,
            'email': '',
            'role': 'user',
            'profile_picture': ''
        }
    
    def get_user_by_login(self, login: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Get user by login name (compatible method)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            users = config.get('users', {})
            if login in users:
                user_data = users[login]
                user_id = user_data.get('id') or user_data.get('user_id')
                return (user_id, user_data)
            return (None, None)
        return self.db.get_user_by_login(login)
    
    def verify_password(self, user_id: str, password: str) -> bool:
        """Verify user password (compatible method)"""
        if self.json_fallback:
            user = self.get_user_by_id(user_id)
            if user:
                return check_password_hash(user['password'], password)
            return False
        
        user = self.db.get_user_by_id(user_id)
        if user:
            return check_password_hash(user['password'], password)
        return False
    
    def add_user(self, username: str, password: str, role: str = 'user', email: str = '') -> str:
        """Add new user (compatible method)"""
        hashed_password = generate_password_hash(password)
        
        if self.json_fallback:
            config = self.json_fallback.get_config()
            users = config.get('users', {})
            
            # Check if user already exists
            if username in users:
                return None
            
            user_id = str(uuid.uuid4())
            users[username] = {
                'id': user_id,
                'user_id': user_id,
                'username': username,
                'password': hashed_password,
                'role': role,
                'name': username,
                'email': email,
                'profile_picture': '',
                'created_at': datetime.now().isoformat()
            }
            
            config['users'] = users
            self.json_fallback.save_config(config)
            return user_id
        
        return self.db.add_user(username, hashed_password, role, email)
    
    def update_user_profile(self, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update user profile (compatible method)"""
        # Hash password if it's being updated
        if 'password' in updates:
            updates['password'] = generate_password_hash(updates['password'])
        
        if self.json_fallback:
            config = self.json_fallback.get_config()
            users = config.get('users', {})
            
            # Find user by ID
            for username, user_data in users.items():
                if user_data.get('id') == user_id or user_data.get('user_id') == user_id:
                    # Update user data
                    for key, value in updates.items():
                        user_data[key] = value
                    
                    config['users'] = users
                    success = self.json_fallback.save_config(config)
                    return (success, "Profile updated successfully" if success else "Failed to update profile")
            
            return (False, "User not found")
        
        return self.db.update_user_profile(user_id, updates)
    
    def change_password(self, user_id: str, new_password: str) -> Tuple[bool, str]:
        """Change user password (compatible method)"""
        hashed_password = generate_password_hash(new_password)
        return self.update_user_profile(user_id, {'password': hashed_password})
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user (compatible method)"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            users = config.get('users', {})
            
            # Find and delete user by ID
            for username, user_data in list(users.items()):
                if user_data.get('id') == user_id or user_data.get('user_id') == user_id:
                    del users[username]
                    config['users'] = users
                    return self.json_fallback.save_config(config)
            
            return False
        
        return self.db.delete_user(user_id)
    
    # ========================================================================
    # ROOM MANAGEMENT METHODS
    # ========================================================================
    
    def add_room(self, room_name: str) -> str:
        """Add new room"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            rooms = config.get('rooms', [])
            if room_name not in rooms:
                rooms.append(room_name)
                config['rooms'] = rooms
                self.json_fallback.save_config(config)
            return room_name
        return self.db.add_room(room_name)
    
    def update_room(self, old_name: str, new_name: str) -> bool:
        """Update room name"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            rooms = config.get('rooms', [])
            if old_name in rooms:
                rooms[rooms.index(old_name)] = new_name
                # Update room names in devices
                for button in config.get('buttons', []):
                    if button.get('room') == old_name:
                        button['room'] = new_name
                for control in config.get('temperature_controls', []):
                    if control.get('room') == old_name:
                        control['room'] = new_name
                config['rooms'] = rooms
                return self.json_fallback.save_config(config)
            return False
        return self.db.update_room(old_name, new_name)
    
    def delete_room(self, room_name: str) -> bool:
        """Delete room"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            rooms = config.get('rooms', [])
            if room_name in rooms:
                rooms.remove(room_name)
                # Remove devices in this room
                config['buttons'] = [b for b in config.get('buttons', []) if b.get('room') != room_name]
                config['temperature_controls'] = [t for t in config.get('temperature_controls', []) if t.get('room') != room_name]
                config['rooms'] = rooms
                return self.json_fallback.save_config(config)
            return False
        return self.db.delete_room(room_name)

    def reorder_rooms(self, room_names: List[str]) -> bool:
        """Reorder rooms based on provided list of room names"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            config['rooms'] = room_names
            return self.json_fallback.save_config(config)
        try:
            return self.db.reorder_rooms(room_names)
        except Exception as e:
            print(f"Failed to reorder rooms: {e}")
            return False
    
    # ========================================================================
    # DEVICE MANAGEMENT METHODS
    # ========================================================================
    
    def add_button(self, name: str, room_name: str, state: bool = False) -> str:
        """Add new button device"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            buttons = config.get('buttons', [])
            device_id = str(uuid.uuid4())
            buttons.append({
                'id': device_id,
                'name': name,
                'room': room_name,
                'state': state
            })
            config['buttons'] = buttons
            self.json_fallback.save_config(config)
            return device_id
        result = self.db.add_button(name, room_name, state)
        return result or ""
    
    def add_temperature_control(self, name: str, room_name: str, temperature: float = 22.0) -> str:
        """Add new temperature control device"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            controls = config.get('temperature_controls', [])
            device_id = str(uuid.uuid4())
            controls.append({
                'id': device_id,
                'name': name,
                'room': room_name,
                'temperature': temperature,
                'enabled': True
            })
            config['temperature_controls'] = controls
            self.json_fallback.save_config(config)
            return device_id
        result = self.db.add_temperature_control(name, room_name, temperature)
        return result or ""
    
    def update_device(self, device_id: str, updates: Dict) -> bool:
        """Update device properties"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            # Update button
            for button in config.get('buttons', []):
                if button.get('id') == device_id:
                    for key, value in updates.items():
                        button[key] = value
                    return self.json_fallback.save_config(config)
            # Update temperature control
            for control in config.get('temperature_controls', []):
                if control.get('id') == device_id:
                    for key, value in updates.items():
                        control[key] = value
                    return self.json_fallback.save_config(config)
            return False
        return self.db.update_device(device_id, updates)
    
    def delete_device(self, device_id: str) -> bool:
        """Delete device"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            # Delete from buttons
            original_len = len(config.get('buttons', []))
            config['buttons'] = [b for b in config.get('buttons', []) if b.get('id') != device_id]
            if len(config['buttons']) < original_len:
                return self.json_fallback.save_config(config)
            # Delete from temperature controls
            original_len = len(config.get('temperature_controls', []))
            config['temperature_controls'] = [t for t in config.get('temperature_controls', []) if t.get('id') != device_id]
            if len(config['temperature_controls']) < original_len:
                return self.json_fallback.save_config(config)
            return False
        return self.db.delete_device(device_id)
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict]:
        """Get device by ID"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            for button in config.get('buttons', []):
                if button.get('id') == device_id:
                    return button
            for control in config.get('temperature_controls', []):
                if control.get('id') == device_id:
                    return control
            return None
        return self.db.get_device_by_id(device_id)
    
    # ========================================================================
    # AUTOMATION METHODS
    # ========================================================================
    
    def add_automation(self, name: str, trigger: Dict, actions: List[Dict], enabled: bool = True) -> str:
        """Add new automation"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            automations = config.get('automations', [])
            automations.append({
                'name': name,
                'trigger': trigger,
                'actions': actions,
                'enabled': enabled
            })
            config['automations'] = automations
            self.json_fallback.save_config(config)
            return name
        return self.db.add_automation(name, trigger, actions, enabled)
    
    def update_automation(self, automation_name: str, updates: Dict) -> bool:
        """Update automation"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            automations = config.get('automations', [])
            for auto in automations:
                if auto.get('name') == automation_name:
                    for key, value in updates.items():
                        auto[key] = value
                    config['automations'] = automations
                    return self.json_fallback.save_config(config)
            return False
        return self.db.update_automation(automation_name, updates)
    
    def delete_automation(self, automation_name: str) -> bool:
        """Delete automation"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            automations = config.get('automations', [])
            original_len = len(automations)
            config['automations'] = [a for a in automations if a.get('name') != automation_name]
            if len(config['automations']) < original_len:
                return self.json_fallback.save_config(config)
            return False
        return self.db.delete_automation(automation_name)
    
    # ========================================================================
    # TEMPERATURE MANAGEMENT METHODS
    # ========================================================================
    
    def set_room_temperature(self, room_name: str, temperature: float) -> bool:
        """Set room temperature"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            temp_states = config.get('temperature_states', {})
            temp_states[room_name] = temperature
            config['temperature_states'] = temp_states
            return self.json_fallback.save_config(config)
        return self.db.set_room_temperature(room_name, temperature)
    
    # ========================================================================
    # SYSTEM SETTINGS METHODS
    # ========================================================================
    
    def get_system_setting(self, key: str) -> Any:
        """Get system setting"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            return config.get(key)
        return self.db.get_system_setting(key)
    
    def set_system_setting(self, key: str, value: Any, description: Optional[str] = None) -> bool:
        """Set system setting"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            config[key] = value
            return self.json_fallback.save_config(config)
        return self.db.set_system_setting(key, value, description)
    
    # ========================================================================
    # LOGGING METHODS
    # ========================================================================
    
    def add_management_log(self, level: str, message: str, event_type: Optional[str] = None,
                          user_id: Optional[str] = None, username: Optional[str] = None,
                          ip_address: Optional[str] = None, details: Optional[Dict] = None) -> str:
        """Add management log entry"""
        if self.json_fallback:
            # In JSON mode, we can't store logs persistently, just return empty string
            # This is acceptable for fallback mode
            print(f"[LOG] {level}: {message} (user: {username}, type: {event_type})")
            return ""
        result = self.db.add_management_log(level, message, event_type, user_id, username, ip_address, details)
        return result or ""
    
    def get_management_logs(self, limit: int = 100, level: Optional[str] = None, event_type: Optional[str] = None) -> List[Dict]:
        """Get management logs"""
        if self.json_fallback:
            # In JSON mode, no logs are stored
            return []
        return self.db.get_management_logs(limit, level, event_type)
    
    def clear_management_logs(self) -> bool:
        """Clear all management logs"""
        if self.json_fallback:
            # No logs to clear in JSON mode
            return True
        return self.db.clear_management_logs()
    
    # ========================================================================
    # COMPATIBILITY METHODS
    # ========================================================================
    
    def load_config(self):
        """Load configuration (compatibility method - no-op in database mode)"""
        # In database mode, data is loaded on demand
        pass
    
    def save_config(self) -> bool:
        """Save configuration (compatibility method - no-op in database mode)"""
        # In database mode, all changes are immediately persisted
        self.last_save_time = datetime.now()
        return True
    
    def check_and_save(self):
        """Check and save configuration (compatibility method)"""
        # In database mode, this is automatic
        self.last_save_time = datetime.now()
    # ========================================================================
    # WEATHER AND EXTERNAL DATA METHODS
    # ========================================================================
    
    def fetch_weather_data(self, home_id: Optional[str] = None):
        """
        Fetch weather data for a specific home location
        
        Args:
            home_id: UUID of the home to fetch weather for. If None, uses legacy IMGW fallback.
            
        Returns:
            Dictionary with weather data or None if failed
        """
        import logging
        from flask import current_app
        logger = logging.getLogger(__name__)
        
        # If no home_id provided, use legacy IMGW fallback
        if not home_id:
            logger.info("No home_id provided, using IMGW fallback (Kraków)")
            return WeatherService.get_weather_imgw_fallback()
        
        # Get multi_db from Flask app config
        multi_db = None
        try:
            multi_db = current_app.config.get('MULTI_DB_MANAGER')
        except RuntimeError:
            # No app context - try to get from self if available
            logger.warning("No Flask app context, cannot access multi_db")
        
        if not multi_db:
            logger.warning("Multi-home database not available, using IMGW fallback")
            return WeatherService.get_weather_imgw_fallback()
        
        try:
            with multi_db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        id, name, city, country, country_code,
                        latitude, longitude, address
                    FROM homes
                    WHERE id = %s
                """, (home_id,))
                
                result = cursor.fetchone()
                
                if not result:
                    logger.warning(f"Home {home_id} not found in database, using IMGW fallback")
                    return WeatherService.get_weather_imgw_fallback()
                
                # Build home_data dict from query result
                home_data = {
                    'id': result[0],
                    'name': result[1],
                    'city': result[2],
                    'country': result[3],
                    'country_code': result[4],
                    'latitude': float(result[5]) if result[5] is not None else None,
                    'longitude': float(result[6]) if result[6] is not None else None,
                    'address': result[7]
                }
                
                logger.info(f"Fetching weather for home: {home_data.get('name', 'Unknown')} "
                           f"in {home_data.get('city', 'Unknown')} "
                           f"({home_data.get('latitude')}, {home_data.get('longitude')})")
                
                # Use the new weather service to get weather for the home
                return WeatherService.get_weather_for_home(home_data, multi_db)
                
        except Exception as e:
            logger.error(f"Error fetching home data for weather: {e}")
            import traceback
            traceback.print_exc()
            return WeatherService.get_weather_imgw_fallback()
    
    # ========================================================================
    # MIGRATION HELPER METHODS
    # ========================================================================
    
    @staticmethod
    def is_uuid(val):
        """Check if value is a valid UUID (unchanged from original)"""
        try:
            uuid.UUID(str(val))
            return True
        except Exception:
            return False
    
    def migrate_users_to_uuid(self):
        """
        Migration method (kept for compatibility but not needed in database mode)
        In database mode, UUIDs are used from the start
        """
        print("UUID migration not needed in database mode - UUIDs are used by default")
        pass
    
    def export_to_json(self) -> Dict:
        """Export all data to JSON format for backup"""
        if self.json_fallback:
            # Already in JSON format
            return self.json_fallback.get_config()
        return self.db.export_to_json_format()
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        if self.json_fallback:
            config = self.json_fallback.get_config()
            return {
                'mode': 'JSON Backup',
                'users': len(config.get('users', {})),
                'rooms': len(config.get('rooms', [])),
                'buttons': len(config.get('buttons', [])),
                'temperature_controls': len(config.get('temperature_controls', [])),
                'automations': len(config.get('automations', []))
            }
        return self.db.get_stats()
    
    # ========================================================================
    # DEVICE STATE HELPERS (for compatibility with existing routes)
    # ========================================================================
    
    def find_button_by_room_and_name(self, room: str, name: str) -> Optional[Dict]:
        """Find button by room and name"""
        room_norm = (room or '').casefold()
        name_norm = (name or '').casefold()
        for button in self.buttons:
            if (button.get('room') or '').casefold() == room_norm and (button.get('name') or '').casefold() == name_norm:
                return button
        # Fallback: try match only by name if unique
        matches = [b for b in self.buttons if (b.get('name') or '').casefold() == name_norm]
        if len(matches) == 1:
            print(f"[DEBUG] find_button_by_room_and_name fallback matched by name only (room mismatch input='{room}')")
            return matches[0]
        return None
    
    def find_temperature_control_by_room_and_name(self, room: str, name: str) -> Optional[Dict]:
        """Find temperature control by room and name"""
        room_norm = (room or '').casefold()
        name_norm = (name or '').casefold()
        for control in self.temperature_controls:
            if (control.get('room') or '').casefold() == room_norm and (control.get('name') or '').casefold() == name_norm:
                return control
        matches = [c for c in self.temperature_controls if (c.get('name') or '').casefold() == name_norm]
        if len(matches) == 1:
            print(f"[DEBUG] find_temperature_control_by_room_and_name fallback matched by name only (room mismatch input='{room}')")
            return matches[0]
        return None
    
    def update_button_state(self, room: str, name: str, state: bool) -> bool:
        """Update button state by room and name"""
        button = self.find_button_by_room_and_name(room, name)
        if button:
            return self.update_device(button['id'], {'state': state})
        return False
    
    def update_temperature_control_value(self, room: str, name: str, temperature: float) -> bool:
        """Update temperature control value by room and name"""
        print(f"[DEBUG] Updating temperature control: room='{room}', name='{name}', temperature={temperature}")
        control = self.find_temperature_control_by_room_and_name(room, name)
        print(f"[DEBUG] Found control: {control}")
        if control:
            result = self.update_device(control['id'], {'temperature': temperature})
            print(f"[DEBUG] Update result: {result}")
            return result
        # Fallback: jeśli brak room (lub None) spróbuj znaleźć unikalnie po nazwie
        if not room:
            print(f"[DEBUG] Fallback search by name only for temperature control: '{name}' (room missing)")
            matches = [c for c in self.temperature_controls if c.get('name') == name]
            if len(matches) == 1:
                ctrl = matches[0]
                print(f"[DEBUG] Fallback matched control id={ctrl.get('id')} in room={ctrl.get('room')}")
                result = self.update_device(ctrl['id'], {'temperature': temperature})
                print(f"[DEBUG] Fallback update result: {result}")
                return result
            elif len(matches) > 1:
                print(f"[DEBUG] Fallback ambiguous: {len(matches)} controls share name '{name}' – aborting update")
            else:
                print(f"[DEBUG] Fallback found no controls with name '{name}'")
        print(f"[DEBUG] No control found for room='{room}', name='{name}'")
        return False
    
    def toggle_temperature_control_enabled(self, room: str, name: str, enabled: bool) -> bool:
        """Toggle temperature control enabled/disabled state by room and name"""
        print(f"[DEBUG] Toggling temperature control enabled: room='{room}', name='{name}', enabled={enabled}")
        control = self.find_temperature_control_by_room_and_name(room, name)
        print(f"[DEBUG] Found control: {control}")
        if control:
            result = self.update_device(control['id'], {'enabled': enabled})
            print(f"[DEBUG] Update enabled result: {result}")
            return result
        # Fallback: jeśli brak room (lub None) spróbuj znaleźć unikalnie po nazwie
        if not room:
            print(f"[DEBUG] Fallback search by name only for temperature control enabled: '{name}' (room missing)")
            matches = [c for c in self.temperature_controls if c.get('name') == name]
            if len(matches) == 1:
                ctrl = matches[0]
                print(f"[DEBUG] Fallback matched control id={ctrl.get('id')} in room={ctrl.get('room')}")
                result = self.update_device(ctrl['id'], {'enabled': enabled})
                print(f"[DEBUG] Fallback enabled update result: {result}")
                return result
            elif len(matches) > 1:
                print(f"[DEBUG] Fallback ambiguous: {len(matches)} controls share name '{name}' – aborting enabled update")
            else:
                print(f"[DEBUG] Fallback found no controls with name '{name}'")
        print(f"[DEBUG] No control found for enabled update: room='{room}', name='{name}'")
        return False
    
    # ========================================================================
    # AUTOMATION COMPATIBILITY HELPERS
    # ========================================================================
    
    def add_automation_by_index(self, automation: Dict) -> bool:
        """Add automation (compatibility method for routes that expect list-based operations)"""
        try:
            name = automation.get('name', f'Automation_{uuid.uuid4().hex[:8]}')
            trigger = automation.get('trigger', {})
            actions = automation.get('actions', [])
            enabled = automation.get('enabled', True)
            
            self.add_automation(name, trigger, actions, enabled)
            return True
        except Exception as e:
            print(f"Failed to add automation: {e}")
            return False
    
    def update_automation_by_index(self, index: int, automation: Dict) -> bool:
        """Update automation by index (compatibility method)"""
        try:
            automations = self.automations
            if 0 <= index < len(automations):
                old_name = automations[index]['name']
                return self.update_automation(old_name, automation)
            return False
        except Exception as e:
            print(f"Failed to update automation at index {index}: {e}")
            return False
    
    def delete_automation_by_index(self, index: int) -> bool:
        """Delete automation by index (compatibility method)"""
        try:
            automations = self.automations
            if 0 <= index < len(automations):
                automation_name = automations[index]['name']
                return self.delete_automation(automation_name)
            return False
        except Exception as e:
            print(f"Failed to delete automation at index {index}: {e}")
            return False
