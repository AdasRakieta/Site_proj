# Diagramy i Schematy Architektury - System SmartHome

## Diagram Architektury Systemu

```
┌─────────────────────────────────────────────    └─────────────────────────────────┘              └─────────────────────────────────┘

### Kluczowe Indeksy i Ograniczenia:

#### Indeksy wydajnościowe:
- `idx_users_name`, `idx_users_email` - szybkie wyszukiwanie użytkowników
- `idx_devices_room`, `idx_devices_type`, `idx_devices_order` - optymalizacja zapytań o urządzenia
- `idx_logs_timestamp DESC`, `idx_logs_level`, `idx_logs_event_type` - wydajne filtrowanie logów
- `idx_auto_exec_time DESC`, `idx_auto_exec_status` - monitorowanie wykonań automatyzacji
- `idx_session_expires` - czyszczenie wygasłych sesji

#### Ograniczenia integralności:
- Foreign Key CASCADE dla `devices.room_id`, `device_history.device_id`
- Foreign Key SET NULL dla `management_logs.user_id`, `device_history.changed_by`
- CHECK constraint dla `device_type` ('button', 'temperature_control')
- UNIQUE constraints dla `users.name`, `users.email`, `rooms.name`, `automations.name`

#### Automatyczne triggery:
- `update_updated_at_column()` - automatyczna aktualizacja timestamp'ów
- UUID generacja przez `uuid_generate_v4()` dla wszystkich primary keys
````───────────────────────────────┐
│                               INTERNET/WAN                                 │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────┐
│                         NGINX REVERSE PROXY                                │
│                     SSL Termination & Load Balancing                       │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│   FLASK APP 1   │  │   FLASK APP 2   │  │   FLASK APP 3   │
│  (Container)    │  │  (Container)    │  │  (Container)    │
│                 │  │                 │  │                 │
│ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
│ │Routes Mgr   │ │  │ │Routes Mgr   │ │  │ │Routes Mgr   │ │
│ │Cache Mgr    │ │  │ │Cache Mgr    │ │  │ │Cache Mgr    │ │
│ │Asset Mgr    │ │  │ │Asset Mgr    │ │  │ │Asset Mgr    │ │
│ │Auth Mgr     │ │  │ │Auth Mgr     │ │  │ │Auth Mgr     │ │
│ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
┌───▼──────────────┐    ┌─────▼──────────┐    ┌────────▼────────┐
│  POSTGRESQL      │    │     REDIS      │    │  FILE STORAGE   │
│   (Primary DB)   │    │    (Cache)     │    │    (Backups)    │
│                  │    │                │    │                 │
│ ┌──────────────┐ │    │ ┌────────────┐ │    │ ┌─────────────┐ │
│ │ Users        │ │    │ │Session Data│ │    │ │ Logs        │ │
│ │ Devices      │ │    │ │API Cache   │ │    │ │ Configs     │ │
│ │ Rooms        │ │    │ │User Cache  │ │    │ │ Assets      │ │
│ │ Automations  │ │    │ │Statistics  │ │    │ │ Backups     │ │
│ │ Logs         │ │    │ └────────────┘ │    │ └─────────────┘ │
│ └──────────────┘ │    └────────────────┘    └─────────────────┘
└──────────────────┘   
  
┌─────────────────────────────────────────────────────┐
│                   CLIENT LAYER                      │
├─────────────────────┬───────────────────────────────┤
│   WEB BROWSERS      │      IoT DEVICES              │
│                     │                               │
│ ┌─────────────────┐ │ ┌───────────────────────────┐ │
│ │ Chrome/Firefox  │ │ │ Smart Lights              │ │
│ │ Safari/Edge     │ │ │ Temperature Sensors       │ │
│ │ JavaScript SPA  │ │ │ Security Cameras          │ │
│ │ WebSocket       │ │ │ Door Locks                │ │
│ └─────────────────┘ │ └───────────────────────────┘ │
└─────────────────────┴───────────────────────────────┘
```

## Diagram Przepływu Danych

