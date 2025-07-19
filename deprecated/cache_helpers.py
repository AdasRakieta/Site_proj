"""
Cache helpers for Site_proj
Provides cached versions of commonly accessed data
"""
from functools import wraps
from flask import jsonify, request, session


def cache_json_response(cache, timeout=300):
    """
    Decorator to cache JSON responses based on URL and user
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key based on endpoint, args, and user
            user_id = session.get('user_id', 'anonymous')
            cache_key = f"api_{f.__name__}_{user_id}_{request.method}_{args}_{request.args.to_dict()}"
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Execute the function and cache the result
            response = f(*args, **kwargs)
            
            # Only cache successful GET responses
            if request.method == 'GET' and hasattr(response, 'status_code') and response.status_code == 200:
                cache.set(cache_key, response, timeout=timeout)
            
            return response
        return decorated_function
    return decorator


def invalidate_api_cache(cache, pattern):
    """
    Invalidate cache entries matching a pattern
    """
    # Note: This is a simplified version. In production, you might want to use Redis SCAN
    # or maintain a list of cache keys
    cache.delete_many(pattern)


class CachedDataAccess:
    """
    Cached data access layer for frequently used data
    """
    def __init__(self, cache, smart_home):
        self.cache = cache
        self.smart_home = smart_home
    
    def get_rooms(self, timeout=300):
        """Get cached rooms list"""
        cache_key = "rooms_list"
        rooms = self.cache.get(cache_key)
        if rooms is None:
            rooms = self.smart_home.rooms
            self.cache.set(cache_key, rooms, timeout=timeout)
        return rooms
    
    def get_buttons(self, timeout=300):
        """Get cached buttons list"""
        cache_key = "buttons_list"
        buttons = self.cache.get(cache_key)
        if buttons is None:
            buttons = self.smart_home.buttons
            self.cache.set(cache_key, buttons, timeout=timeout)
        return buttons
    
    def get_temperature_controls(self, timeout=300):
        """Get cached temperature controls"""
        cache_key = "temperature_controls"
        controls = self.cache.get(cache_key)
        if controls is None:
            controls = self.smart_home.temperature_controls
            self.cache.set(cache_key, controls, timeout=timeout)
        return controls
    
    def get_automations(self, timeout=300):
        """Get cached automations list"""
        cache_key = "automations_list"
        automations = self.cache.get(cache_key)
        if automations is None:
            automations = self.smart_home.automations
            self.cache.set(cache_key, automations, timeout=timeout)
        return automations
    
    def invalidate_rooms_cache(self):
        """Invalidate rooms-related cache"""
        self.cache.delete_many([
            "rooms_list",
            "buttons_list",
            "temperature_controls"
        ])
    
    def invalidate_buttons_cache(self):
        """Invalidate buttons cache"""
        self.cache.delete("buttons_list")
    
    def invalidate_temperature_cache(self):
        """Invalidate temperature controls cache"""
        self.cache.delete("temperature_controls")
    
    def invalidate_automations_cache(self):
        """Invalidate automations cache"""
        self.cache.delete("automations_list")