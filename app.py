from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, g
from flask_socketio import SocketIO, emit
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import secrets
from functools import wraps
from configure import SmartHomeSystem
from mail_manager import MailManager, get_notifications_settings, set_notifications_settings
import time
from datetime import datetime, timedelta
import os
import socket

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
# --- Bezpieczne ustawienia cookies i timeout sesji ---
app.config['SESSION_COOKIE_SECURE'] = False  # wyłącz wymóg HTTPS dla środowiska lokalnego
app.config['SESSION_COOKIE_HTTPONLY'] = True  # niedostępne dla JS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # ochrona przed CSRF
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)  # czas wygaśnięcia sesji
# Konfiguracja CORS - automatyczne wykrywanie adresów lokalnych
def get_allowed_origins():
    # Pobierz lokalny adres IP urządzenia
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"

    base_origins = [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost",
        "http://127.0.0.1",
        f"http://{local_ip}:5000",
        f"http://{local_ip}"
    ]
    return base_origins

socketio = SocketIO(app, cors_allowed_origins=get_allowed_origins())

# --- CSRF token ---
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(32)
    return session['_csrf_token']
app.jinja_env.globals['csrf_token'] = generate_csrf_token

def is_trusted_host(ip):
    """Sprawdza, czy adres IP jest zaufany"""
    if ip in ['127.0.0.1', 'localhost']:
        return True
    try:
        # Sprawdź czy IP jest w sieci 192.168.1.* lub 192.168.0.*
        octets = ip.split('.')
        return (
            len(octets) == 4 and
            octets[0] == '192' and
            octets[1] == '168' and
            octets[2] in ['0', '1'] and
            0 <= int(octets[3]) <= 255
        )
    except:
        return False

@app.before_request
def csrf_protect():
    if request.method in ['POST', 'PUT', 'DELETE']:
        # Sprawdź czy żądanie pochodzi z zaufanego hosta
        if is_trusted_host(request.remote_addr):
            token = request.headers.get('X-CSRFToken') or request.form.get('_csrf_token')
            expected = session.get('_csrf_token')
            print(f"[CSRF DEBUG] IP: {request.remote_addr} | Sent: {token} | Expected: {expected} | Path: {request.path}")
            if not token or token != expected:
                print(f"[CSRF] Invalid CSRF token from {request.remote_addr}. Sent: {token}, Expected: {expected}")
                app.logger.warning(f'Invalid CSRF token from {request.remote_addr}. Token: {token}, Session token: {expected}')
                return 'CSRF token missing or invalid', 400
        else:
            print(f"[CSRF] Request from untrusted host: {request.remote_addr}")
            app.logger.warning(f'Request from untrusted host: {request.remote_addr}')
            return 'Unauthorized host', 403

