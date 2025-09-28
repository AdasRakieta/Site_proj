"""
Multi-home routes for the SmartHome application.
Handles home selection, creation, and management.
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
from utils.multi_home_db_manager import MultiHomeDBManager
import logging

logger = logging.getLogger(__name__)

# Create blueprint
multi_home_bp = Blueprint('multi_home', __name__)

# Authentication helpers for multi-home routes
def login_required(f):
    """Decorator for requiring login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged in user from session"""
    user_id = session.get('user_id')
    if user_id:
        # For now, return a simple user dict - this should integrate with your user system
        return {'id': user_id}
    return None

# Initialize multi-home database manager
try:
    multi_db = MultiHomeDBManager(
        host="100.103.184.90",
        port=5432,
        user="admin", 
        password="Qwuizzy123.",
        database="smarthome_multihouse"
    )
except Exception as e:
    logger.error(f"Failed to initialize MultiHomeDBManager: {e}")
    multi_db = None

@multi_home_bp.route('/home/select')
@login_required
def home_select():
    """Display home selection page."""
    if not multi_db:
        flash("Multi-home functionality is not available", "error")
        return redirect(url_for('main.index'))
    
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    user_id = user['id']
    
    try:
        # Get all homes user has access to
        homes = multi_db.get_user_homes(user_id)
        
        # Get current home ID
        current_home_id = multi_db.get_user_current_home(user_id)
        
        # Add statistics to homes
        for home in homes:
            try:
                rooms = multi_db.get_home_rooms(home['id'], user_id)
                devices = multi_db.get_home_devices(home['id'], user_id)
                
                home['room_count'] = len(rooms)
                home['device_count'] = len(devices)
                home['user_count'] = 1  # TODO: Get actual user count
            except Exception as e:
                logger.error(f"Error getting stats for home {home['id']}: {e}")
                home['room_count'] = 0
                home['device_count'] = 0
                home['user_count'] = 1
        
        return render_template('home_select.html', 
                             homes=homes, 
                             current_home_id=current_home_id)
    
    except Exception as e:
        logger.error(f"Error loading home selection: {e}")
        flash("Error loading homes", "error")
        return redirect(url_for('main.index'))

@multi_home_bp.route('/api/home/select', methods=['POST'])
@login_required
def api_home_select():
    """API endpoint to select/switch current home."""
    if not multi_db:
        return jsonify({"success": False, "error": "Multi-home functionality not available"})
    
    try:
        data = request.get_json()
        home_id = data.get('home_id')
        
        if not home_id:
            return jsonify({"success": False, "error": "Home ID required"})
        
        user_id = get_current_user()['id']
        
        # Verify user has access to this home
        if not multi_db.user_has_home_access(user_id, home_id):
            return jsonify({"success": False, "error": "Access denied to this home"})
        
        # Set current home in session and database
        session_token = session.get('session_token')
        success = multi_db.set_user_current_home(user_id, home_id, session_token)
        
        if success:
            # Also store in Flask session for immediate use
            session['current_home_id'] = home_id
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to switch home"})
    
    except Exception as e:
        logger.error(f"Error switching home: {e}")
        return jsonify({"success": False, "error": "Internal server error"})

@multi_home_bp.route('/home/create')
@login_required
def home_create():
    """Display create home form."""
    return render_template('home_create.html')

@multi_home_bp.route('/api/home/create', methods=['POST'])
@login_required
def api_home_create():
    """API endpoint to create a new home."""
    if not multi_db:
        return jsonify({"success": False, "error": "Multi-home functionality not available"})
    
    try:
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip() or None
        
        if not name:
            return jsonify({"success": False, "error": "Home name is required"})
        
        if len(name) > 100:
            return jsonify({"success": False, "error": "Home name too long (max 100 characters)"})
        
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"})
        user_id = user['id']
        
        # Create the home
        home_id = multi_db.create_home(name, user_id, description)
        
        # Set as current home
        session_token = session.get('session_token')
        multi_db.set_user_current_home(user_id, home_id, session_token)
        session['current_home_id'] = home_id
        
        if request.is_json:
            return jsonify({"success": True, "home_id": home_id})
        else:
            flash(f"Home '{name}' created successfully!", "success")
            return redirect(url_for('multi_home.home_select'))
    
    except Exception as e:
        logger.error(f"Error creating home: {e}")
        if request.is_json:
            return jsonify({"success": False, "error": "Failed to create home"})
        else:
            flash("Error creating home", "error")
            return redirect(url_for('multi_home.home_create'))

@multi_home_bp.route('/home/join')
@login_required
def home_join():
    """Display join home form."""
    return render_template('home_join.html')

@multi_home_bp.route('/api/home/join', methods=['POST'])
@login_required
def api_home_join():
    """API endpoint to join a home via invitation code."""
    if not multi_db:
        return jsonify({"success": False, "error": "Multi-home functionality not available"})
    
    try:
        data = request.get_json() if request.is_json else request.form
        
        invitation_code = data.get('invitation_code', '').strip()
        
        if not invitation_code:
            return jsonify({"success": False, "error": "Invitation code is required"})
        
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"})
        user_id = user['id']
        
        # TODO: Implement invitation system
        # For now, return not implemented
        return jsonify({"success": False, "error": "Invitation system not yet implemented"})
    
    except Exception as e:
        logger.error(f"Error joining home: {e}")
        if request.is_json:
            return jsonify({"success": False, "error": "Failed to join home"})
        else:
            flash("Error joining home", "error")
            return redirect(url_for('multi_home.home_join'))

@multi_home_bp.route('/api/current-home')
@login_required
def api_current_home():
    """Get current home information."""
    if not multi_db:
        return jsonify({"success": False, "error": "Multi-home functionality not available"})
    
    try:
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"})
        user_id = user['id']
        current_home_id = session.get('current_home_id') or multi_db.get_user_current_home(user_id)
        
        if not current_home_id:
            return jsonify({"success": False, "error": "No current home set"})
        
        home_details = multi_db.get_home_details(current_home_id, user_id)
        
        if not home_details:
            return jsonify({"success": False, "error": "Current home not accessible"})
        
        return jsonify({
            "success": True,
            "home": home_details
        })
    
    except Exception as e:
        logger.error(f"Error getting current home: {e}")
        return jsonify({"success": False, "error": "Internal server error"})

def get_current_home_id():
    """Helper function to get current home ID for authenticated user."""
    if not multi_db:
        return None
        
    try:
        user = get_current_user()
        if not user:
            return None
            
        # Try session first, then database
        home_id = session.get('current_home_id')
        if home_id:
            # Verify user still has access
            if multi_db.user_has_home_access(user['id'], home_id):
                return home_id
        
        # Fall back to database
        home_id = multi_db.get_user_current_home(user['id'])
        if home_id:
            session['current_home_id'] = home_id
            return home_id
        
        # No home found - redirect to home selection
        return None
        
    except Exception as e:
        logger.error(f"Error getting current home ID: {e}")
        return None

def require_home_access(permission='view_devices'):
    """Decorator to require home access and specific permission."""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not multi_db:
                flash("Multi-home functionality is not available", "error")
                return redirect(url_for('main.index'))
            
            home_id = get_current_home_id()
            if not home_id:
                return redirect(url_for('multi_home.home_select'))
            
            user = get_current_user()
            if not user:
                return redirect(url_for('login'))
            user_id = user['id']
            if not multi_db.user_has_home_permission(user_id, home_id, permission):
                flash("You don't have permission to perform this action", "error")
                return redirect(url_for('multi_home.home_select'))
            
            # Add home_id to kwargs for the route function
            kwargs['home_id'] = home_id
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator