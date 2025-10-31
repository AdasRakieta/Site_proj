"""
Multi-home routes for the SmartHome application.
Handles home selection, creation, and management.
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from utils.multi_home_db_manager import MultiHomeDBManager
from utils.auth_helpers import login_required, get_current_user
import logging

logger = logging.getLogger(__name__)

# Create blueprint
multi_home_bp = Blueprint('multi_home', __name__)

# This will be set by the main application
multi_db = None

def init_multi_home_routes(db_manager):
    """Initialize multi-home routes with database manager"""
    global multi_db
    if db_manager is None:
        try:
            db_manager = current_app.config.get('MULTI_DB_MANAGER')
        except Exception:
            db_manager = None
    multi_db = db_manager
    logger.info(f"Multi-home routes initialized with db_manager: {db_manager is not None}")

def get_multi_db():
    """Get the multi_db instance"""
    global multi_db
    if multi_db is not None:
        return multi_db
    try:
        app = current_app
    except Exception:
        return None
    db_manager = app.config.get('MULTI_DB_MANAGER')
    if db_manager is not None:
        multi_db = db_manager
    return db_manager


@multi_home_bp.before_app_request
def _ensure_multi_db_loaded():
    """Ensure multi-home DB manager is loaded into module scope before handling requests."""
    get_multi_db()

@multi_home_bp.route('/home/select')
@login_required
def home_select():
    """Display home selection page."""
    print("🏠 Home select page accessed")
    logger.info("🏠 Home select page accessed")
    
    db_manager = get_multi_db()
    if not db_manager:
        print("❌ Multi-home DB not available")
        logger.error("Multi-home DB not available")
        flash("Multi-home functionality is not available", "error")
        return redirect(url_for('home'))
    
    user = get_current_user()
    if not user:
        print("❌ No current user found")
        logger.error("No current user found")
        return redirect(url_for('login'))
    user_id = user['id']
    print(f"👤 Loading homes for user: {user_id}")
    logger.info(f"👤 Loading homes for user: {user_id}")
    
    try:
        # Get all homes user has access to
        homes = db_manager.get_user_homes(user_id)
        print(f"🏠 Found {len(homes)} homes for user")
        logger.info(f"🏠 Found {len(homes)} homes for user")
        
        for home in homes:
            print(f"  - Home: {home['name']} (ID: {home['id']})")
            logger.info(f"  - Home: {home['name']} (ID: {home['id']})")
        
        # Get current home ID
        current_home_id = db_manager.get_user_current_home(user_id)
        print(f"🎯 Current home ID: {current_home_id}")
        logger.info(f"🎯 Current home ID: {current_home_id}")
        
        # Add statistics to homes
        for home in homes:
            try:
                rooms = db_manager.get_home_rooms(home['id'], user_id)
                devices = db_manager.get_home_devices(home['id'], user_id)
                
                home['room_count'] = len(rooms)
                home['device_count'] = len(devices)
                home['user_count'] = 1  # TODO: Get actual user count
            except Exception as e:
                logger.error(f"Error getting stats for home {home['id']}: {e}")
                home['room_count'] = 0
                home['device_count'] = 0
                home['user_count'] = 1
        
        # Get full user data including global role and profile picture
        user_data = db_manager.get_user_by_id(user_id)
        # Derive global role reliably from DB
        user_global_role = (user_data.get('role') if user_data else None) or 'user'
        if not user_data:
            user_data = {
                'id': user_id,
                'name': user_id,
                'email': '',
                'role': user_global_role,
                'profile_picture': ''
            }
        
        return render_template('home_select.html', 
                             homes=homes, 
                             current_home_id=current_home_id,
                             user_global_role=user_global_role,
                             user_data=user_data)
    
    except Exception as e:
        logger.error(f"Error loading home selection: {e}")
        flash("Error loading homes", "error")
        return redirect(url_for('home'))

@multi_home_bp.route('/api/home/select', methods=['POST'])
@login_required
def api_home_select():
    """API endpoint to select/switch current home."""
    logger.info("🏠 API home select endpoint called")
    
    db_manager = get_multi_db()
    if not db_manager:
        logger.error("Multi-home DB not available")
        return jsonify({"success": False, "error": "Multi-home functionality not available"})
    
    try:
        data = request.get_json()
        logger.info(f"📥 Received data: {data}")
        home_id = data.get('home_id')
        
        if not home_id:
            logger.error("No home_id provided")
            return jsonify({"success": False, "error": "Home ID required"})
        
        user = get_current_user()
        if not user:
            logger.error("No current user found")
            return jsonify({"success": False, "error": "Authentication required"})
        
        user_id = user['id']
        logger.info(f"👤 User ID: {user_id}, switching to home: {home_id}")
        
        # Verify user has access to this home
        has_access = db_manager.user_has_home_access(user_id, home_id)
        logger.info(f"🔑 User has access to home {home_id}: {has_access}")
        
        if not has_access:
            return jsonify({"success": False, "error": "Access denied to this home"})
        
        # Set current home in session and database
        session_token = session.get('session_token')
        logger.info(f"💾 Setting current home in DB, session_token: {session_token}")
        success = db_manager.set_user_current_home(user_id, home_id, session_token)
        
        if success:
            # Get user's role in this home
            user_role_in_home = db_manager.get_user_role_in_home(user_id, home_id)
            
            # Update session with home-specific data
            session['current_home_id'] = home_id
            if user_role_in_home:
                session['role'] = user_role_in_home  # Update role to home-specific role
            
            logger.info(f"✅ Successfully switched to home {home_id} with role {user_role_in_home}")
            return jsonify({"success": True})
        else:
            logger.error(f"❌ Failed to set current home in database")
            return jsonify({"success": False, "error": "Failed to switch home"})
    
    except Exception as e:
        logger.error(f"💥 Error switching home: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": "Internal server error"})

@multi_home_bp.route('/home/create')
@login_required
def home_create():
    """Display create home form."""
    db_manager = get_multi_db()
    user = get_current_user()
    
    # Get full user data including profile picture
    user_data = None
    if db_manager and user:
        user_data = db_manager.get_user_by_id(user['id'])
    
    if not user_data:
        user_data = {
            'id': user['id'] if user else '',
            'name': user['id'] if user else '',
            'email': '',
            'role': 'user',
            'profile_picture': ''
        }
    
    return render_template('home_create.html', user_data=user_data)

@multi_home_bp.route('/api/home/create', methods=['POST'])
@login_required
def api_home_create():
    """API endpoint to create a new home."""
    db_manager = get_multi_db()
    if not db_manager:
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
        home_id = db_manager.create_home(name, user_id, description)
        
        # Set as current home
        session_token = session.get('session_token')
        db_manager.set_user_current_home(user_id, str(home_id), session_token)
        session['current_home_id'] = home_id
        
        # Creator is the owner of the home
        session['role'] = 'owner'
        
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
    db_manager = get_multi_db()
    user = get_current_user()
    
    # Get full user data including profile picture
    user_data = None
    if db_manager and user:
        user_data = db_manager.get_user_by_id(user['id'])
    
    if not user_data:
        user_data = {
            'id': user['id'] if user else '',
            'name': user['id'] if user else '',
            'email': '',
            'role': 'user',
            'profile_picture': ''
        }
    
    return render_template('home_join.html', user_data=user_data)

@multi_home_bp.route('/api/home/join', methods=['POST'])
@login_required
def api_home_join():
    """API endpoint to join a home via invitation code."""
    db_manager = get_multi_db()
    if not db_manager:
        return jsonify({"success": False, "error": "Multi-home functionality not available"})
    
    try:
        data = request.get_json() if request.is_json else request.form
        
        invitation_code = data.get('invitation_code', '').strip().upper()
        
        if not invitation_code:
            return jsonify({"success": False, "error": "Invitation code is required"})
        
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"})
        user_id = user['id']
        
        # Accept invitation using multi_db
        db_manager.accept_invitation(
            invitation_code=invitation_code,
            user_id=user_id
        )
        
        # Log the action
        logger.info(f"User {user_id} accepted invitation {invitation_code}")
        
        if request.is_json:
            return jsonify({
                "success": True,
                "message": "Pomyślnie dołączono do domu",
                "redirect": url_for('multi_home.home_select')
            })
        else:
            flash("Pomyślnie dołączono do domu", "success")
            return redirect(url_for('multi_home.home_select'))
    
    except ValueError as e:
        logger.warning(f"Invalid invitation: {e}")
        if request.is_json:
            return jsonify({"success": False, "error": str(e)})
        else:
            flash(str(e), "error")
            return redirect(url_for('multi_home.home_join'))
    except Exception as e:
        logger.error(f"Error joining home: {e}")
        if request.is_json:
            return jsonify({"success": False, "error": "Failed to join home"})
        else:
            flash("Error joining home", "error")
            return redirect(url_for('multi_home.home_join'))

@multi_home_bp.route('/api/home/<home_id>/leave', methods=['POST'])
@login_required
def api_leave_home(home_id):
    """API endpoint for leaving a home."""
    db_manager = get_multi_db()
    if not db_manager:
        return jsonify({"success": False, "error": "Multi-home functionality not available"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    user_id = user['id']
    
    try:
        # Leave the home (can leave any home, not just current one)
        db_manager.leave_home(user_id, home_id)
        
        # Clear session if the home being left is the current one
        if session.get('current_home_id') == home_id:
            session.pop('current_home_id', None)
            session.pop('current_home_name', None)
            session.pop('home_role', None)
            logger.info(f"Cleared current home from session after user {user_id} left home {home_id}")
        
        logger.info(f"User {user_id} left home {home_id}")
        
        return jsonify({
            "success": True,
            "message": "Pomyślnie opuszczono dom",
            "redirect": url_for('multi_home.home_select')
        })
    
    except PermissionError as e:
        logger.warning(f"Permission denied for user {user_id} leaving home {home_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 403
    except ValueError as e:
        logger.warning(f"Invalid leave request from user {user_id} for home {home_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error leaving home {home_id} for user {user_id}: {e}")
        return jsonify({"success": False, "error": "Failed to leave home"}), 500

@multi_home_bp.route('/api/current-home')
@login_required
def api_current_home():
    """Get current home information."""
    db_manager = get_multi_db()
    if not db_manager:
        return jsonify({"success": False, "error": "Multi-home functionality not available"})
    
    try:
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"})
        user_id = user['id']
        current_home_id = session.get('current_home_id') or db_manager.get_user_current_home(user_id)
        
        if not current_home_id:
            return jsonify({"success": False, "error": "No current home set"})
        
        home_details = db_manager.get_home_details(str(current_home_id), user_id)
        
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
    db_manager = get_multi_db()
    if not db_manager:
        return None
        
    try:
        user = get_current_user()
        if not user:
            return None
            
        # Try session first, then database
        home_id = session.get('current_home_id')
        if home_id:
            # Verify user still has access
            if db_manager.user_has_home_access(user['id'], home_id):
                return home_id
        
        # Fall back to database
        home_id = db_manager.get_user_current_home(user['id'])
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
            db_manager = get_multi_db()
            if not db_manager:
                flash("Multi-home functionality is not available", "error")
                return redirect(url_for('home'))
            
            home_id = get_current_home_id()
            if not home_id:
                return redirect(url_for('multi_home.home_select'))
            
            user = get_current_user()
            if not user:
                return redirect(url_for('login'))
            user_id = user['id']
            if not db_manager.user_has_home_permission(user_id, str(home_id), permission):
                flash("You don't have permission to perform this action", "error")
                return redirect(url_for('multi_home.home_select'))
            
            # Add home_id to kwargs for the route function
            kwargs['home_id'] = home_id
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# Home settings routes moved to home_settings_routes.py
# Old routes removed to prevent redirect loops