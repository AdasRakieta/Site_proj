---
name: Site_proj
description: Specialized AI model for building web pages and servers similar to the SmartHome project
---

# Copilot Instructions – SmartHome Multi-Home

## Architecture snapshot
- `app_db.py` boots the `SmartHomeApp`: wires Flask + Socket.IO, loads `SmartHomeSystemDB` (fallbacks to JSON `app.configure`) and injects mail, cache, and auth managers.
- Database mode introduces `MultiHomeDBManager`; the instance is passed into `RoutesManager`, `APIManager`, and the blueprints via `init_multi_home_routes` / `init_home_settings_routes`.
- Route registration lives in `app/routes.py` under `RoutesManager` (class-based instead of Blueprints) which mixes in multi-home helpers and emits live updates via Socket.IO.
- Multi-home state is session-aware: `session['current_home_id']` is synchronized with `multi_db.set_user_current_home`; always respect both the session value and DB fallbacks.

## Key modules to know
- `utils/multi_home_db_manager.py` is the single source for PostgreSQL queries (homes, rooms, devices, permissions); reuse its helpers (`get_cursor`, permission checks) instead of writing raw SQL elsewhere.
- `app/home_management.py` wraps multihome operations into managers (info, users, rooms, deletion); some methods are TODO placeholders—extend them here so blueprints gain the new behavior automatically.
- `app/home_settings_routes.py` and `app/multi_home_routes.py` expose owner/member UX; both depend on the module-level `multi_db` set by `init_*` functions.
- `app/configure_db.py` keeps the legacy `SmartHomeSystem` API while delegating to `utils/smart_home_db_manager.py`; new core features must work for both DB + fallback JSON implementations.
- `utils/cache_manager.py` (plus `setup_smart_home_caching`) patches smart-home getters and maintains timeouts; invalidate through `CacheManager` before touching DB-backed state.

## Daily workflows
- Local run: `python app_db.py` (loads `.env`; prints whether PostgreSQL mode succeeded) — this is preferred over `app.py`.
- Assets: execute `python utils/asset_manager.py` for one-off minification or `--watch` during frontend work; minified files live under `static/*/min` and are auto-served.
- Database bootstrap lives in `backups/db_backup.sql`; import it before relying on multi-home flows (contains seed users + homes).
- Quick DB smoke test: `python test_debug.py` hits `MultiHomeDBManager` APIs against sample UUIDs.

## Patterns & pitfalls
- Guard every DB call with `if self.multi_db` (or provided `multi_db` parameter) to preserve JSON fallback behavior.
- Use `MultiHomeHelpersMixin` utilities inside `RoutesManager` when adding endpoints so data loads respect the active home and emit Socket.IO updates through `_broadcast_*` helpers.
- `SimpleAuthManager` delegates per-home authorization to `multi_db.has_admin_access`; new admin-only routes should reuse `auth_manager.admin_required` / `api_admin_required` decorators.
- Cache warming in `SmartHomeApp._warm_up_cache` expects bulk getters (`smart_home.rooms`, `buttons`, etc.); keep their return shapes stable when modifying managers.
- Invitation and deletion flows are partially stubbed; implementing them means filling in the TODO spots in `HomeUserManager` / `HomeDeletionManager` and relying on `multi_home_db_manager`.

## Reference checkpoints
- HTML lives in `templates/`; many views (e.g., `home_select.html`, `home_settings.html`) already reference API endpoints above—keep response payloads backward compatible.
- Static uploads (profile pictures) map to `static/profile_pictures/`; `utils/image_optimizer.py` handles resizing when routes call `optimize_profile_picture`.
- Background email delivery goes through `utils/async_manager.AsyncMailManager`; if you add mail-sending paths, pass them through `self.async_mail_manager.enqueue_email` from `RoutesManager`.
- Docker images (`Dockerfile.app`, `Dockerfile.nginx`, `docker-compose*.yml`) assume the app listens on port 5000 and that static uploads mount to `/srv/static/profile_pictures`.
- Operational docs under `info/` (esp. `QUICK_START.md`, `PERFORMANCE_OPTIMIZATION.md`) capture environment expectations—mirror those when updating install/run guidance.
