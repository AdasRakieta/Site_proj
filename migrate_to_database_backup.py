#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartHome JSON to PostgreSQL Migration Script
=============================================

This script migrates all data from JSON files to PostgreSQL database.
It handles:
- Users from smart_home_config.json
- Rooms, devices, automations from smart_home_config.json
- Management logs from management_logs.json
- Notification settings from notifications_settings.json
- System settings and temperature states

Usage:
    python migrate_to_database.py [--dry-run] [--force]
"""

import json
import os
import sys
import uuid
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone
import argparse
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': '192.168.1.219',
    'port': 5432,
    'database': 'admin',
    'user': 'admin',
    'password': 'Qwuizzy123.'
}

class SmartHomeMigrator:
    def __init__(self, dry_run=False, force=False):
        self.dry_run = dry_run
        self.force = force
        self.conn = None
        self.home_id = str(uuid.uuid4())  # Generate unique home ID
        
        # File paths
        self.config_file = 'smart_home_config.json'
        self.logs_file = 'management_logs.json'
        self.notifications_file = 'notifications_settings.json'
        
        print(f"Migration mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Force mode: {'ENABLED' if force else 'DISABLED'}")
        print(f"Home ID: {self.home_id}")
        print("-" * 60)

    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            print("✓ Connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            return False

    def load_json_file(self, filename, default=None):
        """Load JSON file with error handling"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✓ Loaded {filename}")
                    return data
            else:
                print(f"⚠ File {filename} not found, using default")
                return default or {}
        except Exception as e:
            print(f"✗ Error loading {filename}: {e}")
            return default or {}

    def check_existing_data(self):
        """Check if data already exists in database"""
        try:
            with self.conn.cursor() as cur:
                # Check if users exist
                cur.execute("SELECT COUNT(*) FROM users")
                user_count = cur.fetchone()[0]
                
                # Check if rooms exist
                cur.execute("SELECT COUNT(*) FROM rooms")
                room_count = cur.fetchone()[0]
                
                # Check if devices exist
                cur.execute("SELECT COUNT(*) FROM devices")
                device_count = cur.fetchone()[0]
                
                if user_count > 0 or room_count > 0 or device_count > 0:
                    print(f"⚠ Existing data found: {user_count} users, {room_count} rooms, {device_count} devices")
                    if not self.force:
                        print("✗ Use --force to overwrite existing data")
                        return False
                    else:
                        print("🔥 Force mode enabled - will overwrite existing data")
                
                return True
        except Exception as e:
            print(f"✗ Error checking existing data: {e}")
            return False

    def clear_existing_data(self):
        """Clear existing data if force mode is enabled"""
        if not self.force:
            return True
            
        try:
            with self.conn.cursor() as cur:
                print("🔥 Clearing existing data...")
                
                # Disable foreign key checks temporarily
                cur.execute("SET session_replication_role = replica;")
                
                # Clear tables in reverse dependency order
                tables = [
                    'automation_executions',
                    'device_history', 
                    'session_tokens',
                    'notification_recipients',
                    'notification_settings',
                    'management_logs',
                    'room_temperature_states',
                    'automations',
                    'devices',
                    'rooms',
                    'system_settings',
                    'users'
                ]
                
                for table in tables:
                    cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                    print(f"  ✓ Cleared {table}")
                
                # Re-enable foreign key checks
                cur.execute("SET session_replication_role = DEFAULT;")
                
                if not self.dry_run:
                    self.conn.commit()
                
                print("✓ All existing data cleared")
                return True
                
        except Exception as e:
            print(f"✗ Error clearing existing data: {e}")
            self.conn.rollback()
            return False

    def migrate_users(self, config_data):
        """Migrate users from JSON to database"""
        print("\n📋 Migrating users...")
        
        users_data = config_data.get('users', {})
        if not users_data:
            print("⚠ No users found in config")
            return True
        
        try:
            with self.conn.cursor() as cur:
                migrated_count = 0
                
                for user_id, user_info in users_data.items():
                    # Validate UUID format
                    try:
                        uuid.UUID(user_id)
                    except ValueError:
                        print(f"⚠ Invalid UUID for user {user_id}, generating new one")
                        user_id = str(uuid.uuid4())
                    
                    user_data = (
                        user_id,
                        user_info.get('name', f'user_{user_id[:8]}'),
                        user_info.get('email', ''),
                        user_info.get('password', ''),
                        user_info.get('role', 'user'),
                        user_info.get('profile_picture', '')
                    )
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO users (id, name, email, password_hash, role, profile_picture)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                email = EXCLUDED.email,
                                password_hash = EXCLUDED.password_hash,
                                role = EXCLUDED.role,
                                profile_picture = EXCLUDED.profile_picture,
                                updated_at = NOW()
                        """, user_data)
                    
                    print(f"  ✓ User: {user_info.get('name', user_id)} ({user_info.get('role', 'user')})")
                    migrated_count += 1
                
                if not self.dry_run:
                    self.conn.commit()
                
                print(f"✓ Migrated {migrated_count} users")
                return True
                
        except Exception as e:
            print(f"✗ Error migrating users: {e}")
            self.conn.rollback()
            return False

    def migrate_rooms(self, config_data):
        """Migrate rooms from JSON to database"""
        print("\n🏠 Migrating rooms...")
        
        rooms_data = config_data.get('rooms', [])
        if not rooms_data:
            print("⚠ No rooms found in config")
            return {}
        
        room_mapping = {}  # Map room names to UUIDs
        
        try:
            with self.conn.cursor() as cur:
                migrated_count = 0
                
                for index, room_name in enumerate(rooms_data):
                    room_id = str(uuid.uuid4())
                    room_mapping[room_name] = room_id
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO rooms (id, name, display_order)
                            VALUES (%s, %s, %s)
                        """, (room_id, room_name, index))
                    
                    print(f"  ✓ Room: {room_name}")
                    migrated_count += 1
                
                if not self.dry_run:
                    self.conn.commit()
                
                print(f"✓ Migrated {migrated_count} rooms")
                return room_mapping
                
        except Exception as e:
            print(f"✗ Error migrating rooms: {e}")
            self.conn.rollback()
            return {}

    def migrate_devices(self, config_data, room_mapping):
        """Migrate buttons and temperature controls to devices table"""
        print("\n🔌 Migrating devices...")
        
        try:
            with self.conn.cursor() as cur:
                migrated_count = 0
                
                # Migrate buttons
                buttons_data = config_data.get('buttons', [])
                for button in buttons_data:
                    device_id = button.get('id') or str(uuid.uuid4())
                    room_id = room_mapping.get(button.get('room'))
                    
                    if not room_id:
                        print(f"⚠ Room '{button.get('room')}' not found for button '{button.get('name')}'")
                        continue
                    
                    device_data = (
                        device_id,
                        button.get('name', 'Unnamed Button'),
                        room_id,
                        'button',
                        button.get('state', False),
                        None,  # temperature
                        16.0,  # min_temperature
                        30.0,  # max_temperature
                        0      # display_order
                    )
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO devices (id, name, room_id, device_type, state, temperature, min_temperature, max_temperature, display_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                room_id = EXCLUDED.room_id,
                                state = EXCLUDED.state,
                                updated_at = NOW()
                        """, device_data)
                    
                    print(f"  ✓ Button: {button.get('name')} in {button.get('room')}")
                    migrated_count += 1
                
                # Migrate temperature controls
                temp_controls_data = config_data.get('temperature_controls', [])
                for temp_control in temp_controls_data:
                    device_id = temp_control.get('id') or str(uuid.uuid4())
                    room_id = room_mapping.get(temp_control.get('room'))
                    
                    if not room_id:
                        print(f"⚠ Room '{temp_control.get('room')}' not found for temperature control '{temp_control.get('name')}'")
                        continue
                    
                    device_data = (
                        device_id,
                        temp_control.get('name', 'Unnamed Thermostat'),
                        room_id,
                        'temperature_control',
                        False,  # state (not used for temperature controls)
                        temp_control.get('temperature', 22.0),
                        16.0,   # min_temperature
                        30.0,   # max_temperature
                        0       # display_order
                    )
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO devices (id, name, room_id, device_type, state, temperature, min_temperature, max_temperature, display_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                room_id = EXCLUDED.room_id,
                                temperature = EXCLUDED.temperature,
                                updated_at = NOW()
                        """, device_data)
                    
                    print(f"  ✓ Thermostat: {temp_control.get('name')} in {temp_control.get('room')} ({temp_control.get('temperature', 22)}°C)")
                    migrated_count += 1
                
                if not self.dry_run:
                    self.conn.commit()
                
                print(f"✓ Migrated {migrated_count} devices")
                return True
                
        except Exception as e:
            print(f"✗ Error migrating devices: {e}")
            self.conn.rollback()
            return False

    def migrate_automations(self, config_data):
        """Migrate automations from JSON to database"""
        print("\n🤖 Migrating automations...")
        
        automations_data = config_data.get('automations', [])
        if not automations_data:
            print("⚠ No automations found in config")
            return True
        
        try:
            with self.conn.cursor() as cur:
                migrated_count = 0
                
                for automation in automations_data:
                    automation_id = str(uuid.uuid4())
                    
                    # Extract trigger and actions
                    trigger_config = automation.get('trigger', {})
                    actions_config = automation.get('actions', [])
                    
                    automation_data = (
                        automation_id,
                        automation.get('name', f'Automation {automation_id[:8]}'),
                        json.dumps(trigger_config),
                        json.dumps(actions_config),
                        automation.get('enabled', True)
                    )
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO automations (id, name, trigger_config, actions_config, enabled)
                            VALUES (%s, %s, %s, %s, %s)
                        """, automation_data)
                    
                    print(f"  ✓ Automation: {automation.get('name')} ({'enabled' if automation.get('enabled', True) else 'disabled'})")
                    migrated_count += 1
                
                if not self.dry_run:
                    self.conn.commit()
                
                print(f"✓ Migrated {migrated_count} automations")
                return True
                
        except Exception as e:
            print(f"✗ Error migrating automations: {e}")
            self.conn.rollback()
            return False

    def migrate_temperature_states(self, config_data, room_mapping):
        """Migrate temperature states from JSON to database"""
        print("\n🌡️ Migrating temperature states...")
        
        temp_states_data = config_data.get('temperature_states', {})
        if not temp_states_data:
            print("⚠ No temperature states found in config")
            return True
        
        try:
            with self.conn.cursor() as cur:
                migrated_count = 0
                
                for room_name, temperature in temp_states_data.items():
                    room_id = room_mapping.get(room_name)
                    
                    if not room_id:
                        print(f"⚠ Room '{room_name}' not found for temperature state")
                        continue
                    
                    temp_state_data = (
                        str(uuid.uuid4()),
                        room_id,
                        float(temperature),
                        float(temperature)  # target same as current initially
                    )
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO room_temperature_states (id, room_id, current_temperature, target_temperature)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (room_id) DO UPDATE SET
                                current_temperature = EXCLUDED.current_temperature,
                                target_temperature = EXCLUDED.target_temperature,
                                last_updated = NOW()
                        """, temp_state_data)
                    
                    print(f"  ✓ Temperature state: {room_name} = {temperature}°C")
                    migrated_count += 1
                
                if not self.dry_run:
                    self.conn.commit()
                
                print(f"✓ Migrated {migrated_count} temperature states")
                return True
                
        except Exception as e:
            print(f"✗ Error migrating temperature states: {e}")
            self.conn.rollback()
            return False

    def migrate_system_settings(self, config_data):
        """Migrate system settings"""
        print("\n⚙️ Migrating system settings...")
        
        try:
            with self.conn.cursor() as cur:
                migrated_count = 0
                
                # Security state
                security_state = config_data.get('security_state', 'Nieznany')
                if not self.dry_run:
                    cur.execute("""
                        INSERT INTO system_settings (setting_key, setting_value, description)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (setting_key) DO UPDATE SET
                            setting_value = EXCLUDED.setting_value,
                            updated_at = NOW()
                    """, ('security_state', json.dumps(security_state), 'Current security system state'))
                
                print(f"  ✓ Security state: {security_state}")
                migrated_count += 1
                
                # Auto-save interval (default from configure.py)
                if not self.dry_run:
                    cur.execute("""
                        INSERT INTO system_settings (setting_key, setting_value, description)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (setting_key) DO NOTHING
                    """, ('auto_save_interval', '3000', 'Auto-save interval in seconds'))
                
                print(f"  ✓ Auto-save interval")
                migrated_count += 1
                
                if not self.dry_run:
                    self.conn.commit()
                
                print(f"✓ Migrated {migrated_count} system settings")
                return True
                
        except Exception as e:
            print(f"✗ Error migrating system settings: {e}")
            self.conn.rollback()
            return False

    def migrate_management_logs(self, logs_data):
        """Migrate management logs from JSON to database"""
        print("\n📝 Migrating management logs...")
        
        if not logs_data:
            print("⚠ No management logs found")
            return True
        
        try:
            with self.conn.cursor() as cur:
                migrated_count = 0
                
                for log_entry in logs_data:
                    # Parse timestamp
                    timestamp_str = log_entry.get('timestamp')
                    try:
                        # Try to parse the timestamp
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        timestamp = datetime.now(timezone.utc)
                    
                    log_data = (
                        str(uuid.uuid4()),
                        timestamp,
                        log_entry.get('level', 'info'),
                        log_entry.get('message', ''),
                        log_entry.get('event_type'),
                        None,  # user_id - we'll try to match by username later
                        log_entry.get('user'),
                        log_entry.get('ip_address'),
                        json.dumps(log_entry.get('details', {}))
                    )
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO management_logs (id, timestamp, level, message, event_type, user_id, username, ip_address, details)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, log_data)
                    
                    if migrated_count < 5:  # Show first 5 entries
                        print(f"  ✓ Log: {log_entry.get('message', 'No message')[:50]}...")
                    elif migrated_count == 5:
                        print("  ...")
                    
                    migrated_count += 1
                
                if not self.dry_run:
                    self.conn.commit()
                
                print(f"✓ Migrated {migrated_count} log entries")
                return True
                
        except Exception as e:
            print(f"✗ Error migrating management logs: {e}")
            self.conn.rollback()
            return False

    def migrate_notification_settings(self, notifications_data):
        """Migrate notification settings from JSON to database"""
        print("\n📧 Migrating notification settings...")
        
        if not notifications_data:
            print("⚠ No notification settings found")
            return True
        
        try:
            with self.conn.cursor() as cur:
                migrated_count = 0
                
                for key, value in notifications_data.items():
                    setting_data = (
                        str(uuid.uuid4()),
                        self.home_id,
                        key,
                        json.dumps(value)
                    )
                    
                    if not self.dry_run:
                        cur.execute("""
                            INSERT INTO notification_settings (id, home_id, setting_key, setting_value)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (home_id, setting_key) DO UPDATE SET
                                setting_value = EXCLUDED.setting_value,
                                updated_at = NOW()
                        """, setting_data)
                    
                    print(f"  ✓ Setting: {key}")
                    migrated_count += 1
                
                if not self.dry_run:
                    self.conn.commit()
                
                print(f"✓ Migrated {migrated_count} notification settings")
                return True
                
        except Exception as e:
            print(f"✗ Error migrating notification settings: {e}")
            self.conn.rollback()
            return False

    def run_migration(self):
        """Run the complete migration process"""
        print("Starting SmartHome JSON to PostgreSQL migration\n")
        
        # Connect to database
        if not self.connect_database():
            return False
        
        # Check existing data
        if not self.check_existing_data():
            return False
        
        # Load JSON files
        config_data = self.load_json_file(self.config_file, {})
        logs_data = self.load_json_file(self.logs_file, [])
        notifications_data = self.load_json_file(self.notifications_file, {})
        
        # Clear existing data if force mode
        if not self.clear_existing_data():
            return False
        
        try:
            # Start transaction
            if not self.dry_run:
                self.conn.autocommit = False
            
            # Migration steps
            steps = [
                ("Users", lambda: self.migrate_users(config_data)),
                ("Rooms", lambda: self.migrate_rooms(config_data)),
                ("System Settings", lambda: self.migrate_system_settings(config_data)),
                ("Management Logs", lambda: self.migrate_management_logs(logs_data)),
                ("Notification Settings", lambda: self.migrate_notification_settings(notifications_data))
            ]
            
            room_mapping = {}
            
            for step_name, step_func in steps:
                print(f"\n🔄 Step: {step_name}")
                
                if step_name == "Rooms":
                    room_mapping = step_func()
                    if not room_mapping and config_data.get('rooms'):
                        print(f"✗ Failed to migrate {step_name}")
                        return False
                else:
                    if not step_func():
                        print(f"✗ Failed to migrate {step_name}")
                        return False
            
            # Migrate devices and temperature states after rooms are created
            if room_mapping:
                print(f"\n🔄 Step: Devices")
                if not self.migrate_devices(config_data, room_mapping):
                    return False
                
                print(f"\n🔄 Step: Temperature States")
                if not self.migrate_temperature_states(config_data, room_mapping):
                    return False
            
            # Migrate automations last
            print(f"\n🔄 Step: Automations")
            if not self.migrate_automations(config_data):
                return False
            
            # Final commit
            if not self.dry_run:
                self.conn.commit()
                print("\n✅ All data committed to database")
            else:
                print("\n🔍 DRY RUN completed - no data was actually written")
            
            print("\n🎉 Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            if not self.dry_run:
                self.conn.rollback()
            return False
        
        finally:
            if self.conn:
                self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Migrate SmartHome JSON data to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run migration without actually writing to database')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite existing data in database')
    
    args = parser.parse_args()
    
    migrator = SmartHomeMigrator(dry_run=args.dry_run, force=args.force)
    success = migrator.run_migration()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
