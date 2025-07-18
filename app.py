from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_socketio import SocketIO
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import secrets
from functools import wraps
from configure import SmartHomeSystem
from mail_manager import MailManager, get_notifications_settings, set_notifications_settings
import time
from datetime import datetime, timedelta
import routes
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
        f"http://{local_ip}",
        "172.17.240.69:5000",
        "172.17.240.69"
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
    if ip in ['127.0.0.1', 'localhost', '172.17.240.69']:
        return True
    try:
        octets = ip.split('.')
        # Sprawdź czy IP jest w sieci 192.168.1.* lub 192.168.0.*
        if (
            len(octets) == 4 and
            octets[0] == '192' and
            octets[1] == '168' and
            octets[2] in ['0', '1'] and
            0 <= int(octets[3]) <= 255
        ):
            return True
        # Dodaj obsługę sieci 172.17.240.*
        if (
            len(octets) == 4 and
            octets[0] == '172' and
            octets[1] == '17' and
            octets[2] == '240' and
            0 <= int(octets[3]) <= 255
        ):
            return True
    except:
        return False
    return False

@app.before_request
def csrf_protect():
    if request.method in ['POST', 'PUT', 'DELETE']:
        # Sprawdź czy żądanie pochodzi z zaufanego hosta
        if is_trusted_host(request.remote_addr):
            token = request.headers.get('X-CSRFToken') or request.form.get('_csrf_token')
            expected = session.get('_csrf_token')
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
        remember_me = request.form.get('remember_me') == 'on'
        ip_address = request.remote_addr
        user_id, user = smart_home.get_user_by_login(login_name)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user_id  # identyfikator techniczny
            session['username'] = user['name']  # login
            session['role'] = user['role']
            session.permanent = True  # aktywuj timeout sesji
            flash('Zalogowano pomyślnie!', 'success')
            # Jeśli użytkownik chce zapamiętać dane, zwróć informację o tym
            if remember_me:
                response = redirect(url_for('home'))
                response.set_cookie('remember_user', 'true', max_age=30*24*60*60)  # 30 dni
                return response
            else:
                # Usuń cookie jeśli użytkownik nie chce zapamiętać danych
                response = redirect(url_for('home'))
                response.set_cookie('remember_user', '', expires=0)
                return response
        # Rejestracja nieudanej próby i wysłanie alertu
        mail_manager.track_and_alert_failed_login(login_name, ip_address)
        flash('Nieprawidłowa nazwa użytkownika lub hasło', 'error')
        # Wygeneruj nowy token CSRF po nieudanym logowaniu
        session['_csrf_token'] = secrets.token_urlsafe(32)
    else:
        # GET: zawsze generuj nowy token CSRF
        session['_csrf_token'] = secrets.token_urlsafe(32)
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

def allowed_file(filename):
    """Sprawdza, czy rozszerzenie pliku jest dozwolone"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        for idx, automation in enumerate(smart_home.automations):
            if automation['enabled']:
                trigger = automation['trigger']
                # Sprawdzenie wyzwalacza czasowego z obsługą dni tygodnia
                if trigger['type'] == 'time':
                    days = trigger.get('days')
                    if days and today not in days:
                        continue  # Pomijamy jeśli dziś nie jest na liście
                    # print(f"[AUTOMATION] Wyzwalacz czasowy: {trigger['time']} == {current_time}?", file=sys.stderr)
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
                        print(f"[AUTOMATION] Warunek urządzenia spełniony! Wykonuję akcje...", file=sys.stderr)
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
                            print(f"[AUTOMATION] Warunek czujnika spełniony! Wykonuję akcje...", file=sys.stderr)
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
            print(f"[AUTOMATION] Ustawiam {room}_{name} na {button['state']}", file=sys.stderr)
            socketio.emit('update_button', {'room': room, 'name': name, 'state': button['state']})
            smart_home.save_config()
        else:
            print(f"[AUTOMATION] Nie znaleziono przycisku {device}", file=sys.stderr)
    elif action['type'] == 'notification':
        print(f"[AUTOMATION] Wysyłam powiadomienie: {action['message']}", file=sys.stderr)
        mail_manager.send_security_alert('automation_notification', {
            'message': action['message']
        })

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"[ERROR] Unhandled exception: {e}")
    print(f"[ERROR] Request: {request.method} {request.path} from {request.remote_addr}")
    # Return a generic error response
    return jsonify({"status": "error", "message": "Błąd serwera"}), 500

# Inicjalizacja menedżerów
routes_manager = routes.RoutesManager(app, smart_home, auth_manager, mail_manager)
api_manager = routes.APIManager(app, socketio, smart_home, auth_manager)
socket_manager = routes.SocketManager(socketio, smart_home)

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