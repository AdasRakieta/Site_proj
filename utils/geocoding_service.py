"""
Geocoding Service using Nominatim (OpenStreetMap)
Converts addresses to geographic coordinates (latitude/longitude)
Free to use, no API key required - respects usage policy (max 1 request/second)
"""

import requests
import time
import logging
from typing import Dict, Optional, Tuple, Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

class GeocodingService:
    """
    Geocoding service using Nominatim API (OpenStreetMap)
    Documentation: https://nominatim.org/release-docs/latest/api/Search/
    """
    
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
    USER_AGENT = "SmartHomeMultiHouse/1.0"  # Required by Nominatim usage policy
    
    # Rate limiting: Nominatim requires max 1 request per second
    _last_request_time = 0
    _min_request_interval = 1.0  # seconds
    
    # Poland bounding box for validation
    POLAND_BOUNDS = {
        'min_lat': 49.0,
        'max_lat': 54.9,
        'min_lon': 14.1,
        'max_lon': 24.2
    }
    
    @classmethod
    def _rate_limit(cls):
        """Ensure we don't exceed 1 request per second (Nominatim policy)"""
        current_time = time.time()
        time_since_last = current_time - cls._last_request_time
        
        if time_since_last < cls._min_request_interval:
            sleep_time = cls._min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        cls._last_request_time = time.time()
    
    @classmethod
    def _is_in_poland(cls, lat: float, lon: float) -> bool:
        """Check if coordinates are within Poland's boundaries"""
        return (
            cls.POLAND_BOUNDS['min_lat'] <= lat <= cls.POLAND_BOUNDS['max_lat'] and
            cls.POLAND_BOUNDS['min_lon'] <= lon <= cls.POLAND_BOUNDS['max_lon']
        )
    
    @classmethod
    def geocode_address(
        cls,
        city: str,
        street: Optional[str] = None,
        house_number: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: str = "Poland"
    ) -> Optional[Dict[str, Any]]:
        """
        Convert address to geographic coordinates
        
        Args:
            city: City name (required)
            street: Street name (optional)
            house_number: House number (optional)
            postal_code: Postal code (optional)
            country: Country name (default: Poland)
        
        Returns:
            Dictionary with geocoding result or None if failed:
            {
                'latitude': float,
                'longitude': float,
                'display_name': str,  # Full formatted address
                'address_components': dict  # Detailed address breakdown
            }
        """
        try:
            # Build address query
            address_parts = []
            
            if house_number and street:
                address_parts.append(f"{street} {house_number}")
            elif street:
                address_parts.append(street)
            
            if postal_code:
                address_parts.append(postal_code)
            
            address_parts.append(city)
            address_parts.append(country)
            
            address_query = ", ".join(filter(None, address_parts))
            
            logger.info(f"Geocoding address: {address_query}")
            
            # Respect rate limiting
            cls._rate_limit()
            
            # Make request to Nominatim
            params = {
                'q': address_query,
                'format': 'json',
                'addressdetails': 1,
                'limit': 1,
                'countrycodes': 'pl',  # Restrict to Poland
                'accept-language': 'pl'  # Prefer Polish names
            }
            
            headers = {
                'User-Agent': cls.USER_AGENT
            }
            
            response = requests.get(
                cls.BASE_URL,
                params=params,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            results = response.json()
            
            if not results:
                logger.warning(f"No geocoding results for: {address_query}")
                return None
            
            result = results[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            
            # Validate coordinates are in Poland
            if not cls._is_in_poland(lat, lon):
                logger.warning(f"Geocoded location outside Poland: {lat}, {lon}")
                return None
            
            geocoded_data = {
                'latitude': lat,
                'longitude': lon,
                'display_name': result.get('display_name', ''),
                'address_components': result.get('address', {}),
                'osm_type': result.get('osm_type', ''),
                'osm_id': result.get('osm_id', ''),
                'importance': result.get('importance', 0)
            }
            
            logger.info(f"Successfully geocoded: {address_query} -> ({lat}, {lon})")
            return geocoded_data
            
        except requests.RequestException as e:
            logger.error(f"Geocoding request failed: {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"Error parsing geocoding response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected geocoding error: {e}")
            return None
    
    @classmethod
    def reverse_geocode(cls, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Convert coordinates to address (reverse geocoding)
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        
        Returns:
            Dictionary with address components or None if failed
        """
        try:
            # Validate coordinates are in Poland
            if not cls._is_in_poland(latitude, longitude):
                logger.warning(f"Coordinates outside Poland: {latitude}, {longitude}")
                return None
            
            logger.info(f"Reverse geocoding: ({latitude}, {longitude})")
            
            # Respect rate limiting
            cls._rate_limit()
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1,
                'accept-language': 'pl'
            }
            
            headers = {
                'User-Agent': cls.USER_AGENT
            }
            
            response = requests.get(
                cls.REVERSE_URL,
                params=params,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                logger.warning(f"Reverse geocoding error: {result.get('error')}")
                return None
            
            address = result.get('address', {})
            
            reverse_data = {
                'city': address.get('city') or address.get('town') or address.get('village', ''),
                'street': address.get('road', ''),
                'house_number': address.get('house_number', ''),
                'postal_code': address.get('postcode', ''),
                'state': address.get('state', ''),
                'country': address.get('country', 'Poland'),
                'country_code': address.get('country_code', 'pl'),
                'display_name': result.get('display_name', ''),
                'address_components': address
            }
            
            logger.info(f"Successfully reverse geocoded: ({latitude}, {longitude}) -> {reverse_data['city']}")
            return reverse_data
            
        except requests.RequestException as e:
            logger.error(f"Reverse geocoding request failed: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing reverse geocoding response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected reverse geocoding error: {e}")
            return None
    
    @classmethod
    def validate_polish_postal_code(cls, postal_code: str) -> bool:
        """
        Validate Polish postal code format (XX-XXX)
        
        Args:
            postal_code: Postal code to validate
        
        Returns:
            True if valid Polish postal code format
        """
        import re
        pattern = r'^\d{2}-\d{3}$'
        return bool(re.match(pattern, postal_code))


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test geocoding with full address
    print("\n=== Test 1: Full address geocoding ===")
    result = GeocodingService.geocode_address(
        city="Warszawa",
        street="Marszałkowska",
        house_number="1",
        postal_code="00-624"
    )
    if result:
        print(f"✓ Coordinates: {result['latitude']:.6f}, {result['longitude']:.6f}")
        print(f"  Display: {result['display_name']}")
    
    # Test geocoding with city only
    print("\n=== Test 2: City only ===")
    result = GeocodingService.geocode_address(city="Kraków")
    if result:
        print(f"✓ Coordinates: {result['latitude']:.6f}, {result['longitude']:.6f}")
    
    # Test reverse geocoding
    print("\n=== Test 3: Reverse geocoding ===")
    result = GeocodingService.reverse_geocode(52.2297, 21.0122)  # Warsaw center
    if result:
        print(f"✓ Address: {result['street']} {result['house_number']}, {result['city']}")
        print(f"  Postal: {result['postal_code']}")
    
    # Test postal code validation
    print("\n=== Test 4: Postal code validation ===")
    print(f"✓ '00-001' valid: {GeocodingService.validate_polish_postal_code('00-001')}")
    print(f"✓ '12345' valid: {GeocodingService.validate_polish_postal_code('12345')}")
