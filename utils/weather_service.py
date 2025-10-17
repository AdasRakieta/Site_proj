"""
Weather Service using IMGW API for Poland
Fetches weather data from nearest IMGW meteorological station
"""

import os
import logging
import requests
from typing import Dict, Optional, Any, Tuple
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Weather service using IMGW (Instytut Meteorologii i Gospodarki Wodnej) API
    Data source: https://danepubliczne.imgw.pl/
    """
    
    # IMGW API endpoint
    IMGW_BASE_URL = "https://danepubliczne.imgw.pl/api/data/synop"
    
    # Mapa stacji IMGW z ich współrzędnymi geograficznymi i nazwami bez polskich znaków
    # Źródło: dane IMGW + OpenStreetMap
    # Format: "station_slug": {"name": "Display Name", "lat": float, "lon": float}
    IMGW_STATIONS = {
        "bialystok": {"name": "Białystok", "lat": 53.1325, "lon": 23.1688},
        "bielsko-biala": {"name": "Bielsko-Biała", "lat": 49.8224, "lon": 19.0448},
        "chojnice": {"name": "Chojnice", "lat": 53.6975, "lon": 17.5580},
        "czestochowa": {"name": "Częstochowa", "lat": 50.8118, "lon": 19.1203},
        "elblag": {"name": "Elbląg", "lat": 54.1522, "lon": 19.4044},
        "gdansk": {"name": "Gdańsk", "lat": 54.3520, "lon": 18.6466},
        "gorzow": {"name": "Gorzów Wlkp.", "lat": 52.7325, "lon": 15.2369},
        "hel": {"name": "Hel", "lat": 54.6080, "lon": 18.8170},
        "jeleniagora": {"name": "Jelenia Góra", "lat": 50.9007, "lon": 15.7841},
        "kalisz": {"name": "Kalisz", "lat": 51.7615, "lon": 18.0747},
        "katowice": {"name": "Katowice", "lat": 50.2649, "lon": 19.0238},
        "kielce": {"name": "Kielce", "lat": 50.8661, "lon": 20.6286},
        "koszalin": {"name": "Koszalin", "lat": 54.1943, "lon": 16.1714},
        "krakow": {"name": "Kraków", "lat": 50.0647, "lon": 19.9450},
        "legnica": {"name": "Legnica", "lat": 51.2070, "lon": 16.1619},
        "leszno": {"name": "Leszno", "lat": 51.8404, "lon": 16.5826},
        "lublin": {"name": "Lublin", "lat": 51.2465, "lon": 22.5684},
        "lodz": {"name": "Łódź", "lat": 51.7592, "lon": 19.4560},
        "leba": {"name": "Łeba", "lat": 54.7527, "lon": 17.5331},
        "mlawa": {"name": "Mława", "lat": 53.1117, "lon": 20.3747},
        "olsztyn": {"name": "Olsztyn", "lat": 53.7799, "lon": 20.4942},
        "opole": {"name": "Opole", "lat": 50.6751, "lon": 17.9213},
        "pila": {"name": "Piła", "lat": 53.1510, "lon": 16.7379},
        "plock": {"name": "Płock", "lat": 52.5463, "lon": 19.7065},
        "kolobrzeg": {"name": "Kołobrzeg", "lat": 54.1761, "lon": 15.5836},
        "poznan": {"name": "Poznań", "lat": 52.4064, "lon": 16.9252},
        "pulawy": {"name": "Puławy", "lat": 51.4167, "lon": 21.9692},
        "raciborz": {"name": "Racibórz", "lat": 50.0911, "lon": 18.2189},
        "siedlce": {"name": "Siedlce", "lat": 52.1676, "lon": 22.2902},
        "sniezka": {"name": "Śnieżka", "lat": 50.7359, "lon": 15.7398},
        "szczecin": {"name": "Szczecin", "lat": 53.4285, "lon": 14.5528},
        "swinoujscie": {"name": "Świnoujście", "lat": 53.9174, "lon": 14.2478},
        "tarnow": {"name": "Tarnów", "lat": 50.0121, "lon": 20.9881},
        "terespol": {"name": "Terespol", "lat": 52.0757, "lon": 23.6173},
        "torun": {"name": "Toruń", "lat": 53.0138, "lon": 18.5984},
        "ustka": {"name": "Ustka", "lat": 54.5805, "lon": 16.8615},
        "warszawa": {"name": "Warszawa", "lat": 52.2297, "lon": 21.0122},
        "wroclaw": {"name": "Wrocław", "lat": 51.1079, "lon": 16.8773},
        "zielonagora": {"name": "Zielona Góra", "lat": 51.9356, "lon": 15.5062},
        "suwalki": {"name": "Suwałki", "lat": 54.1115, "lon": 22.9308},
        "rzeszow": {"name": "Rzeszów", "lat": 50.0412, "lon": 21.9991},
        "ketrzyn": {"name": "Kętrzyn", "lat": 54.0769, "lon": 21.3772},
        "bydgoszcz": {"name": "Bydgoszcz", "lat": 53.1235, "lon": 18.0084},
    }
    
    @classmethod
    def _haversine_distance(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on the earth (in kilometers)
        
        Args:
            lat1, lon1: Coordinates of first point
            lat2, lon2: Coordinates of second point
            
        Returns:
            Distance in kilometers
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    @classmethod
    def find_nearest_imgw_station(cls, latitude: float, longitude: float) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Find the nearest IMGW weather station to given coordinates
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            
        Returns:
            Tuple of (station_id, station_data) or None if not found
        """
        if not latitude or not longitude:
            return None
        
        nearest_station_id = None
        nearest_station_data = None
        min_distance = float('inf')
        
        for station_id, station_info in cls.IMGW_STATIONS.items():
            distance = cls._haversine_distance(
                latitude, longitude,
                station_info['lat'], station_info['lon']
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_station_id = station_id
                nearest_station_data = {
                    **station_info,
                    'distance_km': round(distance, 1)
                }
        
        if nearest_station_id:
            logger.info(f"Found nearest IMGW station: {nearest_station_data['name']} "
                       f"(ID: {nearest_station_id}, {nearest_station_data['distance_km']} km away)")
        
        return (nearest_station_id, nearest_station_data) if nearest_station_id else None
    
    @classmethod
    def get_weather_imgw_fallback(cls, station_slug: str = "krakow") -> Optional[Dict[str, Any]]:
        """
        Get weather from specific IMGW station
        
        Args:
            station_slug: IMGW station slug (default: "krakow" for Kraków)
            
        Returns:
            Dictionary with weather data or None if failed
        """
        url = f"{cls.IMGW_BASE_URL}/station/{station_slug}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched IMGW weather for station {station_slug}")
                return data
        except requests.RequestException as e:
            logger.error(f"IMGW weather request failed: {e}")
        return None
    
    @classmethod
    def get_weather_by_station_slug(cls, station_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get weather data from IMGW API for a specific station
        
        Args:
            station_slug: IMGW station slug (name without Polish characters)
            
        Returns:
            Dictionary with weather data in standardized format or None if failed
        """
        url = f"{cls.IMGW_BASE_URL}/station/{station_slug}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # IMGW returns data in Polish format, keep it as is
            logger.info(f"Successfully fetched weather from IMGW station {station_slug}: "
                       f"{data.get('stacja', 'Unknown')} - {data.get('temperatura', 'N/A')}°C")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"IMGW station {station_slug} request failed: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing IMGW response for station {station_slug}: {e}")
            return None
    
    @classmethod
    def get_weather_for_home(cls, home_data: Dict[str, Any], db_manager=None) -> Optional[Dict[str, Any]]:
        """
        Get weather data for a specific home based on its location
        Uses nearest IMGW station
        
        Args:
            home_data: Dictionary with home information (must include latitude, longitude, city)
            db_manager: Not used for IMGW, kept for compatibility
            
        Returns:
            Dictionary with weather data or None if failed
        """
        latitude = home_data.get('latitude')
        longitude = home_data.get('longitude')
        city_name = home_data.get('city')
        
        # If no coordinates, cannot determine nearest station
        if not latitude or not longitude:
            logger.warning(f"Home '{home_data.get('name', 'Unknown')}' has no location coordinates")
            # Fallback to default Kraków station
            return cls.get_weather_imgw_fallback()
        
        # Find nearest IMGW stations (try top 5 in case some are unavailable)
        station_distances = []
        for station_slug, station_info in cls.IMGW_STATIONS.items():
            distance = cls._haversine_distance(
                latitude, longitude,
                station_info['lat'], station_info['lon']
            )
            station_distances.append((station_slug, station_info, distance))
        
        # Sort by distance
        station_distances.sort(key=lambda x: x[2])
        
        # Try to get weather from nearest available stations
        for station_slug, station_info, distance in station_distances[:5]:
            logger.info(f"Trying IMGW station: {station_info['name']} "
                       f"(slug: {station_slug}, {round(distance, 1)} km away)")
            
            weather_data = cls.get_weather_by_station_slug(station_slug)
            
            if weather_data:
                # Add distance info if station is not very close
                distance_km = round(distance, 1)
                if distance_km > 5:  # More than 5km away
                    weather_data['nearest_city'] = True
                    weather_data['distance_km'] = distance_km
                    weather_data['original_city'] = city_name
                
                return weather_data
        
        # Ultimate fallback - default Kraków station
        logger.warning("Could not fetch weather from any nearby station, using Kraków fallback")
        return cls.get_weather_imgw_fallback()

