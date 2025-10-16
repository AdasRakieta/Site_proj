"""
City Cache Updater - Updates global cities database from API Ninjas
Runs weekly on Mondays at 22:00
"""
import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.multi_home_db_manager import MultiHomeDBManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
API_NINJAS_KEY = "zVhcYv3X8rNW2omHIUquGA==eHc5p2XRGlgnlhuF"
API_NINJAS_URL = "https://api.api-ninjas.com/v1/city"

# List of countries to fetch (you can expand this list)
# Using ISO 3166-1 alpha-2 country codes
COUNTRIES = [
    'PL',  # Poland
    'US',  # United States
    'GB',  # United Kingdom
    'DE',  # Germany
    'FR',  # France
    'ES',  # Spain
    'IT',  # Italy
    'CA',  # Canada
    'AU',  # Australia
    'JP',  # Japan
    'CN',  # China
    'IN',  # India
    'BR',  # Brazil
    'MX',  # Mexico
    'RU',  # Russia
    'NL',  # Netherlands
    'BE',  # Belgium
    'CH',  # Switzerland
    'AT',  # Austria
    'CZ',  # Czech Republic
    'SE',  # Sweden
    'NO',  # Norway
    'DK',  # Denmark
    'FI',  # Finland
    'PT',  # Portugal
    'GR',  # Greece
    'IE',  # Ireland
    'NZ',  # New Zealand
    'SG',  # Singapore
    'KR',  # South Korea
    # Add more countries as needed
]

# Polish cities to fetch individually (major cities)
POLISH_CITIES = [
    'Warsaw', 'Krakow', 'Lodz', 'Wroclaw', 'Poznan',
    'Gdansk', 'Szczecin', 'Bydgoszcz', 'Lublin', 'Katowice',
    'Bialystok', 'Gdynia', 'Czestochowa', 'Radom', 'Sosnowiec',
    'Torun', 'Kielce', 'Gliwice', 'Zabrze', 'Bytom',
    'Olsztyn', 'Bielsko-Biala', 'Rzeszow', 'Ruda Slaska', 'Rybnik',
    'Tychy', 'Dabrowa Gornicza', 'Plock', 'Elblag', 'Opole',
    'Gorzow Wielkopolski', 'Walbrzych', 'Zielona Gora', 'Wloclawek',
    'Tarnow', 'Chorzow', 'Koszalin', 'Kalisze', 'Legnica',
    'Grudziadz', 'Jaworzno', 'Slupsk', 'Jastrzebie-Zdroj', 'Nowy Sacz',
    'Jelenia Gora', 'Konin', 'Piotrkow Trybunalski', 'Lubin',
    'Inowroclaw', 'Ostrowiec Swietokrzyski', 'Suwalki', 'Stargard',
    'Gniezno', 'Ostrow Wielkopolski', 'Zamosc', 'Pila', 'Siedlce',
    'Mysowice', 'Zakopane', 'Sopot', 'Zakopane', 'Malbork',
]

