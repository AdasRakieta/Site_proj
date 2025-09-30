"""
Simple Auth Manager for Database Mode
=====================================

Temporary auth manager for database migration testing.
"""

from functools import wraps
from flask import session, redirect, url_for

class SimpleAuthManager:
    """Simple authentication manager for testing"""
    
    def __init__(self, smart_home):
        self.smart_home = smart_home
    
    def login_required(self, f):
        """Decorator for requiring login"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def api_login_required(self, f):
        """Decorator for requiring login on API endpoints (returns JSON instead of redirect)"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                from flask import jsonify
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    def admin_required(self, f):
        """Decorator for requiring admin role"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user_id = session.get('user_id')
            user = self.smart_home.get_user_by_id(user_id)
            
            # Check if user is sys-admin (global admin) or has admin privileges
            if not user:
                return redirect(url_for('dashboard'))
                
            user_role = user.get('role')
            # Sys-admin has global access
            if user_role == 'sys-admin':
                pass  # Allow access
            elif user_role not in ['admin', 'user']:  # Keep backward compatibility
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    def api_admin_required(self, f):
        """Decorator for requiring admin role on API endpoints (returns JSON instead of redirect)"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                from flask import jsonify
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            
            user_id = session.get('user_id')
            user = self.smart_home.get_user_by_id(user_id)
            
            # Check if user is sys-admin (global admin) or has admin privileges
            if not user:
                from flask import jsonify
                return jsonify({"status": "error", "message": "Admin privileges required"}), 403
                
            user_role = user.get('role')
            # Sys-admin has global access
            if user_role == 'sys-admin':
                pass  # Allow access
            elif user_role not in ['admin', 'user']:  # Keep backward compatibility 
                from flask import jsonify
                return jsonify({"status": "error", "message": "Admin privileges required"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    def login_user(self, user_id, remember=False):
        """Log in a user"""
        session['user_id'] = user_id
        session.permanent = remember
        return True
    
    def logout_user(self):
        """Log out current user"""
        session.pop('user_id', None)
        return True
    
    def get_current_user(self):
        """Get current logged in user"""
        user_id = session.get('user_id')
        if user_id:
            return self.smart_home.get_user_by_id(user_id)
        return None
