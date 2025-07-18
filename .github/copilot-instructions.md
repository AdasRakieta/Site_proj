# Copilot Instructions for Smart Home Flask Project

## Project Overview

- This is a Flask-based smart home management system with real-time features using Flask-SocketIO.
- The main entry point is `app.py`, but most route and API logic is organized in `routes.py` (see `RoutesManager`, `APIManager`, `SocketManager`).
- Core business logic and state are managed by the `SmartHomeSystem` class in `configure.py`.
- Email notifications and alerting are handled by `mail_manager.py`.
- Static assets (JS, CSS, images) are in `static/`, and HTML templates are in `templates/`.

## Key Architectural Patterns

- **Blueprint-like pattern**: Instead of Flask Blueprints, route registration is encapsulated in manager classes (`RoutesManager`, `APIManager`, `SocketManager`) in `routes.py`.
- **Stateful Singleton**: `SmartHomeSystem` is instantiated once and shared across the app for all state (users, rooms, automations, etc.).
- **Session-based Auth**: User authentication and roles are managed via Flask sessions. Decorators like `login_required` and `admin_required` enforce access control.
- **Real-time Updates**: State changes (e.g., buttons, temperature controls) are broadcast to clients using SocketIO events.
- **Config Persistence**: All state is periodically saved to JSON files (`smart_home_config.json`, etc.) by the backend.

## Developer Workflows

- **Run locally**: `python app.py` (Flask-SocketIO will run the server on port 5000)
- **Dependencies**: Install with `pip install -r requirements.txt`
- **Configuration**: Email and notification settings are loaded from `.env` and JSON files in the project root.
- **Debugging**: Logging is enabled in `app.py` when run as `__main__`.
- **No standard tests**: No test suite or test runner is present by default.

## Project-Specific Conventions

- **User IDs**: Users are stored by UUID, not username. Always use `user_id` for lookups.
- **Profile Pictures**: Uploaded to `static/profile_pictures/` and referenced by URL in user profiles.
- **Automations**: Defined as JSON objects with triggers and actions, stored in the main config.
- **CSRF & Host Checks**: Custom CSRF and trusted host logic in `app.py`—update `is_trusted_host` for new subnets.
- **Role Checks**: Use `session['role']` and decorators for admin/user separation.

## Integration Points

- **Email**: Uses SMTP, credentials loaded from `email_conf.env` via `python-dotenv`.
- **Notifications**: Recipients and settings are managed in JSON and encrypted files.
- **SocketIO**: All real-time events are defined in `SocketManager` (see `routes.py`).

## Examples

- To add a new API endpoint, extend `APIManager` in `routes.py` and register the route in `register_routes()`.
- To add a new automation type, update the logic in `configure.py` and the relevant SocketIO handlers.
- To add a new static asset, place it in `static/` and reference it in the appropriate template in `templates/`.

## Key Files

- `app.py`: App entry, session/csrf/auth logic, background tasks
- `routes.py`: All HTTP and SocketIO routes, main app logic
- `configure.py`: SmartHomeSystem state, config persistence
- `mail_manager.py`: Email/notification logic
- `static/`, `templates/`: Frontend assets

---

If you are unsure about a workflow or pattern, check `routes.py` for route logic, or `configure.py` for state management. For new features, follow the encapsulation and registration patterns used in these files.
