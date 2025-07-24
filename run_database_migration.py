#!/usr/bin/env python3
"""
SmartHome Database Migration and Startup Script
===============================================

This script handles:
1. Database schema creation
2. Data migration from JSON to PostgreSQL
3. Application startup in database mode

Usage:
    python run_database_migration.py --help
    python run_database_migration.py migrate --dry-run
    python run_database_migration.py migrate --force
    python run_database_migration.py start
    python run_database_migration.py check
"""

import argparse
import sys
import os
import subprocess
import time
from pathlib import Path

def run_sql_script():
    """Execute the database schema creation script"""
    print("[DB] Creating database schema...")
    
    try:
        import psycopg2
        
        # Database configuration
        db_config = {
            'host': '192.168.1.219',
            'port': 5432,
            'database': 'admin',
            'user': 'admin',
            'password': 'Qwuizzy123.'
        }
        
        # SQL schema script
        schema_sql = """
        -- Enable UUID extension for generating unique identifiers
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL UNIQUE,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'user',
            profile_picture TEXT DEFAULT '',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

        -- Rooms table
        CREATE TABLE IF NOT EXISTS rooms (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL UNIQUE,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_rooms_order ON rooms(display_order);

        -- Devices table (unified for buttons and temperature controls)
        CREATE TABLE IF NOT EXISTS devices (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
            device_type VARCHAR(50) NOT NULL,
            state BOOLEAN DEFAULT FALSE,
            temperature DECIMAL(5,2) DEFAULT 22.0,
            min_temperature DECIMAL(5,2) DEFAULT 16.0,
            max_temperature DECIMAL(5,2) DEFAULT 30.0,
            display_order INTEGER DEFAULT 0,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT check_device_type CHECK (device_type IN ('button', 'temperature_control'))
        );

        CREATE INDEX IF NOT EXISTS idx_devices_room ON devices(room_id);
        CREATE INDEX IF NOT EXISTS idx_devices_type ON devices(device_type);
        CREATE INDEX IF NOT EXISTS idx_devices_order ON devices(room_id, display_order);

        -- Automations table
        CREATE TABLE IF NOT EXISTS automations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL UNIQUE,
            trigger_config JSONB NOT NULL,
            actions_config JSONB NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            last_executed TIMESTAMP WITH TIME ZONE,
            execution_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            last_error TEXT,
            last_error_time TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_automations_enabled ON automations(enabled);
        CREATE INDEX IF NOT EXISTS idx_automations_name ON automations(name);

        -- Room temperature states table
        CREATE TABLE IF NOT EXISTS room_temperature_states (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
            current_temperature DECIMAL(5,2) NOT NULL DEFAULT 22.0,
            target_temperature DECIMAL(5,2) DEFAULT 22.0,
            heating_active BOOLEAN DEFAULT FALSE,
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(room_id)
        );

        CREATE INDEX IF NOT EXISTS idx_temp_states_room ON room_temperature_states(room_id);

        -- System settings table
        CREATE TABLE IF NOT EXISTS system_settings (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            setting_key VARCHAR(255) NOT NULL UNIQUE,
            setting_value JSONB,
            description TEXT,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_by UUID REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(setting_key);

        -- Management logs table
        CREATE TABLE IF NOT EXISTS management_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            level VARCHAR(20) NOT NULL DEFAULT 'info',
            message TEXT NOT NULL,
            event_type VARCHAR(100),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            username VARCHAR(255),
            ip_address INET,
            details JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON management_logs(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_logs_level ON management_logs(level);
        CREATE INDEX IF NOT EXISTS idx_logs_event_type ON management_logs(event_type);
        CREATE INDEX IF NOT EXISTS idx_logs_user ON management_logs(user_id);

        -- Notification settings table
        CREATE TABLE IF NOT EXISTS notification_settings (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            home_id UUID DEFAULT uuid_generate_v4(),
            setting_key VARCHAR(255) NOT NULL,
            setting_value JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(home_id, setting_key)
        );

        CREATE INDEX IF NOT EXISTS idx_notif_settings_home ON notification_settings(home_id);

        -- Notification recipients table
        CREATE TABLE IF NOT EXISTS notification_recipients (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            home_id UUID NOT NULL,
            email VARCHAR(255) NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_notif_recipients_home ON notification_recipients(home_id);
        CREATE INDEX IF NOT EXISTS idx_notif_recipients_enabled ON notification_recipients(enabled);

        -- Device history table
        CREATE TABLE IF NOT EXISTS device_history (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
            old_state JSONB,
            new_state JSONB,
            changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
            change_reason VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_device_history_device ON device_history(device_id);
        CREATE INDEX IF NOT EXISTS idx_device_history_time ON device_history(created_at DESC);

        -- Automation executions table
        CREATE TABLE IF NOT EXISTS automation_executions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            automation_id UUID REFERENCES automations(id) ON DELETE CASCADE,
            execution_status VARCHAR(50) NOT NULL,
            trigger_data JSONB,
            actions_executed JSONB,
            error_message TEXT,
            execution_time_ms INTEGER,
            executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_auto_exec_automation ON automation_executions(automation_id);
        CREATE INDEX IF NOT EXISTS idx_auto_exec_time ON automation_executions(executed_at DESC);
        CREATE INDEX IF NOT EXISTS idx_auto_exec_status ON automation_executions(execution_status);

        -- Session tokens table
        CREATE TABLE IF NOT EXISTS session_tokens (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL UNIQUE,
            remember_me BOOLEAN DEFAULT FALSE,
            ip_address INET,
            user_agent TEXT,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_session_user ON session_tokens(user_id);
        CREATE INDEX IF NOT EXISTS idx_session_token ON session_tokens(token_hash);
        CREATE INDEX IF NOT EXISTS idx_session_expires ON session_tokens(expires_at);

        -- Function for updating timestamps
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        -- Triggers for automatic timestamp updates
        DROP TRIGGER IF EXISTS update_users_updated_at ON users;
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_rooms_updated_at ON rooms;
        CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_devices_updated_at ON devices;
        CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_automations_updated_at ON automations;
        CREATE TRIGGER update_automations_updated_at BEFORE UPDATE ON automations 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
        CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_notification_settings_updated_at ON notification_settings;
        CREATE TRIGGER update_notification_settings_updated_at BEFORE UPDATE ON notification_settings 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_notification_recipients_updated_at ON notification_recipients;
        CREATE TRIGGER update_notification_recipients_updated_at BEFORE UPDATE ON notification_recipients 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        -- Initial system settings
        INSERT INTO system_settings (setting_key, setting_value, description) 
        VALUES ('security_state', '"Wyłączony"', 'Current security system state')
        ON CONFLICT (setting_key) DO NOTHING;

        INSERT INTO system_settings (setting_key, setting_value, description) 
        VALUES ('default_theme', '"light"', 'Default application theme')
        ON CONFLICT (setting_key) DO NOTHING;

        INSERT INTO system_settings (setting_key, setting_value, description) 
        VALUES ('auto_save_interval', '3000', 'Auto-save interval in seconds')
        ON CONFLICT (setting_key) DO NOTHING;
        """
        
        # Connect and execute schema
        conn = psycopg2.connect(**db_config)
        try:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
            print("[OK] Database schema created successfully")
            return True
        finally:
            conn.close()
            
    except ImportError:
        print("[ERROR] psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to create schema: {e}")
        return False

