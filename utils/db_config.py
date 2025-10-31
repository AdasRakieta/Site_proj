"""
Database Configuration Helpers
===============================

Shared utilities for database configuration validation and connection setup.
This module eliminates code duplication across db_manager, smart_home_db_manager,
and multi_home_db_manager.
"""

import os
from typing import Dict, List, Optional


def get_db_config_from_env() -> Dict[str, str]:
    """
    Get database configuration from environment variables.
    
    Returns:
        dict: Database configuration with keys: host, port, dbname, user, password
    """
    return {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }


def validate_db_config(config: Optional[Dict[str, str]] = None) -> List[str]:
    """
    Validate that required database configuration parameters are present.
    
    Args:
        config: Database configuration dict. If None, reads from environment.
        
    Returns:
        List of missing configuration keys. Empty list if all required keys are present.
    """
    if config is None:
        config = get_db_config_from_env()
    
    required_keys = ['host', 'dbname', 'user', 'password']
    missing = []
    
    for key in required_keys:
        if not config.get(key):
            missing.append(key)
    
    return missing


def validate_db_config_or_raise(config: Optional[Dict[str, str]] = None) -> None:
    """
    Validate database configuration and raise ValueError if any required keys are missing.
    
    Args:
        config: Database configuration dict. If None, reads from environment.
        
    Raises:
        ValueError: If any required configuration parameters are missing
    """
    missing = validate_db_config(config)
    
    if missing:
        # Map config keys to environment variable names
        env_var_map = {
            'host': 'DB_HOST',
            'dbname': 'DB_NAME',
            'user': 'DB_USER',
            'password': 'DB_PASSWORD',
            'port': 'DB_PORT'
        }
        env_vars = [env_var_map.get(k, f'DB_{k.upper()}') for k in missing]
        raise ValueError(
            f"Missing required database configuration: {', '.join(missing)}. "
            f"Please set these environment variables: {', '.join(env_vars)}"
        )
