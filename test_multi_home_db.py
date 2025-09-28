#!/usr/bin/env python3
"""
Test script to check multi-home database and create initial data if needed.
"""

from utils.multi_home_db_manager import MultiHomeDBManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize database manager
    try:
        multi_db = MultiHomeDBManager(
            host="100.103.184.90",
            port=5432,
            user="admin", 
            password="Qwuizzy123.",
            database="smarthome_multihouse"
        )
        logger.info("✓ Connected to multi-home database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return

    # Test user ID (from logs - admin user)
    user_id = "727a5147-14e6-405d-921b-931fbc0397ed"
    
    try:
        # Check if user has any homes
        homes = multi_db.get_user_homes(user_id)
        logger.info(f"User has {len(homes)} homes:")
        for home in homes:
            logger.info(f"  - {home['name']} (ID: {home['id']}, Role: {home['role']}, Owner: {home['is_owner']})")
        
        # If no homes, create a default one
        if not homes:
            logger.info("Creating default home for user...")
            home_id = multi_db.create_home("Mój Dom", user_id, "Pierwszy dom w systemie smart home")
            logger.info(f"✓ Created home with ID: {home_id}")
            
            # Set as current home
            multi_db.set_user_current_home(user_id, home_id)
            logger.info(f"✓ Set home {home_id} as current home for user")
            
            # Verify
            homes = multi_db.get_user_homes(user_id)
            logger.info(f"User now has {len(homes)} homes:")
            for home in homes:
                logger.info(f"  - {home['name']} (ID: {home['id']}, Role: {home['role']}, Owner: {home['is_owner']})")
        
        # Check current home
        current_home_id = multi_db.get_user_current_home(user_id)
        logger.info(f"Current home ID: {current_home_id}")
        
        if current_home_id:
            current_home = multi_db.get_home_details(current_home_id, user_id)
            logger.info(f"Current home details: {current_home}")
        
    except Exception as e:
        logger.error(f"Error testing multi-home functionality: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close database connection
        if multi_db._connection:
            multi_db._connection.close()
        logger.info("✓ Database connection closed")

if __name__ == "__main__":
    main()