#!/usr/bin/env python3
"""
Migration script to assign existing rooms to Admin Home and fix multi-home data.
"""

import logging
from utils.multi_home_db_manager import MultiHomeDBManager
from utils.smart_home_db_manager import SmartHomeDatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_rooms_to_admin_home():
    """Migrate existing rooms to Admin Home"""
    
    # Initialize database managers
    try:
        multi_db = MultiHomeDBManager(
            host="100.103.184.90",
            port=5432,
            user="admin", 
            password="Qwuizzy123.",
            database="smarthome_multihouse"
        )
        logger.info("✓ Connected to multi-home database")
        
        smart_db = SmartHomeDatabaseManager()  # Używa domyślnej konfiguracji
        logger.info("✓ Connected to smart-home database")
        
    except Exception as e:
        logger.error(f"Failed to connect to databases: {e}")
        return

    # User and Admin Home IDs
    user_id = "727a5147-14e6-405d-921b-931fbc0397ed"
    admin_home_id = "40a67bc7-6b5d-4a88-bce1-f7ef6d06432c"
    
    try:
        # Get existing rooms from smart home database
        logger.info("📋 Getting existing rooms from smart home database...")
        rooms = smart_db.get_rooms_with_ids()  # Używamy dostępnej metody
        logger.info(f"Found {len(rooms)} rooms: {[room['name'] for room in rooms]}")
        
        # Check if rooms already exist in multi-home database
        existing_multi_rooms = multi_db.get_home_rooms(admin_home_id, user_id)
        logger.info(f"Existing rooms in Admin Home: {len(existing_multi_rooms)}")
        
        # Migrate each room to multi-home database
        for room in rooms:
            room_name = room['name']
            
            # Check if room already exists in multi-home
            room_exists = any(r['name'] == room_name for r in existing_multi_rooms)
            
            if not room_exists:
                logger.info(f"🏠 Creating room '{room_name}' in Admin Home...")
                
                # Create room in multi-home database
                room_id = multi_db.create_room(
                    home_id=admin_home_id,
                    name=room_name,
                    user_id=user_id,
                    description=f"Migrated from original smart home system"
                )
                
                logger.info(f"✅ Created room '{room_name}' with ID: {room_id}")
                
                # Migrate devices from this room
                logger.info(f"🔧 Migrating devices for room '{room_name}'...")
                
                # Pobierz przyciski z tego pokoju
                buttons = smart_db.get_buttons()
                room_buttons = [b for b in buttons if b.get('room') == room_name]
                logger.info(f"  📱 Found {len(room_buttons)} buttons in room '{room_name}'")
                
                for button in room_buttons:
                    device_name = button.get('name')
                    if not device_name:
                        continue
                    state = button.get('state', False)
                    
                    multi_db.create_device(
                        home_id=admin_home_id,
                        room_id=room_id,
                        name=device_name,
                        device_type='button',
                        user_id=user_id,
                        state=state
                    )
                    logger.info(f"  ✓ Migrated button: {device_name}")
                
                # Pobierz kontrolery temperatury z tego pokoju
                temp_controls = smart_db.get_temperature_controls()
                room_temp_controls = [t for t in temp_controls if t.get('room') == room_name]
                logger.info(f"  🌡️ Found {len(room_temp_controls)} temperature controls in room '{room_name}'")
                
                for temp_control in room_temp_controls:
                    device_name = temp_control.get('name')
                    if not device_name:
                        continue
                    temperature = temp_control.get('temperature', 22.0)
                    
                    multi_db.create_device(
                        home_id=admin_home_id,
                        room_id=room_id,
                        name=device_name,
                        device_type='temperature_control',
                        user_id=user_id,
                        temperature=temperature
                    )
                    logger.info(f"  ✓ Migrated temperature control: {device_name}")
            else:
                logger.info(f"⏭️ Room '{room_name}' already exists in Admin Home")
        
        # Verify migration
        logger.info("\n🔍 Verifying migration...")
        final_rooms = multi_db.get_home_rooms(admin_home_id, user_id)
        logger.info(f"✅ Admin Home now has {len(final_rooms)} rooms:")
        
        for room in final_rooms:
            devices = multi_db.get_home_devices(admin_home_id, user_id)  # Pobierz wszystkie urządzenia dla domu
            room_devices = [d for d in devices if d.get('room_id') == room['id']]  # Filtruj po room_id
            logger.info(f"  - {room['name']}: {len(room_devices)} devices")
        
        # Test statistics for both homes
        logger.info("\n📊 Testing home statistics...")
        user_homes = multi_db.get_user_homes(user_id)
        
        for home in user_homes:
            rooms = multi_db.get_home_rooms(home['id'], user_id)
            devices = multi_db.get_home_devices(home['id'], user_id) 
            logger.info(f"🏠 {home['name']} (ID: {home['id']}): {len(rooms)} rooms, {len(devices)} devices")
        
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Error during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if multi_db._connection:
            multi_db._connection.close()
        # Connection będzie automatycznie zamknięte
        logger.info("✓ Database connections closed")

if __name__ == "__main__":
    migrate_rooms_to_admin_home()