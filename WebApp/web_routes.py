from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from utils.cache_manager import CachedDataAccess
from WebApp.management_logger import ManagementLogger
import os
import time
import uuid
from utils.allowed_file import allowed_file


class WebRoutesManager:
    """Manager for web-specific routes that render HTML templates"""
    
    def __init__(self, app, smart_home, auth_manager, mail_manager, async_mail_manager=None, cache=None, cached_data_access=None, management_logger=None):
        self.app = app
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.mail_manager = mail_manager
        self.async_mail_manager = async_mail_manager or mail_manager
        self.cache = cache
        self.cached_data = cached_data_access or (CachedDataAccess(cache, smart_home) if cache else None)
        self.management_logger = management_logger or ManagementLogger()
        self.register_web_routes()

    def register_web_routes(self):
        """Register all web routes that serve HTML templates"""
        print("[DEBUG] Registering web routes for HTML interface...")
        
        @self.app.route('/')
        def home():
            print(f"[DEBUG] Session on /: {dict(session)}")
            if 'username' not in session:
                print("[DEBUG] Brak username w sesji, redirect na login")
                return redirect(url_for('login'))
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            print(f"[DEBUG] user_id in session: {session.get('user_id')}, user_data: {user_data}")
            return render_template('index.html', user_data=user_data)

        @self.app.route('/temp')
        @self.auth_manager.login_required
        def temp():
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            return render_template('temp_lights.html', user_data=user_data)

        @self.app.route('/temperature')
        @self.auth_manager.login_required
        def temperature():
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            return render_template('temperature.html', user_data=user_data)

        @self.app.route('/security')
        @self.auth_manager.login_required
        def security():
            try:
                user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
                current_security_state = self.smart_home.security_state
                return render_template('security.html', user_data=user_data, security_state=current_security_state)
            except Exception as e:
                self.app.logger.error(f"Error in security route: {e}")
                return f"Internal Server Error: {str(e)}", 500

        @self.app.route('/settings', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def settings():
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            return render_template('settings.html', user_data=user_data)

        @self.app.route('/suprise')
        @self.auth_manager.login_required
        def suprise():
            return render_template('suprise.html')

        @self.app.route('/suprise_dog')
        @self.auth_manager.login_required
        def suprise_dog():
            return render_template('suprise_Dog.html')

        @self.app.route('/automations')
        @self.auth_manager.login_required
        def automations():
            return render_template('automations.html')

        @self.app.route('/edit')
        @self.auth_manager.login_required
        def edit():
            """Edit page route"""
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            if not user_data:
                return redirect(url_for('login'))
            
            if self.cached_data:
                rooms = self.cached_data.get_rooms()
                buttons = self.cached_data.get_buttons()
                temperature_controls = self.cached_data.get_temperature_controls()
            else:
                rooms = self.smart_home.rooms
                buttons = self.smart_home.buttons
                temperature_controls = self.smart_home.temperature_controls
            
            return render_template('edit.html', 
                                 user_data=user_data,
                                 rooms=rooms, 
                                 buttons=buttons,
                                 temperature_controls=temperature_controls)

        @self.app.route('/lights')
        @self.auth_manager.login_required
        def lights():
            return render_template('lights.html')

        @self.app.route('/error')
        @self.auth_manager.login_required
        def error():
            return render_template('error.html')

        @self.app.route('/user')
        @self.auth_manager.login_required
        def user():
            return render_template('user.html')

        @self.app.route('/weather')
        @self.auth_manager.login_required
        def weather():
            return render_template('weather.html')
        
        @self.app.route('/<room>')
        @self.auth_manager.login_required
        def room_page(room):
            """Dynamic room page route"""
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            if self.cached_data:
                rooms = self.cached_data.get_rooms()
            else:
                rooms = self.smart_home.rooms
            
            if room not in rooms:
                return redirect(url_for('home'))
            
            return render_template('room.html', room=room, user_data=user_data)
        
        # Authentication routes for web interface
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Web login route"""
            if request.method == 'POST':
                # Handle only form data (web requests)
                if not request.is_json:
                    login_name = request.form.get('username')
                    password = request.form.get('password')
                    remember_me = request.form.get('remember_me') == 'on'
                    
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
                        
                        flash('Zalogowano pomyślnie!', 'success')
                        return redirect(url_for('home'))
                    else:
                        # Log failed login attempt
                        if self.management_logger:
                            self.management_logger.log_login(
                                login_name or 'unknown', ip_address or 'unknown', success=False
                            )
                        
                        flash('Nieprawidłowa nazwa użytkownika lub hasło!', 'error')
                        return render_template('login.html')
                else:
                    # JSON requests should be handled by mobile API
                    return redirect(url_for('home'))
            
            return render_template('login.html')

        @self.app.route('/logout')
        def logout():
            """Web logout route"""
            session.clear()
            flash('Wylogowano pomyślnie!', 'success')
            return redirect(url_for('login'))

        @self.app.route('/register', methods=['GET', 'POST'])
        def register():
            """Web registration route"""
            return render_template('register.html')

        @self.app.route('/forgot_password', methods=['GET', 'POST'])
        def forgot_password():
            """Web forgot password route"""
            return render_template('forgot_password.html')
        
        print("[DEBUG] Web routes registered successfully!")