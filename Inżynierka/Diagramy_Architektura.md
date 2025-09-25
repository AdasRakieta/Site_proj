# Diagramy i Schematy Architektury - System SmartHome

## Diagram Architektury Systemu

```
┌─────────────────────────────────────────────────────────────────────────────┐
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
                              
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                  │
├─────────────────────┬───────────────────────┬───────────────────────────────┤
│   WEB BROWSERS      │    MOBILE APPS        │      IoT DEVICES              │
│                     │                       │                               │
│ ┌─────────────────┐ │ ┌───────────────────┐ │ ┌───────────────────────────┐ │
│ │ Chrome/Firefox  │ │ │ Android/iOS App   │ │ │ Smart Lights              │ │
│ │ Safari/Edge     │ │ │ REST API Client   │ │ │ Temperature Sensors       │ │
│ │ JavaScript SPA  │ │ │ WebSocket Client  │ │ │ Security Cameras          │ │
│ │ WebSocket       │ │ │ Push Notifications│ │ │ Door Locks                │ │
│ └─────────────────┘ │ └───────────────────┘ │ └───────────────────────────┘ │
└─────────────────────┴───────────────────────┴───────────────────────────────┘
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
│ ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│ │ Routes      │  │ WebSocket    │  │ Background Tasks    │  │
│ │ Manager     │  │ Handler      │  │                     │  │
│ │             │  │              │  │ - Email sending     │  │
│ │ - Login     │  │ - Real-time  │  │ - Automation engine │  │
│ │ - API       │  │   updates    │  │ - Log processing    │  │
│ │ - Dashboard │  │ - Device     │  │ - Cache warming     │  │
│ │ - Admin     │  │   control    │  │                     │  │
│ └─────────────┘  └──────────────┘  └─────────────────────┘  │
│         │                │                      │           │
│         ▼                ▼                      ▼           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              SMART HOME CORE ENGINE                     │ │
│ │                                                         │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌────────────────────┐ │ │
│ │ │Device Mgr   │ │Automation   │ │   User Manager     │ │ │
│ │ │             │ │Engine       │ │                    │ │ │
│ │ │- State mgmt │ │             │ │- Authentication    │ │ │
│ │ │- Commands   │ │- Triggers   │ │- Authorization     │ │ │
│ │ │- Validation │ │- Actions    │ │- Session mgmt      │ │ │
│ │ └─────────────┘ └─────────────┘ └────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
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

## Diagram Bazy Danych (ERD)

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
                    │ created_at (TIMESTAMP)          │
                    │ updated_at (TIMESTAMP)          │
                    └─────────────┬───────────────────┘
                                  │
                                  │ 1:N
                                  │
                    ┌─────────────▼───────────────────┐
                    │       MANAGEMENT_LOGS           │
                    │─────────────────────────────────│
                    │ id (UUID) PK                    │
                    │ user_id (UUID) FK               │
                    │ action (VARCHAR)                │
                    │ details (JSONB)                 │
                    │ ip_address (INET)               │
                    │ timestamp (TIMESTAMP)           │
                    └─────────────────────────────────┘

┌─────────────────────────────────┐              ┌─────────────────────────────────┐
│            ROOMS                │              │          DEVICES                │
│─────────────────────────────────│              │─────────────────────────────────│
│ id (UUID) PK                    │              │ id (UUID) PK                    │
│ name (VARCHAR) UNIQUE           │              │ name (VARCHAR)                  │
│ display_order (INTEGER)         │              │ room_id (UUID) FK               │
│ created_at (TIMESTAMP)          │              │ device_type (VARCHAR)           │
│ updated_at (TIMESTAMP)          │              │ state (BOOLEAN)                 │
└─────────────┬───────────────────┘              │ temperature (NUMERIC)           │
              │                                  │ min_temperature (NUMERIC)       │
              │ 1:N                              │ max_temperature (NUMERIC)       │
              │                                  │ display_order (INTEGER)         │
              └──────────────────────────────────│ enabled (BOOLEAN)               │
                                                 │ created_at (TIMESTAMP)          │
                                                 │ updated_at (TIMESTAMP)          │
                                                 └─────────────────────────────────┘

┌─────────────────────────────────┐              ┌─────────────────────────────────┐
│         AUTOMATIONS             │              │     AUTOMATION_EXECUTIONS       │
│─────────────────────────────────│              │─────────────────────────────────│
│ id (UUID) PK                    │              │ id (UUID) PK                    │
│ name (VARCHAR) UNIQUE           │              │ automation_id (UUID) FK         │
│ trigger_config (JSONB)          │              │ execution_status (VARCHAR)      │
│ actions_config (JSONB)          │              │ trigger_data (JSONB)            │
│ enabled (BOOLEAN)               │              │ actions_executed (JSONB)        │
│ last_executed (TIMESTAMP)       │              │ error_message (TEXT)            │
│ execution_count (INTEGER)       │              │ execution_time_ms (INTEGER)     │
│ error_count (INTEGER)           │              │ executed_at (TIMESTAMP)         │
│ last_error (TEXT)               │              └─────────────────────────────────┘
│ last_error_time (TIMESTAMP)     │
│ created_at (TIMESTAMP)          │
│ updated_at (TIMESTAMP)          │
└─────────────┬───────────────────┘
              │
              │ 1:N
              │
              └──────────────────────────────────┘


                    ┌─────────────────────────────────┐
                    │    NOTIFICATION_SETTINGS        │
                    │─────────────────────────────────│
                    │ home_id (UUID)                  │
                    │ key (VARCHAR)                   │
                    │ value (JSONB)                   │
                    │ PRIMARY KEY (home_id, key)      │
                    └─────────────────────────────────┘

                    ┌─────────────────────────────────┐
                    │   NOTIFICATION_RECIPIENTS       │
                    │─────────────────────────────────│
                    │ id (UUID) PK                    │
                    │ home_id (UUID)                  │
                    │ email (VARCHAR)                 │
                    │ user_id (UUID) FK               │
                    │ enabled (BOOLEAN)               │
                    └─────────────────────────────────┘
```

