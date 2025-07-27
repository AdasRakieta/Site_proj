"""
SmartHome Application with Database Integration
==============================================

This is the main application file that integrates the new PostgreSQL database backend
with the existing Flask application structure.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit, disconnect
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the new database-backed SmartHome system

try:
    from app.configure_db import SmartHomeSystemDB as SmartHomeSystem
    DATABASE_MODE = True
    print("✓ Using PostgreSQL database backend")
except ImportError as e:
    print(f"⚠ Failed to import database backend: {e}")
    print("⚠ Falling back to JSON file backend")
    from app.configure import SmartHomeSystem
    DATABASE_MODE = False

# Import other components
from app.routes import RoutesManager
from app.mail_manager import MailManager
from utils.cache_manager import CacheManager, setup_smart_home_caching
from app.management_logger import ManagementLogger

class SmartHomeApp:
    """Main SmartHome application class with database integration"""
    
    def __init__(self):
        """Initialize the SmartHome application"""
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Add context processors
        self.setup_context_processors()
        
        # Initialize core components
        self.initialize_components()
        
        # Setup routes and socket events
        self.setup_routes()
        self.setup_socket_events()
        
        print(f"SmartHome Application initialized (Database mode: {DATABASE_MODE})")
    
    def setup_context_processors(self):
        """Setup template context processors"""
        @self.app.context_processor
        def inject_csrf_token():
            """Inject CSRF token into templates"""
            import secrets
            return dict(csrf_token=lambda: secrets.token_hex(16))
        
        @self.app.template_global()
        def modify_query(**new_values):
            """Modify query parameters for pagination"""
            from flask import request
            from urllib.parse import urlencode
            args = request.args.copy()
            for key, value in new_values.items():
                args[key] = value
            # Convert MultiDict to regular dict for urlencode
            args_dict = {k: v for k, v in args.items()}
            return f'{request.path}?{urlencode(args_dict)}'
    
    def initialize_components(self):
        """Initialize all application components"""
        try:
            # Initialize SmartHome system (with database or JSON backend)
            if DATABASE_MODE:
                try:
                    self.smart_home = SmartHomeSystem()
                    print("✓ SmartHome system initialized with PostgreSQL backend")
                except Exception as e:
                    print(f"⚠ Failed to initialize PostgreSQL backend: {e}")
                    print("⚠ Falling back to JSON file backend")
                    # Import JSON backend as fallback
                    from app.configure import SmartHomeSystem as JSONSmartHomeSystem
                    self.smart_home = JSONSmartHomeSystem()
                    print("✓ SmartHome system initialized with JSON backend (fallback)")
            else:
                self.smart_home = SmartHomeSystem()
                print("✓ SmartHome system initialized with JSON backend")
            
            # Initialize management logger
            self.management_logger = ManagementLogger()
            
            # Initialize mail manager
            self.mail_manager = MailManager()
            
            # Initialize simple auth manager for database mode
            from app.simple_auth import SimpleAuthManager
            self.auth_manager = SimpleAuthManager(self.smart_home)
            
            # Initialize cache (simple in-memory cache for now)
            from flask_caching import Cache
            cache_config = {'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300}
            self.cache = Cache(self.app, config=cache_config)
            
            # Initialize cache manager
            self.cache_manager = CacheManager(self.cache, self.smart_home)
            
            # Setup caching for SmartHome system
            setup_smart_home_caching(self.smart_home, self.cache_manager)
            
            print("✓ All components initialized successfully")
            
        except Exception as e:
            print(f"✗ Failed to initialize components: {e}")
            raise
    
    def setup_routes(self):
        """Setup Flask routes and API endpoints"""
        try:
            from app.routes import APIManager
            self.route_manager = RoutesManager(
                app=self.app,
                smart_home=self.smart_home,
                auth_manager=self.auth_manager,
                mail_manager=self.mail_manager,
                cache=self.cache,  # Pass the Flask cache object, not the cache_manager
                management_logger=self.management_logger
            )
            # Register API endpoints (including /api/automations etc.)
            self.api_manager = APIManager(
                app=self.app,
                socketio=self.socketio,
                smart_home=self.smart_home,
                auth_manager=self.auth_manager,
                management_logger=self.management_logger
            )
            print("✓ Routes and API endpoints configured successfully")
        except Exception as e:
            print(f"✗ Failed to setup routes: {e}")
            raise
    
    def setup_socket_events(self):
        """Setup SocketIO events"""
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            try:
                if 'user_id' not in session:
                    disconnect()
                    return False
                
                user_id = session.get('user_id')
                if not user_id:
                    disconnect()
                    return False
                
                user_data = self.smart_home.get_user_data(user_id)
                emit('user_connected', {
                    'message': f'Welcome back, {user_data.get("name", "User")}!',
                    'user': user_data
                })
                
                # Send current system state
                emit('system_state', {
                    'rooms': self.smart_home.rooms,
                    'buttons': self.smart_home.buttons,
                    'temperature_controls': self.smart_home.temperature_controls,
                    'automations': self.smart_home.automations,
                    'security_state': self.smart_home.security_state,
                    'temperature_states': self.smart_home.temperature_states
                })
                
                print(f"User {user_data.get('name')} connected via WebSocket")
                
            except Exception as e:
                print(f"Error in connect handler: {e}")
                disconnect()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            user_id = session.get('user_id')
            if user_id:
                user_data = self.smart_home.get_user_data(user_id)
                print(f"User {user_data.get('name', 'Unknown')} disconnected")
        
        @self.socketio.on('toggle_button')
        def handle_toggle_button(data):
            """Handle button toggle via WebSocket"""
            try:
                if 'user_id' not in session:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                room = data.get('room')
                name = data.get('name')
                new_state = data.get('state')
                
                # Update device state
                if DATABASE_MODE:
                    success = self.smart_home.update_button_state(room, name, new_state)
                else:
                    # Find and update button in JSON mode
                    success = False
                    for button in self.smart_home.buttons:
                        if button['room'] == room and button['name'] == name:
                            button['state'] = new_state
                            self.smart_home.save_config()
                            success = True
                            break
                
                if success:
                    # Broadcast update to all connected clients
                    self.socketio.emit('update_button', {
                        'room': room,
                        'name': name,
                        'state': new_state
                    })
                    
                    # Log the action
                    user_id = session.get('user_id')
                    if user_id:
                        user_data = self.smart_home.get_user_data(user_id)
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown'),
                            device_name=name,
                            room=room,
                            action='toggle',
                            new_state=new_state,
                            ip_address=request.environ.get('REMOTE_ADDR') or ''
                        )
                    
                    emit('button_toggled', {'success': True, 'room': room, 'name': name, 'state': new_state})
                else:
                    emit('error', {'message': 'Failed to toggle button'})
                    
            except Exception as e:
                print(f"Error in toggle_button handler: {e}")
                emit('error', {'message': 'Internal server error'})
        
        @self.socketio.on('set_temperature')
        def handle_set_temperature(data):
            """Handle temperature setting via WebSocket"""
            try:
                if 'user_id' not in session:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                room = data.get('room')
                name = data.get('name')
                temperature = float(data.get('temperature', 22))
                
                # Validate temperature range
                if not (16 <= temperature <= 30):
                    emit('error', {'message': 'Temperature must be between 16°C and 30°C'})
                    return
                
                # Update temperature control
                if DATABASE_MODE:
                    success = self.smart_home.update_temperature_control_value(room, name, temperature)
                else:
                    # Find and update temperature control in JSON mode
                    success = False
                    for control in self.smart_home.temperature_controls:
                        if control['room'] == room and control['name'] == name:
                            control['temperature'] = temperature
                            self.smart_home.save_config()
                            success = True
                            break
                
                if success:
                    # Update room temperature state
                    if DATABASE_MODE:
                        self.smart_home.set_room_temperature(room, temperature)
                    else:
                        self.smart_home.temperature_states[room] = temperature
                        self.smart_home.save_config()
                    
                    # Broadcast update to all connected clients
                    self.socketio.emit('update_temperature', {
                        'room': room,
                        'name': name,
                        'temperature': temperature
                    })
                    
                    # Log the action
                    user_id = session.get('user_id')
                    if user_id:
                        user_data = self.smart_home.get_user_data(user_id)
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown'),
                            device_name=name,
                            room=room,
                            action='set_temperature',
                            new_state=temperature,
                            ip_address=request.environ.get('REMOTE_ADDR') or ''
                        )
                    
                    emit('temperature_set', {
                        'success': True, 
                        'room': room, 
                        'name': name, 
                        'temperature': temperature
                    })
                else:
                    emit('error', {'message': 'Failed to set temperature'})
                    
            except ValueError:
                emit('error', {'message': 'Invalid temperature value'})
            except Exception as e:
                print(f"Error in set_temperature handler: {e}")
                emit('error', {'message': 'Internal server error'})
        
        @self.socketio.on('set_security_state')
        def handle_set_security_state(data):
            """Handle security state setting via WebSocket"""
            try:
                if 'user_id' not in session:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                new_state = data.get('state')
                if new_state not in ["Załączony", "Wyłączony"]:
                    emit('error', {'message': 'Invalid security state'})
                    return
                
                # Update security state
                self.smart_home.security_state = new_state
                
                # Save configuration
                if DATABASE_MODE:
                    # Database mode - state is automatically saved via setter
                    success = True
                else:
                    # JSON mode - explicitly save config
                    success = self.smart_home.save_config()
                
                if success:
                    # Broadcast update to all connected clients
                    self.socketio.emit('update_security_state', {'state': new_state})
                    
                    # Log the action
                    user_id = session.get('user_id')
                    if user_id:
                        user_data = self.smart_home.get_user_data(user_id)
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown'),
                            device_name='Security System',
                            room='System',
                            action='set_security_state',
                            new_state=new_state,
                            ip_address=request.environ.get('REMOTE_ADDR') or ''
                        )
                    
                    print(f"Security state updated to: {new_state}")
                else:
                    emit('error', {'message': 'Failed to save security state'})
                    
            except Exception as e:
                print(f"Error in set_security_state handler: {e}")
                emit('error', {'message': 'Internal server error'})
        
        @self.socketio.on('get_security_state')
        def handle_get_security_state():
            """Handle security state request via WebSocket"""
            try:
                if 'user_id' not in session:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                # Get current security state
                current_state = self.smart_home.security_state
                
                # Send current state to client
                emit('update_security_state', {'state': current_state})
                print(f"Sent security state to client: {current_state}")
                
            except Exception as e:
                print(f"Error in get_security_state handler: {e}")
                emit('error', {'message': 'Internal server error'})
        
        print("✓ Socket events configured successfully")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the application"""
        print(f"\n🚀 Starting SmartHome Application")
        print(f"📊 Database mode: {'PostgreSQL' if DATABASE_MODE else 'JSON Files'}")
        print(f"🌐 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"🐛 Debug: {debug}")
        
        if DATABASE_MODE:
            # Show database statistics
            try:
                stats = self.smart_home.get_database_stats()
                print(f"📈 Database stats: {stats}")
            except:
                print("📈 Database stats: Not available")
        
        print(f"🏠 Access your SmartHome at: http://{host}:{port}")
        print("-" * 60)
        
        try:
            self.socketio.run(
                self.app,
                host=host,
                port=port,
                debug=debug,
                use_reloader=False  # Disable reloader to prevent issues with threads
            )
        except KeyboardInterrupt:
            print("\n👋 SmartHome Application stopped by user")
        except Exception as e:
            print(f"\n💥 Application error: {e}")
            raise

def create_app():
    """Factory function to create the Flask app"""
    smart_home_app = SmartHomeApp()
    return smart_home_app.app, smart_home_app.socketio

def main():
    """Main entry point"""
    try:
        # Create and run the application
        smart_home_app = SmartHomeApp()
        smart_home_app.run(debug=False)
        
    except Exception as e:
        print(f"💥 Failed to start SmartHome Application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
