"""
Cache Manager for Site_proj

This file provides comprehensive caching functionality for the smart home application.
It handles caching of frequently accessed data like user information, configuration,
and API responses to improve application performance.

Features:
- Redis/SimpleCache integration through Flask-Caching
- Automatic cache invalidation on data updates
- Cached data access layer for smart home entities
- API response caching decorators
- User-specific cache management

Usage:
    The caching is automatically integrated into the application through
    monkey-patching of SmartHomeSystem methods. No manual cache management
    is required for basic operations.

Dependencies:
    - Flask-Caching
    - Redis (optional, falls back to SimpleCache)
"""
from functools import wraps
import logging

# Flask imports (optional for standalone usage)
try:
    from flask import jsonify, request, session
except ImportError:
    # Allow module to be imported without Flask for testing
    jsonify = request = session = None

logger = logging.getLogger(__name__)

# Cache statistics for monitoring
cache_stats = {
    'hits': 0,
    'misses': 0,
    'total_requests': 0
}

def get_cache_hit_rate():
    """Get current cache hit rate percentage"""
    if cache_stats['total_requests'] == 0:
        return 0.0
    return (cache_stats['hits'] / cache_stats['total_requests']) * 100

def reset_cache_stats():
    """Reset cache statistics"""
    global cache_stats
    cache_stats = {'hits': 0, 'misses': 0, 'total_requests': 0}