## Diagram Sekwencji - Sterowanie Urządzeniem

```
Client          WebSocket Handler    SmartHome Core    Database Manager    Device
  │                    │                    │                │              │
  │ toggle_button      │                    │                │              │
  │──────────────────►│                    │                │              │
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
       │ check_triggers       │                   │                │              │
       │────────────────────► │                   │                │              │
       │                     │ evaluate_time     │                │              │
       │                     │─────────────────► │                │              │
       │                     │ evaluate_device   │                │              │
       │                     │─────────────────► │                │              │
       │                     │ evaluate_weather  │                │              │
       │                     │─────────────────► │                │              │
       │ ◄────────────────────│                   │                │              │
       │                     │                   │                │              │
       │ trigger_found        │                   │                │              │
       │ ────────────────────────────────────────► │                │              │
       │                     │                   │ execute_actions│              │
       │                     │                   │──────────────► │              │
       │                     │                   │                │ send_commands│
       │                     │                   │                │────────────► │
       │                     │                   │                │              │
       │                     │                   │ ◄──────────────│              │
       │                     │                   │                │              │
       │ ◄────────────────────────────────────────│                │              │
       │                     │                   │                │              │
       │ log_execution        │                   │                │              │
       │─────────────────────────────────────────────────────────────────────────► │
       │ ◄─────────────────────────────────────────────────────────────────────────│
       │                     │                   │                │              │
       │ update_statistics    │                   │                │              │
       │─────────────────────────────────────────────────────────────────────────► │
       │ ◄─────────────────────────────────────────────────────────────────────────│
```

## Diagram Deployment (Docker)

