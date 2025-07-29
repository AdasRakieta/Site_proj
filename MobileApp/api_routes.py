from flask import jsonify, request, session
from utils.cache_manager import CachedDataAccess  
from MobileApp.management_logger import ManagementLogger
import traceback


class APIRoutesManager:
    """Manager for API routes that serve JSON responses for mobile app"""
    
    def __init__(self, app, smart_home, auth_manager, mail_manager, async_mail_manager=None, cache=None, cached_data_access=None, management_logger=None):
        self.app = app
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.mail_manager = mail_manager
        self.async_mail_manager = async_mail_manager or mail_manager
        self.cache = cache
        self.cached_data = cached_data_access or (CachedDataAccess(cache, smart_home) if cache else None)
        self.management_logger = management_logger or ManagementLogger()
        self.register_api_routes()

    def register_api_routes(self):
        """Register all API routes for mobile app communication"""
        print("[DEBUG] Registering API routes for mobile app...")
        
        # Basic API endpoints
        @self.app.route('/api/ping', methods=['GET'])
        def api_ping():
            """Simple ping endpoint to test connectivity"""
            return jsonify({
                'status': 'success',
                'message': 'API is working',
                'timestamp': None  # Will be added if needed
            })

        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            """Get system status"""
            try:
                return jsonify({
                    'status': 'success',
                    'data': {
                        'system_status': 'online',
                        'version': '1.0.0'
                    }
                })
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/config', methods=['GET'])
        def api_config():
            """Get basic configuration for mobile app"""
            try:
                return jsonify({
                    'status': 'success',
                    'data': {
                        'app_name': 'SmartHome',
                        'version': '1.0.0'
                    }
                })
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        # Mobile authentication API
        @self.app.route('/api/login', methods=['POST'])
        def api_login():
            """API login endpoint for mobile app"""
            try:
                if not request.is_json:
                    return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
                
                data = request.get_json()
                login_name = data.get('username')
                password = data.get('password')
                
                if not login_name or not password:
                    return jsonify({"status": "error", "message": "Username and password required"}), 400
                
                ip_address = request.remote_addr
                
                # Get user by name/email
                users = self.smart_home.users
                user = None
                user_id = None
                
                for uid, user_data in users.items():
                    if user_data.get('name') == login_name or user_data.get('email') == login_name:
                        user = user_data
                        user_id = uid
                        break
                
                # Verify password
                if user and user.get('password') and self.smart_home.verify_password(user_id, password):
                    session['user_id'] = user_id
                    session['username'] = user['name']
                    session['role'] = user.get('role', 'user')
                    session.permanent = True
                    
                    # Log successful login
                    if self.management_logger:
                        self.management_logger.log_login(user['name'], ip_address or 'unknown', success=True)
                    
                    # JSON API response for mobile
                    return jsonify({
                        "status": "success",
                        "message": "Login successful",
                        "data": {
                            "user": {
                                "id": user_id,
                                "name": user['name'],
                                "email": user.get('email', ''),
                                "role": user.get('role', 'user')
                            }
                        }
                    })
                else:
                    # Log failed login attempt
                    if self.management_logger:
                        self.management_logger.log_login(
                            login_name or 'unknown', ip_address or 'unknown', success=False
                        )
                    
                    return jsonify({
                        "status": "error",
                        "message": "Invalid username or password"
                    }), 401
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        # Device management APIs
        @self.app.route('/api/rooms', methods=['GET', 'POST'])
        @self.auth_manager.api_login_required
        def api_rooms():
            """Get all rooms or create a new room"""
            try:
                if request.method == 'GET':
                    if self.cached_data:
                        rooms = self.cached_data.get_rooms()
                    else:
                        rooms = self.smart_home.rooms
                    return jsonify({"status": "success", "data": {"rooms": rooms}})
                
                elif request.method == 'POST':
                    data = request.get_json()
                    if not data or 'room_name' not in data:
                        return jsonify({"status": "error", "message": "room_name is required"}), 400
                    
                    room_name = data['room_name']
                    self.smart_home.add_room(room_name)
                    
                    return jsonify({
                        "status": "success", 
                        "message": f"Room '{room_name}' created successfully"
                    })
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/buttons', methods=['GET', 'POST'])
        @self.auth_manager.api_login_required
        def api_buttons():
            """Get all buttons or create a new button"""
            try:
                if request.method == 'GET':
                    if self.cached_data:
                        buttons = self.cached_data.get_buttons()
                    else:
                        buttons = self.smart_home.buttons
                    return jsonify({"status": "success", "data": {"buttons": buttons}})
                
                elif request.method == 'POST':
                    data = request.get_json()
                    if not data:
                        return jsonify({"status": "error", "message": "No data provided"}), 400
                    
                    # Add button logic here
                    return jsonify({"status": "success", "message": "Button created"})
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/temperature_controls', methods=['GET', 'POST'])
        @self.auth_manager.api_login_required
        def api_temperature_controls():
            """Get all temperature controls or create a new one"""
            try:
                if request.method == 'GET':
                    if self.cached_data:
                        temp_controls = self.cached_data.get_temperature_controls()
                    else:
                        temp_controls = self.smart_home.temperature_controls
                    return jsonify({"status": "success", "data": {"temperature_controls": temp_controls}})
                
                elif request.method == 'POST':
                    data = request.get_json()
                    if not data:
                        return jsonify({"status": "error", "message": "No data provided"}), 400
                    
                    # Add temperature control logic here
                    return jsonify({"status": "success", "message": "Temperature control created"})
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/buttons/<id>/toggle', methods=['POST'])
        @self.auth_manager.api_login_required
        def api_button_toggle(id):
            """Toggle a button state"""
            try:
                # Toggle button logic would go here
                return jsonify({"status": "success", "message": f"Button {id} toggled"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/buttons/<id>', methods=['PUT', 'DELETE'])
        @self.auth_manager.api_login_required
        def api_button_modify(id):
            """Update or delete a button"""
            try:
                if request.method == 'PUT':
                    data = request.get_json()
                    if not data:
                        return jsonify({"status": "error", "message": "No data provided"}), 400
                    # Update button logic
                    return jsonify({"status": "success", "message": f"Button {id} updated"})
                
                elif request.method == 'DELETE':
                    # Delete button logic
                    return jsonify({"status": "success", "message": f"Button {id} deleted"})
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/temperature_controls/<id>', methods=['PUT', 'DELETE'])
        @self.auth_manager.api_login_required
        def api_temp_control_modify(id):
            """Update or delete a temperature control"""
            try:
                if request.method == 'PUT':
                    data = request.get_json()
                    if not data:
                        return jsonify({"status": "error", "message": "No data provided"}), 400
                    # Update temperature control logic
                    return jsonify({"status": "success", "message": f"Temperature control {id} updated"})
                
                elif request.method == 'DELETE':
                    # Delete temperature control logic
                    return jsonify({"status": "success", "message": f"Temperature control {id} deleted"})
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/users', methods=['GET'])
        @self.auth_manager.api_login_required
        def api_users():
            """Get all users (admin only)"""
            try:
                # Check if user has admin role
                user_id = session.get('user_id')
                user_data = self.smart_home.get_user_data(user_id)
                
                if not user_data or user_data.get('role') != 'admin':
                    return jsonify({"status": "error", "message": "Admin access required"}), 403
                
                users = self.smart_home.users
                # Remove sensitive data
                safe_users = {}
                for uid, user in users.items():
                    safe_users[uid] = {
                        'name': user.get('name', ''),
                        'email': user.get('email', ''),
                        'role': user.get('role', 'user')
                    }
                
                return jsonify({"status": "success", "data": {"users": safe_users}})
                
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/security', methods=['GET', 'POST'])
        @self.auth_manager.api_login_required
        def api_security():
            """Get or set security state"""
            try:
                if request.method == 'GET':
                    security_state = getattr(self.smart_home, 'security_state', False)
                    return jsonify({
                        "status": "success", 
                        "data": {"security_state": security_state}
                    })
                
                elif request.method == 'POST':
                    data = request.get_json()
                    if not data or 'state' not in data:
                        return jsonify({"status": "error", "message": "state is required"}), 400
                    
                    new_state = data['state']
                    self.smart_home.security_state = new_state
                    
                    return jsonify({
                        "status": "success", 
                        "message": f"Security state set to {new_state}"
                    })
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/user/profile', methods=['GET', 'PUT'])
        @self.auth_manager.api_login_required
        def api_user_profile():
            """Get or update user profile"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({"status": "error", "message": "User not authenticated"}), 401
                
                if request.method == 'GET':
                    user_data = self.smart_home.get_user_data(user_id)
                    if user_data:
                        # Remove sensitive data
                        safe_user_data = {
                            'name': user_data.get('name', ''),
                            'email': user_data.get('email', ''),
                            'role': user_data.get('role', 'user')
                        }
                        return jsonify({"status": "success", "data": {"user": safe_user_data}})
                    else:
                        return jsonify({"status": "error", "message": "User not found"}), 404
                
                elif request.method == 'PUT':
                    data = request.get_json()
                    if not data:
                        return jsonify({"status": "error", "message": "No data provided"}), 400
                    
                    # Update user profile logic would go here
                    return jsonify({"status": "success", "message": "Profile updated"})
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/automations', methods=['GET', 'POST'])
        @self.auth_manager.api_login_required
        def api_automations():
            """Get all automations or create a new one"""
            try:
                if request.method == 'GET':
                    automations = getattr(self.smart_home, 'automations', [])
                    return jsonify({"status": "success", "data": {"automations": automations}})
                
                elif request.method == 'POST':
                    data = request.get_json()
                    if not data:
                        return jsonify({"status": "error", "message": "No data provided"}), 400
                    
                    # Add automation logic here
                    return jsonify({"status": "success", "message": "Automation created"})
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/admin/logs', methods=['GET'])
        @self.auth_manager.api_login_required
        def api_admin_logs():
            """Get system logs (admin only)"""
            try:
                # Check if user has admin role
                user_id = session.get('user_id')
                user_data = self.smart_home.get_user_data(user_id)
                
                if not user_data or user_data.get('role') != 'admin':
                    return jsonify({"status": "error", "message": "Admin access required"}), 403
                
                # Get logs from management logger
                logs = []
                if self.management_logger:
                    try:
                        logs = self.management_logger.get_recent_logs(limit=100)
                    except:
                        logs = []
                
                return jsonify({"status": "success", "data": {"logs": logs}})
                
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        
        print("[DEBUG] API routes registered successfully!")