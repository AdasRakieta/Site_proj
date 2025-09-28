"""
SmartHome Application with Database Integration
==============================================

This is the main application file that integrates the new PostgreSQL database backend
with the existing Flask application structure.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit, disconnect
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

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
from utils.async_manager import AsyncMailManager
from utils.cache_manager import CacheManager, setup_smart_home_caching
from app.management_logger import ManagementLogger
from app.database_management_logger import DatabaseManagementLogger

class SmartHomeApp:
    """Main SmartHome application class with database integration"""
    
    def __init__(self):
        """Initialize the SmartHome application"""
        self._configure_logging()
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)
        # Cookie security and SameSite settings
        is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('ENV') == 'production' or os.getenv('APP_ENV') == 'production'
        self.app.config.update({
            # Lax is recommended for session cookies; use Secure only in production/HTTPS
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SECURE': bool(is_production),
        })
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Add CORS headers for mobile app
        @self.app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
        
        # Add context processors
        self.setup_context_processors()
        
        # Initialize core components
        self.initialize_components()
        
        # Setup routes and socket events
        self.setup_routes()
        self.setup_socket_events()
        
        print(f"SmartHome Application initialized (Database mode: {DATABASE_MODE})")
    
    def _warm_up_cache(self):
        """Warm up cache with frequently accessed data"""
        try:
            print("🔥 Warming up cache with critical data...")
            
            # Pre-load rooms configuration
            if hasattr(self.smart_home, 'rooms'):
                rooms = self.smart_home.rooms
                if rooms:
                    timeout = self.cache_manager.get_timeout('rooms')
                    self.cache.set("rooms_list", rooms, timeout=timeout)
                    print(f"✓ Cached {len(rooms) if isinstance(rooms, list) else 'N/A'} rooms")
            
            # Pre-load buttons configuration  
            if hasattr(self.smart_home, 'buttons'):
                buttons = self.smart_home.buttons
                if buttons:
                    timeout = self.cache_manager.get_timeout('buttons')
                    self.cache.set("buttons_list", buttons, timeout=timeout)
                    print(f"✓ Cached {len(buttons) if isinstance(buttons, list) else 'N/A'} buttons")
            
            # Pre-load temperature controls
            if hasattr(self.smart_home, 'temperature_controls'):
                temp_controls = self.smart_home.temperature_controls
                if temp_controls:
                    timeout = self.cache_manager.get_timeout('temperature')
                    self.cache.set("temperature_controls", temp_controls, timeout=timeout)
                    print(f"✓ Cached {len(temp_controls) if isinstance(temp_controls, list) else 'N/A'} temperature controls")
            
            # Pre-load automations
            if hasattr(self.smart_home, 'automations'):
                automations = self.smart_home.automations
                if automations:
                    timeout = self.cache_manager.get_timeout('automations')
                    self.cache.set("automations_list", automations, timeout=timeout)
                    print(f"✓ Cached {len(automations) if isinstance(automations, list) else 'N/A'} automations")
            
            print("✓ Cache warming completed")
            
        except Exception as e:
            print(f"⚠ Cache warming failed: {e}")
            # Don't fail initialization if cache warming fails
    
    def _configure_logging(self):
        """Reduce noise from lower-level websocket/werkzeug loggers"""
        noisy_loggers = [
            'geventwebsocket.handler',
            'engineio.server',
            'socketio.server',
            'werkzeug'
        ]
        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    def setup_context_processors(self):
        """Setup template context processors"""
        @self.app.context_processor
        def inject_csrf_token():
            """Inject CSRF token into templates"""
            import secrets
            return dict(csrf_token=lambda: secrets.token_hex(16))
        
        # Add multi-home context processor
        try:
            from app.multi_home_context import multi_home_context_processor
            self.app.context_processor(multi_home_context_processor)
            print("✓ Multi-home context processor registered")
        except Exception as e:
            print(f"⚠ Failed to register multi-home context processor: {e}")
        
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
            # Use database logger when in database mode, JSON logger otherwise
            if DATABASE_MODE:
                try:
                    self.management_logger = DatabaseManagementLogger()
                    print("✓ Management logger initialized with database backend")
                except Exception as e:
                    print(f"⚠ Failed to initialize database logger: {e}")
                    print("⚠ Falling back to JSON logger")
                    self.management_logger = ManagementLogger()
            else:
                self.management_logger = ManagementLogger()
                print("✓ Management logger initialized with JSON backend")
            
            # Initialize mail manager
            self.mail_manager = MailManager()
            self.async_mail_manager = AsyncMailManager(self.mail_manager)
            
            # Initialize simple auth manager for database mode
            from app.simple_auth import SimpleAuthManager
            self.auth_manager = SimpleAuthManager(self.smart_home)
            
            # Initialize cache with Redis if available, fallback to SimpleCache
            from flask_caching import Cache
            import os
            
            # Try Redis first for better performance and persistence
            redis_url = os.getenv('REDIS_URL', None)
            redis_host = os.getenv('REDIS_HOST', None)
            redis_port = os.getenv('REDIS_PORT', 6379)
            
            if redis_url:
                cache_config = {
                    'CACHE_TYPE': 'RedisCache',
                    'CACHE_REDIS_URL': redis_url,
                    'CACHE_DEFAULT_TIMEOUT': 600
                }
                print("✓ Using Redis cache with URL")
            elif redis_host:
                cache_config = {
                    'CACHE_TYPE': 'RedisCache',
                    'CACHE_REDIS_HOST': redis_host,
                    'CACHE_REDIS_PORT': int(redis_port),
                    'CACHE_DEFAULT_TIMEOUT': 600
                }
                print("✓ Using Redis cache with host/port")
            else:
                # Fallback to SimpleCache with optimized timeout
                cache_config = {
                    'CACHE_TYPE': 'SimpleCache',
                    'CACHE_DEFAULT_TIMEOUT': 600,  # Increased from 300 to 600
                    'CACHE_THRESHOLD': 500  # Increase threshold for better performance
                }
                print("✓ Using SimpleCache (in-memory)")
            
            try:
                self.cache = Cache(self.app, config=cache_config)
                # Test cache functionality
                self.cache.set('test_key', 'test_value', timeout=10)
                if self.cache.get('test_key') == 'test_value':
                    print("✓ Cache functionality verified")
                    self.cache.delete('test_key')
                else:
                    print("⚠ Cache test failed, may impact performance")
            except Exception as e:
                print(f"⚠ Cache initialization failed: {e}, using fallback")
                # Ultra-safe fallback
                cache_config = {'CACHE_TYPE': 'NullCache'}
                self.cache = Cache(self.app, config=cache_config)
            
            # Initialize cache manager
            self.cache_manager = CacheManager(self.cache, self.smart_home)
            
            # Setup caching for SmartHome system
            setup_smart_home_caching(self.smart_home, self.cache_manager)
            
            # Warm up cache with critical data
            self._warm_up_cache()
            
            print("✓ All components initialized successfully")
            
        except Exception as e:
            print(f"✗ Failed to initialize components: {e}")
            raise
    
    def setup_routes(self):
        """Setup Flask routes and API endpoints"""
        try:
            from app.routes import APIManager
            # Import multi_db from multi_home_routes
            from app.multi_home_routes import multi_db
            
            self.route_manager = RoutesManager(
                app=self.app,
                smart_home=self.smart_home,
                auth_manager=self.auth_manager,
                mail_manager=self.mail_manager,
                async_mail_manager=self.async_mail_manager,
                cache=self.cache,  # Pass the Flask cache object, not the cache_manager
                management_logger=self.management_logger,
                socketio=self.socketio,  # Add socketio parameter
                multi_db=multi_db  # Add multi_db parameter
            )
            # Register API endpoints (including /api/automations etc.)
            # Be resilient to different APIManager signatures across deployments
            import inspect
            api_init_sig = inspect.signature(APIManager.__init__)
            accepted_params = set(api_init_sig.parameters.keys()) - {"self"}
            possible_kwargs = {
                'app': self.app,
                'socketio': self.socketio,
                'smart_home': self.smart_home,
                'auth_manager': self.auth_manager,
                'management_logger': self.management_logger,
                'cache': self.cache,
            }
            filtered_kwargs = {k: v for k, v in possible_kwargs.items() if k in accepted_params}
            # Helpful debug
            print(f"[DEBUG] Creating APIManager with kwargs: {sorted(filtered_kwargs.keys())}")
            self.api_manager = APIManager(**filtered_kwargs)
            
            # Register multi-home blueprint first
            try:
                from app.multi_home_routes import multi_home_bp
                self.app.register_blueprint(multi_home_bp)
                print("✓ Multi-home routes registered successfully")
            except Exception as e:
                print(f"⚠ Failed to register multi-home routes: {e}")
            
            # Register home settings blueprint after multi-home (needs multi_db)
            try:
                from app.home_settings_routes import home_settings_bp
                self.app.register_blueprint(home_settings_bp)
                print("✓ Home settings routes registered successfully")
            except Exception as e:
                print(f"⚠ Failed to register home settings routes: {e}")
                import traceback
                traceback.print_exc()
            
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

                    # Invalidate relevant caches to reflect immediate state change
                    try:
                        if hasattr(self, 'cache_manager') and self.cache_manager:
                            self.cache.delete('buttons_list')
                            # Room-specific caches (best-effort) - names follow pattern buttons_room_<room>
                            self.cache.delete(f'buttons_room_{room}')
                    except Exception as cache_err:
                        print(f"[DEBUG] Failed to invalidate button caches: {cache_err}")
                    
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
                print(f"[DEBUG] set_temperature called with data: {data}")
                
                if 'user_id' not in session:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                room = data.get('room')
                name = data.get('name')
                temperature = float(data.get('temperature', 22))
                
                print(f"[DEBUG] Parsed values: room='{room}', name='{name}', temperature={temperature}")
                
                # Validate temperature range
                if not (16 <= temperature <= 30):
                    emit('error', {'message': 'Temperature must be between 16°C and 30°C'})
                    return
                
                # Update temperature control
                if DATABASE_MODE:
                    print(f"[DEBUG] Using database mode")
                    success = self.smart_home.update_temperature_control_value(room, name, temperature)
                    print(f"[DEBUG] Database update success: {success}")
                else:
                    print(f"[DEBUG] Using JSON mode")
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

                    # Invalidate temperature related caches
                    try:
                        if hasattr(self, 'cache_manager') and self.cache_manager:
                            self.cache.delete('temperature_controls')
                            self.cache.delete(f'temp_controls_room_{room}')
                    except Exception as cache_err:
                        print(f"[DEBUG] Failed to invalidate temperature caches: {cache_err}")
                    
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
        
        @self.socketio.on('toggle_temperature_control_enabled')
        def handle_toggle_temperature_control_enabled(data):
            """Handle temperature control enable/disable toggle via WebSocket"""
            try:
                print(f"[DEBUG] toggle_temperature_control_enabled called with data: {data}")
                
                if 'user_id' not in session:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                room = data.get('room')
                name = data.get('name')
                enabled = bool(data.get('enabled', True))
                
                print(f"[DEBUG] Parsed values: room='{room}', name='{name}', enabled={enabled}")
                
                # Update temperature control enabled state
                if DATABASE_MODE:
                    print(f"[DEBUG] Using database mode for enabled toggle")
                    success = self.smart_home.toggle_temperature_control_enabled(room, name, enabled)
                    print(f"[DEBUG] Database enabled update success: {success}")
                else:
                    print(f"[DEBUG] Using JSON mode for enabled toggle")
                    # Find and update temperature control in JSON mode
                    success = False
                    for control in self.smart_home.temperature_controls:
                        if control['room'] == room and control['name'] == name:
                            control['enabled'] = enabled
                            self.smart_home.save_config()
                            success = True
                            break
                
                if success:
                    # Broadcast update to all connected clients
                    self.socketio.emit('update_temperature_control_enabled', {
                        'room': room,
                        'name': name,
                        'enabled': enabled
                    })

                    # Invalidate temperature related caches
                    try:
                        if hasattr(self, 'cache_manager') and self.cache_manager:
                            self.cache.delete('temperature_controls')
                            self.cache.delete(f'temp_controls_room_{room}')
                    except Exception as cache_err:
                        print(f"[DEBUG] Failed to invalidate temperature caches: {cache_err}")
                    
                    # Log the action
                    user_id = session.get('user_id')
                    if user_id:
                        user_data = self.smart_home.get_user_data(user_id)
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown'),
                            device_name=name,
                            room=room,
                            action='toggle_temperature_enabled',
                            new_state=enabled,
                            ip_address=request.environ.get('REMOTE_ADDR') or ''
                        )
                    
                    emit('temperature_control_enabled_toggled', {
                        'success': True, 
                        'room': room, 
                        'name': name, 
                        'enabled': enabled
                    })
                else:
                    emit('error', {'message': 'Failed to toggle temperature control enabled state'})
                    
            except Exception as e:
                print(f"Error in toggle_temperature_control_enabled handler: {e}")
                emit('error', {'message': 'Internal server error'})
        
        @self.socketio.on('set_security_state')
        def handle_set_security_state(data):
            """Handle security state setting via WebSocket"""
            try:
                print(f"[DEBUG] set_security_state called with data: {data}")
                print(f"[DEBUG] Session contents: {dict(session)}")
                
                if 'user_id' not in session:
                    print("[DEBUG] No user_id in session - authentication failed")
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                print(f"[DEBUG] Authenticated user_id: {session.get('user_id')}")
                
                new_state = data.get('state')
                if new_state not in ["Załączony", "Wyłączony"]:
                    print(f"[DEBUG] Invalid security state: {new_state}")
                    emit('error', {'message': 'Invalid security state'})
                    return
                
                print(f"[DEBUG] Setting security state to: {new_state}")
                
                # Update security state
                self.smart_home.security_state = new_state
                
                # Save configuration
                if DATABASE_MODE:
                    # Database mode - state is automatically saved via setter
                    success = True
                    print("[DEBUG] Database mode - state saved automatically")
                else:
                    # JSON mode - explicitly save config
                    success = self.smart_home.save_config()
                    print(f"[DEBUG] JSON mode - save_config result: {success}")
                
                if success:
                    # Broadcast update to all connected clients
                    self.socketio.emit('update_security_state', {'state': new_state})
                    print(f"[DEBUG] Broadcasted security state update: {new_state}")
                    
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
                        print(f"[DEBUG] Logged action for user: {user_data.get('name', 'Unknown')}")
                    
                    print(f"Security state updated to: {new_state}")
                else:
                    print("[DEBUG] Failed to save security state")
                    emit('error', {'message': 'Failed to save security state'})
                    
            except Exception as e:
                print(f"Error in set_security_state handler: {e}")
                import traceback
                traceback.print_exc()
                emit('error', {'message': 'Internal server error'})
        
        @self.socketio.on('get_security_state')
        def handle_get_security_state():
            """Handle security state request via WebSocket"""
            try:
                print(f"[DEBUG] get_security_state called")
                print(f"[DEBUG] Session contents: {dict(session)}")
                
                if 'user_id' not in session:
                    print("[DEBUG] No user_id in session - authentication failed")
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                print(f"[DEBUG] Authenticated user_id: {session.get('user_id')}")
                
                # Get current security state
                current_state = self.smart_home.security_state
                print(f"[DEBUG] Current security state from smart_home: {current_state}")
                
                # Send current state to client
                emit('update_security_state', {'state': current_state})
                print(f"Sent security state to client: {current_state}")
                
            except Exception as e:
                print(f"Error in get_security_state handler: {e}")
                import traceback
                traceback.print_exc()
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
        # Load environment variables
        load_dotenv()
        
        # Get configuration from .env
        server_host = os.getenv('SERVER_HOST', '0.0.0.0')
        server_port = int(os.getenv('SERVER_PORT', 5000))
        
        # Create and run the application
        smart_home_app = SmartHomeApp()
        # Use configuration from .env file
        smart_home_app.run(host=server_host, port=server_port, debug=False)
        
    except Exception as e:
        print(f"💥 Failed to start SmartHome Application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
