"""
Home Settings API Routes
Separate API endpoints for home management functionality.
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from functools import wraps
from utils.multi_home_db_manager import MultiHomeDBManager
from app.home_management import HomeSettingsManager
import logging

logger = logging.getLogger(__name__)

# Create blueprint for home settings
home_settings_bp = Blueprint('home_settings', __name__)

# These will be set by the main application
multi_db = None
home_settings_manager = None

def init_home_settings_routes(db_manager):
    """Initialize home settings routes with database manager"""
    global multi_db, home_settings_manager
    multi_db = db_manager
    if multi_db:
        home_settings_manager = HomeSettingsManager(multi_db)
        logger.info("Home settings routes initialized with db_manager")
    else:
        logger.warning("Home settings routes initialized without db_manager")

# Authentication decorator
def login_required(f):
    """Decorator for requiring login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged in user from session"""
    user_id = session.get('user_id')
    if user_id:
        return {'id': user_id}
    return None

# Test route to check if blueprint works
@home_settings_bp.route('/test-home-settings')
def test_home_settings():
    """Test route to verify home settings blueprint is working"""
    return {"status": "ok", "message": "Home settings blueprint is working"}

# Page Routes
@home_settings_bp.route('/home/<home_id>/settings')
@login_required
def home_settings_page(home_id):
    """Display home settings page using HomeSettingsManager"""
    print(f"⚙️ Home settings page accessed for home: {home_id}")
    logger.info(f"⚙️ Home settings page accessed for home: {home_id}")
    
    if not home_settings_manager:
        print("❌ Home settings manager not available")
        logger.error("Home settings manager not available")
        flash("Home settings functionality is not available", "error")
        return redirect('/home/select')
    
    user = get_current_user()
    if not user:
        return redirect('/login')
    user_id = user['id']
    
    try:
        # Get all home settings data using the manager
        result = home_settings_manager.get_home_settings_data(home_id, user_id)
        
        if not result["success"]:
            flash(result["error"], "error")
            return redirect('/home/select')
        
        data = result["data"]
        home = data["home"]
        rooms = data["rooms"]
        users = data["users"]
        
        # Check if user is owner (required for settings page)
        if not home.get('is_owner', False):
            flash("Only home owners can access settings", "error")
            return redirect('/home/select')
        
        # Add device count to home data
        try:
            if multi_db:
                devices = multi_db.get_home_devices(home_id, user_id)
                home['device_count'] = len(devices)
            else:
                home['device_count'] = 0
        except Exception as e:
            logger.error(f"Error getting device count: {e}")
            home['device_count'] = 0
        
        print(f"🏠 Home settings loaded for: {home['name']}")
        logger.info(f"🏠 Home settings loaded for: {home['name']}")
        
        return render_template('home_settings.html',
                             home=home,
                             rooms=rooms,
                             users=users)
    
    except Exception as e:
        print(f"❌ Error loading home settings: {e}")
        logger.error(f"Error loading home settings: {e}")
        flash("An error occurred while loading home settings", "error")
        return redirect('/home/select')

# API Routes for Home Information
@home_settings_bp.route('/api/home/<home_id>/info/update', methods=['POST'])
@login_required
def api_update_home_info(home_id):
    """Update home basic information using HomeInfoManager"""
    print(f"📝 Updating home info for home: {home_id}")
    logger.info(f"📝 Updating home info for home: {home_id}")
    
    if not home_settings_manager:
        return jsonify({"success": False, "error": "Home settings manager not available"}), 500
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not authenticated"}), 401
    user_id = user['id']
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip() if data.get('description') else None
        
        # Use HomeInfoManager to update
        result = home_settings_manager.info_manager.update_home_info(home_id, user_id, name, description)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in API update home info: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

# API Routes for User Management
@home_settings_bp.route('/api/home/<home_id>/users/invite', methods=['POST'])
@login_required
def api_invite_user_to_home(home_id):
    """Invite user to home using HomeUserManager"""
    print(f"📧 Inviting user to home: {home_id}")
    logger.info(f"📧 Inviting user to home: {home_id}")
    
    if not home_settings_manager:
        return jsonify({"success": False, "error": "Home settings manager not available"}), 500
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not authenticated"}), 401
    user_id = user['id']
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        email = data.get('email', '').strip()
        role = data.get('role', 'user')
        
        # Use HomeUserManager to invite
        result = home_settings_manager.user_manager.invite_user(home_id, user_id, email, role)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in API invite user: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@home_settings_bp.route('/api/home/<home_id>/users', methods=['GET'])
@login_required
def api_get_home_users(home_id):
    """Get home users using HomeUserManager"""
    if not home_settings_manager:
        return jsonify({"success": False, "error": "Home settings manager not available"}), 500
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not authenticated"}), 401
    user_id = user['id']
    
    try:
        result = home_settings_manager.user_manager.get_home_users(home_id, user_id)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in API get home users: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@home_settings_bp.route('/api/home/<home_id>/users/<user_id_to_remove>/remove', methods=['DELETE'])
@login_required
def api_remove_user_from_home(home_id, user_id_to_remove):
    """Remove user from home using HomeUserManager"""
    if not home_settings_manager:
        return jsonify({"success": False, "error": "Home settings manager not available"}), 500
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not authenticated"}), 401
    owner_id = user['id']
    
    try:
        result = home_settings_manager.user_manager.remove_user(home_id, owner_id, user_id_to_remove)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in API remove user: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

# API Routes for Room Management
@home_settings_bp.route('/api/home/<home_id>/rooms/<room_id>/update', methods=['PUT'])
@login_required
def api_update_room(home_id, room_id):
    """Update room using HomeRoomManager"""
    if not home_settings_manager:
        return jsonify({"success": False, "error": "Home settings manager not available"}), 500
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not authenticated"}), 401
    user_id = user['id']
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        name = data.get('name', '').strip()
        room_type = data.get('room_type', 'other')
        
        result = home_settings_manager.room_manager.update_room(home_id, user_id, room_id, name, room_type)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in API update room: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@home_settings_bp.route('/api/home/<home_id>/rooms/<room_id>/delete', methods=['DELETE'])
@login_required
def api_delete_room(home_id, room_id):
    """Delete room using HomeRoomManager"""
    if not home_settings_manager:
        return jsonify({"success": False, "error": "Home settings manager not available"}), 500
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not authenticated"}), 401
    user_id = user['id']
    
    try:
        result = home_settings_manager.room_manager.delete_room(home_id, user_id, room_id)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in API delete room: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

# API Routes for Home Deletion
@home_settings_bp.route('/api/home/<home_id>/deletion-info', methods=['GET'])
@login_required
def api_get_home_deletion_info(home_id):
    """Get information about what will be deleted using HomeDeletionManager"""
    if not home_settings_manager:
        return jsonify({"success": False, "error": "Home settings manager not available"}), 500
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not authenticated"}), 401
    user_id = user['id']
    
    try:
        result = home_settings_manager.deletion_manager.get_deletion_info(home_id, user_id)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in API get deletion info: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@home_settings_bp.route('/api/home/<home_id>/delete', methods=['DELETE'])
@login_required
def api_delete_home(home_id):
    """Delete home permanently using HomeDeletionManager"""
    if not home_settings_manager:
        return jsonify({"success": False, "error": "Home settings manager not available"}), 500
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not authenticated"}), 401
    user_id = user['id']
    
    try:
        result = home_settings_manager.deletion_manager.delete_home(home_id, user_id)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in API delete home: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500