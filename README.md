# 🏠 SmartHome Multi-Home System

[**English**](#english) | [**Polski**](#polski)

---

<a name="english"></a>
## 🌍 English

### 📖 Overview

SmartHome Multi-Home is a comprehensive web-based smart home management system built with Flask and Socket.IO. The application enables real-time control of lights, temperature, security systems, and automations across multiple homes. It features a robust PostgreSQL database backend with automatic fallback to JSON file storage, making it flexible for various deployment scenarios.

### ✨ Key Features

- **🔄 Real-Time Control**: WebSocket-based communication for instant device state updates
- **🏘️ Multi-Home Support**: Manage multiple homes with role-based access control (Owner, Admin, Member)
- **🤖 Advanced Automations**: Create complex automation rules with triggers and actions
- **👥 User Management**: Comprehensive user administration with invitation system
- **🔐 Security**: Role-based permissions, secure authentication, and encrypted communications
- **📊 Admin Dashboard**: Statistics, user management, device monitoring, and system logs
- **💾 Database Flexibility**: PostgreSQL primary storage with JSON fallback for resilience
- **⚡ Performance Optimized**: Redis caching, asset minification, and connection pooling
- **📧 Email Notifications**: Asynchronous email delivery for alerts and invitations
- **🐳 Docker Ready**: Complete containerization with Docker Compose support
- **🌐 Mobile Responsive**: Fully responsive design for all device sizes

### 🏗️ System Architecture

#### Backend Components

- **`app_db.py`**: Main application entry point - initializes Flask, Socket.IO, database, cache, and routes
- **`app/routes.py`**: HTTP routes and Socket.IO event handlers (RoutesManager class)
- **`app/configure_db.py`**: Database-backed SmartHome system (`SmartHomeSystemDB`)
- **`utils/smart_home_db_manager.py`**: Low-level database operations for core entities
- **`utils/multi_home_db_manager.py`**: Multi-home specific database operations
- **`utils/cache_manager.py`**: Redis/SimpleCache integration with automatic invalidation
- **`utils/async_manager.py`**: Asynchronous email queue and background task management
- **`app/mail_manager.py`**: SMTP email delivery service
- **`app/simple_auth.py`**: Authentication and authorization manager

#### Frontend Components

- **Templates**: Jinja2 templates in `templates/` directory
  - `index.html`: Main dashboard
  - `room.html`: Room-specific device control
  - `automations.html`: Automation editor
  - `admin_dashboard.html`: System administration
  - `home_settings.html`: Home configuration
  - And more...
- **Static Assets**: CSS, JavaScript, icons in `static/` directory
- **Asset Manager**: `utils/asset_manager.py` for CSS/JS minification and watching

#### Database Layer

- **PostgreSQL**: Primary data storage (users, homes, rooms, devices, automations, logs)
- **Schema**: Complete database schema in `backups/db_backup.sql`
- **Connection Pooling**: Efficient connection management via `utils/db_manager.py`
- **Multi-tenancy**: Home-based data isolation with user permissions

#### Caching Layer

- **Redis**: Optional distributed cache for production deployments
- **SimpleCache**: In-memory fallback for development
- **Smart Invalidation**: Automatic cache invalidation on data changes
- **Session Cache**: User-specific cached data

### 🛠️ Technology Stack

#### Core Technologies
- **Python 3.10+**: Main programming language
- **Flask 3.1.0**: Web framework
- **Flask-SocketIO 5.5.0**: Real-time WebSocket communication
- **PostgreSQL 13+**: Primary database
- **Redis**: Optional caching layer
- **Gunicorn/Waitress**: Production WSGI servers

#### Key Dependencies
- **psycopg2-binary 2.9.10**: PostgreSQL adapter
- **Flask-Caching 2.3.1**: Caching framework
- **Werkzeug 3.1.3**: WSGI utilities
- **Pillow**: Image processing for profile pictures
- **cryptography 44.0.0**: Secure password hashing
- **requests 2.32.3**: HTTP client for external services
- **cssmin 0.2.0 & jsmin 3.0.1**: Asset minification

#### Infrastructure
- **Docker & Docker Compose**: Containerization
- **Nginx**: Reverse proxy and static file serving
- **Eventlet/Gevent**: Async worker support

See `requirements.txt` for complete dependency list.

### 📁 Repository Structure

```
Site_proj/
├── app_db.py                 # Main application entry point
├── app/                      # Application logic
│   ├── routes.py            # Routes and Socket.IO handlers
│   ├── configure_db.py      # Database-backed SmartHome system
│   ├── simple_auth.py       # Authentication manager
│   ├── mail_manager.py      # Email service
│   ├── home_management.py   # Multi-home operations
│   └── ...
├── utils/                    # Utility modules
│   ├── db_manager.py        # Database connection pool
│   ├── smart_home_db_manager.py   # Core DB operations
│   ├── multi_home_db_manager.py   # Multi-home DB operations
│   ├── cache_manager.py     # Caching system
│   ├── async_manager.py     # Background task queue
│   ├── asset_manager.py     # CSS/JS minification
│   └── ...
├── templates/               # Jinja2 HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Dashboard
│   ├── room.html           # Room control
│   ├── automations.html    # Automation editor
│   └── ...
├── static/                  # Static assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   ├── icons/              # Icon files
│   └── profile_pictures/   # User uploads
├── backups/                 # Backup and seed data
│   └── db_backup.sql       # Database schema + seed data
├── info/                    # Documentation
│   ├── README.md           # System overview (Polish)
│   ├── QUICK_START.md      # Quick start guide
│   ├── DEPLOYMENT.md       # Deployment instructions
│   └── ...
├── docker-compose.yml       # Docker Compose config
├── Dockerfile.app          # Application container
├── Dockerfile.nginx        # Nginx container
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

### 🚀 Getting Started

#### Prerequisites

- **Python 3.10 or higher**
- **PostgreSQL 13+** with network access
- **Redis** (optional, for caching)
- **Git** for version control
- **Docker & Docker Compose** (optional, for containerized deployment)

#### 1. Clone the Repository

```bash
git clone https://github.com/AdasRakieta/Site_proj.git
cd Site_proj
```

#### 2. Install Dependencies

**Option A: Using Virtual Environment (Recommended for Development)**

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Option B: Using Docker (Recommended for Production)**

```bash
# Build images
docker-compose build

# Or pull pre-built images
docker-compose pull
```

#### 3. Configure Environment Variables

**Automated Setup (Recommended):**

```bash
# Windows (PowerShell)
.\setup_env.ps1

# Linux/macOS
chmod +x setup_env.sh
./setup_env.sh
```

**Manual Setup:**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smarthome_multihouse
DB_USER=your_db_user
DB_PASSWORD=your_secure_password

# Flask Configuration
SECRET_KEY=your_random_32_character_secret_key
FLASK_ENV=development

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ADMIN_EMAIL=admin@example.com

# Redis (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Validate Configuration:**

```bash
python utils/validate_env.py
```

⚠️ **Security Warning**: Never commit `.env` file to version control! It contains sensitive credentials.

#### 4. Database Setup

**Initialize PostgreSQL Database:**

```bash
# Create database
createdb -U postgres smarthome_multihouse

# Import schema and seed data
psql -h localhost -U your_db_user -d smarthome_multihouse -f backups/db_backup.sql
```

**Default Admin Account:**
- Username: Check `db_backup.sql` for default credentials
- ⚠️ **Change password immediately after first login!**

#### 5. Run the Application

**Development Mode:**

```bash
python app_db.py
```

The application will start on `http://localhost:5000`

**Production Mode:**

**Using Waitress (Windows):**
```bash
python -m waitress --port=5000 app_db:main
```

**Using Gunicorn (Linux/macOS):**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app_db:main"
```

**Using Docker Compose:**
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### 🐳 Docker Deployment

#### Quick Start with Docker Compose

```bash
# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Docker Compose Services

- **app**: Flask application (port 5000)
- **nginx**: Reverse proxy and static file server (ports 80, 443)
- **postgres**: PostgreSQL database (optional, can use external)
- **redis**: Redis cache (optional, can use external)

#### Portainer Deployment

Detailed instructions available in `info/PORTAINER_DEPLOYMENT.md`

### 📡 API Endpoints

#### Authentication
- `POST /login` - User login
- `POST /logout` - User logout
- `POST /register` - User registration
- `POST /forgot-password` - Password reset request

#### Dashboard & Home Management
- `GET /` - Main dashboard
- `GET /home/select` - Home selection
- `POST /api/home/create` - Create new home
- `POST /api/home/join` - Join existing home
- `GET /api/home/switch/<home_id>` - Switch active home

#### Device Control
- `GET /room/<room_name>` - Room device view
- `POST /api/devices/toggle` - Toggle device state
- `POST /api/temperature/set` - Set temperature
- `POST /api/security/set` - Update security state

#### Automation Management
- `GET /automations` - Automation editor
- `GET /api/automations/list` - Get all automations
- `POST /api/automations/create` - Create automation
- `PUT /api/automations/update/<id>` - Update automation
- `DELETE /api/automations/delete/<id>` - Delete automation

#### Admin Panel
- `GET /admin_dashboard` - Admin dashboard (requires admin role)
- `GET /api/users/list` - List all users
- `POST /api/users/create` - Create user
- `DELETE /api/users/<id>` - Delete user
- `PUT /api/users/<id>/role` - Update user role

#### System Status
- `GET /api/ping` - Health check
- `GET /api/status` - Application status
- `GET /api/cache/stats` - Cache statistics
- `GET /api/database/stats` - Database connection stats

### 🔌 Socket.IO Events

#### Client → Server
- `toggle_button` - Toggle device state
- `set_temperature` - Change temperature setpoint
- `set_security_state` - Update security mode
- `automation_execute` - Manually trigger automation

#### Server → Client
- `state_update` - Device state changed
- `temperature_update` - Temperature value changed
- `security_update` - Security state changed
- `notification` - System notification
- `user_list_update` - User list changed (admin only)

### 🔧 Additional Tools

#### Asset Minification

```bash
# One-time minification
python utils/asset_manager.py

# Watch mode (auto-minify on changes)
python utils/asset_manager.py --watch
```

#### Cache Management

Cache statistics available at `/api/cache/stats` when logged in.

Manual cache invalidation methods available in `utils/cache_manager.py`:
- `invalidate_rooms()`
- `invalidate_devices()`
- `invalidate_automations()`
- `clear_all()`

### 🔍 Troubleshooting

#### Database Connection Issues

```bash
# Check database is running
psql -h localhost -U your_db_user -d smarthome_multihouse -c "SELECT 1;"

# Verify environment variables
python utils/validate_env.py

# Check application logs
python app_db.py  # Watch console output
```

**Application will automatically fall back to JSON file storage if PostgreSQL is unavailable.**

#### Cache Issues

```bash
# Check Redis connection
redis-cli ping

# Application works without Redis using SimpleCache fallback
```

#### Email Delivery Issues

```bash
# Test SMTP configuration
python -c "import smtplib; s=smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); s.login('user', 'pass'); print('OK')"
```

#### Port Already in Use

```bash
# Find process using port 5000
# Windows:
netstat -ano | findstr :5000

# Linux/macOS:
lsof -i :5000

# Kill process or change port in .env
```

### 📚 Additional Documentation

- **[QUICK_START.md](info/QUICK_START.md)**: Quick start guide (Polish)
- **[DEPLOYMENT.md](info/DEPLOYMENT.md)**: Detailed deployment instructions
- **[PORTAINER_DEPLOYMENT.md](info/PORTAINER_DEPLOYMENT.md)**: Portainer-specific deployment
- **[SECURITY.md](SECURITY.md)**: Security policy and vulnerability reporting

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 🐛 Bug Reports & Feature Requests

Please use the [GitHub Issues](https://github.com/AdasRakieta/Site_proj/issues) page to report bugs or request features.

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 👥 Authors

- **AdasRakieta** - *Initial work and maintenance*

### 🙏 Acknowledgments

- Flask and Flask-SocketIO communities
- PostgreSQL development team
- All contributors and users of this project

---

<a name="polski"></a>
## 🇵🇱 Polski

### 📖 Przegląd

SmartHome Multi-Home to kompleksowy system zarządzania inteligentnym domem oparty na technologii webowej, zbudowany przy użyciu Flask i Socket.IO. Aplikacja umożliwia sterowanie w czasie rzeczywistym oświetleniem, temperaturą, systemami bezpieczeństwa i automatyzacjami w wielu domach. Posiada solidny backend w postaci bazy danych PostgreSQL z automatycznym przełączaniem awaryjnym na przechowywanie w plikach JSON, co czyni ją elastyczną dla różnych scenariuszy wdrożeniowych.

### ✨ Główne Funkcje

- **🔄 Sterowanie w Czasie Rzeczywistym**: Komunikacja WebSocket dla natychmiastowej aktualizacji stanu urządzeń
- **🏘️ Wsparcie Wielu Domów**: Zarządzanie wieloma domami z kontrolą dostępu opartą na rolach (Właściciel, Administrator, Członek)
- **🤖 Zaawansowane Automatyzacje**: Tworzenie złożonych reguł automatyzacji z wyzwalaczami i akcjami
- **👥 Zarządzanie Użytkownikami**: Kompleksowa administracja użytkownikami z systemem zaproszeń
- **🔐 Bezpieczeństwo**: Uprawnienia oparte na rolach, bezpieczna autentykacja i szyfrowana komunikacja
- **📊 Panel Administratora**: Statystyki, zarządzanie użytkownikami, monitoring urządzeń i logi systemowe
- **💾 Elastyczność Bazy Danych**: Główne przechowywanie w PostgreSQL z awaryjnym przełączeniem na JSON
- **⚡ Zoptymalizowana Wydajność**: Cache Redis, minifikacja zasobów i pooling połączeń
- **📧 Powiadomienia Email**: Asynchroniczna wysyłka emaili dla alertów i zaproszeń
- **🐳 Gotowość Docker**: Pełna konteneryzacja ze wsparciem Docker Compose
- **🌐 Responsywność Mobilna**: Pełny responsywny design dla wszystkich rozmiarów urządzeń

### 🏗️ Architektura Systemu

#### Komponenty Backend

- **`app_db.py`**: Główny punkt wejścia aplikacji - inicjalizuje Flask, Socket.IO, bazę danych, cache i trasy
- **`app/routes.py`**: Trasy HTTP i obsługa zdarzeń Socket.IO (klasa RoutesManager)
- **`app/configure_db.py`**: System SmartHome oparty na bazie danych (`SmartHomeSystemDB`)
- **`utils/smart_home_db_manager.py`**: Niskopoziomowe operacje bazodanowe dla głównych encji
- **`utils/multi_home_db_manager.py`**: Operacje bazodanowe specyficzne dla wielu domów
- **`utils/cache_manager.py`**: Integracja Redis/SimpleCache z automatyczną invalidacją
- **`utils/async_manager.py`**: Kolejka asynchronicznych emaili i zarządzanie zadaniami w tle
- **`app/mail_manager.py`**: Serwis wysyłki emaili SMTP
- **`app/simple_auth.py`**: Menadżer autentykacji i autoryzacji

#### Komponenty Frontend

- **Szablony**: Szablony Jinja2 w katalogu `templates/`
  - `index.html`: Główny dashboard
  - `room.html`: Sterowanie urządzeniami w pokoju
  - `automations.html`: Edytor automatyzacji
  - `admin_dashboard.html`: Administracja systemem
  - `home_settings.html`: Konfiguracja domu
  - I więcej...
- **Zasoby Statyczne**: CSS, JavaScript, ikony w katalogu `static/`
- **Menadżer Zasobów**: `utils/asset_manager.py` do minifikacji CSS/JS

#### Warstwa Bazy Danych

- **PostgreSQL**: Główne przechowywanie danych (użytkownicy, domy, pokoje, urządzenia, automatyzacje, logi)
- **Schemat**: Kompletny schemat bazy w `backups/db_backup.sql`
- **Pooling Połączeń**: Efektywne zarządzanie połączeniami przez `utils/db_manager.py`
- **Multi-tenancy**: Izolacja danych oparta na domach z uprawnieniami użytkowników

#### Warstwa Cache

- **Redis**: Opcjonalny rozproszony cache dla wdrożeń produkcyjnych
- **SimpleCache**: Awaryjny cache w pamięci dla developmentu
- **Inteligentna Invalidacja**: Automatyczna invalidacja cache przy zmianach danych
- **Cache Sesyjny**: Dane cache specyficzne dla użytkownika

### 🛠️ Stos Technologiczny

#### Główne Technologie
- **Python 3.10+**: Główny język programowania
- **Flask 3.1.0**: Framework webowy
- **Flask-SocketIO 5.5.0**: Komunikacja WebSocket w czasie rzeczywistym
- **PostgreSQL 13+**: Główna baza danych
- **Redis**: Opcjonalna warstwa cache
- **Gunicorn/Waitress**: Serwery WSGI produkcyjne

#### Kluczowe Zależności
- **psycopg2-binary 2.9.10**: Adapter PostgreSQL
- **Flask-Caching 2.3.1**: Framework cache
- **Werkzeug 3.1.3**: Narzędzia WSGI
- **Pillow**: Przetwarzanie obrazów dla zdjęć profilowych
- **cryptography 44.0.0**: Bezpieczne hashowanie haseł
- **requests 2.32.3**: Klient HTTP dla usług zewnętrznych
- **cssmin 0.2.0 & jsmin 3.0.1**: Minifikacja zasobów

#### Infrastruktura
- **Docker & Docker Compose**: Konteneryzacja
- **Nginx**: Reverse proxy i serwowanie plików statycznych
- **Eventlet/Gevent**: Wsparcie dla workerów asynchronicznych

Zobacz `requirements.txt` dla kompletnej listy zależności.

### 📁 Struktura Repozytorium

```
Site_proj/
├── app_db.py                 # Główny punkt wejścia aplikacji
├── app/                      # Logika aplikacji
│   ├── routes.py            # Trasy i handlery Socket.IO
│   ├── configure_db.py      # System SmartHome oparty na bazie
│   ├── simple_auth.py       # Menadżer autentykacji
│   ├── mail_manager.py      # Serwis email
│   ├── home_management.py   # Operacje multi-home
│   └── ...
├── utils/                    # Moduły narzędziowe
│   ├── db_manager.py        # Pool połączeń bazodanowych
│   ├── smart_home_db_manager.py   # Główne operacje DB
│   ├── multi_home_db_manager.py   # Operacje DB multi-home
│   ├── cache_manager.py     # System cache
│   ├── async_manager.py     # Kolejka zadań w tle
│   ├── asset_manager.py     # Minifikacja CSS/JS
│   └── ...
├── templates/               # Szablony HTML Jinja2
│   ├── base.html           # Szablon bazowy
│   ├── index.html          # Dashboard
│   ├── room.html           # Sterowanie pokojem
│   ├── automations.html    # Edytor automatyzacji
│   └── ...
├── static/                  # Zasoby statyczne
│   ├── css/                # Arkusze stylów
│   ├── js/                 # Pliki JavaScript
│   ├── icons/              # Pliki ikon
│   └── profile_pictures/   # Przesyłane przez użytkowników
├── backups/                 # Backup i dane początkowe
│   └── db_backup.sql       # Schemat bazy + dane startowe
├── info/                    # Dokumentacja
│   ├── README.md           # Przegląd systemu (polski)
│   ├── QUICK_START.md      # Przewodnik szybkiego startu
│   ├── DEPLOYMENT.md       # Instrukcje wdrożenia
│   └── ...
├── docker-compose.yml       # Konfiguracja Docker Compose
├── Dockerfile.app          # Kontener aplikacji
├── Dockerfile.nginx        # Kontener Nginx
├── requirements.txt        # Zależności Python
├── .env.example           # Szablon środowiska
└── README.md              # Ten plik
```

### 🚀 Pierwsze Kroki

#### Wymagania Wstępne

- **Python 3.10 lub nowszy**
- **PostgreSQL 13+** z dostępem sieciowym
- **Redis** (opcjonalnie, do cache)
- **Git** do kontroli wersji
- **Docker & Docker Compose** (opcjonalnie, do wdrożenia kontenerowego)

#### 1. Sklonuj Repozytorium

```bash
git clone https://github.com/AdasRakieta/Site_proj.git
cd Site_proj
```

#### 2. Zainstaluj Zależności

**Opcja A: Używając Wirtualnego Środowiska (Zalecane dla Developmentu)**

```bash
# Utwórz wirtualne środowisko
python -m venv .venv

# Aktywuj wirtualne środowisko
# Na Windows:
.\.venv\Scripts\activate
# Na Linux/macOS:
source .venv/bin/activate

# Zainstaluj zależności
pip install --upgrade pip
pip install -r requirements.txt
```

**Opcja B: Używając Docker (Zalecane dla Produkcji)**

```bash
# Zbuduj obrazy
docker-compose build

# Lub pobierz gotowe obrazy
docker-compose pull
```

#### 3. Skonfiguruj Zmienne Środowiskowe

**Automatyczna Konfiguracja (Zalecane):**

```bash
# Windows (PowerShell)
.\setup_env.ps1

# Linux/macOS
chmod +x setup_env.sh
./setup_env.sh
```

**Ręczna Konfiguracja:**

```bash
# Skopiuj przykładowy plik środowiska
cp .env.example .env

# Edytuj .env swoją konfiguracją
nano .env  # lub użyj swojego ulubionego edytora
```

**Wymagane Zmienne Środowiskowe:**

```env
# Konfiguracja Bazy Danych
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smarthome_multihouse
DB_USER=twoj_uzytkownik_db
DB_PASSWORD=twoje_bezpieczne_haslo

# Konfiguracja Flask
SECRET_KEY=twoj_losowy_32_znakowy_sekretny_klucz
FLASK_ENV=development

# Konfiguracja Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=twoj_email@gmail.com
SMTP_PASSWORD=twoje_haslo_aplikacji
ADMIN_EMAIL=admin@example.com

# Redis (Opcjonalnie)
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Waliduj Konfigurację:**

```bash
python utils/validate_env.py
```

⚠️ **Ostrzeżenie Bezpieczeństwa**: Nigdy nie commituj pliku `.env` do kontroli wersji! Zawiera on poufne dane uwierzytelniające.

#### 4. Konfiguracja Bazy Danych

**Zainicjalizuj Bazę Danych PostgreSQL:**

```bash
# Utwórz bazę danych
createdb -U postgres smarthome_multihouse

# Importuj schemat i dane początkowe
psql -h localhost -U twoj_uzytkownik_db -d smarthome_multihouse -f backups/db_backup.sql
```

**Domyślne Konto Administratora:**
- Nazwa użytkownika: Sprawdź `db_backup.sql` dla domyślnych danych uwierzytelniających
- ⚠️ **Zmień hasło natychmiast po pierwszym logowaniu!**

#### 5. Uruchom Aplikację

**Tryb Deweloperski:**

```bash
python app_db.py
```

Aplikacja uruchomi się na `http://localhost:5000`

**Tryb Produkcyjny:**

**Używając Waitress (Windows):**
```bash
python -m waitress --port=5000 app_db:main
```

**Używając Gunicorn (Linux/macOS):**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app_db:main"
```

**Używając Docker Compose:**
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### 🐳 Wdrożenie Docker

#### Szybki Start z Docker Compose

```bash
# Ustaw zmienne środowiskowe
cp .env.example .env
# Edytuj .env swoją konfiguracją

# Uruchom serwisy
docker-compose up -d

# Zobacz logi
docker-compose logs -f

# Zatrzymaj serwisy
docker-compose down
```

#### Serwisy Docker Compose

- **app**: Aplikacja Flask (port 5000)
- **nginx**: Reverse proxy i serwer plików statycznych (porty 80, 443)
- **postgres**: Baza danych PostgreSQL (opcjonalnie, można użyć zewnętrznej)
- **redis**: Cache Redis (opcjonalnie, można użyć zewnętrznego)

#### Wdrożenie Portainer

Szczegółowe instrukcje dostępne w `info/PORTAINER_DEPLOYMENT.md`

### 📡 Endpointy API

#### Autentykacja
- `POST /login` - Logowanie użytkownika
- `POST /logout` - Wylogowanie użytkownika
- `POST /register` - Rejestracja użytkownika
- `POST /forgot-password` - Żądanie resetu hasła

#### Dashboard i Zarządzanie Domem
- `GET /` - Główny dashboard
- `GET /home/select` - Wybór domu
- `POST /api/home/create` - Utwórz nowy dom
- `POST /api/home/join` - Dołącz do istniejącego domu
- `GET /api/home/switch/<home_id>` - Przełącz aktywny dom

#### Sterowanie Urządzeniami
- `GET /room/<room_name>` - Widok urządzeń w pokoju
- `POST /api/devices/toggle` - Przełącz stan urządzenia
- `POST /api/temperature/set` - Ustaw temperaturę
- `POST /api/security/set` - Aktualizuj stan bezpieczeństwa

#### Zarządzanie Automatyzacjami
- `GET /automations` - Edytor automatyzacji
- `GET /api/automations/list` - Pobierz wszystkie automatyzacje
- `POST /api/automations/create` - Utwórz automatyzację
- `PUT /api/automations/update/<id>` - Aktualizuj automatyzację
- `DELETE /api/automations/delete/<id>` - Usuń automatyzację

#### Panel Administratora
- `GET /admin_dashboard` - Dashboard administratora (wymaga roli admin)
- `GET /api/users/list` - Lista wszystkich użytkowników
- `POST /api/users/create` - Utwórz użytkownika
- `DELETE /api/users/<id>` - Usuń użytkownika
- `PUT /api/users/<id>/role` - Aktualizuj rolę użytkownika

#### Status Systemu
- `GET /api/ping` - Sprawdzenie stanu
- `GET /api/status` - Status aplikacji
- `GET /api/cache/stats` - Statystyki cache
- `GET /api/database/stats` - Statystyki połączeń z bazą

### 🔌 Zdarzenia Socket.IO

#### Klient → Serwer
- `toggle_button` - Przełącz stan urządzenia
- `set_temperature` - Zmień wartość zadaną temperatury
- `set_security_state` - Aktualizuj tryb bezpieczeństwa
- `automation_execute` - Ręcznie uruchom automatyzację

#### Serwer → Klient
- `state_update` - Stan urządzenia się zmienił
- `temperature_update` - Wartość temperatury się zmieniła
- `security_update` - Stan bezpieczeństwa się zmienił
- `notification` - Powiadomienie systemowe
- `user_list_update` - Lista użytkowników się zmieniła (tylko admin)

### 🔧 Dodatkowe Narzędzia

#### Minifikacja Zasobów

```bash
# Jednorazowa minifikacja
python utils/asset_manager.py

# Tryb obserwacji (auto-minifikacja przy zmianach)
python utils/asset_manager.py --watch
```

#### Zarządzanie Cache

Statystyki cache dostępne pod `/api/cache/stats` po zalogowaniu.

Ręczne metody invalidacji cache dostępne w `utils/cache_manager.py`:
- `invalidate_rooms()`
- `invalidate_devices()`
- `invalidate_automations()`
- `clear_all()`

### 🔍 Rozwiązywanie Problemów

#### Problemy z Połączeniem z Bazą Danych

```bash
# Sprawdź czy baza danych działa
psql -h localhost -U twoj_uzytkownik_db -d smarthome_multihouse -c "SELECT 1;"

# Zweryfikuj zmienne środowiskowe
python utils/validate_env.py

# Sprawdź logi aplikacji
python app_db.py  # Obserwuj wyjście konsoli
```

**Aplikacja automatycznie przełączy się na przechowywanie w plikach JSON jeśli PostgreSQL jest niedostępny.**

#### Problemy z Cache

```bash
# Sprawdź połączenie Redis
redis-cli ping

# Aplikacja działa bez Redis używając awaryjnego SimpleCache
```

#### Problemy z Dostarczaniem Email

```bash
# Testuj konfigurację SMTP
python -c "import smtplib; s=smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); s.login('user', 'pass'); print('OK')"
```

#### Port Już Używany

```bash
# Znajdź proces używający portu 5000
# Windows:
netstat -ano | findstr :5000

# Linux/macOS:
lsof -i :5000

# Zakończ proces lub zmień port w .env
```

### 📚 Dodatkowa Dokumentacja

- **[QUICK_START.md](info/QUICK_START.md)**: Przewodnik szybkiego startu (polski)
- **[DEPLOYMENT.md](info/DEPLOYMENT.md)**: Szczegółowe instrukcje wdrożenia
- **[PORTAINER_DEPLOYMENT.md](info/PORTAINER_DEPLOYMENT.md)**: Wdrożenie specyficzne dla Portainer
- **[SECURITY.md](SECURITY.md)**: Polityka bezpieczeństwa i zgłaszanie podatności

### 🤝 Współpraca

Wkład jest mile widziany! Prosimy o swobodne składanie Pull Requestów.

1. Sforkuj repozytorium
2. Utwórz branch z funkcją (`git checkout -b feature/NowaCecha`)
3. Commituj swoje zmiany (`git commit -m 'Dodaj jakąś NowąCechę'`)
4. Wypchnij do brancha (`git push origin feature/NowaCecha`)
5. Otwórz Pull Request

### 🐛 Zgłoszenia Błędów i Prośby o Funkcje

Prosimy używać strony [GitHub Issues](https://github.com/AdasRakieta/Site_proj/issues) do zgłaszania błędów lub próśb o funkcje.

### 📄 Licencja

Ten projekt jest licencjonowany na licencji MIT - zobacz plik [LICENSE](LICENSE) dla szczegółów.

### 👥 Autorzy

- **AdasRakieta** - *Początkowa praca i utrzymanie*

### 🙏 Podziękowania

- Społeczności Flask i Flask-SocketIO
- Zespołowi rozwoju PostgreSQL
- Wszystkim współtwórcom i użytkownikom tego projektu

---

Made with ❤️ by AdasRakieta
