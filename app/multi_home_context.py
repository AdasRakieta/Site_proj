"""
Context processor for multi-home functionality.
Adds current home information to all templates.
"""

from flask import session, g
from app.multi_home_routes import multi_db, get_current_home_id
import logging

logger = logging.getLogger(__name__)

def multi_home_context_processor():
    """Add multi-home context to all templates"""
    if not multi_db:
        return {}
    
    try:
        # Check if user is logged in
        user_id = session.get('user_id')
        if not user_id:
            return {}
        
        # Get current home
        current_home_id = get_current_home_id()
        current_home = None
        user_homes = []
        
        if current_home_id:
            current_home = multi_db.get_home_details(str(current_home_id), user_id)
        
        # Get all user homes for the dropdown
        user_homes = multi_db.get_user_homes(user_id)
        
        # Check admin access
        is_sys_admin = multi_db.is_sys_admin(user_id)
        has_admin_access = multi_db.has_admin_access(user_id, str(current_home_id) if current_home_id else None)
        
        return {
            'multi_home_enabled': True,
            'current_home': current_home,
            'user_homes': user_homes,
            'current_home_id': current_home_id,
            'is_sys_admin': is_sys_admin,
            'has_admin_access': has_admin_access
        }
        
    except Exception as e:
        logger.error(f"Error in multi_home_context_processor: {e}")
        return {
            'multi_home_enabled': False,
            'current_home': None,
            'user_homes': [],
            'current_home_id': None
        }