# SmartHome - System Zarządzania Domem Inteligentnym

## Spis Treści

1. [Wprowadzenie](#wprowadzenie)
2. [Najnowsze Optymalizacje](#najnowsze-optymalizacje)
3. [Architektura Systemu](#architektura-systemu)
4. [Technologie i Narzędzia](#technologie-i-narzędzia)
5. [Struktura Projektu](#struktura-projektu)
6. [Funkcjonalności](#funkcjonalności)
7. [Bezpieczeństwo](#bezpieczeństwo)
8. [Interfejs Użytkownika](#interfejs-użytkownika)
9. [API i Komunikacja](#api-i-komunikacja)
10. [Baza Danych](#baza-danych)
11. [Konfiguracja i Uruchamianie](#konfiguracja-i-uruchamianie)
12. [Testy i Debugging](#testy-i-debugging)
13. [Rozszerzalność](#rozszerzalność)
14. [Potencjalne Usprawnienia](#potencjalne-usprawnienia)
15. [Podsumowanie](#podsumowanie)

---

## Wprowadzenie

SmartHome to kompleksowy system zarządzania domem inteligentnym, zaprojektowany jako aplikacja webowa wykorzystująca Flask (Python) z PostgreSQL backend oraz nowoczesne technologie frontendowe. System umożliwia kontrolę i monitorowanie różnych aspektów domu inteligentnego, w tym oświetlenia, temperatury, zabezpieczeń oraz automatyzacji.

### Główne Cele Projektu:

- **Wysoka Wydajność**: Template-level pre-loading i database connection pooling
- **Centralna kontrola**: Jednolity interfejs do zarządzania wszystkimi urządzeniami
- **Bezpieczeństwo**: Wielopoziomowe zabezpieczenia i system uwierzytelniania
- **Skalowalność**: PostgreSQL backend z connection pooling dla concurrent users
- **Dostępność**: Responsywny interfejs działający na różnych urządzeniach
- **Automatyzacja**: Inteligentne reguły i scenariusze automatyzacji

---

## Najnowsze Optymalizacje

### 🚀 Template-Level Pre-loading (Issue #49 Fix - Zaimplementowane ✅)

**Problem**: Admin dashboard ładował się zbyt wolno (>2.6 sekundy)
**Rozwiązanie**: Server-side pre-loading danych z JavaScript function override pattern
**Rezultat**: **70% poprawa wydajności (2.6s → 0.87s)**

**Implementacja**:

- **Admin dashboard**: Pre-loaded users, device states, management logs w `window.preloaded*` variables
- **Homepage**: Pre-loaded rooms list eliminuje initial AJAX call
- **Smart fallback**: Pre-loaded data dla initial load → API calls dla manual refreshes
- **Function overrides**: JavaScript functions detect pre-loaded data i używają go before falling back to API

**Techniczne szczegóły**:

- Template variables: `{{ users|tojson }}`, `{{ device_states|tojson }}`, `{{ management_logs|tojson }}`
- Override pattern dla `loadUsers()`, `refreshDeviceStates()`, `refreshLogs()`
- Initialization control w `dashboard.js` aby prevent conflicting auto-initialization

### 🗄️ PostgreSQL Backend Migration

**Zastąpienie**: JSON file storage → PostgreSQL database
**Korzyści**:

- Connection pooling (2-10 concurrent connections)
- Transactional data integrity
- Optimized queries z database indexing
- Better concurrent user support

### ⚡ Intelligent Caching System

**Implementacja**: Session-level user caching + Redis/SimpleCache support
**Cache Timeouts**:

- Session user data: 1 godzina
- General user data: 30 minut
- Room/device data: 10 minut
- API responses: 10 minut

### 📦 Asset Optimization

**Minifikacja**: CSS 36.7% smaller, JS 35.3% smaller
**Auto-serving**: Automatic minified asset detection i serving

---

## Architektura Systemu

### Wzorzec Architektoniczny: MVC (Model-View-Controller) z Database Backend

```
┌────────────────────────────────────────────────────────────────────┐
│                              PREZENTACJA                           │
├────────────────────────────────────────────────────────────────────┤
│  HTML Templates (Jinja2)   │  CSS (Minified)    │  JavaScript      │
│  - admin_dashboard.html    │  - style.min.css   │  - app.min.js    │
│  - index.html (pre-loaded) │  - mobile.css      │  - Socket.IO     │
│  - base.html               │  - user.css        │  - dashboard.js  │
│  - login.html              │  - dashboard.css   │  - automations.js│
└────────────────────────────────────────────────────────────────────┘
                                  ↕
┌───────────────────────────────────────────────────────────────────┐
│                              KONTROLER                            │
├───────────────────────────────────────────────────────────────────┤
│  Flask Routes (app/routes.py)   │  Pre-loading Optimization       │
│  - Template pre-loading         │  - Session-level caching        │
│  - Database-backed operations   │  - Smart fallback patterns      │
│  - Admin dashboard optimization │ - Connection pool management    │
└───────────────────────────────────────────────────────────────────┘
                                  ↕

┌───────────────────────────────────────────────────────────────────┐
│                             KONTROLER                             │
├───────────────────────────────────────────────────────────────────┤
│  Flask Routes                  │  WebSocket Handlers              │
│  - RoutesManager               │  - SocketManager                 │
│  - APIManager                  │  - Real-time Communication       │
│  - AuthManager                 │  - Live Updates                  │
└───────────────────────────────────────────────────────────────────┘
                                  ↕
┌───────────────────────────────────────────────────────────────────┐
│                      MODEL (DATABASE BACKEND)                     │
├───────────────────────────────────────────────────────────────────┤
│  PostgreSQL Database          │  Connection Management            │
│  - SmartHomeDatabaseManager   │  - ThreadedConnectionPool         │  
│  - User/Room/Device tables    │  - Session-level caching          │
│  - Management logs            │  - Transaction handling           │
│  - Automation rules           │  - Cache invalidation             │
└───────────────────────────────────────────────────────────────────┘
```

### Komponenty Systemu:

#### 1. **Frontend (Warstwa Prezentacji)**

- **HTML Templates**: Dynamicznie generowane strony z server-side pre-loading
- **CSS**: Responsywny design z minifikacją (36.7% smaller)
- **JavaScript**: Pre-loaded data patterns, real-time updates, optimized loading

#### 2. **Backend (Warstwa Biznesowa)**

- **Flask Application**: Database-backed aplikacja z connection pooling
- **Route Managers**: Pre-loading optimization i session-level caching
- **WebSocket Handlers**: Real-time komunikacja z user state management
- **Business Logic**: Database transactions z automatic rollback

#### 3. **Data Layer (PostgreSQL Backend)**

- **PostgreSQL Database**: Persistent storage z transaction support
- **Connection Pool**: 2-10 concurrent connections z automatic management
- **Caching Layer**: Session-level i Redis/SimpleCache support
- **Migration System**: Automatic JSON → Database migration tools

---

## Technologie i Narzędzia

### Backend Technologies:

- **Python 3.x**: Główny język programowania
- **Flask 3.1.0**: Framework webowy z database integration
- **Flask-SocketIO 5.5.0**: Real-time komunikacja
- **PostgreSQL**: Production database backend
- **psycopg2-binary 2.9.10**: PostgreSQL driver z connection pooling
- **Flask-Caching 2.3.1**: Intelligent caching system
- **Redis**: Optional cache backend (fallback: SimpleCache)
- **Werkzeug 3.1.3**: WSGI toolkit
- **Jinja2 3.1.5**: Template engine z server-side pre-loading
- **Cryptography 44.0.0**: Szyfrowanie danych
- **python-dotenv**: Environment configuration management

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

## Struktura Projektu (uproszczona)

```
Site_proj/
├── app/                       # Główna aplikacja (app_db.py, routes.py, itd.)
├── utils/                     # Narzędzia (cache, async, asset_manager)
├── static/                    # Pliki statyczne (CSS, JS, ikony)
├── templates/                 # Szablony HTML (Jinja2)
├── info/                      # Dokumentacja, wymagania, quick start
├── .env                       # Zmienne środowiskowe
└── ...                        # Pozostałe pliki konfiguracyjne
```

---

## Szybki Start

1. Skonfiguruj `.env` (baza danych, email)
2. Zainstaluj zależności: `pip install -r info/requirements.txt`
3. Minifikuj zasoby: `python utils/asset_manager.py`
4. Uruchom aplikację:
   - Windows (Waitress):
     `python -m waitress --port=5000 app_db:main`
   - Linux (Gunicorn):
     `gunicorn -w 4 -b 0.0.0.0:5000 'app_db:main'`
5. Wejdź na: http://localhost:5000

---

**Optymalizacja wydajności**: patrz `PERFORMANCE_OPTIMIZATION.md i LATEST_OPTIMIZATIONS.md `

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

#### Sposób 1: Skrypt uruchamiający (Windows - zalecane)

```bash
# Podstawowe uruchomienie
python run_server.py

# Z trybem debug
python run_server.py --debug

# Z innym portem
python run_server.py --port 5000
```

#### Sposób 2: Bezpośrednio przez Flask

```bash
# Tryb rozwojowy
python app.py

# Tryb produkcyjny
python -m flask run --host=0.0.0.0 --port=5000
```

#### Sposób 3: Gunicorn (tylko Linux/Unix)

```bash
# Nie działa na Windows ze względu na brak modułu fcntl
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

#### Sposób 4: Używając pliku .bat (Windows)

```bash
run_server.bat
```

#### Sposób 5: Wersja produkcyjna z gevent

```bash
python run_server_gevent.py
```

#### Problemy z Gunicorn na Windows:

Gunicorn używa modułu `fcntl` który nie jest dostępny na Windows. Błąd:

```
ModuleNotFoundError: No module named 'fcntl'
```

**Rozwiązanie**: Używaj `run_server.py` który został specjalnie przygotowany dla Windows.

#### Skrypt run_server.py:

```python
#!/usr/bin/env python3
"""
Skrypt uruchamiający serwer Smart Home
Dostosowany do środowiska Windows z obsługą SocketIO
"""
import os
import sys
from app import app, socketio

def main():
    """Główna funkcja uruchamiająca serwer"""
    print("=== Smart Home Server ===")
    print("Uruchamianie serwera...")
  
    # Sprawdzenie konfiguracji
    config_files = [
        'smart_home_config.json',
        'notifications_settings.json'
    ]
  
    for config_file in config_files:
        if not os.path.exists(config_file):
            print(f"UWAGA: Plik konfiguracyjny {config_file} nie istnieje")
  
    # Parametry serwera
    host = "0.0.0.0"
    port = 5000
    debug = False
  
    # Argumenty wiersza poleceń
    if "--debug" in sys.argv:
        debug = True
    if "--port" in sys.argv:
        port_idx = sys.argv.index("--port")
        port = int(sys.argv[port_idx + 1])
  
    # Uruchomienie serwera SocketIO
    socketio.run(
        app, 
        debug=debug, 
        host=host, 
        port=port,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )

if __name__ == "__main__":
    sys.exit(main())
```

#### Systemd Service (Linux):

```ini
[Unit]
Description=SmartHome Application
After=network.target

[Service]
Type=simple
User=smarthome
WorkingDirectory=/path/to/smarthome
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. **Weryfikacja Instalacji**

#### Sprawdzenie Uruchomienia:

1. **Otwórz przeglądarkę**: `http://localhost:5000`
2. **Sprawdź logi**: Brak błędów w konsoli
3. **Test logowania**: Użyj domyślnych danych
4. **Test funkcji**: Sprawdź przełączanie urządzeń

#### Debugging:

```bash
# Sprawdź porty
netstat -an | findstr :5000

# Sprawdź logi
python run_server.py --debug

# Sprawdź konfigurację
python -c "import json; print(json.load(open('smart_home_config.json')))"
```

#### Rozwiązywanie Problemów:

**Problem**: `ModuleNotFoundError: No module named 'fcntl'`
**Rozwiązanie**: Używaj `run_server.py` zamiast Gunicorn na Windows

**Problem**: Błąd WebSocket przy użyciu Waitress
**Rozwiązanie**: Używaj `run_server.py` lub `run_server_gevent.py`

**Problem**: Serwer nie odpowiada
**Rozwiązanie**:

- Sprawdź czy port 5000 jest wolny
- Sprawdź firewall
- Uruchom z `--debug` dla szczegółów

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

## Troubleshooting

### Problem z Gradle w Android App

**Error**: `Dependency requires at least JVM runtime version 11. This build uses a Java 8 JVM.`

**Rozwiązanie**:

1. **Downgrade Gradle** (zalecane dla Java 8):

   - Zmień `android_app/build.gradle`: `id 'com.android.application' version '8.0.2'`
   - Zmień `android_app/gradle/wrapper/gradle-wrapper.properties`: `gradle-8.0.2-bin.zip`
2. **Alternatywnie - Upgrade Java** (jeśli możesz):

   - Zainstaluj Java 11 lub nowszą
   - Ustaw `JAVA_HOME` na nową wersję Java

### Performance Issues

**Problem**: Wolne ładowanie admin dashboard
**Rozwiązanie**: Sprawdź czy pre-loaded data optimization działa:

- DevTools Console powinien pokazać "Using pre-loaded ... data"
- Network tab nie powinien pokazywać redundant API calls
- Page load < 1 sekunda

**Problem**: Database connection errors
**Rozwiązanie**: Sprawdź PostgreSQL connection i environment variables:

```bash
export DB_HOST="localhost"
export DB_NAME="smart_home"
export DB_USER="username"
export DB_PASSWORD="password"
```

---

## Podsumowanie

System SmartHome reprezentuje kompleksowe rozwiązanie do zarządzania domem inteligentnym, łączące nowoczesne technologie webowe z praktycznymi funkcjami automatyzacji domowej. Architektura modularna umożliwia łatwe rozszerzanie i dostosowywanie do indywidualnych potrzeb.

### Kluczowe Zalety:

1. **Bezpieczeństwo**: Wielopoziomowe zabezpieczenia
2. **Skalowalność**: Możliwość dodawania nowych funkcji
3. **Użyteczność**: Intuicyjny interfejs użytkownika
4. **Niezawodność**: Robustne obsługa błędów
5. **Wydajność**: Optymalizacja dla real-time communication
6. **Kompatybilność**: Działa na Windows, Linux, macOS
7. **Rozszerzalność**: Plugin system i API integration

### Wartość Biznesowa:

- **Redukcja kosztów**: Automatyzacja zarządzania energią
- **Zwiększenie bezpieczeństwa**: Monitoring i alerty
- **Wygoda użytkowania**: Centralne sterowanie
- **Analityka**: Dane o użytkowaniu i wzorcach

### Wdrożenie Produkcyjne:

System jest gotowy do wykorzystania w środowisku produkcyjnym. Skrypt `run_server.py` umożliwia łatwe uruchomienie na systemach Windows, rozwiązując problemy z kompatybilnością Gunicorn. Dla środowisk Linux/Unix można wykorzystać standardowe narzędzia WSGI.

### Rozwiązanie Problemów z Windows:

- **Gunicorn**: Niekompatybilny z Windows (brak modułu fcntl)
- **Waitress**: Problemy z WebSocket'ami przy SocketIO
- **Rozwiązanie**: Dedykowany skrypt `run_server.py` z pełnym wsparciem dla Windows

System stanowi solidną podstawę do dalszego rozwoju funkcjonalności smart home i może być łatwo dostosowany do specyficznych wymagań użytkowników.

---

**Autor**: [Twoje Imię]
**Data**: 2025
**Wersja**: 1.0
**Technologie**: Python, Flask, JavaScript, HTML/CSS
**Licencja**: MIT License

**Autor**: Szymon Przybysz
**Data**: 2025
**Wersja**: 1.0
**Licencja**: MIT License
