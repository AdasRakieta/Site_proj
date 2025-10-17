"""
Fetch all Polish cities from GeoNames API and load into database
"""
import os
import sys
import requests
import logging
from dotenv import load_dotenv
import time

# Load environment variables from .env file (fallback to system environment)
# Priority: 1) System environment variables, 2) .env file
load_dotenv(override=False)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.multi_home_db_manager import MultiHomeDBManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GeoNames configuration
GEONAMES_USERNAME = "adasrakieta"  # Twój username z GeoNames
GEONAMES_API_URL = "http://api.geonames.org/searchJSON"

def fetch_polish_cities_from_geonames():
    """
    Fetch all Polish cities from GeoNames API
    
    Feature codes for Polish cities:
    - PPL: populated place (general)
    - PPLA: seat of a first-order administrative division
    - PPLA2: seat of a second-order administrative division
    - PPLA3: seat of a third-order administrative division
    - PPLA4: seat of a fourth-order administrative division
    - PPLC: capital of a political entity
    - PPLL: populated locality
    - PPLS: populated places
    - PPLX: section of populated place
    """
    
    all_cities = []
    
    # Feature codes for cities/towns in Poland
    feature_codes = ['PPL', 'PPLA', 'PPLA2', 'PPLA3', 'PPLA4', 'PPLC']
    
    logger.info("=" * 70)
    logger.info("Fetching Polish cities from GeoNames API")
    logger.info("=" * 70)
    
    for feature_code in feature_codes:
        logger.info(f"\nFetching cities with feature code: {feature_code}")
        
        start_row = 0
        max_rows = 1000  # GeoNames max per request
        
        while True:
            params = {
                'country': 'PL',
                'featureCode': feature_code,
                'maxRows': max_rows,
                'startRow': start_row,
                'username': GEONAMES_USERNAME,
                'style': 'FULL'  # Get full information including population
            }
            
            try:
                response = requests.get(GEONAMES_API_URL, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'geonames' not in data:
                        logger.warning(f"No 'geonames' key in response for {feature_code}")
                        break
                    
                    cities = data['geonames']
                    total_results = data.get('totalResultsCount', 0)
                    
                    if not cities:
                        logger.info(f"  No more cities for {feature_code}")
                        break
                    
                    logger.info(f"  Retrieved {len(cities)} cities (start: {start_row}, total available: {total_results})")
                    
                    all_cities.extend(cities)
                    
                    # Check if we got all results
                    if start_row + len(cities) >= total_results:
                        break
                    
                    start_row += max_rows
                    time.sleep(1)  # Rate limiting - 1 request per second
                    
                else:
                    logger.error(f"API request failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching data for {feature_code}: {e}")
                break
    
    logger.info("=" * 70)
    logger.info(f"Total cities fetched: {len(all_cities)}")
    logger.info("=" * 70)
    
    return all_cities

def load_cities_to_database(cities):
    """Load cities into PostgreSQL database"""
    
    logger.info("\nConnecting to database...")
    db = MultiHomeDBManager()
    logger.info("Connected to database")
    
    # Clear existing data
    with db.get_cursor() as cursor:
        cursor.execute("DELETE FROM polish_cities")
        logger.info("Cleared existing city data")
    
    # Remove duplicates based on geonameId
    seen_ids = set()
    unique_cities = []
    
    for city in cities:
        geoname_id = city.get('geonameId')
        if geoname_id and geoname_id not in seen_ids:
            seen_ids.add(geoname_id)
            unique_cities.append(city)
    
    logger.info(f"Unique cities after deduplication: {len(unique_cities)}")
    
    # Insert cities
    inserted_count = 0
    skipped_count = 0
    
    with db.get_cursor() as cursor:
        for city_data in unique_cities:
            try:
                city_name = city_data.get('name', '').strip()
                lat = city_data.get('lat')
                lng = city_data.get('lng')
                admin_name = city_data.get('adminName1', '').strip()  # Województwo
                population = city_data.get('population', 0)
                
                # Skip if missing critical data
                if not city_name or not lat or not lng:
                    skipped_count += 1
                    continue
                
                # Convert to proper types
                latitude = float(lat)
                longitude = float(lng)
                pop = int(population) if population else None
                
                cursor.execute("""
                    INSERT INTO polish_cities (city, latitude, longitude, admin_name, population)
                    VALUES (%s, %s, %s, %s, %s)
                """, (city_name, latitude, longitude, admin_name, pop))
                
                inserted_count += 1
                
                if inserted_count % 100 == 0:
                    logger.info(f"Inserted {inserted_count} cities...")
                
            except Exception as e:
                logger.warning(f"Failed to insert city {city_data.get('name', 'unknown')}: {e}")
                skipped_count += 1
                continue
    
    logger.info("=" * 70)
    logger.info(f"✓ Successfully inserted {inserted_count} Polish cities")
    logger.info(f"✗ Skipped {skipped_count} entries")
    logger.info("=" * 70)
    
    return inserted_count

def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("GeoNames Polish Cities Importer")
    logger.info(f"Username: {GEONAMES_USERNAME}")
    logger.info("=" * 70)
    
    # Fetch cities from GeoNames
    cities = fetch_polish_cities_from_geonames()
    
    if not cities:
        logger.error("No cities fetched from GeoNames!")
        return False
    
    # Load to database
    inserted = load_cities_to_database(cities)
    
    if inserted == 0:
        logger.error("No cities inserted to database!")
        return False
    
    # Show statistics
    db = MultiHomeDBManager()
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT admin_name) as voivodeships,
                COUNT(CASE WHEN population >= 100000 THEN 1 END) as over_100k,
                COUNT(CASE WHEN population >= 10000 THEN 1 END) as over_10k,
                MAX(population) as largest,
                MIN(population) as smallest
            FROM polish_cities
        """)
        stats = cursor.fetchone()
        
        logger.info("\n" + "=" * 70)
        logger.info("DATABASE STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total cities: {stats[0]}")
        logger.info(f"Voivodeships: {stats[1]}")
        logger.info(f"Cities >100k: {stats[2]}")
        logger.info(f"Cities >10k: {stats[3]}")
        logger.info(f"Largest city: {stats[4]:,} residents")
        logger.info(f"Smallest city: {stats[5]:,} residents" if stats[5] else "Smallest city: N/A")
        
        # Show top 10 cities
        cursor.execute("""
            SELECT city, admin_name, population, latitude, longitude
            FROM polish_cities
            ORDER BY population DESC NULLS LAST
            LIMIT 10
        """)
        
        logger.info("\nTop 10 cities by population:")
        for row in cursor.fetchall():
            pop_str = f"{row[2]:>10,}" if row[2] else "       N/A"
            logger.info(f"  {row[0]:<25} {row[1]:<20} Pop: {pop_str}")
    
    logger.info("=" * 70)
    logger.info("Import completed successfully!")
    logger.info("=" * 70)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