class CacheManager:
    """
    Central cache management class for the application
    Provides unified interface for all caching operations
    """
    
    def __init__(self, cache, smart_home=None):
        """
        Initialize cache manager
        
        Args:
            cache: Flask-Caching instance
            smart_home: SmartHomeSystem instance (optional)
        """
        self.cache = cache
        self.smart_home = smart_home
        self._cache_timeouts = {
            'user_data': 1800,      # 30 minutes - user profiles rarely change
            'config': 900,          # 15 minutes - configuration is relatively stable
            'rooms': 1800,          # 30 minutes - room structure rarely changes
            'buttons': 600,         # 10 minutes - device states may change more frequently
            'temperature': 300,     # 5 minutes - temperature changes more frequently
            'automations': 900,     # 15 minutes - automations are configured less frequently
            'api_response': 600,    # 10 minutes - API responses can be cached longer
            'session_user': 3600    # 1 hour - session-level user cache
        }
    
    def get_timeout(self, cache_type):
        """Get cache timeout for specific data type"""
        return self._cache_timeouts.get(cache_type, 300)
    
    def invalidate_user_cache(self, user_id):
        """Invalidate cache for a specific user"""
        logger.info(f"Invalidating cache for user: {user_id}")
        # Invalidate both regular and session-specific caches
        self.cache.delete(f"user_data_{user_id}")
        # Note: Cannot efficiently delete all session caches for a user with SimpleCache
        # In production with Redis, use pattern matching
        self.cache.delete("smart_home_config")
    
    def invalidate_session_user_cache(self, session_id, user_id=None):
        """
        Invalidate session-specific user cache
        
        Args:
            session_id: Session ID to invalidate
            user_id: Optional specific user ID, if None invalidates session entirely
        """
        if user_id:
            logger.info(f"Invalidating session cache for user {user_id} in session {session_id}")
            self.cache.delete(f"session_user_{session_id}_{user_id}")
        else:
            logger.info(f"Invalidating all session cache for session {session_id}")
            # Note: With SimpleCache, we can't efficiently pattern-match
            # In production with Redis, use SCAN with pattern session_user_{session_id}_*
    
    def invalidate_config_cache(self):
        """Invalidate configuration-related cache"""
        logger.info("Invalidating configuration cache")
        cache_keys = [
            "smart_home_config",
            "rooms_list", 
            "buttons_list",
            "temperature_controls",
            "automations_list"
        ]
        self.cache.delete_many(*cache_keys)
    
    def get_session_user_data(self, user_id, session_id=None):
        """
        Get user data with session-level caching optimization
        
        This method provides aggressive caching for user data within the same session,
        reducing database calls significantly for active users.
        
        Args:
            user_id: User ID to fetch data for
            session_id: Optional session ID for per-session caching
            
        Returns:
            User data dictionary
        """
        global cache_stats
        cache_stats['total_requests'] += 1
        
        if not user_id:
            return None
            
        # Create session-specific cache key if session_id provided
        if session_id:
            session_cache_key = f"session_user_{session_id}_{user_id}"
            user_data = self.cache.get(session_cache_key)
            if user_data is not None:
                cache_stats['hits'] += 1
                logger.debug(f"Session cache hit for user: {user_id} (hit rate: {get_cache_hit_rate():.1f}%)")
                return user_data
        
        # Fall back to regular user cache
        cache_key = f"user_data_{user_id}"
        user_data = self.cache.get(cache_key)
        if user_data is None:
            cache_stats['misses'] += 1
            logger.debug(f"Cache miss for user data: {user_id}, fetching from source (hit rate: {get_cache_hit_rate():.1f}%)")
            if self.smart_home and hasattr(self.smart_home, 'get_user_data'):
                user_data = self.smart_home.get_user_data(user_id)
                if user_data:
                    # Cache user data with standard timeout
                    timeout = self.get_timeout('user_data')
                    self.cache.set(cache_key, user_data, timeout=timeout)
                    
                    # Also cache with session-specific key for faster access
                    if session_id:
                        session_timeout = self.get_timeout('session_user')
                        self.cache.set(session_cache_key, user_data, timeout=session_timeout)
                        logger.debug(f"Cached user data for session {session_id} and user {user_id}")
                    
                    logger.debug(f"Cached user data for {user_id} for {timeout}s")
            else:
                logger.warning("SmartHome system not available for user data fetch")
                return None
        else:
            cache_stats['hits'] += 1
            logger.debug(f"Cache hit for user data: {user_id} (hit rate: {get_cache_hit_rate():.1f}%)")
            
            # Update session cache if provided
            if session_id:
                session_cache_key = f"session_user_{session_id}_{user_id}"
                session_timeout = self.get_timeout('session_user')
                self.cache.set(session_cache_key, user_data, timeout=session_timeout)
        
        return user_data
    
    def invalidate_api_cache(self, pattern=None):
        """
        Invalidate API response cache
        
        Args:
            pattern: Optional pattern to match specific cache keys
        """
        logger.info(f"Invalidating API cache with pattern: {pattern}")
        # Note: This is a simplified version. In production with Redis,
        # you would use SCAN or maintain a list of cache keys
        if pattern:
            # For now, just log the pattern - implement Redis SCAN if needed
            logger.warning("Pattern-based cache invalidation not implemented for SimpleCache")
    
    def cache_json_response(self, timeout=None):
        """
        Decorator to cache JSON responses based on URL and user
        
        Args:
            timeout: Cache timeout in seconds (uses default if None)
        """
        if timeout is None:
            timeout = self.get_timeout('api_response')
            
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Create cache key based on endpoint, args, and user
                user_id = (session or {}).get('user_id', 'anonymous')
                # Convert args dict to string to make it hashable
                req_args = getattr(getattr(request, 'args', None), 'to_dict', lambda :{})()
                if isinstance(req_args, dict):
                    req_args_str = '&'.join(f"{k}={v}" for k, v in sorted(req_args.items()))
                else:
                    req_args_str = str(req_args)
                cache_key = f"api_{f.__name__}_{user_id}_{getattr(request, 'method', '')}_{args}_{req_args_str}"
                
                # Try to get from cache
                cached_response = self.cache.get(cache_key)
                if cached_response is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_response
                
                # Execute the function and cache the result
                response = f(*args, **kwargs)
                
                # Only cache successful GET responses
                if getattr(request, 'method', None) == 'GET' and hasattr(response, 'status_code') and response.status_code == 200:
                    self.cache.set(cache_key, response, timeout=timeout)
                    logger.debug(f"Cached response for {cache_key}")
                
                return response
            return decorated_function
        return decorator


