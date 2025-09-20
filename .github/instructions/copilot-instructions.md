# Copilot Instructions for SmartHome (Flask + SocketIO, DB-first)

This codebase is a Flask-SocketIO smart home app with PostgreSQL as the primary datastore and a JSON fallback. Follow these project-specific patterns and conventions when adding or changing code.

Core architecture
- Entry: `app_db.py` (class `SmartHomeApp`). Prefers DB mode via `app/configure_db.py:SmartHomeSystemDB` backed by `utils/smart_home_db_manager.py` (connection pool, CRUD). Falls back to JSON mode via `app/configure.py` only if DB init fails.
- Routes & REST API: `app/routes.py` (`RoutesManager`, `APIManager`). WebSocket events are primarily registered in `SmartHomeApp.setup_socket_events()` in `app_db.py`. A legacy `SocketManager` exists in `routes.py`; prefer the handlers in `app_db.py`.
- Auth: `app/simple_auth.py:SimpleAuthManager` with Flask session (`session['user_id']`). Use decorators: `login_required`, `admin_required`, `api_login_required`, `api_admin_required`.
- Logging: Use `app/database_management_logger.py:DatabaseManagementLogger` (DB-backed). Prefer helpers like `log_login`, `log_user_change`, `log_device_action`.

Caching and preloading
- Caching: `utils/cache_manager.py` provides `CacheManager`, `CachedDataAccess`, and `setup_smart_home_caching`. Cache via Redis if `REDIS_URL`/`REDIS_HOST` is set; otherwise SimpleCache. Invalidate with: `invalidate_buttons_cache`, `invalidate_temperature_cache`, `invalidate_rooms_cache`, `invalidate_automations_cache`.
- Read paths should prefer cached access (`CachedDataAccess`) or DB-backed properties (`smart_home.rooms/buttons/temperature_controls/automations`). Write paths MUST call proper methods (`add_*`, `update_*`, `delete_*`, `update_button_state`, `update_temperature_control_value`) and then invalidate relevant caches and emit socket updates.
- Template preloading: Key pages embed initial JSON to eliminate first-load AJAX. See `templates/index.html` (rooms) and `templates/admin_dashboard.html` (device states, logs, users) and the JS “preloaded*” overrides.

Data and conventions
- Users/devices/rooms/automations live in PostgreSQL; properties on `SmartHomeSystemDB` return fresh DB-backed snapshots. Do NOT assign directly to these properties in DB mode—use methods.
- Always identify users by UUID (`user_id`) and devices by `id`. Room names are case-insensitive for lookups.
- Keep SocketIO auth checks: handlers should require `session['user_id']` and respond with broadcasts like `update_button`, `sync_button_states`, `update_temperature`, `update_security_state`.

Adding endpoints or features
- New REST endpoints: extend `APIManager.register_routes()` in `app/routes.py`. Enforce auth via decorators, call DB methods, invalidate cache, emit socket events, and return JSON with a top-level `status` field.
- New WebSocket behavior: add handlers in `SmartHomeApp.setup_socket_events()` (prefer) and mirror the REST behavior: validate session, update via DB methods, broadcast, invalidate caches, and log.
- UI data flow: when possible, pre-load data via template context and implement a one-time JS override that uses preloaded data first and only fetches on manual refresh.

Running locally
- Dependencies: `pip install -r requirements.txt`.
- Env: configure `.env` with `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and optionally `REDIS_URL` or `REDIS_HOST`/`REDIS_PORT`.
- Start: `python app_db.py` (SocketIO server). The app prints DB/caching mode at startup.

Key files
- `app_db.py`: App composition root, SocketIO, warm-up, diagnostics.
- `app/routes.py`: HTTP routes and REST API managers.
- `app/configure_db.py`: `SmartHomeSystemDB` facade over `utils/smart_home_db_manager.py`.
- `utils/cache_manager.py`: Caching, cache stats (`/api/cache/stats`).
- `app/database_management_logger.py`: DB-backed management logs.
- `templates/`: Preloading patterns in `index.html` and `admin_dashboard.html`.

Tip: When unsure, trace calls from `app_db.SmartHomeApp` to `RoutesManager`/`APIManager` and the `SmartHomeSystemDB` methods. Keep DB-first, cache-aware, preloaded-first rendering in mind for performance.
