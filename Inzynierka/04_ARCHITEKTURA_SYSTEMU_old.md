# Rozdział 4: Architektura systemu

## 4.1. Ogólny zarys architektury

### 4.1.1. Diagram architektury wysokopoziomowej

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Web Browser │  │ Mobile Safari │  │  Desktop App  │          │
│  │   (Chrome)   │  │   (iOS/iPad)  │  │   (Electron)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┼──────────────────┘                   │
│                            │                                      │
│                      HTTPS/WSS                                    │
└────────────────────────────┼──────────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────┐
│                    REVERSE PROXY LAYER                            │
│                   ┌────────────────┐                              │
│                   │  Nginx Server  │                              │
│                   │  - SSL/TLS     │                              │
│                   │  - Load Balance│                              │
│                   │  - Static Files│                              │
│                   └────────┬───────┘                              │
└────────────────────────────┼──────────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────┐
│                   APPLICATION LAYER                               │
│         ┌──────────────────┴───────────────────┐                 │
│         │     Flask Application (Port 5000)    │                 │
│         │  ┌───────────────────────────────┐   │                 │
│         │  │     app_db.py (Main Entry)    │   │                 │
│         │  │  - SmartHomeApp                │   │                 │
│         │  │  - SocketIO Server             │   │                 │
│         │  └──────────────┬────────────────┘   │                 │
│         │                 │                     │                 │
│         │  ┌──────────────┼────────────────┐   │                 │
│         │  │    Routes Layer               │   │                 │
│         │  │  - RoutesManager (HTML views) │   │                 │
│         │  │  - APIManager (REST API)      │   │                 │
│         │  │  - SocketManager (WebSocket)  │   │                 │
│         │  └──────────────┬────────────────┘   │                 │
│         │                 │                     │                 │
│         │  ┌──────────────┼────────────────┐   │                 │
│         │  │   Business Logic Layer        │   │                 │
│         │  │  - SmartHomeSystemDB          │   │                 │
│         │  │  - MultiHomeDBManager         │   │                 │
│         │  │  - HomeManagers               │   │                 │
│         │  │  - AuthManager                │   │                 │
│         │  └──────────────┬────────────────┘   │                 │
│         └─────────────────┼──────────────────────┘                │
└───────────────────────────┼───────────────────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────────────┐
│                  DATA & CACHE LAYER                               │
│    ┌──────────────────────┼─────────────────────┐                │
│    │                      │                     │                │
│    │    ┌─────────────────▼────────┐   ┌───────▼──────────┐    │
│    │    │   PostgreSQL Database    │   │  Redis Cache     │    │
│    │    │   - Users, Homes         │   │  - Session data  │    │
│    │    │   - Rooms, Devices       │   │  - Cached queries│    │
│    │    │   - Automations          │   │  - Real-time state│   │
│    │    │   - Logs, History        │   │  - TTL management│    │
│    │    └──────────────────────────┘   └──────────────────┘    │
│    │                                                             │
└────┼─────────────────────────────────────────────────────────────┘
     │
┌────┼─────────────────────────────────────────────────────────────┐
│    │              EXTERNAL SERVICES LAYER                        │
│    │    ┌──────────────────┐        ┌────────────────┐          │
│    └───▶│  SMTP Server     │                                   │
│         │  (Email sending) │   (Przyszłe adaptery IoT)         │
│         └──────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.1.2. Komponenty systemu

**Warstwa klienta (Client Layer):**
- Przeglądarki webowe (Chrome, Firefox, Safari, Edge)
- Urządzenia mobilne (responsywny interface)
- Komunikacja HTTPS i WSS (WebSocket Secure)