class CachedDataAccess:
    """
    Cached data access layer for frequently used smart home data
    
    This class provides cached access to smart home entities like rooms,
    buttons, temperature controls, and automations. It automatically
    handles cache misses by fetching from the source and updating cache.
    
    All methods return the same data format as the original SmartHomeSystem
    methods, ensuring 1:1 functionality preservation.
    """
    
    def __init__(self, cache, smart_home):
        """
        Initialize cached data access
        
        Args:
            cache: Flask-Caching instance
            smart_home: SmartHomeSystem instance
        """
        self.cache = cache
        self.smart_home = smart_home
        self.cache_manager = CacheManager(cache, smart_home)
    
    def get_rooms_lazy(self, room_filter=None):
        """
        Get rooms with lazy loading and optional filtering
        
        Args:
            room_filter: Optional filter function or list of room names
            
        Returns:
            Filtered list of room objects
        """
        cache_key = "rooms_list"
        if room_filter and isinstance(room_filter, list):
            # Create cache key for specific room filter
            filter_key = "_".join(sorted(room_filter))
            cache_key = f"rooms_filtered_{filter_key}"
        
        rooms = self.cache.get(cache_key)
        if rooms is None:
            logger.debug("Cache miss for rooms, fetching from source")
            all_rooms = self.smart_home.rooms
            
            # Apply filter if provided
            if room_filter:
                if callable(room_filter):
                    rooms = [room for room in all_rooms if room_filter(room)]
                elif isinstance(room_filter, list):
                    rooms = [room for room in all_rooms if room in room_filter]
                else:
                    rooms = all_rooms
            else:
                rooms = all_rooms
            
            timeout = self.cache_manager.get_timeout('rooms')
            self.cache.set(cache_key, rooms, timeout=timeout)
            logger.debug(f"Cached filtered rooms data for {timeout}s")
        else:
            logger.debug("Cache hit for filtered rooms")
        return rooms
    
    def get_buttons_by_room(self, room_name):
        """
        Get buttons for a specific room with caching
        
        Args:
            room_name: Name of the room to get buttons for
            
        Returns:
            List of button objects for the specified room
        """
        cache_key = f"buttons_room_{room_name}"
        buttons = self.cache.get(cache_key)
        if buttons is None:
            logger.debug(f"Cache miss for buttons in room {room_name}")
            all_buttons = self.smart_home.buttons
            # Filter buttons for specific room
            buttons = [btn for btn in all_buttons if btn.get('room') == room_name]
            timeout = self.cache_manager.get_timeout('buttons')
            self.cache.set(cache_key, buttons, timeout=timeout)
            logger.debug(f"Cached buttons for room {room_name} for {timeout}s")
        else:
            logger.debug(f"Cache hit for buttons in room {room_name}")
        return buttons
    
    def get_temperature_controls_by_room(self, room_name):
        """
        Get temperature controls for a specific room with caching
        
        Args:
            room_name: Name of the room to get temperature controls for
            
        Returns:
            List of temperature control objects for the specified room
        """
        cache_key = f"temp_controls_room_{room_name}"
        controls = self.cache.get(cache_key)
        if controls is None:
            logger.debug(f"Cache miss for temperature controls in room {room_name}")
            all_controls = self.smart_home.temperature_controls
            # Filter controls for specific room
            controls = [ctrl for ctrl in all_controls if ctrl.get('room') == room_name]
            timeout = self.cache_manager.get_timeout('temperature')
            self.cache.set(cache_key, controls, timeout=timeout)
            logger.debug(f"Cached temperature controls for room {room_name} for {timeout}s")
        else:
            logger.debug(f"Cache hit for temperature controls in room {room_name}")
        return controls
    
    def get_rooms(self):
        """
        Get cached rooms list
        
        Returns:
            List of room objects, same format as smart_home.rooms
        """
        cache_key = "rooms_list"
        rooms = self.cache.get(cache_key)
        if rooms is None:
            logger.debug("Cache miss for rooms, fetching from source")
            rooms = self.smart_home.rooms
            timeout = self.cache_manager.get_timeout('rooms')
            self.cache.set(cache_key, rooms, timeout=timeout)
            logger.debug(f"Cached rooms data for {timeout}s")
        else:
            logger.debug("Cache hit for rooms")
        return rooms
    
    def get_buttons(self):
        """
        Get cached buttons list
        
        Returns:
            List of button objects, same format as smart_home.buttons
        """
        cache_key = "buttons_list"
        print(f"[DEBUG] get_buttons called, checking cache key: {cache_key}")
        buttons = self.cache.get(cache_key)
        if buttons is None:
            print(f"[DEBUG] Cache miss for buttons, fetching from source")
            logger.debug("Cache miss for buttons, fetching from source")
            buttons = self.smart_home.buttons
            print(f"[DEBUG] Fetched buttons from smart_home: {buttons}")
            timeout = self.cache_manager.get_timeout('buttons')
            self.cache.set(cache_key, buttons, timeout=timeout)
            logger.debug(f"Cached buttons data for {timeout}s")
        else:
            print(f"[DEBUG] Cache hit for buttons: {buttons}")
            logger.debug("Cache hit for buttons")
        return buttons
    
    def get_temperature_controls(self):
        """
        Get cached temperature controls
        
        Returns:
            List of temperature control objects, same format as smart_home.temperature_controls
        """
        cache_key = "temperature_controls"
        controls = self.cache.get(cache_key)
        if controls is None:
            logger.debug("Cache miss for temperature controls, fetching from source")
            controls = self.smart_home.temperature_controls
            timeout = self.cache_manager.get_timeout('temperature')
            self.cache.set(cache_key, controls, timeout=timeout)
            logger.debug(f"Cached temperature controls for {timeout}s")
        else:
            logger.debug("Cache hit for temperature controls")
        return controls
    
    def get_automations(self):
        """
        Get cached automations list
        
        Returns:
            List of automation objects, same format as smart_home.automations
        """
        cache_key = "automations_list"
        automations = self.cache.get(cache_key)
        if automations is None:
            logger.debug("Cache miss for automations, fetching from source")
            automations = self.smart_home.automations
            timeout = self.cache_manager.get_timeout('automations')
            self.cache.set(cache_key, automations, timeout=timeout)
            logger.debug(f"Cached automations data for {timeout}s")
        else:
            logger.debug("Cache hit for automations")
        return automations
    
    def get_config(self):
        """
        Get cached configuration
        
        Returns:
            Configuration object, same format as smart_home.config
        """
        cache_key = "smart_home_config"
        config = self.cache.get(cache_key)
        if config is None:
            logger.debug("Cache miss for config, fetching from source")
            config = self.smart_home.config
            timeout = self.cache_manager.get_timeout('config')
            self.cache.set(cache_key, config, timeout=timeout)
            logger.debug(f"Cached config data for {timeout}s")
        else:
            logger.debug("Cache hit for config")
        return config
    
    def invalidate_rooms_cache(self):
        """Invalidate rooms-related cache"""
        logger.info("Invalidating rooms cache")
        self.cache.delete_many([
            "rooms_list",
            "buttons_list", 
            "temperature_controls"
        ])
    
    def invalidate_buttons_cache(self):
        """Invalidate buttons cache"""
        print(f"[DEBUG] invalidate_buttons_cache called")
        logger.info("Invalidating buttons cache")
        result = self.cache.delete("buttons_list")
        print(f"[DEBUG] Cache delete result: {result}")
        # Force a cache miss by checking if key was actually deleted
        check = self.cache.get("buttons_list")
        print(f"[DEBUG] Cache check after delete: {check}")
        return result
    
    def invalidate_temperature_cache(self):
        """Invalidate temperature controls cache"""
        logger.info("Invalidating temperature cache")
        self.cache.delete("temperature_controls")
    
    def invalidate_automations_cache(self):
        """Invalidate automations cache"""
        logger.info("Invalidating automations cache")
        self.cache.delete("automations_list")
    
    def invalidate_config_cache(self):
        """Invalidate configuration cache"""
        logger.info("Invalidating config cache")
        self.cache.delete("smart_home_config")


