from flask import render_template, jsonify, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from deprecated.cache_helpers import CachedDataAccess, cache_json_response
from management_logger import ManagementLogger
import time
import os
import uuid


def allowed_file(filename):
    """Sprawdza, czy rozszerzenie pliku jest dozwolone"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class RoutesManager:
    """Klasa zarządzająca podstawowymi trasami aplikacji"""
    def __init__(self, app, smart_home, auth_manager, mail_manager, cache=None, async_mail_manager=None, management_logger=None):
        self.app = app
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.mail_manager = mail_manager
        self.async_mail_manager = async_mail_manager or mail_manager  # Fallback to sync
        self.cache = cache
        self.cached_data = CachedDataAccess(cache, smart_home) if cache else None
        # Initialize management logger
        self.management_logger = management_logger or ManagementLogger()
        self.register_routes()

    def register_routes(self):
        @self.app.route('/')
        def home():
            if 'username' not in session:
                return redirect(url_for('login'))
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
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
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            return render_template('security.html', user_data=user_data)

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
        @self.auth_manager.admin_required
        def edit():
            return render_template('edit.html')

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
                
                # Create user
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
                return redirect(url_for('admin_dashboard'))
            
            # Przygotowanie statystyk dla dashboardu
            stats = self._generate_dashboard_stats()
            device_states = self._get_device_states()
            management_logs = self._get_management_logs()
            
            return render_template('admin_dashboard.html', 
                                 stats=stats, 
                                 device_states=device_states,
                                 management_logs=management_logs)

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
            return render_template('lights.html')

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
                        ip_address=request.remote_addr,
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
                filename = secure_filename(f"{user_id}_{int(time.time())}{os.path.splitext(file.filename)[1]}")
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
        import uuid
        user_id = str(uuid.uuid4())
        from werkzeug.security import generate_password_hash
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
            ip_address=request.remote_addr,
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
    def __init__(self, app, socketio, smart_home, auth_manager, management_logger=None):
        self.app = app
        self.socketio = socketio
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.management_logger = management_logger or ManagementLogger()
        self.cached_data = {}  # Naprawa: inicjalizacja cache na potrzeby API
        self.register_routes()

    def register_routes(self):
        @self.app.route('/weather')
        @self.auth_manager.login_required
        def weather():
            weather_data = self.smart_home.fetch_weather_data()
            if weather_data:
                return jsonify(weather_data)
            return jsonify({"error": "Nie udało się pobrać danych pogodowych"}), 500

        @self.app.route('/api/rooms', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_rooms():
            self.smart_home.check_and_save()
            if request.method == 'GET':
                # Use cached data if available
                if self.cached_data:
                    rooms = self.cached_data.get_rooms()
                else:
                    rooms = self.smart_home.rooms
                return jsonify(rooms)
            elif request.method == 'POST':
                if session.get('role') != 'admin':
                    return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
                new_room = request.json.get('room')
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
                        ip_address=request.remote_addr
                    )
                    
                    # Invalidate cache after modification
                    if self.cached_data:
                        self.cached_data.invalidate_rooms_cache()
                    return jsonify({"status": "success"})
                return jsonify({"status": "error", "message": "Invalid room name or room already exists"}), 400

        @self.app.route('/api/rooms/<room>', methods=['DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def delete_room(room):
            print("DELETE /api/rooms/<room> room:", room)
            if not room or room not in self.smart_home.rooms:
                print("Błąd: pokój nie istnieje:", room)
                return jsonify({"status": "error", "message": "Pokój nie istnieje"}), 400
            if room.lower() in [r.lower() for r in self.smart_home.rooms]:
                self.smart_home.rooms.remove(next(r for r in self.smart_home.rooms if r.lower() == room.lower()))
                self.smart_home.buttons = [button for button in self.smart_home.buttons if button['room'].lower() != room.lower()]
                self.smart_home.temperature_controls = [control for control in self.smart_home.temperature_controls if control['room'].lower() != room.lower()]
                self.socketio.emit('update_rooms', self.smart_home.rooms)
                self.socketio.emit('update_buttons', self.smart_home.buttons)
                self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                if not self.smart_home.save_config():
                    return jsonify({"status": "error", "message": "Nie udało się zapisać po usunięciu pokoju"}), 500
                
                # Log room deletion
                self.management_logger.log_room_change(
                    username=session.get('username', 'unknown'),
                    action='delete',
                    room_name=room,
                    ip_address=request.remote_addr
                )
                
                # Invalidate cache after modification
                if self.cached_data:
                    self.cached_data.invalidate_rooms_cache()
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Room not found"}), 404

        @self.app.route('/api/rooms/<room>', methods=['PUT'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def edit_room(room):
            data = request.get_json()
            new_name = data.get('new_name') if data else None
            if not new_name or new_name.lower() in [r.lower() for r in self.smart_home.rooms]:
                return jsonify({"status": "error", "message": "Nieprawidłowa lub już istniejąca nazwa pokoju"}), 400
            
            old_name = room
            for i, r in enumerate(self.smart_home.rooms):
                if r.lower() == room.lower():
                    self.smart_home.rooms[i] = new_name
                    old_name = r
                    break
            for button in self.smart_home.buttons:
                if button['room'].lower() == room.lower():
                    button['room'] = new_name
            for control in self.smart_home.temperature_controls:
                if control['room'].lower() == room.lower():
                    control['room'] = new_name
            self.smart_home.save_config()
            
            # Log room rename
            self.management_logger.log_room_change(
                username=session.get('username', 'unknown'),
                action='rename',
                room_name=new_name,
                ip_address=request.remote_addr,
                old_name=old_name
            )
            
            self.socketio.emit('update_rooms', self.smart_home.rooms)
            self.socketio.emit('update_buttons', self.smart_home.buttons)
            self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
            return jsonify({"status": "success"})

        @self.app.route('/api/rooms/order', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def set_rooms_order():
            data = request.get_json()
            rooms = data.get('rooms')
            if not isinstance(rooms, list):
                return jsonify({'status': 'error', 'message': 'Brak listy pokoi'}), 400
            self.smart_home.rooms = [r for r in rooms if r in self.smart_home.rooms]
            self.socketio.emit('update_rooms', self.smart_home.rooms)
            self.smart_home.save_config()
            return jsonify({'status': 'success'})

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
                    buttons = self.cached_data.get_buttons()
                else:
                    buttons = self.smart_home.buttons
                return jsonify(buttons)
            elif request.method == 'POST':
                if session.get('role') != 'admin':
                    return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
                new_button = request.json
                if new_button:
                    if 'id' not in new_button:
                        new_button['id'] = str(uuid.uuid4())
                    new_button['state'] = False
                    self.smart_home.buttons.append(new_button)
                    self.socketio.emit('update_buttons', self.smart_home.buttons)
                    if not self.smart_home.save_config():
                        return jsonify({"status": "error", "message": "Nie udało się zapisać przycisku"}), 500
                    return jsonify({"status": "success", "id": new_button['id']})
                return jsonify({"status": "error", "message": "Invalid button data"}), 400

        @self.app.route('/api/buttons/<id>', methods=['PUT', 'DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def button_by_id(id):
            idx = next((i for i, b in enumerate(self.smart_home.buttons) if str(b.get('id')) == str(id)), None)
            if idx is None:
                return jsonify({'status': 'error', 'message': 'Button not found'}), 404
            if request.method == 'PUT':
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
                if 'name' in data:
                    self.smart_home.buttons[idx]['name'] = data['name']
                if 'room' in data:
                    self.smart_home.buttons[idx]['room'] = data['room']
                if not self.smart_home.save_config():
                    return jsonify({"status": "error", "message": "Nie udało się zapisać edycji przycisku"}), 500
                self.socketio.emit('update_buttons', self.smart_home.buttons)
                return jsonify({'status': 'success'})
            elif request.method == 'DELETE':
                self.smart_home.buttons.pop(idx)
                if not self.smart_home.save_config():
                    return jsonify({"status": "error", "message": "Nie udało się zapisać po usunięciu przycisku"}), 500
                self.socketio.emit('update_buttons', self.smart_home.buttons)
                return jsonify({'status': 'success'})

        @self.app.route('/api/temperature_controls', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_temperature_controls():
            self.smart_home.check_and_save()
            if request.method == 'GET':
                return jsonify(self.smart_home.temperature_controls)
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
        @self.auth_manager.admin_required
        def temp_control_by_id(id):
            idx = next((i for i, c in enumerate(self.smart_home.temperature_controls) if str(c.get('id')) == str(id)), None)
            if idx is None:
                return jsonify({'status': 'error', 'message': 'Control not found'}), 404
            if request.method == 'PUT':
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
                if 'name' in data:
                    self.smart_home.temperature_controls[idx]['name'] = data['name']
                if 'room' in data:
                    self.smart_home.temperature_controls[idx]['room'] = data['room']
                self.smart_home.save_config()
                self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                return jsonify({'status': 'success'})
            elif request.method == 'DELETE':
                self.smart_home.temperature_controls.pop(idx)
                self.smart_home.save_config()
                self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                return jsonify({'status': 'success'})

        @self.app.route('/api/temperature_controls/<int:index>', methods=['DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def delete_temperature_control(index):
            if 0 <= index < len(self.smart_home.temperature_controls):
                deleted_control = self.smart_home.temperature_controls.pop(index)
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
                self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Control not found"}), 404

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
            
            # Create user using the same logic as registration (without verification)
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
                ip_address=request.remote_addr,
                details={'email': email, 'role': role}
            )
            
            return jsonify({
                'status': 'success', 
                'message': 'Użytkownik został dodany pomyślnie!',
                'user_id': user_id,
                'username': username
            }), 200

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
        def delete_user(user_id):
            success, message = self.smart_home.delete_user(user_id)
            if success:
                return jsonify({"status": "success", "message": message})
            return jsonify({"status": "error", "message": message}), 400

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
                return jsonify(self.smart_home.automations)
            elif request.method == 'POST':
                if session.get('role') != 'admin':
                    return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
                new_automation = request.json
                if new_automation:
                    required_fields = ['name', 'trigger', 'actions', 'enabled']
                    if not all(field in new_automation for field in required_fields):
                        return jsonify({"status": "error", "message": "Brak wymaganych pól"}), 400
                    if any(auto['name'].lower() == new_automation['name'].lower() for auto in self.smart_home.automations):
                        return jsonify({"status": "error", "message": "Automatyzacja o tej nazwie już istnieje"}), 400
                    self.smart_home.automations.append(new_automation)
                    self.socketio.emit('update_automations', self.smart_home.automations)
                    if not self.smart_home.save_config():
                        return jsonify({"status": "error", "message": "Nie udało się zapisać automatyzacji"}), 500
                    
                    # Log automation addition
                    self.management_logger.log_automation_change(
                        username=session.get('username', 'unknown'),
                        action='add',
                        automation_name=new_automation['name'],
                        ip_address=request.remote_addr
                    )
                    
                    return jsonify({"status": "success"})
                return jsonify({"status": "error", "message": "Invalid automation data"}), 400

        @self.app.route('/api/automations/<int:index>', methods=['PUT', 'DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def modify_automation(index):
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
                        self.smart_home.automations[index] = updated_automation
                        self.socketio.emit('update_automations', self.smart_home.automations)
                        if not self.smart_home.save_config():
                            return jsonify({"status": "error", "message": "Nie udało się zapisać automatyzacji"}), 500
                        
                        # Log automation edit
                        self.management_logger.log_automation_change(
                            username=session.get('username', 'unknown'),
                            action='edit',
                            automation_name=updated_automation['name'],
                            ip_address=request.remote_addr
                        )
                        
                        return jsonify({"status": "success"})
                    return jsonify({"status": "error", "message": "Invalid data"}), 400
                return jsonify({"status": "error", "message": "Automation not found"}), 404
            elif request.method == 'DELETE':
                if 0 <= index < len(self.smart_home.automations):
                    automation_name = self.smart_home.automations[index].get('name', 'unknown')
                    del self.smart_home.automations[index]
                    self.socketio.emit('update_automations', self.smart_home.automations)
                    if not self.smart_home.save_config():
                        return jsonify({"status": "error", "message": "Nie udało się zapisać po usunięciu automatyzacji"}), 500
                    
                    # Log automation deletion
                    self.management_logger.log_automation_change(
                        username=session.get('username', 'unknown'),
                        action='delete',
                        automation_name=automation_name,
                        ip_address=request.remote_addr
                    )
                    
                    return jsonify({"status": "success"})
                return jsonify({"status": "error", "message": "Automation not found"}), 404


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
            print(f'Klient {request.sid} rozłączony. Powód: {request.args.get("error")}')

        @self.socketio.on('set_security_state')
        def handle_set_security_state(data):
            if 'username' not in session:
                return
            new_state = data.get('state')
            if new_state in ["Załączony", "Wyłączony"]:
                self.smart_home.security_state = new_state
                self.socketio.emit('update_security_state', {'state': self.smart_home.security_state})
                self.smart_home.save_config()

        @self.socketio.on('get_security_state')
        def handle_get_security_state():
            if 'username' in session:
                self.socketio.emit('update_security_state', {'state': self.smart_home.security_state})

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
                    self.management_logger.log_button_change(
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
                        # Zakładam, że funkcja check_device_triggers jest zdefiniowana w app.py
                        try:
                            from app import check_device_triggers
                            check_device_triggers(room, button_name, state)
                        except Exception as e:
                            print(f"[ERROR] Błąd w check_device_triggers: {e}")
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