class AuthManager:
    """Klasa odpowiedzialna za zarządzanie uwierzytelnianiem"""
    @staticmethod
    def login_required(f):
        """Dekorator wymagający zalogowania"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                flash('Proszę się zalogować, aby uzyskać dostęp do tej strony.', 'warning')
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def admin_required(f):
        """Dekorator wymagający uprawnień administratora"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                flash('Brak uprawnień administratora.', 'danger')
                return redirect(url_for('home'))
            user_id, user = smart_home.get_user_by_login(session['username'])
            if not user or user.get('role') != 'admin':
                flash('Brak uprawnień administratora.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function

# Inicjalizacja systemu SmartHome
smart_home = SmartHomeSystem()
auth_manager = AuthManager()
mail_manager = MailManager()

# Trasy dla uwierzytelniania
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rozszerzona metoda logowania z zabezpieczeniami (login = pole name)"""
    if request.method == 'POST':
        login_name = request.form.get('username')
        password = request.form.get('password')
        ip_address = request.remote_addr
        user_id, user = smart_home.get_user_by_login(login_name)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user_id  # identyfikator techniczny
            session['username'] = user['name']  # login
            session['role'] = user['role']
            session.permanent = True  # aktywuj timeout sesji
            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('home'))
        # Rejestracja nieudanej próby i wysłanie alertu
        mail_manager.track_and_alert_failed_login(login_name, ip_address)
        flash('Nieprawidłowa nazwa użytkownika lub hasło', 'error')
    return render_template('login.html')

@app.route('/logout')
@auth_manager.login_required
def logout():
    """Wylogowanie użytkownika"""
    session.clear()
    if request.args.get('changed') == '1':
        flash('Pomyślnie zmieniono dane', 'success')
    else:
        flash('Wylogowano pomyślnie.', 'info')
    return redirect(url_for('login'))

class RoutesManager:
    """Klasa zarządzająca podstawowymi trasami aplikacji"""
    @staticmethod
    @app.route('/')
    def home():
        if 'username' not in session:
            return redirect(url_for('login'))
        user_data = smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
        return render_template('index.html', user_data=user_data)

    @staticmethod
    @app.route('/temp')
    @auth_manager.login_required
    def temp():
        user_data = smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
        return render_template('temp_lights.html', user_data=user_data)

    @staticmethod
    @app.route('/temperature')
    @auth_manager.login_required
    def temperature():
        user_data = smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
        return render_template('temperature.html', user_data=user_data)

    @staticmethod
    @app.route('/security')
    @auth_manager.login_required
    def security():
        user_data = smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
        return render_template('security.html', user_data=user_data)

    @staticmethod
    @app.route('/settings')
    @auth_manager.login_required
    def settings():
        user_data = smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
        return render_template('settings.html', user_data=user_data)

    @staticmethod
    @app.route('/suprise')
    @auth_manager.login_required
    def suprise():
        return render_template('suprise.html')

    @staticmethod
    @app.route('/suprise_dog')
    @auth_manager.login_required
    def suprise_dog():
        return render_template('suprise_Dog.html')

    @staticmethod
    @app.route('/automations')
    @auth_manager.login_required
    def automations():
        return render_template('automations.html')

    @staticmethod
    @app.route('/edit')
    @auth_manager.login_required
    @auth_manager.admin_required
    def edit():
        return render_template('edit.html')

    @staticmethod
    @app.route('/lights')
    @auth_manager.login_required
    def lights():
        return render_template('lights.html')

    @staticmethod
    @app.route('/error')
    def error():
        return render_template('error.html')

    @app.route('/test-email')
    def test_email():
        result = mail_manager.send_security_alert('failed_login', {
            'username': 'testuser',
            'ip_address': '127.0.0.1',
            'attempt_count': 3
        })
        return jsonify({"status": "success" if result else "error"})

    @staticmethod
    @app.route('/user')
    @auth_manager.login_required
    def user_profile():
        user_id, user = smart_home.get_user_by_login(session['username'])
        user_data = smart_home.get_user_data(user_id) if user else None
        return render_template('user.html', user_data=user_data)

    @staticmethod
    @app.route('/api/user/profile', methods=['GET', 'PUT'])
    @auth_manager.login_required
    def manage_profile():
        user_id, user = smart_home.get_user_by_login(session['username'])
        if not user:
            return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 400
        if request.method == 'GET':
            user_data = smart_home.get_user_data(user_id)
            return jsonify(user_data)
        elif request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Brak danych"}), 400

            updates = {}
            # Jeśli użytkownik zmienia login (nazwę użytkownika)
            if 'username' in data and data['username'] != user['name']:
                updates['name'] = data['username']
            # Update name if provided
            if 'name' in data:
                updates['name'] = data['name']
            # Update email if provided
            if 'email' in data:
                updates['email'] = data['email']
            # Handle password change if provided
            if data.get('current_password') and data.get('new_password'):
                if not smart_home.verify_password(user_id, data['current_password']):
                    return jsonify({"status": "error", "message": "Nieprawidłowe aktualne hasło"}), 400
                updates['password'] = data['new_password']
            success, message = smart_home.update_user_profile(user_id, updates)
            if success:
                # Jeśli login, email lub hasło zostały zmienione, wyloguj użytkownika i przekaż info o sukcesie
                if any(k in updates for k in ['name', 'email', 'password']):
                    return jsonify({"status": "success", "logout": True, "message": "pomyślnie zmieniono dane"})
                return jsonify({"status": "success", "message": message})
            return jsonify({"status": "error", "message": message}), 400

    @staticmethod
    @app.route('/api/user/profile-picture', methods=['POST'])
    @auth_manager.login_required
    def update_profile_picture():
        if 'profile_picture' not in request.files:
            return jsonify({"status": "error", "message": "Brak pliku"}), 400
            
        file = request.files['profile_picture']
        if file.filename == '':
            return jsonify({"status": "error", "message": "Nie wybrano pliku"}), 400
            
        if not file or not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Niedozwolony typ pliku"}), 400
            
        try:
            user_id, user = smart_home.get_user_by_login(session['username'])
            if not user:
                return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 400
            filename = secure_filename(f"{user_id}_{int(time.time())}{os.path.splitext(file.filename)[1]}")
            profile_pictures_dir = os.path.join(app.static_folder, 'profile_pictures')
            if not os.path.exists(profile_pictures_dir):
                os.makedirs(profile_pictures_dir)

            file_path = os.path.join(profile_pictures_dir, filename)
            file.save(file_path)

            # Update user's profile picture URL in database
            profile_picture_url = url_for('static', filename=f'profile_pictures/{filename}')
            success, message = smart_home.update_user_profile(user_id, {'profile_picture': profile_picture_url})

            if success:
                return jsonify({
                    "status": "success",
                    "message": "Zdjęcie profilowe zostało zaktualizowane",
                    "profile_picture_url": profile_picture_url
                })
            return jsonify({"status": "error", "message": message}), 500
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

def allowed_file(filename):
    """Sprawdza, czy rozszerzenie pliku jest dozwolone"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class APIManager:
    """Klasa zarządzająca endpointami API"""
    @staticmethod
    @app.route('/weather')
    @auth_manager.login_required
    def weather():
        weather_data = smart_home.fetch_weather_data()
        if weather_data:
            return jsonify(weather_data)
        return jsonify({"error": "Nie udało się pobrać danych pogodowych"}), 500

    @staticmethod
    @app.route('/api/rooms', methods=['GET', 'POST'])
    @auth_manager.login_required
    def manage_rooms():
        smart_home.check_and_save()
        if request.method == 'GET':
            return jsonify(smart_home.rooms)
        elif request.method == 'POST':
            if session.get('role') != 'admin':
                return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
            new_room = request.json.get('room')
            if new_room and new_room.lower() not in [room.lower() for room in smart_home.rooms]:
                smart_home.rooms.append(new_room)
                socketio.emit('update_rooms', smart_home.rooms)
                smart_home.save_config()
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Invalid room name or room already exists"}), 400

    @staticmethod
    @app.route('/api/rooms/<room>', methods=['DELETE'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def delete_room(room):
        print("DELETE /api/rooms/<room> room:", room)  # Dodaj ten log
        if not room or room not in smart_home.rooms:
            print("Błąd: pokój nie istnieje:", room)
            return jsonify({"status": "error", "message": "Pokój nie istnieje"}), 400
        if room.lower() in [r.lower() for r in smart_home.rooms]:
            smart_home.rooms.remove(next(r for r in smart_home.rooms if r.lower() == room.lower()))
            smart_home.buttons = [button for button in smart_home.buttons if button['room'].lower() != room.lower()]
            smart_home.temperature_controls = [control for control in smart_home.temperature_controls if control['room'].lower() != room.lower()]
            socketio.emit('update_rooms', smart_home.rooms)
            socketio.emit('update_buttons', smart_home.buttons)
            socketio.emit('update_temperature_controls', smart_home.temperature_controls)
            smart_home.save_config()
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Room not found"}), 404

    @staticmethod
    @app.route('/api/rooms/<room>', methods=['PUT'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def edit_room(room):
        data = request.get_json()
        new_name = data.get('new_name') if data else None
        if not new_name or new_name.lower() in [r.lower() for r in smart_home.rooms]:
            return jsonify({"status": "error", "message": "Nieprawidłowa lub już istniejąca nazwa pokoju"}), 400
        # Zmień nazwę pokoju w liście pokoi
        for i, r in enumerate(smart_home.rooms):
            if r.lower() == room.lower():
                smart_home.rooms[i] = new_name
                break
        # Zmień nazwę pokoju w przyciskach
        for button in smart_home.buttons:
            if button['room'].lower() == room.lower():
                button['room'] = new_name
        # Zmień nazwę pokoju w sterownikach temperatury
        for control in smart_home.temperature_controls:
            if control['room'].lower() == room.lower():
                control['room'] = new_name
        smart_home.save_config()
        socketio.emit('update_rooms', smart_home.rooms)
        socketio.emit('update_buttons', smart_home.buttons)
        socketio.emit('update_temperature_controls', smart_home.temperature_controls)
        return jsonify({"status": "success"})

    @staticmethod
    @app.route('/api/rooms/order', methods=['POST'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def set_rooms_order():
        data = request.get_json()
        rooms = data.get('rooms')
        if not isinstance(rooms, list):
            return jsonify({'status': 'error', 'message': 'Brak listy pokoi'}), 400
        # Zachowaj tylko istniejące pokoje, w nowej kolejności
        smart_home.rooms = [r for r in rooms if r in smart_home.rooms]
        socketio.emit('update_rooms', smart_home.rooms)
        smart_home.save_config()
        return jsonify({'status': 'success'})

    @staticmethod
    @app.route('/api/buttons/order', methods=['POST'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def set_buttons_order():
        data = request.get_json()
        # Obsługa formatu Kanban: {room, order: [id, id, ...]}
        if 'room' in data and 'order' in data:
            room = data['room']
            order = data['order']
            # Zbierz przyciski z tego pokoju
            room_buttons = [b for b in smart_home.buttons if b.get('room') == room]
            # Ustaw nową kolejność dla tego pokoju
            new_room_buttons = []
            for btn_id in order:
                found = next((b for b in room_buttons if str(b.get('id')) == str(btn_id)), None)
                if found:
                    new_room_buttons.append(found)
            # Zachowaj przyciski z innych pokoi w tej samej kolejności
            other_buttons = [b for b in smart_home.buttons if b.get('room') != room]
            smart_home.buttons = other_buttons + new_room_buttons
            socketio.emit('update_buttons', smart_home.buttons)
            smart_home.save_config()
            return jsonify({'status': 'success'})
        # Obsługa starego formatu: {buttons: [...]}
        buttons = data.get('buttons')
        if not isinstance(buttons, list):
            return jsonify({'status': 'error', 'message': 'Brak listy przycisków'}), 400
        new_order = []
        for btn in buttons:
            found = next((b for b in smart_home.buttons if b['name'] == btn.get('name') and b['room'] == btn.get('room')), None)
            if found:
                new_order.append(found)
        smart_home.buttons = new_order
        socketio.emit('update_buttons', smart_home.buttons)
        smart_home.save_config()
        return jsonify({'status': 'success'})

    @staticmethod
    @app.route('/api/temperature_controls/order', methods=['POST'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def set_temp_controls_order():
        data = request.get_json()
        # Obsługa formatu Kanban: {room, order: [id, id, ...]}
        if 'room' in data and 'order' in data:
            room = data['room']
            order = data['order']
            room_controls = [c for c in smart_home.temperature_controls if c.get('room') == room]
            new_room_controls = []
            for ctrl_id in order:
                found = next((c for c in room_controls if c['id'] == ctrl_id), None)
                if found:
                    new_room_controls.append(found)
            # Zastąp kolejność sterowników temperatury w tym pokoju
            smart_home.temperature_controls = [c for c in smart_home.temperature_controls if c.get('room') != room] + new_room_controls
            socketio.emit('update_temperature_controls', smart_home.temperature_controls)
            smart_home.save_config()
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Brak danych lub nieprawidłowy format'}), 400

    @staticmethod
    @app.route('/api/buttons', methods=['GET', 'POST'])
    @auth_manager.login_required
    def manage_buttons():
        smart_home.check_and_save()
        if request.method == 'GET':
            # ZAWSZE zwracaj id
            return jsonify(smart_home.buttons)
        elif request.method == 'POST':
            if session.get('role') != 'admin':
                return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
            new_button = request.json
            if new_button:
                if 'id' not in new_button:
                    import uuid
                    new_button['id'] = str(uuid.uuid4())
                new_button['state'] = False
                smart_home.buttons.append(new_button)
                socketio.emit('update_buttons', smart_home.buttons)
                smart_home.save_config()
                return jsonify({"status": "success", "id": new_button['id']})
            return jsonify({"status": "error", "message": "Invalid button data"}), 400

    @staticmethod
    @app.route('/api/buttons/<id>', methods=['PUT', 'DELETE'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def button_by_id(id):
        # Szukaj po id
        idx = next((i for i, b in enumerate(smart_home.buttons) if str(b.get('id')) == str(id)), None)
        if idx is None:
            return jsonify({'status': 'error', 'message': 'Button not found'}), 404
        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
            if 'name' in data:
                smart_home.buttons[idx]['name'] = data['name']
            if 'room' in data:
                smart_home.buttons[idx]['room'] = data['room']
            smart_home.save_config()
            socketio.emit('update_buttons', smart_home.buttons)
            return jsonify({'status': 'success'})
        elif request.method == 'DELETE':
            smart_home.buttons.pop(idx)
            smart_home.save_config()
            socketio.emit('update_buttons', smart_home.buttons)
            return jsonify({'status': 'success'})

    @staticmethod
    @app.route('/api/temperature_controls', methods=['GET', 'POST'])
    @auth_manager.login_required
    def manage_temperature_controls():
        smart_home.check_and_save()
        if request.method == 'GET':
            # ZAWSZE zwracaj id
            return jsonify(smart_home.temperature_controls)
        elif request.method == 'POST':
            if session.get('role') != 'admin':
                return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
            new_control = request.json
            if new_control:
                if 'id' not in new_control:
                    import uuid
                    new_control['id'] = str(uuid.uuid4())
                new_control['temperature'] = 22
                smart_home.temperature_controls.append(new_control)
                socketio.emit('update_temperature_controls', smart_home.temperature_controls)
                socketio.emit('update_room_temperature_controls', new_control)
                smart_home.save_config()
                return jsonify({"status": "success", "id": new_control['id']})
            return jsonify({"status": "error", "message": "Invalid control data"}), 400

    @staticmethod
    @app.route('/api/temperature_controls/<id>', methods=['PUT', 'DELETE'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def temp_control_by_id(id):
        idx = next((i for i, c in enumerate(smart_home.temperature_controls) if str(c.get('id')) == str(id)), None)
        if idx is None:
            return jsonify({'status': 'error', 'message': 'Control not found'}), 404
        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
            if 'name' in data:
                smart_home.temperature_controls[idx]['name'] = data['name']
            if 'room' in data:
                smart_home.temperature_controls[idx]['room'] = data['room']
            smart_home.save_config()
            socketio.emit('update_temperature_controls', smart_home.temperature_controls)
            return jsonify({'status': 'success'})
        elif request.method == 'DELETE':
            smart_home.temperature_controls.pop(idx)
            smart_home.save_config()
            socketio.emit('update_temperature_controls', smart_home.temperature_controls)
            return jsonify({'status': 'success'})

    @staticmethod
    @app.route('/api/temperature_controls/<int:index>', methods=['DELETE'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def delete_temperature_control(index):
        if 0 <= index < len(smart_home.temperature_controls):
            deleted_control = smart_home.temperature_controls.pop(index)
            socketio.emit('update_temperature_controls', smart_home.temperature_controls)
            socketio.emit('remove_room_temperature_control', deleted_control)
            smart_home.save_config()
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Control not found"}), 404

    @staticmethod
    @app.route('/api/temperature_controls/<int:index>', methods=['PUT'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def edit_temperature_control(index):
        if 0 <= index < len(smart_home.temperature_controls):
            data = request.get_json()
            # Pozwól na aktualizację tylko name, tylko room lub obu naraz
            if not data:
                return jsonify({"status": "error", "message": "Brak danych"}), 400
            if 'name' in data:
                smart_home.temperature_controls[index]['name'] = data['name']
            if 'room' in data:
                smart_home.temperature_controls[index]['room'] = data['room']
            smart_home.save_config()
            socketio.emit('update_temperature_controls', smart_home.temperature_controls)
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Control not found"}), 404

    @staticmethod
    @app.route('/<room>')
    @auth_manager.login_required
    def dynamic_room(room):
        if room.lower() in [r.lower() for r in smart_home.rooms]:
            room_buttons = [button for button in smart_home.buttons if button['room'].lower() == room.lower()]
            room_temperature_controls = [control for control in smart_home.temperature_controls if control['room'].lower() == room.lower()]
            user_data = smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            return render_template('room.html', 
                                room=room.capitalize(), 
                                buttons=room_buttons, 
                                temperature_controls=room_temperature_controls,
                                user_data=user_data)
        return redirect(url_for('error'))

    @staticmethod
    @app.route('/api/users', methods=['GET'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def get_users():
        """Zwraca listę wszystkich użytkowników (bez haseł)"""
        users_list = [
            {
                'user_id': user_id,
                'username': data['name'],
                'role': data['role']
            }
            for user_id, data in smart_home.users.items()
        ]
        return jsonify(users_list)

    @staticmethod
    @app.route('/api/users', methods=['POST'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def add_user():
        """Dodaje nowego użytkownika"""
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Brak danych"}), 400
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        if not username or not password:
            return jsonify({"status": "error", "message": "Brak wymaganych pól"}), 400
        success, message = smart_home.add_user(username, password, role)
        if success:
            # Pobierz user_id nowego użytkownika
            user_id, user = smart_home.get_user_by_login(username)
            return jsonify({"status": "success", "message": message, "user_id": user_id, "username": username})
        return jsonify({"status": "error", "message": message}), 400

    @staticmethod
    @app.route('/api/users/<user_id>', methods=['DELETE'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def delete_user(user_id):
        """Usuwa użytkownika po user_id (UUID)"""
        success, message = smart_home.delete_user(user_id)
        if success:
            return jsonify({"status": "success", "message": message})
        return jsonify({"status": "error", "message": message}), 400

    @staticmethod
    @app.route('/api/users/<user_id>/password', methods=['PUT'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def change_password(user_id):
        """Zmienia hasło użytkownika po user_id (UUID)"""
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Brak danych"}), 400
        new_password = data.get('new_password')
        if not new_password:
            return jsonify({"status": "error", "message": "Brak nowego hasła"}), 400
        success, message = smart_home.change_password(user_id, new_password)
        if success:
            return jsonify({"status": "success", "message": message})
        return jsonify({"status": "error", "message": message}), 400

    @staticmethod
    @app.route('/api/automations', methods=['GET', 'POST'])
    @auth_manager.login_required
    def manage_automations():
        smart_home.check_and_save()
        if request.method == 'GET':
            return jsonify(smart_home.automations)
        elif request.method == 'POST':
            if session.get('role') != 'admin':
                return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
            new_automation = request.json
            if new_automation:
                # Walidacja danych automatyzacji
                required_fields = ['name', 'trigger', 'actions', 'enabled']
                if not all(field in new_automation for field in required_fields):
                    return jsonify({"status": "error", "message": "Brak wymaganych pól"}), 400
                # Sprawdź czy automatyzacja o tej nazwie już istnieje
                if any(auto['name'].lower() == new_automation['name'].lower() for auto in smart_home.automations):
                    return jsonify({"status": "error", "message": "Automatyzacja o tej nazwie już istnieje"}), 400
                smart_home.automations.append(new_automation)
                socketio.emit('update_automations', smart_home.automations)
                smart_home.save_config()
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Invalid automation data"}), 400

    @staticmethod
    @app.route('/api/automations/<int:index>', methods=['PUT', 'DELETE'])
    @auth_manager.login_required
    @auth_manager.admin_required
    def modify_automation(index):
        if request.method == 'PUT':
            if 0 <= index < len(smart_home.automations):
                updated_automation = request.json
                if updated_automation:
                    # Sprawdź unikalność nazwy (ignorując aktualną automatyzację)
                    name_exists = any(
                        i != index and auto['name'].lower() == updated_automation['name'].lower()
                        for i, auto in enumerate(smart_home.automations)
                    )
                    if name_exists:
                        return jsonify({"status": "error", "message": "Automatyzacja o tej nazwie już istnieje"}), 400
                    smart_home.automations[index] = updated_automation
                    socketio.emit('update_automations', smart_home.automations)
                    smart_home.save_config()
                    return jsonify({"status": "success"})
                return jsonify({"status": "error", "message": "Invalid data"}), 400
            return jsonify({"status": "error", "message": "Automation not found"}), 404
        
        elif request.method == 'DELETE':
            if 0 <= index < len(smart_home.automations):
                del smart_home.automations[index]
                socketio.emit('update_automations', smart_home.automations)
                smart_home.save_config()
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Automation not found"}), 404

@app.route("/api/notifications/settings", methods=["GET"])
@auth_manager.login_required
@auth_manager.admin_required
def get_notifications_settings_api():
    settings = get_notifications_settings()
    return jsonify({"recipients": settings.get("recipients", [])})

@app.route("/api/notifications/settings", methods=["POST"])
@auth_manager.login_required
@auth_manager.admin_required
def set_notifications_settings_api():
    data = request.get_json()
    recipients = data.get("recipients", [])
    if not isinstance(recipients, list) or not all(isinstance(r, dict) and "email" in r and "user" in r for r in recipients):
        return jsonify({"status": "error", "message": "Nieprawidłowa lista odbiorców"}), 400
    set_notifications_settings({"recipients": recipients})
    return jsonify({"status": "success"})

class SocketManager:
    """Klasa zarządzająca obsługą WebSocket"""
    @staticmethod
    @socketio.on('connect')
    def handle_connect():
        if 'username' not in session:
            print("Brak autentykacji - odrzucenie połączenia")
            return False  # Blokuje połączenie
        print(f"Użytkownik {session['username']} połączony przez WebSocket")
        # Emit current automations to the client
        socketio.emit('update_automations', smart_home.automations)

    @staticmethod    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Klient {request.sid} rozłączony. Powód: {request.args.get("error")}')

    @staticmethod
    @socketio.on('set_security_state')
    def handle_set_security_state(data):
        if 'username' not in session:
            return
        new_state = data.get('state')
        if new_state in ["Załączony", "Wyłączony"]:
            smart_home.security_state = new_state
            socketio.emit('update_security_state', {'state': smart_home.security_state})
            smart_home.save_config()

    @staticmethod
    @socketio.on('get_security_state')
    def handle_get_security_state():
        if 'username' in session:
            socketio.emit('update_security_state', {'state': smart_home.security_state})

    @staticmethod
    @socketio.on('toggle_button')
    def handle_toggle_button(data):
        if 'username' not in session:
            return
        button_name = data.get('name')
        room = data.get('room')
        state = data.get('state')
        if button_name and room and isinstance(state, bool):
            button = next((b for b in smart_home.buttons if b['name'] == button_name and b['room'].lower() == room.lower()), None)
            if button:
                button['state'] = state
                socketio.emit('update_button', {'room': room, 'name': button_name, 'state': state})
                socketio.emit('sync_button_states', {f"{b['room']}_{b['name']}": b['state'] for b in smart_home.buttons})
                smart_home.save_config()
                # Sprawdź automatyzacje po zmianie stanu przycisku
                print(f"[AUTOMATION] Wywołanie check_device_triggers dla {room}_{button_name} => {state}")
                check_device_triggers(room, button_name, state)

    @staticmethod
    @socketio.on('get_button_states')
    def handle_get_button_states():
        if 'username' in session:
            socketio.emit('sync_button_states', {f"{button['room']}_{button['name']}": button['state'] for button in smart_home.buttons})

    @staticmethod
    @socketio.on('set_temperature')
    def handle_set_temperature(data):
        if 'username' not in session:
            return
        control_name = data.get('name')
        temperature = data.get('temperature')
        if control_name and isinstance(temperature, int) and 16 <= temperature <= 30:
            control = next((control for control in smart_home.temperature_controls if control['name'] == control_name), None)
            if control:
                control['temperature'] = temperature
                socketio.emit('sync_temperature', {'name': control_name, 'temperature': temperature})
                smart_home.save_config()

    @staticmethod
    @socketio.on('get_temperatures')
    def handle_get_temperatures():
        if 'username' in session:
            socketio.emit('sync_temperature', smart_home.temperature_states)

    @staticmethod
    @socketio.on('get_room_temperature_controls')
    def handle_get_room_temperature_controls(room):
        if 'username' in session:
            room_controls = [control for control in smart_home.temperature_controls if control['room'].lower() == room.lower()]
            socketio.emit('update_room_temperature_controls', room_controls)

    @staticmethod
    @socketio.on('save_config')
    def handle_save_config():
        smart_home.save_config()

@app.context_processor
def inject_user_data():
    user_data = None
    # Używaj user_id z sesji, nie loginu!
    if 'user_id' in session:
        user_data = smart_home.get_user_data(session['user_id'])
    return dict(user_data=user_data)

def check_device_triggers(room, name, new_state):
    import sys
    print(f"[AUTOMATION] Sprawdzam automatyzacje po zmianie stanu urządzenia: {room}_{name} => {new_state}", file=sys.stderr)
    for idx, automation in enumerate(smart_home.automations):
        if automation['enabled']:
            trigger = automation['trigger']
            if trigger['type'] == 'device':
                print(f"[AUTOMATION] (trigger) {automation['name']}: {trigger}", file=sys.stderr)
                if trigger['device'] == f"{room}_{name}":
                    if trigger['state'] == 'toggle':
                        print(f"[AUTOMATION] Wyzwalacz urządzenia 'toggle' spełniony po zmianie! Wykonuję akcje...", file=sys.stderr)
                        for action in automation['actions']:
                            execute_action(action)
                    elif (new_state and trigger['state'] == 'on') or (not new_state and trigger['state'] == 'off'):
                        print(f"[AUTOMATION] Wyzwalacz urządzenia spełniony po zmianie! Wykonuję akcje...", file=sys.stderr)
                        for action in automation['actions']:
                            execute_action(action)

def execute_automations():
    """Sprawdza warunki automatyzacji i wykonuje akcje."""
    import sys
    while True:
        current_time = datetime.now().strftime('%H:%M')
        current_weekday = datetime.now().weekday()  # 0=Monday
        weekday_map = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        today = weekday_map[current_weekday]
        print(f"[AUTOMATION] Sprawdzanie automatyzacji o {current_time} ({today})", file=sys.stderr)
        for idx, automation in enumerate(smart_home.automations):
            if automation['enabled']:
                trigger = automation['trigger']
                print(f"[AUTOMATION] Sprawdzam: {automation['name']} (trigger: {trigger})", file=sys.stderr)
                # Sprawdzenie wyzwalacza czasowego z obsługą dni tygodnia
                if trigger['type'] == 'time':
                    days = trigger.get('days')
                    if days and today not in days:
                        continue  # Pomijamy jeśli dziś nie jest na liście
                    print(f"[AUTOMATION] Wyzwalacz czasowy: {trigger['time']} == {current_time}?", file=sys.stderr)
                    if trigger['time'] == current_time:
                        print(f"[AUTOMATION] Warunek czasowy spełniony! Wykonuję akcje...", file=sys.stderr)
                        for action in automation['actions']:
                            execute_action(action)
                # Sprawdzenie wyzwalacza urządzenia
                elif trigger['type'] == 'device':
                    device_state = next(
                        (button['state'] for button in smart_home.buttons 
                            if f"{button['room']}_{button['name']}" == trigger['device']), None)
                    # print(f"[AUTOMATION] Wyzwalacz urządzenia: {trigger['device']} stan={device_state}, oczekiwany={trigger['state']}", file=sys.stderr)
                    if trigger['state'] == 'toggle':
                        # Nie sprawdzamy w pętli co minutę, bo toggle ma sens tylko przy zmianie
                        pass
                    elif device_state is not None and ((device_state and trigger['state'] == 'on') or (not device_state and trigger['state'] == 'off')):
                        # print(f"[AUTOMATION] Warunek urządzenia spełniony! Wykonuję akcje...", file=sys.stderr)
                        for action in automation['actions']:
                            execute_action(action)
                # Sprawdzenie wyzwalacza czujnika
                elif trigger['type'] == 'sensor':
                    sensor_value = smart_home.temperature_states.get(trigger['sensor'])
                    # print(f"[AUTOMATION] Wyzwalacz czujnika: {trigger['sensor']} value={sensor_value}, warunek={trigger['condition']} {trigger['value']}", file=sys.stderr)
                    if sensor_value is not None:
                        condition_met = (
                            (trigger['condition'] == 'above' and sensor_value > trigger['value']) or
                            (trigger['condition'] == 'below' and sensor_value < trigger['value'])
                        )
                        if condition_met:
                            # print(f"[AUTOMATION] Warunek czujnika spełniony! Wykonuję akcje...", file=sys.stderr)
                            for action in automation['actions']:
                                execute_action(action)
        time.sleep(60)  # Sprawdzaj co minutę

def execute_action(action):
    """Wykonuje akcję na podstawie jej typu."""
    import sys
    print(f"[AUTOMATION] Wykonuję akcję: {action}", file=sys.stderr)
    if action['type'] == 'device':
        device = action['device']
        state = action['state']
        room, name = device.split('_')
        button = next((b for b in smart_home.buttons if b['room'] == room and b['name'] == name), None)
        if button:
            if state == 'toggle':
                button['state'] = not button['state']
            else:
                button['state'] = state == 'on'
            # print(f"[AUTOMATION] Ustawiam {room}_{name} na {button['state']}", file=sys.stderr)
            socketio.emit('update_button', {'room': room, 'name': name, 'state': button['state']})
            smart_home.save_config()
        # else:
        #     print(f"[AUTOMATION] Nie znaleziono przycisku {device}", file=sys.stderr)
    elif action['type'] == 'notification':
        # print(f"[AUTOMATION] Wysyłam powiadomienie: {action['message']}", file=sys.stderr)
        mail_manager.send_security_alert('automation_notification', {
            'message': action['message']
        })

# Inicjalizacja menedżerów
routes_manager = RoutesManager()
api_manager = APIManager()
socket_manager = SocketManager()

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    # Uruchomienie wątku okresowo zapisującego konfigurację
    def periodic_save():
        while True:
            socketio.sleep(smart_home.save_interval)
            with app.app_context():  # Upewnij się, że kontekst aplikacji jest aktywny
                smart_home.save_config()
    socketio.start_background_task(periodic_save)
    # Uruchomienie wątku okresowo sprawdzającego automatyzacje
    socketio.start_background_task(execute_automations)
    socketio.run(app, debug=False, host="0.0.0.0" , port=5000)