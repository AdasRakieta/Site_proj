# Architektura Systemu SmartHome - Diagramy i Schematy

## 1. Diagram Architektury Ogólnej

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET/WAN                                  │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────────┐
│                         NGINX REVERSE PROXY                                │
│                     SSL Termination & Load Balancing                       │
│                          (Docker Container)                                │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│   FLASK APP 1   │  │   FLASK APP 2   │  │   FLASK APP 3   │
│  (app_db.py)    │  │  (app_db.py)    │  │  (app_db.py)    │
│                 │  │                 │  │                 │
│ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
│ │ Routes Mgr  │ │  │ │ Routes Mgr  │ │  │ │ Routes Mgr  │ │
│ │ Socket Mgr  │ │  │ │ Socket Mgr  │ │  │ │ Socket Mgr  │ │
│ │ Cache Mgr   │ │  │ │ Cache Mgr   │ │  │ │ Cache Mgr   │ │
│ │ DB Manager  │ │  │ │ DB Manager  │ │  │ │ DB Manager  │ │
│ │ Auth Mgr    │ │  │ │ Auth Mgr    │ │  │ │ Auth Mgr    │ │
│ │ Mail Mgr    │ │  │ │ Mail Mgr    │ │  │ │ Mail Mgr    │ │
│ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
    │                         │                         │
┌───▼──────────────┐    ┌─────▼──────────┐    ┌────────▼────────┐
│  POSTGRESQL 17.5 │    │     REDIS      │    │  FILE STORAGE   │
│  (Main Database) │    │    (Cache)     │    │ (Logs & Assets) │
│                  │    │                │    │                 │
│ ┌──────────────┐ │    │ ┌────────────┐ │    │ ┌─────────────┐ │
│ │ 12 Tables:   │ │    │ │Session Data│ │    │ │ App Logs    │ │
│ │ • users      │ │    │ │API Cache   │ │    │ │ Error Logs  │ │
│ │ • devices    │ │    │ │User Cache  │ │    │ │ Static CSS  │ │
│ │ • rooms      │ │    │ │Device Stats│ │    │ │ Static JS   │ │
│ │ • automations│ │    │ │Statistics  │ │    │ │ Profile Pics│ │
│ │ • device_hist│ │    │ └────────────┘ │    │ │ Backups     │ │
│ │ • mgmt_logs  │ │    └────────────────┘    │ └─────────────┘ │
│ │ • sessions   │ │                          └─────────────────┘
│ │ • settings   │ │   
│ │ • notifications│ │   
│ │ • temp_states│ │   
│ │ • auto_exec  │ │   
│ └──────────────┘ │   
└──────────────────┘   

┌─────────────────────────────────────────────────────┐
│                   CLIENT LAYER                      │
├─────────────────────┬───────────────────────────────┤
│   WEB BROWSERS      │      IoT DEVICES              │
│                     │                               │
│ ┌─────────────────┐ │ ┌───────────────────────────┐ │
│ │ Desktop/Mobile  │ │ │ Smart Lights              │ │
│ │ Chrome/Firefox  │ │ │ Temperature Sensors       │ │
│ │ Safari/Edge     │ │ │ Security Cameras          │ │
│ │ JavaScript SPA  │ │ │ Door Locks                │ │
│ │ WebSocket       │ │ │ Smart Switches            │ │
│ │ Real-time UI    │ │ │ HVAC Controllers          │ │
│ └─────────────────┘ │ └───────────────────────────┘ │
└─────────────────────┴───────────────────────────────┘
```

## 2. Przepływ Danych w Systemie

```
┌─────────────┐    HTTP/WebSocket    ┌─────────────────┐
│   CLIENT    │◄────────────────────►│  NGINX PROXY    │
│ (Browser/   │                      │                 │
│  Mobile)    │      Request         │ SSL/TLS         │
└─────────────┘                      │ Load Balancing  │
                                     └─────────┬───────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FLASK APPLICATION (app_db.py)                         │
