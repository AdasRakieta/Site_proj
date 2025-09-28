import psycopg2
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class MultiHomeDBManager:
    """
    Database manager for multi-home smart home system.
    Handles all database operations with home context isolation.
    """
    
    def __init__(self, host: str = "localhost", port: int = 5432, 
                 user: str = "postgres", password: str = "", 
                 database: str = "smarthome_multihouse", 
                 connection_timeout: int = 10):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection_timeout = connection_timeout
        self._connection = None
        self._ensure_connection()

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor with automatic transaction handling."""
        cursor = None
        try:
            self._ensure_connection()
            if self._connection:
                cursor = self._connection.cursor()
                yield cursor
                self._connection.commit()
        except Exception as e:
            if self._connection:
                self._connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def _ensure_connection(self):
        """Ensure database connection is active."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    connect_timeout=self.connection_timeout
                )
                logger.info(f"Connected to database {self.database}")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise

    def close_connection(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")

    # ============================================================================
    # HOME MANAGEMENT
    # ============================================================================

    def create_home(self, name: str, owner_id: int, description: Optional[str] = None) -> int:
        """Create a new home and return its ID."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO homes (name, owner_id, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (name, owner_id, description, datetime.now(), datetime.now()))
            
            result = cursor.fetchone()
            if not result:
                raise Exception("Failed to create home")
            home_id = result[0]
            
            # Add owner to user_homes with admin role
            cursor.execute("""
                INSERT INTO user_homes (user_id, home_id, role, permissions, joined_at)
                VALUES (%s, %s, 'admin', %s, %s)
            """, (owner_id, home_id, json.dumps(['full_control']), datetime.now()))
            
            logger.info(f"Created home '{name}' with ID {home_id} for owner {owner_id}")
            return home_id

    def get_user_homes(self, user_id: int) -> List[Dict]:
        """Get all homes a user has access to."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT h.id, h.name, h.description, h.owner_id, 
                       uh.role, uh.permissions, uh.joined_at,
                       (h.owner_id = %s) as is_owner
                FROM homes h
                JOIN user_homes uh ON h.id = uh.home_id
                WHERE uh.user_id = %s
                ORDER BY h.name
            """, (user_id, user_id))
            
            homes = []
            for row in cursor.fetchall():
                homes.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'owner_id': row[3],
                    'role': row[4],
                    'permissions': json.loads(row[5]) if row[5] else [],
                    'joined_at': row[6],
                    'is_owner': row[7]
                })
            
            return homes

    def get_home_details(self, home_id: int, user_id: int) -> Optional[Dict]:
        """Get detailed information about a home if user has access."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT h.id, h.name, h.description, h.owner_id, h.created_at,
                       uh.role, uh.permissions,
                       (h.owner_id = %s) as is_owner
                FROM homes h
                JOIN user_homes uh ON h.id = uh.home_id
                WHERE h.id = %s AND uh.user_id = %s
            """, (user_id, home_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'owner_id': row[3],
                'created_at': row[4],
                'role': row[5],
                'permissions': json.loads(row[6]) if row[6] else [],
                'is_owner': row[7]
            }

    def user_has_home_access(self, user_id: int, home_id: int) -> bool:
        """Check if user has access to a specific home."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM user_homes 
                WHERE user_id = %s AND home_id = %s
            """, (user_id, home_id))
            
            return cursor.fetchone() is not None

    def user_has_home_permission(self, user_id: int, home_id: int, permission: str) -> bool:
        """Check if user has specific permission in a home."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT permissions, role FROM user_homes 
                WHERE user_id = %s AND home_id = %s
            """, (user_id, home_id))
            
            row = cursor.fetchone()
            if not row:
                return False
                
            permissions = json.loads(row[0]) if row[0] else []
            role = row[1]
            
            # Admin and owner roles have all permissions
            if role in ['admin', 'owner']:
                return True
                
            return permission in permissions

    # ============================================================================
    # ROOM MANAGEMENT
    # ============================================================================

    def create_room(self, home_id: int, name: str, user_id: int, 
                   description: Optional[str] = None) -> int:
        """Create a new room in a home."""
        if not self.user_has_home_permission(user_id, home_id, 'manage_rooms'):
            raise PermissionError("User doesn't have permission to manage rooms")
            
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO rooms (home_id, name, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (home_id, name, description, datetime.now(), datetime.now()))
            
            result = cursor.fetchone()
            if not result:
                raise Exception("Failed to create room")
            room_id = result[0]
            logger.info(f"Created room '{name}' with ID {room_id} in home {home_id}")
            return room_id

    def get_home_rooms(self, home_id: int, user_id: int) -> List[Dict]:
        """Get all rooms in a home that user has access to."""
        if not self.user_has_home_access(user_id, home_id):
            return []
            
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, created_at, updated_at
                FROM rooms 
                WHERE home_id = %s
                ORDER BY name
            """, (home_id,))
            
            rooms = []
            for row in cursor.fetchall():
                rooms.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'created_at': row[3],
                    'updated_at': row[4],
                    'home_id': home_id
                })
            
            return rooms

    def get_room(self, room_id: int, user_id: int) -> Optional[Dict]:
        """Get room details if user has access."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT r.id, r.home_id, r.name, r.description, r.created_at, r.updated_at
                FROM rooms r
                JOIN user_homes uh ON r.home_id = uh.home_id
                WHERE r.id = %s AND uh.user_id = %s
            """, (room_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return {
                'id': row[0],
                'home_id': row[1],
                'name': row[2],
                'description': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            }

    # ============================================================================
    # DEVICE MANAGEMENT
    # ============================================================================

    def create_device(self, room_id: int, name: str, device_type: str, 
                      user_id: int, **kwargs) -> int:
        """Create a new device in a room."""
        # Verify user has access to the room's home
        room = self.get_room(room_id, user_id)
        if not room:
            raise PermissionError("User doesn't have access to this room")
            
        if not self.user_has_home_permission(user_id, room['home_id'], 'manage_devices'):
            raise PermissionError("User doesn't have permission to manage devices")
            
        with self.get_cursor() as cursor:
            # Prepare device data
            device_data = {
                'name': name,
                'type': device_type,
                'enabled': kwargs.get('enabled', True),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Add type-specific fields
            if device_type == 'light':
                device_data.update({
                    'state': kwargs.get('state', False),
                    'brightness': kwargs.get('brightness', 100),
                    'color': kwargs.get('color', '#FFFFFF')
                })
            elif device_type == 'temperature_control':
                device_data.update({
                    'current_temperature': kwargs.get('current_temperature', 20.0),
                    'target_temperature': kwargs.get('target_temperature', 21.0),
                    'mode': kwargs.get('mode', 'auto')
                })
            elif device_type == 'button':
                device_data.update({
                    'action': kwargs.get('action', 'toggle'),
                    'target_device_id': kwargs.get('target_device_id')
                })
            
            cursor.execute("""
                INSERT INTO devices (room_id, name, type, state, brightness, color,
                                   current_temperature, target_temperature, mode,
                                   action, target_device_id, enabled, created_at, updated_at)
                VALUES (%(room_id)s, %(name)s, %(type)s, %(state)s, %(brightness)s, %(color)s,
                        %(current_temperature)s, %(target_temperature)s, %(mode)s,
                        %(action)s, %(target_device_id)s, %(enabled)s, %(created_at)s, %(updated_at)s)
                RETURNING id
            """, {
                'room_id': room_id,
                **device_data
            })
            
            result = cursor.fetchone()
            if not result:
                raise Exception("Failed to create device")
            device_id = result[0]
            logger.info(f"Created {device_type} device '{name}' with ID {device_id} in room {room_id}")
            return device_id

    def get_home_devices(self, home_id: int, user_id: int, 
                        device_type: Optional[str] = None) -> List[Dict]:
        """Get all devices in a home, optionally filtered by type."""
        if not self.user_has_home_access(user_id, home_id):
            return []
            
        with self.get_cursor() as cursor:
            query = """
                SELECT d.*, r.name as room_name, r.home_id
                FROM devices d
                JOIN rooms r ON d.room_id = r.id
                WHERE r.home_id = %s
            """
            params: List[Any] = [home_id]
            
            if device_type:
                query += " AND d.type = %s"
                params.append(device_type)
                
            query += " ORDER BY r.name, d.name"
            
            cursor.execute(query, params)
            
            devices = []
            for row in cursor.fetchall():
                device = {
                    'id': row[0],
                    'room_id': row[1],
                    'name': row[2],
                    'type': row[3],
                    'state': row[4],
                    'brightness': row[5],
                    'color': row[6],
                    'current_temperature': row[7],
                    'target_temperature': row[8],
                    'mode': row[9],
                    'action': row[10],
                    'target_device_id': row[11],
                    'enabled': row[12],
                    'created_at': row[13],
                    'updated_at': row[14],
                    'room_name': row[15],
                    'home_id': row[16]
                }
                devices.append(device)
            
            return devices

    def get_room_devices(self, room_id: int, user_id: int, 
                        device_type: Optional[str] = None) -> List[Dict]:
        """Get all devices in a room, optionally filtered by type."""
        room = self.get_room(room_id, user_id)
        if not room:
            return []
            
        with self.get_cursor() as cursor:
            query = "SELECT * FROM devices WHERE room_id = %s"
            params: List[Any] = [room_id]
            
            if device_type:
                query += " AND type = %s"
                params.append(device_type)
                
            query += " ORDER BY name"
            
            cursor.execute(query, params)
            
            devices = []
            for row in cursor.fetchall():
                device = {
                    'id': row[0],
                    'room_id': row[1],
                    'name': row[2],
                    'type': row[3],
                    'state': row[4],
                    'brightness': row[5],
                    'color': row[6],
                    'current_temperature': row[7],
                    'target_temperature': row[8],
                    'mode': row[9],
                    'action': row[10],
                    'target_device_id': row[11],
                    'enabled': row[12],
                    'created_at': row[13],
                    'updated_at': row[14]
                }
                devices.append(device)
            
            return devices

    def update_device(self, device_id: int, user_id: int, **updates) -> bool:
        """Update device properties."""
        # First verify user has access to this device
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT d.room_id, r.home_id
                FROM devices d
                JOIN rooms r ON d.room_id = r.id
                JOIN user_homes uh ON r.home_id = uh.home_id
                WHERE d.id = %s AND uh.user_id = %s
            """, (device_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return False
                
            room_id, home_id = row
            
            if not self.user_has_home_permission(user_id, home_id, 'control_devices'):
                return False
            
            # Build update query
            update_fields = []
            update_values = []
            
            allowed_fields = ['name', 'state', 'brightness', 'color', 'current_temperature', 
                            'target_temperature', 'mode', 'action', 'target_device_id', 'enabled']
            
            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = %s")
                    update_values.append(value)
            
            if not update_fields:
                return False
                
            update_fields.append("updated_at = %s")
            update_values.append(datetime.now())
            update_values.append(device_id)
            
            cursor.execute(f"""
                UPDATE devices 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """, update_values)
            
            logger.info(f"Updated device {device_id} with fields: {list(updates.keys())}")
            return cursor.rowcount > 0

    def get_device(self, device_id: int, user_id: int) -> Optional[Dict]:
        """Get device details if user has access."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT d.*, r.name as room_name, r.home_id
                FROM devices d
                JOIN rooms r ON d.room_id = r.id
                JOIN user_homes uh ON r.home_id = uh.home_id
                WHERE d.id = %s AND uh.user_id = %s
            """, (device_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return {
                'id': row[0],
                'room_id': row[1],
                'name': row[2],
                'type': row[3],
                'state': row[4],
                'brightness': row[5],
                'color': row[6],
                'current_temperature': row[7],
                'target_temperature': row[8],
                'mode': row[9],
                'action': row[10],
                'target_device_id': row[11],
                'enabled': row[12],
                'created_at': row[13],
                'updated_at': row[14],
                'room_name': row[15],
                'home_id': row[16]
            }

    # ============================================================================
    # USER AND SESSION MANAGEMENT
    # ============================================================================

    def get_user_current_home(self, user_id: int) -> Optional[int]:
        """Get user's current home ID from session or default."""
        with self.get_cursor() as cursor:
            # First try to get from active session
            cursor.execute("""
                SELECT current_home_id FROM session_tokens 
                WHERE user_id = %s AND expires_at > %s 
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, datetime.now()))
            
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
            
            # Fall back to user's default home
            cursor.execute("""
                SELECT default_home_id FROM users WHERE id = %s
            """, (user_id,))
            
            row = cursor.fetchone()
            return row[0] if row else None

    def set_user_current_home(self, user_id: int, home_id: int, session_token: Optional[str] = None) -> bool:
        """Set user's current home in session."""
        if not self.user_has_home_access(user_id, home_id):
            return False
            
        with self.get_cursor() as cursor:
            if session_token:
                cursor.execute("""
                    UPDATE session_tokens 
                    SET current_home_id = %s, updated_at = %s
                    WHERE token = %s AND user_id = %s
                """, (home_id, datetime.now(), session_token, user_id))
            else:
                # Update user's default home
                cursor.execute("""
                    UPDATE users 
                    SET default_home_id = %s, updated_at = %s
                    WHERE id = %s
                """, (home_id, datetime.now(), user_id))
            
            return cursor.rowcount > 0

    # ============================================================================
    # CONVENIENCE METHODS (Type-specific device access)
    # ============================================================================

    def get_lights(self, home_id: int, user_id: int) -> List[Dict]:
        """Get all lights in a home."""
        return self.get_home_devices(home_id, user_id, 'light')

    def get_temperature_controls(self, home_id: int, user_id: int) -> List[Dict]:
        """Get all temperature controls in a home."""
        return self.get_home_devices(home_id, user_id, 'temperature_control')

    def get_buttons(self, home_id: int, user_id: int) -> List[Dict]:
        """Get all buttons in a home."""
        return self.get_home_devices(home_id, user_id, 'button')