**Warstwa Reverse Proxy:**
- **Nginx** jako reverse proxy
- Obsługa SSL/TLS certificates (Let's Encrypt)
- Serwowanie statycznych plików (CSS, JS, obrazy)
- Load balancing (w przypadku skalowania)
- Rate limiting i ochrona DDoS

**Warstwa aplikacji:**
- **Flask Application** - główny serwer aplikacji
- **SocketIO Server** - obsługa real-time communication
- **Menedżery tras** - organizacja endpointów
- **Logika biznesowa** - walidacja, autoryzacja, operacje na danych

**Warstwa danych i cache:**
- **PostgreSQL** - główna baza danych relacyjna
- **Redis** - cache dla optymalizacji wydajności (opcjonalny)
- **Backup system** - regularne kopie zapasowe

**Warstwa usług zewnętrznych:**
- **SMTP Server** – wysyłka powiadomień email
- (Opcjonalnie, w przyszłości) Adaptery IoT – możliwość integracji z fizycznymi urządzeniami poprzez standardowe protokoły (planowane, brak implementacji w obecnej wersji)

### 4.1.3. Przepływ danych

**Scenariusz 1: Użytkownik włącza światło**
```
1. User → [Browser] → HTTPS POST /api/devices/{id}/state
2. [Nginx] → Forward request → [Flask App]
3. [APIManager] → Validate auth & permissions
4. [MultiHomeDBManager] → UPDATE devices SET state = true
5. [PostgreSQL] ← Execute query
6. [CacheManager] → Invalidate cache for device
7. [SocketIO] → emit('update_device', data) to all clients in room
8. [Browser] ← WebSocket update → Update UI immediately
9. [Browser] ← HTTP response → {status: 'success'}
```

2. [SmartHomeSystemDB] → Get enabled automations
3. [PostgreSQL] ← SELECT automations WHERE enabled = true
4. [AutomationEngine] → Evaluate trigger conditions
5. [AutomationEngine] → Execute actions (set device state)
6. [MultiHomeDBManager] → UPDATE devices + INSERT automation_executions
7. [SocketIO] → emit('update_device') → Notify all clients
8. [MailManager] → Send notification if configured
```

**Scenariusz 3: Ładowanie strony głównej**
```
1. User → [Browser] → GET /
2. [Nginx] → Forward → [Flask App]
3. [RoutesManager] → Check session authentication
4. [CacheManager] → Check cache for rooms/devices
5. IF cache miss:
   [MultiHomeDBManager] → Query PostgreSQL
   [CacheManager] → Store in cache with TTL
10. [SocketIO] → Join room for user's current home
```

## 4.2. Warstwa Backend

### 4.2.1. Struktura aplikacji Flask

**Główny punkt wejścia: `app_db.py`**
```python
class SmartHomeApp:
    def __init__(self):
        # Initialize Flask app
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        
        # Initialize core components
        self.smart_home = SmartHomeSystemDB()
        self.multi_db = MultiHomeDBManager()
        self.cache_manager = CacheManager()
        self.auth_manager = AuthManager()
        self.mail_manager = MailManager()
        
        # Setup routes
        self.setup_routes()
        self.setup_socket_events()
```

**Struktura katalogów:**
```
app_db.py                    # Main application entry point
app/
  ├── routes.py               # RoutesManager, APIManager, SocketManager
  ├── configure_db.py         # SmartHomeSystemDB
  ├── simple_auth.py          # AuthManager
  ├── mail_manager.py         # MailManager
  ├── home_management.py      # HomeInfoManager, HomeUserManager, etc.
  ├── multi_home_routes.py    # Multi-home specific routes
  └── home_settings_routes.py # Home settings routes
utils/
  ├── multi_home_db_manager.py # MultiHomeDBManager
  ├── smart_home_db_manager.py # SmartHomeDBManager
  ├── cache_manager.py         # CacheManager
  ├── async_manager.py         # AsyncMailManager
  └── asset_manager.py         # CSS/JS minification
templates/
  ├── index.html              # Main dashboard
  ├── home_select.html        # Home selection
  ├── edit.html               # Device management
  ├── automations.html        # Automation editor
  └── admin_dashboard.html    # Admin panel
static/
  ├── css/
  ├── js/
  ├── icons/
  └── profile_pictures/
```

### 4.2.2. Managery i wzorce projektowe

**Manager Pattern**
Zamiast Flask Blueprints używamy klas Manager z metodą `register_routes()`:

```python
class RoutesManager:
    """Manages HTML view routes"""
    def __init__(self, app, smart_home, auth_manager, multi_db):
        self.app = app
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.multi_db = multi_db
    
    def register_routes(self):
        @self.app.route('/')
        @self.auth_manager.login_required
        def index():
            # Get current home from session
            home_id = session.get('current_home_id')
            # Render dashboard
            return render_template('index.html', ...)

class APIManager:
    """Manages REST API endpoints"""
    def register_routes(self):
        @self.app.route('/api/devices', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def devices():
            if request.method == 'GET':
                return jsonify(self.smart_home.get_devices())
            # POST logic...

class SocketManager:
    """Manages WebSocket events"""
    def register_handlers(self):
        @self.socketio.on('toggle_device')
        def handle_toggle(data):
            # Handle device toggle
            # Emit update to all clients
```

**Singleton Pattern dla SmartHomeSystemDB**
```python
class SmartHomeSystemDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Factory Pattern dla Home Managers**
```python
class HomeManagementFactory:
    @staticmethod
    def create_info_manager(multi_db):
        return HomeInfoManager(multi_db)
    
    @staticmethod
    def create_user_manager(multi_db):
        return HomeUserManager(multi_db)
```

**Strategy Pattern dla Cache**
```python
class CacheManager:
    def __init__(self):
        if redis_available():
            self.cache = RedisCache()
        else:
            self.cache = SimpleCache()
    
    def get(self, key):
        return self.cache.get(key)
```

### 4.2.3. System zarządzania stanem (SmartHomeSystem)

**SmartHomeSystemDB - Centralne repozytorium stanu:**

```python
class SmartHomeSystemDB:
    """
    Database-backed smart home system state manager.
    Provides unified interface for accessing system state.
    """
    
    def __init__(self):
        self.db_manager = SmartHomeDBManager()
        self.cache_manager = CacheManager()
    
    @property
    def rooms(self):
        """Get rooms for current home"""
        home_id = session.get('current_home_id')
        cache_key = f"rooms_{home_id}"
        
        cached = self.cache_manager.get(cache_key)
        if cached:
            return cached
        
        rooms = self.db_manager.get_rooms(home_id)
        self.cache_manager.set(cache_key, rooms, timeout=300)
        return rooms
    
    @property
    def buttons(self):
        """Get button devices for current home"""
        home_id = session.get('current_home_id')
        return self.db_manager.get_devices(
            home_id, device_type='button'
        )
    
    def get_device_by_id(self, device_id):
        """Get single device with permission check"""
        home_id = session.get('current_home_id')
        device = self.db_manager.get_device(device_id)
        
        # Verify device belongs to current home
        if device.get('home_id') != home_id:
            raise PermissionError("Access denied")
        
        return device
```

**Klucz owe cechy:**
- **Cache-aware** - automatyczne cache'owanie często używanych danych
- **Session-aware** - respektuje current_home_id z sesji
- **Permission-aware** - sprawdza uprawnienia przy dostępie
- **Fallback-ready** - graceful degradation przy braku cache

### 4.2.4. Obsługa wielodostępu (Multi-Home)

**Architektura Multi-Tenant:**

```
User 1                    User 2                    User 3
  │                         │                         │
  ├─ Home A (owner)        ├─ Home B (owner)        ├─ Home A (member)
  ├─ Home C (member)       └─ Home A (admin)        └─ Home C (admin)
  └─ Home B (member)
```

**Tabele kluczowe:**
```sql
-- Homes table
CREATE TABLE homes (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP
);

-- Home members with roles
CREATE TABLE home_members (
    home_id UUID REFERENCES homes(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(50),  -- 'owner', 'admin', 'user'
    joined_at TIMESTAMP,
    PRIMARY KEY (home_id, user_id)
);

-- Devices scoped to home
CREATE TABLE devices (
    id UUID PRIMARY KEY,
    home_id UUID REFERENCES homes(id),
    room_id UUID,
    name VARCHAR(255),
    device_type VARCHAR(50),
    state JSONB
);
```

**Izolacja danych:**
```python
class MultiHomeDBManager:
    def get_devices(self, home_id, user_id):
        """Get devices with home isolation and permission check"""
        # 1. Verify user has access to home
        if not self.has_home_access(home_id, user_id):
            raise PermissionError("Access denied to home")
        
        # 2. Query devices only for this home
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM devices 
                WHERE home_id = %s
                ORDER BY display_order
            """, (home_id,))
            return cursor.fetchall()
    
    def has_home_access(self, home_id, user_id):
        """Check if user is member of home"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM home_members
                WHERE home_id = %s AND user_id = %s
            """, (home_id, user_id))
            return cursor.fetchone() is not None
    
    def has_admin_access(self, home_id, user_id):
        """Check if user has admin or owner role"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT role FROM home_members
                WHERE home_id = %s AND user_id = %s
            """, (home_id, user_id))
            row = cursor.fetchone()
            return row and row[0] in ('owner', 'admin')
```

**Session management:**
```python
def switch_home(home_id):
    """Switch to different home"""
    user_id = session.get('user_id')
    
    # Verify access
    if not multi_db.has_home_access(home_id, user_id):
        flash("You don't have access to this home")
        return redirect(url_for('home_select'))
    
    # Update session
    session['current_home_id'] = home_id
    multi_db.set_user_current_home(user_id, home_id)
    
    # Invalidate cache
    cache_manager.invalidate_home_cache(home_id)
    
    return redirect(url_for('index'))
```

## 4.3. Warstwa bazy danych

### 4.3.1. Schemat bazy PostgreSQL

**Pełny schemat ER (Entity-Relationship):**

```
┌────────────────┐
│     USERS      │
├────────────────┤
│ id (UUID) PK   │◄────────┐
│ name           │         │
│ email UNIQUE   │         │
│ password_hash  │         │
│ role           │         │
│ profile_picture│         │
│ created_at     │         │
│ updated_at     │         │
└────────────────┘         │
        │                  │
        │ created_by       │ user_id
        ▼                  │
┌────────────────┐         │
│     HOMES      │         │
├────────────────┤         │
│ id (UUID) PK   │◄────────┤
│ name           │         │
│ description    │         │
│ created_by FK  │─────────┘
│ created_at     │
│ updated_at     │
└────────┬───────┘
         │ home_id
         │
    ┌────┴───────────────────┬──────────────────┐
    │                        │                  │
    ▼                        ▼                  ▼
┌──────────────┐    ┌────────────────┐  ┌──────────────┐
│ HOME_MEMBERS │    │     ROOMS      │  │  AUTOMATIONS │
├──────────────┤    ├────────────────┤  ├──────────────┤
│ home_id FK   │    │ id (UUID) PK   │  │ id (UUID) PK │
│ user_id FK   │    │ home_id FK     │  │ home_id FK   │
│ role         │    │ name           │  │ name         │
│ joined_at    │    │ display_order  │  │ trigger_cfg  │
└──────────────┘    │ created_at     │  │ actions_cfg  │
                    └────────┬───────┘  │ enabled      │
                             │          │ executed_at  │
                         room_id        └──────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │    DEVICES     │
                    ├────────────────┤
                    │ id (UUID) PK   │
                    │ home_id FK     │
                    │ room_id FK     │
                    │ name           │
                    │ device_type    │
                    │ state          │
                    │ temperature    │
                    │ display_order  │
                    │ created_at     │
                    └────────┬───────┘
                             │
                             │ device_id
                             ▼
                    ┌────────────────┐
                    │ DEVICE_HISTORY │
                    ├────────────────┤
                    │ id (UUID) PK   │
                    │ device_id FK   │
                    │ old_state      │
                    │ new_state      │
                    │ changed_by FK  │
                    │ change_reason  │
                    │ created_at     │
                    └────────────────┘
```

### 4.3.2. Tabele i relacje

**Tabela: users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    profile_picture TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger auto-update updated_at
CREATE TRIGGER update_users_updated_at 
BEFORE UPDATE ON users 
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Tabela: homes**
```sql
CREATE TABLE homes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_homes_created_by ON homes(created_by);
```

**Tabela: home_members (join table)**
```sql
CREATE TABLE home_members (
    home_id UUID REFERENCES homes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'user' NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (home_id, user_id),
    CHECK (role IN ('owner', 'admin', 'user'))
);

CREATE INDEX idx_home_members_user_id ON home_members(user_id);
CREATE INDEX idx_home_members_home_id ON home_members(home_id);
```

**Tabela: rooms**
```sql
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_id UUID REFERENCES homes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (home_id, name)
);

CREATE INDEX idx_rooms_home_id ON rooms(home_id);
CREATE INDEX idx_rooms_display_order ON rooms(home_id, display_order);
```

**Tabela: devices**
```sql
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_id UUID REFERENCES homes(id) ON DELETE CASCADE,
    room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    state BOOLEAN DEFAULT false,
    temperature NUMERIC(5,2) DEFAULT 22.0,
    min_temperature NUMERIC(5,2) DEFAULT 16.0,
    max_temperature NUMERIC(5,2) DEFAULT 30.0,
    display_order INT DEFAULT 0,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CHECK (device_type IN ('button', 'temperature_control'))
);

CREATE INDEX idx_devices_home_id ON devices(home_id);
CREATE INDEX idx_devices_room_id ON devices(room_id);
CREATE INDEX idx_devices_type ON devices(home_id, device_type);
```

**Tabela: automations**
```sql
CREATE TABLE automations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_id UUID REFERENCES homes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    trigger_config JSONB NOT NULL,
    actions_config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT true,
    last_executed TIMESTAMP WITH TIME ZONE,
    execution_count INT DEFAULT 0,
    error_count INT DEFAULT 0,
    last_error TEXT,
    last_error_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (home_id, name)
);

CREATE INDEX idx_automations_home_id ON automations(home_id);
CREATE INDEX idx_automations_enabled ON automations(home_id, enabled);
```

**Tabela: device_history**
```sql
CREATE TABLE device_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID REFERENCES devices(id) ON DELETE CASCADE,
    old_state JSONB,
    new_state JSONB,
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    change_reason VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_device_history_device_id ON device_history(device_id);
CREATE INDEX idx_device_history_created_at ON device_history(created_at);

-- Partition by month for large tables (optional)
-- CREATE TABLE device_history_2024_01 PARTITION OF device_history
-- FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 4.3.3. Indeksy i optymalizacja

**Strategia indeksowania:**

1. **Primary Keys** - automatyczne indeksy B-tree na UUID
2. **Foreign Keys** - indeksy na wszystkich FK dla szybkich JOIN
3. **Composite Indexes** - dla często używanych zapytań z WHERE

```sql
-- Most common query: Get all devices for home
CREATE INDEX idx_devices_home_type 
ON devices(home_id, device_type) 
INCLUDE (name, state, temperature);

-- Dashboard query: Get rooms with devices count
CREATE INDEX idx_devices_room_count 
ON devices(room_id) WHERE enabled = true;

-- Automation execution
CREATE INDEX idx_automations_next_run 
ON automations(home_id, last_executed) 
WHERE enabled = true;

-- History queries (time-range)
CREATE INDEX idx_device_history_timerange 
ON device_history(device_id, created_at DESC);
```

**Query optimization przykłady:**

```sql
-- BAD: Sequential scan
SELECT * FROM devices WHERE home_id = '123';

-- GOOD: Index scan + covering index
SELECT id, name, state, temperature 
FROM devices 
WHERE home_id = '123' AND device_type = 'button'
ORDER BY display_order;

-- EXPLAIN ANALYZE output:
-- Index Scan using idx_devices_home_type (cost=0.15..8.17 rows=1)
```

**Connection pooling:**
```python
class MultiHomeDBManager:
    def __init__(self):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,    # Minimum connections
            maxconn=10,   # Maximum connections
            host=...,
            # ...
        )
    
    def get_connection(self):
        return self.pool.getconn()
    
    def return_connection(self, conn):
        self.pool.putconn(conn)
```

### 4.3.4. Migracje i backup

**Migration strategy:**
```bash
# backups/migrations/
001_initial_schema.sql
002_add_homes_table.sql
003_add_home_members.sql
004_add_automations.sql
```

**Backup script:**
```bash
#!/bin/bash
# backup_db.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U smarthome -d smart_home \
    --clean --if-exists \
    > backups/db_backup_$DATE.sql
    
# Keep only last 7 days
find backups/ -name "db_backup_*.sql" -mtime +7 -delete
```

**Restore:**
```bash
psql -h localhost -U smarthome -d smart_home \
    < backups/db_backup_20241108_120000.sql
```

---

**Podsumowanie sekcji:**

Rozdział 4 przedstawia szczegółową architekturę systemu SmartHome Multi-Home. Opisano wysokopoziomową strukturę komponentów oraz przepływy danych dla kluczowych scenariuszy. Szczególną uwagę poświęcono architekturze multi-tenant, która zapewnia silną izolację danych między domami przy jednoczesnym umożliwieniu współdzielenia dostępu. Zaprezentowano również pełny schemat bazy danych PostgreSQL wraz z indeksami i strategiami optymalizacyjnymi.

W kolejnych rozdziałach zostaną omówione szczegóły implementacji poszczególnych funkcjonalności oraz mechanizmy real-time communication.
