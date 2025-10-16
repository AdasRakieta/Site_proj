"""
Load Polish cities from worldcities.csv into the database
"""
import os
import sys
import csv
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.multi_home_db_manager import MultiHomeDBManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_polish_cities():
    """Load Polish cities from worldcities.csv file into database"""
    try:
        # Read CSV file
        csv_path = os.path.join(os.path.dirname(__file__), 'worldcities.csv')
        logger.info(f"Reading cities from {csv_path}")
        
        polish_cities = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter for Poland (iso2 = "PL")
                if row.get('iso2') == 'PL':
                    polish_cities.append(row)
        
        logger.info(f"Found {len(polish_cities)} Polish cities in CSV")
        
        # Connect to database
        db = MultiHomeDBManager()
        logger.info("Connected to database")
        
        # Clear existing data
        with db.get_cursor() as cursor:
            cursor.execute("DELETE FROM polish_cities")
            logger.info("Cleared existing city data")
        
        # Insert cities
        inserted_count = 0
        skipped_count = 0
        
        with db.get_cursor() as cursor:
            for city_data in polish_cities:
                try:
                    city_name = city_data.get('city_ascii', city_data.get('city', '')).strip()
                    lat = city_data.get('lat')
                    lng = city_data.get('lng')
                    admin_name = city_data.get('admin_name', '').strip()
                    population = city_data.get('population')
                    
                    # Skip if missing critical data
                    if not city_name or not lat or not lng:
                        skipped_count += 1
                        continue
                    
                    # Convert to proper types
                    latitude = float(lat)
                    longitude = float(lng)
                    pop = int(population) if population and population.strip() else None
                    
                    cursor.execute("""
                        INSERT INTO polish_cities (city, latitude, longitude, admin_name, population)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (city_name, latitude, longitude, admin_name, pop))
                    
                    inserted_count += 1
                    
                    if inserted_count % 100 == 0:
                        logger.info(f"Inserted {inserted_count} cities...")
                    
                except Exception as e:
                    logger.warning(f"Failed to insert city {city_data.get('city', 'unknown')}: {e}")
                    skipped_count += 1
                    continue
        
        logger.info("=" * 60)
        logger.info(f"✓ Successfully inserted {inserted_count} Polish cities")
        logger.info(f"✗ Skipped {skipped_count} entries")
        logger.info("=" * 60)
        
        # Show sample cities
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT city, admin_name, population, latitude, longitude
                FROM polish_cities
                ORDER BY population DESC NULLS LAST
                LIMIT 10
            """)
            
            logger.info("\nTop 10 cities by population:")
            for row in cursor.fetchall():
                pop_str = f"{row[2]:>10}" if row[2] else "       N/A"
                logger.info(f"  {row[0]:<20} {row[1]:<20} Pop: {pop_str} ({row[3]:.4f}, {row[4]:.4f})")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading cities: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Polish Cities Database Loader (from CSV)")
    logger.info("=" * 60)
    success = load_polish_cities()
    sys.exit(0 if success else 1)