```
┌─────────────┐    HTTP/WebSocket    ┌─────────────────┐
│   CLIENT    │◄────────────────────►│  NGINX PROXY    │
│ (Browser/   │                      │                 │
│  Mobile)    │                      │ SSL/TLS         │
└─────────────┘                      │ Load Balancing  │
                                     └─────────┬───────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    FLASK APPLICATION                         │
│                                                              │
│ ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│ │ Routes      │  │ WebSocket    │  │ Background Tasks    │   │
│ │ Manager     │  │ Handler      │  │                     │   │
│ │             │  │              │  │ - Email sending     │   │
│ │ - Login     │  │ - Real-time  │  │ - Automation engine │   │
│ │ - API       │  │   updates    │  │ - Log processing    │   │
│ │ - Dashboard │  │ - Device     │  │ - Cache warming     │   │
│ │ - Admin     │  │   control    │  │                     │   │
│ └─────────────┘  └──────────────┘  └─────────────────────┘   │
│         │                │                      │            │
│         ▼                ▼                      ▼            │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │              SMART HOME CORE ENGINE                     │  │
│ │                                                         │  │
│ │ ┌─────────────┐ ┌─────────────┐ ┌────────────────────┐  │  │
│ │ │Device Mgr   │ │Automation   │ │   User Manager     │  │  │
│ │ │             │ │Engine       │ │                    │  │  │
│ │ │- State mgmt │ │             │ │- Authentication    │  │  │
│ │ │- Commands   │ │- Triggers   │ │- Authorization     │  │  │
│ │ │- Validation │ │- Actions    │ │- Session mgmt      │  │  │
│ │ └─────────────┘ └─────────────┘ └────────────────────┘  │  │
│ └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ POSTGRESQL  │    │    REDIS    │    │ FILE SYSTEM │
│             │    │             │    │             │
│ Persistent  │    │ Cache &     │    │ Logs &      │
│ Data Store  │    │ Session     │    │ Assets      │
│             │    │ Store       │    │             │
│ - Users     │    │             │    │ - App logs  │
│ - Devices   │    │ - User data │    │ - Error logs│
│ - Rooms     │    │ - API cache │    │ - Backups   │
│ - Automations│   │ - Statistics│    │ - Static    │
│ - Logs      │    │ - Sessions  │    │   assets    │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Diagram Bazy Danych (ERD) - PostgreSQL 17.5

```
                    ┌─────────────────────────────────┐
                    │             USERS               │
                    │─────────────────────────────────│
                    │ id (UUID) PK                    │
                    │ name (VARCHAR) UNIQUE           │
                    │ email (VARCHAR) UNIQUE          │
                    │ password_hash (TEXT)            │
                    │ role (VARCHAR) DEFAULT 'user'   │
                    │ profile_picture (TEXT)          │
                    │ created_at (TIMESTAMPTZ)        │
                    │ updated_at (TIMESTAMPTZ)        │
                    └─────────────┬───────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────────────────┐
        │                         │                                     │
        │ 1:N                     │ 1:N                                 │ 1:N
        │                         │                                     │
┌───────▼─────────────┐  ┌────────▼────────────┐           ┌──────────▼──────────┐
│  MANAGEMENT_LOGS    │  │   SESSION_TOKENS    │           │   SYSTEM_SETTINGS   │
│─────────────────────│  │─────────────────────│           │─────────────────────│
│ id (UUID) PK        │  │ id (UUID) PK        │           │ id (UUID) PK        │
│ user_id (UUID) FK   │  │ user_id (UUID) FK   │           │ setting_key (VAR)   │
│ username (VARCHAR)  │  │ token_hash (VAR)    │           │ setting_value (JSON)│
│ timestamp (TSTZ)    │  │ remember_me (BOOL)  │           │ description (TEXT)  │
│ level (VARCHAR)     │  │ ip_address (INET)   │           │ updated_by (UUID)FK │
│ message (TEXT)      │  │ user_agent (TEXT)   │           │ updated_at (TSTZ)   │
│ event_type (VAR)    │  │ expires_at (TSTZ)   │           └─────────────────────┘
│ ip_address (INET)   │  │ created_at (TSTZ)   │           
│ details (JSONB)     │  │ last_used_at (TSTZ) │           
└─────────────────────┘  └─────────────────────┘           

