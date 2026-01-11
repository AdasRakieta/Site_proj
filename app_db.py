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

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables FIRST, before any other imports that need them
# Priority: 1) Environment variables (from Portainer/system), 2) .env file (local development)
# This allows Portainer to override values without needing .env file in container
load_dotenv(override=False)  # Don't override existing environment variables

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the new database-backed SmartHome system

try:
    from app.configure_db import SmartHomeSystemDB as SmartHomeSystem
    DATABASE_MODE = True
    print("✓ Using PostgreSQL database backend")
except ImportError as e:
    print(f"⚠ Failed to import database backend: {e}")
    print("⚠ Falling back to JSON file backend with automatic configuration")
    from app.configure import SmartHomeSystem
    from utils.json_backup_manager import ensure_json_backup
    
    # Ensure JSON backup is ready
    try:
        json_manager = ensure_json_backup()
        print("✓ JSON backup system initialized")
    except Exception as backup_error:
        print(f"✗ Failed to initialize JSON backup: {backup_error}")
    
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
        
        # Setup system administrator if in database mode
        self.setup_sys_admin()
        
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
    
    @staticmethod
    def _normalize_device_id(raw_id):
        """Coerce device identifiers to int when numeric, otherwise return trimmed string."""
        if raw_id is None:
            return None
        if isinstance(raw_id, int):
            return raw_id
        if isinstance(raw_id, str):
            value = raw_id.strip()
            if not value:
                return None
            if value.isdigit():
                try:
                    return int(value)
                except ValueError:
                    return value
            return value
        return raw_id

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
        
        # Add URL prefix globals for easy environment switching
        # Empty string means root path deployment (no prefix)
        url_prefix = os.getenv('URL_PREFIX') or ''
        api_prefix = os.getenv('API_PREFIX') or '/api'
        static_prefix = os.getenv('STATIC_PREFIX') or '/static'
        socket_prefix = os.getenv('SOCKET_PREFIX') or '/socket.io'
        
        self.app.jinja_env.globals.update(
            URL_PREFIX=url_prefix,
            API_PREFIX=api_prefix,
            STATIC_PREFIX=static_prefix,
            SOCKET_PREFIX=socket_prefix
        )
        print(f"✓ URL prefixes configured: URL={url_prefix or '/'}, API={api_prefix}, STATIC={static_prefix}, SOCKET={socket_prefix}")

        @self.app.template_filter('fmt_ts')
        def fmt_ts(value):
            """Format timestamps uniformly as 'YYYY-MM-DD HH:MM'. Accepts datetime or string.
            - Truncates seconds and microseconds
            - Supports ISO strings with 'T' and common space-separated formats
            """
            try:
                from datetime import datetime
                if value is None:
                    return ''
                # If already a datetime
                if hasattr(value, 'strftime'):
                    return value.strftime('%Y-%m-%d %H:%M')
                s = str(value)
                # Try known formats
                for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
                    try:
                        dt = datetime.strptime(s, fmt)
                        return dt.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        pass
                # Fallback: extract date and HH:MM
                import re
                m = re.match(r'^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})', s)
                return f"{m.group(1)} {m.group(2)}" if m else s
            except Exception:
                return str(value)
    
    def setup_sys_admin(self):
        """Setup system administrator if in database mode"""
        # Sys-admin setup will happen in setup_routes after multi_db is initialized
        pass
    
    def _display_admin_credentials(self):
        """Display admin credentials if in JSON fallback mode"""
        try:
            # Check if we have a JSON fallback with admin credentials
            if (hasattr(self.smart_home, 'json_fallback') and 
                self.smart_home.json_fallback is not None):
                
                # Try to get admin credentials from JSON fallback
                json_mgr = self.smart_home.json_fallback
                config = json_mgr.get_config()
                users = config.get('users', {})
                
                # Look for sys-admin or any admin user
                admin_user = None
                admin_username = None
                admin_password = None
                
                # First look for sys-admin
                if 'sys-admin' in users:
                    admin_user = users['sys-admin']
                    admin_username = 'sys-admin'
                
                # If not found, look for any admin role
                if not admin_user:
                    for username, user_data in users.items():
                        if user_data.get('role') == 'admin':
                            admin_user = user_data
                            admin_username = username
                            break
                
                # Display credentials
                if admin_user and admin_username:
                    print("\n" + "="*70)
                    print("🔐 ADMIN CREDENTIALS (JSON FALLBACK MODE)")
                    print("="*70)
                    print(f"\n   Username: {admin_username}")
                    print(f"   Role: {admin_user.get('role', 'admin')}")
                    print(f"   Email: {admin_user.get('email', 'Not set')}")
                    print(f"\n⚠️  If you don't know the password, you can reset it:")
                    print(f"   Run: python reset_admin_password.py")
                    print("="*70 + "\n")
        except Exception as e:
            # Silent fail - not critical
            pass
    
    def _display_system_configuration(self):
        """Display system configuration information during startup"""
        try:
            # Display admin credentials if in JSON fallback mode
            self._display_admin_credentials()
            
            print("\n" + "="*70)
            print("📊 SYSTEM CONFIGURATION")
            print("="*70)
            
            # Display users
            users = self.smart_home.users
            if users:
                print(f"\n👥 Users ({len(users)}):")
                # Handle both DB mode (key=username) and JSON fallback (key=ID, username in 'name')
                for key, user_data in users.items():
                    # Determine if key is username or ID
                    if isinstance(user_data, dict):
                        username = key  # DB mode - key is username
                        user_id = user_data.get('id') or user_data.get('user_id', key)
                    else:
                        # Fallback - shouldn't happen but handle it
                        username = key
                        user_id = key
                    
                    role = user_data.get('role', 'user')
                    email = user_data.get('email', '')
                    is_system = user_data.get('is_system_user', False)
                    
                    system_marker = " 🔒 [SYSTEM]" if is_system else ""
                    email_str = f" - {email}" if email else ""
                    print(f"   • {username:<20} ({role:<6}){email_str}{system_marker}")
            else:
                print(f"\n👥 Users: None configured")
            
            # Display rooms
            rooms = self.smart_home.rooms
            room_count = len(rooms) if rooms else 0
            print(f"\n🏠 Rooms ({room_count}):")
            if rooms:
                for room in rooms:
                    print(f"   • {room}")
            else:
                print("   (no rooms configured)")
            
            # Display devices
            buttons = self.smart_home.buttons
            button_count = len(buttons) if buttons else 0
            temp_controls = self.smart_home.temperature_controls
            temp_count = len(temp_controls) if temp_controls else 0
            
            print(f"\n🔌 Devices ({button_count + temp_count}):")
            print(f"   • Buttons: {button_count}")
            if buttons:
                for btn in buttons:
                    btn_name = btn.get('name', 'Unknown')
                    btn_room = btn.get('room', 'Unknown')
                    btn_state = "ON" if btn.get('state') else "OFF"
                    print(f"     - {btn_name:<20} (in {btn_room:<15}) [{btn_state}]")
            print(f"   • Temperature Controls: {temp_count}")
            if temp_controls:
                for ctrl in temp_controls:
                    ctrl_name = ctrl.get('name', 'Unknown')
                    ctrl_room = ctrl.get('room', 'Unknown')
                    ctrl_temp = ctrl.get('temperature', 'N/A')
                    ctrl_enabled = "enabled" if ctrl.get('enabled', False) else "disabled"
                    print(f"     - {ctrl_name:<20} (in {ctrl_room:<15}) [{ctrl_temp}°C, {ctrl_enabled}]")
            
            # Display automations
            automations = self.smart_home.automations
            auto_count = len(automations) if automations else 0
            print(f"\n⚙️  Automations ({auto_count}):")
            if automations and auto_count > 0:
                for auto in automations:
                    name = auto.get('name', 'Unknown')
                    enabled = auto.get('enabled', False)
                    status = "✓ ENABLED" if enabled else "✗ DISABLED"
                    print(f"   • {name:<25} [{status}]")
            else:
                print("   (no automations configured)")
            
            # Display security state
            security_state = self.smart_home.security_state
            print(f"\n🔐 Security State: {security_state}")
            
            print("="*70 + "\n")
            
        except Exception as e:
            # Don't fail startup if displaying configuration fails
            print(f"⚠ Could not display system configuration: {e}\n")
    
    
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
            
            # Initialize multi_db for database mode
            self.multi_db = None
            if DATABASE_MODE:
                try:
                    print("🔧 Initializing Multi-home database manager...")
                    from utils.multi_home_db_manager import MultiHomeDBManager
                    
                    # Get database credentials from environment variables (no defaults)
                    db_host = os.getenv('DB_HOST')
                    db_port = int(os.getenv('DB_PORT', '5432'))
                    db_user = os.getenv('DB_USER')
                    db_password = os.getenv('DB_PASSWORD')
                    db_name = os.getenv('DB_NAME')
                    
                    # Validate required environment variables
                    if not all([db_host, db_user, db_password, db_name]):
                        missing = []
                        if not db_host: missing.append('DB_HOST')
                        if not db_user: missing.append('DB_USER')
                        if not db_password: missing.append('DB_PASSWORD')
                        if not db_name: missing.append('DB_NAME')
                        raise ValueError(
                            f"Missing required environment variables: {', '.join(missing)}. "
                            f"Please create a .env file based on .env.example"
                        )
                    
                    print(f"📊 Connecting to database: {db_user}@{db_host}:{db_port}/{db_name}")
                    
                    self.multi_db = MultiHomeDBManager(
                        host=db_host,
                        port=db_port,
                        user=db_user,
                        password=db_password,
                        database=db_name
                    )
                    self.app.config['MULTI_DB_MANAGER'] = self.multi_db
                    print(f"✓ Multi-home database manager initialized: {self.multi_db is not None}")
                except Exception as e:
                    print(f"⚠ Failed to initialize multi-home database manager: {e}")
                    import traceback
                    traceback.print_exc()
                    self.app.config.pop('MULTI_DB_MANAGER', None)
            else:
                print("ℹ Database mode disabled, skipping multi-home database manager")
                self.app.config.pop('MULTI_DB_MANAGER', None)
            
            # Initialize management logger
            # Use database logger when in database mode, JSON logger otherwise
            if DATABASE_MODE:
                try:
                    self.management_logger = DatabaseManagementLogger(multi_db=self.multi_db)
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
            
            # Initialize simple auth manager for database mode with multihouse support
            from app.simple_auth import SimpleAuthManager
            self.auth_manager = SimpleAuthManager(self.smart_home, multi_db=self.multi_db)
            
            # Initialize cache with Redis if available, fallback to SimpleCache
            from flask_caching import Cache
            
            # Check if we're in JSON fallback mode (database failed)
            # If so, skip Redis as it's likely on the same unreachable server
            in_json_fallback = (hasattr(self.smart_home, 'json_fallback') and 
                               self.smart_home.json_fallback is not None)
            
            if in_json_fallback:
                print("⚠ Database in JSON fallback mode - skipping Redis, using SimpleCache")
                cache_config = {
                    'CACHE_TYPE': 'SimpleCache',
                    'CACHE_DEFAULT_TIMEOUT': 600,
                    'CACHE_THRESHOLD': 500
                }
            else:
                # Try Redis first for better performance and persistence
                redis_url = os.getenv('REDIS_URL', None)
                redis_host = os.getenv('REDIS_HOST', None)
                redis_port = os.getenv('REDIS_PORT', 6379)
                
                if redis_url:
                    cache_config = {
                        'CACHE_TYPE': 'RedisCache',
                        'CACHE_REDIS_URL': redis_url,
                        'CACHE_DEFAULT_TIMEOUT': 600,
                        'CACHE_OPTIONS': {
                            'socket_connect_timeout': 2,  # 2 second connection timeout
                            'socket_timeout': 2,          # 2 second socket timeout
                            'retry_on_timeout': False
                        }
                    }
                    print("✓ Using Redis cache with URL")
                elif redis_host:
                    cache_config = {
                        'CACHE_TYPE': 'RedisCache',
                        'CACHE_REDIS_HOST': redis_host,
                        'CACHE_REDIS_PORT': int(redis_port),
                        'CACHE_DEFAULT_TIMEOUT': 600,
                        'CACHE_OPTIONS': {
                            'socket_connect_timeout': 2,  # 2 second connection timeout
                            'socket_timeout': 2,          # 2 second socket timeout
                            'retry_on_timeout': False
                        }
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
                # Test cache functionality (with short timeout to avoid hanging)
                self.cache.set('test_key', 'test_value', timeout=10)
                if self.cache.get('test_key') == 'test_value':
                    print("✓ Cache functionality verified")
                    self.cache.delete('test_key')
                else:
                    print("⚠ Cache test failed, may impact performance")
            except Exception as e:
                print(f"⚠ Cache initialization failed: {e}, using fallback")
                # Ultra-safe fallback
                cache_config = {'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600, 'CACHE_THRESHOLD': 500}
                self.cache = Cache(self.app, config=cache_config)
            
            # Initialize cache manager
            self.cache_manager = CacheManager(self.cache, self.smart_home)
            
            # Setup caching for SmartHome system
            setup_smart_home_caching(self.smart_home, self.cache_manager)
            
            # Warm up cache with critical data
            self._warm_up_cache()
            
            # Initialize automation scheduler for time-based automations (database mode only)
            self.automation_scheduler = None
            self.socket_automation_executor = None  # Executor for socket handlers
            if DATABASE_MODE and self.multi_db:
                try:
                    from utils.automation_executor import AutomationExecutor
                    from utils.automation_scheduler import AutomationScheduler
                    
                    # Create automation executor for socket handlers (socketio will be set in setup_socket_events)
                    self.socket_automation_executor = AutomationExecutor(self.multi_db, None)
                    
                    # Create automation executor for scheduler (no socketio needed for scheduler)
                    automation_executor = AutomationExecutor(self.multi_db, None)
                    
                    # Create and start scheduler
                    self.automation_scheduler = AutomationScheduler(self.multi_db, automation_executor)
                    self.automation_scheduler.start()
                    
                    print("✓ Automation scheduler initialized and started")
                except Exception as e:
                    print(f"⚠ Failed to initialize automation scheduler: {e}")
                    import traceback
                    traceback.print_exc()
            
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
                async_mail_manager=self.async_mail_manager,
                cache=self.cache,  # Pass the Flask cache object, not the cache_manager
                management_logger=self.management_logger,
                socketio=self.socketio,  # Add socketio parameter
                multi_db=self.multi_db  # Add multi_db parameter
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
                'multi_db': self.multi_db,
                'mail_manager': self.mail_manager,
                'async_mail_manager': self.async_mail_manager,
            }
            filtered_kwargs = {k: v for k, v in possible_kwargs.items() if k in accepted_params}
            # Helpful debug
            print(f"[DEBUG] Creating APIManager with kwargs: {sorted(filtered_kwargs.keys())}")
            self.api_manager = APIManager(**filtered_kwargs)
            
            # Register multi-home blueprint first
            try:
                from app.multi_home_routes import multi_home_bp, init_multi_home_routes
                # Initialize routes with multi_db instance
                print(f"🔗 Passing multi_db to multi_home_routes: {self.multi_db is not None}")
                init_multi_home_routes(self.multi_db)
                self.app.register_blueprint(multi_home_bp)
                print("✓ Multi-home routes registered successfully")
            except Exception as e:
                print(f"⚠ Failed to register multi-home routes: {e}")
                import traceback
                traceback.print_exc()
            
            # Register home settings blueprint after multi-home (needs multi_db)
            try:
                from app.home_settings_routes import home_settings_bp, init_home_settings_routes
                # Initialize routes with multi_db instance
                print(f"🔗 Passing multi_db to home_settings_routes: {self.multi_db is not None}")
                init_home_settings_routes(self.multi_db)
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
        # Set socketio instance for automation executor
        if self.socket_automation_executor:
            self.socket_automation_executor.socketio = self.socketio
            logger.info("[AUTOMATION] SocketIO connected to automation executor")
        
        # Set socketio instance for scheduler's automation executor
        if hasattr(self, 'automation_scheduler') and self.automation_scheduler:
            self.automation_scheduler.automation_executor.socketio = self.socketio
            logger.info("[AUTOMATION] SocketIO connected to scheduler's automation executor")
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            try:
                if 'user_id' not in session:
                    disconnect()
                    return False
                
                user_id_value = session.get('user_id')
                if not user_id_value:
                    emit('error', {'message': 'Not authenticated'})
                    return
                user_id = str(user_id_value)
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
                
                if room is None or name is None or not isinstance(new_state, bool):
                    emit('error', {'message': 'Invalid toggle payload'})
                    return

                user_id = session.get('user_id')
                if not user_id:
                    emit('error', {'message': 'Not authenticated'})
                    return

                def _normalize(value):
                    return (value or '').strip().lower()

                # Multi-home aware toggle handling
                multi_db = getattr(self, 'multi_db', None)
                if multi_db:
                    current_home_id = session.get('current_home_id')
                    if not current_home_id:
                        current_home_id = multi_db.get_user_current_home(user_id)
                        if current_home_id:
                            session['current_home_id'] = current_home_id

                    if not current_home_id:
                        emit('error', {'message': 'No home selected'})
                        return

                    # Find target button in current home (case-insensitive match)
                    buttons = multi_db.get_buttons(str(current_home_id), user_id) or []
                    name_norm = _normalize(name)
                    room_norm = _normalize(room)
                    target_button = None
                    name_only_match = None
                    for button in buttons:
                        btn_name = _normalize(button.get('name'))
                        btn_room = _normalize(button.get('room_name'))
                        if btn_name == name_norm and btn_room == room_norm:
                            target_button = button
                            break
                        if name_only_match is None and btn_name == name_norm:
                            name_only_match = button
                    if target_button is None:
                        target_button = name_only_match

                    if not target_button:
                        emit('error', {'message': 'Button not found'})
                        return

                    success = multi_db.update_device(target_button['id'], user_id, state=bool(new_state))
                    if not success:
                        emit('error', {'message': 'Failed to toggle button'})
                        return

                    # Trigger automation execution after successful state change
                    if self.socket_automation_executor:
                        try:
                            results = self.socket_automation_executor.process_device_trigger(
                                device_id=str(target_button['id']),
                                room_name=target_button.get('room_name', ''),
                                device_name=target_button.get('name', ''),
                                new_state=bool(new_state),
                                home_id=str(current_home_id),
                                user_id=str(user_id)
                            )
                            if results:
                                logger.info(f"[AUTOMATION] Executed {len(results)} automations via SocketIO")
                        except Exception as auto_error:
                            logger.error(f"[AUTOMATION] Error in SocketIO automation trigger: {auto_error}")
                            import traceback
                            traceback.print_exc()

                    updated_button = multi_db.get_device(target_button['id'], user_id) or target_button
                    payload_room = updated_button.get('room_name') or room
                    payload_name = updated_button.get('name') or name
                    payload_state = updated_button.get('state') if updated_button.get('state') is not None else new_state
                    payload_room_id = updated_button.get('room_id', '')  # Add room_id for consistent switch matching

                    # Broadcast update to all connected clients
                    self.socketio.emit('update_button', {
                        'room': payload_room,
                        'room_id': str(payload_room_id) if payload_room_id else '',  # Include room_id for UUID-based switch IDs
                        'name': payload_name,
                        'state': payload_state,
                        'device_id': str(target_button['id'])  # Include device_id for fallback matching
                    })
                    self.socketio.emit('sync_button_states', {
                        f"{payload_room}_{payload_name}": payload_state
                    })

                    # Invalidate relevant caches to reflect immediate state change
                    try:
                        if hasattr(self, 'cache_manager') and self.cache_manager:
                            self.cache.delete('buttons_list')
                            self.cache.delete(f'buttons_room_{payload_room}')
                    except Exception as cache_err:
                        print(f"[DEBUG] Failed to invalidate button caches: {cache_err}")

                    # Log the action using management logger if available
                    if hasattr(self.management_logger, 'log_device_action'):
                        user_data = self.smart_home.get_user_data(user_id) if user_id else None
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                            device_name=payload_name,
                            room=payload_room,
                            action='toggle',
                            new_state=payload_state,
                            ip_address=request.environ.get('REMOTE_ADDR') or ''
                        )

                    emit('button_toggled', {
                        'success': True,
                        'room': payload_room,
                        'name': payload_name,
                        'state': payload_state
                    })
                    return

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

                user_id = session.get('user_id')
                room = data.get('room')
                name = data.get('name')
                control_id = data.get('id')

                try:
                    temperature = float(data.get('temperature', 22))
                except (TypeError, ValueError):
                    emit('error', {'message': 'Invalid temperature value'})
                    return

                print(f"[DEBUG] Parsed values: room='{room}', name='{name}', id='{control_id}', temperature={temperature}")

                if not (16 <= temperature <= 30):
                    emit('error', {'message': 'Temperature must be between 16°C and 30°C'})
                    return

                multi_db = getattr(self, 'multi_db', None)
                if multi_db:
                    device = None
                    device_identifier = self._normalize_device_id(control_id) if control_id is not None else None
                    if device_identifier is not None:
                        try:
                            device = multi_db.get_device(device_identifier, str(user_id))
                        except Exception as get_err:
                            print(f"[DEBUG] Error fetching temperature control {control_id}: {get_err}")

                    if not device:
                        current_home_id = session.get('current_home_id') or multi_db.get_user_current_home(str(user_id))
                        if current_home_id:
                            controls = multi_db.get_temperature_controls(str(current_home_id), str(user_id))
                            for ctrl in controls:
                                if control_id and str(ctrl.get('id')) == str(control_id):
                                    device = ctrl
                                    break
                                if not control_id and (ctrl.get('name') == name) and (not room or (ctrl.get('room_name') or '').lower() == (room or '').lower()):
                                    device = ctrl
                                    break

                    if not device:
                        emit('error', {'message': 'Temperature control not found'})
                        return

                    update_payload = {'temperature': temperature}
                    target_device_id = self._normalize_device_id(device.get('id', device_identifier))
                    if target_device_id is None:
                        fallback_id = device_identifier if device_identifier is not None else device.get('id')
                        target_device_id = self._normalize_device_id(fallback_id)
                    if target_device_id is None:
                        emit('error', {'message': 'Invalid device identifier'})
                        return
                    if not multi_db.update_device(target_device_id, str(user_id), **update_payload):
                        emit('error', {'message': 'Failed to set temperature'})
                        return

                    updated_device = multi_db.get_device(target_device_id, str(user_id)) or device
                    payload_room = updated_device.get('room_name') or room or ''
                    payload_name = updated_device.get('name') or name or ''
                    payload_temperature = updated_device.get('temperature') if updated_device.get('temperature') is not None else temperature

                    self.socketio.emit('update_temperature', {
                        'room': payload_room,
                        'name': payload_name,
                        'temperature': payload_temperature
                    })
                    self.socketio.emit('sync_temperature', {
                        'name': payload_name,
                        'temperature': payload_temperature
                    })

                    try:
                        if hasattr(self, 'cache_manager') and self.cache_manager:
                            self.cache.delete('temperature_controls')
                            self.cache.delete(f'temp_controls_room_{payload_room}')
                    except Exception as cache_err:
                        print(f"[DEBUG] Failed to invalidate temperature caches: {cache_err}")

                    if hasattr(self.management_logger, 'log_device_action'):
                        user_data = self.smart_home.get_user_data(user_id) if user_id else None
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                            device_name=payload_name,
                            room=payload_room,
                            action='set_temperature',
                            new_state=payload_temperature,
                            ip_address=request.environ.get('REMOTE_ADDR') or ''
                        )

                    emit('temperature_set', {
                        'success': True,
                        'room': payload_room,
                        'name': payload_name,
                        'temperature': payload_temperature
                    })
                    return

                # Fallback to legacy behaviour
                success = False
                if DATABASE_MODE:
                    print(f"[DEBUG] Using database mode (legacy fallback)")
                    success = self.smart_home.update_temperature_control_value(room, name, temperature)
                    print(f"[DEBUG] Database update success: {success}")
                else:
                    print(f"[DEBUG] Using JSON mode (legacy fallback)")
                    for control in self.smart_home.temperature_controls:
                        if control['room'] == room and control['name'] == name:
                            control['temperature'] = temperature
                            self.smart_home.save_config()
                            success = True
                            break

                if success:
                    if DATABASE_MODE:
                        self.smart_home.set_room_temperature(room, temperature)
                    else:
                        self.smart_home.temperature_states[room] = temperature
                        self.smart_home.save_config()

                    self.socketio.emit('update_temperature', {
                        'room': room,
                        'name': name,
                        'temperature': temperature
                    })

                    try:
                        if hasattr(self, 'cache_manager') and self.cache_manager:
                            self.cache.delete('temperature_controls')
                            self.cache.delete(f'temp_controls_room_{room}')
                    except Exception as cache_err:
                        print(f"[DEBUG] Failed to invalidate temperature caches: {cache_err}")

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

                user_id_value = session.get('user_id')
                if not user_id_value:
                    emit('error', {'message': 'Not authenticated'})
                    return
                user_id = str(user_id_value)

                room = data.get('room')
                name = data.get('name')
                control_id = data.get('id')
                enabled_raw = data.get('enabled', True)

                if isinstance(enabled_raw, str):
                    enabled = enabled_raw.strip().lower() in ('true', '1', 'yes', 'on')
                else:
                    enabled = bool(enabled_raw)

                print(f"[DEBUG] Parsed values: room='{room}', name='{name}', id='{control_id}', enabled={enabled}")

                multi_db = getattr(self, 'multi_db', None)
                if multi_db:
                    device = None
                    device_identifier = self._normalize_device_id(control_id) if control_id is not None else None
                    if device_identifier is not None:
                        try:
                            device = multi_db.get_device(device_identifier, str(user_id))
                        except Exception as get_err:
                            print(f"[DEBUG] Error fetching temperature control {control_id}: {get_err}")

                    if not device:
                        current_home_id = session.get('current_home_id') or multi_db.get_user_current_home(str(user_id))
                        if current_home_id:
                            controls = multi_db.get_temperature_controls(str(current_home_id), str(user_id))
                            for ctrl in controls:
                                if control_id and str(ctrl.get('id')) == str(control_id):
                                    device = ctrl
                                    break
                                if not control_id and (ctrl.get('name') == name) and (not room or (ctrl.get('room_name') or '').lower() == (room or '').lower()):
                                    device = ctrl
                                    break

                    if not device:
                        emit('error', {'message': 'Temperature control not found'})
                        return

                    target_device_id = self._normalize_device_id(device.get('id', device_identifier))
                    if target_device_id is None:
                        fallback_id = device_identifier if device_identifier is not None else device.get('id')
                        target_device_id = self._normalize_device_id(fallback_id)
                    if target_device_id is None:
                        emit('error', {'message': 'Invalid device identifier'})
                        return
                    if not multi_db.update_device(target_device_id, str(user_id), enabled=enabled):
                        emit('error', {'message': 'Failed to toggle temperature control enabled state'})
                        return

                    updated_device = multi_db.get_device(target_device_id, str(user_id)) or device
                    payload_room = updated_device.get('room_name') or room or ''
                    payload_name = updated_device.get('name') or name or ''
                    payload_enabled = bool(updated_device.get('enabled', enabled))

                    self.socketio.emit('update_temperature_control_enabled', {
                        'id': updated_device.get('id'),
                        'room': payload_room,
                        'name': payload_name,
                        'enabled': payload_enabled
                    })

                    # Trigger automation execution after successful thermostat state change
                    if self.socket_automation_executor:
                        try:
                            results = self.socket_automation_executor.process_device_trigger(
                                device_id=str(updated_device.get('id')),
                                room_name=payload_room,
                                device_name=payload_name,
                                new_state=payload_enabled,  # Thermostat enabled state (True/False)
                                home_id=str(current_home_id),
                                user_id=str(user_id)
                            )
                            if results:
                                logger.info(f"[AUTOMATION] Executed {len(results)} automations via SocketIO (thermostat trigger)")
                        except Exception as auto_error:
                            logger.error(f"[AUTOMATION] Error in SocketIO automation trigger (thermostat): {auto_error}")
                            import traceback
                            traceback.print_exc()

                    try:
                        if hasattr(self, 'cache_manager') and self.cache_manager:
                            self.cache.delete('temperature_controls')
                            self.cache.delete(f'temp_controls_room_{payload_room}')
                    except Exception as cache_err:
                        print(f"[DEBUG] Failed to invalidate temperature caches: {cache_err}")

                    if hasattr(self.management_logger, 'log_device_action'):
                        user_data = self.smart_home.get_user_data(user_id) if user_id else None
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                            device_name=payload_name,
                            room=payload_room,
                            action='toggle_temperature_enabled',
                            new_state=payload_enabled,
                            ip_address=request.environ.get('REMOTE_ADDR') or ''
                        )

                    emit('temperature_control_enabled_toggled', {
                        'success': True,
                        'room': payload_room,
                        'name': payload_name,
                        'enabled': payload_enabled
                    })
                    return

                print(f"[DEBUG] Falling back to legacy toggle flow")
                success = False
                if DATABASE_MODE:
                    print(f"[DEBUG] Using database mode for enabled toggle")
                    success = self.smart_home.toggle_temperature_control_enabled(room, name, enabled)
                    print(f"[DEBUG] Database enabled update success: {success}")
                else:
                    print(f"[DEBUG] Using JSON mode for enabled toggle")
                    for control in self.smart_home.temperature_controls:
                        if control['room'] == room and control['name'] == name:
                            control['enabled'] = enabled
                            self.smart_home.save_config()
                            success = True
                            break

                if success:
                    self.socketio.emit('update_temperature_control_enabled', {
                        'room': room,
                        'name': name,
                        'enabled': enabled
                    })

                    try:
                        if hasattr(self, 'cache_manager') and self.cache_manager:
                            self.cache.delete('temperature_controls')
                            self.cache.delete(f'temp_controls_room_{room}')
                    except Exception as cache_err:
                        print(f"[DEBUG] Failed to invalidate temperature caches: {cache_err}")

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
                user_id = str(session.get('user_id'))
                home_id = data.get('home_id')
                success = False

                multi_db = getattr(self, 'multi_db', None)
                if multi_db:
                    try:
                        if not home_id:
                            home_id = session.get('current_home_id') or multi_db.get_user_current_home(user_id)
                        if not home_id:
                            emit('error', {'message': 'Brak wybranego domu'})
                            return

                        success = multi_db.set_security_state(str(home_id), user_id, new_state, {
                            'source': 'socket',
                            'timestamp': datetime.utcnow().isoformat()
                        })

                        if not success:
                            emit('error', {'message': 'Brak uprawnień do zmiany stanu zabezpieczeń'})
                            return

                        payload = {'state': new_state, 'home_id': str(home_id)}
                        print(f"[DEBUG] Multi-home mode - security state persisted for home {home_id}")
                    except PermissionError:
                        emit('error', {'message': 'Brak dostępu do wybranego domu'})
                        return
                    except Exception as err:
                        print(f"[DEBUG] Failed to set security state in multi-home mode: {err}")
                        emit('error', {'message': 'Nie udało się zapisać stanu zabezpieczeń'})
                        return
                else:
                    # Update security state in legacy single-home mode
                    self.smart_home.security_state = new_state
                    if DATABASE_MODE:
                        success = True
                        print("[DEBUG] Database mode - state saved automatically")
                    else:
                        success = self.smart_home.save_config()
                        print(f"[DEBUG] JSON mode - save_config result: {success}")
                    payload = {'state': new_state, 'home_id': None}
                    home_id = None

                if success:
                    # Broadcast update to all connected clients
                    self.socketio.emit('update_security_state', payload)
                    print(f"[DEBUG] Broadcasted security state update: {payload}")
                    
                    # Log the action
                    if user_id:
                        user_data = self.smart_home.get_user_data(user_id)
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown'),
                            device_name='Security System',
                            room='System',
                            action='set_security_state',
                            new_state={'state': new_state, 'home_id': str(home_id) if home_id else None},
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
        def handle_get_security_state(data=None):
            """Handle security state request via WebSocket"""
            try:
                print(f"[DEBUG] get_security_state called")
                print(f"[DEBUG] Session contents: {dict(session)}")
                
                if 'user_id' not in session:
                    print("[DEBUG] No user_id in session - authentication failed")
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                print(f"[DEBUG] Authenticated user_id: {session.get('user_id')}")
                user_id = str(session.get('user_id'))
                requested_home_id = None
                if isinstance(data, dict):
                    requested_home_id = data.get('home_id')
                home_id = requested_home_id or (session.get('current_home_id') if getattr(self, 'multi_db', None) else None)
                current_state = self.smart_home.security_state

                multi_db = getattr(self, 'multi_db', None)
                if multi_db:
                    try:
                        if not home_id:
                            home_id = multi_db.get_user_current_home(user_id)
                        if home_id:
                            current_state = multi_db.get_security_state(str(home_id), user_id)
                    except Exception as err:
                        print(f"[DEBUG] Failed to fetch multi-home security state: {err}")

                print(f"[DEBUG] Current security state from backend: {current_state} (home: {home_id})")
                
                # Send current state to client
                emit('update_security_state', {'state': current_state, 'home_id': str(home_id) if home_id else None})
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
        
        # Display system configuration
        self._display_system_configuration()
        
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
        # Environment variables are already loaded at the top of the file
        # Priority: 1) System environment variables (Portainer GUI)
        #          2) .env file in project root (local development)
        
        # Get configuration from environment
        server_host = os.getenv('SERVER_HOST', '0.0.0.0')
        server_port = int(os.getenv('SERVER_PORT', 5000))
        
        # Start background scheduler for periodic tasks
        try:
            from utils.background_scheduler import scheduler
            scheduler.start()
            print("✅ Background scheduler started (City cache updates: Mondays at 22:00)")
        except Exception as e:
            print(f"⚠️  Warning: Failed to start background scheduler: {e}")
        
        # Create and run the application
        smart_home_app = SmartHomeApp()
        # Use configuration from environment variables
        smart_home_app.run(host=server_host, port=server_port, debug=False)
        
    except Exception as e:
        print(f"💥 Failed to start SmartHome Application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