```
                               HOST MACHINE
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                                                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐    │
    │  │                    DOCKER NETWORK (smarthome_net)               │    │
    │  │                                                                 │    │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │    │
    │  │  │   NGINX     │  │  FLASK APP  │  │  FLASK APP  │            │    │
    │  │  │ Container   │  │ Container 1 │  │ Container 2 │            │    │
    │  │  │             │  │             │  │             │            │    │
    │  │  │ Port: 80    │  │ Port: 5000  │  │ Port: 5001  │            │    │
    │  │  │ Port: 443   │  │             │  │             │            │    │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘            │    │
    │  │                                                                 │    │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │    │
    │  │  │ PostgreSQL  │  │    Redis    │  │   Backup    │            │    │
    │  │  │ Container   │  │ Container   │  │  Container  │            │    │
    │  │  │             │  │             │  │             │            │    │
    │  │  │ Port: 5432  │  │ Port: 6379  │  │ Cron Jobs   │            │    │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘            │    │
    │  └─────────────────────────────────────────────────────────────────┘    │
    │                                                                         │
    │  ┌─────────────────────────────────────────────────────────────────┐    │
    │  │                      DOCKER VOLUMES                            │    │
    │  │                                                                 │    │
    │  │  postgres_data  │  redis_data  │  nginx_logs  │  app_logs      │    │
    │  │  nginx_ssl      │  backups     │  uploads     │  static_files  │    │
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
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PERFORMANCE METRICS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  RESPONSE TIME  │  │  THROUGHPUT     │  │  ERROR RATE     │            │
│  │                 │  │                 │  │                 │            │
│  │  Avg: 120ms     │  │  1000 req/s     │  │  0.01%          │            │
│  │  95%: 250ms     │  │  Peak: 1500/s   │  │  Errors: 1/10k  │            │
│  │  99%: 500ms     │  │  Min: 100/s     │  │  Timeouts: 0    │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  CACHE STATS    │  │  DATABASE       │  │  SYSTEM LOAD    │            │
│  │                 │  │                 │  │                 │            │
│  │  Hit Rate: 78%  │  │  Connections:15 │  │  CPU: 45%       │            │
│  │  Misses: 22%    │  │  Query Time:45ms│  │  Memory: 62%    │            │
│  │  Evictions: 12  │  │  Slow Queries:2 │  │  Disk I/O: 15%  │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                           ACTIVE CONNECTIONS                          │ │
│  │                                                                       │ │
│  │  WebSocket Connections: 45                                           │ │
│  │  HTTP Connections: 128                                               │ │
│  │  Database Connections: 8/20                                          │ │
│  │  Redis Connections: 12                                               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Security Architecture Diagram

```
                         ┌─────────────────────────────────────┐
                         │            EXTERNAL THREATS        │
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
│       LAYER 1          │          NETWORK SECURITY          │        NGINX           │
├────────────────────────┼─────────────────────────────────────┼────────────────────────┤
│ • Rate Limiting        │                                     │ • SSL/TLS Termination  │
│ • IP Filtering         │                                     │ • HTTP Headers         │
│ • DDoS Protection      │                                     │ • Request Filtering    │
└────────────────────────┼─────────────────────────────────────┼────────────────────────┘
                         │                                     │
┌────────────────────────┼─────────────────────────────────────┼────────────────────────┐
│       LAYER 2          │       APPLICATION SECURITY         │     FLASK APP          │
├────────────────────────┼─────────────────────────────────────┼────────────────────────┤
│ • Session Management   │                                     │ • Input Validation     │
│ • CSRF Protection      │                                     │ • Authentication       │
│ • XSS Prevention       │                                     │ • Authorization        │
│ • SQL Injection Protect│                                     │ • Secure Headers       │
└────────────────────────┼─────────────────────────────────────┼────────────────────────┘
                         │                                     │
┌────────────────────────┼─────────────────────────────────────┼────────────────────────┐
│       LAYER 3          │          DATA SECURITY             │     POSTGRESQL         │
├────────────────────────┼─────────────────────────────────────┼────────────────────────┤
│ • Password Hashing     │                                     │ • Connection Encryption│
│ • Data Encryption      │                                     │ • Access Control       │
│ • Audit Logging        │                                     │ • Query Parameterization│
│ • Backup Encryption    │                                     │ • Row Level Security   │
└────────────────────────┼─────────────────────────────────────┼────────────────────────┘
                         │                                     │
                         └─────────────────────────────────────┘

Security Implementation Details:

┌─────────────────────────────────────────────────────────────────────────────┐
│                            AUTHENTICATION FLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. User Login ──► 2. Password Verification ──► 3. Session Creation         │
│      │                     │                           │                    │
│      ▼                     ▼                           ▼                    │
│  Input Validation    Bcrypt Hashing             Secure Cookie               │
│  Rate Limiting       Password Strength          HTTPOnly Flag               │
│  CAPTCHA (optional)  Salt Generation           SameSite=Lax                │
│                                                                             │
│  4. Token Generation ──► 5. Permission Check ──► 6. Access Granted         │
│      │                       │                         │                    │
│      ▼                       ▼                         ▼                    │
│  JWT/Session Token     Role-Based Access        Audit Logging              │
│  Expiration Time       Resource Permissions     Activity Tracking          │
│  Refresh Mechanism     Dynamic Authorization    Security Events            │
└─────────────────────────────────────────────────────────────────────────────┘
```