┌─────────────────────────────────┐              ┌─────────────────────────────────┐
│            ROOMS                │              │          DEVICES                │
│─────────────────────────────────│              │─────────────────────────────────│
│ id (UUID) PK                    │              │ id (UUID) PK                    │
│ name (VARCHAR) UNIQUE           │              │ name (VARCHAR)                  │
│ display_order (INTEGER)         │              │ room_id (UUID) FK               │
│ created_at (TIMESTAMPTZ)        │              │ device_type (VARCHAR)           │
│ updated_at (TIMESTAMPTZ)        │              │ state (BOOLEAN) DEFAULT false   │
└─────────────┬───────────────────┘              │ temperature (NUMERIC(5,2))      │
              │                                  │ min_temperature (NUMERIC(5,2))  │
              │ 1:N                              │ max_temperature (NUMERIC(5,2))  │
              │                                  │ display_order (INTEGER)         │
              └──────────────────────────────────│ enabled (BOOLEAN) DEFAULT true  │
                                                 │ created_at (TIMESTAMPTZ)        │
                                                 │ updated_at (TIMESTAMPTZ)        │
                                                 └─────────────┬───────────────────┘
                                                               │
              ┌─────────────────────────────────┐              │ 1:N
              │  ROOM_TEMPERATURE_STATES        │              │
              │─────────────────────────────────│              │
              │ id (UUID) PK                    │              ▼
              │ room_id (UUID) FK UNIQUE        │    ┌─────────────────────────────────┐
              │ current_temperature (NUM(5,2))  │    │       DEVICE_HISTORY            │
              │ target_temperature (NUM(5,2))   │    │─────────────────────────────────│
              │ heating_active (BOOLEAN)        │    │ id (UUID) PK                    │
              │ last_updated (TIMESTAMPTZ)      │    │ device_id (UUID) FK             │
              └─────────────────────────────────┘    │ old_state (JSONB)               │
                                                     │ new_state (JSONB)               │
                                                     │ changed_by (UUID) FK            │
                                                     │ change_reason (VARCHAR)         │
                                                     │ created_at (TIMESTAMPTZ)        │
                                                     └─────────────────────────────────┘

┌─────────────────────────────────┐              ┌─────────────────────────────────┐
│         AUTOMATIONS             │              │     AUTOMATION_EXECUTIONS       │
│─────────────────────────────────│              │─────────────────────────────────│
│ id (UUID) PK                    │              │ id (UUID) PK                    │
│ name (VARCHAR) UNIQUE           │              │ automation_id (UUID) FK         │
│ trigger_config (JSONB)          │              │ execution_status (VARCHAR(50))  │
│ actions_config (JSONB)          │              │ trigger_data (JSONB)            │
│ enabled (BOOLEAN) DEFAULT true  │              │ actions_executed (JSONB)        │
│ last_executed (TIMESTAMPTZ)     │              │ error_message (TEXT)            │
│ execution_count (INT) DEFAULT 0 │              │ execution_time_ms (INTEGER)     │
│ error_count (INT) DEFAULT 0     │              │ executed_at (TIMESTAMPTZ)       │
│ last_error (TEXT)               │              └──┬──────────────────────────────┘
│ last_error_time (TIMESTAMPTZ)   │                 |
│ created_at (TIMESTAMPTZ)        │                 |
│ updated_at (TIMESTAMPTZ)        │                 |
└─────────────┬───────────────────┘                 |
              │                                     |
              │ 1:N                                 |
              │                                     |
              └─────────────────────────────────────┘

    ┌─────────────────────────────────┐              ┌─────────────────────────────────┐
    │    NOTIFICATION_SETTINGS        │              │   NOTIFICATION_RECIPIENTS       │
    │─────────────────────────────────│              │─────────────────────────────────│
    │ id (UUID) PK                    │              │ id (UUID) PK                    │
    │ home_id (UUID) DEFAULT gen_v4() │              │ home_id (UUID)                  │
    │ setting_key (VARCHAR(255))      │              │ email (VARCHAR(255))            │
    │ setting_value (JSONB)           │              │ user_id (UUID) FK               │
    │ created_at (TIMESTAMPTZ)        │              │ enabled (BOOLEAN) DEFAULT true  │
    │ updated_at (TIMESTAMPTZ)        │              │ created_at (TIMESTAMPTZ)        │
    │ UNIQUE(home_id, setting_key)    │              │ updated_at (TIMESTAMPTZ)        │
    └─────────────────────────────────┘              └─────────────────────────────────┘
```
```

## Diagram Sekwencji - Sterowanie Urządzeniem