def run_migration(dry_run=False, force=False):
    """Run the data migration from JSON to PostgreSQL"""
    print("[MIGRATE] Starting data migration...")
    
    try:
        # Build migration command using the simple migrator
        cmd = [sys.executable, "migrate_simple.py"]
        
        if dry_run:
            cmd.append("--dry-run")
        
        # Run migration script
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[OK] Migration completed successfully")
            print(result.stdout)
            return True
        else:
            print("[ERROR] Migration failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"[ERROR] Migration error: {e}")
        return False

def check_database_connection():
    """Check if database connection is working"""
    print("[CHECK] Checking database connection...")
    
    try:
        from utils.smart_home_db_manager import SmartHomeDatabaseManager
        
        # Try to initialize database manager
        db = SmartHomeDatabaseManager()
        stats = db.get_stats()
        
        print("[OK] Database connection successful")
        print(f"[STATS] Database statistics: {stats}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

def start_application():
    """Start the SmartHome application in database mode"""
    print("[START] Starting SmartHome application with database backend...")
    
    try:
        from app_db import main
        main()
    except Exception as e:
        print(f"[ERROR] Failed to start application: {e}")
        return False

def install_requirements():
    """Install required Python packages"""
    print("[INSTALL] Installing required packages...")
    
    requirements = [
        "psycopg2-binary",
        "flask",
        "flask-socketio",
        "werkzeug",
        "requests"
    ]
    
    try:
        for package in requirements:
            print(f"  Installing {package}...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  [WARNING] Failed to install {package}")
            else:
                print(f"  [OK] {package} installed")
        
        print("[OK] Package installation completed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Package installation failed: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='SmartHome Database Migration and Startup')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install required packages')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check database connection')
    
    # Schema command
    schema_parser = subparsers.add_parser('schema', help='Create database schema')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate data from JSON to database')
    migrate_parser.add_argument('--dry-run', action='store_true', 
                               help='Run migration without writing to database')
    migrate_parser.add_argument('--force', action='store_true',
                               help='Overwrite existing data in database')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start application in database mode')
    
    # Full command (install + schema + migrate + start)
    full_parser = subparsers.add_parser('full', help='Complete setup: install + schema + migrate + start')
    full_parser.add_argument('--force', action='store_true',
                            help='Force migration overwrite')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("=" * 60)
    print("[HOME] SmartHome Database Migration & Startup")
    print("=" * 60)
    
    if args.command == 'install':
        success = install_requirements()
        
    elif args.command == 'check':
        success = check_database_connection()
        
    elif args.command == 'schema':
        success = run_sql_script()
        
    elif args.command == 'migrate':
        success = run_migration(dry_run=args.dry_run, force=args.force)
        
    elif args.command == 'start':
        if check_database_connection():
            start_application()
        else:
            print("[ERROR] Cannot start application - database connection failed")
            sys.exit(1)
            
    elif args.command == 'full':
        print("[SETUP] Running complete setup process...\n")
        
        steps = [
            ("Installing packages", lambda: install_requirements()),
            ("Creating schema", lambda: run_sql_script()),
            ("Checking connection", lambda: check_database_connection()),
            ("Migrating data", lambda: run_migration(force=args.force)),
        ]
        
        for step_name, step_func in steps:
            print(f"\n[STEP] {step_name}")
            if not step_func():
                print(f"[ERROR] Failed at step: {step_name}")
                sys.exit(1)
            time.sleep(1)  # Brief pause between steps
        
        print("\n[SUCCESS] Setup completed successfully!")
        print("[START] Starting application...")
        start_application()
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
