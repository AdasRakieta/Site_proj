#!/usr/bin/env python3
"""
Simple migration script without Unicode characters for Windows compatibility
"""

import json
import os
import sys
import psycopg2
import uuid
from datetime import datetime
import argparse

class SimpleMigrator:
    def __init__(self):
        self.config = {
            'host': '192.168.1.219',
            'port': 5432,
            'database': 'admin',
            'user': 'admin',
            'password': 'Qwuizzy123.'
        }
        self.conn = None
        self.dry_run = False
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**self.config)
            print("[OK] Connected to database")
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False
    
    def load_json_file(self, filename, default=None):
        """Load JSON file with encoding detection"""
        if not os.path.exists(filename):
            print(f"[WARNING] File {filename} not found")
            return default or {}
        
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'cp1250', 'latin1']
        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    data = json.load(f)
                    print(f"[OK] Loaded {filename} with {encoding}")
                    return data
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON error in {filename}: {e}")
                return default or {}
        
        print(f"[ERROR] Could not decode {filename}")
        return default or {}
    
    def migrate_users(self, config_data):
        """Migrate users from JSON to database"""
        print("[MIGRATE] Processing users...")
        
        users = config_data.get('users', {})
        if not users:
            print("[WARNING] No users found in config")
            return True
        
        try:
            with self.conn.cursor() as cur:
                for username, user_data in users.items():
                    user_id = str(uuid.uuid4())
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO users (id, name, email, password_hash, role, profile_picture)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (name) DO UPDATE SET
                                email = EXCLUDED.email,
                                password_hash = EXCLUDED.password_hash,
                                role = EXCLUDED.role,
                                profile_picture = EXCLUDED.profile_picture
                        """, (
                            user_id,
                            username,
                            user_data.get('email', f"{username}@local.home"),
                            user_data.get('password', ''),
                            user_data.get('role', 'user'),
                            user_data.get('profile_picture', '')
                        ))
                    
                    print(f"  [USER] {username} -> {user_id}")
            
            if not self.dry_run:
                self.conn.commit()
            
            print(f"[OK] Migrated {len(users)} users")
            return True
            
        except Exception as e:
            print(f"[ERROR] User migration failed: {e}")
            if not self.dry_run:
                self.conn.rollback()
            return False
    
    def migrate_rooms(self, config_data):
        """Migrate rooms from JSON to database"""
        print("[MIGRATE] Processing rooms...")
        
        rooms = config_data.get('rooms', [])
        if not rooms:
            print("[WARNING] No rooms found in config")
            return True
        
        try:
            with self.conn.cursor() as cur:
                for i, room_name in enumerate(rooms):
                    room_id = str(uuid.uuid4())
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO rooms (id, name, display_order)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (name) DO UPDATE SET
                                display_order = EXCLUDED.display_order
                        """, (
                            room_id,
                            room_name,
                            i
                        ))
                    
                    print(f"  [ROOM] {room_name} -> {room_id}")
            
            if not self.dry_run:
                self.conn.commit()
            
            print(f"[OK] Migrated {len(rooms)} rooms")
            return True
            
        except Exception as e:
            print(f"[ERROR] Room migration failed: {e}")
            if not self.dry_run:
                self.conn.rollback()
            return False
    
    def migrate_devices(self, config_data):
        """Migrate devices from JSON to database"""
        print("[MIGRATE] Processing devices...")
        
        # Get room mappings first
        room_mappings = {}
        if not self.dry_run:
            with self.conn.cursor() as cur:
                cur.execute("SELECT name, id FROM rooms")
                room_mappings = {name: room_id for name, room_id in cur.fetchall()}
        else:
            # For dry run, create fake mappings
            rooms = config_data.get('rooms', [])
            for room_name in rooms:
                room_mappings[room_name] = str(uuid.uuid4())
        
        total_devices = 0
        
        # Migrate buttons
        buttons = config_data.get('buttons', [])
        for button in buttons:
            button_name = button.get('name', 'Unknown Button')
            room_name = button.get('room', 'Unknown Room')
            button_id = button.get('id', str(uuid.uuid4()))
            room_id = room_mappings.get(room_name)
            
            if not self.dry_run and room_id:
                with self.conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO devices (id, name, room_id, device_type, state, enabled)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        button_id,
                        button_name,
                        room_id,
                        'button',
                        button.get('state', False),
                        True
                    ))
            
            print(f"  [BUTTON] {room_name}/{button_name} -> {button_id}")
            total_devices += 1
        
        # Migrate temperature controls
        temp_controls = config_data.get('temperature_controls', [])
        for temp_control in temp_controls:
            control_name = temp_control.get('name', 'Unknown Temperature Control')
            room_name = temp_control.get('room', 'Unknown Room')
            control_id = temp_control.get('id', str(uuid.uuid4()))
            room_id = room_mappings.get(room_name)
            
            if not self.dry_run and room_id:
                with self.conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO devices (id, name, room_id, device_type, temperature, min_temperature, max_temperature, enabled)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        control_id,
                        control_name,
                        room_id,
                        'temperature_control',
                        temp_control.get('temperature', 22.0),
                        16.0,  # Default min
                        30.0,  # Default max
                        True
                    ))
            
            print(f"  [TEMP] {room_name}/{control_name} -> {control_id}")
            total_devices += 1
        
        if not self.dry_run:
            self.conn.commit()
        
        print(f"[OK] Migrated {total_devices} devices")
        return True
    
    def migrate_system_settings(self, config_data):
        """Migrate system settings"""
        print("[MIGRATE] Processing system settings...")
        
        settings_map = {
            'security_state': config_data.get('security_state', 'Wyłączony'),
            'auto_save_interval': config_data.get('auto_save_interval', 3000)
        }
        
        try:
            with self.conn.cursor() as cur:
                for key, value in settings_map.items():
                    if not self.dry_run:
                        cur.execute("""
                            UPDATE system_settings 
                            SET setting_value = %s 
                            WHERE setting_key = %s
                        """, (json.dumps(value), key))
                    
                    print(f"  [SETTING] {key} = {value}")
            
            if not self.dry_run:
                self.conn.commit()
            
            print(f"[OK] Migrated {len(settings_map)} settings")
            return True
            
        except Exception as e:
            print(f"[ERROR] Settings migration failed: {e}")
            if not self.dry_run:
                self.conn.rollback()
            return False
    
    def run_migration(self, dry_run=False):
        """Run the complete migration"""
        self.dry_run = dry_run
        
        if dry_run:
            print("[DRY-RUN] Running in dry-run mode - no changes will be made")
        
        # Connect to database
        if not self.connect():
            return False
        
        try:
            # Load configuration
            config_data = self.load_json_file('smart_home_config.json', {})
            
            # Run migrations
            steps = [
                ("users", lambda: self.migrate_users(config_data)),
                ("rooms", lambda: self.migrate_rooms(config_data)),
                ("devices", lambda: self.migrate_devices(config_data)),
                ("settings", lambda: self.migrate_system_settings(config_data)),
            ]
            
            for step_name, step_func in steps:
                print(f"\n[STEP] Migrating {step_name}...")
                if not step_func():
                    print(f"[ERROR] Failed to migrate {step_name}")
                    return False
            
            print("\n[SUCCESS] Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            return False
        
        finally:
            if self.conn:
                self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Simple migration script')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    args = parser.parse_args()
    
    print("=" * 50)
    print("[MIGRATE] SmartHome Data Migration")
    print("=" * 50)
    
    migrator = SimpleMigrator()
    success = migrator.run_migration(dry_run=args.dry_run)
    
    if success:
        print("\n[DONE] Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAILED] Migration failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
