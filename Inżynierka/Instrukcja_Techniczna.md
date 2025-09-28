# Instrukcja Techniczna - System SmartHome

## Spis treści

1. [Wymagania Systemowe](#1-wymagania-systemowe)
2. [Instalacja i Konfiguracja](#2-instalacja-i-konfiguracja)
3. [Architektura Kodu](#3-architektura-kodu)
4. [API Reference](#4-api-reference)
5. [Baza Danych](#5-baza-danych)
6. [Konfiguracja Środowiska](#6-konfiguracja-środowiska)
7. [Deployment](#7-deployment)
8. [Troubleshooting](#8-troubleshooting)
9. [Monitoring i Logowanie](#9-monitoring-i-logowanie)
10. [Backup i Recovery](#10-backup-i-recovery)

---

## 1. Wymagania Systemowe

### 1.1 Środowisko Deweloperskie

#### Minimalne wymagania:

- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.10 lub nowszy
- **RAM**: 4GB (8GB rekomendowane)
- **Disk**: 2GB wolnego miejsca
- **CPU**: 2 cores (4 cores rekomendowane)

#### Opcjonalne komponenty:

- **PostgreSQL**: 13+ (dla production)
- **Redis**: 6+ (dla cache'owania)
- **Docker**: 20+ (dla konteneryzacji)
- **Node.js**: 16+ (dla asset management)

### 1.2 Środowisko Produkcyjne

#### Minimalne wymagania:

- **OS**: Ubuntu 20.04 LTS, CentOS 8+, RHEL 8+
- **RAM**: 8GB (16GB rekomendowane)
- **CPU**: 4 cores (8 cores rekomendowane)
- **Disk**: 50GB SSD
- **Network**: 100Mbps

#### Wymagane usługi:

- **PostgreSQL**: 13+ z odpowiednią konfiguracją
- **Redis**: 6+ dla cache'a i sesji
- **Nginx**: 1.18+ jako reverse proxy
- **SSL Certificate**: Let's Encrypt lub komercyjny

---

## 2. Instalacja i Konfiguracja

### 2.1 Klonowanie Repozytorium

```bash
# Klonowanie repozytorium
git clone https://github.com/AdasRakieta/Site_proj
cd Site_proj

# Sprawdzenie dostępnych branchy
git branch -a
```

### 2.2 Konfiguracja Python Environment

```bash
# Tworzenie środowiska wirtualnego
python3 -m venv .venv

# Aktywacja środowiska (Linux/Mac)
source .venv/bin/activate

# Aktywacja środowiska (Windows)
.venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Instalacja zależności
pip install -r requirements.txt
```

### 2.3 Konfiguracja Bazy Danych

#### PostgreSQL Setup:

```bash
# Instalacja PostgreSQL (Ubuntu)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Tworzenie użytkownika i bazy danych
sudo -u postgres psql

CREATE USER admin WITH PASSWORD 'secure_password';
CREATE DATABASE admin OWNER admin;
GRANT ALL PRIVILEGES ON DATABASE admin TO admin;

# Instalacja rozszerzeń (wymagane)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS plpgsql;
\q

# Import pełnego schematu (12 tabel + indeksy + triggery)
psql -h localhost -U admin -d admin -f backups/db_backup.sql
```

#### Redis Setup:

```bash
# Instalacja Redis (Ubuntu)
sudo apt install redis-server

# Konfiguracja Redis
sudo nano /etc/redis/redis.conf

# Dodaj następujące linie:
maxmemory 256mb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

### 2.4 Konfiguracja Środowiska

```bash
# Kopiowanie template konfiguracji
cp .env.example .env

# Edycja konfiguracji
nano .env
```

Przykładowy plik `.env`:

```env
# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

# Database Configuration (PostgreSQL 17.5)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=admin
DB_USER=admin
DB_PASSWORD=secure_password
DB_POOL_MIN=2
DB_POOL_MAX=10

# Redis Configuration (Optional - fallback to SimpleCache)
REDIS_URL=redis://localhost:6379/0

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-here
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourdomain.com

# Security
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### 2.5 Pierwszez Uruchomienie

```bash
# Weryfikacja konfiguracji
python -c "from app_db import SmartHomeApp; print('Configuration OK')"

# Uruchomienie aplikacji
python app_db.py

# Aplikacja powinna być dostępna na http://localhost:5000
```

---

## 3. Architektura Kodu

### 3.1 Struktura Katalogów

```
smarthome/
├── app_db.py                     # Główny punkt wejścia
├── requirements.txt              # Zależności Python
├── .env.example                  # Template konfiguracji
├── docker-compose.yml            # Docker compose development
├── docker-compose.prod.yml       # Docker compose production
├── Dockerfile.app                # Docker image dla aplikacji
│
├── app/                          # Główna logika aplikacji
│   ├── __init__.py
│   ├── configure.py              # Konfiguracja JSON fallback
│   ├── configure_db.py           # Konfiguracja PostgreSQL
│   ├── routes.py                 # Zarządzanie trasami HTTP/WS
│   ├── simple_auth.py            # System uwierzytelniania
│   ├── mail_manager.py           # Zarządzanie emailami
│   ├── management_logger.py      # Logowanie administracyjne
│   ├── database_management_logger.py  # DB logging
│   └── config_manager.py         # Zarządzanie konfiguracją
│
├── utils/                        # Narzędzia pomocnicze
│   ├── __init__.py
│   ├── smart_home_db_manager.py  # Manager bazy danych
│   ├── cache_manager.py          # System cache'owania
│   ├── asset_manager.py          # Minifikacja zasobów
│   ├── async_manager.py          # Zadania asynchroniczne
│   ├── db_manager.py             # Połączenia DB
│   └── allowed_file.py           # Walidacja plików
│
├── templates/                    # Szablony HTML (Jinja2)
│   ├── base.html                 # Szablon bazowy
│   ├── index.html               # Dashboard główny
│   ├── login.html               # Strona logowania
│   ├── register.html            # Rejestracja użytkownika
│   ├── admin_dashboard.html     # Panel administratora
│   ├── automations.html         # Zarządzanie automatyzacjami
│   ├── settings.html            # Ustawienia użytkownika
│   └── error.html               # Obsługa błędów
│
├── static/                       # Zasoby statyczne
│   ├── css/                     # Arkusze stylów
│   │   ├── style.css           # Główne style
│   │   ├── dashboard.css       # Style dashboard
│   │   ├── mobile.css          # Style mobilne
│   │   └── min/                # Zminifikowane CSS
│   ├── js/                      # Skrypty JavaScript
│   │   ├── app.js              # Główna logika JS
│   │   ├── dashboard.js        # Dashboard functionality
│   │   ├── automations.js      # Automations UI
│   │   └── min/                # Zminifikowane JS
│   ├── icons/                   # Ikony interfejsu
│   └── profile_pictures/        # Zdjęcia profilowe
│
├── backups/                      # Kopie zapasowe i schema
│   ├── db_backup.sql            # Pełny schemat bazy
│   └── config_backup.json       # Backup konfiguracji
│
├── info/                         # Dokumentacja operacyjna
│   ├── QUICK_START.md           # Szybki start
│   └── PERFORMANCE_OPTIMIZATION.md  # Optymalizacje
│
├── nginx/                        # Konfiguracja Nginx
│   ├── Dockerfile               # Nginx Docker image
│   ├── nginx.conf              # Główna konfiguracja
│   └── ssl/                    # Certyfikaty SSL
│
└── scripts/                      # Skrypty pomocnicze
    ├── backup_database.sh       # Backup bazy danych
    ├── health_check.py         # Monitoring zdrowia systemu
    └── deploy.sh               # Skrypt wdrożenia
```

### 3.2 Kluczowe Klasy i Moduły

#### 3.2.1 SmartHomeApp (app_db.py)

```python
class SmartHomeApp:
    """Main SmartHome application class with database integration"""
  
    def __init__(self):
        # Inicjalizacja Flask app
        # Konfiguracja bezpieczeństwa
        # Setup Socket.IO
        # Inicjalizacja komponentów
      
    def initialize_components(self):
        # Inicjalizacja SmartHome Core
        # Setup Cache Manager
        # Setup Auth Manager
        # Setup Mail Manager
      
    def setup_routes(self):
        # Rejestracja tras HTTP
        # Setup Routes Manager
      
    def setup_socket_events(self):
        # Obsługa WebSocket events
        # Real-time communication
```

#### 3.2.2 SmartHomeDatabaseManager (utils/smart_home_db_manager.py)

```python
class SmartHomeDatabaseManager:
    """PostgreSQL Database Manager for SmartHome System"""
  
    def __init__(self, db_config=None):
        # Konfiguracja połączenia
        # Inicjalizacja connection pool
      
    # User Management
    def create_user(self, name, email, password_hash, role='user')
    def get_user_by_id(self, user_id)
    def get_user_by_email(self, email)
    def update_user(self, user_id, updates)
    def delete_user(self, user_id)
  
    # Device Management  
    def create_device(self, name, room_id, device_type, **kwargs)
    def get_device_by_id(self, device_id)
    def update_device_state(self, device_id, state)
    def get_devices_by_room(self, room_id)
  
    # Room Management
    def create_room(self, name, display_order=0)
    def get_all_rooms(self)
    def update_room(self, room_id, updates)
  
    # Automation Management
    def create_automation(self, name, trigger_config, actions_config)
    def get_automation_by_id(self, automation_id)
    def execute_automation(self, automation_id)
    def log_automation_execution(self, automation_id, status, details)
```

#### 3.2.3 CacheManager (utils/cache_manager.py)

```python
class CacheManager:
    """Advanced caching system with Redis/SimpleCache fallback"""
  
    def __init__(self, cache, smart_home):
        # Cache configuration
        # Timeout settings
      
    def get_session_user_data(self, user_id, session_id=None):
        # Session-level caching
        # User data optimization
      
    def invalidate_user_cache(self, user_id):
        # Cache invalidation
        # Pattern-based cleanup
      
    def get_api_response_cache(self, endpoint, params):
        # API response caching
        # Performance optimization
```

#### 3.2.4 RoutesManager (app/routes.py)

```python
class RoutesManager:
    """Centralized routes and WebSocket management"""
  
    def __init__(self, app, smart_home, auth_manager, ...):
        # Component initialization
      
    def register_routes(self):
        # HTTP routes registration
        # Authentication routes
        # API endpoints
        # WebSocket handlers
      
    def _send_verification_code(self, data):
        # Email verification process
      
    def _verify_and_register(self, data):
        # User registration completion
      
    def emit_update(self, event_name, data):
        # WebSocket broadcasting
```

---

## 4. API Reference

### 4.1 Authentication API

#### POST /login

Uwierzytelnienie użytkownika

**Request:**

```json
{
    "username": "admin",
    "password": "admin123"
}
```

**Response (Success):**

```json
{
    "status": "success",
    "message": "Zalogowano pomyślnie",
    "user": {
        "id": "uuid",
        "name": "admin",
        "role": "admin"
    }
}
```

**Response (Error):**

```json
{
    "status": "error",
    "message": "Nieprawidłowe dane logowania"
}
```

#### POST /register

Rejestracja nowego użytkownika (dwuetapowa)

**Krok 1 - Wysłanie kodu weryfikacyjnego:**

```json
{
    "username": "newuser",
    "email": "user@example.com",
    "password": "password123"
}
```

**Krok 2 - Weryfikacja kodu:**

```json
{
    "username": "newuser", 
    "email": "user@example.com",
    "password": "password123",
    "verification_code": "123456"
}
```

#### POST /logout

Wylogowanie użytkownika (wymaga zalogowania)

### 4.2 System API

#### GET /api/ping

Health check endpoint

**Response:**

```json
{
    "status": "ok",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0"
}
```

#### GET /api/status

Status systemu

**Response:**

```json
{
    "status": "running",
    "database_mode": true,
    "cache_type": "RedisCache",
    "rooms_count": 5,
    "devices_count": 23,
    "automations_count": 8
}
```

#### GET /api/cache/stats

Statystyki cache'a (wymaga zalogowania)

**Response:**

```json
{
    "hit_rate": 78.5,
    "total_requests": 10000,
    "hits": 7850,
    "misses": 2150
}
```

### 4.3 Device Management API

#### GET /api/devices

Lista wszystkich urządzeń

**Response:**

```json
{
    "devices": [
        {
            "id": "uuid",
            "name": "Living Room Light",
            "room_id": "room-uuid",
            "device_type": "button",
            "state": true,
            "enabled": true
        }
    ]
}
```

#### PUT /api/devices/

Aktualizacja stanu urządzenia

**Request:**

```json
{
    "state": true,
    "temperature": 22.5
}
```

### 4.4 WebSocket Events

#### Client → Server Events

**toggle_button:**

```json
{
    "button_id": "device-uuid"
}
```

**set_temperature:**

```json
{
    "control_id": "device-uuid",
    "temperature": 22.5
}
```

**set_security_state:**

```json
{
    "state": "armed",
    "zones": ["zone1", "zone2"]
}
```

#### Server → Client Events

**system_state:**

```json
{
    "rooms": [...],
    "buttons": [...],
    "temperature_controls": [...],
    "automations": [...],
    "security_state": {...}
}
```

**device_updated:**

```json
{
    "device_id": "uuid",
    "state": true,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

**automation_executed:**

```json
{
    "automation_id": "uuid",
    "name": "Evening Lights",
    "status": "success",
    "executed_at": "2024-01-15T18:00:00Z"
}
```

---

## 5. Baza Danych

### 5.1 Schemat Tabel

#### Tabela users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    profile_picture TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabela rooms

```sql
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabela devices

```sql
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    device_type VARCHAR(50) NOT NULL CHECK (device_type IN ('button', 'temperature_control')),
    state BOOLEAN DEFAULT FALSE,
    temperature NUMERIC(5,2) DEFAULT 22.0,
    min_temperature NUMERIC(5,2) DEFAULT 16.0, 
    max_temperature NUMERIC(5,2) DEFAULT 30.0,
    display_order INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabela automations

```sql
CREATE TABLE automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    trigger_config JSONB NOT NULL,
    actions_config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    last_executed TIMESTAMP WITH TIME ZONE,
    execution_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    last_error_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 5.2 Indeksy

```sql
-- Performance indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_name ON users(name);
CREATE INDEX idx_devices_room_id ON devices(room_id);
CREATE INDEX idx_devices_type ON devices(device_type);
CREATE INDEX idx_automations_enabled ON automations(enabled);
CREATE INDEX idx_management_logs_timestamp ON management_logs(timestamp);
CREATE INDEX idx_management_logs_user_id ON management_logs(user_id);
```

### 5.3 Triggery

```sql
-- Automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rooms_updated_at 
    BEFORE UPDATE ON rooms 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_devices_updated_at 
    BEFORE UPDATE ON devices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_automations_updated_at 
    BEFORE UPDATE ON automations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 5.4 Przykładowe Zapytania

#### Pobranie wszystkich urządzeń z nazwami pokoi:

```sql
SELECT 
    d.id,
    d.name,
    d.device_type,
    d.state,
    d.temperature,
    r.name as room_name
FROM devices d
LEFT JOIN rooms r ON d.room_id = r.id
WHERE d.enabled = true
ORDER BY r.display_order, d.display_order;
```

#### Statystyki urządzeń według pokoi:

```sql
SELECT 
    r.name as room_name,
    COUNT(d.id) as device_count,
    COUNT(CASE WHEN d.state = true THEN 1 END) as active_devices,
    AVG(CASE WHEN d.device_type = 'temperature_control' THEN d.temperature END) as avg_temperature
FROM rooms r
LEFT JOIN devices d ON r.id = d.room_id
WHERE d.enabled = true
GROUP BY r.id, r.name
ORDER BY r.display_order;
```

#### Historia wykonania automatyzacji:

```sql
SELECT 
    a.name,
    ae.execution_status,
    ae.execution_time_ms,
    ae.executed_at
FROM automation_executions ae
JOIN automations a ON ae.automation_id = a.id
WHERE ae.executed_at >= NOW() - INTERVAL '24 hours'
ORDER BY ae.executed_at DESC;
```

---

## 6. Konfiguracja Środowiska

### 6.1 Zmienne Środowiskowe

#### Database Configuration

```env
DB_HOST=localhost                 # PostgreSQL host
DB_PORT=5432                     # PostgreSQL port
DB_NAME=smarthome                # Database name
DB_USER=smartuser                # Database user
DB_PASSWORD=secure_password      # Database password
DB_POOL_MIN=2                    # Minimum connections in pool
DB_POOL_MAX=10                   # Maximum connections in pool
```

#### Redis Configuration

```env
REDIS_URL=redis://localhost:6379/0    # Full Redis URL
# OR individual settings:
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                       # Optional password
```

#### Flask Configuration

```env
FLASK_ENV=development            # development/production
SECRET_KEY=your-secret-key       # Session encryption key
SERVER_HOST=0.0.0.0             # Server bind address
SERVER_PORT=5000                # Server port
```

#### Security Configuration

```env
SESSION_COOKIE_SECURE=False     # True for HTTPS only
SESSION_COOKIE_HTTPONLY=True    # Prevent XSS
SESSION_COOKIE_SAMESITE=Lax     # CSRF protection
```

#### Email Configuration

```env
SMTP_SERVER=smtp.gmail.com      # SMTP server
SMTP_PORT=587                   # SMTP port
SMTP_USERNAME=your@email.com    # SMTP username
SMTP_PASSWORD=app-password      # SMTP password (app password for Gmail)
ADMIN_EMAIL=admin@domain.com    # Admin email for notifications
```

### 6.2 Konfiguracja Rozwojowa

#### Development Settings (.env.development)

```env
FLASK_ENV=development
DEBUG=True
DB_HOST=localhost
REDIS_URL=redis://localhost:6379/0
SMTP_SERVER=localhost
SMTP_PORT=1025
LOG_LEVEL=DEBUG
```

#### Testing Settings (.env.testing)

```env
FLASK_ENV=testing
DB_NAME=smarthome_test
REDIS_URL=redis://localhost:6379/1
TESTING=True
WTF_CSRF_ENABLED=False
```

### 6.3 Konfiguracja Produkcyjna

#### Production Settings (.env.production)

```env
FLASK_ENV=production
DEBUG=False
DB_HOST=postgres-server
DB_PASSWORD=very-secure-password
REDIS_URL=redis://redis-server:6379/0
SESSION_COOKIE_SECURE=True
SMTP_SERVER=smtp.production.com
LOG_LEVEL=INFO
```

---

## 7. Deployment

### 7.1 Docker Deployment

#### Development Environment

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop environment
docker-compose down
```

#### Production Environment

```bash
# Build and start production environment
docker-compose -f docker-compose.prod.yml up -d --build

# Scale application
docker-compose -f docker-compose.prod.yml up -d --scale app=3

# Update application
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### 7.2 Manual Deployment

#### System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv postgresql redis-server nginx

# Create application user
sudo useradd -m -s /bin/bash smarthome
sudo su - smarthome
```

#### Application Setup

```bash
# Clone and setup application
git clone https://github.com/your-repo/smarthome.git
cd smarthome
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env

# Setup database
sudo -u postgres createuser smarthome
sudo -u postgres createdb smarthome -O smarthome
psql -U smarthome -d smarthome -f backups/db_backup.sql
```

#### Service Configuration

```bash
# Create systemd service
sudo nano /etc/systemd/system/smarthome.service
```

```ini
[Unit]
Description=SmartHome Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=smarthome
WorkingDirectory=/home/smarthome/smarthome
Environment=PATH=/home/smarthome/smarthome/.venv/bin
ExecStart=/home/smarthome/smarthome/.venv/bin/python app_db.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable smarthome
sudo systemctl start smarthome

# Check status
sudo systemctl status smarthome
```

### 7.3 Nginx Configuration

```nginx
# /etc/nginx/sites-available/smarthome
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
  
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
  
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
  
    # Static files
    location /static/ {
        alias /home/smarthome/smarthome/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
  
    # WebSocket proxy
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
  
    # Main application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/smarthome /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 8. Troubleshooting

### 8.1 Najczęstsze Problemy

#### Problem: Application nie startuje

**Objawy:**

- Błąd przy uruchomieniu `python app_db.py`
- ImportError lub ModuleNotFoundError

**Rozwiązanie:**

```bash
# Sprawdź czy virtual environment jest aktywny
which python
# Should return path with .venv

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check Python version
python --version
# Should be 3.10+
```

#### Problem: Database connection failed

**Objawy:**

- "⚠ Failed to import database backend"
- Application falls back to JSON mode

**Rozwiązanie:**

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U smartuser -d smarthome -c "SELECT 1;"

# Check .env configuration
grep DB_ .env

# Verify database exists
sudo -u postgres psql -c "\l" | grep smarthome
```

#### Problem: Redis connection failed

**Objawy:**

- "⚠ Redis unavailable, falling back to SimpleCache"
- Cache hit rate bardzo niski

**Rozwiązanie:**

```bash
# Check Redis status
sudo systemctl status redis

# Test Redis connection
redis-cli ping
# Should return PONG

# Check Redis configuration
redis-cli CONFIG GET maxmemory
```

#### Problem: WebSocket connection failed

**Objawy:**

- Real-time updates nie działają
- JavaScript console errors

**Rozwiązanie:**

```javascript
// Check browser console for WebSocket errors
// Verify Socket.IO is loaded
console.log(typeof io);  // Should return 'function'

// Check network tab for WebSocket upgrade
// Look for 101 Switching Protocols response
```

### 8.2 Diagnostyka

#### System Health Check

```bash
# Run built-in health check
python scripts/health_check.py

# Check system resources
df -h                    # Disk space
free -h                  # Memory usage
top                      # CPU usage

# Check service status
sudo systemctl status smarthome
sudo systemctl status postgresql
sudo systemctl status redis
sudo systemctl status nginx
```

#### Database Diagnostics

```sql
-- Check database connections
SELECT pid, usename, application_name, client_addr, state 
FROM pg_stat_activity 
WHERE datname = 'smarthome';

-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check recent errors
SELECT * FROM pg_stat_database WHERE datname = 'smarthome';
```

#### Cache Diagnostics

```bash
# Redis info
redis-cli INFO memory
redis-cli INFO stats

# Check cache keys
redis-cli KEYS "*"

# Monitor Redis operations
redis-cli MONITOR
```

### 8.3 Performance Issues

#### Slow Database Queries

```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

#### High Memory Usage

```bash
# Check Python memory usage
ps aux | grep python | grep app_db.py

# Monitor memory over time
while true; do
    ps -o pid,rss,command -p $(pgrep -f app_db.py)
    sleep 5
done
```

#### High CPU Usage

```bash
# Profile application
pip install py-spy
py-spy top --pid $(pgrep -f app_db.py)

# Generate flame graph
py-spy record -o profile.svg --pid $(pgrep -f app_db.py) --duration 60
```

---

## 9. Monitoring i Logowanie

### 9.1 Application Logging

#### Log Levels

```python
# app_db.py logging configuration
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/smarthome/app.log'),
        logging.StreamHandler()
    ]
)
```

#### Log Locations

```bash
# Application logs
tail -f /var/log/smarthome/app.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# PostgreSQL logs
tail -f /var/log/postgresql/postgresql-13-main.log

# Redis logs
tail -f /var/log/redis/redis-server.log

# System logs
journalctl -u smarthome -f
```

### 9.2 Monitoring Metrics

#### Application Metrics

```python
# Custom metrics endpoint
@app.route('/metrics')
def metrics():
    return {
        'active_connections': len(connected_users),
        'cache_hit_rate': get_cache_hit_rate(),
        'database_connections': db_manager.get_active_connections(),
        'memory_usage': get_memory_usage(),
        'uptime': get_uptime()
    }
```

#### System Monitoring Script

```bash
#!/bin/bash
# scripts/monitor.sh

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is $DISK_USAGE%"
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEM_USAGE -gt 80 ]; then
    echo "WARNING: Memory usage is $MEM_USAGE%"
fi

# Check service status
if ! systemctl is-active --quiet smarthome; then
    echo "ERROR: SmartHome service is not running"
fi

# Check database connectivity
if ! pg_isready -h localhost -U smartuser >/dev/null 2>&1; then
    echo "ERROR: Cannot connect to PostgreSQL"
fi

# Check Redis connectivity
if ! redis-cli ping >/dev/null 2>&1; then
    echo "ERROR: Cannot connect to Redis"
fi
```

### 9.3 Alerting

#### Email Alerts Setup

```python
# utils/alerting.py
import smtplib
from email.mime.text import MIMEText

def send_alert(subject, message):
    """Send alert email to administrators"""
    try:
        msg = MIMEText(message)
        msg['Subject'] = f"SmartHome Alert: {subject}"
        msg['From'] = os.getenv('SMTP_USERNAME')
        msg['To'] = os.getenv('ADMIN_EMAIL')
      
        server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
    except Exception as e:
        logging.error(f"Failed to send alert email: {e}")
```

#### Automated Monitoring

```bash
# Add to crontab (crontab -e)
# Check every 5 minutes
*/5 * * * * /home/smarthome/smarthome/scripts/monitor.sh

# Health check every minute
* * * * * /home/smarthome/smarthome/.venv/bin/python /home/smarthome/smarthome/scripts/health_check.py

# Daily backup
0 2 * * * /home/smarthome/smarthome/scripts/backup_database.sh
```

---

## 10. Backup i Recovery

### 10.1 Database Backup

#### Automated Backup Script

```bash
#!/bin/bash
# scripts/backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/smarthome/backups"
DB_NAME="smarthome"
DB_USER="smartuser"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/backup_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/backup_$DATE.sql"

# Keep only last 30 backups
find $BACKUP_DIR -name "backup_*.sql.gz" -type f -mtime +30 -delete

# Log backup completion
echo "$(date): Database backup completed: backup_$DATE.sql.gz" >> $BACKUP_DIR/backup.log
```

#### Manual Backup

```bash
# Full database backup
pg_dump -h localhost -U smartuser -d smarthome > backup_$(date +%Y%m%d).sql

# Schema only backup
pg_dump -h localhost -U smartuser -d smarthome --schema-only > schema_backup.sql

# Specific table backup
pg_dump -h localhost -U smartuser -d smarthome -t users > users_backup.sql
```

### 10.2 Application Backup

#### Configuration Backup

```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    .env \
    /etc/nginx/sites-available/smarthome \
    /etc/systemd/system/smarthome.service

# Backup application logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz /var/log/smarthome/
```

#### Static Files Backup

```bash
# Backup uploaded files and assets
tar -czf static_backup_$(date +%Y%m%d).tar.gz \
    static/profile_pictures/ \
    static/uploads/
```

### 10.3 Recovery Procedures

#### Database Recovery

```bash
# Stop application
sudo systemctl stop smarthome

# Drop existing database (if needed)
sudo -u postgres psql -c "DROP DATABASE IF EXISTS smarthome;"
sudo -u postgres psql -c "CREATE DATABASE smarthome OWNER smartuser;"

# Restore from backup
gunzip -c backup_20240115_020000.sql.gz | psql -h localhost -U smartuser -d smarthome

# Start application
sudo systemctl start smarthome
```

#### Full System Recovery

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql redis-server nginx

# 2. Restore application code
git clone https://github.com/your-repo/smarthome.git
cd smarthome
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Restore configuration
tar -xzf config_backup_20240115.tar.gz

# 4. Restore database
sudo -u postgres createuser smartuser
sudo -u postgres createdb smarthome -O smartuser
gunzip -c backup_20240115_020000.sql.gz | psql -h localhost -U smartuser -d smarthome

# 5. Restore static files
tar -xzf static_backup_20240115.tar.gz

# 6. Configure services
sudo cp smarthome.service /etc/systemd/system/
sudo cp nginx_smarthome /etc/nginx/sites-available/smarthome
sudo ln -s /etc/nginx/sites-available/smarthome /etc/nginx/sites-enabled/

# 7. Start services
sudo systemctl daemon-reload
sudo systemctl enable smarthome
sudo systemctl start smarthome
sudo systemctl reload nginx
```

### 10.4 Disaster Recovery Plan

#### RTO/RPO Objectives

- **Recovery Time Objective (RTO)**: 4 hours
- **Recovery Point Objective (RPO)**: 1 hour (automated backups)

#### Recovery Steps

1. **Assessment** (15 minutes)

   - Identify failure scope
   - Determine recovery approach
2. **Infrastructure Recovery** (1 hour)

   - Provision new server if needed
   - Install base operating system
   - Configure network and security
3. **Application Recovery** (2 hours)

   - Install application dependencies
   - Restore application code
   - Restore configuration files
4. **Data Recovery** (45 minutes)

   - Restore database from latest backup
   - Restore static files
   - Verify data integrity
5. **Testing and Validation** (15 minutes)

   - Test application functionality
   - Verify all services are running
   - Notify users of service restoration

---

**Koniec Instrukcji Technicznej**

Ten dokument zawiera kompletne informacje techniczne niezbędne do instalacji, konfiguracji, zarządzania i utrzymania systemu SmartHome. Dla dodatkowych informacji skontaktuj się z zespołem rozwoju lub sprawdź dokumentację w repozytorium projektu.