```
Client          WebSocket Handler    SmartHome Core    Database Manager    Device
  │                    │                    │                │              │
  │ toggle_button      │                    │                │              │
  │──────────────────► │                    │                │              │
  │                    │ validate_session   │                │              │
  │                    │──────────────────► │                │              │
  │                    │                    │ get_user_data  │              │
  │                    │                    │──────────────► │              │
  │                    │                    │ ◄──────────────│              │
  │                    │ ◄──────────────────│                │              │
  │                    │                    │                │              │
  │                    │ toggle_device      │                │              │
  │                    │──────────────────► │                │              │
  │                    │                    │ get_device     │              │
  │                    │                    │──────────────► │              │
  │                    │                    │ ◄──────────────│              │
  │                    │                    │                │              │
  │                    │                    │ validate_action│              │
  │                    │                    │──────────────► │              │
  │                    │                    │                │ send_command │
  │                    │                    │                │────────────► │
  │                    │                    │                │ ◄────────────│
  │                    │                    │                │              │
  │                    │                    │ update_device_state           │
  │                    │                    │──────────────► │              │
  │                    │                    │ ◄──────────────│              │
  │                    │                    │                │              │
  │                    │                    │ log_action     │              │
  │                    │                    │──────────────► │              │
  │                    │                    │ ◄──────────────│              │
  │                    │ ◄──────────────────│                │              │
  │                    │                    │                │              │
  │ device_updated     │                    │                │              │
  │◄───────────────────│                    │                │              │
  │                    │                    │                │              │
  │ broadcast to all   │                    │                │              │
  │◄───────────────────│                    │                │              │
```

## Diagram Procesu Automatyzacji

```
Automation Engine     Trigger Manager     Action Manager     Device Manager     Database
       │                     │                   │                │              │
       │ check_triggers      │                   │                │              │
       │────────────────────►│                   │                │              │
       │                     │ evaluate_time     │                │              │
       │                     │─────────────────► │                │              │
       │                     │ evaluate_device   │                │              │
       │                     │─────────────────► │                │              │
       │                     │ evaluate_weather  │                │              │
       │                     │─────────────────► │                │              │
       │ ◄───────────────────│                   │                │              │
       │                     │                   │                │              │
       │ trigger_found       │                   │                │              │
       │ ──────────────────────────────────────► │                │              │
       │                     │                   │ execute_actions│              │
       │                     │                   │──────────────► │              │
       │                     │                   │                │ send_commands│
       │                     │                   │                │────────────► │
       │                     │                   │                │              │
       │                     │                   │ ◄──────────────│              │
       │                     │                   │                │              │
       │ ◄───────────────────────────────────────│                │              │
       │                     │                   │                │              │
       │ log_execution       │                   │                │              │
       │───────────────────────────────────────────────────────────────────────► │
       │ ◄───────────────────────────────────────────────────────────────────────│
       │                     │                   │                │              │
       │ update_statistics   │                   │                │              │
       │───────────────────────────────────────────────────────────────────────► │
       │ ◄───────────────────────────────────────────────────────────────────────│
```

## Diagram Deployment (Docker)

```
                               HOST MACHINE
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                                                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐    │
    │  │                    DOCKER NETWORK (smarthome_net)               │    │
    │  │                                                                 │    │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │    │
    │  │  │   NGINX     │  │  FLASK APP  │  │  FLASK APP  │              │    │
    │  │  │ Container   │  │ Container 1 │  │ Container 2 │              │    │
    │  │  │             │  │             │  │             │              │    │
    │  │  │ Port: 80    │  │ Port: 5000  │  │ Port: 5001  │              │    │
    │  │  │ Port: 443   │  │             │  │             │              │    │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘              │    │
    │  │                                                                 │    │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │    │
    │  │  │ PostgreSQL  │  │    Redis    │  │   Backup    │              │    │
    │  │  │ Container   │  │ Container   │  │  Container  │              │    │
    │  │  │             │  │             │  │             │              │    │
    │  │  │ Port: 5432  │  │ Port: 6379  │  │ Cron Jobs   │              │    │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘              │    │
    │  └─────────────────────────────────────────────────────────────────┘    │
    │                                                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐    │
    │  │                      DOCKER VOLUMES                             │    │
    │  │                                                                 │    │
    │  │  postgres_data  │  redis_data  │  nginx_logs  │  app_logs       │    │
    │  │  nginx_ssl      │  backups     │  uploads     │  static_files   │    │
    │  └─────────────────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────────────────┘

    External Ports:
    80 (HTTP) ────► NGINX ────► Flask Apps (5000, 5001)
    443 (HTTPS) ──► NGINX ────► Flask Apps (5000, 5001)
    5432 (PostgreSQL) ────────► PostgreSQL Container
    6379 (Redis) ─────────────► Redis Container
```

