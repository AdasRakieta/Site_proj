import psycopg2
import json
import uuid
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any, Tuple
from contextlib import contextmanager
import logging
from psycopg2 import errors, sql

logger = logging.getLogger(__name__)

class MultiHomeDBManager:
    """
    Database manager for multi-home smart home system.
    Handles all database operations with home context isolation.
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, 
                 user: Optional[str] = None, password: Optional[str] = None, 
                 database: Optional[str] = None, 
                 connection_timeout: int = 10):
        # Use environment variables if parameters not provided
        self.host = host or os.getenv('DB_HOST', '100.103.184.90')
        self.port = port or int(os.getenv('DB_PORT', '5432'))
        self.user = user or os.getenv('DB_USER', 'admin')
        self.password = password or os.getenv('DB_PASSWORD', 'Qwuizzy123.')
        self.database = database or os.getenv('DB_NAME', 'smarthome_multihouse')
        self.connection_timeout = connection_timeout
        self._connection = None
        self._ensure_connection()
        self._ensure_security_state_table()
        self._ensure_automation_table()
        self._ensure_invitations_table()

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

    @staticmethod
    def _normalize_device_id(device_id: Any) -> Optional[Any]:
        """Normalize device identifier, allowing UUID strings alongside integers."""
        if device_id is None:
            return None
        if isinstance(device_id, int):
            return device_id
        if isinstance(device_id, str):
            value = device_id.strip()
            if not value:
                return None
            if value.isdigit():
                try:
                    return int(value)
                except ValueError:
                    return value
            return value
        return device_id

    @staticmethod
    def _normalize_home_id(home_id: Any) -> Optional[str]:
        """Normalize home identifier to a non-empty string."""
        if home_id is None:
            return None
        value = str(home_id).strip()
        return value or None

    @staticmethod
    def _normalize_automation_name(name: Any) -> str:
        """Normalize automation name and raise if invalid."""
        if name is None:
            raise ValueError("Automation name is required")
        value = str(name).strip()
        if not value:
            raise ValueError("Automation name cannot be empty")
        return value

    def _can_manage_automations(self, user_id: str, home_id: str) -> bool:
        """Check whether a user can manage automations in the given home."""
        return (
            self.user_has_home_permission(user_id, home_id, 'manage_automations') or
            self.user_has_home_permission(user_id, home_id, 'manage_devices') or
            self.user_has_home_permission(user_id, home_id, 'control_devices')
        )

    def _ensure_security_state_table(self):
        """Ensure the per-home security state table exists."""
        create_sql = """
            CREATE TABLE IF NOT EXISTS home_security_states (
                home_id UUID PRIMARY KEY,
                state VARCHAR(32) NOT NULL,
                last_changed TIMESTAMPTZ NOT NULL,
                changed_by UUID,
                details JSONB
            )
        """
        with self.get_cursor() as cursor:
            cursor.execute(create_sql)

    def _ensure_automation_table(self):
        """Ensure the per-home automations table exists."""
        create_sql = """
            CREATE TABLE IF NOT EXISTS home_automations (
                id UUID PRIMARY KEY,
                home_id UUID NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                name_normalized TEXT NOT NULL,
                trigger_config JSONB NOT NULL DEFAULT '{}'::jsonb,
                actions_config JSONB NOT NULL DEFAULT '[]'::jsonb,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                execution_count INTEGER NOT NULL DEFAULT 0,
                last_executed TIMESTAMPTZ,
                error_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """
        index_sql = """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_home_automations_unique
            ON home_automations (home_id, name_normalized)
        """
        with self.get_cursor() as cursor:
            cursor.execute(create_sql)
            cursor.execute(index_sql)

    def _ensure_invitations_table(self):
        """Ensure the home invitations table exists."""
        create_sql = """
            CREATE TABLE IF NOT EXISTS home_invitations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                home_id UUID NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'member', 'guest')),
                invitation_code VARCHAR(20) UNIQUE NOT NULL,
                invited_by UUID NOT NULL REFERENCES users(id),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired', 'rejected')),
                accepted_at TIMESTAMPTZ,
                accepted_by UUID REFERENCES users(id)
            )
        """
        column_check_sql = """
            SELECT column_name, is_nullable, column_default, data_type
            FROM information_schema.columns
            WHERE table_name = 'home_invitations' AND table_schema = current_schema()
        """
        constraint_check_sql = """
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
             AND tc.constraint_schema = ccu.constraint_schema
            WHERE tc.table_name = 'home_invitations'
              AND tc.table_schema = current_schema()
              AND tc.constraint_type = 'CHECK'
              AND ccu.column_name = 'status'
        """
        index_sql_1 = """
            CREATE INDEX IF NOT EXISTS idx_home_invitations_code 
            ON home_invitations (invitation_code) WHERE status = 'pending'
        """
        index_sql_2 = """
            CREATE INDEX IF NOT EXISTS idx_home_invitations_home_email 
            ON home_invitations (home_id, email, status)
        """
        ensure_unique_invitation_code_sql = """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE tablename = 'home_invitations'
                      AND indexname = 'home_invitations_invitation_code_key'
                ) THEN
                    EXECUTE 'CREATE UNIQUE INDEX home_invitations_invitation_code_key
                             ON home_invitations (invitation_code)';
                END IF;
            END
            $$;
        """
        with self.get_cursor() as cursor:
            cursor.execute(create_sql)
            cursor.execute(column_check_sql)
            column_rows = cursor.fetchall()
            existing_columns = {
                row[0]: {
                    'is_nullable': row[1],
                    'default': row[2],
                    'data_type': row[3]
                }
                for row in column_rows
            }

            # Drop invitation_token column if it exists (legacy)
            if 'invitation_token' in existing_columns:
                cursor.execute("""
                    ALTER TABLE home_invitations DROP COLUMN IF EXISTS invitation_token
                """)
                logger.info("Dropped legacy invitation_token column")

            # Handle legacy schema upgrades
            if 'status' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE home_invitations
                    ADD COLUMN status VARCHAR(20)
                    DEFAULT 'pending'
                """)

            cursor.execute("""
                UPDATE home_invitations
                SET status = 'pending'
                WHERE status IS NULL OR status NOT IN ('pending', 'accepted', 'expired', 'rejected')
            """)
            cursor.execute("""
                ALTER TABLE home_invitations
                ALTER COLUMN status TYPE VARCHAR(20)
            """)
            cursor.execute("""
                ALTER TABLE home_invitations
                ALTER COLUMN status SET DEFAULT 'pending'
            """)
            cursor.execute("""
                ALTER TABLE home_invitations
                ALTER COLUMN status SET NOT NULL
            """)

            if 'invitation_code' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE home_invitations
                    ADD COLUMN invitation_code VARCHAR(20)
                """)

            cursor.execute("""
                UPDATE home_invitations
                SET invitation_code = substr(md5((random())::text || id::text), 1, 20)
                WHERE invitation_code IS NULL OR length(trim(invitation_code)) = 0
            """)

            cursor.execute("""
                ALTER TABLE home_invitations
                ALTER COLUMN invitation_code TYPE VARCHAR(20)
            """)

            cursor.execute("""
                ALTER TABLE home_invitations
                ALTER COLUMN invitation_code SET DEFAULT substr(md5(random()::text), 1, 20)
            """)

            cursor.execute("""
                ALTER TABLE home_invitations
                ALTER COLUMN invitation_code SET NOT NULL
            """)

            cursor.execute(constraint_check_sql)
            status_constraints = [row[0] for row in cursor.fetchall()]
            for constraint_name in status_constraints:
                cursor.execute(
                    sql.SQL("ALTER TABLE home_invitations DROP CONSTRAINT {}").format(
                        sql.Identifier(constraint_name)
                    )
                )
            cursor.execute("""
                ALTER TABLE home_invitations
                ADD CONSTRAINT home_invitations_status_check
                CHECK (status IN ('pending', 'accepted', 'expired', 'rejected'))
            """)

            cursor.execute(ensure_unique_invitation_code_sql)
            if 'accepted_at' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE home_invitations
                    ADD COLUMN accepted_at TIMESTAMPTZ
                """)
            if 'accepted_by' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE home_invitations
                    ADD COLUMN accepted_by UUID REFERENCES users(id)
                """)

            cursor.execute(index_sql_1)
            cursor.execute(index_sql_2)

    # ============================================================================
    # HOME MANAGEMENT
    # ============================================================================

    def create_home(self, name: str, owner_id: str, description: Optional[str] = None) -> int:
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
            
            # Add owner to user_homes with owner role (creator becomes owner of their home)
            cursor.execute("""
                INSERT INTO user_homes (user_id, home_id, role, permissions, joined_at)
                VALUES (%s, %s, 'owner', %s, %s)
            """, (owner_id, home_id, json.dumps(['full_control']), datetime.now()))
            
            # Note: Owner field in homes table tracks ownership, and user gets owner role in user_homes
            
            logger.info(f"Created home '{name}' with ID {home_id} for owner {owner_id}")
            return home_id

    def get_user_homes(self, user_id: str) -> List[Dict]:
        """Get all homes a user has access to. Sys-admin sees all homes."""
        with self.get_cursor() as cursor:
            # Check if user is sys-admin - if so, return all homes with sys-admin role
            if self.is_sys_admin(user_id):
                cursor.execute("""
                    SELECT h.id, h.name, h.description, h.owner_id, 
                           'sys-admin' as role, '[]' as permissions, NOW() as joined_at,
                           (h.owner_id = %s) as is_owner
                    FROM homes h
                    ORDER BY h.name
                """, (user_id,))
            else:
                # Regular users - only homes they're members of
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
                # Handle permissions - might already be parsed by psycopg2
                permissions = row[5]
                if isinstance(permissions, str):
                    permissions = json.loads(permissions) if permissions else []
                elif permissions is None:
                    permissions = []
                    
                homes.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'owner_id': row[3],
                    'role': row[4],
                    'permissions': permissions,
                    'joined_at': row[6],
                    'is_owner': row[7]
                })
            
            return homes

    def get_home_details(self, home_id: str, user_id: str) -> Optional[Dict]:
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
                
            # Handle permissions - might already be parsed by psycopg2
            permissions = row[6]
            if isinstance(permissions, str):
                permissions = json.loads(permissions) if permissions else []
            elif permissions is None:
                permissions = []
            
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'owner_id': row[3],
                'created_at': row[4],
                'role': row[5],
                'permissions': permissions,
                'is_owner': row[7]
            }

    def user_has_home_access(self, user_id: str, home_id: str) -> bool:
        """Check if user has access to a specific home."""
        # First check if user is sys-admin (has global access)
        if self.is_sys_admin(user_id):
            return True
            
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM user_homes 
                WHERE user_id = %s AND home_id = %s
            """, (user_id, home_id))
            
            return cursor.fetchone() is not None
            
    def is_sys_admin(self, user_id: str) -> bool:
        """Check if user has system administrator role."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM users 
                WHERE id = %s AND role = 'sys-admin'
            """, (user_id,))
            return cursor.fetchone() is not None

    def user_has_home_permission(self, user_id: str, home_id: str, permission: str) -> bool:
        """Check if user has specific permission in a home."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT permissions, role FROM user_homes 
                WHERE user_id = %s AND home_id = %s
            """, (user_id, home_id))
            
            row = cursor.fetchone()
            if not row:
                return False
                
            permissions = row[0] if row[0] else []  # Already parsed by psycopg2
            role = row[1]
            
            # Admin, owner, and sys-admin roles have all permissions
            if role in ['admin', 'owner', 'sys-admin']:
                return True
                
            return permission in permissions

    def get_user_role_in_home(self, user_id: str, home_id: str) -> Optional[str]:
        """Get user's role in a specific home."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT role FROM user_homes 
                WHERE user_id = %s AND home_id = %s
            """, (user_id, home_id))
            
            row = cursor.fetchone()
            return row[0] if row else None
            
    def has_admin_access(self, user_id: str, home_id: Optional[str] = None) -> bool:
        """
        Check if user has admin access (sys-admin globally or admin/owner in specific home).
        
        Args:
            user_id: ID of the user
            home_id: ID of the home to check (if None, checks global access only)
            
        Returns:
            True if user has admin access, False otherwise
            
        Role hierarchy:
        - sys-admin: Full access to all homes and all functions (highest)
        - owner: Full access to their own home
        - admin: Admin access to specific home (can manage users, settings)
        - member: Regular user access (can view/control devices)
        - guest: Limited read-only access
        """
        # 1. Check if user is sys-admin (global access to everything)
        if self.is_sys_admin(user_id):
            return True
            
        # 2. If home_id provided, check home-specific access
        if home_id:
            home_role = self.get_user_role_in_home(user_id, home_id)
            # owner and admin have admin access, sys-admin checked above
            return home_role in ['owner', 'admin', 'sys-admin']
            
        # 3. If no home specified, check if user has admin/owner access in any home
        user_homes = self.get_user_homes(user_id)
        return any(home.get('role') in ['admin', 'owner', 'sys-admin'] for home in user_homes)

    # ============================================================================
    # HOME ADMIN FUNCTIONS
    # ============================================================================
    
    def get_home_users(self, home_id: str, admin_user_id: str) -> List[Dict]:
        """
        Get all users in a specific home (for admin dashboard).
        
        Args:
            home_id: ID of the home
            admin_user_id: ID of the admin requesting the list
            
        Returns:
            List of users with their roles in this home
        """
        # Check admin access
        if not self.has_admin_access(admin_user_id, home_id):
            raise PermissionError("User doesn't have admin access to this home")
            
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT u.id, u.name, u.email, u.role as global_role,
                       uh.role as home_role, uh.joined_at, uh.last_access,
                       (h.owner_id = u.id) as is_home_owner
                FROM users u
                JOIN user_homes uh ON u.id = uh.user_id  
                JOIN homes h ON uh.home_id = h.id
                WHERE uh.home_id = %s
                ORDER BY uh.role DESC, u.name
            """, (home_id,))
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'user_id': str(row[0]),
                    'username': row[1], 
                    'email': row[2] or '',
                    'global_role': row[3],
                    'home_role': row[4],
                    'joined_at': row[5],
                    'last_access': row[6],
                    'is_home_owner': row[7]
                })
            
            return users
            
    def add_user_to_home(self, home_id: str, username: str, email: str, password: str, 
                        role: str, admin_user_id: str) -> str:
        """
        Add new user to the system and assign to home.
        
        Args:
            home_id: ID of the home to add user to
            username: Username for new user
            email: Email for new user
            password: Plain text password (will be hashed)
            role: Role in the home ('admin', 'member', 'guest')
            admin_user_id: ID of the admin adding the user
            
        Returns:
            ID of the created user
        """
        # Check admin access
        if not self.has_admin_access(admin_user_id, home_id):
            raise PermissionError("User doesn't have admin access to this home")
            
        # Validate role
        if role not in ['admin', 'member', 'guest']:
            raise ValueError(f"Invalid home role: {role}")
            
        with self.get_cursor() as cursor:
            # Check if user already exists globally
            cursor.execute("SELECT id FROM users WHERE name = %s OR email = %s", (username, email))
            existing = cursor.fetchone()
            
            if existing:
                existing_user_id = str(existing[0])
                
                # Check if user is already in this home
                cursor.execute("SELECT 1 FROM user_homes WHERE user_id = %s AND home_id = %s", 
                             (existing_user_id, home_id))
                if cursor.fetchone():
                    raise ValueError("User already exists in this home")
                    
                # Add existing user to home
                cursor.execute("""
                    INSERT INTO user_homes (user_id, home_id, role, joined_at)
                    VALUES (%s, %s, %s, %s)
                """, (existing_user_id, home_id, role, datetime.now()))
                
                logger.info(f"Added existing user {username} to home {home_id} with role {role}")
                return existing_user_id
            else:
                # Create new user and add to home
                user_id, _ = self.create_user(username, email, password, create_default_home=False)
                
                # Add to specified home
                cursor.execute("""
                    INSERT INTO user_homes (user_id, home_id, role, joined_at)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, home_id, role, datetime.now()))
                
                logger.info(f"Created new user {username} and added to home {home_id} with role {role}")
                return user_id
                
    def get_home_management_logs(self, home_id: str, admin_user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get management logs for a specific home.
        
        Args:
            home_id: ID of the home
            admin_user_id: ID of the admin requesting logs
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries for this home
        """
        # Check admin access
        if not self.has_admin_access(admin_user_id, home_id):
            raise PermissionError("User doesn't have admin access to this home")
            
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, timestamp, level, message, event_type, 
                       user_id, username, ip_address, details
                FROM management_logs 
                WHERE home_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (home_id, limit))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'id': str(row[0]),
                    'timestamp': row[1],
                    'level': row[2],
                    'message': row[3],
                    'event_type': row[4],
                    'user_id': str(row[5]) if row[5] else None,
                    'username': row[6],
                    'ip_address': str(row[7]) if row[7] else None,
                    'details': row[8] or {}
                })
            
            return logs

    def add_home_management_log(self, home_id: str, level: str, message: str,
                              event_type: str = 'general', user_id: Optional[str] = None,
                              username: Optional[str] = None, ip_address: Optional[str] = None,
                              details: Optional[Dict] = None) -> bool:
        """
        Add a management log entry for a specific home.
        
        Args:
            home_id: ID of the home
            level: Log level (info, warning, error)
            message: Log message
            event_type: Type of event (device_creation, room_creation, etc.)
            user_id: ID of user performing the action
            username: Username of user performing the action
            ip_address: IP address of user
            details: Additional details as JSON
            
        Returns:
            True if log was added successfully
        """
        import json
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO management_logs 
                (home_id, timestamp, level, message, event_type, user_id, username, ip_address, details)
                VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s)
            """, (
                home_id, level, message, event_type,
                user_id, username, ip_address, 
                json.dumps(details or {})
            ))
            return True

    def get_home_stats(self, home_id: str, admin_user_id: str) -> Dict:
        """
        Get statistics for a specific home.
        
        Args:
            home_id: ID of the home
            admin_user_id: ID of the admin requesting stats
            
        Returns:
            Dictionary with home statistics
        """
        # Check admin access
        if not self.has_admin_access(admin_user_id, home_id):
            raise PermissionError("User doesn't have admin access to this home")
            
        with self.get_cursor() as cursor:
            # Get basic counts
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM user_homes WHERE home_id = %s) as users_count,
                    (SELECT COUNT(*) FROM rooms WHERE home_id = %s) as rooms_count,
                    (SELECT COUNT(*) FROM devices d JOIN rooms r ON d.room_id = r.id WHERE r.home_id = %s) as devices_count,
                    (SELECT COUNT(*) FROM automations WHERE home_id = %s) as automations_count,
                    (SELECT COUNT(*) FROM management_logs WHERE home_id = %s) as logs_count
            """, (home_id, home_id, home_id, home_id, home_id))
            
            row = cursor.fetchone()
            
            if not row:
                return {
                    'users_count': 0,
                    'rooms_count': 0,
                    'devices_count': 0,
                    'automations_count': 0,
                    'logs_count': 0
                }
            
            return {
                'users_count': row[0] or 0,
                'rooms_count': row[1] or 0, 
                'devices_count': row[2] or 0,
                'automations_count': row[3] or 0,
                'logs_count': row[4] or 0
            }
            
    def get_notification_recipients(self, home_id: str, admin_user_id: str) -> List[Dict]:
        """
        Get notification recipients for a specific home.
        
        Args:
            home_id: ID of the home
            admin_user_id: ID of the admin requesting recipients
            
        Returns:
            List of notification recipients
        """
        # Check admin access
        if not self.has_admin_access(admin_user_id, home_id):
            raise PermissionError("User doesn't have admin access to this home")
        
        with self.get_cursor() as cursor:
            # For now, return home users as potential recipients
            # In future, this could be a separate notification_recipients table
            cursor.execute("""
                SELECT u.id, u.name, u.email, uh.role, 
                       TRUE as enabled  -- Default all users to enabled
                FROM users u
                JOIN user_homes uh ON u.id = uh.user_id
                WHERE uh.home_id = %s
                ORDER BY uh.role DESC, u.name
            """, (home_id,))
            
            recipients = []
            for row in cursor.fetchall():
                recipients.append({
                    'user_id': str(row[0]),
                    'user': row[1],  # username
                    'email': row[2] or '',
                    'role': row[3],
                    'enabled': row[4]
                })
            
            return recipients
            
    def set_notification_recipients(self, home_id: str, recipients: List[Dict], admin_user_id: str) -> bool:
        """
        Set notification recipients for a specific home.
        
        Args:
            home_id: ID of the home
            recipients: List of recipients with enabled status
            admin_user_id: ID of the admin setting recipients
            
        Returns:
            True if successful
        """
        # Check admin access
        if not self.has_admin_access(admin_user_id, home_id):
            raise PermissionError("User doesn't have admin access to this home")
        
        # For now, just validate the input since we don't have a separate notifications table
        # In the future, this could update a notification_recipients table
        try:
            for recipient in recipients:
                if not isinstance(recipient.get('enabled'), bool):
                    raise ValueError("Invalid recipient format")
            
            logger.info(f"Updated notification recipients for home {home_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update notification recipients for home {home_id}: {e}")
            return False

    # ============================================================================
    # ROOM MANAGEMENT
    # ============================================================================

    def create_room(self, home_id: str, name: str, user_id: str, 
                   description: Optional[str] = None) -> int:
        """Create a new room in a home."""
        if not self.user_has_home_permission(user_id, home_id, 'manage_rooms'):
            raise PermissionError("User doesn't have permission to manage rooms")

        normalized_name = (name or '').strip()
        if not normalized_name:
            raise ValueError("Room name is required")

        with self.get_cursor() as cursor:
            # Ensure uniqueness of room name within the home (case-insensitive)
            cursor.execute(
                """
                SELECT 1 FROM rooms 
                WHERE home_id = %s AND LOWER(name) = LOWER(%s)
                """,
                (home_id, normalized_name)
            )
            if cursor.fetchone():
                raise ValueError("Room with this name already exists in the selected home")

            cursor.execute(
                """
                SELECT COALESCE(MAX(display_order), 0) + 1 
                FROM rooms 
                WHERE home_id = %s
                """,
                (home_id,)
            )
            next_order_row = cursor.fetchone()
            next_order = next_order_row[0] if next_order_row else 1

            cursor.execute(
                """
                INSERT INTO rooms (home_id, name, description, display_order, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, display_order
                """,
                (home_id, normalized_name, description, next_order, datetime.now(), datetime.now())
            )

            result = cursor.fetchone()
            if not result:
                raise Exception("Failed to create room")

            room_id = result[0]
            logger.info(f"Created room '{normalized_name}' with ID {room_id} in home {home_id}")
            return room_id

    def get_home_rooms(self, home_id: str, user_id: str) -> List[Dict]:
        """Get all rooms in a home that user has access to."""
        if not self.user_has_home_access(user_id, home_id):
            return []
            
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, description, display_order, created_at, updated_at
                FROM rooms 
                WHERE home_id = %s
                ORDER BY display_order ASC NULLS LAST, name
                """,
                (home_id,)
            )

            rooms = []
            for row in cursor.fetchall():
                rooms.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'display_order': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'home_id': home_id
                })
            
            return rooms

    def ensure_unassigned_room(self, home_id: Any, user_id: str) -> Optional[int]:
        """Ensure the special 'Nieprzypisane' room exists for a home and return its ID."""
        normalized_home_id = self._normalize_home_id(home_id)
        if not normalized_home_id or not user_id:
            return None

        if not self.user_has_home_access(user_id, normalized_home_id):
            raise PermissionError("User doesn't have access to this home")

        system_room_name = 'Nieprzypisane'

        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM rooms
                WHERE home_id = %s AND LOWER(name) = LOWER(%s)
                LIMIT 1
                """,
                (normalized_home_id, system_room_name)
            )

            row = cursor.fetchone()
            if row:
                return row[0]

            cursor.execute(
                """
                INSERT INTO rooms (home_id, name, description, display_order, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    normalized_home_id,
                    system_room_name,
                    'Systemowy pokój na urządzenia bez przypisania',
                    9999,
                    datetime.now(),
                    datetime.now()
                )
            )

            result = cursor.fetchone()
            return result[0] if result else None

    def get_room(self, room_id: Any, user_id: str) -> Optional[Dict]:
        """Get room details if user has access."""
        if room_id is None:
            return None

        normalized_id: Any = room_id
        if isinstance(room_id, str):
            normalized_id = room_id.strip()
            if not normalized_id:
                return None

        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT r.id, r.home_id, r.name, r.description, r.created_at, r.updated_at
                FROM rooms r
                JOIN user_homes uh ON r.home_id = uh.home_id
                WHERE r.id = %s AND uh.user_id = %s
            """, (normalized_id, user_id))
            
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

    def get_room_by_name(self, home_id: str, user_id: str, name: str) -> Optional[Dict]:
        """Fetch a room within a home by its name (case-insensitive)."""
        if not name:
            return None

        if not self.user_has_home_access(user_id, home_id):
            return None

        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM rooms
                WHERE home_id = %s AND LOWER(name) = LOWER(%s)
                LIMIT 1
                """,
                (home_id, name)
            )

            row = cursor.fetchone()
            if not row:
                return None

            return self.get_room(row[0], user_id)

    def update_room(self, room_id: Any, user_id: str, **changes) -> Optional[Dict]:
        """Update room metadata (name, description, display order)."""
        if room_id is None:
            return None

        room = self.get_room(room_id, user_id)
        if not room:
            return None

        if not self.user_has_home_permission(user_id, room['home_id'], 'manage_rooms'):
            raise PermissionError("User doesn't have permission to update rooms")

        allowed_fields = {}
        if 'name' in changes and changes['name'] is not None:
            new_name = str(changes['name']).strip()
            if not new_name:
                raise ValueError("Room name cannot be empty")

            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 1 FROM rooms
                    WHERE home_id = %s AND LOWER(name) = LOWER(%s) AND id != %s
                    """,
                    (room['home_id'], new_name, room['id'])
                )
                if cursor.fetchone():
                    raise ValueError("Another room with this name already exists")

            allowed_fields['name'] = new_name

        if 'description' in changes:
            allowed_fields['description'] = changes['description']

        if 'display_order' in changes and changes['display_order'] is not None:
            try:
                allowed_fields['display_order'] = int(changes['display_order'])
            except (TypeError, ValueError):
                raise ValueError("display_order must be an integer")

        if not allowed_fields:
            return room

        set_fragments = []
        values: List[Any] = []
        for column, value in allowed_fields.items():
            set_fragments.append(f"{column} = %s")
            values.append(value)

        values.extend([datetime.now(), room['id']])

        with self.get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE rooms
                SET {', '.join(set_fragments)}, updated_at = %s
                WHERE id = %s
                """,
                tuple(values)
            )

        return self.get_room(room['id'], user_id)

    def delete_room(self, room_id: Any, user_id: str) -> bool:
        """Delete a room and unassign associated devices."""
        if room_id is None:
            return False

        room = self.get_room(room_id, user_id)
        if not room:
            return False

        if not self.user_has_home_permission(user_id, room['home_id'], 'manage_rooms'):
            raise PermissionError("User doesn't have permission to delete rooms")

        with self.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE devices
                SET room_id = NULL, updated_at = %s
                WHERE room_id = %s
                """,
                (datetime.now(), room['id'])
            )

            cursor.execute(
                """
                DELETE FROM room_temperature_states
                WHERE room_id = %s
                """,
                (room['id'],)
            )

            cursor.execute(
                """
                DELETE FROM rooms
                WHERE id = %s
                """,
                (room['id'],)
            )

            return cursor.rowcount > 0

    def reorder_rooms(self, home_id: str, user_id: str, room_ids: List[Any]) -> bool:
        """Update display order of rooms within a home."""
        if not room_ids:
            return False

        if not self.user_has_home_permission(user_id, home_id, 'manage_rooms'):
            raise PermissionError("User doesn't have permission to reorder rooms")

        normalized_ids: List[Any] = []
        for room_id in room_ids:
            if room_id is None:
                continue
            normalized_ids.append(room_id)

        if not normalized_ids:
            return False

        with self.get_cursor() as cursor:
            for order_index, room_id in enumerate(normalized_ids):
                cursor.execute(
                    """
                    UPDATE rooms
                    SET display_order = %s, updated_at = %s
                    WHERE id = %s AND home_id = %s
                    """,
                    (order_index, datetime.now(), room_id, home_id)
                )

        return True

    # ============================================================================
    # DEVICE MANAGEMENT
    # ============================================================================

    def create_device(self, room_id: Optional[int], name: str, device_type: str,
                      user_id: str, **kwargs) -> int:
        """Create a new device, optionally unassigned (room_id = NULL).

        When room_id is None, a 'home_id' kwarg must be provided to validate permissions.
        """
        target_home_id: Optional[str] = None
        if room_id is not None:
            # Verify user has access to the room's home
            room = self.get_room(room_id, user_id)
            if not room:
                raise PermissionError("User doesn't have access to this room")
            target_home_id = room['home_id']
        else:
            # Unassigned device creation requires explicit home context for permissions
            target_home_id = self._normalize_home_id(kwargs.get('home_id'))
            if not target_home_id:
                raise ValueError("home_id is required when creating device without room")

        if not target_home_id:
            raise ValueError("Unable to determine home context for device creation")
        if not self.user_has_home_permission(user_id, target_home_id, 'manage_devices'):
            raise PermissionError("User doesn't have permission to manage devices")
            
        with self.get_cursor() as cursor:
            # Create settings JSON from type-specific fields
            settings = {}
            if device_type == 'light':
                settings = {
                    'brightness': kwargs.get('brightness', 100),
                    'color': kwargs.get('color', '#FFFFFF')
                }
            elif device_type == 'temperature_control':
                settings = {
                    'target_temperature': kwargs.get('target_temperature', 21.0),
                    'mode': kwargs.get('mode', 'auto')
                }
            elif device_type == 'button':
                settings = {
                    'action': kwargs.get('action', 'toggle'),
                    'target_device_id': kwargs.get('target_device_id')
                }
            
            cursor.execute("""
                INSERT INTO devices (room_id, name, device_type, state, temperature,
                                   enabled, settings, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                room_id,
                name,
                device_type,
                kwargs.get('state', False if device_type == 'light' else None),
                kwargs.get('current_temperature', 20.0 if device_type == 'temperature_control' else None),
                kwargs.get('enabled', True),
                json.dumps(settings) if settings else None,
                datetime.now(),
                datetime.now()
            ))
            
            result = cursor.fetchone()
            if not result:
                raise Exception("Failed to create device")
            device_id = result[0]
            logger.info(f"Created {device_type} device '{name}' with ID {device_id} in room {room_id}")
            return device_id

    def get_home_devices(self, home_id: str, user_id: str,
                        device_type: Optional[str] = None) -> List[Dict]:
        """Get all devices in a home, optionally filtered by type."""
        if not self.user_has_home_access(user_id, home_id):
            return []
            
        with self.get_cursor() as cursor:
            query = """
                SELECT d.*, r.name as room_name, r.home_id
                FROM devices d
                LEFT JOIN rooms r ON d.room_id = r.id
                WHERE (r.home_id = %s OR d.room_id IS NULL)
            """
            params: List[Any] = [home_id]
            
            if device_type:
                query += " AND d.device_type = %s"
                params.append(device_type)
                
            # Sort by room name, then device type (buttons first, then temperature_controls), then display_order within type
            query += """ ORDER BY r.name NULLS LAST, 
                        CASE d.device_type 
                            WHEN 'light' THEN 1 
                            WHEN 'button' THEN 1
                            WHEN 'temperature_control' THEN 2 
                            ELSE 3 
                        END,
                        d.display_order NULLS LAST, d.name"""
            
            cursor.execute(query, params)
            
            devices = []
            for row in cursor.fetchall():
                device = {
                    'id': row[0],          # id
                    'name': row[1],        # name  
                    'room_id': row[2],     # room_id
                    'type': row[3],        # device_type
                    'state': row[4],       # state
                    'temperature': row[5], # temperature (current)
                    'min_temperature': row[6],  # min_temperature
                    'max_temperature': row[7],  # max_temperature
                    'display_order': row[8],    # display_order
                    'enabled': row[9],     # enabled
                    'settings': row[10],   # settings (JSONB)
                    'created_at': row[11], # created_at
                    'updated_at': row[12], # updated_at
                    'room_name': row[13],  # room_name
                    'home_id': row[14]     # home_id
                }
                devices.append(device)
            
            return devices

    def get_room_devices(self, room_id: int, user_id: str, 
                        device_type: Optional[str] = None) -> List[Dict]:
        """Get all devices in a room, optionally filtered by type."""
        room = self.get_room(room_id, user_id)
        if not room:
            return []
            
        with self.get_cursor() as cursor:
            query = "SELECT * FROM devices WHERE room_id = %s"
            params: List[Any] = [room_id]
            
            if device_type:
                query += " AND device_type = %s"
                params.append(device_type)
                
            # Sort by device type (buttons first, then temperature_controls), then display_order within type
            query += """ ORDER BY 
                        CASE device_type 
                            WHEN 'light' THEN 1 
                            WHEN 'button' THEN 1
                            WHEN 'temperature_control' THEN 2 
                            ELSE 3 
                        END,
                        display_order NULLS LAST, name"""
            
            cursor.execute(query, params)
            
            devices = []
            for row in cursor.fetchall():
                device = {
                    'id': row[0],          # id
                    'name': row[1],        # name
                    'room_id': row[2],     # room_id
                    'type': row[3],        # device_type
                    'device_type': row[3], # alias for compatibility
                    'state': row[4],       # state
                    'temperature': row[5], # temperature
                    'min_temperature': row[6],  # min_temperature
                    'max_temperature': row[7],  # max_temperature
                    'display_order': row[8],    # display_order
                    'enabled': row[9],     # enabled
                    'settings': row[10],   # settings
                    'created_at': row[11], # created_at
                    'updated_at': row[12]  # updated_at
                }
                devices.append(device)
            
            return devices

    def update_device(self, device_id: Any, user_id: str, **updates) -> bool:
        """Update device properties."""
        normalized_id = self._normalize_device_id(device_id)
        if normalized_id is None:
            raise ValueError("device_id is required for update")
        # First verify user has access to this device
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT d.room_id, r.home_id
                FROM devices d
                LEFT JOIN rooms r ON d.room_id = r.id
                LEFT JOIN user_homes uh ON r.home_id = uh.home_id
                WHERE d.id = %s AND (uh.user_id = %s OR d.room_id IS NULL)
            """, (normalized_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return False
                
            room_id, home_id = row
            
            # If device has no room, we'll need to validate permission on target room during update
            if home_id and not self.user_has_home_permission(user_id, home_id, 'control_devices'):
                return False
            
            # Build update query
            update_fields = []
            update_values = []
            
            allowed_fields = ['name', 'state', 'brightness', 'color', 'temperature', 'current_temperature', 
                            'target_temperature', 'mode', 'action', 'target_device_id', 'enabled', 'room_id', 'display_order']
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'room_id':
                        # Validate new room exists and user has access
                        if value is not None:
                            cursor.execute("""
                                SELECT home_id FROM rooms 
                                WHERE id = %s
                            """, (value,))
                            room_row = cursor.fetchone()
                            if not room_row:
                                raise ValueError(f"Room with ID {value} not found")
                            new_room_home_id = room_row[0]
                            if not self.user_has_home_permission(user_id, new_room_home_id, 'manage_devices'):
                                raise PermissionError("No permission to move device to target room")
                        update_fields.append(f"{field} = %s")
                        update_values.append(value)
                    else:
                        update_fields.append(f"{field} = %s")
                        update_values.append(value)
            
            if not update_fields:
                return False
                
            update_fields.append("updated_at = %s")
            update_values.append(datetime.now())
            update_values.append(normalized_id)

            cursor.execute(f"""
                UPDATE devices 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """, update_values)

            rows_updated = cursor.rowcount

            # If temperature-related fields are being updated, sync room temperature states
            if rows_updated and ('temperature' in updates or 'current_temperature' in updates or 'target_temperature' in updates):
                current_temp = updates.get('current_temperature', updates.get('temperature'))
                target_temp = updates.get('target_temperature', current_temp)
                if current_temp is not None:
                    cursor.execute("""
                        INSERT INTO room_temperature_states (room_id, current_temperature, target_temperature, last_updated)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (room_id) DO UPDATE SET
                            current_temperature = EXCLUDED.current_temperature,
                            target_temperature = COALESCE(EXCLUDED.target_temperature, room_temperature_states.target_temperature),
                            last_updated = EXCLUDED.last_updated
                    """, (room_id, current_temp, target_temp, datetime.now()))

            logger.info(f"Updated device {normalized_id} with fields: {list(updates.keys())}")
            return rows_updated > 0

    def batch_update_devices(self, device_updates: List[Dict], user_id: str) -> Dict:
        """Update multiple devices in a single transaction for optimal performance."""
        if not device_updates:
            return {'updated': [], 'failed': []}

        updated_devices = []
        failed_updates = []

        with self.get_cursor() as cursor:
            try:
                # Start transaction
                cursor.execute("BEGIN")
                
                for update_data in device_updates:
                    if not isinstance(update_data, dict) or 'id' not in update_data:
                        failed_updates.append({'update': update_data, 'error': 'Missing device id'})
                        continue
                        
                    device_id = update_data['id']
                    normalized_id = self._normalize_device_id(device_id)
                    
                    if normalized_id is None:
                        failed_updates.append({'device_id': device_id, 'error': 'Invalid device id'})
                        continue
                        
                    try:
                        # Verify user has access to this device
                        cursor.execute("""
                            SELECT d.room_id, r.home_id
                            FROM devices d
                            LEFT JOIN rooms r ON d.room_id = r.id
                            LEFT JOIN user_homes uh ON r.home_id = uh.home_id
                            WHERE d.id = %s AND (uh.user_id = %s OR d.room_id IS NULL)
                        """, (normalized_id, user_id))
                        
                        row = cursor.fetchone()
                        if not row:
                            failed_updates.append({'device_id': device_id, 'error': 'No permission or device not found'})
                            continue
                            
                        room_id, home_id = row
                        
                        # If device has no room, we'll need to validate permission on target room during update
                        if home_id and not self.user_has_home_permission(user_id, home_id, 'control_devices'):
                            failed_updates.append({'device_id': device_id, 'error': 'No permission to access device'})
                            continue
                        
                        # Build update query
                        update_fields = []
                        update_values = []
                        
                        allowed_fields = ['name', 'state', 'brightness', 'color', 'temperature', 'current_temperature', 
                                        'target_temperature', 'mode', 'action', 'target_device_id', 'enabled', 'room_id', 'display_order']
                        
                        for field, value in update_data.items():
                            if field in allowed_fields and field != 'id':
                                if field == 'room_id':
                                    # Validate new room exists and user has access
                                    if value is not None:
                                        cursor.execute("SELECT home_id FROM rooms WHERE id = %s", (value,))
                                        room_row = cursor.fetchone()
                                        if not room_row:
                                            failed_updates.append({'device_id': device_id, 'error': f'Room {value} not found'})
                                            break
                                        new_room_home_id = room_row[0]
                                        if not self.user_has_home_permission(user_id, new_room_home_id, 'manage_devices'):
                                            failed_updates.append({'device_id': device_id, 'error': 'No permission to move device to target room'})
                                            break
                                    update_fields.append(f"{field} = %s")
                                    update_values.append(value)
                                else:
                                    update_fields.append(f"{field} = %s")
                                    update_values.append(value)
                        
                        if not update_fields:
                            failed_updates.append({'device_id': device_id, 'error': 'No valid update fields'})
                            continue
                            
                        update_fields.append("updated_at = %s")
                        update_values.append(datetime.now())
                        update_values.append(normalized_id)

                        cursor.execute(f"""
                            UPDATE devices 
                            SET {', '.join(update_fields)}
                            WHERE id = %s
                        """, update_values)

                        if cursor.rowcount > 0:
                            updated_devices.append(str(normalized_id))
                            logger.info(f"Batch updated device {normalized_id} with fields: {[f for f in update_data.keys() if f != 'id']}")
                        else:
                            failed_updates.append({'device_id': device_id, 'error': 'No rows updated'})
                            
                    except Exception as device_error:
                        failed_updates.append({'device_id': device_id, 'error': str(device_error)})
                        logger.error(f"Error updating device {device_id} in batch: {device_error}")
                        continue
                
                # Commit transaction
                cursor.execute("COMMIT")
                logger.info(f"Batch update completed: {len(updated_devices)} updated, {len(failed_updates)} failed")
                return {'updated': updated_devices, 'failed': failed_updates}
                
            except Exception as e:
                # Rollback on any error
                cursor.execute("ROLLBACK")
                logger.error(f"Batch update transaction failed: {e}")
                raise e

    def delete_device(self, device_id: Any, user_id: str, home_id: Optional[str] = None) -> bool:
        """Delete a device if the user has permission within the target home."""
        normalized_id = self._normalize_device_id(device_id)
        if normalized_id is None:
            return False

        normalized_home_id = self._normalize_home_id(home_id)

        with self.get_cursor() as cursor:
            # First check if device exists and get its home context
            cursor.execute("""
                SELECT r.home_id
                FROM devices d
                LEFT JOIN rooms r ON d.room_id = r.id
                WHERE d.id = %s
            """, (normalized_id,))

            row = cursor.fetchone()
            if not row:
                return False

            # For unassigned devices (room_id NULL), use passed home_id
            device_home_id = self._normalize_home_id(row[0]) or normalized_home_id
            if not device_home_id:
                return False

            if not self.user_has_home_permission(user_id, device_home_id, 'manage_devices'):
                return False

            cursor.execute("DELETE FROM devices WHERE id = %s", (normalized_id,))
            return cursor.rowcount > 0

    def get_device(self, device_id: Any, user_id: str) -> Optional[Dict]:
        """Get device details if user has access."""
        normalized_id = self._normalize_device_id(device_id)
        if normalized_id is None:
            return None
        with self.get_cursor() as cursor:
            # Query to find device in any home user has access to
            cursor.execute("""
                SELECT DISTINCT
                    d.id,
                    d.name,
                    d.room_id,
                    d.device_type,
                    d.state,
                    d.temperature,
                    d.min_temperature,
                    d.max_temperature,
                    d.display_order,
                    d.enabled,
                    d.settings,
                    d.created_at,
                    d.updated_at,
                    r.home_id,
                    r.name AS room_name
                FROM devices d
                LEFT JOIN rooms r ON d.room_id = r.id
                LEFT JOIN user_homes uh ON r.home_id = uh.home_id
                WHERE d.id = %s AND (uh.user_id = %s OR r.home_id IS NULL)
            """, (normalized_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return {
                'id': row[0],          # id
                'name': row[1],        # name
                'room_id': row[2],     # room_id
                'type': row[3],        # device_type
                'state': row[4],       # state
                'temperature': row[5], # temperature
                'min_temperature': row[6],  # min_temperature
                'max_temperature': row[7],  # max_temperature
                'display_order': row[8],    # display_order
                'enabled': row[9],     # enabled
                'settings': row[10],   # settings
                'created_at': row[11], # created_at
                'updated_at': row[12], # updated_at
                'home_id': row[13],    # home_id
                'room_name': row[14]   # room_name
            }

    # ============================================================================
    # USER AND SESSION MANAGEMENT
    # ============================================================================

    def get_user_current_home(self, user_id: str) -> Optional[int]:
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

    def set_user_current_home(self, user_id: str, home_id: str, session_token: Optional[str] = None) -> bool:
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

    def get_lights(self, home_id: str, user_id: str) -> List[Dict]:
        """Get all lights in a home."""
        return self.get_home_devices(home_id, user_id, 'light')

    def get_temperature_controls(self, home_id: str, user_id: str) -> List[Dict]:
        """Get all temperature controls in a home."""
        return self.get_home_devices(home_id, user_id, 'temperature_control')

    def get_buttons(self, home_id: str, user_id: str) -> List[Dict]:
        """Get all buttons in a home."""
        return self.get_home_devices(home_id, user_id, 'button')
    
    # ============================================================================
    # SYSTEM ADMINISTRATION
    # ============================================================================
    
    def upgrade_user_to_sys_admin(self, user_id: str) -> bool:
        """Upgrade a user to system administrator. Can only be done via direct database access."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET role = 'sys-admin', updated_at = %s
                WHERE id = %s AND role = 'admin'
            """, (datetime.now(), user_id))
            
            if cursor.rowcount > 0:
                logger.info(f"User {user_id} upgraded to sys-admin")
                return True
            return False
            
    def get_sys_admin_users(self) -> List[Dict]:
        """Get all system administrators. Internal use only."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, email, created_at, updated_at
                FROM users 
                WHERE role = 'sys-admin'
                ORDER BY created_at
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': str(row[0]),
                    'name': row[1],
                    'email': row[2],
                    'created_at': row[3],
                    'updated_at': row[4]
                })
            return users

    def get_all_users(self) -> List[Dict]:
        """Get all users in the system. For sys-admin use only."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.id, 
                    u.name, 
                    u.email, 
                    u.role, 
                    u.created_at,
                    u.profile_picture,
                    COUNT(DISTINCT uh.home_id) as home_count
                FROM users u
                LEFT JOIN user_homes uh ON u.id = uh.user_id
                GROUP BY u.id, u.name, u.email, u.role, u.created_at, u.profile_picture
                ORDER BY u.created_at DESC
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': str(row[0]),
                    'name': row[1],
                    'email': row[2],
                    'role': row[3],
                    'created_at': row[4],
                    'profile_picture': row[5],
                    'home_count': row[6] or 0
                })
            return users

    # ============================================================================
    # SECURITY MANAGEMENT
    # ============================================================================

    def _user_can_control_security(self, user_id: str, home_id: str) -> bool:
        """Check whether user has permissions to control security in a home."""
        # Owners/admins are covered by permission check in user_has_home_permission
        # Try specific permission first, then fall back to device control permissions
        return (
            self.user_has_home_permission(user_id, home_id, 'control_security') or
            self.user_has_home_permission(user_id, home_id, 'manage_security') or
            self.user_has_home_permission(user_id, home_id, 'manage_devices') or
            self.user_has_home_permission(user_id, home_id, 'control_devices')
        )

    def get_security_state(self, home_id: Any, user_id: str, default: str = "Wyłączony") -> str:
        """Get the security state for a specific home, initializing defaults if needed."""
        normalized_home_id = self._normalize_home_id(home_id)
        if not normalized_home_id or not user_id:
            return default

        if not self.user_has_home_access(user_id, normalized_home_id):
            raise PermissionError("User doesn't have access to this home")

        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT state
                FROM home_security_states
                WHERE home_id = %s
                """,
                (normalized_home_id,)
            )
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]

            # Initialize default state if missing
            cursor.execute(
                """
                INSERT INTO home_security_states (home_id, state, last_changed)
                VALUES (%s, %s, %s)
                ON CONFLICT (home_id) DO NOTHING
                """,
                (normalized_home_id, default, datetime.now())
            )

        return default

    def set_security_state(self, home_id: Any, user_id: str, state: str, details: Optional[Dict] = None) -> bool:
        """Set the security state for a specific home."""
        normalized_home_id = self._normalize_home_id(home_id)
        if not normalized_home_id:
            raise ValueError("home_id is required")

        if state not in ("Załączony", "Wyłączony"):
            raise ValueError("Invalid security state")

        if not self.user_has_home_access(user_id, normalized_home_id):
            raise PermissionError("User doesn't have access to this home")

        if not self._user_can_control_security(user_id, normalized_home_id):
            return False

        payload_details = json.dumps(details) if details else None

        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO home_security_states (home_id, state, last_changed, changed_by, details)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (home_id) DO UPDATE SET
                    state = EXCLUDED.state,
                    last_changed = EXCLUDED.last_changed,
                    changed_by = EXCLUDED.changed_by,
                    details = CASE
                        WHEN EXCLUDED.details IS NOT NULL THEN EXCLUDED.details
                        ELSE home_security_states.details
                    END
                """,
                (normalized_home_id, state, datetime.now(), user_id, payload_details)
            )

        return True

    # ============================================================================
    # AUTOMATION MANAGEMENT
    # ============================================================================

    def get_home_automations(self, home_id: Any, user_id: str) -> List[Dict]:
        """Retrieve automations for a specific home accessible by the user."""
        normalized_home_id = self._normalize_home_id(home_id)
        if not normalized_home_id or not user_id:
            return []

        if not self.user_has_home_access(user_id, normalized_home_id):
            raise PermissionError("User doesn't have access to this home")

        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, trigger_config, actions_config, enabled,
                       execution_count, last_executed, error_count
                FROM home_automations
                WHERE home_id = %s
                ORDER BY name
                """,
                (normalized_home_id,)
            )
            rows = cursor.fetchall() or []

        automations: List[Dict] = []
        for row in rows:
            trigger_cfg = row[2]
            actions_cfg = row[3]

            if isinstance(trigger_cfg, str):
                try:
                    trigger_cfg = json.loads(trigger_cfg)
                except json.JSONDecodeError:
                    trigger_cfg = {}
            elif trigger_cfg is None:
                trigger_cfg = {}

            if isinstance(actions_cfg, str):
                try:
                    actions_cfg = json.loads(actions_cfg)
                except json.JSONDecodeError:
                    actions_cfg = []
            elif actions_cfg is None:
                actions_cfg = []

            if not isinstance(trigger_cfg, dict):
                trigger_cfg = {}
            if not isinstance(actions_cfg, list):
                if isinstance(actions_cfg, dict):
                    actions_cfg = list(actions_cfg.values())
                else:
                    actions_cfg = []

            last_executed = row[6]
            automations.append({
                'id': str(row[0]) if row[0] is not None else None,
                'home_id': normalized_home_id,
                'name': row[1],
                'trigger': trigger_cfg,
                'actions': actions_cfg,
                'enabled': bool(row[4]),
                'execution_count': row[5] or 0,
                'last_executed': last_executed.isoformat() if last_executed and hasattr(last_executed, 'isoformat') else None,
                'error_count': row[7] or 0
            })

        return automations

    def add_home_automation(self, home_id: Any, user_id: str, automation: Dict) -> Dict:
        """Create a new automation within a home."""
        normalized_home_id = self._normalize_home_id(home_id)
        if not normalized_home_id or not user_id:
            raise ValueError("home_id and user_id are required")

        if not self.user_has_home_access(user_id, normalized_home_id):
            raise PermissionError("User doesn't have access to this home")

        if not self._can_manage_automations(user_id, normalized_home_id):
            raise PermissionError("User lacks permissions to manage automations in this home")

        name_clean = self._normalize_automation_name(automation.get('name'))
        trigger_cfg = automation.get('trigger') or {}
        actions_cfg = automation.get('actions') or []
        enabled = bool(automation.get('enabled', True))

        automation_id = str(uuid.uuid4())

        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO home_automations (
                        id, home_id, name, name_normalized, trigger_config,
                        actions_config, enabled, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, NOW(), NOW())
                    """,
                    (
                        automation_id,
                        normalized_home_id,
                        name_clean,
                        name_clean.casefold(),
                        json.dumps(trigger_cfg),
                        json.dumps(actions_cfg),
                        enabled
                    )
                )
        except errors.UniqueViolation as exc:
            logger.warning("Duplicate automation name for home %s: %s", normalized_home_id, name_clean)
            raise ValueError("Automatyzacja o tej nazwie już istnieje w tym domu") from exc

        return {
            'id': automation_id,
            'home_id': normalized_home_id,
            'name': name_clean,
            'trigger': trigger_cfg,
            'actions': actions_cfg,
            'enabled': enabled,
            'execution_count': 0,
            'last_executed': None,
            'error_count': 0
        }

    def update_home_automation(self, home_id: Any, user_id: str, automation_id: Any, updates: Dict) -> bool:
        """Update an existing automation within a home."""
        normalized_home_id = self._normalize_home_id(home_id)
        if not normalized_home_id or not user_id or not automation_id:
            raise ValueError("home_id, user_id and automation_id are required")

        automation_id = str(automation_id)

        if not self.user_has_home_access(user_id, normalized_home_id):
            raise PermissionError("User doesn't have access to this home")

        if not self._can_manage_automations(user_id, normalized_home_id):
            raise PermissionError("User lacks permissions to manage automations in this home")

        set_clauses: List[str] = []
        params: List[Any] = []

        if 'name' in updates:
            name_clean = self._normalize_automation_name(updates.get('name'))
            set_clauses.append("name = %s")
            params.append(name_clean)
            set_clauses.append("name_normalized = %s")
            params.append(name_clean.casefold())

        if 'trigger' in updates:
            trigger_cfg = updates.get('trigger') or {}
            set_clauses.append("trigger_config = %s::jsonb")
            params.append(json.dumps(trigger_cfg))

        if 'actions' in updates:
            actions_cfg = updates.get('actions') or []
            set_clauses.append("actions_config = %s::jsonb")
            params.append(json.dumps(actions_cfg))

        if 'enabled' in updates:
            set_clauses.append("enabled = %s")
            params.append(bool(updates.get('enabled')))

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")

        query = f"""
            UPDATE home_automations
            SET {', '.join(set_clauses)}
            WHERE id = %s AND home_id = %s
        """

        params.extend([automation_id, normalized_home_id])

        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, tuple(params))
                return cursor.rowcount > 0
        except errors.UniqueViolation as exc:
            logger.warning("Duplicate automation name during update for home %s: %s", normalized_home_id, updates.get('name'))
            raise ValueError("Automatyzacja o tej nazwie już istnieje w tym domu") from exc

    def delete_home_automation(self, home_id: Any, user_id: str, automation_id: Any) -> bool:
        """Delete an automation from a home."""
        normalized_home_id = self._normalize_home_id(home_id)
        if not normalized_home_id or not user_id or not automation_id:
            raise ValueError("home_id, user_id and automation_id są wymagane")

        automation_id = str(automation_id)

        if not self.user_has_home_access(user_id, normalized_home_id):
            raise PermissionError("User doesn't have access to this home")

        if not self._can_manage_automations(user_id, normalized_home_id):
            raise PermissionError("User lacks permissions to manage automations in this home")

        with self.get_cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM home_automations
                WHERE id = %s AND home_id = %s
                """,
                (automation_id, normalized_home_id)
            )
            return cursor.rowcount > 0

    # ============================================================================
    # USER MANAGEMENT (for registration, authentication, password management)
    # ============================================================================

    def create_user(self, username: str, email: str, password_hash: str, 
                   role: str = 'user', create_default_home: bool = True) -> Tuple[str, Optional[str]]:
        """
        Create a new user and optionally create their default home.
        
        Args:
            username: User's username (must be unique)
            email: User's email address (must be unique) 
            password_hash: Pre-hashed password
            role: Global user role ('user', 'admin', 'sys-admin')
            create_default_home: Whether to create a default home for the user
            
        Returns:
            Tuple of (user_id, home_id) where home_id is None if no home was created
            
        Raises:
            ValueError: If username or email already exists
        """
        with self.get_cursor() as cursor:
            try:
                # Check if username already exists
                cursor.execute("SELECT id FROM users WHERE name = %s", (username,))
                if cursor.fetchone():
                    raise ValueError("Użytkownik o tej nazwie już istnieje")
                
                # Check if email already exists  
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    raise ValueError("Adres email jest już używany")
                
                # Create user
                user_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO users (id, name, email, password_hash, role, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, username, email, password_hash, role, datetime.now(), datetime.now()))
                
                home_id = None
                if create_default_home:
                    # Create default home for user (they become owner of their own home)
                    home_name = f"{username} Home"
                    
                    # Ensure unique home name
                    counter = 1
                    original_name = home_name
                    while True:
                        cursor.execute("SELECT id FROM homes WHERE name = %s AND owner_id = %s", (home_name, user_id))
                        if not cursor.fetchone():
                            break
                        counter += 1
                        home_name = f"{original_name} {counter}"
                    
                    # Create the home
                    home_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO homes (id, name, owner_id, description, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (home_id, home_name, user_id, f"Domyślny dom użytkownika {username}", datetime.now(), datetime.now()))
                    
                    # Add user to their home with owner role (home creators become owners)
                    cursor.execute("""
                        INSERT INTO user_homes (user_id, home_id, role, permissions, joined_at)
                        VALUES (%s, %s, 'owner', %s, %s)
                    """, (user_id, home_id, json.dumps(['full_control']), datetime.now()))
                    
                    # Set as user's default home
                    cursor.execute("""
                        UPDATE users SET default_home_id = %s WHERE id = %s
                    """, (home_id, user_id))
                
                logger.info(f"Created user '{username}' with ID {user_id}" + 
                          (f" and default home {home_id}" if home_id else ""))
                
                return user_id, home_id
                
            except Exception as e:
                logger.error(f"Error creating user '{username}': {e}")
                raise

    def find_user_by_email_or_username(self, identifier: str) -> Optional[Dict]:
        """
        Find user by email address or username.
        
        Args:
            identifier: Email address or username to search for
            
        Returns:
            User dict with keys: id, name, email, password_hash, role, etc.
            Returns None if user not found
        """
        with self.get_cursor() as cursor:
            # First try by email
            cursor.execute("""
                SELECT id, name, email, password_hash, role, default_home_id, 
                       created_at, updated_at
                FROM users 
                WHERE email = %s
            """, (identifier,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': str(row[0]),
                    'name': row[1], 
                    'email': row[2],
                    'password_hash': row[3],
                    'role': row[4],
                    'default_home_id': str(row[5]) if row[5] else None,
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            
            # If not found by email, try by username
            cursor.execute("""
                SELECT id, name, email, password_hash, role, default_home_id,
                       created_at, updated_at
                FROM users 
                WHERE name = %s
            """, (identifier,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': str(row[0]),
                    'name': row[1],
                    'email': row[2], 
                    'password_hash': row[3],
                    'role': row[4],
                    'default_home_id': str(row[5]) if row[5] else None,
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            
            return None

    def verify_user_password(self, user_id: str, password_hash: str) -> bool:
        """
        Verify user's password hash matches stored hash.
        
        Args:
            user_id: User's ID
            password_hash: Hashed password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT password_hash FROM users WHERE id = %s
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return row[0] == password_hash
            return False

    def update_user_password(self, user_id: str, new_password_hash: str) -> bool:
        """
        Update user's password.
        
        Args:
            user_id: User's ID
            new_password_hash: New hashed password
            
        Returns:
            True if password was updated, False if user not found
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s, updated_at = %s
                WHERE id = %s
            """, (new_password_hash, datetime.now(), user_id))
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated password for user {user_id}")
            return success
            
    def update_user(self, user_id: str, updates: dict) -> bool:
        """
        Update user profile data.
        
        Args:
            user_id: User's ID
            updates: Dict of fields to update (name, email, profile_picture, etc.)
            
        Returns:
            True if user was updated, False if user not found
        """
        if not updates:
            return False
            
        # Build dynamic update query
        valid_fields = {'name', 'email', 'profile_picture', 'timezone', 'language'}
        update_fields = {k: v for k, v in updates.items() if k in valid_fields}
        
        if not update_fields:
            return False
            
        set_clause = ', '.join([f"{field} = %s" for field in update_fields.keys()])
        values = list(update_fields.values())
        values.extend([datetime.now(), user_id])  # updated_at, WHERE user_id
        
        with self.get_cursor() as cursor:
            cursor.execute(f"""
                UPDATE users 
                SET {set_clause}, updated_at = %s
                WHERE id = %s
            """, values)
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated user {user_id} fields: {list(update_fields.keys())}")
            return success

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Get user details by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User dict or None if not found
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, email, password_hash, role, default_home_id,
                       profile_picture, timezone, language, created_at, updated_at
                FROM users 
                WHERE id = %s
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': str(row[0]),
                    'name': row[1],
                    'email': row[2],
                    'password_hash': row[3], 
                    'role': row[4],
                    'default_home_id': str(row[5]) if row[5] else None,
                    'profile_picture': row[6] or '',
                    'timezone': row[7] or 'UTC',
                    'language': row[8] or 'pl',
                    'created_at': row[9],
                    'updated_at': row[10]
                }
            return None

    def get_user_data(self, user_id: str) -> Optional[Dict]:
        """
        Get user data by ID (alias for compatibility).
        Returns format compatible with SmartHomeSystem.
        
        Args:
            user_id: User's ID
            
        Returns:
            User dict with user_id field or None if not found
        """
        user = self.get_user_by_id(user_id)
        if user:
            # Add user_id alias for compatibility
            user['user_id'] = user['id']
        return user

    def check_user_exists(self, username: Optional[str] = None, email: Optional[str] = None) -> bool:
        """
        Check if user exists by username or email.
        
        Args:
            username: Username to check (optional)
            email: Email to check (optional)
            
        Returns:
            True if user exists, False otherwise
        """
        with self.get_cursor() as cursor:
            if username:
                cursor.execute("SELECT 1 FROM users WHERE name = %s", (username,))
                if cursor.fetchone():
                    return True
            
            if email:
                cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return True
                    
            return False

    # ============================================================================
    # HOME INVITATIONS MANAGEMENT
    # ============================================================================

    def create_invitation(self, home_id: str, email: str, role: str, invited_by: str) -> str:
        """
        Create a new home invitation.
        
        Args:
            home_id: ID of the home
            email: Email address to invite
            role: Role to assign (admin, member, guest)
            invited_by: User ID of the inviter
            
        Returns:
            Invitation code
        """
        import secrets
        
        # Validate role
        if role not in ['admin', 'member', 'guest']:
            raise ValueError(f"Invalid role: {role}")
        
        # Check admin access
        if not self.has_admin_access(invited_by, home_id):
            raise PermissionError("User doesn't have admin access to this home")
        
        # Generate unique invitation code (8 characters, alphanumeric)
        invitation_code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        
        # Set expiration (7 days from now)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        with self.get_cursor() as cursor:
            # Check if there's already a pending invitation for this email in this home
            cursor.execute("""
                SELECT id FROM home_invitations 
                WHERE home_id = %s AND email = %s AND status = 'pending'
            """, (home_id, email))
            
            if cursor.fetchone():
                raise ValueError("An invitation for this email already exists for this home")
            
            # Check if user with this email already exists in the system
            cursor.execute("""
                SELECT id, name FROM users WHERE LOWER(email) = LOWER(%s)
            """, (email,))
            existing_user = cursor.fetchone()
            
            existing_user_id = None
            if existing_user:
                existing_user_id = str(existing_user[0])
                existing_username = existing_user[1]
                
                # Check if user is already in this home
                cursor.execute("""
                    SELECT 1 FROM user_homes WHERE user_id = %s AND home_id = %s
                """, (existing_user_id, home_id))
                if cursor.fetchone():
                    raise ValueError(f"Użytkownik {existing_username} już należy do tego domu")
                
                logger.info(f"Invitation for existing user {existing_username} ({email})")
            
            # Create invitation
            invitation_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO home_invitations 
                (id, home_id, email, role, invitation_code, invited_by, expires_at, accepted_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (invitation_id, home_id, email.lower(), role, invitation_code, invited_by, expires_at, existing_user_id))
            
            logger.info(f"Created invitation {invitation_code} for {email} to home {home_id}")
            return invitation_code

    def get_invitation(self, invitation_code: str) -> Optional[Dict]:
        """
        Get invitation details by code.
        
        Args:
            invitation_code: The invitation code
            
        Returns:
            Dictionary with invitation details or None if not found
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT i.id, i.home_id, i.email, i.role, i.invitation_code, 
                       i.invited_by, i.created_at, i.expires_at, i.status,
                       h.name as home_name, inviter.name as inviter_name,
                       i.accepted_by, existing_user.name as existing_username
                FROM home_invitations i
                JOIN homes h ON i.home_id = h.id
                JOIN users inviter ON i.invited_by = inviter.id
                LEFT JOIN users existing_user ON i.accepted_by = existing_user.id
                WHERE i.invitation_code = %s
            """, (invitation_code,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': str(row[0]),
                    'home_id': str(row[1]),
                    'email': row[2],
                    'role': row[3],
                    'invitation_code': row[4],
                    'invited_by': str(row[5]),
                    'created_at': row[6],
                    'expires_at': row[7],
                    'status': row[8],
                    'home_name': row[9],
                    'inviter_name': row[10],
                    'existing_user_id': str(row[11]) if row[11] else None,
                    'existing_username': row[12] if row[12] else None
                }
            return None

    def accept_invitation(self, invitation_code: str, user_id: str, username: Optional[str] = None) -> bool:
        """
        Accept a home invitation and add user to home.
        
        Args:
            invitation_code: The invitation code
            user_id: ID of the user accepting the invitation  
            username: Optional username for new users (ignored if user exists)
            
        Returns:
            True if successful
        """
        with self.get_cursor() as cursor:
            # Get invitation with user check
            cursor.execute("""
                SELECT i.id, i.home_id, i.email, i.role, i.status, i.expires_at, i.accepted_by,
                       u.name as existing_username
                FROM home_invitations i
                LEFT JOIN users u ON i.accepted_by = u.id
                WHERE i.invitation_code = %s
            """, (invitation_code,))
            
            invitation = cursor.fetchone()
            if not invitation:
                raise ValueError("Invalid invitation code")
            
            inv_id, home_id, email, role, status, expires_at, existing_user_id, existing_username = invitation
            
            # Check status
            if status != 'pending':
                raise ValueError(f"Invitation is {status}")
            
            # Check expiration
            if datetime.now(timezone.utc) > expires_at:
                cursor.execute("""
                    UPDATE home_invitations 
                    SET status = 'expired' 
                    WHERE id = %s
                """, (str(inv_id),))
                raise ValueError("Invitation has expired")
            
            # Verify email matches user
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            user_row = cursor.fetchone()
            if not user_row or user_row[0].lower() != email.lower():
                raise ValueError("This invitation is for a different email address")
            
            # Check if user is already in this home
            cursor.execute("""
                SELECT 1 FROM user_homes 
                WHERE user_id = %s AND home_id = %s
            """, (user_id, home_id))
            
            if cursor.fetchone():
                # Mark as accepted even though already a member
                cursor.execute("""
                    UPDATE home_invitations 
                    SET status = 'accepted', accepted_at = %s, accepted_by = %s 
                    WHERE id = %s
                """, (datetime.now(timezone.utc), user_id, str(inv_id)))
                raise ValueError("You are already a member of this home")
            
            # Add user to home
            cursor.execute("""
                INSERT INTO user_homes (user_id, home_id, role, joined_at)
                VALUES (%s, %s, %s, %s)
            """, (user_id, home_id, role, datetime.now(timezone.utc)))
            
            # Mark invitation as accepted
            cursor.execute("""
                UPDATE home_invitations 
                SET status = 'accepted', accepted_at = %s, accepted_by = %s 
                WHERE id = %s
            """, (datetime.now(timezone.utc), user_id, str(inv_id)))
            
            logger.info(f"User {user_id} accepted invitation {invitation_code} to home {home_id}")
            return True

    def get_pending_invitations(self, home_id: str, admin_user_id: str) -> List[Dict]:
        """
        Get all pending invitations for a home.
        
        Args:
            home_id: ID of the home
            admin_user_id: ID of the admin requesting the list
            
        Returns:
            List of pending invitations
        """
        # Check admin access
        if not self.has_admin_access(admin_user_id, home_id):
            raise PermissionError("User doesn't have admin access to this home")
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT i.id, i.email, i.role, i.invitation_code, 
                       i.created_at, i.expires_at, u.name as inviter_name
                FROM home_invitations i
                JOIN users u ON i.invited_by = u.id
                WHERE i.home_id = %s AND i.status = 'pending'
                ORDER BY i.created_at DESC
            """, (home_id,))
            
            invitations = []
            for row in cursor.fetchall():
                invitations.append({
                    'id': str(row[0]),
                    'email': row[1],
                    'role': row[2],
                    'invitation_code': row[3],
                    'created_at': row[4],
                    'expires_at': row[5],
                    'inviter_name': row[6]
                })
            
            return invitations

    def cancel_invitation(self, invitation_id: str, admin_user_id: str) -> bool:
        """
        Cancel a pending invitation.
        
        Args:
            invitation_id: ID of the invitation
            admin_user_id: ID of the admin canceling
            
        Returns:
            True if successful
        """
        with self.get_cursor() as cursor:
            # Get invitation and check permissions
            cursor.execute("""
                SELECT home_id, status FROM home_invitations WHERE id = %s
            """, (invitation_id,))
            
            row = cursor.fetchone()
            if not row:
                raise ValueError("Invitation not found")
            
            home_id, status = row
            
            if not self.has_admin_access(admin_user_id, str(home_id)):
                raise PermissionError("User doesn't have admin access to this home")
            
            if status != 'pending':
                raise ValueError(f"Cannot cancel {status} invitation")
            
            # Cancel invitation
            cursor.execute("""
                UPDATE home_invitations 
                SET status = 'rejected' 
                WHERE id = %s
            """, (invitation_id,))
            
            logger.info(f"Admin {admin_user_id} cancelled invitation {invitation_id}")
            return True
    
    def leave_home(self, user_id: str, home_id: str) -> bool:
        """
        Allow a user to leave a home they are a member of.
        Owner cannot leave their own home.
        
        Args:
            user_id: ID of the user leaving
            home_id: ID of the home to leave
            
        Returns:
            True if successful
            
        Raises:
            PermissionError: If user is the owner or sys-admin
            ValueError: If user is not a member or other validation error
        """
        with self.get_cursor() as cursor:
            # Check if user is a member of this home
            cursor.execute("""
                SELECT role FROM user_homes 
                WHERE user_id = %s AND home_id = %s
            """, (user_id, home_id))
            
            row = cursor.fetchone()
            if not row:
                raise ValueError("You are not a member of this home")
            
            user_role = row[0]
            
            # Check if user is the owner
            cursor.execute("""
                SELECT owner_id FROM homes WHERE id = %s
            """, (home_id,))
            
            owner_row = cursor.fetchone()
            if owner_row and str(owner_row[0]) == user_id:
                raise PermissionError("Owner cannot leave their own home. Transfer ownership or delete the home instead.")
            
            # Get user's global role
            cursor.execute("""
                SELECT role FROM users WHERE id = %s
            """, (user_id,))
            
            global_role_row = cursor.fetchone()
            if global_role_row and global_role_row[0] == 'sys-admin':
                raise PermissionError("System administrators cannot leave homes. Contact another admin.")
            
            # Remove user from home
            cursor.execute("""
                DELETE FROM user_homes 
                WHERE user_id = %s AND home_id = %s
            """, (user_id, home_id))
            
            # Note: current_home_id is managed in session, not in database
            # The API endpoint will clear it from session if needed
            
            logger.info(f"User {user_id} left home {home_id}")
            return True
    