def setup_smart_home_caching(smart_home, cache_manager):
    """
    Setup caching for SmartHomeSystem methods
    
    This function monkey-patches SmartHomeSystem methods to include
    automatic cache invalidation. This ensures data consistency
    while maintaining the original API.
    
    Args:
        smart_home: SmartHomeSystem instance to patch
        cache_manager: CacheManager instance for invalidation
        
    Returns:
        Dictionary of original methods for potential restoration
    """
    logger.info("Setting up smart home caching")
    
    # Store original methods for potential restoration
    original_methods = {}
    
    # Cache user data getter
    if hasattr(smart_home, 'get_user_data'):
        original_methods['get_user_data'] = smart_home.get_user_data
        
        def cached_get_user_data(user_id):
            """Cached version of get_user_data"""
            cache_key = f"user_data_{user_id}"
            user_data = cache_manager.cache.get(cache_key)
            if user_data is None:
                logger.debug(f"Cache miss for user data: {user_id}")
                user_data = original_methods['get_user_data'](user_id)
                timeout = cache_manager.get_timeout('user_data')
                cache_manager.cache.set(cache_key, user_data, timeout=timeout)
                logger.debug(f"Cached user data for {user_id} for {timeout}s")
            else:
                logger.debug(f"Cache hit for user data: {user_id}")
            return user_data
        
        smart_home.get_user_data = cached_get_user_data
    
    # Cache config save method
    if hasattr(smart_home, 'save_config'):
        original_methods['save_config'] = smart_home.save_config
        
        def cached_save_config():
            """Config save with cache invalidation"""
            logger.info("Saving config and invalidating cache")
            result = original_methods['save_config']()
            cache_manager.invalidate_config_cache()
            return result
        
        smart_home.save_config = cached_save_config
    
    # Cache user profile update method
    if hasattr(smart_home, 'update_user_profile'):
        original_methods['update_user_profile'] = smart_home.update_user_profile
        
        def cached_update_user_profile(username, updates):
            """User profile update with cache invalidation"""
            logger.info(f"Updating user profile for {username}")
            result = original_methods['update_user_profile'](username, updates)
            
            # Invalidate user cache for old and potentially new username
            cache_manager.invalidate_user_cache(username)
            if 'username' in updates:
                cache_manager.invalidate_user_cache(updates['username'])
            
            return result
        
        smart_home.update_user_profile = cached_update_user_profile

    # Device update method (buttons / temperature controls)
    if hasattr(smart_home, 'update_device'):
        original_methods['update_device'] = smart_home.update_device

        def cached_update_device(device_id, updates):
            """Device update with cache invalidation for buttons & temperature controls"""
            logger.debug(f"Cached update_device called: id={device_id}, updates={updates}")
            result = original_methods['update_device'](device_id, updates)
            if result:
                # Always invalidate both device-related caches (cheap & safe)
                try:
                    smart_home_cache = cache_manager.cache
                    smart_home_cache.delete('buttons_list')
                    smart_home_cache.delete('temperature_controls')
                    # Room-specific caches (best-effort) - only possible with Redis pattern scan; here just log
                    logger.debug("Invalidated buttons_list & temperature_controls caches after device update")
                except Exception as e:
                    logger.warning(f"Failed to invalidate device caches: {e}")
            else:
                logger.debug("update_device returned False; caches not invalidated")
            return result

        smart_home.update_device = cached_update_device
    
    logger.info("Smart home caching setup complete")
    return original_methods