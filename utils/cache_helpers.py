"""
Cache Invalidation Helpers
===========================

Common utilities for cache invalidation operations.
Eliminates repetitive try-except blocks for cache operations.
"""

import logging

logger = logging.getLogger(__name__)


def safe_cache_delete(cache_manager, cache_keys, context=""):
    """
    Safely delete cache keys with error handling.
    
    Args:
        cache_manager: Cache manager instance with 'delete' method
        cache_keys: Single key (str) or list of keys to delete
        context: Optional context string for logging (e.g., "temperature_controls")
    
    Returns:
        bool: True if successful, False if error occurred
    """
    if not cache_manager:
        return False
    
    # Normalize to list
    if isinstance(cache_keys, str):
        cache_keys = [cache_keys]
    
    try:
        for key in cache_keys:
            cache_manager.delete(key)
        return True
    except Exception as e:
        context_str = f" ({context})" if context else ""
        logger.debug(f"Failed to invalidate cache{context_str}: {e}")
        return False


def safe_cache_delete_pattern(cache_manager, pattern, context=""):
    """
    Safely delete cache keys matching a pattern with error handling.
    
    Args:
        cache_manager: Cache manager instance
        pattern: Pattern to match cache keys
        context: Optional context string for logging
    
    Returns:
        bool: True if successful, False if error occurred
    """
    if not cache_manager:
        return False
    
    try:
        if hasattr(cache_manager, 'delete_pattern'):
            cache_manager.delete_pattern(pattern)
        return True
    except Exception as e:
        context_str = f" ({context})" if context else ""
        logger.debug(f"Failed to invalidate cache pattern{context_str}: {e}")
        return False
