"""
PostgreSQL Database Manager for SmartHome System
===============================================

This module replaces the JSON-based storage system with PostgreSQL database operations.
It provides a complete interface for all SmartHome data operations.
"""

import psycopg2
import psycopg2.extras
import psycopg2.pool
import json
import uuid
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class SmartHomeDatabaseManager:
    """
    PostgreSQL Database Manager for SmartHome System
    
    This class provides all database operations to replace JSON file storage.
    It handles users, rooms, devices, automations, logs, and settings.
    """
    
    def __init__(self, db_config=None):
        """
        Initialize database manager with connection configuration
        
        Args:
            db_config (dict): Database connection configuration
        """
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST', '100.103.184.90'),
            'port': os.getenv('DB_PORT', '5432'),
            'dbname': os.getenv('DB_NAME', 'admin'),  # ensure 'dbname' not 'database'
            'user': os.getenv('DB_USER', 'admin'),
            'password': os.getenv('DB_PASSWORD', 'Qwuizzy123.')
            
        }
        
        self.home_id = os.getenv('HOME_ID', str(uuid.uuid4()))
        self._connection_pool = None
        self._lock = threading.Lock()
        self._pool_minconn = int(os.getenv('DB_POOL_MIN', '2'))  # Minimum connections
        self._pool_maxconn = int(os.getenv('DB_POOL_MAX', '10'))  # Maximum connections
        
        # Initialize connection pool
        self._initialize_connection_pool()
        
        # Test connection on initialization
        self._test_connection()
    
    def _initialize_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            # Only allow valid psycopg2 keys for connection
            allowed_keys = {'host', 'port', 'dbname', 'user', 'password', 'connect_timeout'}
            filtered_config = {}
            for k, v in self.db_config.items():
                if k in allowed_keys:
                    if k == 'port':
                        try:
                            filtered_config[k] = int(v)
                        except Exception:
                            filtered_config[k] = v
                    else:
                        filtered_config[k] = str(v)
            
            # Add connection timeout if not specified
            if 'connect_timeout' not in filtered_config:
                filtered_config['connect_timeout'] = 5  # 5 second timeout
            
            # Create connection pool
            self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self._pool_minconn,
                maxconn=self._pool_maxconn,
                **filtered_config
            )
            logger.info(f"✓ Connection pool initialized with {self._pool_minconn}-{self._pool_maxconn} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            # Fall back to single connection mode
            self._connection_pool = None
            logger.warning("⚠ Falling back to single connection mode")
    
    def _test_connection(self):
        """Test database connection"""
        try:
            conn = self._get_connection()
            conn.close()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise DatabaseError(f"Cannot connect to database: {e}")
    
    def _get_connection(self):
        """Get database connection from pool or create new one"""
        try:
            if self._connection_pool:
                # Use connection pool if available
                with self._lock:
                    conn = self._connection_pool.getconn()
                    if conn:
                        # Reset connection state
                        conn.rollback()
                        return conn
                    else:
                        logger.warning("No connection available from pool")
            
            # Fallback to direct connection if pool not available
            logger.debug("Using direct connection (pool not available)")
            # Only allow valid psycopg2 keys
            allowed_keys = {'host', 'port', 'dbname', 'user', 'password', 'connect_timeout'}
            filtered_config = {}
            for k, v in self.db_config.items():
                if k in allowed_keys:
                    if k == 'port':
                        try:
                            filtered_config[k] = int(v)
                        except Exception:
                            filtered_config[k] = v
                    else:
                        filtered_config[k] = str(v)
            
            # Add connection timeout if not specified
            if 'connect_timeout' not in filtered_config:
                filtered_config['connect_timeout'] = 5  # 5 second timeout
                
            return psycopg2.connect(**filtered_config)
        except Exception as e:
            logger.error(f"Failed to get database connection: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
    
    def _return_connection(self, conn):
        """Return connection to pool or close if not using pool"""
        try:
            if self._connection_pool and conn:
                with self._lock:
                    self._connection_pool.putconn(conn)
            elif conn:
                conn.close()
        except Exception as e:
            logger.error(f"Error returning connection: {e}")
            # If returning to pool fails, close the connection
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    from typing import Optional

    def _execute_query(self, query: str, params: Optional[tuple] = None, fetch: Optional[str] = None):
        """
        Execute database query with error handling
        
        Args:
            query (str): SQL query
            params (tuple): Query parameters
            fetch (str): 'one', 'all', or None
            
        Returns:
            Query result or None
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if params is not None:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                if fetch == 'one':
                    result = cur.fetchone()
                    return dict(result) if result else None
                elif fetch == 'all':
                    results = cur.fetchall()
                    return [dict(row) for row in results] if results else []
                else:
                    # For INSERT/UPDATE/DELETE operations
                    conn.commit()
                    return cur.rowcount
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database query failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise DatabaseError(f"Query execution failed: {e}")
        finally:
            if conn:
                self._return_connection(conn)
    
    def close_pool(self):
        """Close connection pool and all connections"""
        try:
            if self._connection_pool:
                with self._lock:
                    self._connection_pool.closeall()
                    logger.info("✓ Connection pool closed")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")
    
    def get_pool_status(self):
        """Get connection pool status for monitoring"""
        if not self._connection_pool:
            return {"pool_enabled": False}
        
        try:
            # Note: psycopg2 connection pool doesn't provide detailed stats
            # This is a basic status check
            return {
                "pool_enabled": True,
                "min_connections": self._pool_minconn,
                "max_connections": self._pool_maxconn,
                "pool_type": "ThreadedConnectionPool"
            }
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {"pool_enabled": True, "error": str(e)}
    
    # ========================================================================
    # USER MANAGEMENT METHODS
    # ========================================================================
    
    def get_users(self) -> Dict[str, Dict]:
        """Get all users in the format expected by the original system"""
        query = """
            SELECT id, name, email, password_hash, role, profile_picture, created_at, updated_at
            FROM users
            ORDER BY created_at
        """
        
        print(f"[DEBUG] get_users() - executing query: {query}")
        users = self._execute_query(query, fetch='all')
        print(f"[DEBUG] get_users() - got {len(users) if users else 0} users from database")
        
        # Convert to original format (id as key)
        result = {}
        if users:
            for user in users:
                print(f"[DEBUG] Processing user: {user['id']} - {user['name']}")
                result[user['id']] = {
                    'name': user['name'],
                    'email': user['email'],
                    'password': user['password_hash'],
                    'role': user['role'],
                    'profile_picture': user['profile_picture']
                }
        
        print(f"[DEBUG] get_users() - returning {len(result)} users: {list(result.keys())}")
        return result
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        query = """
            SELECT id, name, email, password_hash, role, profile_picture
            FROM users 
            WHERE id = %s
        """
        
        user = self._execute_query(query, (user_id,), fetch='one')
        
        if user and isinstance(user, dict):
            return {
                'user_id': user.get('id'),
                'name': user.get('name'),
                'email': user.get('email'),
                'password': user.get('password_hash'),
                'role': user.get('role'),
                'profile_picture': user.get('profile_picture')
            }
        return None
    
    def get_user_by_login(self, login: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Get user by login name (returns user_id and user_dict)"""
        query = """
            SELECT id, name, email, password_hash, role, profile_picture
            FROM users 
            WHERE name = %s
        """
        
        user = self._execute_query(query, (login,), fetch='one')
        
        if user and isinstance(user, dict):
            user_dict = {
                'name': user.get('name'),
                'email': user.get('email'),
                'password': user.get('password_hash'),
                'role': user.get('role'),
                'profile_picture': user.get('profile_picture')
            }
            return user.get('id'), user_dict
        return None, None
    
    def add_user(self, username: str, password: str, role: str = 'user', email: str = '') -> str:
        """Add new user and return user ID"""
        user_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO users (id, name, email, password_hash, role)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        self._execute_query(query, (user_id, username, email, password, role))
        return user_id
    
    def update_user_profile(self, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update user profile"""
        try:
            # Build dynamic UPDATE query
            set_clauses = []
            params = []
            for key, value in updates.items():
                if key in ['name', 'email', 'password', 'role', 'profile_picture']:
                    # Map 'password' to 'password_hash'
                    db_key = 'password_hash' if key == 'password' else key
                    set_clauses.append(f"{db_key} = %s")
                    params.append(value)
            if not set_clauses:
                return False, "No valid fields to update"
            set_clauses.append("updated_at = NOW()")
            params.append(user_id)
            query = f"""
                UPDATE users 
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """
            rows_affected = self._execute_query(query, tuple(params))
            if isinstance(rows_affected, int) and rows_affected > 0:
                return True, "Profile updated successfully"
            else:
                return False, "User not found"
        except Exception as e:
            return False, f"Update failed: {str(e)}"
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        query = "DELETE FROM users WHERE id = %s"
        rows_affected = self._execute_query(query, (user_id,))
        return isinstance(rows_affected, int) and rows_affected > 0
    
    def verify_password(self, user_id: str, password: str) -> bool:
        """Verify user password using proper password hash checking"""
        from werkzeug.security import check_password_hash
        
        user = self.get_user_by_id(user_id)
        pw_hash = user.get('password') if user and isinstance(user, dict) else None
        if pw_hash and isinstance(pw_hash, str):
            return check_password_hash(pw_hash, password)
        return False
    
    # ========================================================================
    # ROOM MANAGEMENT METHODS
    # ========================================================================
    
    def get_rooms(self) -> List[str]:
        """Get all rooms as a list of names (original format)"""
        query = """
            SELECT name 
            FROM rooms 
            ORDER BY display_order, name
        """
        
        rooms = self._execute_query(query, fetch='all')
        return [str(room.get('name')) for room in (rooms or []) if isinstance(room, dict) and 'name' in room and room.get('name') is not None]
    
    def get_rooms_with_ids(self) -> List[Dict]:
        """Get all rooms with IDs"""
        query = """
            SELECT id, name, display_order, created_at, updated_at
            FROM rooms 
            ORDER BY display_order, name
        """
        
        result = self._execute_query(query, fetch='all')
        return result if isinstance(result, list) else []
    
    def add_room(self, room_name: str) -> str:
        """Add new room and return room ID"""
        room_id = str(uuid.uuid4())
        
        # Get next display order
        query_order = "SELECT COALESCE(MAX(display_order), 0) + 1 AS next_order FROM rooms"
        next_order = self._execute_query(query_order, fetch='one')
        order_value = next_order.get('next_order') if next_order and isinstance(next_order, dict) else 0
        query = """
            INSERT INTO rooms (id, name, display_order)
            VALUES (%s, %s, %s)
        """
        self._execute_query(query, (room_id, room_name, order_value))
        return room_id
    
    def update_room(self, old_name: str, new_name: str) -> bool:
        """Update room name"""
        query = """
            UPDATE rooms 
            SET name = %s, updated_at = NOW()
            WHERE name = %s
        """
        
        rows_affected = self._execute_query(query, (old_name, new_name))
        return isinstance(rows_affected, int) and rows_affected > 0
    
    def delete_room(self, room_name: str) -> bool:
        """Delete room and all associated devices"""
        query = """
            DELETE FROM rooms 
            WHERE name = %s
        """
        
        rows_affected = self._execute_query(query, (room_name,))
        return isinstance(rows_affected, int) and rows_affected > 0
    
    def reorder_rooms(self, room_names: List[str]) -> bool:
        """Reorder rooms based on provided list"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                for i, room_name in enumerate(room_names):
                    cur.execute("""
                        UPDATE rooms 
                        SET display_order = %s, updated_at = NOW()
                        WHERE name = %s
                    """, (i, room_name))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to reorder rooms: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    # ========================================================================
    # DEVICE MANAGEMENT METHODS (BUTTONS & TEMPERATURE CONTROLS)
    # ========================================================================
    
    def get_buttons(self) -> List[Dict]:
        """Get all button devices in original format"""
        query = """
            SELECT d.id, d.name, r.name as room, d.state, d.display_order
            FROM devices d
            JOIN rooms r ON d.room_id = r.id
            WHERE d.device_type = 'button'
            ORDER BY r.display_order, d.display_order, d.name
        """
        
        buttons = self._execute_query(query, fetch='all')
        
        # Convert to original format
        result = []
        for button in (buttons or []):
            if button and isinstance(button, dict):
                result.append({
                    'id': button.get('id'),
                    'name': button.get('name'),
                    'room': button.get('room'),
                    'state': button.get('state')
                })
        return result
    
    @property
    def buttons(self) -> List[Dict]:
        """Get all button devices as property (for compatibility)"""
        return self.get_buttons()
    
    def get_temperature_controls(self) -> List[Dict]:
        """Get all temperature control devices in original format"""
        query = """
            SELECT d.id, d.name, r.name as room, d.temperature, d.display_order
            FROM devices d
            JOIN rooms r ON d.room_id = r.id
            WHERE d.device_type = 'temperature_control'
            ORDER BY r.display_order, d.display_order, d.name
        """
        
        controls = self._execute_query(query, fetch='all')
        
        # Convert to original format
        result = []
        for control in (controls or []):
            if control and isinstance(control, dict):
                temp_val = control.get('temperature')
                try:
                    temp_float = float(temp_val) if temp_val is not None else None
                except (TypeError, ValueError):
                    temp_float = None
                result.append({
                    'id': control.get('id'),
                    'name': control.get('name'),
                    'room': control.get('room'),
                    'temperature': temp_float
                })
        
        return result
    
    @property
    def temperature_controls(self) -> List[Dict]:
        """Get all temperature control devices as property (for compatibility)"""
        return self.get_temperature_controls()
    
    def add_button(self, name: str, room_name: str, state: bool = False) -> Optional[str]:
        """Add new button device"""
        # Get room ID
        room_query = "SELECT id FROM rooms WHERE name = %s"
        room = self._execute_query(room_query, (room_name,), fetch='one')
        
        if not room or not isinstance(room, dict) or 'id' not in room:
            raise DatabaseError(f"Room '{room_name}' not found")
        
        device_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO devices (id, name, room_id, device_type, state)
            VALUES (%s, %s, %s, 'button', %s)
        """
        
        self._execute_query(query, (device_id, name, room.get('id'), state))
        return device_id
    
    def add_temperature_control(self, name: str, room_name: str, temperature: float = 22.0) -> Optional[str]:
        """Add new temperature control device"""
        # Get room ID
        room_query = "SELECT id FROM rooms WHERE name = %s"
        room = self._execute_query(room_query, (room_name,), fetch='one')
        
        if not room or not isinstance(room, dict) or 'id' not in room:
            raise DatabaseError(f"Room '{room_name}' not found")
        
        device_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO devices (id, name, room_id, device_type, temperature)
            VALUES (%s, %s, %s, 'temperature_control', %s)
        """
        
        self._execute_query(query, (device_id, name, room.get('id'), temperature))
        return device_id
    
    def update_device(self, device_id: str, updates: Dict) -> bool:
        """Update device properties"""
        try:
            print(f"[DEBUG] update_device called: device_id={device_id}, updates={updates}")
            
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if key in ['name', 'state', 'temperature', 'room']:
                    if key == 'room':
                        # Convert room name to room_id
                        room_query = "SELECT id FROM rooms WHERE name = %s"
                        room = self._execute_query(room_query, (value,), fetch='one')
                        if room and isinstance(room, dict) and 'id' in room:
                            set_clauses.append("room_id = %s")
                            params.append(room.get('id'))
                            print(f"[DEBUG] Room '{value}' converted to room_id: {room.get('id')}")
                        else:
                            print(f"[DEBUG] Room '{value}' not found")
                    else:
                        set_clauses.append(f"{key} = %s")
                        params.append(value)
                        print(f"[DEBUG] Added update: {key} = {value}")
            
            if not set_clauses:
                print(f"[DEBUG] No valid update fields found")
                return False
            
            set_clauses.append("updated_at = NOW()")
            params.append(device_id)
            
            query = f"""
                UPDATE devices 
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """
            
            print(f"[DEBUG] Executing query: {query}")
            print(f"[DEBUG] Query params: {params}")
            
            rows_affected = self._execute_query(query, tuple(params))
            print(f"[DEBUG] Rows affected: {rows_affected}")
            
            success = isinstance(rows_affected, int) and rows_affected > 0
            print(f"[DEBUG] Update success: {success}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update device {device_id}: {e}")
            print(f"[DEBUG] Exception in update_device: {e}")
            return False
    
    def delete_device(self, device_id: str) -> bool:
        """Delete device"""
        query = "DELETE FROM devices WHERE id = %s"
        rows_affected = self._execute_query(query, (device_id,))
        return isinstance(rows_affected, int) and rows_affected > 0
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict]:
        """Get device by ID"""
        query = """
            SELECT d.id, d.name, r.name as room, d.device_type, d.state, d.temperature
            FROM devices d
            JOIN rooms r ON d.room_id = r.id
            WHERE d.id = %s
        """
        
        device = self._execute_query(query, (device_id,), fetch='one')
        
        if device and isinstance(device, dict):
            result = {
                'id': device.get('id'),
                'name': device.get('name'),
                'room': device.get('room'),
                'device_type': device.get('device_type')
            }
            dtype = device.get('device_type')
            if dtype == 'button':
                result['state'] = device.get('state')
            elif dtype == 'temperature_control':
                temp_val = device.get('temperature')
                try:
                    temp_float = float(temp_val) if temp_val is not None else None
                except (TypeError, ValueError):
                    temp_float = None
                result['temperature'] = temp_float
            return result
        return None
    
    # ========================================================================
    # AUTOMATION MANAGEMENT METHODS
    # ========================================================================
    
    def get_automations(self) -> List[Dict]:
        """Get all automations in original format"""
        query = """
            SELECT id, name, trigger_config, actions_config, enabled, 
                   execution_count, last_executed, error_count
            FROM automations
            ORDER BY name
        """
        
        automations = self._execute_query(query, fetch='all')
        
        # Convert to original format
        result = []
        for auto in (automations or []):
            if auto and isinstance(auto, dict):
                trigger_cfg = auto.get('trigger_config')
                actions_cfg = auto.get('actions_config')
                last_executed = auto.get('last_executed')
                result.append({
                    'name': auto.get('name'),
                    'trigger': json.loads(trigger_cfg) if isinstance(trigger_cfg, str) else {},
                    'actions': json.loads(actions_cfg) if isinstance(actions_cfg, str) else [],
                    'enabled': auto.get('enabled'),
                    'execution_count': auto.get('execution_count') or 0,
                    'last_executed': last_executed.isoformat() if last_executed is not None and hasattr(last_executed, 'isoformat') else None,
                    'error_count': auto.get('error_count') or 0
                })
        return result
    
    def add_automation(self, name: str, trigger: Dict, actions: List[Dict], enabled: bool = True) -> str:
        """Add new automation"""
        automation_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO automations (id, name, trigger_config, actions_config, enabled)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        self._execute_query(query, (
            automation_id, 
            name, 
            json.dumps(trigger), 
            json.dumps(actions), 
            enabled
        ))
        
        return automation_id
    
    def update_automation(self, automation_name: str, updates: Dict) -> bool:
        """Update automation"""
        try:
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if key == 'trigger':
                    set_clauses.append("trigger_config = %s")
                    params.append(json.dumps(value))
                elif key == 'actions':
                    set_clauses.append("actions_config = %s")
                    params.append(json.dumps(value))
                elif key in ['name', 'enabled']:
                    set_clauses.append(f"{key} = %s")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = NOW()")
            params.append(automation_name)
            
            query = f"""
                UPDATE automations 
                SET {', '.join(set_clauses)}
                WHERE name = %s
            """
            
            rows_affected = self._execute_query(query, tuple(params))
            return isinstance(rows_affected, int) and rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update automation {automation_name}: {e}")
            return False
    
    def delete_automation(self, automation_name: str) -> bool:
        """Delete automation"""
        query = "DELETE FROM automations WHERE name = %s"
        rows_affected = self._execute_query(query, (automation_name,))
        return isinstance(rows_affected, int) and rows_affected > 0
    
    # ========================================================================
    # SYSTEM SETTINGS METHODS
    # ========================================================================
    
    def get_system_setting(self, key: str) -> Any:
        """Get system setting value"""
        query = """
            SELECT setting_value 
            FROM system_settings 
            WHERE setting_key = %s
        """
        
        result = self._execute_query(query, (key,), fetch='one')
        
        if result and isinstance(result, dict) and 'setting_value' in result:
            setting_val = result.get('setting_value')
            # Handle empty or null values
            if setting_val is None or setting_val == '':
                return None
            
            # Since setting_value is jsonb type, it should already be parsed by psycopg2
            # If it's still a string, try to parse it as JSON
            if isinstance(setting_val, str):
                try:
                    return json.loads(setting_val)
                except json.JSONDecodeError:
                    # If JSON parsing fails, return the string as-is
                    return setting_val
            else:
                # Already parsed as Python object (dict, list, bool, int, etc.)
                return setting_val
        return None
    
    def set_system_setting(self, key: str, value: Any, description: Optional[str] = None) -> bool:
        """Set system setting value"""
        query = """
            INSERT INTO system_settings (setting_key, setting_value, description)
            VALUES (%s, %s, %s)
            ON CONFLICT (setting_key) DO UPDATE SET
                setting_value = EXCLUDED.setting_value,
                description = COALESCE(EXCLUDED.description, system_settings.description),
                updated_at = NOW()
        """
        
        # Always store as valid JSON since setting_value is jsonb type
        store_value = json.dumps(value)
        
        rows_affected = self._execute_query(query, (key, store_value, description))
        return isinstance(rows_affected, int) and rows_affected > 0
    
    def get_security_state(self) -> str:
        """Get current security state"""
        # Get boolean value from database
        state_bool = self.get_system_setting('security_state')
        if state_bool is None:
            # If no state exists, set and return default (False = Wyłączony)
            self.set_security_state('Wyłączony')
            return 'Wyłączony'
        
        # Convert boolean to Polish text
        if isinstance(state_bool, bool):
            return 'Załączony' if state_bool else 'Wyłączony'
        elif isinstance(state_bool, str):
            # Handle existing string values for backward compatibility
            if state_bool.lower() in ['true', 'załączony', 'włączony']:
                return 'Załączony'
            else:
                return 'Wyłączony'
        else:
            return 'Wyłączony'
    
    def set_security_state(self, state: str) -> bool:
        """Set security state - convert Polish text to boolean"""
        # Convert Polish text to boolean
        state_bool = state in ['Załączony', 'Włączony', 'true', 'True']
        return self.set_system_setting('security_state', state_bool, 'Current security system state (boolean)')
    
    # ========================================================================
    # TEMPERATURE STATES METHODS
    # ========================================================================
    
    def get_temperature_states(self) -> Dict[str, float]:
        """Get all room temperature states in original format"""
        query = """
            SELECT r.name, rts.current_temperature
            FROM room_temperature_states rts
            JOIN rooms r ON rts.room_id = r.id
        """
        
        states = self._execute_query(query, fetch='all')
        
        # Convert to original format (room_name: temperature)
        result = {}
        for state in (states or []):
            if state and isinstance(state, dict) and 'name' in state and 'current_temperature' in state:
                temp_val = state.get('current_temperature')
                try:
                    temp = float(temp_val) if temp_val is not None and (isinstance(temp_val, (int, float, str)) and str(temp_val).replace('.','',1).isdigit()) else None
                except (TypeError, ValueError):
                    temp = None
                result[state.get('name')] = temp
        return result
    
    def set_room_temperature(self, room_name: str, temperature: float) -> bool:
        """Set room temperature"""
        # Get room ID
        room_query = "SELECT id FROM rooms WHERE name = %s"
        room = self._execute_query(room_query, (room_name,), fetch='one')
        room_id = None
        if isinstance(room, dict):
            room_id = room.get('id')
        elif isinstance(room, list) and room and isinstance(room[0], dict):
            room_id = room[0].get('id')
        if not room_id:
            return False
        query = """
            INSERT INTO room_temperature_states (room_id, current_temperature, target_temperature)
            VALUES (%s, %s, %s)
            ON CONFLICT (room_id) DO UPDATE SET
                current_temperature = EXCLUDED.current_temperature,
                target_temperature = EXCLUDED.target_temperature,
                last_updated = NOW()
        """
        rows_affected = self._execute_query(query, (room_id, temperature, temperature))
        return isinstance(rows_affected, int) and rows_affected > 0
    
    # ========================================================================
    # LOGGING METHODS
    # ========================================================================
    
    def add_management_log(self, level: str, message: str, event_type: Optional[str] = None, 
                          user_id: Optional[str] = None, username: Optional[str] = None, 
                          ip_address: Optional[str] = None, details: Optional[Dict] = None) -> str:
        """Add management log entry"""
        log_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO management_logs 
            (id, level, message, event_type, user_id, username, ip_address, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        self._execute_query(query, (
            log_id, level, message, event_type, user_id, username, 
            ip_address, json.dumps(details or {})
        ))
        
        return log_id
    
    def get_management_logs(self, limit: int = 100, level: Optional[str] = None, 
                           event_type: Optional[str] = None) -> List[Dict]:
        """Get management logs"""
        query = """
            SELECT id, timestamp, level, message, event_type, username, ip_address, details
            FROM management_logs
        """
        
        conditions = []
        params = []
        
        if level:
            conditions.append("level = %s")
            params.append(level)
        
        if event_type:
            conditions.append("event_type = %s")
            params.append(event_type)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        logs = self._execute_query(query, tuple(params), fetch='all')
        
        # Convert to original format
        result = []
        for log in (logs or []):
            if log and isinstance(log, dict):
                ts = log.get('timestamp')
                details_val = log.get('details')
                if isinstance(details_val, str) and details_val:
                    details_val_stripped = details_val.strip()
                    details = json.loads(details_val_stripped) if details_val_stripped.startswith('{') else {}
                elif isinstance(details_val, dict):
                    details = details_val
                else:
                    details = {}
                result.append({
                    'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S') if ts is not None and hasattr(ts, 'strftime') else None,
                    'level': log.get('level'),
                    'message': log.get('message'),
                    'event_type': log.get('event_type'),
                    'user': log.get('username'),
                    'ip_address': log.get('ip_address'),
                    'details': details
                })
        return result
    
    def clear_management_logs(self) -> bool:
        """Clear all management logs"""
        query = "DELETE FROM management_logs"
        rows_affected = self._execute_query(query)
        return isinstance(rows_affected, int) and rows_affected >= 0
    
    # ========================================================================
    # COMPATIBILITY METHODS (for existing SmartHomeSystem interface)
    # ========================================================================
    
    def save_config(self) -> bool:
        """
        Compatibility method - in database mode, this is automatic
        Returns True to maintain compatibility with existing code
        """
        # In database mode, all changes are immediately persisted
        # This method exists for compatibility with the existing SmartHomeSystem interface
        return True
    
    def load_config(self):
        """
        Compatibility method - in database mode, data is loaded on demand
        This method exists for compatibility with the existing SmartHomeSystem interface
        """
        # In database mode, data is loaded on demand from the database
        # This method exists for compatibility with the existing SmartHomeSystem interface
        pass
    
    # ========================================================================
    # MIGRATION HELPER METHODS
    # ========================================================================
    
    def export_to_json_format(self) -> Dict:
        """Export all data in original JSON format for backup purposes"""
        return {
            'users': self.get_users(),
            'rooms': self.get_rooms(),
            'buttons': self.get_buttons(),
            'temperature_controls': self.get_temperature_controls(),
            'automations': self.get_automations(),
            'temperature_states': self.get_temperature_states(),
            'security_state': self.get_security_state()
        }
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        tables = ['users', 'rooms', 'devices', 'automations', 'management_logs']
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            result = self._execute_query(query, fetch='one')
            stats[table] = result.get('count') if result and isinstance(result, dict) and 'count' in result else 0
        
        return stats
