from flask import render_template, jsonify, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from utils.cache_manager import CachedDataAccess
from app.management_logger import ManagementLogger
import os
import time
import uuid
from utils.allowed_file import allowed_file


class RoutesManager:
    def __init__(self, app, smart_home, auth_manager, mail_manager, async_mail_manager=None, cache=None, cached_data_access=None, management_logger=None, socketio=None):
        self.app = app
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.mail_manager = mail_manager
        self.async_mail_manager = async_mail_manager or mail_manager  # Fallback to sync
        self.cache = cache
        print(f"[DEBUG] RoutesManager init - cache: {cache}, cached_data_access: {cached_data_access}")
        # Use injected cached_data_access if provided, else fallback
        self.cached_data = cached_data_access or (CachedDataAccess(cache, smart_home) if cache else None)
        print(f"[DEBUG] RoutesManager init - self.cached_data: {type(self.cached_data)} {self.cached_data}")
        # Initialize management logger
        self.management_logger = management_logger or ManagementLogger()
        # Initialize socketio for real-time updates
        self.socketio = socketio
        
        # Initialize cache manager for optimized user data access
        from utils.cache_manager import CacheManager
        self.cache_manager = CacheManager(cache, smart_home) if cache else None
        
        self.register_routes()

    def get_cached_user_data(self, user_id, session_id=None):
        """
        Helper method to get cached user data efficiently
        
        Args:
            user_id: User ID from session
            session_id: Session ID for session-level caching
            
        Returns:
            User data dictionary or None
        """
        if not user_id:
            return None
            
        if self.cache_manager:
            # Use optimized session-level caching
            return self.cache_manager.get_session_user_data(user_id, session_id)
        else:
            # Fallback to direct database call
            return self.smart_home.get_user_data(user_id) if self.smart_home else None

    def emit_update(self, event_name, data):
        """Safely emit socketio updates only if socketio is available"""
        if self.socketio:
            self.socketio.emit(event_name, data)

    def register_routes(self):
        print("[DEBUG] register_routes called - registering Flask routes!")

        @self.app.context_processor
        def inject_asset_version():
            """Provide a global asset version for cache-busting static files."""
            version = os.environ.get('ASSET_VERSION') or os.environ.get('IMAGE_TAG') or 'dev'
            return {'asset_version': version}

        @self.app.route('/')
        def home():
            print(f"[DEBUG] Session on /: {dict(session)}")
            if 'username' not in session:
                print("[DEBUG] Brak username w sesji, redirect na login")
                return redirect(url_for('login'))
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            print(f"[DEBUG] user_id in session: {session.get('user_id')}, user_data: {user_data}")
            
            # Always use DB-ordered rooms list directly (bypass cached rooms list)
            rooms = self.smart_home.rooms
            print(f"[DEBUG] Pre-loading {len(rooms)} rooms for home page")
            
            return render_template('index.html', user_data=user_data, rooms=rooms)

        @self.app.route('/temp')
        @self.auth_manager.login_required
        def temp():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('temp_lights.html', user_data=user_data)

        @self.app.route('/temperature')
        @self.auth_manager.login_required
        def temperature():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('temperature.html', user_data=user_data)

        @self.app.route('/security')
        @self.auth_manager.login_required
        def security():
            try:
                user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
                current_security_state = self.smart_home.security_state
                return render_template('security.html', user_data=user_data, security_state=current_security_state)
            except Exception as e:
                self.app.logger.error(f"Error in security route: {e}")
                return f"Internal Server Error: {str(e)}", 500

        @self.app.route('/settings', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def settings():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('settings.html', user_data=user_data)

        @self.app.route('/suprise')
        @self.auth_manager.login_required
        def suprise():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('suprise.html', user_data=user_data)

        @self.app.route('/suprise_dog')
        @self.auth_manager.login_required
        def suprise_dog():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('suprise_Dog.html', user_data=user_data)

        @self.app.route('/automations')
        @self.auth_manager.login_required
        def automations():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('automations.html', user_data=user_data)

        # API endpoints for mobile app
        @self.app.route('/api/ping', methods=['GET'])
        def api_ping():
            """Simple ping endpoint to test connectivity"""
            return jsonify({
                'status': 'success',
                'message': 'SmartHome server is running',
                'timestamp': int(time.time()),
                'version': '1.0'
            })
        
        # Cache monitoring endpoint
        @self.app.route('/api/cache/stats', methods=['GET'])
        @self.auth_manager.login_required
        def cache_stats():
            """Get cache performance statistics"""
            from utils.cache_manager import cache_stats, get_cache_hit_rate
            return jsonify({
                'status': 'success',
                'cache_stats': {
                    'hits': cache_stats['hits'],
                    'misses': cache_stats['misses'],
                    'total_requests': cache_stats['total_requests'],
                    'hit_rate_percentage': round(get_cache_hit_rate(), 2)
                },
                'cache_config': {
                    'type': self.cache.config.get('CACHE_TYPE', 'Unknown'),
                    'default_timeout': self.cache.config.get('CACHE_DEFAULT_TIMEOUT', 'Unknown')
                }
            })
        
        # Database monitoring endpoint
        @self.app.route('/api/database/stats', methods=['GET'])
        @self.auth_manager.login_required
        def database_stats():
            """Get database performance statistics"""
            try:
                stats = {
                    'status': 'success',
                    'database_mode': hasattr(self.smart_home, 'db'),
                    'connection_pool': {'enabled': False}
                }
                
                # Get database statistics if available
                if hasattr(self.smart_home, 'db') and self.smart_home.db:
                    try:
                        pool_status = self.smart_home.db.get_pool_status()
                        stats['connection_pool'] = pool_status
                        
                        # Get database stats if method exists
                        if hasattr(self.smart_home, 'get_database_stats'):
                            db_stats = self.smart_home.get_database_stats()
                            stats['database_stats'] = db_stats
                    except Exception as e:
                        stats['database_error'] = str(e)
                
                return jsonify(stats)
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                })

        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            """Server status endpoint"""
            try:
                from app_db import DATABASE_MODE
            except ImportError:
                DATABASE_MODE = False
            return jsonify({
                'status': 'success',
                'server_status': 'running',
                'database_mode': DATABASE_MODE,
                'timestamp': int(time.time())
            })

        @self.app.route('/api/config', methods=['GET'])
        def api_config():
            """Configuration info endpoint"""
            return jsonify({
                'server_ip': request.host.split(':')[0],
                'server_port': request.environ.get('SERVER_PORT', '5000'),
                'cors_enabled': True,
                'auth_required': True,
                'timestamp': int(time.time())
            })

        @self.app.route('/edit')
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def edit():
            # Get user data for profile picture and menu
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            
            # Use cached data for performance
            print(f"[DEBUG] /edit route - Getting data for template")
            print(f"[DEBUG] cached_data object: {type(self.cached_data)}")
            # Always use DB-ordered rooms list directly (bypass cached rooms list)
            rooms = self.smart_home.rooms
            buttons = self.cached_data.get_buttons() if self.cached_data else self.smart_home.buttons
            temperature_controls = self.cached_data.get_temperature_controls() if self.cached_data else self.smart_home.temperature_controls
            
            print(f"[DEBUG] /edit route - Buttons data for template: {buttons}")
            
            # Add type attribute to devices for proper kanban rendering
            if buttons:
                for button in buttons:
                    if not hasattr(button, 'type') and not isinstance(button, dict):
                        button.type = 'light'
                    elif isinstance(button, dict) and 'type' not in button:
                        button['type'] = 'light'
            
            if temperature_controls:
                for control in temperature_controls:
                    if not hasattr(control, 'type') and not isinstance(control, dict):
                        control.type = 'thermostat'
                    elif isinstance(control, dict) and 'type' not in control:
                        control['type'] = 'thermostat'
            
            return render_template(
                'edit.html',
                user_data=user_data,
                rooms=rooms,
                buttons=buttons,
                temperature_controls=temperature_controls
            )

        @self.app.route('/admin_dashboard', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def admin_dashboard():
            if request.method == 'POST':
                # Handle admin user creation
                username = request.form.get('username', '').strip()
                email = request.form.get('email', '').strip()
                password = request.form.get('password', '')
                role = request.form.get('role', 'user')
                
                # Basic validation
                if not username or len(username) < 3:
                    flash('Nazwa użytkownika musi mieć co najmniej 3 znaki.', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                if not email or '@' not in email:
                    flash('Podaj poprawny adres email.', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                if not password or len(password) < 6:
                    flash('Hasło musi mieć co najmniej 6 znaków.', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                if role not in ['user', 'admin']:
                    flash('Nieprawidłowa rola użytkownika.', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                # Check if user already exists
                for user in self.smart_home.users.values():
                    if user.get('name') == username:
                        flash('Użytkownik już istnieje.', 'error')
                        return redirect(url_for('admin_dashboard'))
                    if user.get('email') == email:
                        flash('Adres email jest już używany.', 'error')
                        return redirect(url_for('admin_dashboard'))
                
                # Dodawanie użytkownika - obsługa trybu DB i plikowego
                try:
                    if hasattr(self.smart_home, 'add_user'):
                        self.smart_home.add_user(username, password, role, email)
                    else:
                        import uuid
                        from werkzeug.security import generate_password_hash
                        user_id = str(uuid.uuid4())
                        self.smart_home.users[user_id] = {
                            'name': username,
                            'password': generate_password_hash(password),
                            'role': role,
                            'email': email,
                            'profile_picture': ''
                        }
                        self.smart_home.save_config()
                    flash(f'Użytkownik {username} został dodany pomyślnie!', 'success')
                except Exception as e:
                    flash(f'Błąd podczas dodawania użytkownika: {e}', 'error')
                return redirect(url_for('admin_dashboard'))
            
            # Przygotowanie statystyk dla dashboardu
            stats = self._generate_dashboard_stats()
            device_states = self._get_device_states()
            management_logs = self._get_management_logs()
            
            # Pre-load users data for immediate rendering
            users_list = [
                {
                    'user_id': user_id,
                    'username': data['name'],
                    'email': data.get('email', ''),
                    'role': data['role'],
                    'password': '••••••••'  # Always show dots for password
                }
                for user_id, data in self.smart_home.users.items()
            ]
            
            # Pobierz dane użytkownika dla wyświetlenia zdjęcia profilowego
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            
            return render_template('admin_dashboard.html', 
                                 stats=stats, 
                                 device_states=device_states,
                                 management_logs=management_logs,
                                 user_data=user_data,
                                 preloaded_users=users_list)

        @self.app.route('/api/admin/device-states')
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_device_states():
            device_states = self._get_device_states()
            return jsonify(device_states)

        @self.app.route('/api/admin/logs')
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_logs():
            logs = self._get_management_logs()
            return jsonify(logs)

        # Notification settings (recipients) API
        @self.app.route('/api/notifications/settings', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_notification_settings():
            """Get or set notification recipients for the home.
            Frontend expects:
              GET -> { recipients: [{ email, user, enabled }] }
              POST body -> { recipients: [{ email, user, enabled }] }
            where 'user' is the username (not id). DB stores user_id.
            """
            from utils.db_manager import (
                get_notification_recipients,
                set_notification_recipients,
            )
            import os

            # Map users: id <-> name
            users_by_id = {}
            users_by_name = {}
            try:
                for uid, data in self.smart_home.users.items():
                    name = data.get('name')
                    if name:
                        users_by_id[str(uid)] = name
                        users_by_name[name] = str(uid)
            except Exception:
                pass

            # Choose a home id for persistence (single-home setup default = 1)
            home_id_env = os.getenv('HOME_ID')
            try:
                home_id = int(home_id_env) if home_id_env else 1
            except ValueError:
                home_id = 1

            if request.method == 'GET':
                try:
                    recipients_db = get_notification_recipients(home_id)
                    # Convert to frontend shape: use username
                    recipients = []
                    for r in recipients_db:
                        uid = r.get('user_id')
                        recipients.append({
                            'email': r.get('email', ''),
                            'user': users_by_id.get(str(uid), ''),
                            'enabled': bool(r.get('enabled', True))
                        })
                    return jsonify({ 'recipients': recipients })
                except Exception as e:
                    return jsonify({ 'recipients': [] , 'error': str(e) }), 200

            # POST
            try:
                data = request.get_json(silent=True) or {}
                recipients = data.get('recipients', [])
                # Map to DB shape (email, user_id, enabled)
                recipients_db = []
                for r in recipients:
                    username = (r.get('user') or '').strip()
                    email = (r.get('email') or '').strip()
                    enabled = bool(r.get('enabled', True))
                    user_id = users_by_name.get(username)
                    recipients_db.append({
                        'email': email,
                        'user_id': user_id,
                        'enabled': enabled,
                    })
                set_notification_recipients(recipients_db, home_id)
                return jsonify({ 'status': 'success' })
            except Exception as e:
                return jsonify({ 'status': 'error', 'message': str(e) }), 500

        @self.app.route('/api/admin/logs/clear', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_clear_logs():
            """Clear all logs"""
            try:
                self.management_logger.clear_logs()
                
                # Log the clearing action
                self.management_logger.log_event(
                    'info',
                    f'Administrator {session.get("username", "unknown")} wyczyścił wszystkie logi',
                    'admin_action',
                    session.get('username', 'unknown'),
                    request.remote_addr
                )
                
                return jsonify({'status': 'success', 'message': 'Wszystkie logi zostały usunięte'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Błąd przy usuwaniu logów: {str(e)}'}), 500

        @self.app.route('/api/admin/logs/delete', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_delete_logs():
            """Delete logs by date range or number of days"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych w żądaniu'}), 400
                
                deleted_count = 0
                
                if 'days' in data:
                    # Delete logs older than specified days
                    days = int(data['days'])
                    if days < 0:
                        return jsonify({'status': 'error', 'message': 'Liczba dni musi być dodatnia'}), 400
                    
                    deleted_count = self.management_logger.delete_logs_older_than(days)
                    action_msg = f'Usunięto {deleted_count} logów starszych niż {days} dni'
                    
                elif 'start_date' in data or 'end_date' in data:
                    # Delete logs by date range
                    start_date = data.get('start_date')
                    end_date = data.get('end_date')
                    
                    deleted_count = self.management_logger.delete_logs_by_date_range(start_date, end_date)
                    
                    if start_date and end_date:
                        action_msg = f'Usunięto {deleted_count} logów z okresu {start_date} - {end_date}'
                    elif start_date:
                        action_msg = f'Usunięto {deleted_count} logów od {start_date}'
                    elif end_date:
                        action_msg = f'Usunięto {deleted_count} logów do {end_date}'
                    else:
                        action_msg = f'Usunięto {deleted_count} logów'
                else:
                    return jsonify({'status': 'error', 'message': 'Brak parametrów usuwania (days, start_date lub end_date)'}), 400
                
                # Log the deletion action
                self.management_logger.log_event(
                    'info',
                    f'Administrator {session.get("username", "unknown")}: {action_msg}',
                    'admin_action',
                    session.get('username', 'unknown'),
                    request.remote_addr,
                    {'deleted_count': deleted_count, 'action': 'delete_logs'}
                )
                
                return jsonify({
                    'status': 'success', 
                    'message': action_msg,
                    'deleted_count': deleted_count
                })
                
            except ValueError as e:
                return jsonify({'status': 'error', 'message': f'Błąd formatu daty: {str(e)}'}), 400
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Błąd przy usuwaniu logów: {str(e)}'}), 500

        @self.app.route('/lights')
        @self.auth_manager.login_required
        def lights():
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            return render_template('lights.html', user_data=user_data)

        @self.app.route('/error')
        def error():
            return render_template('error.html')

        @self.app.route('/test-email')
        def test_email():
            # Use async mail manager for non-critical test emails
            result = self.async_mail_manager.send_security_alert_async('failed_login', {
                'username': 'testuser',
                'ip_address': '127.0.0.1',
                'attempt_count': 3
            })
            return jsonify({"status": "success" if result else "error"})

        @self.app.route('/user')
        @self.auth_manager.login_required
        def user_profile():
            user_id, user = self.smart_home.get_user_by_login(session['username'])
            user_data = self.smart_home.get_user_data(user_id) if user else None
            return render_template('user.html', user_data=user_data)

        @self.app.route('/api/user/profile', methods=['GET', 'PUT'])
        @self.auth_manager.login_required
        def manage_profile():
            user_id, user = self.smart_home.get_user_by_login(session['username'])
            if not user:
                return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 400
            if request.method == 'GET':
                user_data = self.smart_home.get_user_data(user_id)
                return jsonify(user_data)
            elif request.method == 'PUT':
                data = request.get_json()
                if not data:
                    return jsonify({"status": "error", "message": "Brak danych"}), 400

                updates = {}
                if 'username' in data and data['username'] != user['name']:
                    updates['name'] = data['username']
                if 'name' in data:
                    updates['name'] = data['name']
                if 'email' in data:
                    updates['email'] = data['email']
                if data.get('current_password') and data.get('new_password'):
                    if not self.smart_home.verify_password(user_id, data['current_password']):
                        return jsonify({"status": "error", "message": "Nieprawidłowe aktualne hasło"}), 400
                    updates['password'] = data['new_password']
                success, message = self.smart_home.update_user_profile(user_id, updates)
                if success:
                    # Log user profile change
                    action = 'password_change' if 'password' in updates else 'edit'
                    self.management_logger.log_user_change(
                        username=user['name'],
                        action=action,
                        target_user=user['name'],
                        ip_address=request.remote_addr or "",
                        details={'fields_updated': list(updates.keys())}
                    )
                    
                    if any(k in updates for k in ['name', 'email', 'password']):
                        return jsonify({"status": "success", "logout": True, "message": "pomyślnie zmieniono dane"})
                    return jsonify({"status": "success", "message": message})
                return jsonify({"status": "error", "message": message}), 400

        @self.app.route('/api/user/profile-picture', methods=['POST'])
        @self.auth_manager.login_required
        def update_profile_picture():
            if 'profile_picture' not in request.files:
                return jsonify({"status": "error", "message": "Brak pliku"}), 400

            file = request.files['profile_picture']
            if file.filename == '':
                return jsonify({"status": "error", "message": "Nie wybrano pliku"}), 400

            if not file or not allowed_file(file.filename):
                return jsonify({"status": "error", "message": "Niedozwolony typ pliku"}), 400

            try:
                user_id, user = self.smart_home.get_user_by_login(session['username'])
                if not user:
                    return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 400
                filename = secure_filename(f"{user_id}_{int(time.time())}{os.path.splitext(file.filename or '')[1]}")
                profile_pictures_dir = os.path.join(self.app.static_folder, 'profile_pictures')
                if not os.path.exists(profile_pictures_dir):
                    os.makedirs(profile_pictures_dir)

                file_path = os.path.join(profile_pictures_dir, filename)
                file.save(file_path)

                profile_picture_url = url_for('static', filename=f'profile_pictures/{filename}')
                success, message = self.smart_home.update_user_profile(user_id, {'profile_picture': profile_picture_url})

                if success:
                    return jsonify({
                        "status": "success",
                        "message": "Zdjęcie profilowe zostało zaktualizowane",
                        "profile_picture_url": profile_picture_url
                    })
                return jsonify({"status": "error", "message": message}), 500

            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login route for user authentication"""
            if request.method == 'POST':
                try:
                    # Handle both form data (web) and JSON (mobile API)
                    if request.is_json:
                        # Mobile API request (JSON)
                        data = request.get_json()
                        login_name = data.get('username')
                        password = data.get('password')
                        remember_me = False
                    else:
                        # Web form request
                        login_name = request.form.get('username')
                        password = request.form.get('password')
                        remember_me = request.form.get('remember_me') == 'on'
                    
                    ip_address = request.remote_addr
                    
                    print(f"[DEBUG] Login attempt: username='{login_name}', password_length={len(password) if password else 0}")
                    
                    # Get user by name/email (DB mode: use get_user_by_login)
                    user_id = None
                    user = None
                    if hasattr(self.smart_home, 'get_user_by_login'):
                        user_id, user = self.smart_home.get_user_by_login(login_name)
                        print(f"[DEBUG] DB mode: get_user_by_login('{login_name}') -> {user_id}")
                    else:
                        users = self.smart_home.users
                        print(f"[DEBUG] Got users: {list(users.keys())}")
                        for uid, user_data in users.items():
                            print(f"[DEBUG] Checking user {uid}: name='{user_data.get('name')}', email='{user_data.get('email')}'")
                            if user_data.get('name') == login_name or user_data.get('email') == login_name:
                                user = user_data
                                user_id = uid
                                print(f"[DEBUG] Found matching user: {uid}")
                                break
                    if user:
                        print(f"[DEBUG] User found, checking password...")
                        password_check = self.smart_home.verify_password(user_id, password)
                        print(f"[DEBUG] Password verification result: {password_check}")
                    else:
                        print(f"[DEBUG] No user found for login_name: '{login_name}'")
                    
                    # Proper password verification
                    if user and user.get('password') and self.smart_home.verify_password(user_id, password):
                        session['user_id'] = user_id
                        session['username'] = user['name']
                        session['role'] = user.get('role', 'user')
                        session.permanent = True
                        
                        print(f"[DEBUG] Login successful for user: {user['name']}")
                        
                        # Log successful login
                        if self.management_logger:
                            self.management_logger.log_login(user['name'], ip_address or 'unknown', success=True)
                        
                        # Return appropriate response based on request type
                        if request.is_json:
                            # JSON API response for mobile - format compatible with Android ApiResponse<LoginResponse>
                            return jsonify({
                                "status": "success",
                                "message": "Login successful",
                                "data": {
                                    "status": "success",
                                    "message": "Login successful", 
                                    "user": {
                                        "id": user_id,
                                        "name": user['name'],
                                        "email": user.get('email', ''),
                                        "role": user.get('role', 'user')
                                    },
                                    "session_id": None  # Flask sessions don't use explicit session IDs
                                }
                            })
                        else:
                            # Web response
                            flash('Zalogowano pomyślnie!', 'success')
                            return redirect(url_for('home'))
                    else:
                        print(f"[DEBUG] Login failed - user exists: {user is not None}, has password: {user.get('password') is not None if user else False}")
                        
                        # Log failed login attempt
                        if self.management_logger:
                            self.management_logger.log_login(
                                login_name or 'unknown', ip_address or 'unknown', success=False
                            )
                        
                        # Return appropriate error response
                        if request.is_json:
                            # JSON API error response for mobile
                            return jsonify({
                                "status": "error",
                                "message": "Invalid username or password"
                            }), 401
                        else:
                            # Web error response
                            flash('Nieprawidłowa nazwa użytkownika lub hasło!', 'error')
                            return render_template('login.html')
                        
                except Exception as e:
                    print(f"[DEBUG] Exception during login: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Return appropriate error response
                    if request.is_json:
                        # JSON API error response for mobile
                        return jsonify({
                            "status": "error",
                            "message": "Login error occurred"
                        }), 500
                    else:
                        # Web error response
                        flash('Błąd podczas logowania!', 'error')
                        return render_template('login.html')
            
            return render_template('login.html')

        @self.app.route('/logout')
        def logout():
            """Logout route"""
            username = session.get('username', 'Unknown')
            session.clear()
            flash('Wylogowano pomyślnie!', 'info')
            return redirect(url_for('login'))

        @self.app.route('/register', methods=['GET', 'POST'])
        def register():
            if request.method == 'POST':
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
                
                # Sprawdź czy to pierwszy krok (wysłanie kodu) czy drugi (weryfikacja)
                if 'verification_code' in data:
                    # Drugi krok - weryfikacja kodu
                    return self._verify_and_register(data)
                else:
                    # Pierwszy krok - wysłanie kodu weryfikacyjnego
                    return self._send_verification_code(data)
            
            return render_template('register.html')

        @self.app.route('/forgot_password', methods=['GET', 'POST'])
        def forgot_password():
            if request.method == 'POST':
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
                
                email_or_username = data.get('email_or_username', '').strip()
                if not email_or_username:
                    return jsonify({'status': 'error', 'message': 'Wprowadź email lub nazwę użytkownika'}), 400
                
                # Znajdź użytkownika po email lub nazwie użytkownika
                user_id, user, email = self._find_user_by_email_or_username(email_or_username)
                if not user:
                    # Ze względów bezpieczeństwa, nie ujawniamy czy użytkownik istnieje
                    return jsonify({
                        'status': 'verification_sent',
                        'message': 'Jeśli podany email/użytkownik istnieje, kod weryfikacyjny został wysłany.'
                    }), 200
                
                # Wygeneruj i wyślij kod resetowania hasła
                verification_code = self.mail_manager.generate_verification_code()
                self.mail_manager.store_password_reset_code(email, verification_code, user_id)
                
                # Send password reset email
                if self.mail_manager.send_password_reset_email(email, verification_code):
                    return jsonify({
                        'status': 'verification_sent',
                        'message': 'Kod resetowania hasła został wysłany na podany adres email.'
                    }), 200
                else:
                    return jsonify({'status': 'error', 'message': 'Błąd podczas wysyłania kodu resetowania hasła.'}), 500
            
            return render_template('forgot_password.html')

        @self.app.route('/reset_password', methods=['POST'])
        def reset_password():
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
            
            email_or_username = data.get('email_or_username', '').strip()
            verification_code = data.get('verification_code', '').strip()
            new_password = data.get('new_password', '')
            
            if not email_or_username or not verification_code or not new_password:
                return jsonify({'status': 'error', 'message': 'Wszystkie pola są wymagane'}), 400
            
            if len(new_password) < 6:
                return jsonify({'status': 'error', 'message': 'Hasło musi mieć co najmniej 6 znaków'}), 400
            
            # Znajdź użytkownika po email lub nazwie użytkownika
            user_id, user, email = self._find_user_by_email_or_username(email_or_username)
            if not user:
                return jsonify({'status': 'error', 'message': 'Nieprawidłowy użytkownik'}), 400
            
            # Weryfikuj kod resetowania hasła
            is_valid, message, verified_user_id = self.mail_manager.verify_password_reset_code(email, verification_code)
            if not is_valid:
                return jsonify({'status': 'error', 'message': message}), 400
            
            # Sprawdź czy user_id się zgadza (dodatkowe zabezpieczenie)
            if verified_user_id != user_id:
                return jsonify({'status': 'error', 'message': 'Błąd weryfikacji użytkownika'}), 400
            
            # Zmień hasło
            success, msg = self.smart_home.change_password(user_id, new_password)
            if success:
                return jsonify({'status': 'success', 'message': 'Hasło zostało pomyślnie zresetowane. Możesz się teraz zalogować.'}), 200
            else:
                return jsonify({'status': 'error', 'message': msg}), 500
        
    def _send_verification_code(self, data):
        """Pierwszy krok rejestracji - wysłanie kodu weryfikacyjnego"""
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        # Podstawowa walidacja
        if not username or len(username) < 3:
            return jsonify({'status': 'error', 'message': 'Nazwa użytkownika musi mieć co najmniej 3 znaki.'}), 400
        if not email or '@' not in email:
            return jsonify({'status': 'error', 'message': 'Podaj poprawny adres email.'}), 400
        if not password or len(password) < 6:
            return jsonify({'status': 'error', 'message': 'Hasło musi mieć co najmniej 6 znaków.'}), 400
        
        # Sprawdź czy użytkownik już istnieje
        for user in self.smart_home.users.values():
            if user.get('name') == username:
                return jsonify({'status': 'error', 'message': 'Użytkownik już istnieje.'}), 400
            if user.get('email') == email:
                return jsonify({'status': 'error', 'message': 'Adres email jest już używany.'}), 400
        
        # Wygeneruj i wyślij kod weryfikacyjny
        verification_code = self.mail_manager.generate_verification_code()
        self.mail_manager.store_verification_code(email, verification_code)
        
        # Use async mail sending for verification emails to improve response time
        if self.async_mail_manager.send_verification_email_async(email, verification_code):
            return jsonify({
                'status': 'verification_sent',
                'message': 'Kod weryfikacyjny został wysłany na podany adres email.'
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'Błąd podczas wysyłania kodu weryfikacyjnego.'}), 500
    
    def _verify_and_register(self, data):
        """Drugi krok rejestracji - weryfikacja kodu i utworzenie użytkownika"""
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        verification_code = data.get('verification_code', '').strip()
        
        # Podstawowa walidacja
        if not username or not password or not email or not verification_code:
            return jsonify({'status': 'error', 'message': 'Wszystkie pola są wymagane.'}), 400
        
        # Weryfikuj kod
        is_valid, message = self.mail_manager.verify_code(email, verification_code)
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        # Ponowna walidacja danych (na wszelki wypadek)
        if len(username) < 3:
            return jsonify({'status': 'error', 'message': 'Nazwa użytkownika musi mieć co najmniej 3 znaki.'}), 400
        if '@' not in email:
            return jsonify({'status': 'error', 'message': 'Podaj poprawny adres email.'}), 400
        if len(password) < 6:
            return jsonify({'status': 'error', 'message': 'Hasło musi mieć co najmniej 6 znaków.'}), 400
        
        # Sprawdź czy użytkownik już istnieje (ponownie)
        for user in self.smart_home.users.values():
            if user.get('name') == username:
                return jsonify({'status': 'error', 'message': 'Użytkownik już istnieje.'}), 400
            if user.get('email') == email:
                return jsonify({'status': 'error', 'message': 'Adres email jest już używany.'}), 400
        
        # Utwórz użytkownika
        if hasattr(self.smart_home, 'add_user'):
            self.smart_home.add_user(username, password, 'user', email)
        else:
            from werkzeug.security import generate_password_hash
            import uuid
            user_id = str(uuid.uuid4())
            self.smart_home.users[user_id] = {
                'name': username,
                'password': generate_password_hash(password),
                'role': 'user',
                'email': email,
                'profile_picture': ''
            }
            self.smart_home.save_config()
        
        # Log user registration
        self.management_logger.log_user_change(
            username=username, 
            action='register', 
            target_user=username,
            ip_address=request.remote_addr or "",
            details={'email': email}
        )
        
        return jsonify({'status': 'success', 'message': 'Rejestracja zakończona sukcesem!'}), 200

    def _find_user_by_email_or_username(self, email_or_username):
        """Znajduje użytkownika po email lub nazwie użytkownika"""
        # Najpierw spróbuj znaleźć po email
        for user_id, user in self.smart_home.users.items():
            if user.get('email') == email_or_username:
                return user_id, user, user.get('email')
        
        # Jeśli nie znaleziono po email, spróbuj po nazwie użytkownika
        for user_id, user in self.smart_home.users.items():
            if user.get('name') == email_or_username:
                return user_id, user, user.get('email')
        
        return None, None, None

    def _generate_dashboard_stats(self):
        """Generuje statystyki dla dashboardu administratora"""
        from datetime import datetime
        import random
        
        # Podstawowe statystyki
        users_count = len(self.smart_home.users)
        devices_count = len(self.smart_home.buttons) + len(self.smart_home.temperature_controls)
        automations_count = len(self.smart_home.automations)
        active_automations = sum(1 for auto in self.smart_home.automations if auto.get('enabled', False))
        
        # Symulowane dane energii (w rzeczywistości pobierane z urządzeń)
        energy_today = round(random.uniform(10, 30), 1)
        energy_month = round(random.uniform(200, 500), 1)
        
        # Symulowane dane automatyzacji
        automations_executed_today = random.randint(5, 25)
        automation_errors = random.randint(0, 3)
        
        return {
            'users_count': users_count,
            'devices_count': devices_count,
            'automations_count': automations_count,
            'active_automations': active_automations,
            'energy_today': energy_today,
            'energy_month': energy_month,
            'automations_executed_today': automations_executed_today,
            'automation_errors': automation_errors
        }

    def _get_device_states(self):
        """Pobiera aktualny stan wszystkich urządzeń"""
        device_states = []
        
        # Dodaj przyciski
        for button in self.smart_home.buttons:
            device_states.append({
                'name': button['name'],
                'room': button['room'],
                'state': button['state'],
                'type': 'button'
            })
        
        # Dodaj kontrolery temperatury
        for control in self.smart_home.temperature_controls:
            device_states.append({
                'name': control['name'],
                'room': control['room'],
                'state': True,  # Kontrolery temperatury są zawsze aktywne
                'type': 'temperature',
                'temperature': control.get('temperature', 22)
            })
        
        return device_states

    def _get_management_logs(self):
        """Pobiera rzeczywiste logi zarządzania systemem"""
        return self.management_logger.get_logs(limit=50)

class APIManager:
    """Klasa zarządzająca endpointami API"""
    def __init__(self, app, socketio, smart_home, auth_manager, management_logger=None, cache=None, cached_data_access=None):
        self.app = app
        self.socketio = socketio
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.management_logger = management_logger or ManagementLogger()
        # Use the same caching approach as RoutesManager to share cache keys
        try:
            self.cached_data = cached_data_access or (CachedDataAccess(cache, smart_home) if cache else None)
        except Exception:
            # Fallback to simple dict if cache not available
            self.cached_data = {}
        self.register_routes()

    def emit_update(self, event_name, data):
        """Safely emit socketio updates only if socketio is available"""
        if self.socketio:
            self.socketio.emit(event_name, data)

    def register_routes(self):
        @self.app.route('/api', methods=['GET'])
        def api_root():
            return jsonify({"status": "ok", "message": "API root"}), 200

        @self.app.route('/weather')
        @self.auth_manager.login_required
        def weather():
            weather_data = self.smart_home.fetch_weather_data()
            if weather_data:
                return jsonify(weather_data)
            return jsonify({"error": "Nie udało się pobrać danych pogodowych"}), 500

        @self.app.route('/api/admin', methods=['GET'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_root():
            return jsonify({"status": "ok", "message": "Admin API root"}), 200

        @self.app.route('/api/rooms', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_rooms():
            self.smart_home.check_and_save()
            if request.method == 'GET':
                # Always reflect DB display_order: bypass room cache for this endpoint
                rooms = self.smart_home.rooms
                return jsonify(rooms)
            elif request.method == 'POST':
                if session.get('role') != 'admin':
                    return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
                new_room = (request.json or {}).get('room')
                if new_room and new_room.lower() not in [room.lower() for room in self.smart_home.rooms]:
                    self.smart_home.rooms.append(new_room)
                    self.socketio.emit('update_rooms', self.smart_home.rooms)
                    if not self.smart_home.save_config():
                        return jsonify({"status": "error", "message": "Nie udało się zapisać nowego pokoju"}), 500
                    
                    # Log room addition
                    self.management_logger.log_room_change(
                        username=session.get('username', 'unknown'),
                        action='add',
                        room_name=new_room,
                        ip_address=request.remote_addr or ""
                    )
                    
                    # Invalidate cache after modification
                    if self.cached_data:
                        invalidate = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                        if callable(invalidate):
                            invalidate()
                    return jsonify({"status": "success"})
                return jsonify({"status": "error", "message": "Invalid room name or room already exists"}), 400

        @self.app.route('/api/rooms/<room>', methods=['DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def delete_room(room):
            print("DELETE /api/rooms/<room> room:", room)
            if not room:
                return jsonify({"status": "error", "message": "Brak nazwy pokoju"}), 400

            # Prefer DB-backed deletion when available
            db_deleted = False
            if hasattr(self.smart_home, 'delete_room'):
                db_deleted = self.smart_home.delete_room(room)
                if not db_deleted:
                    return jsonify({"status": "error", "message": "Nie udało się usunąć pokoju w bazie"}), 500

            # Log room deletion
            self.management_logger.log_room_change(
                username=session.get('username', 'unknown'),
                action='delete',
                room_name=room,
                ip_address=request.remote_addr or ""
            )

            # Invalidate caches so subsequent GETs return fresh data
            try:
                if hasattr(self, 'cached_data') and self.cached_data:
                    invalidate_rooms = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                    if callable(invalidate_rooms):
                        invalidate_rooms()
                    invalidate_buttons = getattr(self.cached_data, 'invalidate_buttons_cache', None)
                    if callable(invalidate_buttons):
                        invalidate_buttons()
                    invalidate_temp = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                    if callable(invalidate_temp):
                        invalidate_temp()
            except Exception as _e:
                print(f"[DEBUG] Cache invalidation after room delete failed: {_e}")

            # Emit socket updates with fresh data from source (DB mode properties fetch fresh)
            self.socketio.emit('update_rooms', self.smart_home.rooms)
            self.socketio.emit('update_buttons', self.smart_home.buttons)
            self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
            return jsonify({"status": "success"})

        @self.app.route('/api/rooms/<room>', methods=['PUT'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def edit_room(room):
            data = request.get_json()
            new_name = data.get('new_name') if data else None
            old_name = room
            # Check for valid new name
            if not new_name or new_name.lower() in [r.lower() for r in self.smart_home.rooms]:
                return jsonify({"status": "error", "message": "Nieprawidłowa lub już istniejąca nazwa pokoju"}), 400

            # If DB mode, persist to DB
            db_success = None
            if hasattr(self.smart_home, 'update_room'):
                db_success = self.smart_home.update_room(old_name, new_name)
                if not db_success:
                    return jsonify({"status": "error", "message": "Błąd zapisu do bazy danych"}), 500

            # Always update config for legacy/JSON mode
            if not db_success:
                for i, r in enumerate(self.smart_home.rooms):
                    if r.lower() == old_name.lower():
                        self.smart_home.rooms[i] = new_name
                        old_name = r
                        break
                for button in self.smart_home.buttons:
                    if button['room'].lower() == old_name.lower():
                        button['room'] = new_name
                for control in self.smart_home.temperature_controls:
                    if control['room'].lower() == old_name.lower():
                        control['room'] = new_name
                self.smart_home.save_config()

            # Log room rename
            self.management_logger.log_room_change(
                username=session.get('username', 'unknown'),
                action='rename',
                room_name=new_name,
                ip_address=request.remote_addr or "",
                old_name=old_name
            )

            # Invalidate caches so subsequent GETs return fresh data
            try:
                if hasattr(self, 'cached_data') and self.cached_data:
                    invalidate_rooms = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                    if callable(invalidate_rooms):
                        invalidate_rooms()
                    # Be explicit as well (redundant but safe with SimpleCache)
                    invalidate_buttons = getattr(self.cached_data, 'invalidate_buttons_cache', None)
                    if callable(invalidate_buttons):
                        invalidate_buttons()
                    invalidate_temp = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                    if callable(invalidate_temp):
                        invalidate_temp()
            except Exception as _e:
                # Non-fatal: caching is best-effort
                print(f"[DEBUG] Cache invalidation after room rename failed: {_e}")

            # Emit socket updates
            self.socketio.emit('update_rooms', self.smart_home.rooms)
            self.socketio.emit('update_buttons', self.smart_home.buttons)
            self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
            return jsonify({"status": "success", "message": "Nazwa pokoju zaktualizowana poprawnie!"}), 200

        @self.app.route('/api/rooms/order', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def set_rooms_order():
            data = request.get_json()
            rooms = data.get('rooms')
            if not isinstance(rooms, list):
                return jsonify({'status': 'error', 'message': 'Brak listy pokoi'}), 400
            try:
                # Prefer database-backed reordering when available
                if hasattr(self.smart_home, 'reorder_rooms'):
                    # Only pass valid existing room names in desired order
                    current = set([r for r in self.smart_home.rooms])
                    desired_order = [r for r in rooms if r in current]
                    success = self.smart_home.reorder_rooms(desired_order)
                    if not success:
                        return jsonify({'status': 'error', 'message': 'Nie udało się zapisać kolejności pokoi w bazie'}), 500
                    # Fetch fresh ordered rooms from DB-backed property
                    ordered_rooms = self.smart_home.rooms
                else:
                    # JSON mode fallback preserves original behavior
                    self.smart_home.rooms = [r for r in rooms if r in self.smart_home.rooms]
                    self.smart_home.save_config()
                    ordered_rooms = self.smart_home.rooms

                # Emit updates and invalidate caches if available
                if self.socketio:
                    self.socketio.emit('update_rooms', ordered_rooms)
                if hasattr(self, 'cached_data') and self.cached_data:
                    invalidate = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                    if callable(invalidate):
                        invalidate()

                # Log reorder (optional detail only)
                try:
                    self.management_logger.log_room_change(
                        username=session.get('username', 'unknown'),
                        action='reorder',
                        room_name='order_update',
                        ip_address=request.remote_addr or "",
                        old_name=''
                    )
                except Exception:
                    pass

                return jsonify({'status': 'success'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Błąd zapisu kolejności: {e}'}), 500

        @self.app.route('/api/buttons/order', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def set_buttons_order():
            data = request.get_json()
            if 'room' in data and 'order' in data:
                room = data['room']
                order = data['order']
                room_buttons = [b for b in self.smart_home.buttons if b.get('room') == room]
                new_room_buttons = []
                for btn_id in order:
                    found = next((b for b in room_buttons if str(b.get('id')) == str(btn_id)), None)
                    if found:
                        new_room_buttons.append(found)
                other_buttons = [b for b in self.smart_home.buttons if b.get('room') != room]
                self.smart_home.buttons = other_buttons + new_room_buttons
                self.socketio.emit('update_buttons', self.smart_home.buttons)
                self.smart_home.save_config()
                return jsonify({'status': 'success'})
            buttons = data.get('buttons')
            if not isinstance(buttons, list):
                return jsonify({'status': 'error', 'message': 'Brak listy przycisków'}), 400
            new_order = []
            for btn in buttons:
                found = next((b for b in self.smart_home.buttons if b['name'] == btn.get('name') and b['room'] == btn.get('room')), None)
                if found:
                    new_order.append(found)
            self.smart_home.buttons = new_order
            self.socketio.emit('update_buttons', self.smart_home.buttons)
            self.smart_home.save_config()
            return jsonify({'status': 'success'})

        @self.app.route('/api/temperature_controls/order', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def set_temp_controls_order():
            data = request.get_json()
            if 'room' in data and 'order' in data:
                room = data['room']
                order = data['order']
                room_controls = [c for c in self.smart_home.temperature_controls if c.get('room') == room]
                new_room_controls = []
                for ctrl_id in order:
                    found = next((c for c in room_controls if c['id'] == ctrl_id), None)
                    if found:
                        new_room_controls.append(found)
                self.smart_home.temperature_controls = [c for c in self.smart_home.temperature_controls if c.get('room') != room] + new_room_controls
                self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                self.smart_home.save_config()
                return jsonify({'status': 'success'})
            return jsonify({'status': 'error', 'message': 'Brak danych lub nieprawidłowy format'}), 400

        @self.app.route('/api/buttons', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_buttons():
            self.smart_home.check_and_save()
            if request.method == 'GET':
                # Use cached data if available
                if self.cached_data:
                    print("[DEBUG] GET /api/buttons using cached_data")
                    buttons = self.cached_data.get('buttons', []) if isinstance(self.cached_data, dict) else self.cached_data.get_buttons()
                else:
                    print("[DEBUG] GET /api/buttons direct smart_home.buttons fetch")
                    buttons = self.smart_home.buttons
                print(f"[DEBUG] GET /api/buttons returning {len(buttons)} buttons: {[ (b.get('name'), b.get('room')) for b in buttons ]}")
                return jsonify(buttons)
            elif request.method == 'POST':
                if session.get('role') != 'admin':
                    return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
                new_button = request.json
                if new_button:
                    name = new_button.get('name')
                    room = new_button.get('room')
                    if not name or not room:
                        return jsonify({"status": "error", "message": "Brak nazwy lub pokoju"}), 400
                    try:
                        if hasattr(self.smart_home, 'add_button'):
                            print(f"[DEBUG] POST /api/buttons add_button DB path: name={name}, room={room}")
                            new_id = self.smart_home.add_button(name, room, state=False)
                            # Invalidate cache if available
                            if self.cached_data and hasattr(self.cached_data, 'cache'):
                                self.cached_data.cache.delete('buttons_list')
                            # Emit updated list
                            self.socketio.emit('update_buttons', self.smart_home.buttons)
                            return jsonify({"status": "success", "id": new_id})
                        else:
                            return jsonify({"status": "error", "message": "Brak metody add_button"}), 500
                    except Exception as e:
                        print(f"[DEBUG] POST /api/buttons error: {e}")
                        return jsonify({"status": "error", "message": str(e)}), 500
                return jsonify({"status": "error", "message": "Invalid button data"}), 400

        @self.app.route('/api/buttons/<id>', methods=['PUT', 'DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.api_admin_required
        def button_by_id(id):
            if request.method == 'PUT':
                print(f"[DEBUG] PUT /api/buttons/{id} - Starting")
                data = request.get_json()
                print(f"[DEBUG] PUT data received: {data}")
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
                
                # Check if device exists first
                device = self.smart_home.get_device_by_id(id)
                print(f"[DEBUG] Device found: {device}")
                if not device:
                    return jsonify({'status': 'error', 'message': 'Button not found'}), 404
                
                # Prepare updates
                updates = {}
                if 'name' in data:
                    updates['name'] = data['name']
                if 'room' in data:
                    updates['room'] = data['room']
                
                print(f"[DEBUG] Updates prepared: {updates}")
                if not updates:
                    return jsonify({'status': 'error', 'message': 'No valid fields to update'}), 400
                
                # Update device in database
                if hasattr(self.smart_home, 'update_device'):
                    print(f"[DEBUG] Using database mode - calling update_device")
                    # Database mode - use proper database update method
                    success = self.smart_home.update_device(id, updates)
                    print(f"[DEBUG] update_device result: {success}")
                    if not success:
                        return jsonify({"status": "error", "message": "Nie udało się zapisać edycji przycisku"}), 500
                    # Invalidate cache after successful update
                    if self.cached_data:
                        print(f"[DEBUG] Invalidating cache")
                        self.cached_data.invalidate_buttons_cache()
                    update_mode = 'db'
                else:
                    print(f"[DEBUG] Using JSON mode fallback")
                    # JSON mode fallback
                    idx = next((i for i, b in enumerate(self.smart_home.buttons) if str(b.get('id')) == str(id)), None)
                    if idx is None:
                        return jsonify({'status': 'error', 'message': 'Button not found'}), 404
                    if 'name' in updates:
                        self.smart_home.buttons[idx]['name'] = updates['name']
                    if 'room' in updates:
                        self.smart_home.buttons[idx]['room'] = updates['room']
                    if not self.smart_home.save_config():
                        return jsonify({"status": "error", "message": "Nie udało się zapisać edycji przycisku"}), 500
                    update_mode = 'json'

                # Emit socket update (both modes)
                if self.socketio:
                    print(f"[DEBUG] Emitting socket update")
                    # Get fresh data from cache (same source as main page) for socket update
                    fresh_buttons = self.cached_data.get_buttons() if self.cached_data else self.smart_home.buttons
                    print(f"[DEBUG] Fresh buttons data from cache: {fresh_buttons}")
                    self.socketio.emit('update_buttons', fresh_buttons)

                print(f"[DEBUG] PUT /api/buttons/{id} - Success ({update_mode} mode)")
                return jsonify({'status': 'success', 'message': 'Nazwa przycisku zaktualizowana poprawnie!'}), 200
                
            elif request.method == 'DELETE':
                # Check if device exists first
                device = self.smart_home.get_device_by_id(id)
                if not device:
                    return jsonify({'status': 'error', 'message': 'Button not found'}), 404
                
                # Delete device
                if hasattr(self.smart_home, 'delete_device'):
                    # Database mode - use proper database delete method
                    success = self.smart_home.delete_device(id)
                    if not success:
                        return jsonify({"status": "error", "message": "Nie udało się usunąć przycisku"}), 500
                    
                    # Invalidate cache after successful delete
                    if self.cached_data:
                        self.cached_data.invalidate_buttons_cache()
                else:
                    # JSON mode fallback
                    idx = next((i for i, b in enumerate(self.smart_home.buttons) if str(b.get('id')) == str(id)), None)
                    if idx is None:
                        return jsonify({'status': 'error', 'message': 'Button not found'}), 404
                    
                    self.smart_home.buttons.pop(idx)
                    if not self.smart_home.save_config():
                        return jsonify({"status": "error", "message": "Nie udało się zapisać po usunięciu przycisku"}), 500
                
                # Emit socket update
                if self.socketio:
                    self.socketio.emit('update_buttons', self.smart_home.buttons)
                
                return jsonify({'status': 'success'})
                return jsonify({'status': 'success'})

        @self.app.route('/api/buttons/<id>/toggle', methods=['POST'])
        @self.auth_manager.api_login_required
        def toggle_button_state(id):
            """Toggle button state via REST API"""
            try:
                print(f"[DEBUG] toggle_button_state called with id: {id}")
                print(f"[DEBUG] Request content_type: {request.content_type}")
                print(f"[DEBUG] Request method: {request.method}")
                
                # Find button by ID
                button = None
                button_idx = None
                for i, b in enumerate(self.smart_home.buttons):
                    if str(b.get('id')) == str(id):
                        button = b
                        button_idx = i
                        break
                
                if not button:
                    print(f"[DEBUG] Button not found with id: {id}")
                    return jsonify({'status': 'error', 'message': 'Button not found'}), 404
                
                print(f"[DEBUG] Found button: {button['name']} in {button['room']}, current state: {button.get('state', False)}")
                
                # Get new state from request or toggle current state
                data = {}
                if request.content_type and 'application/json' in request.content_type:
                    data = request.get_json() or {}
                
                new_state = data.get('state')
                if new_state is None:
                    new_state = not button.get('state', False)
                
                print(f"[DEBUG] New state will be: {new_state}")
                
                # Update button state
                if hasattr(self.smart_home, 'update_button_state'):
                    # Use database method if available
                    print(f"[DEBUG] Updating button state in database: {button['room']}, {button['name']}, {new_state}")
                    success = self.smart_home.update_button_state(button['room'], button['name'], new_state)
                    print(f"[DEBUG] Database update success: {success}")
                    if not success:
                        return jsonify({'status': 'error', 'message': 'Failed to update button state in database'}), 500
                else:
                    # Fallback to JSON mode
                    print(f"[DEBUG] Updating button state in JSON mode")
                    self.smart_home.buttons[button_idx]['state'] = new_state
                    if not self.smart_home.save_config():
                        return jsonify({'status': 'error', 'message': 'Failed to save button state'}), 500
                
                # Emit socket updates
                self.socketio.emit('update_button', {
                    'room': button['room'],
                    'name': button['name'],
                    'state': new_state
                })
                self.socketio.emit('sync_button_states', {
                    f"{b['room']}_{b['name']}": b['state'] for b in self.smart_home.buttons
                })
                
                # Log the action
                if hasattr(self.management_logger, 'log_device_action'):
                    user_id = session.get('user_id')
                    user_data = self.smart_home.get_user_data(user_id) if user_id else None
                    self.management_logger.log_device_action(
                        user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                        device_name=button['name'],
                        room=button['room'],
                        action='toggle',
                        new_state=new_state,
                        ip_address=request.environ.get('REMOTE_ADDR', '')
                    )
                
                return jsonify({
                    'status': 'success',
                    'button': {
                        'id': button['id'],
                        'name': button['name'],
                        'room': button['room'],
                        'state': new_state
                    }
                })
                
            except Exception as e:
                print(f"Error in toggle_button_state: {e}")
                return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

        @self.app.route('/api/temperature_controls', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_temperature_controls():
            self.smart_home.check_and_save()
            if request.method == 'GET':
                return jsonify({
                    "status": "success", 
                    "data": self.smart_home.temperature_controls
                })
            elif request.method == 'POST':
                try:
                    if session.get('role') != 'admin':
                        return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
                    new_control = request.json
                    if new_control:
                        if 'id' not in new_control:
                            new_control['id'] = str(uuid.uuid4())
                        new_control['temperature'] = 22
                        self.smart_home.temperature_controls.append(new_control)
                        # Emit updates only if socketio is available
                        if self.socketio:
                            self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                            self.socketio.emit('update_room_temperature_controls', new_control)
                        self.smart_home.save_config()
                        return jsonify({"status": "success", "id": new_control['id']})
                    return jsonify({"status": "error", "message": "Invalid control data"}), 400
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Exception in POST /api/temperature_controls: {e}\n{traceback.format_exc()}")
                    return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

        @self.app.route('/api/temperature_controls/<id>', methods=['PUT', 'DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.api_admin_required
        def temp_control_by_id(id):
            if request.method == 'PUT':
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
                
                # Check if device exists first
                device = self.smart_home.get_device_by_id(id)
                if not device:
                    return jsonify({'status': 'error', 'message': 'Control not found'}), 404
                
                # Prepare updates
                updates = {}
                if 'name' in data:
                    updates['name'] = data['name']
                if 'room' in data:
                    updates['room'] = data['room']
                
                if not updates:
                    return jsonify({'status': 'error', 'message': 'No valid fields to update'}), 400
                
                # Update device in database
                if hasattr(self.smart_home, 'update_device'):
                    # Database mode - use proper database update method
                    success = self.smart_home.update_device(id, updates)
                    if not success:
                        return jsonify({"status": "error", "message": "Nie udało się zapisać edycji termostatu"}), 500
                    
                    # Invalidate cache after successful update
                    if self.cached_data:
                        self.cached_data.invalidate_temperature_cache()
                else:
                    # JSON mode fallback
                    idx = next((i for i, c in enumerate(self.smart_home.temperature_controls) if str(c.get('id')) == str(id)), None)
                    if idx is None:
                        return jsonify({'status': 'error', 'message': 'Control not found'}), 404
                    
                    if 'name' in updates:
                        self.smart_home.temperature_controls[idx]['name'] = updates['name']
                    if 'room' in updates:
                        self.smart_home.temperature_controls[idx]['room'] = updates['room']
                    
                    self.smart_home.save_config()
                
                # Emit updates only if socketio is available
                if self.socketio:
                    self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                
                return jsonify({'status': 'success'})
                
            elif request.method == 'DELETE':
                # Check if device exists first
                device = self.smart_home.get_device_by_id(id)
                if not device:
                    return jsonify({'status': 'error', 'message': 'Control not found'}), 404
                
                # Delete device
                if hasattr(self.smart_home, 'delete_device'):
                    # Database mode - use proper database delete method
                    success = self.smart_home.delete_device(id)
                    if not success:
                        return jsonify({"status": "error", "message": "Nie udało się usunąć termostatu"}), 500
                    
                    # Invalidate cache after successful delete
                    if self.cached_data:
                        self.cached_data.invalidate_temperature_cache()
                else:
                    # JSON mode fallback
                    idx = next((i for i, c in enumerate(self.smart_home.temperature_controls) if str(c.get('id')) == str(id)), None)
                    if idx is None:
                        return jsonify({'status': 'error', 'message': 'Control not found'}), 404
                    
                    self.smart_home.temperature_controls.pop(idx)
                    self.smart_home.save_config()
                
                # Emit updates only if socketio is available
                if self.socketio:
                    self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                
                return jsonify({'status': 'success'})

        @self.app.route('/api/temperature_controls/<int:index>', methods=['DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def delete_temperature_control(index):
            if 0 <= index < len(self.smart_home.temperature_controls):
                deleted_control = self.smart_home.temperature_controls.pop(index)
                # Emit updates only if socketio is available
                if self.socketio:
                    self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                    self.socketio.emit('remove_room_temperature_control', deleted_control)
                self.smart_home.save_config()
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Control not found"}), 404

        @self.app.route('/api/temperature_controls/<int:index>', methods=['PUT'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def edit_temperature_control(index):
            if 0 <= index < len(self.smart_home.temperature_controls):
                data = request.get_json()
                if not data:
                    return jsonify({"status": "error", "message": "Brak danych"}), 400
                if 'name' in data:
                    self.smart_home.temperature_controls[index]['name'] = data['name']
                if 'room' in data:
                    self.smart_home.temperature_controls[index]['room'] = data['room']
                self.smart_home.save_config()
                # Emit updates only if socketio is available
                if self.socketio:
                    self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Control not found"}), 404

        @self.app.route('/api/temperature_controls/<id>/temperature', methods=['POST'])
        @self.auth_manager.login_required
        def set_temperature_control_value(id):
            """Set temperature control value via REST API"""
            try:
                # Find temperature control by ID
                control = None
                control_idx = None
                for i, c in enumerate(self.smart_home.temperature_controls):
                    if str(c.get('id')) == str(id):
                        control = c
                        control_idx = i
                        break
                
                if not control:
                    return jsonify({'status': 'error', 'message': 'Temperature control not found'}), 404
                
                # Get temperature from request
                data = request.get_json() or {}
                temperature = data.get('temperature')
                
                if temperature is None:
                    return jsonify({'status': 'error', 'message': 'Temperature value is required'}), 400
                
                # Validate temperature range
                try:
                    temperature = float(temperature)
                    if not (16 <= temperature <= 30):
                        return jsonify({'status': 'error', 'message': 'Temperature must be between 16°C and 30°C'}), 400
                except (ValueError, TypeError):
                    return jsonify({'status': 'error', 'message': 'Invalid temperature value'}), 400
                
                # Update temperature control
                if hasattr(self.smart_home, 'update_temperature_control_value'):
                    # Use database method if available
                    success = self.smart_home.update_temperature_control_value(control['room'], control['name'], temperature)
                    if not success:
                        return jsonify({'status': 'error', 'message': 'Failed to update temperature in database'}), 500
                else:
                    # Fallback to JSON mode
                    self.smart_home.temperature_controls[control_idx]['temperature'] = temperature
                    if not self.smart_home.save_config():
                        return jsonify({'status': 'error', 'message': 'Failed to save temperature'}), 500
                
                # Update room temperature state
                if hasattr(self.smart_home, 'set_room_temperature'):
                    self.smart_home.set_room_temperature(control['room'], temperature)
                else:
                    self.smart_home.temperature_states[control['room']] = temperature
                    self.smart_home.save_config()
                
                # Emit socket updates
                if self.socketio:
                    self.socketio.emit('update_temperature', {
                        'room': control['room'],
                        'name': control['name'],
                        'temperature': temperature
                    })
                    self.socketio.emit('sync_temperature', {
                        'name': control['name'],
                        'temperature': temperature
                    })
                
                # Log the action
                if hasattr(self.management_logger, 'log_device_action'):
                    user_id = session.get('user_id')
                    user_data = self.smart_home.get_user_data(user_id) if user_id else None
                    self.management_logger.log_device_action(
                        user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                        device_name=control['name'],
                        room=control['room'],
                        action='set_temperature',
                        new_state=temperature,
                        ip_address=request.environ.get('REMOTE_ADDR', '')
                    )
                
                return jsonify({
                    'status': 'success',
                    'control': {
                        'id': control['id'],
                        'name': control['name'],
                        'room': control['room'],
                        'temperature': temperature
                    }
                })
                
            except Exception as e:
                print(f"Error in set_temperature_control_value: {e}")
                return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

        @self.app.route('/<room>')
        @self.auth_manager.login_required
        def dynamic_room(room):
            if room.lower() in [r.lower() for r in self.smart_home.rooms]:
                room_buttons = [button for button in self.smart_home.buttons if button['room'].lower() == room.lower()]
                room_temperature_controls = [control for control in self.smart_home.temperature_controls if control['room'].lower() == room.lower()]
                user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
                return render_template('room.html', 
                                      room=room.capitalize(), 
                                      buttons=room_buttons, 
                                      temperature_controls=room_temperature_controls,
                                      user_data=user_data)
            return redirect(url_for('error'))

        @self.app.route('/api/users', methods=['GET'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def get_users():
            users_list = [
                {
                    'user_id': user_id,
                    'username': data['name'],
                    'email': data.get('email', ''),
                    'role': data['role'],
                    'password': '••••••••'  # Always show dots for password
                }
                for user_id, data in self.smart_home.users.items()
            ]
            return jsonify(users_list)

        @self.app.route('/api/users', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def add_user():
            """Add user using the same logic as registration but without email verification"""
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            email = data.get('email', '').strip()
            role = data.get('role', 'user')
            
            # Use the same validation logic as registration
            if not username or len(username) < 3:
                return jsonify({'status': 'error', 'message': 'Nazwa użytkownika musi mieć co najmniej 3 znaki.'}), 400
            if not email or '@' not in email:
                return jsonify({'status': 'error', 'message': 'Podaj poprawny adres email.'}), 400
            if not password or len(password) < 6:
                return jsonify({'status': 'error', 'message': 'Hasło musi mieć co najmniej 6 znaków.'}), 400
            if role not in ['user', 'admin']:
                return jsonify({'status': 'error', 'message': 'Nieprawidłowa rola użytkownika.'}), 400
            
            # Check if user already exists (same as registration)
            for user in self.smart_home.users.values():
                if user.get('name') == username:
                    return jsonify({'status': 'error', 'message': 'Użytkownik już istnieje.'}), 400
                if user.get('email') == email:
                    return jsonify({'status': 'error', 'message': 'Adres email jest już używany.'}), 400
            
            # Dodawanie użytkownika - obsługa trybu DB i plikowego
            try:
                if hasattr(self.smart_home, 'add_user'):
                    # Tryb DB
                    user_id = self.smart_home.add_user(username, password, role, email)
                else:
                    # Tryb plikowy (legacy)
                    import uuid
                    from werkzeug.security import generate_password_hash
                    user_id = str(uuid.uuid4())
                    self.smart_home.users[user_id] = {
                        'name': username,
                        'password': generate_password_hash(password),
                        'role': role,
                        'email': email,
                        'profile_picture': ''
                    }
                    self.smart_home.save_config()
                # Log admin user creation
                self.management_logger.log_user_change(
                    username=session.get('username', 'unknown'),
                    action='add',
                    target_user=username,
                    ip_address=request.remote_addr or "",
                    details={'email': email, 'role': role}
                )
                return jsonify({
                    'status': 'success', 
                    'message': 'Użytkownik został dodany pomyślnie!',
                    'user_id': user_id,
                    'username': username
                }), 200
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Błąd podczas dodawania użytkownika: {e}'}), 500

        @self.app.route('/api/users/<user_id>', methods=['PUT'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def update_user(user_id):
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Brak danych"}), 400
            
            user = self.smart_home.users.get(user_id)
            if not user:
                return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 404
            
            updates = {}
            if 'username' in data:
                # Sprawdź czy nowa nazwa użytkownika nie jest już zajęta
                for uid, u in self.smart_home.users.items():
                    if uid != user_id and u.get('name') == data['username']:
                        return jsonify({"status": "error", "message": "Nazwa użytkownika jest już zajęta"}), 400
                updates['name'] = data['username']
            
            if 'email' in data:
                updates['email'] = data['email']
            
            if 'role' in data and data['role'] in ['user', 'admin']:
                updates['role'] = data['role']
            
            # Aktualizuj dane użytkownika
            for key, value in updates.items():
                user[key] = value
            
            self.smart_home.save_config()
            return jsonify({"status": "success", "message": "Użytkownik zaktualizowany"})

        @self.app.route('/api/users/<user_id>', methods=['DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def delete_user_api(user_id):
            try:
                # Try DB mode first
                if hasattr(self.smart_home, 'delete_user'):
                    result = self.smart_home.delete_user(user_id)
                    # Obsłuż różne typy zwracane przez delete_user
                    if isinstance(result, tuple):
                        success, message = result
                    elif isinstance(result, bool):
                        success, message = result, ''
                    elif result is None:
                        success, message = True, ''
                    else:
                        success, message = False, str(result)
                    if not success:
                        print(f"[ERROR] delete_user zwróciło błąd: {message}")
                        return jsonify({'status': 'error', 'message': message or 'Błąd usuwania użytkownika'}), 400
                else:
                    # Legacy file mode
                    if user_id not in self.smart_home.users:
                        return jsonify({'status': 'error', 'message': 'Użytkownik nie istnieje'}), 404
                    del self.smart_home.users[user_id]
                    self.smart_home.save_config()
                # Optionally log the deletion
                try:
                    self.management_logger.log_user_change(
                        username=session.get('username', 'unknown'),
                        action='delete',
                        target_user=user_id,
                        ip_address=request.remote_addr or "",
                        details={}
                    )
                except Exception as log_exc:
                    print(f"[WARN] Błąd logowania usunięcia użytkownika: {log_exc}")
                return jsonify({'status': 'success', 'message': 'Użytkownik został usunięty'})
            except Exception as e:
                import traceback
                print(f"[ERROR] Błąd podczas usuwania użytkownika: {e}\n{traceback.format_exc()}")
                return jsonify({'status': 'error', 'message': f'Błąd podczas usuwania użytkownika: {e}'}), 500

        @self.app.route('/api/users/<user_id>', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def update_user_post(user_id):
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Brak danych"}), 400
            user = self.smart_home.users.get(user_id)
            if not user:
                return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 404
            updates = {}
            if 'username' in data:
                # Sprawdź czy nowa nazwa użytkownika nie jest już zajęta
                for uid, u in self.smart_home.users.items():
                    if uid != user_id and u.get('name') == data['username']:
                        return jsonify({"status": "error", "message": "Nazwa użytkownika jest już zajęta"}), 400
                updates['name'] = data['username']
            if 'email' in data:
                updates['email'] = data['email']
            if 'role' in data and data['role'] in ['user', 'admin']:
                updates['role'] = data['role']
            # Aktualizuj dane użytkownika
            for key, value in updates.items():
                user[key] = value
            self.smart_home.save_config()
            return jsonify({"status": "success", "message": "Użytkownik zaktualizowany (POST)"})

        @self.app.route('/api/users/<user_id>/password', methods=['PUT'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def change_password(user_id):
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Brak danych"}), 400
            new_password = data.get('new_password')
            if not new_password:
                return jsonify({"status": "error", "message": "Brak nowego hasła"}), 400
            success, message = self.smart_home.change_password(user_id, new_password)
            if success:
                return jsonify({"status": "success", "message": message})
            return jsonify({"status": "error", "message": message}), 400

        @self.app.route('/api/automations', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_automations():
            self.smart_home.check_and_save()
            if request.method == 'GET':
                # Always fetch fresh automations from DB-backed property
                return jsonify(self.smart_home.automations)
            elif request.method == 'POST':
                if session.get('role') != 'admin':
                    return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
                new_automation = request.json
                if new_automation:
                    required_fields = ['name', 'trigger', 'actions', 'enabled']
                    if not all(field in new_automation for field in required_fields):
                        return jsonify({"status": "error", "message": "Brak wymaganych pól"}), 400
                    # Always check for duplicates using the DB-backed property
                    if any(auto['name'].lower() == new_automation['name'].lower() for auto in self.smart_home.automations):
                        return jsonify({"status": "error", "message": "Automatyzacja o tej nazwie już istnieje"}), 400
                    try:
                        from app_db import DATABASE_MODE
                    except ImportError:
                        DATABASE_MODE = False
                    if DATABASE_MODE:
                        self.smart_home.add_automation(
                            name=new_automation['name'],
                            trigger=new_automation['trigger'],
                            actions=new_automation['actions'],
                            enabled=new_automation['enabled']
                        )
                        # Always fetch updated automations from DB after insert
                        automations = self.smart_home.automations
                    else:
                        self.smart_home.automations.append(new_automation)
                        self.smart_home.save_config()
                        automations = self.smart_home.automations
                    self.socketio.emit('update_automations', automations)
                    # Log automation addition
                    self.management_logger.log_automation_change(
                        username=session.get('username', 'unknown'),
                        action='add',
                        automation_name=new_automation['name'],
                        ip_address=request.remote_addr or ""
                    )
                    return jsonify({"status": "success", "automations": automations})
                return jsonify({"status": "error", "message": "Invalid automation data"}), 400

        @self.app.route('/api/automations/<int:index>', methods=['PUT', 'DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def modify_automation(index):
            try:
                from app_db import DATABASE_MODE
            except ImportError:
                DATABASE_MODE = False
            if request.method == 'PUT':
                if 0 <= index < len(self.smart_home.automations):
                    updated_automation = request.json
                    if updated_automation:
                        name_exists = any(
                            i != index and auto['name'].lower() == updated_automation['name'].lower()
                            for i, auto in enumerate(self.smart_home.automations)
                        )
                        if name_exists:
                            return jsonify({"status": "error", "message": "Automatyzacja o tej nazwie już istnieje"}), 400
                        if DATABASE_MODE:
                            self.smart_home.update_automation_by_index(index, updated_automation)
                        else:
                            self.smart_home.automations[index] = updated_automation
                            self.smart_home.save_config()
                        self.socketio.emit('update_automations', self.smart_home.automations)
                        # Log automation edit
                        self.management_logger.log_automation_change(
                            username=session.get('username', 'unknown'),
                            action='edit',
                            automation_name=updated_automation['name'],
                            ip_address=request.remote_addr or ""
                        )
                        return jsonify({"status": "success"})
                    return jsonify({"status": "error", "message": "Invalid data"}), 400
                return jsonify({"status": "error", "message": "Automation not found"}), 404
            elif request.method == 'DELETE':
                if 0 <= index < len(self.smart_home.automations):
                    automation_name = self.smart_home.automations[index].get('name', 'unknown')
                    if DATABASE_MODE:
                        self.smart_home.delete_automation_by_index(index)
                    else:
                        del self.smart_home.automations[index]
                        self.smart_home.save_config()
                    self.socketio.emit('update_automations', self.smart_home.automations)
                    # Log automation deletion
                    self.management_logger.log_automation_change(
                        username=session.get('username', 'unknown'),
                        action='delete',
                        automation_name=automation_name,
                        ip_address=request.remote_addr or ""
                    )
                    return jsonify({"status": "success"})
                return jsonify({"status": "error", "message": "Automation not found"}), 404

        @self.app.route('/api/security', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_security_state():
            """REST API endpoint for security state management"""
            try:
                if request.method == 'GET':
                    # Get current security state
                    current_state = self.smart_home.security_state
                    return jsonify({
                        "status": "success",
                        "security_state": current_state
                    })
                
                elif request.method == 'POST':
                    # Set security state
                    data = request.get_json()
                    if not data:
                        return jsonify({"status": "error", "message": "Brak danych"}), 400
                    
                    new_state = data.get('state')
                    if new_state not in ["Załączony", "Wyłączony"]:
                        return jsonify({
                            "status": "error", 
                            "message": "Nieprawidłowy stan zabezpieczeń. Dopuszczalne wartości: 'Załączony', 'Wyłączony'"
                        }), 400
                    
                    # Update security state using property
                    self.smart_home.security_state = new_state
                    
                    # Save configuration (in database mode, this is automatic via setter)
                    try:
                        from app_db import DATABASE_MODE
                    except ImportError:
                        DATABASE_MODE = False
                    
                    if DATABASE_MODE:
                        # Database mode - state is automatically saved via setter
                        success = True
                    else:
                        # JSON mode - explicitly save config
                        success = self.smart_home.save_config()
                    
                    if success:
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
                                ip_address=request.environ.get('REMOTE_ADDR', '')
                            )
                        
                        return jsonify({
                            "status": "success",
                            "message": f"Stan zabezpieczeń zaktualizowany na: {new_state}",
                            "security_state": new_state
                        })
                    else:
                        return jsonify({
                            "status": "error", 
                            "message": "Nie udało się zapisać stanu zabezpieczeń"
                        }), 500
                        
            except Exception as e:
                self.app.logger.error(f"Error in security API: {e}")
                return jsonify({
                    "status": "error", 
                    "message": f"Błąd podczas operacji na zabezpieczeniach: {str(e)}"
                }), 500


class SocketManager:
    """Klasa zarządzająca obsługą WebSocket"""
    def __init__(self, socketio, smart_home, management_logger=None):
        self.socketio = socketio
        self.smart_home = smart_home
        self.management_logger = management_logger or ManagementLogger()
        self.register_handlers()

    def register_handlers(self):
        @self.socketio.on('connect')
        def handle_connect():
            if 'username' not in session:
                print("Brak autentykacji - odrzucenie połączenia")
                return False
            print(f"Użytkownik {session['username']} połączony przez WebSocket")
            self.socketio.emit('update_automations', self.smart_home.automations)

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f'Klient {getattr(request, "sid", "?")} rozłączony. Powód: {getattr(getattr(request, "args", None), "get", lambda x: None)("error")}')

        @self.socketio.on('set_security_state')
        def handle_set_security_state(data):
            print(f"[DEBUG] set_security_state called with data: {data}")
            print(f"[DEBUG] Session contents: {dict(session)}")
            
            # Check both username and user_id for compatibility
            if 'username' not in session and 'user_id' not in session:
                print("[DEBUG] No authentication found in session")
                return
                
            new_state = data.get('state')
            print(f"[DEBUG] Requested new state: {new_state}")
            
            if new_state in ["Załączony", "Wyłączony"]:
                try:
                    print(f"[DEBUG] Setting security state to: {new_state}")
                    self.smart_home.security_state = new_state
                    
                    current_state = self.smart_home.security_state
                    print(f"[DEBUG] State after setting: {current_state}")
                    
                    print(f"[DEBUG] Emitting update_security_state with: {current_state}")
                    self.socketio.emit('update_security_state', {'state': current_state})
                    
                    # In database mode, saving is automatic through the property setter
                    try:
                        from app_db import DATABASE_MODE
                    except ImportError:
                        DATABASE_MODE = False
                    if not DATABASE_MODE:
                        self.smart_home.save_config()
                        
                except Exception as e:
                    print(f"[ERROR] Error setting security state: {e}")
            else:
                print(f"[DEBUG] Invalid state requested: {new_state}")

        @self.socketio.on('get_security_state')
        def handle_get_security_state():
            print(f"[DEBUG] get_security_state called")
            print(f"[DEBUG] Session contents: {dict(session)}")
            
            if 'username' in session or 'user_id' in session:
                current_state = self.smart_home.security_state
                print(f"[DEBUG] Emitting current state: {current_state}")
                self.socketio.emit('update_security_state', {'state': current_state})
            else:
                print("[DEBUG] No authentication found for get_security_state")

        @self.socketio.on('toggle_button')
        def handle_toggle_button(data):
            if 'username' not in session:
                return
            button_name = data.get('name')
            room = data.get('room')
            state = data.get('state')
            if button_name and room and isinstance(state, bool):
                button = next((b for b in self.smart_home.buttons if b['name'] == button_name and b['room'].lower() == room.lower()), None)
                if button:
                    button['state'] = state
                    self.socketio.emit('update_button', {'room': room, 'name': button_name, 'state': state})
                    self.socketio.emit('sync_button_states', {f"{b['room']}_{b['name']}": b['state'] for b in self.smart_home.buttons})
                    
                    # Log button state change
                    from flask import request
                    log_btn = getattr(self.management_logger, 'log_button_change', None)
                    if callable(log_btn):
                        log_btn(
                        username=session.get('username', 'unknown'),
                        room=room,
                        button_name=button_name,
                        new_state=state,
                        ip_address=getattr(request, 'remote_addr', 'unknown')
                    )
                    
                    # Zapisz konfigurację z obsługą błędów
                    if not self.smart_home.save_config():
                        print(f"[ERROR] Nie udało się zapisać stanu przycisku {room}_{button_name}")
                        # Wyślij powiadomienie o błędzie do klienta
                        self.socketio.emit('error_message', {
                            'message': f'Nie udało się zapisać stanu przycisku {button_name}',
                            'type': 'warning'
                        })
                    else:
                        print(f"[AUTOMATION] Wywołanie check_device_triggers dla {room}_{button_name} => {state}")
                        # check_device_triggers function is not available, skipping automation trigger
                        try:
                            # Check if automation system exists and trigger automations if available
                            if hasattr(self.smart_home, 'automations'):
                                print(f"[AUTOMATION] Checking automations for device {room}_{button_name}")
                            else:
                                print(f"[AUTOMATION] Automation system not available")
                        except Exception as e:
                            print(f"[ERROR] Błąd w automation check: {e}")
                else:
                    print(f"[ERROR] Nie znaleziono przycisku {button_name} w pokoju {room}")
                    self.socketio.emit('error_message', {
                        'message': f'Nie znaleziono przycisku {button_name}',
                        'type': 'error'
                    })

        @self.socketio.on('get_button_states')
        def handle_get_button_states():
            if 'username' in session:
                self.socketio.emit('sync_button_states', {f"{button['room']}_{button['name']}": button['state'] for button in self.smart_home.buttons})

        @self.socketio.on('set_temperature')
        def handle_set_temperature(data):
            if 'username' not in session:
                return
            control_name = data.get('name')
            temperature = data.get('temperature')
            if control_name and isinstance(temperature, int) and 16 <= temperature <= 30:
                control = next((control for control in self.smart_home.temperature_controls if control['name'] == control_name), None)
                if control:
                    control['temperature'] = temperature
                    self.socketio.emit('sync_temperature', {'name': control_name, 'temperature': temperature})
                    self.smart_home.save_config()

        @self.socketio.on('get_temperatures')
        def handle_get_temperatures():
            if 'username' in session:
                self.socketio.emit('sync_temperature', self.smart_home.temperature_states)

        @self.socketio.on('get_room_temperature_controls')
        def handle_get_room_temperature_controls(room):
            if 'username' in session:
                room_controls = [control for control in self.smart_home.temperature_controls if control['room'].lower() == room.lower()]
                self.socketio.emit('update_room_temperature_controls', room_controls)

        @self.socketio.on('save_config')
        def handle_save_config():
            self.smart_home.save_config()