# SmartHome - System Zarządzania Domem Inteligentnym

## Spis Treści

1. [Wprowadzenie](#wprowadzenie)
2. [Architektura Systemu](#architektura-systemu)
3. [Technologie i Narzędzia](#technologie-i-narzędzia)
4. [Struktura Projektu](#struktura-projektu)
5. [Funkcjonalności](#funkcjonalności)
6. [Bezpieczeństwo](#bezpieczeństwo)
7. [Interfejs Użytkownika](#interfejs-użytkownika)
8. [API i Komunikacja](#api-i-komunikacja)
9. [Baza Danych](#baza-danych)
10. [Konfiguracja i Uruchamianie](#konfiguracja-i-uruchamianie)
11. [Testy i Debugging](#testy-i-debugging)
12. [Rozszerzalność](#rozszerzalność)
13. [Potencjalne Usprawnienia](#potencjalne-usprawnienia)

---

## Wprowadzenie

SmartHome to kompleksowy system zarządzania domem inteligentnym, zaprojektowany jako aplikacja webowa wykorzystująca Flask (Python) oraz nowoczesne technologie frontendowe. System umożliwia kontrolę i monitorowanie różnych aspektów domu inteligentnego, w tym oświetlenia, temperatury, zabezpieczeń oraz automatyzacji.

### Główne Cele Projektu:

- **Centralna kontrola**: Jednolity interfejs do zarządzania wszystkimi urządzeniami
- **Bezpieczeństwo**: Wielopoziomowe zabezpieczenia i system uwierzytelniania
- **Skalowalność**: Możliwość łatwego dodawania nowych urządzeń i funkcji
- **Dostępność**: Responsywny interfejs działający na różnych urządzeniach
- **Automatyzacja**: Inteligentne reguły i scenariusze automatyzacji

---

## Architektura Systemu

### Wzorzec Architektoniczny: MVC (Model-View-Controller)

```
┌─────────────────────────────────────────────────────────────┐
│                    PREZENTACJA                              │
├─────────────────────────────────────────────────────────────┤
│  HTML Templates (Jinja2)  │  CSS (Responsive)  │  JavaScript│
│  - base.html               │  - style.css       │  - app.js  │
│  - index.html              │  - mobile.css      │  - Socket.IO│
│  - login.html              │  - user.css        │  - automations.js│
│  - settings.html           │  - dragNdrop.css   │  - controls.js│
└─────────────────────────────────────────────────────────────┘
                                  ↕
┌─────────────────────────────────────────────────────────────┐
│                    KONTROLER                                │
├─────────────────────────────────────────────────────────────┤
│  Flask Routes              │  WebSocket Handlers            │
│  - RoutesManager           │  - SocketManager               │
│  - APIManager              │  - Real-time Communication     │
│  - AuthManager             │  - Live Updates                │
└─────────────────────────────────────────────────────────────┘
                                  ↕
┌─────────────────────────────────────────────────────────────┐
│                    MODEL                                    │
├─────────────────────────────────────────────────────────────┤
│  Business Logic            │  Data Management               │
│  - SmartHomeSystem         │  - JSON Configuration          │
│  - MailManager             │  - File Storage                │
│  - User Management         │  - State Persistence           │
│  - Automation Engine       │  - Backup System               │
└─────────────────────────────────────────────────────────────┘
```

### Komponenty Systemu:

#### 1. **Frontend (Warstwa Prezentacji)**

- **HTML Templates**: Dynamicznie generowane strony przy użyciu Jinja2
- **CSS**: Responsywny design z obsługą motywów jasnego/ciemnego
- **JavaScript**: Interaktywność, komunikacja z backendem, real-time updates

#### 2. **Backend (Warstwa Biznesowa)**

- **Flask Application**: Główna aplikacja webowa
- **Route Managers**: Obsługa tras HTTP i API endpoints
- **WebSocket Handlers**: Komunikacja w czasie rzeczywistym
- **Business Logic**: Logika biznesowa i przetwarzanie danych

#### 3. **Data Layer (Warstwa Danych)**

- **JSON Configuration**: Przechowywanie konfiguracji i stanu systemu
- **File Storage**: Zarządzanie plikami użytkowników
- **Session Management**: Zarządzanie sesjami użytkowników

---

## Technologie i Narzędzia

### Backend Technologies:

- **Python 3.x**: Główny język programowania
- **Flask 3.1.0**: Framework webowy
- **Flask-SocketIO 5.5.0**: Komunikacja w czasie rzeczywistym
- **Werkzeug 3.1.3**: WSGI toolkit (bezpieczeństwo, utilities)
- **Jinja2 3.1.5**: Template engine
- **Cryptography 44.0.0**: Szyfrowanie danych
- **python-dotenv**: Zarządzanie zmiennymi środowiskowymi

### Frontend Technologies:

- **HTML5**: Markup language
- **CSS3**: Styling z CSS Grid, Flexbox, animacje
- **JavaScript ES6+**: Interaktywność
- **Socket.IO 4.7.1**: Real-time communication
- **Leaflet.js**: Mapy interaktywne
- **Dragula.js**: Drag & drop functionality

### Security & Communication:

- **CSRF Protection**: Zabezpieczenie przed atakami CSRF
- **Password Hashing**: Scrypt hashing algorithm
- **Session Management**: Bezpieczne sesje z timeout
- **SMTP Integration**: Wysyłanie powiadomień email
- **Input Validation**: Walidacja danych wejściowych

### Development Tools:

- **pytest**: Framework testowy
- **gunicorn**: WSGI server dla produkcji
- **Git**: System kontroli wersji

---

## Struktura Projektu

```
SmartHome/
├── app.py                      # Główna aplikacja Flask
├── configure.py                # Konfiguracja systemu SmartHome
├── routes.py                   # Definicje tras i API endpoints
├── mail_manager.py             # Zarządzanie powiadomieniami email
├── requirements.txt            # Dependencje Python
├── README.md                   # Dokumentacja projektu
├── *.json                      # Pliki konfiguracyjne
├── *.env                       # Zmienne środowiskowe
├── *.enc, *.key               # Pliki szyfrowane
│
├── templates/                  # Szablony HTML (Jinja2)
│   ├── base.html              # Szablon bazowy
│   ├── index.html             # Strona główna
│   ├── login.html             # Strona logowania
│   ├── register.html          # Rejestracja użytkownika
│   ├── settings.html          # Panel ustawień
│   ├── user.html              # Profil użytkownika
│   ├── automations.html       # Panel automatyzacji
│   ├── temperature.html       # Kontrola temperatury
│   ├── security.html          # Panel zabezpieczeń
│   ├── lights.html            # Kontrola oświetlenia
│   ├── edit.html              # Edycja konfiguracji
│   ├── room.html              # Widok pojedynczego pokoju
│   └── error.html             # Strona błędów
│
├── static/                     # Pliki statyczne
│   ├── css/                   # Style CSS
│   │   ├── style.css          # Główne style
│   │   ├── mobile.css         # Responsive design
│   │   ├── user.css           # Style profilu użytkownika
│   │   ├── register.css       # Style rejestracji
│   │   ├── dragNdrop.css      # Style drag & drop
│   │   ├── user_menu.css      # Style menu użytkownika
│   │   └── style_404.css      # Style strony błędów
│   │
│   ├── js/                    # JavaScript
│   │   ├── app.js             # Główna aplikacja JS
│   │   ├── automations.js     # Logika automatyzacji
│   │   ├── controls.js        # Kontrolki urządzeń
│   │   ├── lights.js          # Kontrola oświetlenia
│   │   ├── settings.js        # Panel ustawień
│   │   ├── user.js            # Profil użytkownika
│   │   ├── register.js        # Rejestracja
│   │   ├── dragNdrop.js       # Drag & drop
│   │   ├── setup.js           # Konfiguracja
│   │   └── user_menu.js       # Menu użytkownika
│   │
│   ├── icons/                 # Ikony systemu
│   │   ├── *_icon_light.png   # Ikony jasne
│   │   ├── *_icon_dark.png    # Ikony ciemne
│   │   └── site_icon.png      # Favicon
│   │
│   └── profile_pictures/      # Zdjęcia profilowe
│       ├── podstawowe.jpg     # Domyślne zdjęcie
│       └── *.png              # Zdjęcia użytkowników
│
└── __pycache__/               # Skompilowane pliki Python
```

---

## Funkcjonalności

### 1. **System Uwierzytelniania i Autoryzacji**

#### Funkcje Podstawowe:

- **Rejestracja z weryfikacją email**: Dwustopniowy proces rejestracji
- **Logowanie z "Zapamiętaj mnie"**: Persistent sessions
- **Zarządzanie profilami**: Edycja danych osobowych, zmiana haseł
- **Zdjęcia profilowe**: Upload i zarządzanie awatarami
- **Role użytkowników**: Admin/User z różnymi uprawnieniami

#### Zabezpieczenia:

- **CSRF Protection**: Tokeny CSRF dla wszystkich formularzy
- **Password Hashing**: Scrypt algorithm
- **Session Timeout**: Automatyczne wylogowanie
- **Failed Login Tracking**: Monitorowanie nieudanych prób logowania
- **Email Notifications**: Powiadomienia o podejrzanych aktywnościach

```python
# Przykład implementacji zabezpieczeń
@app.before_request
def csrf_protect():
    if request.method in ['POST', 'PUT', 'DELETE']:
        token = request.headers.get('X-CSRFToken') or request.form.get('_csrf_token')
        expected = session.get('_csrf_token')
        if not token or token != expected:
            return 'CSRF token missing or invalid', 400
```

### 2. **Zarządzanie Pokojami i Urządzeniami**

#### Struktura Hierarchiczna:

```
Dom
├── Pokój 1
│   ├── Światło 1 (ON/OFF)
│   ├── Światło 2 (ON/OFF)
│   └── Termostat 1 (16-30°C)
├── Pokój 2
│   ├── Światło 1 (ON/OFF)
│   └── Termostat 1 (16-30°C)
└── Pokój N...
```

#### Funkcje:

- **Dodawanie/Usuwanie pokojów**: Dynamiczne zarządzanie strukturą domu
- **Kontrola urządzeń**: Przełączniki, regulatory temperatury
- **Drag & Drop**: Intuicyjne przenoszenie urządzeń między pokojami
- **Grupowanie**: Organizacja urządzeń według typu i lokalizacji
- **Stan urządzeń**: Śledzenie stanu ON/OFF, wartości temperatury

### 3. **System Automatyzacji**

#### Typy Wyzwalaczy:

1. **Czasowe**: Określone godziny/dni tygodnia
2. **Urządzenia**: Zmiana stanu urządzeń
3. **Sensory**: Progi temperaturowe

#### Typy Akcji:

1. **Kontrola urządzeń**: ON/OFF/Toggle
2. **Powiadomienia**: Email alerts
3. **Scenariusze**: Łańcuchy akcji

```json
{
  "name": "Wieczorne światła",
  "trigger": {
    "type": "time",
    "time": "19:00",
    "days": ["mon", "tue", "wed", "thu", "fri"]
  },
  "actions": [
    {
      "type": "device",
      "device": "Salon_Główne światło",
      "state": "on"
    },
    {
      "type": "notification",
      "message": "Włączono wieczorne oświetlenie"
    }
  ],
  "enabled": true
}
```

### 4. **Panel Administracyjny**

#### Zarządzanie Użytkownikami:

- **Lista użytkowników**: Tabela z danymi użytkowników
- **Dodawanie użytkowników**: Formularz tworzenia kont
- **Edycja in-place**: Bezpośrednia edycja w tabeli
- **Usuwanie użytkowników**: Z zabezpieczeniami
- **Zarządzanie rolami**: Admin/User assignments

#### Konfiguracja Systemu:

- **Motywy**: Przełączanie jasny/ciemny
- **Powiadomienia**: Konfiguracja odbiorców email
- **Backup**: Eksport/import konfiguracji

### 5. **Monitoring i Powiadomienia**

#### System Powiadomień:

- **Email alerts**: SMTP integration
- **Weryfikacja kodu**: 6-cyfrowe kody weryfikacyjne
- **Szyfrowanie**: Encrypted recipient lists
- **Szablony**: HTML email templates

#### Monitoring:

- **Logi systemu**: Tracking user activities
- **Failed login attempts**: Security monitoring
- **Performance metrics**: System health checks

---

## Bezpieczeństwo

### 1. **Uwierzytelnianie i Autoryzacja**

#### Mechanizmy Bezpieczeństwa:

```python
class AuthManager:
    @staticmethod
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                flash('Proszę się zalogować', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != 'admin':
                flash('Brak uprawnień administratora', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
```

### 2. **Ochrona Danych**

#### Hashowanie Haseł:

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Tworzenie hasła
password_hash = generate_password_hash(password)

# Weryfikacja
is_valid = check_password_hash(stored_hash, provided_password)
```

#### Szyfrowanie Plików:

```python
from cryptography.fernet import Fernet

def get_fernet():
    if not os.path.exists(FERNET_KEY_PATH):
        key = Fernet.generate_key()
        with open(FERNET_KEY_PATH, "wb") as f:
            f.write(key)
    else:
        with open(FERNET_KEY_PATH, "rb") as f:
            key = f.read()
    return Fernet(key)
```

### 3. **Walidacja Danych**

#### Input Validation:

- **Długość**: Minimum 3 znaki dla username, 6 dla hasła
- **Format email**: Regex validation
- **Temperatura**: Zakres 16-30°C
- **Sanityzacja**: Escape HTML, SQL injection prevention

#### CSRF Protection:

```python
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(32)
    return session['_csrf_token']
```

### 4. **Bezpieczeństwo Sieci**

#### Trusted Hosts:

```python
def is_trusted_host(ip):
    trusted_networks = [
        '127.0.0.1',
        '192.168.1.0/24',
        '192.168.0.0/24',
        '172.17.240.0/24'
    ]
    return ip in trusted_networks
```

#### Session Security:

```python
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
```

---

## Interfejs Użytkownika

### 1. **Responsive Design**

#### Breakpoints:

```css
/* Mobile First Approach */
@media (max-width: 768px) {
    .grid-container {
        grid-template-columns: 1fr !important;
    }
  
    .side-menu {
        width: 100vw;
    }
  
    .user-management {
        flex-direction: column;
    }
}
```

#### Adaptive Layout:

- **Desktop**: Multi-column grids, sidebars
- **Tablet**: Adjusted spacing, collapsed menus
- **Mobile**: Single column, touch-friendly buttons

### 2. **Tematyzacja (Theming)**

#### CSS Custom Properties:

```css
:root[data-theme="light"] {
    --primary: #1e3a8a;
    --secondary: #f3f4f6;
    --accent: #3b82f6;
    --background: #ffffff;
    --text-color: #1f2937;
}

:root[data-theme="dark"] {
    --primary: #1e40af;
    --secondary: #374151;
    --accent: #60a5fa;
    --background: #111827;
    --text-color: #f9fafb;
}
```

#### Dynamic Theme Switching:

```javascript
changeTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    this.updateThemeIcons(theme);
}
```

### 3. **Interactive Elements**

#### Drag & Drop Interface:

```javascript
// Kanban-style room management
function initializeDragDrop() {
    const drake = dragula([...columns], {
        isContainer: function(el) {
            return el.classList.contains('kanban-column-content');
        },
        moves: function(el, source, handle, sibling) {
            return handle.classList.contains('kanban-item');
        }
    });
}
```

#### Real-time Updates:

```javascript
// Socket.IO integration
app.socket.on('update_button', function(data) {
    const switchElement = document.getElementById(`${data.name}Switch`);
    if (switchElement) {
        switchElement.checked = data.state;
    }
});
```

### 4. **User Experience Features**

#### Animations:

```css
.switch {
    transition: all 0.3s ease;
}

.side-menu {
    transition: left 0.3s ease-in-out;
}

.notification {
    animation: slideIn 0.3s ease-out;
}
```

#### Accessibility:

- **ARIA labels**: Screen reader support
- **Keyboard navigation**: Tab order, focus management
- **Color contrast**: WCAG compliance
- **Touch targets**: Minimum 44px touch zones

---

## API i Komunikacja

### 1. **RESTful API Endpoints**

#### User Management:

```python
# GET /api/users - Lista użytkowników
# POST /api/users - Dodanie użytkownika
# PUT /api/users/<id> - Aktualizacja użytkownika
# DELETE /api/users/<id> - Usunięcie użytkownika
```

#### Device Control:

```python
# GET /api/buttons - Lista przycisków
# POST /api/buttons - Dodanie przycisku
# PUT /api/buttons/<id> - Aktualizacja przycisku
# DELETE /api/buttons/<id> - Usunięcie przycisku
```

#### Room Management:

```python
# GET /api/rooms - Lista pokojów
# POST /api/rooms - Dodanie pokoju
# PUT /api/rooms/<name> - Aktualizacja pokoju
# DELETE /api/rooms/<name> - Usunięcie pokoju
```

### 2. **WebSocket Communication**

#### Real-time Events:

```python
@socketio.on('toggle_button')
def handle_toggle_button(data):
    # Update device state
    button['state'] = data['state']
  
    # Broadcast to all clients
    socketio.emit('update_button', {
        'room': data['room'],
        'name': data['name'],
        'state': data['state']
    })
```

#### Event Types:

- **connect/disconnect**: Connection management
- **toggle_button**: Device state changes
- **set_temperature**: Temperature control
- **update_automations**: Automation changes
- **security_state**: Security system updates

### 3. **Data Formats**

#### JSON Structure:

```json
{
    "users": {
        "uuid": {
            "name": "string",
            "email": "string",
            "role": "admin|user",
            "password": "hashed_string",
            "profile_picture": "url"
        }
    },
    "rooms": ["string"],
    "buttons": [{
        "id": "uuid",
        "name": "string",
        "room": "string",
        "state": "boolean"
    }],
    "temperature_controls": [{
        "id": "uuid",
        "name": "string",
        "room": "string",
        "temperature": "integer"
    }],
    "automations": [{
        "name": "string",
        "trigger": "object",
        "actions": ["object"],
        "enabled": "boolean"
    }]
}
```

### 4. **Error Handling**

#### HTTP Status Codes:

```python
# 200 OK - Success
# 400 Bad Request - Invalid data
# 401 Unauthorized - Authentication required
# 403 Forbidden - Insufficient permissions
# 404 Not Found - Resource not found
# 500 Internal Server Error - Server error
```

#### Error Response Format:

```json
{
    "status": "error",
    "message": "Human readable error message",
    "details": "Optional detailed information"
}
```

---

## Baza Danych

### 1. **JSON File Storage**

#### Struktura Plików:

```
├── smart_home_config.json      # Główna konfiguracja
├── smart_home_1st_conf.json    # Backup konfiguracji
├── notifications_settings.json # Ustawienia powiadomień
├── notification_recipients.enc # Szyfrowana lista odbiorców
├── notification_recipients.key # Klucz szyfrowania
└── email_conf.env             # Konfiguracja SMTP
```

### 2. **Data Models**

#### User Model:

```python
{
    "uuid": {
        "name": "admin",
        "email": "admin@example.com",
        "password": "scrypt:32768:8:1$...",
        "role": "admin",
        "profile_picture": "/static/profile_pictures/uuid_timestamp.png"
    }
}
```

#### Device Models:

```python
# Button Model
{
    "id": "uuid",
    "name": "Światło główne",
    "room": "Salon",
    "state": false
}

# Temperature Control Model
{
    "id": "uuid",
    "name": "Termostat",
    "room": "Salon",
    "temperature": 22
}
```

#### Automation Model:

```python
{
    "name": "Automation Name",
    "trigger": {
        "type": "time|device|sensor",
        "time": "19:00",
        "days": ["mon", "tue", "wed", "thu", "fri"],
        "device": "Room_DeviceName",
        "state": "on|off|toggle",
        "sensor": "SensorName",
        "condition": "above|below",
        "value": 25
    },
    "actions": [
        {
            "type": "device|notification",
            "device": "Room_DeviceName",
            "state": "on|off|toggle",
            "message": "Notification text"
        }
    ],
    "enabled": true
}
```

### 3. **Data Persistence**

#### Auto-save Mechanism:

```python
def periodic_save():
    while True:
        socketio.sleep(smart_home.save_interval)
        with app.app_context():
            smart_home.save_config()
```

#### Backup Strategy:

```python
def save_config(self):
    # Create backup
    if os.path.exists(self.config_file):
        backup_file = f"{self.config_file}.backup"
        shutil.copy2(self.config_file, backup_file)
  
    # Save new configuration
    with open(self.config_file, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
```

### 4. **Data Migration**

#### UUID Migration:

```python
def migrate_users_to_uuid(self):
    """Migruje użytkowników z username na UUID keys"""
    new_users = {}
    for old_key, user in self.users.items():
        if not self.is_uuid(old_key):
            user_id = str(uuid.uuid4())
            user['name'] = old_key
            new_users[user_id] = user
        else:
            new_users[old_key] = user
    self.users = new_users
```

---

## Konfiguracja i Uruchamianie

### 1. **Wymagania Systemowe**

#### Minimalne Wymagania:

- **Python**: 3.8+
- **RAM**: 512MB
- **Disk**: 100MB
- **Network**: Port 5000 (domyślny)

#### Zalecane Wymagania:

- **Python**: 3.11+
- **RAM**: 1GB
- **Disk**: 1GB
- **Network**: HTTPS z certyfikatem SSL

### 2. **Instalacja**

#### Krok 1: Klonowanie repozytorium

```bash
git clone https://github.com/username/smarthome.git
cd smarthome
```

#### Krok 2: Środowisko wirtualne

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### Krok 3: Instalacja dependencji

```bash
pip install -r requirements.txt
```

#### Krok 4: Konfiguracja środowiska

```bash
cp email_conf.env.example email_conf.env
# Edytuj email_conf.env z własnymi ustawieniami SMTP
```

### 3. **Konfiguracja**

#### Plik email_conf.env:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ADMIN_EMAIL=admin@example.com
```

#### Pierwsze uruchomienie:

```python
# Domyślni użytkownicy
users = {
    'admin': {
        'password': 'admin123',
        'role': 'admin'
    },
    'user': {
        'password': 'user123',
        'role': 'user'
    }
}
```

### 4. **Uruchamianie**

#### Tryb rozwojowy:

```bash
python app.py
```

#### Tryb produkcyjny:

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

#### Systemd Service:

```ini
[Unit]
Description=SmartHome Application
After=network.target

[Service]
Type=simple
User=smarthome
WorkingDirectory=/path/to/smarthome
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Testy i Debugging

### 1. **Test Framework**

#### Pytest Configuration:

```python
# conftest.py
import pytest
from app import app, smart_home

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_client(client):
    # Login user for authenticated tests
    client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    })
    yield client
```

#### Unit Tests:

```python
def test_user_registration(client):
    response = client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    assert 'verification_sent' in response.get_json()['status']

def test_device_control(auth_client):
    response = auth_client.post('/api/buttons', json={
        'name': 'Test Light',
        'room': 'Test Room'
    })
    assert response.status_code == 200
    assert response.get_json()['status'] == 'success'
```

### 2. **Debugging Tools**

#### Logging Configuration:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### Debug Endpoints:

```python
@app.route('/test-email')
def test_email():
    result = mail_manager.send_security_alert('failed_login', {
        'username': 'testuser',
        'ip_address': '127.0.0.1',
        'attempt_count': 3
    })
    return jsonify({"status": "success" if result else "error"})
```

### 3. **Performance Monitoring**

#### Metrics Collection:

```python
def track_performance():
    start_time = time.time()
    # Operation
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Operation took {duration:.2f} seconds")
```

#### Memory Usage:

```python
import psutil
import os

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB
```

---

## Rozszerzalność

### 1. **Modular Architecture**

#### Plugin System:

```python
class DevicePlugin:
    def __init__(self, name):
        self.name = name
  
    def register_routes(self, app):
        pass
  
    def register_socketio_handlers(self, socketio):
        pass
  
    def get_device_types(self):
        pass
```

#### Device Types:

```python
# Możliwe rozszerzenia
DEVICE_TYPES = {
    'light': 'Światło',
    'thermostat': 'Termostat',
    'camera': 'Kamera',
    'sensor': 'Czujnik',
    'lock': 'Zamek',
    'speaker': 'Głośnik',
    'curtains': 'Rolety'
}
```

### 2. **Integration Points**

#### External APIs:

```python
# Weather API integration
def fetch_weather_data(self):
    url = "https://danepubliczne.imgw.pl/api/data/synop/id/12330"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None
```

#### Hardware Integration:

```python
# TinyTuya integration for smart devices
import tinytuya

class TuyaDevice:
    def __init__(self, device_id, local_key):
        self.device = tinytuya.OutletDevice(device_id, 
                                          'Auto', 
                                          local_key)
  
    def toggle(self):
        return self.device.turn_on()
```

### 3. **Database Expansion**

#### SQL Database Migration:

```python
# Możliwa migracja z JSON do SQL
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
  
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default='user')
```

---

## Potencjalne Usprawnienia

### 1. **Funkcjonalności**

#### Zaawansowane Automatyzacje:

- **Machine Learning**: Uczenie wzorców użytkowania
- **Geolokalizacja**: Automatyzacja oparta na lokalizacji
- **Sensory zewnętrzne**: Integracja z czujnikami pogody
- **Voice Control**: Integracja z asystentami głosowymi

#### Bezpieczeństwo:

- **Two-Factor Authentication**: SMS/Authenticator app
- **OAuth Integration**: Google/Facebook login
- **API Rate Limiting**: Throttling requests
- **Audit Logs**: Szczegółowe logi aktywności

### 2. **Wydajność**

#### Optimization:

- **Caching**: Redis dla częstych zapytań
- **Database**: PostgreSQL/MySQL dla lepszej wydajności
- **CDN**: Statyczne pliki z CDN
- **Load Balancing**: Horizontal scaling

#### Monitoring:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **ELK Stack**: Log aggregation i analysis
- **Health Checks**: Automated monitoring

### 3. **User Experience**

#### Mobile App:

- **React Native**: Cross-platform mobile app
- **Push Notifications**: Real-time alerts
- **Offline Mode**: Cached data access
- **Biometric Auth**: Fingerprint/Face ID

#### Advanced UI:

- **Data Visualization**: Charts i graphs
- **3D Floor Plans**: Interactive home layouts
- **AR Integration**: Augmented reality controls
- **Dark Mode**: Advanced theming options

---

## Podsumowanie

System SmartHome reprezentuje kompleksowe rozwiązanie do zarządzania domem inteligentnym, łączące nowoczesne technologie webowe z praktycznymi funkcjami automatyzacji domowej. Architektura modularna umożliwia łatwe rozszerzanie i dostosowywanie do indywidualnych potrzeb.

### Kluczowe Zalety:

1. **Bezpieczeństwo**: Wielopoziomowe zabezpieczenia
2. **Skalowalność**: Możliwość dodawania nowych funkcji
3. **Użyteczność**: Intuicyjny interfejs użytkownika
4. **Niezawodność**: Robustne obsługa błędów
5. **Wydajność**: Optymalizacja dla real-time communication

### Wartość Biznesowa:

- **Redukcja kosztów**: Automatyzacja zarządzania energią
- **Zwiększenie bezpieczeństwa**: Monitoring i alerty
- **Wygoda użytkowania**: Centralne sterowanie
- **Analityka**: Dane o użytkowaniu i wzorcach

System jest gotowy do wykorzystania w środowisku produkcyjnym i stanowi solidną podstawę do dalszego rozwoju funkcjonalności smart home.

---

**Autor**: Szymon Przybysz
**Data**: 2025
**Wersja**: 1.0
**Licencja**: MIT License
