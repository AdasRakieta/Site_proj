"""
SmartHome Configuration Switch
==============================

This script allows switching between JSON and Database modes
and handles configuration management.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

class SmartHomeConfig:
    """SmartHome configuration manager"""
    
    def __init__(self):
        self.config_file = "smarthome_mode.json"
        self.backup_dir = "backups"
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Ensure backup directory exists"""
        Path(self.backup_dir).mkdir(exist_ok=True)
    
    def get_current_mode(self):
        """Get current operation mode"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('mode', 'json')
            return 'json'
        except:
            return 'json'
    
    def set_mode(self, mode):
        """Set operation mode"""
        config = {
            'mode': mode,
            'last_changed': datetime.now().isoformat(),
            'version': '2.0'
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Mode set to: {mode}")
    
    def backup_json_files(self):
        """Create backup of JSON files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"json_backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        os.makedirs(backup_path, exist_ok=True)
        
        json_files = [
            'smart_home_config.json',
            'smart_home_1st_conf.json',
            'management_logs.json',
            'notifications_settings.json'
        ]
        
        backed_up = []
        for file in json_files:
            if os.path.exists(file):
                shutil.copy2(file, backup_path)
                backed_up.append(file)
        
        if backed_up:
            print(f"✓ Backed up {len(backed_up)} JSON files to {backup_path}")
            return backup_path
        else:
            print("⚠ No JSON files found to backup")
            return None
    
    def switch_to_database(self):
        """Switch to database mode"""
        print("🔄 Switching to Database mode...")
        
        # Backup JSON files first
        backup_path = self.backup_json_files()
        
        # Set mode
        self.set_mode('database')
        
        # Create environment file if not exists
        self.create_env_file()
        
        print("✅ Switched to Database mode")
        print("📋 Next steps:")
        print("   1. Run: python run_database_migration.py check")
        print("   2. Run: python run_database_migration.py migrate")
        print("   3. Run: python app_db.py")
        
        return True
    
    def switch_to_json(self):
        """Switch to JSON mode"""
        print("🔄 Switching to JSON mode...")
        
        # Export from database if possible
        try:
            from utils.smart_home_db_manager import SmartHomeDatabaseManager
            db = SmartHomeDatabaseManager()
            data = db.export_to_json_format()
            
            # Save exported data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_file = f"exported_from_db_{timestamp}.json"
            with open(export_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✓ Exported database data to {export_file}")
            
        except Exception as e:
            print(f"⚠ Could not export from database: {e}")
        
        # Set mode
        self.set_mode('json')
        
        print("✅ Switched to JSON mode")
        print("📋 Use original app.py to run in JSON mode")
        
        return True
    
    def create_env_file(self):
        """Create .env file for database configuration"""
        env_content = """# SmartHome Database Configuration
DB_HOST=192.168.1.219
DB_PORT=5432
DB_NAME=admin
DB_USER=admin
DB_PASSWORD=Qwuizzy123.

# Unique Home ID (auto-generated)
HOME_ID=auto-generated

# Email Configuration (from email_conf.env)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ADMIN_EMAIL=admin@example.com
"""
        
        env_file = ".env"
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write(env_content)
            print(f"✓ Created {env_file} file")
        else:
            print(f"⚠ {env_file} already exists")
    
    def status(self):
        """Show current status"""
        mode = self.get_current_mode()
        
        print("🏠 SmartHome System Status")
        print("-" * 40)
        print(f"Current Mode: {mode.upper()}")
        
        if mode == 'database':
            # Check database connection
            try:
                from utils.smart_home_db_manager import SmartHomeDatabaseManager
                db = SmartHomeDatabaseManager()
                stats = db.get_stats()
                print("Database Status: ✅ Connected")
                print(f"Database Stats: {stats}")
            except Exception as e:
                print(f"Database Status: ❌ Error - {e}")
        
        elif mode == 'json':
            # Check JSON files
            json_files = [
                'smart_home_config.json',
                'management_logs.json',
                'notifications_settings.json'
            ]
            
            existing_files = [f for f in json_files if os.path.exists(f)]
            print(f"JSON Files: {len(existing_files)}/{len(json_files)} found")
            
            for file in json_files:
                status = "✅" if os.path.exists(file) else "❌"
                print(f"  {status} {file}")
        
        print("-" * 40)
    
    def migrate_data(self, dry_run=False, force=False):
        """Run data migration"""
        if self.get_current_mode() != 'database':
            print("❌ Not in database mode. Switch first with: switch database")
            return False
        
        import subprocess
        import sys
        
        cmd = [sys.executable, "run_database_migration.py", "migrate"]
        
        if dry_run:
            cmd.append("--dry-run")
        if force:
            cmd.append("--force")
        
        try:
            result = subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Migration failed: {e}")
            return False

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SmartHome Configuration Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show current status')
    
    # Switch commands
    switch_parser = subparsers.add_parser('switch', help='Switch operation mode')
    switch_parser.add_argument('mode', choices=['database', 'json'], help='Target mode')
    
    # Migration commands
    migrate_parser = subparsers.add_parser('migrate', help='Migrate data to database')
    migrate_parser.add_argument('--dry-run', action='store_true', help='Dry run migration')
    migrate_parser.add_argument('--force', action='store_true', help='Force migration')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup JSON files')
    
    args = parser.parse_args()
    
    config = SmartHomeConfig()
    
    if not args.command:
        config.status()
        return
    
    if args.command == 'status':
        config.status()
    
    elif args.command == 'switch':
        if args.mode == 'database':
            config.switch_to_database()
        elif args.mode == 'json':
            config.switch_to_json()
    
    elif args.command == 'migrate':
        config.migrate_data(dry_run=args.dry_run, force=args.force)
    
    elif args.command == 'backup':
        config.backup_json_files()

if __name__ == '__main__':
    main()