class CityCacheUpdater:
    """Updates the global cities cache from API Ninjas"""
    
    def __init__(self, db_manager: Optional[MultiHomeDBManager] = None):
        self.db = db_manager or MultiHomeDBManager()
        self.api_key = API_NINJAS_KEY
        self.api_url = API_NINJAS_URL
        
    def fetch_polish_cities(self) -> List[Dict]:
        """
        Fetch Polish cities by name to get more detailed data
        
        Returns:
            List of Polish city dictionaries
        """
        headers = {'X-Api-Key': self.api_key}
        polish_cities = []
        
        logger.info(f"Fetching {len(POLISH_CITIES)} Polish cities by name...")
        
        for city_name in POLISH_CITIES:
            try:
                # API Ninjas doesn't accept both name and country together
                # We'll fetch by name only and filter for Poland
                params = {
                    'name': city_name,
                    'limit': 5  # Get multiple results to find Polish one
                }
                
                response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    cities = response.json()
                    # Filter for Polish cities
                    for city in cities:
                        if city.get('country') == 'PL':
                            city['country_code'] = 'PL'
                            city['country'] = 'Poland'
                            # Avoid duplicates
                            if not any(c['name'] == city['name'] and c.get('country_code') == 'PL' for c in polish_cities):
                                polish_cities.append(city)
                                logger.debug(f"  ✓ {city['name']}: {city.get('population', 'N/A')} residents")
                            break  # Take first Polish match
                else:
                    logger.warning(f"  ✗ {city_name}: API returned status {response.status_code}")
                    
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.15)
                
            except Exception as e:
                logger.warning(f"  ✗ {city_name}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(polish_cities)} Polish cities")
        return polish_cities
        
    def fetch_cities_from_api(self, min_population: int = 10000, limit: int = 30) -> List[Dict]:
        """
        Fetch cities from all countries in the COUNTRIES list (except Poland - handled separately)
        
        Args:
            min_population: Minimum population to fetch
            limit: Maximum number of results per request (not used - API limitation)
            
        Returns:
            List of city dictionaries
        """
        headers = {'X-Api-Key': self.api_key}
        all_cities = []
        
        try:
            # Fetch cities from each country (skip Poland - we fetch it separately)
            for country_code in COUNTRIES:
                if country_code == 'PL':
                    continue  # Poland is fetched separately by name
                    
                params = {
                    'country': country_code,
                    'min_population': min_population
                }
                
                logger.info(f"Fetching cities from {country_code} with population >= {min_population}")
                
                try:
                    response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        cities = response.json()
                        logger.info(f"Received {len(cities)} cities from {country_code}")
                        
                        # Add country code to each city for easier filtering later
                        for city in cities:
                            city['country_code'] = country_code
                            # Avoid duplicates based on name and country
                            city_key = f"{city['name']}_{country_code}"
                            if not any(f"{c['name']}_{c.get('country_code')}" == city_key for c in all_cities):
                                all_cities.append(city)
                    else:
                        logger.warning(f"API request for {country_code} failed with status {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout fetching cities from {country_code}")
                    continue
                except Exception as e:
                    logger.error(f"Error fetching cities from {country_code}: {e}")
                    continue
            
            logger.info(f"Total unique cities fetched from {len(COUNTRIES)} countries: {len(all_cities)}")
            return all_cities
            
        except Exception as e:
            logger.error(f"Error in fetch_cities_from_api: {e}")
            return []
    
    def update_city_cache(self) -> bool:
        """
        Update the city cache in database
        
        Returns:
            bool: True if update was successful
        """
        try:
            logger.info("Starting city cache update...")
            
            # Update metadata status
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE city_cache_metadata 
                    SET update_status = 'in_progress',
                        error_message = NULL
                    WHERE id = 1
                """)
            
            # Fetch cities from API
            logger.info("Fetching Polish cities by name...")
            polish_cities = self.fetch_polish_cities()
            
            logger.info("Fetching international cities...")
            international_cities = self.fetch_cities_from_api()
            
            # Combine both lists
            cities = polish_cities + international_cities
            
            if not cities:
                raise Exception("No cities fetched from API")
            
            logger.info(f"Total cities to insert: {len(cities)} ({len(polish_cities)} Polish + {len(international_cities)} international)")
            
            # Clear old data and insert new
            with self.db.get_cursor() as cursor:
                # Delete old cities
                cursor.execute("DELETE FROM world_cities")
                logger.info("Cleared old city data")
                
                # Insert new cities
                insert_count = 0
                for city in cities:
                    try:
                        cursor.execute("""
                            INSERT INTO world_cities (name, latitude, longitude, population, country, country_code)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (name, latitude, longitude) DO UPDATE
                            SET population = EXCLUDED.population,
                                country = EXCLUDED.country,
                                country_code = EXCLUDED.country_code,
                                updated_at = NOW()
                        """, (
                            city.get('name'),
                            city.get('latitude'),
                            city.get('longitude'),
                            city.get('population', 0),
                            city.get('country', 'Unknown'),
                            city.get('country_code')
                        ))
                        insert_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to insert city {city.get('name')}: {e}")
                
                logger.info(f"Inserted/updated {insert_count} cities")
                
                # Update metadata
                cursor.execute("""
                    UPDATE city_cache_metadata 
                    SET last_updated = NOW(),
                        cities_count = %s,
                        update_status = 'completed',
                        error_message = NULL
                    WHERE id = 1
                """, (insert_count,))
            
            logger.info("City cache update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating city cache: {e}")
            
            # Update metadata with error
            try:
                with self.db.get_cursor() as cursor:
                    cursor.execute("""
                        UPDATE city_cache_metadata 
                        SET update_status = 'failed',
                            error_message = %s
                        WHERE id = 1
                    """, (str(e),))
            except:
                pass
            
            return False
    
    def get_cached_cities(self, search_term: Optional[str] = None, country_code: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get cities from cache
        
        Args:
            search_term: Optional search term to filter cities by name
            country_code: Optional ISO country code to filter by country
            limit: Maximum number of results
            
        Returns:
            List of city dictionaries
        """
        with self.db.get_cursor() as cursor:
            conditions = []
            params = []
            
            if search_term:
                conditions.append("name ILIKE %s")
                params.append(f"%{search_term}%")
            
            if country_code:
                conditions.append("country_code = %s")
                params.append(country_code.upper())
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f"""
                SELECT name, latitude, longitude, population, country, country_code
                FROM world_cities
                WHERE {where_clause}
                ORDER BY population DESC, name ASC
                LIMIT %s
            """
            params.append(limit)
            
            cursor.execute(query, tuple(params))
            
            cities = []
            for row in cursor.fetchall():
                cities.append({
                    'name': row[0],
                    'latitude': float(row[1]) if row[1] else None,
                    'longitude': float(row[2]) if row[2] else None,
                    'population': row[3],
                    'country': row[4],
                    'country_code': row[5]
                })
            
            return cities
    
    def get_cache_status(self) -> Dict:
        """Get the status of the city cache"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT last_updated, cities_count, update_status, error_message
                FROM city_cache_metadata
                WHERE id = 1
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    'last_updated': row[0],
                    'cities_count': row[1],
                    'update_status': row[2],
                    'error_message': row[3]
                }
            return None


def main():
    """Main function to run city cache update"""
    logger.info("=" * 50)
    logger.info("Starting Global Cities Cache Update")
    logger.info("=" * 50)
    
    updater = CityCacheUpdater()
    
    # Check current status
    status = updater.get_cache_status()
    if status:
        logger.info(f"Current cache status: {status['update_status']}")
        logger.info(f"Last updated: {status['last_updated']}")
        logger.info(f"Cities count: {status['cities_count']}")
    
    # Run update
    success = updater.update_city_cache()
    
    if success:
        logger.info("City cache update completed successfully!")
        status = updater.get_cache_status()
        logger.info(f"New cities count: {status['cities_count']}")
    else:
        logger.error("City cache update failed!")
        sys.exit(1)
    
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