│                                                                                 │
│ ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│ │ Routes      │  │ WebSocket    │  │ Background   │  │ Cache Manager       │   │
│ │ Manager     │  │ Handler      │  │ Tasks        │  │                     │   │
│ │             │  │              │  │              │  │ - Redis/SimpleCache │   │
│ │ - /         │  │ - Real-time  │  │ - Email      │  │ - Session caching   │   │
│ │ - /login    │  │   updates    │  │   sending    │  │ - API caching       │   │
│ │ - /api/*    │  │ - Device     │  │ - Automation │  │ - Statistics cache  │   │
│ │ - /admin    │  │   control    │  │   engine     │  │ - Cache invalidation│   │
│ │ - /settings │  │ - User sync  │  │ - Log cleanup│  │                     │   │
│ └─────────────┘  └──────────────┘  └──────────────┘  └─────────────────────┘   │
│         │                │                  │                    │            │
│         ▼                ▼                  ▼                    ▼            │
│ ┌─────────────────────────────────────────────────────────────────────────┐   │
│ │                 SMART HOME CORE ENGINE                                  │   │
│ │                                                                         │   │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │   │
│ │ │SmartHomeDB  │ │Automation   │ │Auth Manager │ │ Database Logger     │ │   │
│ │ │Manager      │ │Engine       │ │             │ │                     │ │   │
│ │ │             │ │             │ │- JWT tokens │ │- Management logs    │ │   │
│ │ │- CRUD ops   │ │- Triggers   │ │- Sessions   │ │- Device history     │ │   │
│ │ │- Connection │ │- Actions    │ │- Roles      │ │- Automation logs    │ │   │
│ │ │  pooling    │ │- Scheduler  │ │- Security   │ │- Error tracking     │ │   │
│ │ │- Transaction│ │- Execution  │ │             │ │                     │ │   │
│ │ │  management │ │  tracking   │ │             │ │                     │ │   │
│ │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘ │   │
│ └─────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ POSTGRESQL  │    │    REDIS    │    │ FILE SYSTEM │
│             │    │             │    │             │
│ Connection  │    │ Cache &     │    │ Logs &      │
│ Pool (2-10) │    │ Session     │    │ Assets      │
│             │    │ Store       │    │             │
│ Tables:     │    │             │    │ Files:      │
│ - users(12K)│    │ Keys:       │    │ - app.log   │
│ - devices   │    │ - sess:*    │    │ - error.log │
│ - rooms     │    │ - cache:*   │    │ - backups/  │
│ - automations│   │ - stats:*   │    │ - static/   │
│ - history   │    │ - user:*    │    │ - uploads/  │
│ + 7 more    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 3. Architektura Bazy Danych - Relacje ERD

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
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        │ 1:N                     │ 1:N                     │ 1:N
        │                         │                         │
┌───────▼───────────┐    ┌────────▼─────────┐    ┌─────────▼──────────┐
│ MANAGEMENT_LOGS   │    │ SESSION_TOKENS   │    │ SYSTEM_SETTINGS    │
│───────────────────│    │──────────────────│    │────────────────────│
│ id (UUID) PK      │    │ id (UUID) PK     │    │ id (UUID) PK       │
│ user_id (UUID) FK │    │ user_id (UUID) FK│    │ setting_key (VAR)  │
│ username (VARCHAR)│    │ token_hash (VAR) │    │ setting_value (JSON)│
│ timestamp (TSTZ)  │    │ expires_at (TSTZ)│    │ updated_by (UUID)FK│
│ level (VARCHAR)   │    │ ip_address (INET)│    │ description (TEXT) │
│ message (TEXT)    │    │ user_agent (TEXT)│    │ updated_at (TSTZ)  │
│ event_type (VAR)  │    │ remember_me (BOOL)│   └────────────────────┘
│ ip_address (INET) │    │ created_at (TSTZ)│  
│ details (JSONB)   │    │ last_used_at (TSTZ)│   
└───────────────────┘    └──────────────────┘  

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
              │─────────────────────────────────│              ▼
              │ id (UUID) PK                    │    ┌─────────────────────────────────┐
              │ room_id (UUID) FK UNIQUE        │    │       DEVICE_HISTORY            │
              │ current_temperature (NUM(5,2))  │    │─────────────────────────────────│
              │ target_temperature (NUM(5,2))   │    │ id (UUID) PK                    │
              │ heating_active (BOOLEAN)        │    │ device_id (UUID) FK             │
              │ last_updated (TIMESTAMPTZ)      │    │ old_state (JSONB)               │
              └─────────────────────────────────┘    │ new_state (JSONB)               │
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

## 4. Diagram Przepływu Automatyzacji

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AUTOMATION ENGINE                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
     │   TRIGGER   │         │  CONDITION  │         │   ACTION    │
     │   EVENTS    │         │  EVALUATION │         │  EXECUTION  │
     └─────────────┘         └─────────────┘         └─────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Time-based      │       │ Rule Engine     │       │ Device Control  │
│ - Cron schedule │   ──► │ - AND/OR logic  │   ──► │ - State changes │
│ - Intervals     │       │ - Comparisons   │       │ - Notifications │
│                 │       │ - Custom scripts│       │ - Email alerts  │
└─────────────────┘       └─────────────────┘       └─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Device-based    │       │ Context Data    │       │ Log & Audit     │
│ - State changes │   ──► │ - Device states │   ──► │ - Execution log │
│ - Sensor values │       │ - User presence │       │ - Performance   │
│ - Connectivity  │       │ - Time context  │       │ - Error tracking│
└─────────────────┘       └─────────────────┘       └─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ User-triggered  │       │ Database Query  │       │ System Updates  │
│ - Manual exec   │   ──► │ - Current state │   ──► │ - Device states │
│ - API calls     │       │ - History data  │       │ - Database logs │
│ - WebSocket     │       │ - User prefs    │       │ - Cache refresh │
└─────────────────┘       └─────────────────┘       └─────────────────┘

                    ┌───────────────────────────────────────┐
                    │         EXECUTION TRACKING            │
                    │                                       │
                    │  automation_executions table:        │
                    │  - execution_status                   │
                    │  - trigger_data (JSONB)               │
                    │  - actions_executed (JSONB)           │
                    │  - execution_time_ms                  │
                    │  - error_message                      │
                    │  - executed_at                        │
                    └───────────────────────────────────────┘
```

## 5. Architektura Cache i Session Management

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CACHE LAYER                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

              ┌─────────────────┐         ┌─────────────────┐
              │     REDIS       │         │  SIMPLE CACHE   │
              │   (Primary)     │         │   (Fallback)    │
              └─────────────────┘         └─────────────────┘
                       │                          │
                       ▼                          ▼
              ┌─────────────────┐         ┌─────────────────┐
              │ Cache Types:    │         │ In-Memory Dict  │
              │ - Session data  │         │ - Basic caching │
              │ - User profiles │         │ - No persistence│
              │ - Device states │         │                 │
              │ - API responses │         │                 │
              │ - Statistics    │         │                 │
              └─────────────────┘         └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SESSION MANAGEMENT                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │  Session Token  │         │   Database      │         │ Cache Storage   │
    │   Generation    │   ──►   │    Storage      │   ──►   │   (Redis)       │
    └─────────────────┘         └─────────────────┘         └─────────────────┘

    session_tokens table:               Cache Keys:
    - token_hash (UNIQUE)               - sess:{token_hash}
    - user_id (FK)                      - user:{user_id}
    - expires_at                        - user_session:{user_id}
    - ip_address (INET)               
    - user_agent (TEXT)                 TTL: 1 hour (default)
    - remember_me (BOOLEAN)             TTL: 30 days (remember_me)
    - last_used_at

                    ┌───────────────────────────────────────┐
                    │        SESSION LIFECYCLE             │
                    │                                       │
                    │  1. Login → Generate token           │
                    │  2. Store in DB + Cache              │
                    │  3. Validate on each request         │
                    │  4. Update last_used_at               │
                    │  5. Auto-cleanup expired tokens      │
                    │  6. Invalidate on logout             │
                    └───────────────────────────────────────┘
```

## 6. Bezpieczeństwo i Audyt

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            SECURITY LAYERS                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Authentication │    │  Authorization  │    │    Auditing     │    │   Data Privacy  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ • Password hash │    │ • Role-based    │    │ • Management    │    │ • Hashed        │
│   (scrypt)      │    │   access (admin │    │   logs table    │    │   passwords     │
│ • Session tokens│    │   /user)        │    │ • Device        │    │ • INET for IPs  │
│ • Remember me   │    │ • Route         │    │   history       │    │ • JSONB for     │
│ • Token expiry  │    │   protection    │    │ • Automation    │    │   sensitive     │
│ • IP tracking   │    │ • API           │    │   executions    │    │   config        │
│ • User agent    │    │   authentication│    │ • Error         │    │ • Connection    │
│   validation    │    │ • CSRF          │    │   tracking      │    │   encryption    │
│                 │    │   protection    │    │ • IP logging    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

management_logs table structure:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ id | timestamp | level | message | event_type | user_id | username | ip_address │
│────┼───────────┼───────┼─────────┼────────────┼─────────┼──────────┼────────────│
│UUID│TIMESTAMPTZ│VARCHAR│  TEXT   │  VARCHAR   │ UUID FK │ VARCHAR  │    INET    │
│────┼───────────┼───────┼─────────┼────────────┼─────────┼──────────┼────────────│
│    │           │       │         │            │         │          │            │
│    │           │ info  │ Login   │ auth       │ user123 │ admin    │192.168.1.1 │
│    │           │ warn  │ Failed  │ auth_fail  │ NULL    │ unknown  │192.168.1.5 │
│    │           │ error │ DB conn │ database   │ NULL    │ system   │127.0.0.1   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 7. Monitoring i Metryki

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            MONITORING SYSTEM                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │  Application    │         │    Database     │         │     Cache       │
    │    Metrics      │         │    Metrics      │         │    Metrics      │
    └─────────────────┘         └─────────────────┘         └─────────────────┘
             │                           │                           │
             ▼                           ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │ • Request count │         │ • Connection    │         │ • Hit ratio     │
    │ • Response time │         │   pool usage    │         │ • Memory usage  │
    │ • Error rate    │         │ • Query         │         │ • Key count     │
    │ • Active users  │         │   performance   │         │ • Eviction rate │
    │ • Device states │         │ • Table sizes   │         │ • TTL stats     │
    │ • Automation    │         │ • Lock waits    │         │                 │
    │   executions    │         │ • Transaction   │         │                 │
    │                 │         │   rollbacks     │         │                 │
    └─────────────────┘         └─────────────────┘         └─────────────────┘

Available API Endpoints for Monitoring:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ GET /api/ping           - Simple health check                                  │
│ GET /api/status         - Application status with backend info                 │  
│ GET /api/cache/stats    - Cache hit/miss ratios and memory usage              │
│ GET /api/database/stats - Database connection pool and query statistics       │
└─────────────────────────────────────────────────────────────────────────────────┘
```
