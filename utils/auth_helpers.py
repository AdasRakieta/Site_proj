"""
Shared Authentication Helpers
==============================

Common authentication decorators and utilities used across blueprints.
This module eliminates code duplication between home_settings_routes and multi_home_routes.
"""

from functools import wraps
from flask import session, redirect, url_for


def login_required(f):
    """
    Decorator for requiring login on page routes.
    
    Returns a redirect to login page if user is not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """
    Get current logged in user from session.
    
    Returns:
        dict: User dictionary with 'id' key if logged in, None otherwise
    """
    user_id = session.get('user_id')
    if user_id:
        return {'id': user_id}
    return None