## Performance Monitoring Dashboard Schema

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        PERFORMANCE METRICS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  RESPONSE TIME  │  │  THROUGHPUT     │  │  ERROR RATE     │            │
│  │                 │  │                 │  │                 │            │
│  │  Avg: 120ms     │  │  1000 req/s     │  │  0.01%          │            │
│  │  95%: 250ms     │  │  Peak: 1500/s   │  │  Errors: 1/10k  │            │
│  │  99%: 500ms     │  │  Min: 100/s     │  │  Timeouts: 0    │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  CACHE STATS    │  │  DATABASE       │  │  SYSTEM LOAD    │            │
│  │                 │  │                 │  │                 │            │
│  │  Hit Rate: 78%  │  │  Connections:15 │  │  CPU: 45%       │            │
│  │  Misses: 22%    │  │  Query Time:45ms│  │  Memory: 62%    │            │
│  │  Evictions: 12  │  │  Slow Queries:2 │  │  Disk I/O: 15%  │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                           ACTIVE CONNECTIONS                         │ │
│  │                                                                      │ │
│  │  WebSocket Connections: 45                                           │ │
│  │  HTTP Connections: 128                                               │ │
│  │  Database Connections: 8/20                                          │ │
│  │  Redis Connections: 12                                               │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────┘
```

## Security Architecture Diagram

```
                         ┌─────────────────────────────────────┐
                         │          EXTERNAL THREATS           │
                         │                                     │
                         │  • DDoS Attacks                     │
                         │  • SQL Injection                    │
                         │  • XSS Attacks                      │
                         │  • Brute Force                      │
                         │  • Man in the Middle                │
                         └─────────────┬───────────────────────┘
                                       │
                         ┌─────────────▼───────────────────────┐
                         │         SECURITY LAYERS             │
                         ├─────────────────────────────────────┤
                         │                                     │
┌────────────────────────┼─────────────────────────────────────┼────────────────────────┐
│       LAYER 1          │          NETWORK SECURITY           │        NGINX           │
├────────────────────────┼─────────────────────────────────────┼────────────────────────┤
│ • Rate Limiting        │                                     │ • SSL/TLS Termination  │
│ • IP Filtering         │                                     │ • HTTP Headers         │
│ • DDoS Protection      │                                     │ • Request Filtering    │
└────────────────────────┼─────────────────────────────────────┼────────────────────────┘
                         │                                     │
┌────────────────────────┼─────────────────────────────────────┼────────────────────────┐
│       LAYER 2          │       APPLICATION SECURITY          │     FLASK APP          │
├────────────────────────┼─────────────────────────────────────┼────────────────────────┤
│ • Session Management   │                                     │ • Input Validation     │
│ • CSRF Protection      │                                     │ • Authentication       │
│ • XSS Prevention       │                                     │ • Authorization        │
│ • SQL Injection Protect│                                     │ • Secure Headers       │
└────────────────────────┼─────────────────────────────────────┼────────────────────────┘
                         │                                     │
┌────────────────────────┼─────────────────────────────────────┼────────────────────────┐
│       LAYER 3          │           DATA SECURITY             │     POSTGRESQL         │
├────────────────────────┼─────────────────────────────────────┼────────────────────────┤
│ • Password Hashing     │                                     │• Connection Encryption │
│ • Data Encryption      │                                     │• Access Control        │
│ • Audit Logging        │                                     │• Query Parameterization│
│ • Backup Encryption    │                                     │• Row Level Security    │
└────────────────────────┼─────────────────────────────────────┼────────────────────────┘
                         │                                     │
                         └─────────────────────────────────────┘

Security Implementation Details:

┌─────────────────────────────────────────────────────────────────────────────┐
│                            AUTHENTICATION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. User Login ──► 2. Password Verification ──► 3. Session Creation         │
│      │                     │                           │                    │
│      ▼                     ▼                           ▼                    │
│  Input Validation    Bcrypt Hashing             Secure Cookie               │
│  Rate Limiting       Password Strength          HTTPOnly Flag               │
│  CAPTCHA (optional)  Salt Generation           SameSite=Lax                 │
│                                                                             │
│  4. Token Generation ──► 5. Permission Check ──► 6. Access Granted          │
│      │                       │                         │                    │
│      ▼                       ▼                         ▼                    │
│  JWT/Session Token     Role-Based Access        Audit Logging               │
│  Expiration Time       Resource Permissions     Activity Tracking           │
│  Refresh Mechanism     Dynamic Authorization    Security Events             │
└─────────────────────────────────────────────────────────────────────────────┘
```
