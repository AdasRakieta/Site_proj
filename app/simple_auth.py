"""
Simple Auth Manager for Database Mode
=====================================

Temporary auth manager for database migration testing.
"""

from functools import wraps
from flask import session, redirect, url_for

class SimpleAuthManager:
    """Simple authentication manager for testing"""
    
    def __init__(self, smart_home, multi_db=None):
        self.smart_home = smart_home
        self.multi_db = multi_db
    
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
        """Decorator for requiring admin role (supports multihouse per-home admin roles)"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user_id = session.get('user_id')
            
            # Check multihouse system first (preferred)
            if self.multi_db:
                try:
                    current_home_id = session.get('current_home_id')
                    
                    # Use the centralized admin access check
                    if self.multi_db.has_admin_access(user_id, current_home_id):
                        # Get details for logging
                        if self.multi_db.is_sys_admin(user_id):
                            print(f"[DEBUG] Admin access granted - sys-admin: {user_id}")
                        elif current_home_id:
                            home_role = self.multi_db.get_user_role_in_home(user_id, current_home_id)
                            print(f"[DEBUG] Admin access granted - home role '{home_role}' in home {current_home_id}")
                        else:
                            print(f"[DEBUG] Admin access granted - has admin role in some home")
                        
                        return f(*args, **kwargs)
                    
                    # No admin access found
                    print(f"[DEBUG] Admin access denied for user {user_id}")
                    return redirect(url_for('dashboard'))
                    
                except Exception as e:
                    # Fallback to old system on error
                    print(f"[DEBUG] Multihouse admin check failed, falling back to old system: {e}")
            
            # Fallback to old system
            user = self.smart_home.get_user_by_id(user_id)
            if not user:
                return redirect(url_for('dashboard'))
                
            user_role = user.get('role')
            # Sys-admin has global access
            if user_role == 'sys-admin':
                return f(*args, **kwargs)
            elif user_role not in ['admin', 'user']:  # Keep backward compatibility
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    def api_admin_required(self, f):
        """Decorator for requiring admin role on API endpoints (supports multihouse per-home admin roles)"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import jsonify
            
            if 'user_id' not in session:
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            
            user_id = session.get('user_id')
            
            # Check multihouse system first (preferred)
            if self.multi_db:
                try:
                    current_home_id = session.get('current_home_id')
                    
                    # Use the centralized admin access check
                    if self.multi_db.has_admin_access(user_id, current_home_id):
                        return f(*args, **kwargs)
                    
                    # No admin access found
                    return jsonify({"status": "error", "message": "Admin privileges required"}), 403
                    
                except Exception as e:
                    # Fallback to old system on error
                    print(f"[DEBUG] Multihouse API admin check failed, falling back to old system: {e}")
            
            # Fallback to old system
            user = self.smart_home.get_user_by_id(user_id)
            if not user:
                return jsonify({"status": "error", "message": "Admin privileges required"}), 403
                
            user_role = user.get('role')
            # Sys-admin has global access
            if user_role == 'sys-admin':
                return f(*args, **kwargs)
            elif user_role not in ['admin', 'user']:  # Keep backward compatibility 
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
