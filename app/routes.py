    # No property stubs: subclasses must provide app, multi_db, smart_home, socketio attributes directly.
from flask import render_template, jsonify, request, redirect, url_for, session, flash
from flask_socketio import emit
from werkzeug.utils import secure_filename
from utils.cache_manager import CachedDataAccess
from app.management_logger import ManagementLogger
import os
import time
import uuid
import json
import logging
from decimal import Decimal
from utils.allowed_file import allowed_file
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


def normalize_device_id(raw_id):
    """Coerce device identifiers to int when numeric, otherwise return trimmed string."""
    if raw_id is None:
        return None
    if isinstance(raw_id, int):
        return raw_id
    if isinstance(raw_id, str):
        value = raw_id.strip()
        if not value:
            return None
        if value.isdigit():
            try:
                return int(value)
            except ValueError:
                return value
        return value
    return raw_id


class MultiHomeHelpersMixin:
    def _resolve_home_id(self, user_id, preferred_home_id=None):
        """Resolve current home for the given user."""
        if not self.multi_db or not user_id:  # type: ignore
            return None

        user_id_str = str(user_id)
        home_id = preferred_home_id or session.get('current_home_id')

        if not home_id:
            try:
                home_id = self.multi_db.get_user_current_home(user_id_str)  # type: ignore
            except Exception as exc:
                if self.app:  # type: ignore
                    self.app.logger.error(f"Failed to resolve home for user {user_id_str}: {exc}")  # type: ignore
                home_id = None

        return str(home_id) if home_id else None

    def _normalize_rooms_for_response(self, rooms, default_home_id=None):
        """Normalize various room payload formats to a consistent API response."""
        normalized = []
        if not rooms:
            return normalized

        for index, room in enumerate(rooms):
            if isinstance(room, dict):
                room_id = room.get('id') or room.get('room_id')
                name = room.get('name') or room.get('room') or room.get('title')
                description = room.get('description')
                display_order = room.get('display_order', index)
                home_id = room.get('home_id', default_home_id)
            else:
                room_id = room
                name = room
                description = None
                display_order = index
                home_id = default_home_id

            if not name:
                continue

            normalized.append({
                'id': str(room_id) if room_id is not None else str(name),
                'name': str(name),
                'description': description,
                'display_order': int(display_order) if display_order is not None else index,
                'home_id': str(home_id) if home_id else None
            })

        # Ensure stable ordering by display_order then name
        normalized.sort(key=lambda r: (r.get('display_order', 0), r.get('name', '').lower()))
        return normalized

    def _get_rooms_payload(self, user_id, preferred_home_id=None):
        """Fetch rooms for a user/home pair and return normalized response payload."""
        resolved_home_id = self._resolve_home_id(user_id, preferred_home_id)
        rooms_data = []

        if self.multi_db and resolved_home_id:  # type: ignore
            try:
                rooms_data = self.multi_db.get_home_rooms(resolved_home_id, str(user_id))  # type: ignore
            except Exception as exc:
                if self.app:  # type: ignore
                    self.app.logger.error(f"Failed to load rooms for home {resolved_home_id}: {exc}")  # type: ignore
                rooms_data = []
        else:
            rooms_data = list(self.smart_home.rooms)  # type: ignore

        normalized = self._normalize_rooms_for_response(rooms_data, resolved_home_id)
        return normalized, resolved_home_id

    def _broadcast_rooms_update(self, user_id, preferred_home_id=None):
        """Emit socket updates with the latest room payload for the user/home context."""
        if not self.socketio:  # type: ignore
            return

        try:
            rooms_payload, resolved_home_id = self._get_rooms_payload(user_id, preferred_home_id)
            payload = {
                'status': 'success',
                'data': rooms_payload
            }
            if resolved_home_id:
                payload['meta'] = {'home_id': resolved_home_id}
            self.socketio.emit('update_rooms', payload)  # type: ignore
        except Exception as exc:
            if self.app:  # type: ignore
                self.app.logger.warning(f"Failed to broadcast room update: {exc}")  # type: ignore

    def get_current_home_temperature_controls(self, user_id):
        """Return normalized temperature control payload for the active home, sanitizing Decimal values."""
        base_controls = list(getattr(self.smart_home, 'temperature_controls', []))  # type: ignore
        if not user_id:
            return base_controls

        if not getattr(self, 'multi_db', None):  # type: ignore
            return base_controls

        try:
            resolved_home_id = self._resolve_home_id(user_id)
            if not resolved_home_id:
                return base_controls

            raw_controls = self.multi_db.get_temperature_controls(resolved_home_id, str(user_id))  # type: ignore
            normalized = []
            for control in raw_controls or []:
                settings = control.get('settings') or {}
                if isinstance(settings, str):
                    try:
                        settings = json.loads(settings)
                    except json.JSONDecodeError:
                        settings = {}

                temperature_value = control.get('temperature')
                if isinstance(temperature_value, Decimal):
                    temperature_value = float(temperature_value)
                elif isinstance(temperature_value, str):
                    try:
                        temperature_value = float(temperature_value)
                    except (TypeError, ValueError):
                        temperature_value = None

                min_temperature = control.get('min_temperature')
                if isinstance(min_temperature, Decimal):
                    min_temperature = float(min_temperature)
                elif isinstance(min_temperature, str):
                    try:
                        min_temperature = float(min_temperature)
                    except (TypeError, ValueError):
                        min_temperature = None

                max_temperature = control.get('max_temperature')
                if isinstance(max_temperature, Decimal):
                    max_temperature = float(max_temperature)
                elif isinstance(max_temperature, str):
                    try:
                        max_temperature = float(max_temperature)
                    except (TypeError, ValueError):
                        max_temperature = None

                target_temperature = settings.get('target_temperature', 21.0)
                if isinstance(target_temperature, Decimal):
                    target_temperature = float(target_temperature)
                elif isinstance(target_temperature, str):
                    try:
                        target_temperature = float(target_temperature)
                    except (TypeError, ValueError):
                        target_temperature = 21.0

                mode_value = settings.get('mode', 'auto') or 'auto'
                if isinstance(mode_value, Decimal):
                    mode_value = str(mode_value)
                elif not isinstance(mode_value, str):
                    mode_value = str(mode_value)

                room_id = control.get('room_id')
                room_name = control.get('room_name') or control.get('room')
                normalized.append({
                    'id': control.get('id'),
                    'name': control.get('name'),
                    'room': room_name,
                    'room_name': room_name,
                    'room_id': str(room_id) if room_id is not None else None,
                    'temperature': temperature_value,
                    'target_temperature': target_temperature,
                    'mode': mode_value,
                    'min_temperature': min_temperature,
                    'max_temperature': max_temperature,
                    'enabled': control.get('enabled', True),
                    'type': control.get('type', 'temperature_control')
                })
            return normalized
        except Exception as exc:
            print(f"[DEBUG] Error getting multi-home temperature controls: {exc}")
            return base_controls

    def _resolve_room_identifier(self, identifier, user_id, preferred_home_id=None):
        """Resolve room identifiers supplied as ID or name into a concrete room ID."""
        if identifier is None:
            return None

        if isinstance(identifier, dict):
            identifier = identifier.get('id') or identifier.get('room_id') or identifier.get('name')

        if identifier is None:
            return None

        if isinstance(identifier, str):
            normalized_identifier = identifier.strip()
            if normalized_identifier.lower() in {'', 'nieprzypisane', 'unassigned', 'none', 'null'}:
                # Treat common unassigned labels as no-room (NULL) and do not create any special room
                return None
            identifier = normalized_identifier

        if not self.multi_db:  # type: ignore
            return None

        resolved_home_id = self._resolve_home_id(user_id, preferred_home_id)
        if not resolved_home_id:
            return None

        # Try direct lookup by room ID (supports both UUID/string and integer identifiers)
        direct_lookup_candidates = [identifier]
        if isinstance(identifier, str) and identifier.isdigit():
            direct_lookup_candidates.append(int(identifier))

        for candidate in direct_lookup_candidates:
            try:
                room = self.multi_db.get_room(candidate, str(user_id))  # type: ignore
                if room:
                    return room['id']
            except Exception as exc:
                if self.app:  # type: ignore
                    self.app.logger.debug(f"Direct room lookup failed for '{candidate}': {exc}")  # type: ignore

        # Attempt to interpret as integer ID for legacy numeric identifiers
        try:
            return int(identifier)
        except (TypeError, ValueError):
            pass

        # Fallback to name-based lookup
        try:
            room = self.multi_db.get_room_by_name(resolved_home_id, str(user_id), str(identifier))  # type: ignore
            return room['id'] if room else None
        except Exception as exc:
            if self.app:  # type: ignore
                self.app.logger.debug(f"Failed to resolve room identifier '{identifier}': {exc}")  # type: ignore
            return None


class RoutesManager(MultiHomeHelpersMixin):
    def __init__(self, app, smart_home, auth_manager, mail_manager, async_mail_manager=None, cache=None, cached_data_access=None, management_logger=None, socketio=None, multi_db=None):
        self.app = app
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.mail_manager = mail_manager
        self.async_mail_manager = async_mail_manager or mail_manager  # Fallback to sync
        self.cache = cache
        self.multi_db = multi_db
        print(f"[DEBUG] RoutesManager init - cache: {cache}, cached_data_access: {cached_data_access}")
        # Use injected cached_data_access if provided, else fallback
        self.cached_data = cached_data_access or (CachedDataAccess(cache, smart_home) if cache else None)
        print(f"[DEBUG] RoutesManager init - self.cached_data: {type(self.cached_data)} {self.cached_data}")
        # Initialize management logger
        self.management_logger = management_logger or ManagementLogger()
        # Initialize socketio for real-time updates
        self.socketio = socketio
        
        # Initialize cache manager for optimized user data access
        from utils.cache_manager import CacheManager
        self.cache_manager = CacheManager(cache, smart_home) if cache else None
        
        self.register_routes()

    def get_current_user(self):
        """Get current logged in user from session"""
        user_id = session.get('user_id')
        if user_id:
            # For now, return a simple user dict - this should integrate with your user system
            return {'id': user_id}
        return None

    def get_current_home_rooms(self, user_id):
        """Get rooms from current selected home or fallback to main database"""
        if not user_id:
            return list(self.smart_home.rooms)

        try:
            rooms_payload, _ = self._get_rooms_payload(user_id)
            return [room['name'] for room in rooms_payload]
        except Exception as e:
            print(f"[DEBUG] Error getting multi-home rooms: {e}")
            return list(self.smart_home.rooms)

    def get_current_home_buttons(self, user_id):
        """Get buttons from current selected home or fallback to main database"""
        if not user_id:
            return list(getattr(self.smart_home, 'buttons', []))

        if not self.multi_db:
            return self.smart_home.buttons

        try:
            resolved_home_id = self._resolve_home_id(user_id)
            if not resolved_home_id:
                return self.smart_home.buttons

            raw_buttons = self.multi_db.get_buttons(resolved_home_id, str(user_id))
            normalized = []
            for button in raw_buttons or []:
                room_id = button.get('room_id')
                room_name = button.get('room_name') or button.get('room')
                normalized.append({
                    'id': button.get('id'),
                    'name': button.get('name'),
                    'room': room_name,
                    'room_name': room_name,
                    'room_id': str(room_id) if room_id is not None else None,
                    'state': button.get('state'),
                    'type': button.get('type', 'button'),
                    'enabled': button.get('enabled', True),
                    'display_order': button.get('display_order')
                })
            return normalized
        except Exception as e:
            print(f"[DEBUG] Error getting multi-home buttons: {e}")
            return self.smart_home.buttons

    def _resolve_home_id(self, user_id, preferred_home_id=None):
        """Resolve current home for the given user."""
        if not self.multi_db or not user_id:
            return None

        user_id_str = str(user_id)
        home_id = preferred_home_id or session.get('current_home_id')

        if not home_id:
            try:
                home_id = self.multi_db.get_user_current_home(user_id_str)
            except Exception as exc:
                if self.app:
                    self.app.logger.error(f"Failed to resolve home for user {user_id_str}: {exc}")
                home_id = None

        return str(home_id) if home_id else None

    def _normalize_rooms_for_response(self, rooms, default_home_id=None):
        """Normalize various room payload formats to a consistent API response."""
        normalized = []
        if not rooms:
            return normalized

        for index, room in enumerate(rooms):
            if isinstance(room, dict):
                room_id = room.get('id') or room.get('room_id')
                name = room.get('name') or room.get('room') or room.get('title')
                description = room.get('description')
                display_order = room.get('display_order', index)
                home_id = room.get('home_id', default_home_id)
            else:
                room_id = room
                name = room
                description = None
                display_order = index
                home_id = default_home_id

            if not name:
                continue

            normalized.append({
                'id': str(room_id) if room_id is not None else str(name),
                'name': str(name),
                'description': description,
                'display_order': int(display_order) if display_order is not None else index,
                'home_id': str(home_id) if home_id else None
            })

        # Ensure stable ordering by display_order then name
        normalized.sort(key=lambda r: (r.get('display_order', 0), r.get('name', '').lower()))
        return normalized

    def _get_rooms_payload(self, user_id, preferred_home_id=None):
        """Fetch rooms for a user/home pair and return normalized response payload."""
        resolved_home_id = self._resolve_home_id(user_id, preferred_home_id)
        rooms_data = []

        if self.multi_db and resolved_home_id:
            try:
                rooms_data = self.multi_db.get_home_rooms(resolved_home_id, str(user_id))
            except Exception as exc:
                if self.app:
                    self.app.logger.error(f"Failed to load rooms for home {resolved_home_id}: {exc}")
                rooms_data = []
        else:
            rooms_data = list(self.smart_home.rooms)

        normalized = self._normalize_rooms_for_response(rooms_data, resolved_home_id)
        return normalized, resolved_home_id

    def _broadcast_rooms_update(self, user_id, preferred_home_id=None):
        """Emit socket updates with the latest room payload for the user/home context."""
        if not self.socketio:
            return

        try:
            rooms_payload, resolved_home_id = self._get_rooms_payload(user_id, preferred_home_id)
            payload = {
                'status': 'success',
                'data': rooms_payload
            }
            if resolved_home_id:
                payload['meta'] = {'home_id': resolved_home_id}
            self.socketio.emit('update_rooms', payload)
        except Exception as exc:
            if self.app:
                self.app.logger.warning(f"Failed to broadcast room update: {exc}")

    def _resolve_room_identifier(self, identifier, user_id, preferred_home_id=None):
        """Resolve room identifiers supplied as ID or name into a concrete room ID."""
        if identifier is None:
            return None

        if isinstance(identifier, dict):
            identifier = identifier.get('id') or identifier.get('room_id') or identifier.get('name')

        if identifier is None:
            return None

        # Attempt to interpret as integer ID first
        try:
            return int(identifier)
        except (TypeError, ValueError):
            pass

        if not self.multi_db:
            return None

        resolved_home_id = self._resolve_home_id(user_id, preferred_home_id)
        if not resolved_home_id:
            return None

        try:
            room = self.multi_db.get_room_by_name(resolved_home_id, str(user_id), str(identifier))
            return room['id'] if room else None
        except Exception as exc:
            if self.app:
                self.app.logger.debug(f"Failed to resolve room identifier '{identifier}': {exc}")
            return None

    def get_current_home_automations(self, user_id, home_id=None):
        """Fetch automations for the resolved home context."""
        if not self.multi_db or not user_id:
            return list(self.smart_home.automations), None

        resolved_home_id = self._resolve_home_id(user_id, home_id)
        if not resolved_home_id:
            return [], None

        try:
            automations = self.multi_db.get_home_automations(resolved_home_id, str(user_id))
            return automations, resolved_home_id
        except PermissionError:
            raise
        except Exception as exc:
            if self.app:
                self.app.logger.error(f"Failed to load automations for home {resolved_home_id}: {exc}")
            return [], resolved_home_id

    def _emit_automation_update(self, home_id, automations):
        """Emit automation updates with home identifier."""
        payload = {
            'home_id': str(home_id) if home_id else None,
            'automations': automations
        }
        self.emit_update('update_automations', payload)

    def get_current_home_lights(self, user_id):
        """Get lights from current selected home or fallback to main database"""
        if not self.multi_db or not user_id:
            # Fallback to main database
            return self.smart_home.lights if hasattr(self.smart_home, 'lights') else []
        
        try:
            # Get current home ID from session or database
            current_home_id = session.get('current_home_id')
            if not current_home_id:
                current_home_id = self.multi_db.get_user_current_home(user_id)
            
            if current_home_id:
                # Get lights from multi-home system
                lights_data = self.multi_db.get_lights(current_home_id, user_id)
                # Convert to old format for compatibility
                lights = []
                for light in lights_data:
                    settings = light.get('settings', {}) or {}
                    lights.append({
                        'id': light['id'],
                        'name': light['name'],
                        'room': light['room_name'],
                        'state': light['state'],
                        'brightness': settings.get('brightness', 100),
                        'color': settings.get('color', '#FFFFFF'),
                        'type': light['type']
                    })
                return lights
            else:
                # No current home set, fallback to main database
                return self.smart_home.lights if hasattr(self.smart_home, 'lights') else []
                
        except Exception as e:
            print(f"[DEBUG] Error getting multi-home lights: {e}")
            # Fallback to main database
            return self.smart_home.lights if hasattr(self.smart_home, 'lights') else []

    def get_cached_user_data(self, user_id, session_id=None):
        """
        Helper method to get cached user data efficiently
        
        Args:
            user_id: User ID from session
            session_id: Session ID for session-level caching
            
        Returns:
            User data dictionary or None
        """
        if not user_id:
            return None
            
        if self.cache_manager:
            # Use optimized session-level caching
            return self.cache_manager.get_session_user_data(user_id, session_id)
        else:
            # Fallback to direct database call
            return self.smart_home.get_user_data(user_id) if self.smart_home else None

    def emit_update(self, event_name, data):
        """Safely emit socketio updates only if socketio is available"""
        if self.socketio:
            self.socketio.emit(event_name, data)

    def register_routes(self):
        print("[DEBUG] register_routes called - registering Flask routes!")

        @self.app.context_processor
        def inject_asset_version():
            """Provide a global asset version for cache-busting static files."""
            version = os.environ.get('ASSET_VERSION') or os.environ.get('IMAGE_TAG') or 'dev'
            return {'asset_version': version}

        @self.app.route('/')
        def home():
            print(f"[DEBUG] Session on /: {dict(session)}")
            if 'username' not in session:
                print("[DEBUG] Brak username w sesji, redirect na login")
                return redirect(url_for('login'))
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            print(f"[DEBUG] user_id in session: {session.get('user_id')}, user_data: {user_data}")
            
            # Get rooms from current home or fallback to main database
            user_id = session.get('user_id')
            rooms = self.get_current_home_rooms(user_id)
            print(f"[DEBUG] Pre-loading {len(rooms)} rooms for home page (current home)")
            
            # Get current home info with statistics for the header
            current_home = None
            if self.multi_db and user_id:
                try:
                    current_home_id = session.get('current_home_id') or self.multi_db.get_user_current_home(user_id)
                    if current_home_id:
                        current_home = self.multi_db.get_home_details(current_home_id, user_id)
                        if current_home:
                            # Add statistics
                            home_rooms = self.multi_db.get_home_rooms(current_home_id, user_id)
                            home_devices = self.multi_db.get_home_devices(current_home_id, user_id)
                            current_home['room_count'] = len(home_rooms)
                            current_home['device_count'] = len(home_devices)
                            print(f"[DEBUG] Current home stats: {current_home['name']} - {current_home['room_count']} rooms, {current_home['device_count']} devices")
                except Exception as e:
                    print(f"[DEBUG] Error getting current home info: {e}")
            
            return render_template('index.html', user_data=user_data, rooms=rooms, current_home=current_home)

        @self.app.route('/temp')
        @self.auth_manager.login_required
        def temp():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('temp_lights.html', user_data=user_data)

        @self.app.route('/temperature')
        @self.auth_manager.login_required
        def temperature():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('temperature.html', user_data=user_data)

        @self.app.route('/security')
        @self.auth_manager.login_required
        def security():
            try:
                user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
                current_security_state = self.smart_home.security_state
                home_id = None

                user_id = session.get('user_id')
                if self.multi_db and user_id:
                    try:
                        home_id = session.get('current_home_id') or self.multi_db.get_user_current_home(user_id)
                        if home_id:
                            current_security_state = self.multi_db.get_security_state(str(home_id), str(user_id))
                    except PermissionError:
                        self.app.logger.warning("User lacks access to current home when fetching security state")
                    except Exception as err:
                        self.app.logger.error(f"Failed to fetch security state for home {home_id}: {err}")

                return render_template('security.html', user_data=user_data, security_state=current_security_state)
            except Exception as e:
                self.app.logger.error(f"Error in security route: {e}")
                return f"Internal Server Error: {str(e)}", 500

        @self.app.route('/settings', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def settings():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('settings.html', user_data=user_data)

        @self.app.route('/suprise')
        @self.auth_manager.login_required
        def suprise():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('suprise.html', user_data=user_data)

        @self.app.route('/suprise_dog')
        @self.auth_manager.login_required
        def suprise_dog():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('suprise_Dog.html', user_data=user_data)

        @self.app.route('/automations')
        @self.auth_manager.login_required
        def automations():
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            return render_template('automations.html', user_data=user_data)

        # API endpoints for mobile app
        @self.app.route('/api/ping', methods=['GET'])
        def api_ping():
            """Simple ping endpoint to test connectivity"""
            return jsonify({
                'status': 'success',
                'message': 'SmartHome server is running',
                'timestamp': int(time.time()),
                'version': '1.0'
            })
        
        # Cache monitoring endpoint
        @self.app.route('/api/cache/stats', methods=['GET'])
        @self.auth_manager.login_required
        def cache_stats():
            """Get cache performance statistics"""
            from utils.cache_manager import cache_stats, get_cache_hit_rate
            cache_type = 'Disabled'
            cache_default_timeout = 'Unknown'
            cache_obj = getattr(self, 'cache', None)
            if cache_obj and hasattr(cache_obj, 'config'):
                cache_type = cache_obj.config.get('CACHE_TYPE', 'Unknown')
                cache_default_timeout = cache_obj.config.get('CACHE_DEFAULT_TIMEOUT', 'Unknown')
            return jsonify({
                'status': 'success',
                'cache_stats': {
                    'hits': cache_stats['hits'],
                    'misses': cache_stats['misses'],
                    'total_requests': cache_stats['total_requests'],
                    'hit_rate_percentage': round(get_cache_hit_rate(), 2)
                },
                'cache_config': {
                    'type': cache_type,
                    'default_timeout': cache_default_timeout
                }
            })
        
        # Database monitoring endpoint
        @self.app.route('/api/database/stats', methods=['GET'])
        @self.auth_manager.login_required
        def database_stats():
            """Get database performance statistics"""
            try:
                stats = {
                    'status': 'success',
                    'database_mode': hasattr(self.smart_home, 'db'),
                    'connection_pool': {'enabled': False}
                }
                
                # Get database statistics if available
                if hasattr(self.smart_home, 'db') and self.smart_home.db:
                    try:
                        pool_status = self.smart_home.db.get_pool_status()
                        stats['connection_pool'] = pool_status
                        
                        # Get database stats if method exists
                        if hasattr(self.smart_home, 'get_database_stats'):
                            db_stats = self.smart_home.get_database_stats()
                            stats['database_stats'] = db_stats
                    except Exception as e:
                        stats['database_error'] = str(e)
                
                return jsonify(stats)
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                })

        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            """Server status endpoint"""
            try:
                from app_db import DATABASE_MODE
            except ImportError:
                DATABASE_MODE = False
            return jsonify({
                'status': 'success',
                'server_status': 'running',
                'database_mode': DATABASE_MODE,
                'timestamp': int(time.time())
            })

        @self.app.route('/api/config', methods=['GET'])
        def api_config():
            """Configuration info endpoint"""
            return jsonify({
                'server_ip': request.host.split(':')[0],
                'server_port': request.environ.get('SERVER_PORT', '5000'),
                'cors_enabled': True,
                'auth_required': True,
                'timestamp': int(time.time())
            })

        @self.app.route('/edit')
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def edit():
            # Get user data for profile picture and menu
            user_data = self.get_cached_user_data(session.get('user_id'), session.get('user_id'))
            
            # Use cached data for performance
            print(f"[DEBUG] /edit route - Getting data for template")
            print(f"[DEBUG] cached_data object: {type(self.cached_data)}")
            user_id = session.get('user_id')
            resolved_home_id = None
            rooms = []
            buttons = []
            temperature_controls = []

            if self.multi_db and user_id:
                try:
                    resolved_home_id = self._resolve_home_id(user_id)
                    if resolved_home_id:
                        rooms = self.multi_db.get_home_rooms(resolved_home_id, str(user_id))
                        buttons = self.multi_db.get_buttons(resolved_home_id, str(user_id))
                        temperature_controls = self.multi_db.get_temperature_controls(resolved_home_id, str(user_id))
                        print(f"[DEBUG] /edit route - Loaded {len(rooms)} rooms from multi-home DB (home_id={resolved_home_id})")
                except PermissionError as perm_err:
                    if self.app:
                        self.app.logger.warning(f"User {user_id} lacks permissions for home {resolved_home_id}: {perm_err}")
                except Exception as exc:
                    if self.app:
                        self.app.logger.error(f"Failed to load multi-home data for user {user_id}: {exc}")

            if not rooms:
                legacy_rooms = self.get_current_home_rooms(user_id)
                rooms = [{
                    'id': str(idx),
                    'name': name,
                    'home_id': resolved_home_id,
                    'description': None,
                    'display_order': idx
                } for idx, name in enumerate(legacy_rooms or [])]

            if not buttons:
                buttons = self.cached_data.get_buttons() if self.cached_data else getattr(self.smart_home, 'buttons', [])

            if not temperature_controls:
                temperature_controls = self.cached_data.get_temperature_controls() if self.cached_data else getattr(self.smart_home, 'temperature_controls', [])

            print(f"[DEBUG] /edit route - Buttons data for template: {buttons}")

            def _normalize_devices(devices, fallback_type):
                normalized = []
                for device in devices or []:
                    if isinstance(device, dict):
                        normalized.append({
                            'id': device.get('id'),
                            'name': device.get('name'),
                            'room': device.get('room_name') or device.get('room'),
                            'room_id': device.get('room_id'),
                            'type': 'light' if fallback_type == 'light' else ('thermostat' if fallback_type == 'thermostat' else device.get('type', fallback_type)),
                            'state': device.get('state'),
                            'enabled': device.get('enabled', True)
                        })
                    else:
                        # Legacy object with attributes
                        normalized.append({
                            'id': getattr(device, 'id', None),
                            'name': getattr(device, 'name', None),
                            'room': getattr(device, 'room', None),
                            'room_id': getattr(device, 'room_id', None),
                            'type': fallback_type,
                            'state': getattr(device, 'state', None),
                            'enabled': getattr(device, 'enabled', True)
                        })
                return normalized

            buttons = _normalize_devices(buttons, 'light')
            temperature_controls = _normalize_devices(temperature_controls, 'thermostat')

            return render_template(
                'edit.html',
                user_data=user_data,
                rooms=rooms,
                buttons=buttons,
                temperature_controls=temperature_controls
            )

        @self.app.route('/admin_dashboard', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def admin_dashboard():
            if request.method == 'POST':
                # Handle admin user creation
                username = request.form.get('username', '').strip()
                email = request.form.get('email', '').strip()
                password = request.form.get('password', '')
                role = request.form.get('role', 'user')
                
                # Basic validation
                if not username or len(username) < 3:
                    flash('Nazwa użytkownika musi mieć co najmniej 3 znaki.', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                if not email or '@' not in email:
                    flash('Podaj poprawny adres email.', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                if not password or len(password) < 6:
                    flash('Hasło musi mieć co najmniej 6 znaków.', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                if role not in ['user', 'admin']:
                    flash('Nieprawidłowa rola użytkownika.', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                # Check if user already exists
                for user in self.smart_home.users.values():
                    if user.get('name') == username:
                        flash('Użytkownik już istnieje.', 'error')
                        return redirect(url_for('admin_dashboard'))
                    if user.get('email') == email:
                        flash('Adres email jest już używany.', 'error')
                        return redirect(url_for('admin_dashboard'))
                
                # Dodawanie użytkownika - obsługa trybu DB i plikowego
                try:
                    if hasattr(self.smart_home, 'add_user'):
                        self.smart_home.add_user(username, password, role, email)
                    else:
                        import uuid
                        from werkzeug.security import generate_password_hash
                        user_id = str(uuid.uuid4())
                        self.smart_home.users[user_id] = {
                            'name': username,
                            'password': generate_password_hash(password),
                            'role': role,
                            'email': email,
                            'profile_picture': ''
                        }
                        self.smart_home.save_config()
                    flash(f'Użytkownik {username} został dodany pomyślnie!', 'success')
                except Exception as e:
                    flash(f'Błąd podczas dodawania użytkownika: {e}', 'error')
                return redirect(url_for('admin_dashboard'))
            
            # Przygotowanie statystyk dla dashboardu
            stats = self._generate_dashboard_stats()
            device_states = self._get_device_states()
            management_logs = self._get_management_logs()
            
            # Pre-load users data for immediate rendering
            users_list = [
                {
                    'user_id': user_id,
                    'username': data['name'],
                    'email': data.get('email', ''),
                    'role': data['role'],
                    'password': '••••••••'  # Always show dots for password
                }
                for user_id, data in self.smart_home.users.items()
            ]
            
            # Pobierz dane użytkownika dla wyświetlenia zdjęcia profilowego
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            
            return render_template('admin_dashboard.html', 
                                 stats=stats, 
                                 device_states=device_states,
                                 management_logs=management_logs,
                                 user_data=user_data,
                                 preloaded_users=users_list)

        @self.app.route('/api/admin/device-states')
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_device_states():
            device_states = self._get_device_states()
            return jsonify(device_states)

        @self.app.route('/api/admin/logs')
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_logs():
            logs = self._get_management_logs()
            return jsonify(logs)

        # Notification settings (recipients) API
        @self.app.route('/api/notifications/settings', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_notification_settings():
            """Get or set notification recipients for the home.
            Frontend expects:
              GET -> { recipients: [{ email, user, enabled }] }
              POST body -> { recipients: [{ email, user, enabled }] }
            where 'user' is the username (not id). DB stores user_id.
            """
            from utils.db_manager import (
                get_notification_recipients,
                set_notification_recipients,
            )
            import os, json
            from pathlib import Path

            # Map users: id <-> name
            users_by_id = {}
            users_by_name = {}
            try:
                for uid, data in self.smart_home.users.items():
                    name = data.get('name')
                    if name:
                        users_by_id[str(uid)] = name
                        users_by_name[name] = str(uid)
            except Exception:
                pass

            # Choose a home id for persistence (single-home setup default = 1)
            home_id_env = os.getenv('HOME_ID')
            try:
                home_id = int(home_id_env) if home_id_env else 1
            except ValueError:
                home_id = 1

            def _fallback_file_path():
                base = Path(os.path.dirname(os.path.abspath(__file__))).parent
                return base / 'backups' / 'notification_recipients.json'

            if request.method == 'GET':
                try:
                    recipients_db = get_notification_recipients(home_id)
                    # Convert to frontend shape: use username
                    recipients = []
                    for r in recipients_db:
                        uid = r.get('user_id')
                        recipients.append({
                            'email': r.get('email', ''),
                            'user': users_by_id.get(str(uid), ''),
                            'enabled': bool(r.get('enabled', True))
                        })
                    return jsonify({ 'recipients': recipients })
                except Exception:
                    # Fallback to JSON file store
                    try:
                        fp = _fallback_file_path()
                        if fp.exists():
                            data = json.loads(fp.read_text(encoding='utf-8'))
                            if isinstance(data, dict) and 'recipients' in data:
                                return jsonify({ 'recipients': data['recipients'] })
                    except Exception:
                        pass
                    return jsonify({ 'recipients': [] }), 200

            # POST
            try:
                data = request.get_json(silent=True) or {}
                recipients = data.get('recipients', [])
                # Validate and map to DB shape (email, user_id, enabled)
                recipients_db = []
                for r in recipients:
                    username = (r.get('user') or '').strip()
                    email = (r.get('email') or '').strip()
                    enabled = bool(r.get('enabled', True))
                    uid_str = users_by_name.get(username)
                    uid_val = None
                    if uid_str is not None:
                        # Coerce to int when possible
                        try:
                            uid_val = int(uid_str)
                        except (TypeError, ValueError):
                            # keep None if not numeric
                            uid_val = None
                    recipients_db.append({
                        'email': email,
                        'user_id': uid_val,
                        'enabled': enabled,
                    })
                # Try DB first
                try:
                    set_notification_recipients(recipients_db, home_id)
                    return jsonify({ 'status': 'success' })
                except Exception as db_err:
                    # Fallback to JSON file store to avoid 500s
                    try:
                        fp = _fallback_file_path()
                        fp.parent.mkdir(parents=True, exist_ok=True)
                        payload = { 'recipients': recipients }
                        fp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
                        return jsonify({ 'status': 'success', 'warning': 'DB unavailable, saved to file store' })
                    except Exception as file_err:
                        return jsonify({ 'status': 'error', 'message': f'{db_err}; fallback failed: {file_err}' }), 500
            except Exception as e:
                return jsonify({ 'status': 'error', 'message': str(e) }), 500

        @self.app.route('/api/admin/logs/clear', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_clear_logs():
            """Clear all logs"""
            try:
                self.management_logger.clear_logs()
                
                # Log the clearing action
                self.management_logger.log_event(
                    'info',
                    f'Administrator {session.get("username", "unknown")} wyczyścił wszystkie logi',
                    'admin_action',
                    session.get('username', 'unknown'),
                    request.remote_addr
                )
                
                return jsonify({'status': 'success', 'message': 'Wszystkie logi zostały usunięte'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Błąd przy usuwaniu logów: {str(e)}'}), 500

        @self.app.route('/api/admin/logs/delete', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_delete_logs():
            """Delete logs by date range or number of days"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych w żądaniu'}), 400
                
                deleted_count = 0
                
                if 'days' in data:
                    # Delete logs older than specified days
                    days = int(data['days'])
                    if days < 0:
                        return jsonify({'status': 'error', 'message': 'Liczba dni musi być dodatnia'}), 400
                    
                    deleted_count = self.management_logger.delete_logs_older_than(days)
                    action_msg = f'Usunięto {deleted_count} logów starszych niż {days} dni'
                    
                elif 'start_date' in data or 'end_date' in data:
                    # Delete logs by date range
                    start_date = data.get('start_date')
                    end_date = data.get('end_date')
                    
                    deleted_count = self.management_logger.delete_logs_by_date_range(start_date, end_date)
                    
                    if start_date and end_date:
                        action_msg = f'Usunięto {deleted_count} logów z okresu {start_date} - {end_date}'
                    elif start_date:
                        action_msg = f'Usunięto {deleted_count} logów od {start_date}'
                    elif end_date:
                        action_msg = f'Usunięto {deleted_count} logów do {end_date}'
                    else:
                        action_msg = f'Usunięto {deleted_count} logów'
                else:
                    return jsonify({'status': 'error', 'message': 'Brak parametrów usuwania (days, start_date lub end_date)'}), 400
                
                # Log the deletion action
                self.management_logger.log_event(
                    'info',
                    f'Administrator {session.get("username", "unknown")}: {action_msg}',
                    'admin_action',
                    session.get('username', 'unknown'),
                    request.remote_addr,
                    {'deleted_count': deleted_count, 'action': 'delete_logs'}
                )
                
                return jsonify({
                    'status': 'success', 
                    'message': action_msg,
                    'deleted_count': deleted_count
                })
                
            except ValueError as e:
                return jsonify({'status': 'error', 'message': f'Błąd formatu daty: {str(e)}'}), 400
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Błąd przy usuwaniu logów: {str(e)}'}), 500

        @self.app.route('/lights')
        @self.auth_manager.login_required
        def lights():
            user_data = self.smart_home.get_user_data(session.get('user_id')) if session.get('user_id') else None
            return render_template('lights.html', user_data=user_data)

        @self.app.route('/error')
        def error():
            return render_template('error.html')

        @self.app.route('/test-email')
        def test_email():
            # Use async mail manager for non-critical test emails
            result = self.async_mail_manager.send_security_alert_async('failed_login', {
                'username': 'testuser',
                'ip_address': '127.0.0.1',
                'attempt_count': 3
            })
            return jsonify({"status": "success" if result else "error"})

        @self.app.route('/user')
        @self.auth_manager.login_required
        def user_profile():
            user_id = session.get('user_id')
            if not user_id:
                flash('Błąd autoryzacji', 'error')
                return redirect(url_for('login'))
                
            # Use multihouse system if available
            if self.multi_db:
                user_data = self.multi_db.get_user_by_id(user_id)
                # Convert for template compatibility
                if user_data:
                    user_data.update({
                        'user_id': user_data.get('id'),
                        'username': user_data.get('name')
                    })
            else:
                # Fallback to old system
                user_id, user = self.smart_home.get_user_by_login(session['username'])
                user_data = self.smart_home.get_user_data(user_id) if user else None
                
            return render_template('user.html', user_data=user_data)

        @self.app.route('/api/user/profile', methods=['GET', 'PUT'])
        @self.auth_manager.login_required
        def manage_profile():
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 400
                
            # Get user data from multihouse system if available
            if self.multi_db:
                user_data = self.multi_db.get_user_by_id(user_id)
                if not user_data:
                    return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 400
            else:
                # Fallback to old system
                user_id, user = self.smart_home.get_user_by_login(session['username'])
                if not user:
                    return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 400
                user_data = self.smart_home.get_user_data(user_id)
                
            if request.method == 'GET':
                return jsonify(user_data)
            elif request.method == 'PUT':
                data = request.get_json()
                if not data:
                    return jsonify({"status": "error", "message": "Brak danych"}), 400

                # Use multihouse system if available
                if self.multi_db:
                    updates = {}
                    if 'username' in data and data['username'] != user_data['name']:
                        updates['name'] = data['username']
                    if 'name' in data:
                        updates['name'] = data['name']  
                    if 'email' in data:
                        updates['email'] = data['email']
                    
                    # Handle password change separately
                    if data.get('current_password') and data.get('new_password'):
                        if not self.multi_db.verify_user_password(user_id, data['current_password']):
                            return jsonify({"status": "error", "message": "Nieprawidłowe aktualne hasło"}), 400
                        
                        from werkzeug.security import generate_password_hash
                        password_hash = generate_password_hash(data['new_password'])
                        if not self.multi_db.update_user_password(user_id, password_hash):
                            return jsonify({"status": "error", "message": "Błąd podczas zmiany hasła"}), 500
                    
                    # Update other fields
                    if updates:
                        if not self.multi_db.update_user(user_id, updates):
                            return jsonify({"status": "error", "message": "Błąd podczas aktualizacji profilu"}), 500
                else:
                    # Fallback to old system
                    updates = {}
                    if 'username' in data and data['username'] != user['name']:
                        updates['name'] = data['username']
                    if 'name' in data:
                        updates['name'] = data['name']
                    if 'email' in data:
                        updates['email'] = data['email']
                    if data.get('current_password') and data.get('new_password'):
                        if not self.smart_home.verify_password(user_id, data['current_password']):
                            return jsonify({"status": "error", "message": "Nieprawidłowe aktualne hasło"}), 400
                        updates['password'] = data['new_password']
                success, message = self.smart_home.update_user_profile(user_id, updates)
                if success:
                    # Log user profile change
                    action = 'password_change' if 'password' in updates else 'edit'
                    self.management_logger.log_user_change(
                        username=user['name'],
                        action=action,
                        target_user=user['name'],
                        ip_address=request.remote_addr or "",
                        details={'fields_updated': list(updates.keys())}
                    )
                    
                    if any(k in updates for k in ['name', 'email', 'password']):
                        return jsonify({"status": "success", "logout": True, "message": "pomyślnie zmieniono dane"})
                    return jsonify({"status": "success", "message": message})
                return jsonify({"status": "error", "message": message}), 400

        @self.app.route('/api/user/profile-picture', methods=['POST'])
        @self.auth_manager.login_required
        def update_profile_picture():
            if 'profile_picture' not in request.files:
                return jsonify({"status": "error", "message": "Brak pliku"}), 400

            file = request.files['profile_picture']
            if file.filename == '':
                return jsonify({"status": "error", "message": "Nie wybrano pliku"}), 400

            if not file or not allowed_file(file.filename):
                return jsonify({"status": "error", "message": "Niedozwolony typ pliku"}), 400

            try:
                user_id, user = self.smart_home.get_user_by_login(session['username'])
                if not user:
                    return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 400
                filename = secure_filename(f"{user_id}_{int(time.time())}{os.path.splitext(file.filename or '')[1]}")
                profile_pictures_dir = os.path.join(self.app.static_folder, 'profile_pictures')
                if not os.path.exists(profile_pictures_dir):
                    os.makedirs(profile_pictures_dir)

                file_path = os.path.join(profile_pictures_dir, filename)
                file.save(file_path)

                profile_picture_url = url_for('static', filename=f'profile_pictures/{filename}')
                success, message = self.smart_home.update_user_profile(user_id, {'profile_picture': profile_picture_url})

                if success:
                    return jsonify({
                        "status": "success",
                        "message": "Zdjęcie profilowe zostało zaktualizowane",
                        "profile_picture_url": profile_picture_url
                    })
                return jsonify({"status": "error", "message": message}), 500

            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login route for user authentication"""
            if request.method == 'POST':
                try:
                    # Handle both form data (web) and JSON (mobile API)
                    if request.is_json:
                        # Mobile API request (JSON)
                        data = request.get_json()
                        login_name = data.get('username')
                        password = data.get('password')
                        remember_me = False
                    else:
                        # Web form request
                        login_name = request.form.get('username')
                        password = request.form.get('password')
                        remember_me = request.form.get('remember_me') == 'on'
                    
                    ip_address = request.remote_addr
                    
                    print(f"[DEBUG] Login attempt: username='{login_name}', password_length={len(password) if password else 0}")
                    
                    # Get user by name/email using multihouse system
                    user_id = None
                    user = None
                    password_verified = False
                    
                    if self.multi_db:
                        # Use new multihouse system
                        user = self.multi_db.find_user_by_email_or_username(login_name)
                        if user:
                            user_id = user['id']
                            print(f"[DEBUG] Multihouse mode: found user {user_id} for '{login_name}'")
                            
                            # Verify password using werkzeug
                            from werkzeug.security import check_password_hash
                            stored_password_hash = user.get('password_hash', '')
                            if stored_password_hash and isinstance(stored_password_hash, str) and password:
                                password_verified = check_password_hash(stored_password_hash, password)
                            else:
                                password_verified = False
                            print(f"[DEBUG] Password verification result: {password_verified}")
                        else:
                            print(f"[DEBUG] No user found in multihouse system for login_name: '{login_name}'")
                    
                    # Fallback to old system if multi_db not available
                    elif hasattr(self.smart_home, 'get_user_by_login'):
                        user_id, user = self.smart_home.get_user_by_login(login_name)
                        print(f"[DEBUG] DB mode: get_user_by_login('{login_name}') -> {user_id}")
                        if user:
                            password_verified = self.smart_home.verify_password(user_id, password)
                            print(f"[DEBUG] Password verification result: {password_verified}")
                    else:
                        users = self.smart_home.users
                        print(f"[DEBUG] Got users: {list(users.keys())}")
                        for uid, user_data in users.items():
                            print(f"[DEBUG] Checking user {uid}: name='{user_data.get('name')}', email='{user_data.get('email')}'")
                            if user_data.get('name') == login_name or user_data.get('email') == login_name:
                                user = user_data
                                user_id = uid
                                print(f"[DEBUG] Found matching user: {uid}")
                                password_verified = self.smart_home.verify_password(user_id, password)
                                break
                    
                    # Check authentication result
                    if user and password_verified:
                        session['user_id'] = user_id
                        session['username'] = user['name']
                        session['role'] = user.get('role', 'user')
                        session.permanent = True
                        
                        # For multihouse system, set current home and load user homes
                        if self.multi_db:
                            # Get user's default home or first available home
                            user_homes = self.multi_db.get_user_homes(user_id)
                            if user_homes:
                                # Use default home if set, otherwise first home
                                default_home = user.get('default_home_id')
                                current_home = None
                                
                                if default_home:
                                    # Find the default home in user's homes
                                    for home in user_homes:
                                        if home['id'] == default_home:
                                            current_home = home
                                            break
                                
                                # If no default home found, use first home
                                if not current_home and user_homes:
                                    current_home = user_homes[0]
                                
                                if current_home:
                                    session['current_home_id'] = current_home['id']
                                    session['current_home_name'] = current_home['name']
                                    session['home_role'] = current_home['role']
                                    
                                    # Set user's current home in database
                                    self.multi_db.set_user_current_home(user_id, current_home['id'])
                                    
                                    print(f"[DEBUG] Set current home: {current_home['name']} (ID: {current_home['id']}) with role: {current_home['role']}")
                                else:
                                    print(f"[DEBUG] User {user['name']} has no homes")
                            else:
                                print(f"[DEBUG] User {user['name']} has no homes in multihouse system")
                        
                        print(f"[DEBUG] Login successful for user: {user['name']}")
                        
                        # Log successful login
                        if self.management_logger:
                            self.management_logger.log_login(user['name'], ip_address or 'unknown', success=True)
                        
                        # Return appropriate response based on request type
                        if request.is_json:
                            # Prepare response data
                            response_data = {
                                "status": "success",
                                "message": "Login successful",
                                "data": {
                                    "status": "success",
                                    "message": "Login successful", 
                                    "user": {
                                        "id": user_id,
                                        "name": user['name'],
                                        "email": user.get('email', ''),
                                        "role": user.get('role', 'user')
                                    },
                                    "session_id": None  # Flask sessions don't use explicit session IDs
                                }
                            }
                            
                            # Add home information for multihouse system
                            if self.multi_db:
                                user_homes = self.multi_db.get_user_homes(user_id)
                                current_home_id = session.get('current_home_id')
                                current_home = None
                                
                                # Find current home details
                                for home in user_homes:
                                    if home['id'] == current_home_id:
                                        current_home = home
                                        break
                                
                                response_data["data"]["homes"] = user_homes
                                response_data["data"]["current_home"] = current_home
                                response_data["data"]["multihouse_enabled"] = True
                            else:
                                response_data["data"]["multihouse_enabled"] = False
                            
                            # JSON API response for mobile - format compatible with Android ApiResponse<LoginResponse>
                            return jsonify(response_data)
                        else:
                            # Web response
                            flash('Zalogowano pomyślnie!', 'success')
                            return redirect(url_for('home'))
                    else:
                        print(f"[DEBUG] Login failed - user exists: {user is not None}, has password: {user.get('password') is not None if user else False}")
                        
                        # Log failed login attempt
                        if self.management_logger:
                            self.management_logger.log_login(
                                login_name or 'unknown', ip_address or 'unknown', success=False
                            )
                        
                        # Return appropriate error response
                        if request.is_json:
                            # JSON API error response for mobile
                            return jsonify({
                                "status": "error",
                                "message": "Invalid username or password"
                            }), 401
                        else:
                            # Web error response
                            flash('Nieprawidłowa nazwa użytkownika lub hasło!', 'error')
                            return render_template('login.html')
                        
                except Exception as e:
                    print(f"[DEBUG] Exception during login: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Return appropriate error response
                    if request.is_json:
                        # JSON API error response for mobile
                        return jsonify({
                            "status": "error",
                            "message": "Login error occurred"
                        }), 500
                    else:
                        # Web error response
                        flash('Błąd podczas logowania!', 'error')
                        return render_template('login.html')
            
            return render_template('login.html')

        @self.app.route('/logout')
        def logout():
            """Logout route"""
            username = session.get('username', 'Unknown')
            session.clear()
            flash('Wylogowano pomyślnie!', 'info')
            return redirect(url_for('login'))

        @self.app.route('/api/switch_home', methods=['POST'])
        def switch_home():
            """Switch user's current home in multihouse system"""
            if not self.multi_db:
                return jsonify({'status': 'error', 'message': 'Multihouse system not available'}), 400
                
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'status': 'error', 'message': 'User not logged in'}), 401
            
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'No data provided'}), 400
                
            home_id = data.get('home_id')
            if not home_id:
                return jsonify({'status': 'error', 'message': 'home_id is required'}), 400
            
            try:
                # Verify user has access to this home
                if not self.multi_db.user_has_home_access(user_id, home_id):
                    return jsonify({'status': 'error', 'message': 'Access denied to this home'}), 403
                
                # Get home details
                home_details = self.multi_db.get_home_details(home_id, user_id)
                if not home_details:
                    return jsonify({'status': 'error', 'message': 'Home not found'}), 404
                
                # Update session
                session['current_home_id'] = home_id
                session['current_home_name'] = home_details['name']
                session['home_role'] = home_details['role']
                
                # Update database
                self.multi_db.set_user_current_home(user_id, home_id)
                
                return jsonify({
                    'status': 'success',
                    'message': f'Switched to home: {home_details["name"]}',
                    'current_home': {
                        'id': home_id,
                        'name': home_details['name'],
                        'role': home_details['role'],
                        'is_owner': home_details['is_owner']
                    }
                }), 200
                
            except Exception as e:
                logger.error(f"Error switching home for user {user_id}: {e}")
                return jsonify({'status': 'error', 'message': 'Failed to switch home'}), 500

        @self.app.route('/api/get_user_homes', methods=['GET'])
        def get_user_homes():
            """Get list of homes user has access to"""
            if not self.multi_db:
                return jsonify({'status': 'error', 'message': 'Multihouse system not available'}), 400
                
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'status': 'error', 'message': 'User not logged in'}), 401
            
            try:
                user_homes = self.multi_db.get_user_homes(user_id)
                current_home_id = session.get('current_home_id')
                
                return jsonify({
                    'status': 'success',
                    'homes': user_homes,
                    'current_home_id': current_home_id
                }), 200
                
            except Exception as e:
                logger.error(f"Error getting user homes for {user_id}: {e}")
                return jsonify({'status': 'error', 'message': 'Failed to get user homes'}), 500

        @self.app.route('/register', methods=['GET', 'POST'])
        def register():
            if request.method == 'POST':
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
                
                # Sprawdź czy to pierwszy krok (wysłanie kodu) czy drugi (weryfikacja)
                if 'verification_code' in data:
                    # Drugi krok - weryfikacja kodu
                    return self._verify_and_register(data)
                else:
                    # Pierwszy krok - wysłanie kodu weryfikacyjnego
                    return self._send_verification_code(data)
            
            return render_template('register.html')

        @self.app.route('/forgot_password', methods=['GET', 'POST'])
        def forgot_password():
            if request.method == 'POST':
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
                
                email_or_username = data.get('email_or_username', '').strip()
                if not email_or_username:
                    return jsonify({'status': 'error', 'message': 'Wprowadź email lub nazwę użytkownika'}), 400
                
                # Znajdź użytkownika po email lub nazwie użytkownika
                user_id, user, email = self._find_user_by_email_or_username(email_or_username)
                if not user:
                    # Ze względów bezpieczeństwa, nie ujawniamy czy użytkownik istnieje
                    return jsonify({
                        'status': 'verification_sent',
                        'message': 'Jeśli podany email/użytkownik istnieje, kod weryfikacyjny został wysłany.'
                    }), 200
                
                # Wygeneruj i wyślij kod resetowania hasła
                verification_code = self.mail_manager.generate_verification_code()
                self.mail_manager.store_password_reset_code(email, verification_code, user_id)
                
                # Send password reset email
                if self.mail_manager.send_password_reset_email(email, verification_code):
                    return jsonify({
                        'status': 'verification_sent',
                        'message': 'Kod resetowania hasła został wysłany na podany adres email.'
                    }), 200
                else:
                    return jsonify({'status': 'error', 'message': 'Błąd podczas wysyłania kodu resetowania hasła.'}), 500
            
            return render_template('forgot_password.html')

        @self.app.route('/reset_password', methods=['POST'])
        def reset_password():
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
            
            email_or_username = data.get('email_or_username', '').strip()
            verification_code = data.get('verification_code', '').strip()
            new_password = data.get('new_password', '')
            
            if not email_or_username or not verification_code or not new_password:
                return jsonify({'status': 'error', 'message': 'Wszystkie pola są wymagane'}), 400
            
            if len(new_password) < 6:
                return jsonify({'status': 'error', 'message': 'Hasło musi mieć co najmniej 6 znaków'}), 400
            
            # Znajdź użytkownika po email lub nazwie użytkownika
            user_id, user, email = self._find_user_by_email_or_username(email_or_username)
            if not user:
                return jsonify({'status': 'error', 'message': 'Nieprawidłowy użytkownik'}), 400
            
            # Weryfikuj kod resetowania hasła
            is_valid, message, verified_user_id = self.mail_manager.verify_password_reset_code(email, verification_code)
            if not is_valid:
                return jsonify({'status': 'error', 'message': message}), 400
            
            # Sprawdź czy user_id się zgadza (dodatkowe zabezpieczenie)
            if verified_user_id != user_id:
                return jsonify({'status': 'error', 'message': 'Błąd weryfikacji użytkownika'}), 400
            
            # Zmień hasło w multihouse systemie
            if self.multi_db:
                try:
                    from werkzeug.security import generate_password_hash
                    new_password_hash = generate_password_hash(new_password)
                    
                    success = self.multi_db.update_user_password(user_id, new_password_hash)
                    if success:
                        # Log password reset
                        self.management_logger.log_user_change(
                            username=user.get('name', 'Unknown'),
                            action='password_reset',
                            target_user=user.get('name', 'Unknown'),
                            ip_address=request.remote_addr or "",
                            details={'email': email, 'user_id': user_id}
                        )
                        
                        return jsonify({
                            'status': 'success', 
                            'message': 'Hasło zostało pomyślnie zresetowane. Możesz się teraz zalogować.'
                        }), 200
                    else:
                        return jsonify({'status': 'error', 'message': 'Błąd podczas resetowania hasła.'}), 500
                        
                except Exception as e:
                    logger.error(f"Password reset failed for user {user_id}: {e}")
                    return jsonify({'status': 'error', 'message': 'Błąd podczas resetowania hasła.'}), 500
            
            # Fallback to old system
            else:
                success, msg = self.smart_home.change_password(user_id, new_password)
                if success:
                    return jsonify({'status': 'success', 'message': 'Hasło zostało pomyślnie zresetowane. Możesz się teraz zalogować.'}), 200
                else:
                    return jsonify({'status': 'error', 'message': msg}), 500
        
    def _send_verification_code(self, data):
        """Pierwszy krok rejestracji - wysłanie kodu weryfikacyjnego"""
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        # Podstawowa walidacja
        if not username or len(username) < 3:
            return jsonify({'status': 'error', 'message': 'Nazwa użytkownika musi mieć co najmniej 3 znaki.'}), 400
        if not email or '@' not in email:
            return jsonify({'status': 'error', 'message': 'Podaj poprawny adres email.'}), 400
        if not password or len(password) < 6:
            return jsonify({'status': 'error', 'message': 'Hasło musi mieć co najmniej 6 znaków.'}), 400
        
        # Sprawdź czy użytkownik już istnieje w multihouse systemie
        if self.multi_db and self.multi_db.check_user_exists(username=username):
            return jsonify({'status': 'error', 'message': 'Użytkownik już istnieje.'}), 400
        if self.multi_db and self.multi_db.check_user_exists(email=email):
            return jsonify({'status': 'error', 'message': 'Adres email jest już używany.'}), 400
        
        # Fallback to old system if multi_db not available
        if not self.multi_db:
            for user in self.smart_home.users.values():
                if user.get('name') == username:
                    return jsonify({'status': 'error', 'message': 'Użytkownik już istnieje.'}), 400
                if user.get('email') == email:
                    return jsonify({'status': 'error', 'message': 'Adres email jest już używany.'}), 400
        
        # Wygeneruj i wyślij kod weryfikacyjny
        verification_code = self.mail_manager.generate_verification_code()
        self.mail_manager.store_verification_code(email, verification_code)
        
        # Use async mail sending for verification emails to improve response time
        if self.async_mail_manager.send_verification_email_async(email, verification_code):
            return jsonify({
                'status': 'verification_sent',
                'message': 'Kod weryfikacyjny został wysłany na podany adres email.'
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'Błąd podczas wysyłania kodu weryfikacyjnego.'}), 500
    
    def _verify_and_register(self, data):
        """Drugi krok rejestracji - weryfikacja kodu i utworzenie użytkownika"""
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        verification_code = data.get('verification_code', '').strip()
        
        # Podstawowa walidacja
        if not username or not password or not email or not verification_code:
            return jsonify({'status': 'error', 'message': 'Wszystkie pola są wymagane.'}), 400
        
        # Weryfikuj kod
        is_valid, message = self.mail_manager.verify_code(email, verification_code)
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        # Ponowna walidacja danych (na wszelki wypadek)
        if len(username) < 3:
            return jsonify({'status': 'error', 'message': 'Nazwa użytkownika musi mieć co najmniej 3 znaki.'}), 400
        if '@' not in email:
            return jsonify({'status': 'error', 'message': 'Podaj poprawny adres email.'}), 400
        if len(password) < 6:
            return jsonify({'status': 'error', 'message': 'Hasło musi mieć co najmniej 6 znaków.'}), 400
        
        # Utwórz użytkownika w multihouse systemie z domyślnym domem
        if self.multi_db:
            try:
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash(password)
                
                # Utwórz użytkownika z automatycznym tworzeniem domyślnego domu
                # Nowy użytkownik otrzymuje rolę 'user' globalnie i 'admin' w swoim domyślnym domu
                user_id, home_id = self.multi_db.create_user(
                    username=username,
                    email=email, 
                    password_hash=password_hash,
                    role='user',  # Global role
                    create_default_home=True  # Automatically create home with admin role
                )
                
                # Log successful registration with home creation
                self.management_logger.log_user_change(
                    username=username,
                    action='register',
                    target_user=username,
                    ip_address=request.remote_addr or "",
                    details={
                        'email': email,
                        'user_id': user_id,
                        'home_id': home_id,
                        'home_created': True if home_id else False
                    }
                )
                
                return jsonify({
                    'status': 'success', 
                    'message': f'Rejestracja zakończona sukcesem! Utworzono domyślny dom: {username} Home.'
                }), 200
                
            except ValueError as e:
                return jsonify({'status': 'error', 'message': str(e)}), 400
            except Exception as e:
                logger.error(f"Registration failed for {username}: {e}")
                return jsonify({'status': 'error', 'message': 'Błąd podczas rejestracji. Spróbuj ponownie.'}), 500
        
        # Fallback to old system if multi_db not available  
        else:
            # Sprawdź czy użytkownik już istnieje (ponownie)
            for user in self.smart_home.users.values():
                if user.get('name') == username:
                    return jsonify({'status': 'error', 'message': 'Użytkownik już istnieje.'}), 400
                if user.get('email') == email:
                    return jsonify({'status': 'error', 'message': 'Adres email jest już używany.'}), 400
            
            # Utwórz użytkownika w starym systemie
            if hasattr(self.smart_home, 'add_user'):
                self.smart_home.add_user(username, password, 'user', email)
            else:
                from werkzeug.security import generate_password_hash
                import uuid
                user_id = str(uuid.uuid4())
                self.smart_home.users[user_id] = {
                    'name': username,
                    'password': generate_password_hash(password),
                    'role': 'user',
                    'email': email,
                    'profile_picture': ''
                }
                self.smart_home.save_config()
                
            # Log user registration for old system
            self.management_logger.log_user_change(
                username=username, 
                action='register', 
                target_user=username,
                ip_address=request.remote_addr or "",
                details={'email': email, 'system': 'legacy'}
            )
            
            return jsonify({'status': 'success', 'message': 'Rejestracja zakończona sukcesem!'}), 200
        
        # Log user registration
        self.management_logger.log_user_change(
            username=username, 
            action='register', 
            target_user=username,
            ip_address=request.remote_addr or "",
            details={'email': email}
        )
        
        return jsonify({'status': 'success', 'message': 'Rejestracja zakończona sukcesem!'}), 200

    def _find_user_by_email_or_username(self, email_or_username):
        """Znajduje użytkownika po email lub nazwie użytkownika"""
        
        # Use multihouse system if available
        if self.multi_db:
            user = self.multi_db.find_user_by_email_or_username(email_or_username)
            if user:
                return user['id'], user, user.get('email')
            return None, None, None
        
        # Fallback to old system
        else:
            # Najpierw spróbuj znaleźć po email
            for user_id, user in self.smart_home.users.items():
                if user.get('email') == email_or_username:
                    return user_id, user, user.get('email')
            
            # Jeśli nie znaleziono po email, spróbuj po nazwie użytkownika
            for user_id, user in self.smart_home.users.items():
                if user.get('name') == email_or_username:
                    return user_id, user, user.get('email')
            
            return None, None, None

    def _generate_dashboard_stats(self):
        """Generuje statystyki dla dashboardu administratora"""
        from datetime import datetime
        import random
        
        # Podstawowe statystyki
        users_count = len(self.smart_home.users)
        devices_count = len(self.smart_home.buttons) + len(self.smart_home.temperature_controls)

        automations_source = self.smart_home.automations
        if self.multi_db:
            user_id = session.get('user_id')
            if user_id:
                try:
                    automations_source, _ = self.get_current_home_automations(user_id)
                except PermissionError:
                    automations_source = []
                except Exception as exc:
                    self.app.logger.error(f"Failed to compute automation stats for multi-home dashboard: {exc}")
                    automations_source = []

        automations_count = len(automations_source)
        active_automations = sum(1 for auto in automations_source if auto.get('enabled', False))
        
        # Symulowane dane energii (w rzeczywistości pobierane z urządzeń)
        energy_today = round(random.uniform(10, 30), 1)
        energy_month = round(random.uniform(200, 500), 1)
        
        # Symulowane dane automatyzacji
        automations_executed_today = random.randint(5, 25)
        automation_errors = random.randint(0, 3)
        
        return {
            'users_count': users_count,
            'devices_count': devices_count,
            'automations_count': automations_count,
            'active_automations': active_automations,
            'energy_today': energy_today,
            'energy_month': energy_month,
            'automations_executed_today': automations_executed_today,
            'automation_errors': automation_errors
        }

    def _get_device_states(self):
        """Pobiera aktualny stan wszystkich urządzeń"""
        device_states = []
        
        # Dodaj przyciski
        for button in self.smart_home.buttons:
            device_states.append({
                'name': button['name'],
                'room': button['room'],
                'state': button['state'],
                'type': 'button'
            })
        
        # Dodaj kontrolery temperatury
        for control in self.smart_home.temperature_controls:
            device_states.append({
                'name': control['name'],
                'room': control['room'],
                'state': True,  # Kontrolery temperatury są zawsze aktywne
                'type': 'temperature',
                'temperature': control.get('temperature', 22)
            })
        
        return device_states

    def _get_management_logs(self):
        """Pobiera rzeczywiste logi zarządzania systemem"""
        return self.management_logger.get_logs(limit=50)

class APIManager(MultiHomeHelpersMixin):
    """Klasa zarządzająca endpointami API"""
    def __init__(self, app, socketio, smart_home, auth_manager, management_logger=None, cache=None, cached_data_access=None, multi_db=None):
        self.app = app
        self.socketio = socketio
        self.smart_home = smart_home
        self.auth_manager = auth_manager
        self.management_logger = management_logger or ManagementLogger()
        self.multi_db = multi_db
        # Use the same caching approach as RoutesManager to share cache keys
        try:
            self.cached_data = cached_data_access or (CachedDataAccess(cache, smart_home) if cache else None)
        except Exception:
            # Fallback to no caching helper if backend cache isn't available
            self.cached_data = None
        self.register_routes()

    def emit_update(self, event_name, data):
        """Safely emit socketio updates only if socketio is available"""
        if self.socketio:
            self.socketio.emit(event_name, data)

    def _resolve_home_id(self, user_id, preferred_home_id=None):
        """Resolve the active home identifier for the given user."""
        if not self.multi_db or not user_id:
            return None

        user_id_str = str(user_id)
        home_id = preferred_home_id or session.get('current_home_id')

        if not home_id:
            try:
                home_id = self.multi_db.get_user_current_home(user_id_str)
            except Exception as exc:
                if self.app:
                    self.app.logger.error(f"Failed to resolve current home for user {user_id_str}: {exc}")
                home_id = None

        return str(home_id) if home_id else None

    def get_current_home_automations(self, user_id, home_id=None):
        """Fetch automations for the current home context."""
        if not self.multi_db or not user_id:
            return list(self.smart_home.automations), None

        resolved_home_id = self._resolve_home_id(user_id, home_id)
        if not resolved_home_id:
            return [], None

        try:
            automations = self.multi_db.get_home_automations(resolved_home_id, str(user_id))
            return automations, resolved_home_id
        except PermissionError:
            raise
        except Exception as exc:
            if self.app:
                self.app.logger.error(f"Failed to load automations for home {resolved_home_id}: {exc}")
            return [], resolved_home_id

    def _emit_automation_update(self, home_id, automations):
        """Emit automation update events with home scoping information."""
        payload = {
            'home_id': str(home_id) if home_id else None,
            'automations': automations
        }
        self.emit_update('update_automations', payload)

    def get_current_home_rooms(self, user_id):
        """Get rooms from current selected home or fallback to main database"""
        if not self.multi_db or not user_id:
            # Fallback to main database
            return self.smart_home.rooms
        
        try:
            # Get current home ID from session or database
            from flask import session
            current_home_id = session.get('current_home_id')
            if not current_home_id:
                current_home_id = self.multi_db.get_user_current_home(user_id)
            
            if current_home_id:
                # Get rooms from multi-home system
                rooms_data = self.multi_db.get_home_rooms(current_home_id, user_id)
                # Convert to simple room names list for compatibility
                return [room['name'] for room in rooms_data]
            else:
                # No current home set, fallback to main database
                return self.smart_home.rooms
                
        except Exception as e:
            print(f"[DEBUG] Error getting multi-home rooms: {e}")
            # Fallback to main database
            return self.smart_home.rooms

    def get_current_home_buttons(self, user_id):
        """Get buttons from current selected home or fallback to main database"""
        if not self.multi_db or not user_id:
            # Fallback to main database
            return self.smart_home.buttons
        
        try:
            # Get current home ID from session or database
            from flask import session
            current_home_id = session.get('current_home_id')
            if not current_home_id:
                current_home_id = self.multi_db.get_user_current_home(user_id)
            
            if current_home_id:
                # Get buttons from multi-home system
                buttons_data = self.multi_db.get_buttons(current_home_id, user_id)
                # Convert to old format for compatibility
                buttons = []
                for button in buttons_data:
                    buttons.append({
                        'id': button['id'],
                        'name': button['name'],
                        'room': button['room_name'],
                        'state': button['state'],
                        'type': button['type']
                    })
                return buttons
            else:
                # No current home set, fallback to main database
                return self.smart_home.buttons
                
        except Exception as e:
            print(f"[DEBUG] Error getting multi-home buttons: {e}")
            # Fallback to main database
            return self.smart_home.buttons

    def register_routes(self):
        @self.app.route('/api', methods=['GET'])
        def api_root():
            return jsonify({"status": "ok", "message": "API root"}), 200

        @self.app.route('/weather')
        @self.auth_manager.login_required
        def weather():
            weather_data = self.smart_home.fetch_weather_data()
            if weather_data:
                return jsonify(weather_data)
            return jsonify({"error": "Nie udało się pobrać danych pogodowych"}), 500

        @self.app.route('/api/admin', methods=['GET'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def api_admin_root():
            return jsonify({"status": "ok", "message": "Admin API root"}), 200

        @self.app.route('/api/rooms', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_rooms():
            self.smart_home.check_and_save()
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({"status": "error", "message": "Nie jesteś zalogowany"}), 401

            if request.method == 'GET':
                rooms_payload, resolved_home_id = self._get_rooms_payload(user_id)
                response = {
                    'status': 'success',
                    'data': rooms_payload
                }
                if resolved_home_id:
                    response['meta'] = {'home_id': resolved_home_id}
                return jsonify(response)

            # POST branch
            if session.get('role') != 'admin':
                return jsonify({"status": "error", "message": "Brak uprawnień"}), 403

            payload = request.get_json(silent=True) or {}
            requested_name = payload.get('name') or payload.get('room')
            description = payload.get('description')

            if not requested_name or not str(requested_name).strip():
                return jsonify({"status": "error", "message": "Brak nazwy pokoju"}), 400

            room_name = str(requested_name).strip()
            resolved_home_id = self._resolve_home_id(user_id)

            if self.multi_db and resolved_home_id:
                try:
                    new_room_id = self.multi_db.create_room(resolved_home_id, room_name, str(user_id), description)
                    rooms_payload, _ = self._get_rooms_payload(user_id, resolved_home_id)
                    self._broadcast_rooms_update(user_id, resolved_home_id)

                    if self.cached_data:
                        invalidate = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                        if callable(invalidate):
                            invalidate()

                    try:
                        self.management_logger.log_room_change(
                            username=session.get('username', 'unknown'),
                            action='add',
                            room_name=room_name,
                            ip_address=request.remote_addr or ""
                        )
                    except Exception:
                        pass

                    new_room = next((room for room in rooms_payload if str(room.get('id')) == str(new_room_id)), None)
                    response = {
                        'status': 'success',
                        'room': new_room,
                        'meta': {'home_id': resolved_home_id}
                    }
                    return jsonify(response), 201
                except PermissionError:
                    return jsonify({"status": "error", "message": "Brak uprawnień do zarządzania pokojami"}), 403
                except ValueError as exc:
                    return jsonify({"status": "error", "message": str(exc)}), 400
                except Exception as exc:
                    if self.app:
                        self.app.logger.error(f"Failed to create room '{room_name}': {exc}")
                    return jsonify({"status": "error", "message": "Nie udało się utworzyć pokoju"}), 500

            # Legacy fallback when multi-home DB is unavailable
            if room_name.lower() in [room.lower() for room in self.smart_home.rooms]:
                return jsonify({"status": "error", "message": "Pokój o tej nazwie już istnieje"}), 400

            self.smart_home.rooms.append(room_name)
            if not self.smart_home.save_config():
                self.smart_home.rooms.pop()
                return jsonify({"status": "error", "message": "Nie udało się zapisać nowego pokoju"}), 500

            if self.cached_data:
                invalidate = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                if callable(invalidate):
                    invalidate()

            try:
                self.management_logger.log_room_change(
                    username=session.get('username', 'unknown'),
                    action='add',
                    room_name=room_name,
                    ip_address=request.remote_addr or ""
                )
            except Exception:
                pass

            self._broadcast_rooms_update(user_id)
            fallback_room = self._normalize_rooms_for_response([
                {'id': room_name, 'name': room_name}
            ])[0]
            return jsonify({'status': 'success', 'room': fallback_room}), 201

        @self.app.route('/api/rooms/<room_identifier>', methods=['DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def delete_room(room_identifier):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({"status": "error", "message": "Nie jesteś zalogowany"}), 401

            if not room_identifier:
                return jsonify({"status": "error", "message": "Brak identyfikatora pokoju"}), 400

            resolved_home_id = self._resolve_home_id(user_id)

            if self.multi_db and resolved_home_id:
                try:
                    room_id = self._resolve_room_identifier(room_identifier, user_id, resolved_home_id)
                    if room_id is None:
                        return jsonify({"status": "error", "message": "Nie znaleziono pokoju"}), 404

                    room_before = self.multi_db.get_room(room_id, str(user_id))
                    if not room_before:
                        return jsonify({"status": "error", "message": "Nie znaleziono pokoju"}), 404

                    deleted = self.multi_db.delete_room(room_id, str(user_id))
                    if not deleted:
                        return jsonify({"status": "error", "message": "Nie udało się usunąć pokoju"}), 500

                    if self.cached_data:
                        try:
                            invalidate_rooms = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                            if callable(invalidate_rooms):
                                invalidate_rooms()
                            invalidate_buttons = getattr(self.cached_data, 'invalidate_buttons_cache', None)
                            if callable(invalidate_buttons):
                                invalidate_buttons()
                            invalidate_temp = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                            if callable(invalidate_temp):
                                invalidate_temp()
                        except Exception:
                            pass

                    try:
                        self.management_logger.log_room_change(
                            username=session.get('username', 'unknown'),
                            action='delete',
                            room_name=room_before.get('name', ''),
                            ip_address=request.remote_addr or "",
                            old_name=room_before.get('name', '')
                        )
                    except Exception:
                        pass

                    self._broadcast_rooms_update(user_id, resolved_home_id)

                    if self.socketio:
                        buttons = self.get_current_home_buttons(user_id)
                        temp_controls = self.get_current_home_temperature_controls(user_id)
                        self.socketio.emit('update_buttons', buttons)
                        self.socketio.emit('update_temperature_controls', temp_controls)

                    return jsonify({"status": "success", "meta": {"home_id": resolved_home_id}})
                except PermissionError:
                    return jsonify({"status": "error", "message": "Brak uprawnień do usuwania pokoju"}), 403
                except Exception as exc:
                    if self.app:
                        self.app.logger.error(f"Failed to delete room {room_identifier}: {exc}")
                    return jsonify({"status": "error", "message": "Nie udało się usunąć pokoju"}), 500

            # Legacy fallback
            room_name = room_identifier
            if room_name not in self.smart_home.rooms:
                matching = [r for r in self.smart_home.rooms if r.lower() == room_name.lower()]
                if matching:
                    room_name = matching[0]
                else:
                    return jsonify({"status": "error", "message": "Nie znaleziono pokoju"}), 404

            self.smart_home.rooms = [r for r in self.smart_home.rooms if r != room_name]
            self.smart_home.buttons = [b for b in self.smart_home.buttons if b.get('room') != room_name]
            self.smart_home.temperature_controls = [c for c in self.smart_home.temperature_controls if c.get('room') != room_name]

            if not self.smart_home.save_config():
                return jsonify({"status": "error", "message": "Nie udało się usunąć pokoju"}), 500

            try:
                self.management_logger.log_room_change(
                    username=session.get('username', 'unknown'),
                    action='delete',
                    room_name=room_name,
                    ip_address=request.remote_addr or ""
                )
            except Exception:
                pass

            if self.cached_data:
                try:
                    invalidate_rooms = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                    if callable(invalidate_rooms):
                        invalidate_rooms()
                    invalidate_buttons = getattr(self.cached_data, 'invalidate_buttons_cache', None)
                    if callable(invalidate_buttons):
                        invalidate_buttons()
                    invalidate_temp = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                    if callable(invalidate_temp):
                        invalidate_temp()
                except Exception:
                    pass

            self._broadcast_rooms_update(user_id)

            if self.socketio:
                self.socketio.emit('update_buttons', self.smart_home.buttons)
                self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)

            return jsonify({"status": "success"})

        @self.app.route('/api/rooms/<room_identifier>', methods=['PUT'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def edit_room(room_identifier):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({"status": "error", "message": "Nie jesteś zalogowany"}), 401

            data = request.get_json(silent=True) or {}
            new_name = data.get('name') or data.get('new_name')
            new_description = data.get('description') if 'description' in data else None

            if new_name is not None and not str(new_name).strip():
                return jsonify({"status": "error", "message": "Nieprawidłowa nazwa pokoju"}), 400

            if new_name is None and new_description is None:
                return jsonify({"status": "error", "message": "Brak danych do aktualizacji"}), 400

            resolved_home_id = self._resolve_home_id(user_id)

            if self.multi_db and resolved_home_id:
                try:
                    room_id = self._resolve_room_identifier(room_identifier, user_id, resolved_home_id)
                    if room_id is None:
                        return jsonify({"status": "error", "message": "Nie znaleziono pokoju"}), 404

                    current_room = self.multi_db.get_room(room_id, str(user_id))
                    if not current_room:
                        return jsonify({"status": "error", "message": "Nie znaleziono pokoju"}), 404

                    updates = {}
                    if new_name is not None:
                        updates['name'] = str(new_name).strip()
                    if new_description is not None:
                        updates['description'] = new_description

                    updated_room = self.multi_db.update_room(room_id, str(user_id), **updates)
                    if not updated_room:
                        return jsonify({"status": "error", "message": "Nie udało się zaktualizować pokoju"}), 500

                    if self.cached_data:
                        try:
                            invalidate_rooms = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                            if callable(invalidate_rooms):
                                invalidate_rooms()
                        except Exception:
                            pass

                    try:
                        self.management_logger.log_room_change(
                            username=session.get('username', 'unknown'),
                            action='rename',
                            room_name=updated_room.get('name', ''),
                            ip_address=request.remote_addr or "",
                            old_name=current_room.get('name', '')
                        )
                    except Exception:
                        pass

                    self._broadcast_rooms_update(user_id, resolved_home_id)

                    if self.socketio:
                        buttons = self.get_current_home_buttons(user_id)
                        temp_controls = self.get_current_home_temperature_controls(user_id)
                        self.socketio.emit('update_buttons', buttons)
                        self.socketio.emit('update_temperature_controls', temp_controls)

                    normalized_room = self._normalize_rooms_for_response([updated_room], resolved_home_id)[0]
                    return jsonify({
                        'status': 'success',
                        'message': 'Nazwa pokoju zaktualizowana poprawnie!',
                        'room': normalized_room,
                        'meta': {'home_id': resolved_home_id}
                    }), 200
                except PermissionError:
                    return jsonify({"status": "error", "message": "Brak uprawnień do edycji pokoju"}), 403
                except ValueError as exc:
                    return jsonify({"status": "error", "message": str(exc)}), 400
                except Exception as exc:
                    if self.app:
                        self.app.logger.error(f"Failed to update room {room_identifier}: {exc}")
                    return jsonify({"status": "error", "message": "Nie udało się zaktualizować pokoju"}), 500

            # Legacy fallback
            if new_name is None:
                return jsonify({"status": "error", "message": "Nieprawidłowa nazwa pokoju"}), 400

            old_name = room_identifier
            matching = [r for r in self.smart_home.rooms if r.lower() == str(old_name).lower()]
            if not matching:
                return jsonify({"status": "error", "message": "Nie znaleziono pokoju"}), 404
            resolved_old_name = matching[0]

            if str(new_name).strip().lower() in [r.lower() for r in self.smart_home.rooms if r != resolved_old_name]:
                return jsonify({"status": "error", "message": "Pokój o tej nazwie już istnieje"}), 400

            for idx, value in enumerate(self.smart_home.rooms):
                if value == resolved_old_name:
                    self.smart_home.rooms[idx] = str(new_name).strip()
                    break

            for button in self.smart_home.buttons:
                if button.get('room') and button['room'].lower() == resolved_old_name.lower():
                    button['room'] = str(new_name).strip()

            for control in self.smart_home.temperature_controls:
                if control.get('room') and control['room'].lower() == resolved_old_name.lower():
                    control['room'] = str(new_name).strip()

            if not self.smart_home.save_config():
                return jsonify({"status": "error", "message": "Nie udało się zapisać edycji pokoju"}), 500

            try:
                self.management_logger.log_room_change(
                    username=session.get('username', 'unknown'),
                    action='rename',
                    room_name=str(new_name).strip(),
                    ip_address=request.remote_addr or "",
                    old_name=resolved_old_name
                )
            except Exception:
                pass

            if self.cached_data:
                try:
                    invalidate_rooms = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                    if callable(invalidate_rooms):
                        invalidate_rooms()
                    invalidate_buttons = getattr(self.cached_data, 'invalidate_buttons_cache', None)
                    if callable(invalidate_buttons):
                        invalidate_buttons()
                    invalidate_temp = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                    if callable(invalidate_temp):
                        invalidate_temp()
                except Exception:
                    pass

            self._broadcast_rooms_update(user_id)

            if self.socketio:
                self.socketio.emit('update_buttons', self.smart_home.buttons)
                self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)

            return jsonify({
                "status": "success",
                "message": "Nazwa pokoju zaktualizowana poprawnie!"
            }), 200

        @self.app.route('/api/rooms/order', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def set_rooms_order():
            data = request.get_json()
            rooms_input = []
            if data:
                if isinstance(data.get('room_ids'), list):
                    rooms_input = data.get('room_ids')
                elif isinstance(data.get('rooms'), list):
                    rooms_input = data.get('rooms')

            if not isinstance(rooms_input, list) or not rooms_input:
                return jsonify({'status': 'error', 'message': 'Brak listy pokoi'}), 400

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'status': 'error', 'message': 'Nie jesteś zalogowany'}), 401

            resolved_home_id = self._resolve_home_id(user_id)

            if self.multi_db and resolved_home_id:
                try:
                    normalized_ids = []
                    for item in rooms_input:
                        room_id = self._resolve_room_identifier(item, user_id, resolved_home_id)
                        if room_id is not None and room_id not in normalized_ids:
                            normalized_ids.append(room_id)

                    if not normalized_ids:
                        return jsonify({'status': 'error', 'message': 'Nie znaleziono żadnych pokoi do aktualizacji'}), 400

                    self.multi_db.reorder_rooms(resolved_home_id, str(user_id), normalized_ids)

                    if self.cached_data:
                        try:
                            invalidate = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                            if callable(invalidate):
                                invalidate()
                        except Exception:
                            pass

                    self._broadcast_rooms_update(user_id, resolved_home_id)

                    try:
                        self.management_logger.log_room_change(
                            username=session.get('username', 'unknown'),
                            action='reorder',
                            room_name='order_update',
                            ip_address=request.remote_addr or ""
                        )
                    except Exception:
                        pass

                    rooms_payload, _ = self._get_rooms_payload(user_id, resolved_home_id)
                    return jsonify({'status': 'success', 'data': rooms_payload, 'meta': {'home_id': resolved_home_id}})
                except PermissionError:
                    return jsonify({'status': 'error', 'message': 'Brak uprawnień do zmiany kolejności pokoi'}), 403
                except Exception as exc:
                    if self.app:
                        self.app.logger.error(f'Failed to reorder rooms: {exc}')
                    return jsonify({'status': 'error', 'message': 'Błąd zapisu kolejności'}), 500

            # Legacy fallback for non multi-home setups
            normalized_names = []
            for item in rooms_input:
                if isinstance(item, dict):
                    candidate = item.get('name')
                else:
                    candidate = item
                if candidate and candidate in self.smart_home.rooms and candidate not in normalized_names:
                    normalized_names.append(candidate)

            if normalized_names:
                self.smart_home.rooms = normalized_names
                if not self.smart_home.save_config():
                    return jsonify({'status': 'error', 'message': 'Nie udało się zapisać kolejności pokoi'}), 500
            else:
                return jsonify({'status': 'error', 'message': 'Brak prawidłowych pokoi do zapisania'}), 400

            if self.cached_data:
                try:
                    invalidate = getattr(self.cached_data, 'invalidate_rooms_cache', None)
                    if callable(invalidate):
                        invalidate()
                except Exception:
                    pass

            self._broadcast_rooms_update(user_id)

            try:
                self.management_logger.log_room_change(
                    username=session.get('username', 'unknown'),
                    action='reorder',
                    room_name='order_update',
                    ip_address=request.remote_addr or ""
                )
            except Exception:
                pass

            return jsonify({'status': 'success'})

        @self.app.route('/api/devices/batch-update', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def batch_update_devices():
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'status': 'error', 'message': 'Nie jesteś zalogowany'}), 401
                
            data = request.get_json()
            print(f"[DEBUG] POST /api/devices/batch-update - data: {data}")
            
            if not data or 'devices' not in data:
                return jsonify({'status': 'error', 'message': 'Missing devices array'}), 400
                
            devices = data['devices']
            if not isinstance(devices, list):
                return jsonify({'status': 'error', 'message': 'devices must be an array'}), 400
                
            try:
                if self.multi_db:
                    print(f"[DEBUG] Processing batch update for {len(devices)} devices")
                    result = self.multi_db.batch_update_devices(devices, str(user_id))
                    
                    updated_count = len(result['updated'])
                    failed_count = len(result['failed'])
                    
                    print(f"[DEBUG] Batch update result: {updated_count} updated, {failed_count} failed")
                    
                    # Invalidate caches after batch update
                    if updated_count > 0 and self.cached_data:
                        try:
                            methods = ['invalidate_buttons_cache', 'invalidate_temperature_cache', 'invalidate_room_cache']
                            for method_name in methods:
                                method = getattr(self.cached_data, method_name, None)
                                if callable(method):
                                    method()
                            print(f"[DEBUG] Cache invalidation completed")
                        except Exception as cache_error:
                            print(f"[WARNING] Cache invalidation error: {cache_error}")
                            
                    # Emit socket updates for affected device types
                    if updated_count > 0 and self.socketio:
                        try:
                            buttons = self.get_current_home_buttons(user_id)
                            controls = self.get_current_home_temperature_controls(user_id)
                            self.socketio.emit('update_buttons', buttons)
                            self.socketio.emit('update_temperature_controls', controls)
                            print(f"[DEBUG] Socket updates emitted")
                        except Exception as socket_error:
                            print(f"[WARNING] Socket emission error: {socket_error}")
                            
                    response_data = {
                        'status': 'success' if failed_count == 0 else 'partial_success',
                        'updated': updated_count,
                        'total': len(devices)
                    }
                    
                    if result['failed']:
                        response_data['failed'] = result['failed']
                        
                    print(f"[DEBUG] Batch update completed successfully")
                    return jsonify(response_data)
                    
                else:
                    return jsonify({'status': 'error', 'message': 'Multi-home database not available'}), 500
                    
            except Exception as e:
                print(f"[ERROR] Batch update failed: {e}")
                return jsonify({'status': 'error', 'message': f'Batch update error: {str(e)}'}), 500

        @self.app.route('/api/buttons/order', methods=['POST'])
        @self.auth_manager.api_login_required
        @self.auth_manager.api_admin_required
        def set_buttons_order():
            data = request.get_json() or {}
            order = data.get('order')
            if not isinstance(order, list):
                order = data.get('buttons')

            if not isinstance(order, list):
                return jsonify({'status': 'error', 'message': 'Brak listy przycisków'}), 400

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'status': 'error', 'message': 'Nie jesteś zalogowany'}), 401

            if self.multi_db:
                resolved_home_id = self._resolve_home_id(user_id)
                if not resolved_home_id:
                    return jsonify({'status': 'error', 'message': 'Nie wybrano domu'}), 400

                room_identifier = data.get('room_id') if data.get('room_id') not in (None, '', 'null') else None
                if room_identifier is None and data.get('room') not in (None, '', 'null'):
                    room_identifier = data.get('room')

                room_id = None
                if room_identifier is not None:
                    try:
                        room_id = int(room_identifier)
                    except (TypeError, ValueError):
                        room_id = self._resolve_room_identifier(room_identifier, user_id, resolved_home_id)

                if room_id is None:
                    return jsonify({'status': 'error', 'message': 'Nie znaleziono pokoju'}), 400

                try:
                    for index, device_id in enumerate(order):
                        if device_id in (None, '', 'null'):
                            continue
                        self.multi_db.update_device(device_id, str(user_id), display_order=index)

                    if self.cached_data:
                        invalidate = getattr(self.cached_data, 'invalidate_buttons_cache', None)
                        if callable(invalidate):
                            invalidate()

                    buttons_payload = self.get_current_home_buttons(user_id)
                    if self.socketio:
                        self.socketio.emit('update_buttons', buttons_payload)

                    response = {'status': 'success', 'data': buttons_payload, 'meta': {'home_id': resolved_home_id}}
                    return jsonify(response)
                except PermissionError:
                    return jsonify({'status': 'error', 'message': 'Brak uprawnień do zmiany kolejności urządzeń'}), 403
                except Exception as exc:
                    if self.app:
                        self.app.logger.error(f'Failed to reorder buttons: {exc}')
                    return jsonify({'status': 'error', 'message': 'Błąd zapisu kolejności'}), 500

            # Legacy fallback for single-home mode
            if 'room' in data and isinstance(data.get('order'), list):
                room = data['room']
                order_list = data['order']
                room_buttons = [b for b in self.smart_home.buttons if b.get('room') == room]
                new_room_buttons = []
                for btn_id in order_list:
                    found = next((b for b in room_buttons if str(b.get('id')) == str(btn_id)), None)
                    if found:
                        new_room_buttons.append(found)
                other_buttons = [b for b in self.smart_home.buttons if b.get('room') != room]
                self.smart_home.buttons = other_buttons + new_room_buttons
                if self.socketio:
                    self.socketio.emit('update_buttons', self.smart_home.buttons)
                self.smart_home.save_config()
                return jsonify({'status': 'success'})

            new_order = []
            for btn in order:
                found = next((b for b in self.smart_home.buttons if b['name'] == btn.get('name') and b['room'] == btn.get('room')), None)
                if found:
                    new_order.append(found)
            self.smart_home.buttons = new_order
            if self.socketio:
                self.socketio.emit('update_buttons', self.smart_home.buttons)
            self.smart_home.save_config()
            return jsonify({'status': 'success'})

        @self.app.route('/api/temperature_controls/order', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def set_temp_controls_order():
            data = request.get_json() or {}
            order = data.get('order')
            if not isinstance(order, list):
                return jsonify({'status': 'error', 'message': 'Brak danych lub nieprawidłowy format'}), 400

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'status': 'error', 'message': 'Nie jesteś zalogowany'}), 401

            if self.multi_db:
                resolved_home_id = self._resolve_home_id(user_id)
                if not resolved_home_id:
                    return jsonify({'status': 'error', 'message': 'Nie wybrano domu'}), 400

                room_identifier = data.get('room_id') if data.get('room_id') not in (None, '', 'null') else None
                if room_identifier is None and data.get('room') not in (None, '', 'null'):
                    room_identifier = data.get('room')

                room_id = None
                if room_identifier is not None:
                    try:
                        room_id = int(room_identifier)
                    except (TypeError, ValueError):
                        room_id = self._resolve_room_identifier(room_identifier, user_id, resolved_home_id)

                if room_id is None:
                    return jsonify({'status': 'error', 'message': 'Nie znaleziono pokoju'}), 400

                try:
                    for index, control_id in enumerate(order):
                        if control_id in (None, '', 'null'):
                            continue
                        self.multi_db.update_device(control_id, str(user_id), display_order=index)

                    if self.cached_data:
                        invalidate = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                        if callable(invalidate):
                            invalidate()

                    controls_payload = self.get_current_home_temperature_controls(user_id)
                    if self.socketio:
                        self.socketio.emit('update_temperature_controls', controls_payload)

                    response = {'status': 'success', 'data': controls_payload, 'meta': {'home_id': resolved_home_id}}
                    return jsonify(response)
                except PermissionError:
                    return jsonify({'status': 'error', 'message': 'Brak uprawnień do zmiany kolejności urządzeń'}), 403
                except Exception as exc:
                    if self.app:
                        self.app.logger.error(f'Failed to reorder temperature controls: {exc}')
                    return jsonify({'status': 'error', 'message': 'Błąd zapisu kolejności'}), 500

            # Legacy fallback
            if 'room' in data:
                room = data['room']
                order_list = data['order']
                room_controls = [c for c in self.smart_home.temperature_controls if c.get('room') == room]
                new_room_controls = []
                for ctrl_id in order_list:
                    found = next((c for c in room_controls if c['id'] == ctrl_id), None)
                    if found:
                        new_room_controls.append(found)
                self.smart_home.temperature_controls = [c for c in self.smart_home.temperature_controls if c.get('room') != room] + new_room_controls
                if self.socketio:
                    self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                self.smart_home.save_config()
                return jsonify({'status': 'success'})

            return jsonify({'status': 'error', 'message': 'Brak danych lub nieprawidłowy format'}), 400

        @self.app.route('/api/buttons', methods=['GET', 'POST'])
        @self.auth_manager.api_login_required
        def manage_buttons():
            self.smart_home.check_and_save()
            if request.method == 'GET':
                # Get current user and use multi-home system
                user_id = session.get('user_id')
                buttons = self.get_current_home_buttons(user_id)
                resolved_home_id = self._resolve_home_id(user_id) if user_id else None
                payload = {
                    "status": "success",
                    "data": buttons
                }
                if resolved_home_id:
                    payload['meta'] = {'home_id': resolved_home_id}
                print(f"[DEBUG] GET /api/buttons returning {len(buttons)} buttons")
                return jsonify(payload)
            elif request.method == 'POST':
                if session.get('role') != 'admin':
                    return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
                payload = request.get_json(silent=True) or {}
                name = (payload.get('name') or '').strip()
                raw_room = payload.get('room')
                raw_room_id = payload.get('room_id')
                try:
                    print(f"[DEBUG] POST /api/buttons payload: name={name!r}, raw_room={raw_room!r}, raw_room_id={raw_room_id!r}")
                except Exception:
                    pass

                if raw_room is None:
                    raw_room = payload.get('room_name') or payload.get('roomName')
                if raw_room_id in (None, '', 'null'):
                    raw_room_id = payload.get('roomId') or payload.get('roomIdentifier') or payload.get('room_id_value')

                if isinstance(raw_room, dict):
                    raw_room_id = raw_room_id or raw_room.get('id') or raw_room.get('room_id')
                    raw_room = raw_room.get('name') or raw_room.get('room')

                room_value = raw_room
                room_id_value = raw_room_id
                user_id = session.get('user_id')

                if not name:
                    return jsonify({"status": "error", "message": "Brak nazwy urządzenia"}), 400

                if self.multi_db:
                    if not user_id:
                        return jsonify({"status": "error", "message": "Nie jesteś zalogowany"}), 401

                    resolved_home_id = self._resolve_home_id(user_id)
                    if not resolved_home_id:
                        return jsonify({"status": "error", "message": "Nie wybrano domu"}), 400

                    try:
                        room_identifier = room_id_value if room_id_value not in (None, '', 'null') else None
                        if room_identifier is None and room_value not in (None, '', 'null'):
                            room_identifier = room_value

                        room_id = None
                        if room_identifier is None:
                            room_id = None  # explicit unassigned
                        else:
                            # Treat common unassigned aliases as unassigned rather than erroring
                            if isinstance(room_identifier, str) and room_identifier.strip().lower() in {"", "nieprzypisane", "unassigned", "none", "null"}:
                                room_id = None
                            else:
                                try:
                                    room_id = int(room_identifier)
                                except (TypeError, ValueError):
                                    room_id = self._resolve_room_identifier(room_identifier, user_id, resolved_home_id)
                        try:
                            print(f"[DEBUG] POST /api/buttons home={resolved_home_id}, room_identifier={room_identifier!r} -> resolved room_id={room_id!r}")
                        except Exception:
                            pass

                            # If user provided a specific non-unassigned identifier but resolution failed -> 404
                            if room_id is None and not (isinstance(room_identifier, str) and room_identifier.strip().lower() in {"", "nieprzypisane", "unassigned", "none", "null"}):
                                return jsonify({"status": "error", "message": "Nie znaleziono pokoju"}), 404

                        new_id = self.multi_db.create_device(room_id, name, 'button', str(user_id), state=False, enabled=True, home_id=resolved_home_id)
                        if self.cached_data:
                            invalidate = getattr(self.cached_data, 'invalidate_buttons_cache', None)
                            if callable(invalidate):
                                invalidate()

                        buttons = self.get_current_home_buttons(user_id)
                        created_button = next((btn for btn in buttons if str(btn.get('id')) == str(new_id)), None)

                        if self.socketio:
                            self.socketio.emit('update_buttons', buttons)

                        response = {
                            "status": "success",
                            "id": new_id,
                            "button": created_button,
                            "meta": {"home_id": resolved_home_id}
                        }
                        return jsonify(response), 201
                    except PermissionError:
                        return jsonify({"status": "error", "message": "Brak uprawnień do dodawania urządzeń"}), 403
                    except ValueError as exc:
                        return jsonify({"status": "error", "message": str(exc)}), 400
                    except Exception as exc:
                        if self.app:
                            self.app.logger.error(f"Failed to create button '{name}': {exc}")
                        return jsonify({"status": "error", "message": "Nie udało się utworzyć urządzenia"}), 500

                # Legacy single-home fallback
                if not room_value:
                    return jsonify({"status": "error", "message": "Brak nazwy lub pokoju"}), 400

                try:
                    if hasattr(self.smart_home, 'add_button'):
                        print(f"[DEBUG] POST /api/buttons add_button legacy path: name={name}, room={room_value}")
                        new_id = self.smart_home.add_button(name, room_value, state=False)
                        if self.cached_data and hasattr(self.cached_data, 'cache'):
                            self.cached_data.cache.delete('buttons_list')
                        if self.socketio:
                            self.socketio.emit('update_buttons', self.smart_home.buttons)
                        return jsonify({"status": "success", "id": new_id})
                    else:
                        return jsonify({"status": "error", "message": "Brak metody add_button"}), 500
                except Exception as e:
                    print(f"[DEBUG] POST /api/buttons error: {e}")
                    return jsonify({"status": "error", "message": str(e)}), 500

                return jsonify({"status": "error", "message": "Invalid button data"}), 400

        @self.app.route('/api/buttons/<id>', methods=['PUT', 'DELETE'])
        @self.auth_manager.api_login_required
        @self.auth_manager.api_admin_required
        def button_by_id(id):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'status': 'error', 'message': 'Nie jesteś zalogowany'}), 401

            if request.method == 'PUT':
                print(f"[DEBUG] PUT /api/buttons/{id} - Starting")
                data = request.get_json()
                print(f"[DEBUG] PUT data received: {data}")
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400

                # Multi-home branch
                if self.multi_db:
                    print(f"[DEBUG] PUT /api/buttons/{id} - Multi-home mode")
                    device = self.multi_db.get_device(id, str(user_id))
                    print(f"[DEBUG] Current device: {device}")
                    if not device:
                        return jsonify({'status': 'error', 'message': 'Button not found'}), 404

                    updates = {}
                    if 'name' in data and data['name']:
                        updates['name'] = data['name']
                        print(f"[DEBUG] Name update: {data['name']}")

                    room_identifier = None
                    if data.get('room_id') not in (None, '', 'null'):
                        room_identifier = data.get('room_id')
                        print(f"[DEBUG] Room ID provided: {room_identifier}")
                    elif 'room' in data and data['room'] not in (None, '', 'null'):
                        room_identifier = data['room']
                        print(f"[DEBUG] Room name provided: {room_identifier}")

                    if room_identifier is not None:
                        print(f"[DEBUG] Processing room change to: {room_identifier}")
                        try:
                            updates['room_id'] = int(room_identifier)
                            print(f"[DEBUG] Using room_id as integer: {updates['room_id']}")
                        except (TypeError, ValueError):
                            resolved_room_id = self._resolve_room_identifier(room_identifier, user_id, device.get('home_id'))
                            print(f"[DEBUG] Resolved room_id: {resolved_room_id}")
                            if resolved_room_id is None:
                                return jsonify({'status': 'error', 'message': 'Nie znaleziono pokoju'}), 404
                            updates['room_id'] = resolved_room_id

                    print(f"[DEBUG] Final updates dict: {updates}")
                    if not updates:
                        return jsonify({'status': 'error', 'message': 'Brak pól do aktualizacji'}), 400

                    try:
                        print(f"[DEBUG] Calling multi_db.update_device with: id={id}, user_id={user_id}, updates={updates}")
                        success = self.multi_db.update_device(id, str(user_id), **updates)
                        print(f"[DEBUG] update_device result: {success}")
                    except PermissionError as e:
                        print(f"[DEBUG] Permission error: {e}")
                        return jsonify({'status': 'error', 'message': 'Brak uprawnień do edycji urządzenia'}), 403
                    except ValueError as exc:
                        print(f"[DEBUG] Value error: {exc}")
                        return jsonify({'status': 'error', 'message': str(exc)}), 400
                    except Exception as exc:
                        print(f"[DEBUG] Unexpected error: {exc}")
                        return jsonify({'status': 'error', 'message': f'Update failed: {exc}'}), 500

                    if not success:
                        print(f"[DEBUG] Update returned False")
                        return jsonify({'status': 'error', 'message': 'Nie udało się zapisać edycji przycisku'}), 500

                    print(f"[DEBUG] Update successful, invalidating cache")
                    if self.cached_data:
                        try:
                            invalidate = getattr(self.cached_data, 'invalidate_buttons_cache', None)
                            if callable(invalidate):
                                invalidate()
                        except Exception:
                            pass

                    updated_device = self.multi_db.get_device(id, str(user_id))
                    print(f"[DEBUG] Updated device: {updated_device}")
                    buttons = self.get_current_home_buttons(user_id)
                    print(f"[DEBUG] Emitting {len(buttons)} buttons via socketio")
                    if self.socketio:
                        self.socketio.emit('update_buttons', buttons)

                    response = {
                        'status': 'success',
                        'button': updated_device,
                        'meta': {'home_id': str(updated_device.get('home_id')) if updated_device else None}
                    }
                    print(f"[DEBUG] PUT /api/buttons/{id} - Success response: {response}")
                    return jsonify(response)

                # Legacy single-home fallback
                device = self.smart_home.get_device_by_id(id)
                print(f"[DEBUG] Device found: {device}")
                if not device:
                    return jsonify({'status': 'error', 'message': 'Button not found'}), 404

                updates = {}
                if 'name' in data:
                    updates['name'] = data['name']
                if 'room' in data:
                    updates['room'] = data['room']

                print(f"[DEBUG] Updates prepared: {updates}")
                if not updates:
                    return jsonify({'status': 'error', 'message': 'No valid fields to update'}), 400

                if hasattr(self.smart_home, 'update_device'):
                    print(f"[DEBUG] Using database mode - calling update_device")
                    success = self.smart_home.update_device(id, updates)
                    print(f"[DEBUG] update_device result: {success}")
                    if not success:
                        return jsonify({"status": "error", "message": "Nie udało się zapisać edycji przycisku"}), 500
                    if self.cached_data:
                        print(f"[DEBUG] Invalidating cache")
                        self.cached_data.invalidate_buttons_cache()
                else:
                    print(f"[DEBUG] Using JSON mode fallback")
                    idx = next((i for i, b in enumerate(self.smart_home.buttons) if str(b.get('id')) == str(id)), None)
                    if idx is None:
                        return jsonify({'status': 'error', 'message': 'Button not found'}), 404
                    if 'name' in updates:
                        self.smart_home.buttons[idx]['name'] = updates['name']
                    if 'room' in updates:
                        self.smart_home.buttons[idx]['room'] = updates['room']
                    if not self.smart_home.save_config():
                        return jsonify({"status": "error", "message": "Nie udało się zapisać edycji przycisku"}), 500

                if self.socketio:
                    print(f"[DEBUG] Emitting socket update")
                    fresh_buttons = self.cached_data.get_buttons() if self.cached_data else self.smart_home.buttons
                    print(f"[DEBUG] Fresh buttons data from cache: {fresh_buttons}")
                    self.socketio.emit('update_buttons', fresh_buttons)

                print(f"[DEBUG] PUT /api/buttons/{id} - Success (legacy mode)")
                return jsonify({'status': 'success', 'message': 'Nazwa przycisku zaktualizowana poprawnie!'}), 200
                
            elif request.method == 'DELETE':
                if self.multi_db:
                    resolved_home_id = self._resolve_home_id(user_id)
                    device = self.multi_db.get_device(id, str(user_id))
                    if not device:
                        return jsonify({'status': 'error', 'message': 'Button not found'}), 404

                    try:
                        success = self.multi_db.delete_device(id, str(user_id), resolved_home_id)
                    except PermissionError:
                        return jsonify({'status': 'error', 'message': 'Brak uprawnień do usunięcia urządzenia'}), 403

                    if not success:
                        return jsonify({"status": "error", "message": "Nie udało się usunąć przycisku"}), 500

                    if self.cached_data:
                        try:
                            invalidate = getattr(self.cached_data, 'invalidate_buttons_cache', None)
                            if callable(invalidate):
                                invalidate()
                        except Exception:
                            pass

                    buttons = self.get_current_home_buttons(user_id)
                    if self.socketio:
                        self.socketio.emit('update_buttons', buttons)

                    return jsonify({'status': 'success', 'meta': {'home_id': str(resolved_home_id) if resolved_home_id else None}})

                device = self.smart_home.get_device_by_id(id)
                if not device:
                    return jsonify({'status': 'error', 'message': 'Button not found'}), 404

                if hasattr(self.smart_home, 'delete_device'):
                    success = self.smart_home.delete_device(id)
                    if not success:
                        return jsonify({"status": "error", "message": "Nie udało się usunąć przycisku"}), 500
                    if self.cached_data:
                        self.cached_data.invalidate_buttons_cache()
                else:
                    idx = next((i for i, b in enumerate(self.smart_home.buttons) if str(b.get('id')) == str(id)), None)
                    if idx is None:
                        return jsonify({'status': 'error', 'message': 'Button not found'}), 404
                    self.smart_home.buttons.pop(idx)
                    if not self.smart_home.save_config():
                        return jsonify({"status": "error", "message": "Nie udało się zapisać po usunięciu przycisku"}), 500

                if self.socketio:
                    self.socketio.emit('update_buttons', self.smart_home.buttons)
                
                return jsonify({'status': 'success'})

        @self.app.route('/api/buttons/<id>/toggle', methods=['POST'])
        @self.auth_manager.api_login_required
        def toggle_button_state(id):
            """Toggle button state via REST API using multi-home system"""
            try:
                from flask import session
                user_id = session.get('user_id')
                print(f"[DEBUG] toggle_button_state called with id: {id}, user_id: {user_id}")
                
                if not user_id:
                    return jsonify({'status': 'error', 'message': 'User not logged in'}), 401
                
                # Use multi-home system if available
                if self.multi_db:
                    device_id = normalize_device_id(id)
                    print(f"[DEBUG] Using multi-home system, raw_device_id: {id} (type: {type(id)}), normalized: {device_id} (type: {type(device_id)}), user_id: {user_id}")

                    if device_id is None:
                        return jsonify({'status': 'error', 'message': 'Invalid device identifier'}), 400

                    # Get device details from multi-home system
                    try:
                        device = self.multi_db.get_device(device_id, user_id)
                        print(f"[DEBUG] get_device returned: {device}")
                    except Exception as e:
                        print(f"[DEBUG ERROR] Exception in get_device: {e}")
                        return jsonify({'status': 'error', 'message': f'Error getting device: {str(e)}'}), 500
                    
                    if not device:
                        print(f"[DEBUG] Device not found with id: {id}")
                        return jsonify({'status': 'error', 'message': 'Device not found or access denied'}), 404
                    
                    print(f"[DEBUG] Found device: {device['name']} in room_id: {device['room_id']}, current state: {device.get('state', False)}")
                    
                    # Get new state from request or toggle current state
                    data = {}
                    if request.content_type and 'application/json' in request.content_type:
                        data = request.get_json() or {}
                    
                    new_state = data.get('state')
                    if new_state is None:
                        new_state = not device.get('state', False)
                    
                    print(f"[DEBUG] New state will be: {new_state} (type: {type(new_state)})")
                    
                    # Update device state in multi-home system
                    try:
                        target_device_id = normalize_device_id(device.get('id', device_id))
                        if target_device_id is None:
                            fallback_id = device_id if device_id is not None else device.get('id')
                            target_device_id = normalize_device_id(fallback_id)
                        if target_device_id is None:
                            return jsonify({'status': 'error', 'message': 'Invalid device identifier'}), 400
                        print(f"[DEBUG] Calling update_device with device_id={target_device_id}, raw_id={id}, user_id={user_id}, state={new_state}")
                        success = self.multi_db.update_device(target_device_id, user_id, state=new_state)
                        print(f"[DEBUG] update_device returned: {success} (type: {type(success)})")
                        if not success:
                            return jsonify({'status': 'error', 'message': 'Failed to update device state'}), 500
                        
                        print(f"[DEBUG] Device state updated successfully in multi-home system")
                    except Exception as e:
                        print(f"[DEBUG ERROR] Exception in update_device: {e}")
                        return jsonify({'status': 'error', 'message': f'Error updating device: {str(e)}'}), 500
                    
                    # Emit socket updates
                    if self.socketio:
                        self.socketio.emit('update_button', {
                            'room': device.get('room_name', ''),
                            'name': device['name'],
                            'state': new_state
                        })
                    
                    # Log the action
                    if hasattr(self.management_logger, 'log_device_action'):
                        user_data = self.smart_home.get_user_data(user_id) if user_id else None
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                            device_name=device['name'],
                            room=device.get('room_name', ''),
                            action='toggle',
                            new_state=new_state,
                            ip_address=request.environ.get('REMOTE_ADDR', '')
                        )
                    
                    return jsonify({
                        'status': 'success',
                        'button': {
                            'id': device['id'],
                            'name': device['name'],
                            'room': device.get('room_name', ''),
                            'state': new_state
                        }
                    })
                
                # Fallback to old system
                print(f"[DEBUG] Using old system fallback")
                
                # Find button by ID in old system
                button = None
                button_idx = None
                for i, b in enumerate(self.smart_home.buttons):
                    if str(b.get('id')) == str(id):
                        button = b
                        button_idx = i
                        break
                
                if not button:
                    print(f"[DEBUG] Button not found with id: {id}")
                    return jsonify({'status': 'error', 'message': 'Button not found'}), 404
                
                print(f"[DEBUG] Found button: {button['name']} in {button['room']}, current state: {button.get('state', False)}")
                
                # Get new state from request or toggle current state
                data = {}
                if request.content_type and 'application/json' in request.content_type:
                    data = request.get_json() or {}
                
                new_state = data.get('state')
                if new_state is None:
                    new_state = not button.get('state', False)
                
                print(f"[DEBUG] New state will be: {new_state}")
                
                # Update button state
                if hasattr(self.smart_home, 'update_button_state'):
                    # Use database method if available
                    print(f"[DEBUG] Updating button state in database: {button['room']}, {button['name']}, {new_state}")
                    success = self.smart_home.update_button_state(button['room'], button['name'], new_state)
                    print(f"[DEBUG] Database update success: {success}")
                    if not success:
                        return jsonify({'status': 'error', 'message': 'Failed to update button state in database'}), 500
                else:
                    # Fallback to JSON mode
                    print(f"[DEBUG] Updating button state in JSON mode")
                    self.smart_home.buttons[button_idx]['state'] = new_state
                    if not self.smart_home.save_config():
                        return jsonify({'status': 'error', 'message': 'Failed to save button state'}), 500
                
                # Emit socket updates
                self.socketio.emit('update_button', {
                    'room': button['room'],
                    'name': button['name'],
                    'state': new_state
                })
                self.socketio.emit('sync_button_states', {
                    f"{b['room']}_{b['name']}": b['state'] for b in self.smart_home.buttons
                })
                
                # Log the action
                if hasattr(self.management_logger, 'log_device_action'):
                    user_id = session.get('user_id')
                    user_data = self.smart_home.get_user_data(user_id) if user_id else None
                    self.management_logger.log_device_action(
                        user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                        device_name=button['name'],
                        room=button['room'],
                        action='toggle',
                        new_state=new_state,
                        ip_address=request.environ.get('REMOTE_ADDR', '')
                    )
                
                return jsonify({
                    'status': 'success',
                    'button': {
                        'id': button['id'],
                        'name': button['name'],
                        'room': button['room'],
                        'state': new_state
                    }
                })
                
            except Exception as e:
                print(f"Error in toggle_button_state: {e}")
                return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

        @self.app.route('/api/temperature_controls', methods=['GET', 'POST'])
        @self.auth_manager.api_login_required
        def manage_temperature_controls():
            self.smart_home.check_and_save()
            if request.method == 'GET':
                # Get current user and use multi-home system
                user_id = session.get('user_id')
                temp_controls = self.get_current_home_temperature_controls(user_id)
                resolved_home_id = self._resolve_home_id(user_id) if user_id else None
                response = {
                    "status": "success", 
                    "data": temp_controls
                }
                if resolved_home_id:
                    response['meta'] = {'home_id': resolved_home_id}
                return jsonify(response)
            elif request.method == 'POST':
                try:
                    if session.get('role') != 'admin':
                        return jsonify({"status": "error", "message": "Brak uprawnień"}), 403
                    payload = request.get_json(silent=True) or {}
                    name = (payload.get('name') or '').strip()
                    raw_room = payload.get('room')
                    raw_room_id = payload.get('room_id')
                    user_id = session.get('user_id')

                    if raw_room is None:
                        raw_room = payload.get('room_name') or payload.get('roomName')
                    if raw_room_id in (None, '', 'null'):
                        raw_room_id = payload.get('roomId') or payload.get('roomIdentifier') or payload.get('room_id_value')

                    if isinstance(raw_room, dict):
                        raw_room_id = raw_room_id or raw_room.get('id') or raw_room.get('room_id')
                        raw_room = raw_room.get('name') or raw_room.get('room')

                    room_value = raw_room
                    room_id_value = raw_room_id

                    if not name:
                        return jsonify({"status": "error", "message": "Brak nazwy sterownika"}), 400

                    if self.multi_db:
                        if not user_id:
                            return jsonify({"status": "error", "message": "Nie jesteś zalogowany"}), 401

                        resolved_home_id = self._resolve_home_id(user_id)
                        if not resolved_home_id:
                            return jsonify({"status": "error", "message": "Nie wybrano domu"}), 400

                        try:
                            room_identifier = room_id_value if room_id_value not in (None, '', 'null') else None
                            if room_identifier is None and room_value not in (None, '', 'null'):
                                room_identifier = room_value

                            room_id = None
                            if room_identifier is None:
                                room_id = None  # create unassigned device (room_id NULL)
                            else:
                                try:
                                    room_id = int(room_identifier)
                                except (TypeError, ValueError):
                                    room_id = self._resolve_room_identifier(room_identifier, user_id, resolved_home_id)

                            # If user provided a specific room identifier but resolution failed -> 404
                            if room_identifier is not None and room_id is None:
                                return jsonify({"status": "error", "message": "Nie znaleziono pokoju"}), 404

                            target_temp = payload.get('target_temperature', 21.0)
                            mode = payload.get('mode', 'auto')
                            new_id = self.multi_db.create_device(
                                room_id,
                                name,
                                'temperature_control',
                                str(user_id),
                                state=None,
                                target_temperature=target_temp,
                                mode=mode,
                                enabled=payload.get('enabled', True),
                                home_id=resolved_home_id
                            )

                            if self.cached_data:
                                invalidate = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                                if callable(invalidate):
                                    invalidate()

                            controls = self.get_current_home_temperature_controls(user_id)
                            created_control = next((ctrl for ctrl in controls if str(ctrl.get('id')) == str(new_id)), None)

                            if self.socketio:
                                self.socketio.emit('update_temperature_controls', controls)

                            response = {
                                "status": "success",
                                "id": new_id,
                                "control": created_control,
                                "meta": {"home_id": resolved_home_id}
                            }
                            return jsonify(response), 201
                        except PermissionError:
                            return jsonify({"status": "error", "message": "Brak uprawnień do dodawania urządzeń"}), 403
                        except ValueError as exc:
                            return jsonify({"status": "error", "message": str(exc)}), 400
                        except Exception as exc:
                            if self.app:
                                self.app.logger.error(f"Failed to create temperature control '{name}': {exc}")
                            return jsonify({"status": "error", "message": "Nie udało się utworzyć sterownika"}), 500

                    # Legacy single-home fallback
                    if payload:
                        if 'id' not in payload:
                            payload['id'] = str(uuid.uuid4())
                        payload['temperature'] = payload.get('temperature', 22)
                        self.smart_home.temperature_controls.append(payload)
                        if self.socketio:
                            self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                            self.socketio.emit('update_room_temperature_controls', payload)
                        self.smart_home.save_config()
                        return jsonify({"status": "success", "id": payload['id']})
                    return jsonify({"status": "error", "message": "Invalid control data"}), 400
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Exception in POST /api/temperature_controls: {e}\n{traceback.format_exc()}")
                    return jsonify({"status": "error", "message": f"Server error: {e}"}), 500

        @self.app.route('/api/temperature_controls/<id>', methods=['PUT', 'DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.api_admin_required
        def temp_control_by_id(id):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'status': 'error', 'message': 'Nie jesteś zalogowany'}), 401
                
            if request.method == 'PUT':
                print(f"[DEBUG] PUT /api/temperature_controls/{id} - Starting")
                data = request.get_json()
                print(f"[DEBUG] PUT data received: {data}")
                if not data:
                    return jsonify({'status': 'error', 'message': 'Brak danych'}), 400

                # Multi-home branch
                if self.multi_db:
                    device = self.multi_db.get_device(id, str(user_id))
                    print(f"[DEBUG] Current device: {device}")
                    if not device:
                        return jsonify({'status': 'error', 'message': 'Control not found'}), 404

                    updates = {}
                    if 'name' in data and data['name']:
                        updates['name'] = data['name']
                        print(f"[DEBUG] Name update: {data['name']}")
                    
                    if 'display_order' in data:
                        updates['display_order'] = data['display_order']
                        print(f"[DEBUG] Display order update: {data['display_order']}")

                    room_identifier = None
                    if data.get('room_id') not in (None, '', 'null'):
                        room_identifier = data.get('room_id')
                        print(f"[DEBUG] Room ID provided: {room_identifier}")
                    elif 'room' in data and data['room'] not in (None, '', 'null'):
                        room_identifier = data['room']
                        print(f"[DEBUG] Room name provided: {room_identifier}")

                    if room_identifier is not None:
                        print(f"[DEBUG] Processing room change to: {room_identifier}")
                        try:
                            updates['room_id'] = int(room_identifier)
                            print(f"[DEBUG] Using room_id as integer: {updates['room_id']}")
                        except (TypeError, ValueError):
                            resolved_room_id = self._resolve_room_identifier(room_identifier, user_id, device.get('home_id'))
                            print(f"[DEBUG] Resolved room_id: {resolved_room_id}")
                            if resolved_room_id is None:
                                return jsonify({'status': 'error', 'message': 'Nie znaleziono pokoju'}), 404
                            updates['room_id'] = resolved_room_id

                    print(f"[DEBUG] Final updates dict: {updates}")
                    if not updates:
                        return jsonify({'status': 'error', 'message': 'Brak pól do aktualizacji'}), 400

                    try:
                        print(f"[DEBUG] Calling multi_db.update_device with: id={id}, user_id={user_id}, updates={updates}")
                        success = self.multi_db.update_device(id, str(user_id), **updates)
                        print(f"[DEBUG] update_device result: {success}")
                    except PermissionError as e:
                        print(f"[DEBUG] Permission error: {e}")
                        return jsonify({'status': 'error', 'message': 'Brak uprawnień do edycji urządzenia'}), 403
                    except ValueError as exc:
                        print(f"[DEBUG] Value error: {exc}")
                        return jsonify({'status': 'error', 'message': str(exc)}), 400
                    except Exception as exc:
                        print(f"[DEBUG] Unexpected error: {exc}")
                        return jsonify({'status': 'error', 'message': f'Update failed: {exc}'}), 500

                    if not success:
                        print(f"[DEBUG] Update returned False")
                        return jsonify({'status': 'error', 'message': 'Nie udało się zapisać edycji termostatu'}), 500

                    print(f"[DEBUG] Update successful, invalidating cache")
                    if self.cached_data:
                        try:
                            invalidate = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                            if callable(invalidate):
                                invalidate()
                        except Exception:
                            pass

                    updated_device = self.multi_db.get_device(id, str(user_id))
                    print(f"[DEBUG] Updated device: {updated_device}")
                    controls = self.get_current_home_temperature_controls(user_id)
                    print(f"[DEBUG] Emitting {len(controls)} temperature controls via socketio")
                    if self.socketio:
                        self.socketio.emit('update_temperature_controls', controls)

                    response = {
                        'status': 'success',
                        'control': updated_device,
                        'meta': {'home_id': str(updated_device.get('home_id')) if updated_device else None}
                    }
                    print(f"[DEBUG] PUT /api/temperature_controls/{id} - Success response: {response}")
                    return jsonify(response)

                # Legacy single-home fallback  
                device = self.smart_home.get_device_by_id(id)
                print(f"[DEBUG] Device found: {device}")
                if not device:
                    return jsonify({'status': 'error', 'message': 'Control not found'}), 404

                updates = {}
                if 'name' in data:
                    updates['name'] = data['name']
                if 'room' in data:
                    updates['room'] = data['room']
                if 'display_order' in data:
                    updates['display_order'] = data['display_order']

                print(f"[DEBUG] Updates prepared: {updates}")
                if not updates:
                    return jsonify({'status': 'error', 'message': 'No valid fields to update'}), 400

                if hasattr(self.smart_home, 'update_device'):
                    print(f"[DEBUG] Using database mode - calling update_device")
                    success = self.smart_home.update_device(id, updates)
                    print(f"[DEBUG] update_device result: {success}")
                    if not success:
                        return jsonify({"status": "error", "message": "Nie udało się zapisać edycji termostatu"}), 500
                    if self.cached_data:
                        print(f"[DEBUG] Invalidating cache")
                        self.cached_data.invalidate_temperature_cache()
                else:
                    print(f"[DEBUG] Using JSON mode fallback")
                    idx = next((i for i, c in enumerate(self.smart_home.temperature_controls) if str(c.get('id')) == str(id)), None)
                    if idx is None:
                        return jsonify({'status': 'error', 'message': 'Control not found'}), 404
                    
                    if 'name' in updates:
                        self.smart_home.temperature_controls[idx]['name'] = updates['name']
                    if 'room' in updates:
                        self.smart_home.temperature_controls[idx]['room'] = updates['room']
                    if 'display_order' in updates:
                        self.smart_home.temperature_controls[idx]['display_order'] = updates['display_order']
                    
                    self.smart_home.save_config()

                if self.socketio:
                    print(f"[DEBUG] Emitting socket update")
                    fresh_controls = self.cached_data.get_temperature_controls() if self.cached_data else self.smart_home.temperature_controls
                    print(f"[DEBUG] Fresh temperature controls data from cache: {fresh_controls}")
                    self.socketio.emit('update_temperature_controls', fresh_controls)

                print(f"[DEBUG] PUT /api/temperature_controls/{id} - Success (legacy mode)")
                return jsonify({'status': 'success', 'message': 'Termostat zaktualizowany poprawnie!'}), 200
                
            elif request.method == 'DELETE':
                user_id = session.get('user_id')

                if self.multi_db:
                    if not user_id:
                        return jsonify({'status': 'error', 'message': 'Nie jesteś zalogowany'}), 401

                    resolved_home_id = self._resolve_home_id(user_id)
                    user_id_str = str(user_id)
                    device_identifier = normalize_device_id(id)

                    device = None
                    try:
                        lookup_id = device_identifier if device_identifier is not None else id
                        device = self.multi_db.get_device(lookup_id, user_id_str)
                    except Exception as exc:
                        if self.app:
                            self.app.logger.debug(f"Failed to fetch temperature control {id} for delete: {exc}")

                    if not device and resolved_home_id:
                        try:
                            controls = self.multi_db.get_temperature_controls(resolved_home_id, user_id_str)
                            device = next((ctrl for ctrl in controls if str(ctrl.get('id')) == str(id)), None)
                            if device and device_identifier is None:
                                device_identifier = normalize_device_id(device.get('id'))
                        except Exception as exc:
                            if self.app:
                                self.app.logger.debug(f"Failed to resolve temperature control {id} from home list: {exc}")

                    if not device:
                        return jsonify({'status': 'error', 'message': 'Control not found'}), 404

                    target_device_id = device_identifier if device_identifier is not None else device.get('id')
                    if not self.multi_db.delete_device(target_device_id, user_id_str, resolved_home_id):
                        return jsonify({"status": "error", "message": "Nie udało się usunąć termostatu"}), 500

                    if self.cached_data:
                        invalidate = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                        if callable(invalidate):
                            invalidate()

                    updated_controls = self.get_current_home_temperature_controls(user_id)
                    if self.socketio:
                        self.socketio.emit('update_temperature_controls', updated_controls)

                    if hasattr(self.management_logger, 'log_device_action'):
                        try:
                            username = session.get('username', 'unknown')
                            room_name = device.get('room_name') or device.get('room')
                            self.management_logger.log_device_action(
                                user=username,
                                device_name=device.get('name'),
                                room=room_name,
                                action='delete_temperature_control',
                                new_state=None,
                                ip_address=request.remote_addr or ''
                            )
                        except Exception:
                            pass

                    return jsonify({'status': 'success'})

                # Legacy JSON storage fallback
                device = self.smart_home.get_device_by_id(id)
                if not device:
                    return jsonify({'status': 'error', 'message': 'Control not found'}), 404

                updated_controls = []
                if hasattr(self.smart_home, 'delete_device'):
                    success = self.smart_home.delete_device(id)
                    if not success:
                        return jsonify({"status": "error", "message": "Nie udało się usunąć termostatu"}), 500

                    if self.cached_data:
                        invalidate = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                        if callable(invalidate):
                            invalidate()

                    updated_controls = self.get_current_home_temperature_controls(user_id)
                else:
                    idx = next((i for i, c in enumerate(self.smart_home.temperature_controls) if str(c.get('id')) == str(id)), None)
                    if idx is None:
                        return jsonify({'status': 'error', 'message': 'Control not found'}), 404

                    self.smart_home.temperature_controls.pop(idx)
                    self.smart_home.save_config()
                    updated_controls = list(self.smart_home.temperature_controls)

                if self.socketio:
                    self.socketio.emit('update_temperature_controls', updated_controls)

                return jsonify({'status': 'success'})

        @self.app.route('/api/temperature_controls/<int:index>', methods=['DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def delete_temperature_control(index):
            if 0 <= index < len(self.smart_home.temperature_controls):
                deleted_control = self.smart_home.temperature_controls.pop(index)
                # Emit updates only if socketio is available
                if self.socketio:
                    self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                    self.socketio.emit('remove_room_temperature_control', deleted_control)
                self.smart_home.save_config()
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Control not found"}), 404

        @self.app.route('/api/temperature_controls/<int:index>', methods=['PUT'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def edit_temperature_control(index):
            if 0 <= index < len(self.smart_home.temperature_controls):
                data = request.get_json()
                if not data:
                    return jsonify({"status": "error", "message": "Brak danych"}), 400
                if 'name' in data:
                    self.smart_home.temperature_controls[index]['name'] = data['name']
                if 'room' in data:
                    self.smart_home.temperature_controls[index]['room'] = data['room']
                self.smart_home.save_config()
                # Emit updates only if socketio is available
                if self.socketio:
                    self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Control not found"}), 404

        @self.app.route('/api/temperature_controls/<id>/temperature', methods=['POST'])
        @self.auth_manager.login_required
        def set_temperature_control_value(id):
            """Set temperature control value via REST API"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'status': 'error', 'message': 'User not logged in'}), 401
                user_id_str = str(user_id)

                data = request.get_json() or {}
                temperature = data.get('temperature')

                if temperature is None:
                    return jsonify({'status': 'error', 'message': 'Temperature value is required'}), 400

                try:
                    temperature = float(temperature)
                    if not (16 <= temperature <= 30):
                        return jsonify({'status': 'error', 'message': 'Temperature must be between 16°C and 30°C'}), 400
                except (ValueError, TypeError):
                    return jsonify({'status': 'error', 'message': 'Invalid temperature value'}), 400

                if self.multi_db:
                    device = None
                    device_identifier = normalize_device_id(id)
                    if device_identifier is None:
                        return jsonify({'status': 'error', 'message': 'Invalid temperature control identifier'}), 400
                    try:
                        device = self.multi_db.get_device(device_identifier, user_id_str)
                    except Exception as get_err:
                        print(f"[DEBUG] Error fetching temperature control {id} for user {user_id}: {get_err}")

                    if not device:
                        current_home_id = session.get('current_home_id') or self.multi_db.get_user_current_home(user_id_str)
                        if current_home_id:
                            controls = self.multi_db.get_temperature_controls(str(current_home_id), user_id_str)
                            for ctrl in controls:
                                if str(ctrl.get('id')) == str(id):
                                    device = ctrl
                                    break

                    if not device:
                        return jsonify({'status': 'error', 'message': 'Temperature control not found or access denied'}), 404

                    update_payload = {
                        'temperature': temperature
                    }
                    target_device_id = normalize_device_id(device.get('id', device_identifier))
                    if target_device_id is None:
                        fallback_id = device_identifier if device_identifier is not None else device.get('id')
                        target_device_id = normalize_device_id(fallback_id)
                    if target_device_id is None:
                        return jsonify({'status': 'error', 'message': 'Invalid temperature control identifier'}), 400
                    if not self.multi_db.update_device(target_device_id, user_id_str, **update_payload):
                        return jsonify({'status': 'error', 'message': 'Failed to update temperature state'}), 500

                    updated_device = self.multi_db.get_device(target_device_id, user_id_str) or device
                    room_name = updated_device.get('room_name') or device.get('room') or ''
                    control_payload = {
                        'id': updated_device.get('id'),
                        'name': updated_device.get('name'),
                        'room': room_name,
                        'temperature': updated_device.get('temperature') if updated_device.get('temperature') is not None else temperature,
                        'enabled': updated_device.get('enabled', True)
                    }

                    if self.socketio:
                        self.socketio.emit('update_temperature', {
                            'room': room_name,
                            'name': control_payload['name'],
                            'temperature': control_payload['temperature']
                        })
                        self.socketio.emit('sync_temperature', {
                            'name': control_payload['name'],
                            'temperature': control_payload['temperature']
                        })

                    if hasattr(self.management_logger, 'log_device_action'):
                        user_data = self.smart_home.get_user_data(user_id) if user_id else None
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                            device_name=control_payload['name'],
                            room=room_name,
                            action='set_temperature',
                            new_state=control_payload['temperature'],
                            ip_address=request.environ.get('REMOTE_ADDR', '')
                        )

                    return jsonify({'status': 'success', 'control': control_payload})

                # Fallback to legacy single-home implementation
                control = None
                control_idx = None
                for i, c in enumerate(self.smart_home.temperature_controls):
                    if str(c.get('id')) == str(id):
                        control = c
                        control_idx = i
                        break

                if not control:
                    return jsonify({'status': 'error', 'message': 'Temperature control not found'}), 404

                if hasattr(self.smart_home, 'update_temperature_control_value'):
                    success = self.smart_home.update_temperature_control_value(control['room'], control['name'], temperature)
                    if not success:
                        return jsonify({'status': 'error', 'message': 'Failed to update temperature in database'}), 500
                else:
                    self.smart_home.temperature_controls[control_idx]['temperature'] = temperature
                    if not self.smart_home.save_config():
                        return jsonify({'status': 'error', 'message': 'Failed to save temperature'}), 500

                if hasattr(self.smart_home, 'set_room_temperature'):
                    self.smart_home.set_room_temperature(control['room'], temperature)
                else:
                    self.smart_home.temperature_states[control['room']] = temperature
                    self.smart_home.save_config()

                if self.socketio:
                    self.socketio.emit('update_temperature', {
                        'room': control['room'],
                        'name': control['name'],
                        'temperature': temperature
                    })
                    self.socketio.emit('sync_temperature', {
                        'name': control['name'],
                        'temperature': temperature
                    })

                if hasattr(self.management_logger, 'log_device_action'):
                    user_data = self.smart_home.get_user_data(user_id) if user_id else None
                    self.management_logger.log_device_action(
                        user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                        device_name=control['name'],
                        room=control['room'],
                        action='set_temperature',
                        new_state=temperature,
                        ip_address=request.environ.get('REMOTE_ADDR', '')
                    )

                return jsonify({
                    'status': 'success',
                    'control': {
                        'id': control['id'],
                        'name': control['name'],
                        'room': control['room'],
                        'temperature': temperature
                    }
                })

            except Exception as e:
                print(f"Error in set_temperature_control_value: {e}")
                return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

        @self.app.route('/api/temperature_controls/<id>/toggle', methods=['POST'])
        @self.auth_manager.api_login_required
        def toggle_temperature_control(id):
            """Toggle temperature control state via REST API"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'status': 'error', 'message': 'User not logged in'}), 401
                user_id_str = str(user_id)

                print(f"[DEBUG] Temperature control toggle for ID: {id}")

                if self.multi_db:
                    device = self.multi_db.get_device(id, user_id_str)
                    if not device:
                        return jsonify({'status': 'error', 'message': 'Temperature control not found'}), 404

                    # Toggle enabled state
                    current_enabled = device.get('enabled', True)
                    new_enabled = not current_enabled
                    print(f"[DEBUG] Toggling enabled: {current_enabled} -> {new_enabled}")

                    try:
                        success = self.multi_db.update_device(id, user_id_str, enabled=new_enabled)
                        if not success:
                            return jsonify({'status': 'error', 'message': 'Failed to toggle temperature control'}), 500

                        # Get updated device
                        updated_device = self.multi_db.get_device(id, user_id_str) or device
                        room_name = updated_device.get('room_name') or device.get('room')

                        # Invalidate cache
                        if self.cached_data:
                            try:
                                invalidate = getattr(self.cached_data, 'invalidate_temperature_cache', None)
                                if callable(invalidate):
                                    invalidate()
                            except Exception:
                                pass

                        # Emit updates
                        controls = self.get_current_home_temperature_controls(user_id)
                        if self.socketio:
                            self.socketio.emit('update_temperature_controls', controls)
                            self.socketio.emit('toggle_temperature_control', {
                                'id': updated_device.get('id'),
                                'name': updated_device.get('name'),
                                'room': room_name,
                                'enabled': updated_device.get('enabled')
                            })

                        # Log action
                        if hasattr(self.management_logger, 'log_device_action'):
                            try:
                                username = session.get('username', 'unknown')
                                self.management_logger.log_device_action(
                                    user=username,
                                    device_name=updated_device.get('name'),
                                    room=room_name,
                                    action='toggle_temperature_control',
                                    new_state=new_enabled,
                                    ip_address=request.remote_addr or ''
                                )
                            except Exception:
                                pass

                        return jsonify({
                            'status': 'success',
                            'control': {
                                'id': updated_device.get('id'),
                                'name': updated_device.get('name'),
                                'room': room_name,
                                'enabled': updated_device.get('enabled')
                            }
                        })
                    except PermissionError:
                        return jsonify({'status': 'error', 'message': 'Permission denied'}), 403
                    except Exception as exc:
                        print(f"[DEBUG] Error toggling temperature control: {exc}")
                        return jsonify({'status': 'error', 'message': str(exc)}), 500

                # Legacy fallback
                control = None
                for i, c in enumerate(self.smart_home.temperature_controls):
                    if str(c.get('id')) == str(id):
                        control = c
                        break

                if not control:
                    return jsonify({'status': 'error', 'message': 'Temperature control not found'}), 404

                # Toggle enabled state
                current_enabled = control.get('enabled', True)
                control['enabled'] = not current_enabled
                self.smart_home.save_config()

                if self.socketio:
                    self.socketio.emit('update_temperature_controls', self.smart_home.temperature_controls)

                return jsonify({
                    'status': 'success',
                    'control': {
                        'id': control.get('id'),
                        'name': control.get('name'),
                        'room': control.get('room'),
                        'enabled': control.get('enabled')
                    }
                })

            except Exception as e:
                print(f"[DEBUG] Exception in toggle_temperature_control: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/temperature_controls/<id>/enabled', methods=['POST'])
        @self.auth_manager.login_required
        def toggle_temperature_control_enabled(id):
            """Toggle temperature control enabled/disabled state via REST API"""
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'status': 'error', 'message': 'User not logged in'}), 401
                user_id_str = str(user_id)

                data = request.get_json() or {}
                enabled_value = data.get('enabled')

                if enabled_value is None:
                    return jsonify({'status': 'error', 'message': 'Enabled value is required'}), 400

                if isinstance(enabled_value, str):
                    enabled = enabled_value.strip().lower() in ('true', '1', 'yes', 'on')
                else:
                    enabled = bool(enabled_value)

                if self.multi_db:
                    device = None
                    device_identifier = normalize_device_id(id)
                    if device_identifier is None:
                        return jsonify({'status': 'error', 'message': 'Invalid temperature control identifier'}), 400
                    try:
                        device = self.multi_db.get_device(device_identifier, user_id_str)
                    except Exception as get_err:
                        print(f"[DEBUG] Error fetching temperature control {id} for user {user_id}: {get_err}")

                    if not device:
                        current_home_id = session.get('current_home_id') or self.multi_db.get_user_current_home(user_id_str)
                        if current_home_id:
                            controls = self.multi_db.get_temperature_controls(str(current_home_id), user_id_str)
                            for ctrl in controls:
                                if str(ctrl.get('id')) == str(id):
                                    device = ctrl
                                    break

                    if not device:
                        return jsonify({'status': 'error', 'message': 'Temperature control not found or access denied'}), 404

                    target_device_id = normalize_device_id(device.get('id', device_identifier))
                    if target_device_id is None:
                        fallback_id = device_identifier if device_identifier is not None else device.get('id')
                        target_device_id = normalize_device_id(fallback_id)
                    if target_device_id is None:
                        return jsonify({'status': 'error', 'message': 'Invalid temperature control identifier'}), 400
                    if not self.multi_db.update_device(target_device_id, user_id_str, enabled=enabled):
                        return jsonify({'status': 'error', 'message': 'Failed to update enabled state'}), 500

                    updated_device = self.multi_db.get_device(target_device_id, user_id_str) or device
                    room_name = updated_device.get('room_name') or device.get('room') or ''
                    control_payload = {
                        'id': updated_device.get('id'),
                        'name': updated_device.get('name'),
                        'room': room_name,
                        'enabled': bool(updated_device.get('enabled', enabled))
                    }

                    if self.socketio:
                        self.socketio.emit('update_temperature_control_enabled', {
                            'id': control_payload['id'],
                            'room': room_name,
                            'name': control_payload['name'],
                            'enabled': control_payload['enabled']
                        })

                    if hasattr(self.management_logger, 'log_device_action'):
                        user_data = self.smart_home.get_user_data(user_id) if user_id else None
                        self.management_logger.log_device_action(
                            user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                            device_name=control_payload['name'],
                            room=room_name,
                            action='toggle_temperature_enabled',
                            new_state=control_payload['enabled'],
                            ip_address=request.environ.get('REMOTE_ADDR', '')
                        )

                    return jsonify({'status': 'success', 'control': control_payload})

                # Fallback to legacy single-home implementation
                control = None
                control_idx = None
                for i, c in enumerate(self.smart_home.temperature_controls):
                    if str(c.get('id')) == str(id):
                        control = c
                        control_idx = i
                        break

                if not control:
                    return jsonify({'status': 'error', 'message': 'Temperature control not found'}), 404

                if hasattr(self.smart_home, 'toggle_temperature_control_enabled'):
                    success = self.smart_home.toggle_temperature_control_enabled(control['room'], control['name'], enabled)
                    if not success:
                        return jsonify({'status': 'error', 'message': 'Failed to update enabled state in database'}), 500
                else:
                    self.smart_home.temperature_controls[control_idx]['enabled'] = enabled
                    if not self.smart_home.save_config():
                        return jsonify({'status': 'error', 'message': 'Failed to save enabled state'}), 500

                if self.socketio:
                    self.socketio.emit('update_temperature_control_enabled', {
                        'id': control['id'],
                        'room': control['room'],
                        'name': control['name'],
                        'enabled': enabled
                    })

                if hasattr(self.management_logger, 'log_device_action'):
                    user_data = self.smart_home.get_user_data(user_id) if user_id else None
                    self.management_logger.log_device_action(
                        user=user_data.get('name', 'Unknown') if user_data else session.get('username', 'Unknown'),
                        device_name=control['name'],
                        room=control['room'],
                        action='toggle_temperature_enabled',
                        new_state=enabled,
                        ip_address=request.environ.get('REMOTE_ADDR', '')
                    )

                return jsonify({
                    'status': 'success',
                    'control': {
                        'id': control['id'],
                        'name': control['name'],
                        'room': control['room'],
                        'enabled': enabled
                    }
                })

            except Exception as e:
                print(f"Error in toggle_temperature_control_enabled: {e}")
                return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

        @self.app.route('/<room>')
        @self.auth_manager.login_required
        def dynamic_room(room):
            user_id = session.get('user_id')
            rooms = self.get_current_home_rooms(user_id)
            
            if room.lower() in [r.lower() for r in rooms]:
                # Get buttons and temperature controls for current home
                buttons = self.get_current_home_buttons(user_id)
                temp_controls = self.get_current_home_temperature_controls(user_id)
                
                # Filter by room
                room_buttons = [button for button in buttons if button.get('room') and button['room'].lower() == room.lower()]
                room_temperature_controls = [control for control in temp_controls if control.get('room') and control['room'].lower() == room.lower()]
                user_data = self.smart_home.get_user_data(user_id) if user_id else None
                return render_template('room.html', 
                                      room=room.capitalize(), 
                                      buttons=room_buttons, 
                                      temperature_controls=room_temperature_controls,
                                      user_data=user_data)
            return redirect(url_for('error'))

        @self.app.route('/api/users', methods=['GET'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def get_users():
            users_list = [
                {
                    'user_id': user_id,
                    'username': data['name'],
                    'email': data.get('email', ''),
                    'role': data['role'],
                    'password': '••••••••'  # Always show dots for password
                }
                for user_id, data in self.smart_home.users.items()
            ]
            return jsonify(users_list)

        @self.app.route('/api/users', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def add_user():
            """Add user using the same logic as registration but without email verification"""
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'Brak danych'}), 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            email = data.get('email', '').strip()
            role = data.get('role', 'user')
            
            # Use the same validation logic as registration
            if not username or len(username) < 3:
                return jsonify({'status': 'error', 'message': 'Nazwa użytkownika musi mieć co najmniej 3 znaki.'}), 400
            if not email or '@' not in email:
                return jsonify({'status': 'error', 'message': 'Podaj poprawny adres email.'}), 400
            if not password or len(password) < 6:
                return jsonify({'status': 'error', 'message': 'Hasło musi mieć co najmniej 6 znaków.'}), 400
            if role not in ['user', 'admin']:
                return jsonify({'status': 'error', 'message': 'Nieprawidłowa rola użytkownika.'}), 400
            
            # Check if user already exists (same as registration)
            for user in self.smart_home.users.values():
                if user.get('name') == username:
                    return jsonify({'status': 'error', 'message': 'Użytkownik już istnieje.'}), 400
                if user.get('email') == email:
                    return jsonify({'status': 'error', 'message': 'Adres email jest już używany.'}), 400
            
            # Dodawanie użytkownika - obsługa trybu DB i plikowego
            try:
                if hasattr(self.smart_home, 'add_user'):
                    # Tryb DB
                    user_id = self.smart_home.add_user(username, password, role, email)
                else:
                    # Tryb plikowy (legacy)
                    import uuid
                    from werkzeug.security import generate_password_hash
                    user_id = str(uuid.uuid4())
                    self.smart_home.users[user_id] = {
                        'name': username,
                        'password': generate_password_hash(password),
                        'role': role,
                        'email': email,
                        'profile_picture': ''
                    }
                    self.smart_home.save_config()
                # Log admin user creation
                self.management_logger.log_user_change(
                    username=session.get('username', 'unknown'),
                    action='add',
                    target_user=username,
                    ip_address=request.remote_addr or "",
                    details={'email': email, 'role': role}
                )
                return jsonify({
                    'status': 'success', 
                    'message': 'Użytkownik został dodany pomyślnie!',
                    'user_id': user_id,
                    'username': username
                }), 200
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Błąd podczas dodawania użytkownika: {e}'}), 500

        @self.app.route('/api/users/<user_id>', methods=['PUT'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def update_user(user_id):
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Brak danych"}), 400
            
            user = self.smart_home.users.get(user_id)
            if not user:
                return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 404
            
            updates = {}
            if 'username' in data:
                # Sprawdź czy nowa nazwa użytkownika nie jest już zajęta
                for uid, u in self.smart_home.users.items():
                    if uid != user_id and u.get('name') == data['username']:
                        return jsonify({"status": "error", "message": "Nazwa użytkownika jest już zajęta"}), 400
                updates['name'] = data['username']
            
            if 'email' in data:
                updates['email'] = data['email']
            
            if 'role' in data and data['role'] in ['user', 'admin']:
                updates['role'] = data['role']
            
            # Aktualizuj dane użytkownika
            for key, value in updates.items():
                user[key] = value
            
            self.smart_home.save_config()
            return jsonify({"status": "success", "message": "Użytkownik zaktualizowany"})

        @self.app.route('/api/users/<user_id>', methods=['DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def delete_user_api(user_id):
            try:
                # Try DB mode first
                if hasattr(self.smart_home, 'delete_user'):
                    result = self.smart_home.delete_user(user_id)
                    # Obsłuż różne typy zwracane przez delete_user
                    if isinstance(result, tuple):
                        success, message = result
                    elif isinstance(result, bool):
                        success, message = result, ''
                    elif result is None:
                        success, message = True, ''
                    else:
                        success, message = False, str(result)
                    if not success:
                        print(f"[ERROR] delete_user zwróciło błąd: {message}")
                        return jsonify({'status': 'error', 'message': message or 'Błąd usuwania użytkownika'}), 400
                else:
                    # Legacy file mode
                    if user_id not in self.smart_home.users:
                        return jsonify({'status': 'error', 'message': 'Użytkownik nie istnieje'}), 404
                    del self.smart_home.users[user_id]
                    self.smart_home.save_config()
                # Optionally log the deletion
                try:
                    self.management_logger.log_user_change(
                        username=session.get('username', 'unknown'),
                        action='delete',
                        target_user=user_id,
                        ip_address=request.remote_addr or "",
                        details={}
                    )
                except Exception as log_exc:
                    print(f"[WARN] Błąd logowania usunięcia użytkownika: {log_exc}")
                return jsonify({'status': 'success', 'message': 'Użytkownik został usunięty'})
            except Exception as e:
                import traceback
                print(f"[ERROR] Błąd podczas usuwania użytkownika: {e}\n{traceback.format_exc()}")
                return jsonify({'status': 'error', 'message': f'Błąd podczas usuwania użytkownika: {e}'}), 500

        @self.app.route('/api/users/<user_id>', methods=['POST'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def update_user_post(user_id):
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Brak danych"}), 400
            user = self.smart_home.users.get(user_id)
            if not user:
                return jsonify({"status": "error", "message": "Użytkownik nie istnieje"}), 404
            updates = {}
            if 'username' in data:
                # Sprawdź czy nowa nazwa użytkownika nie jest już zajęta
                for uid, u in self.smart_home.users.items():
                    if uid != user_id and u.get('name') == data['username']:
                        return jsonify({"status": "error", "message": "Nazwa użytkownika jest już zajęta"}), 400
                updates['name'] = data['username']
            if 'email' in data:
                updates['email'] = data['email']
            if 'role' in data and data['role'] in ['user', 'admin']:
                updates['role'] = data['role']
            # Aktualizuj dane użytkownika
            for key, value in updates.items():
                user[key] = value
            self.smart_home.save_config()
            return jsonify({"status": "success", "message": "Użytkownik zaktualizowany (POST)"})

        @self.app.route('/api/users/<user_id>/password', methods=['PUT'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def change_password(user_id):
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Brak danych"}), 400
            new_password = data.get('new_password')
            if not new_password:
                return jsonify({"status": "error", "message": "Brak nowego hasła"}), 400
            success, message = self.smart_home.change_password(user_id, new_password)
            if success:
                return jsonify({"status": "success", "message": message})
            return jsonify({"status": "error", "message": message}), 400

        @self.app.route('/api/automations', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_automations():
            self.smart_home.check_and_save()
            user_id = session.get('user_id')
            preferred_home_id = request.args.get('home_id')

            if request.method == 'GET':
                if self.multi_db and user_id:
                    try:
                        automations, _ = self.get_current_home_automations(user_id, preferred_home_id)
                        return jsonify(automations)
                    except PermissionError:
                        return jsonify({"status": "error", "message": "Brak dostępu do wybranego domu"}), 403
                # Legacy/global mode
                return jsonify(self.smart_home.automations)

            if session.get('role') != 'admin':
                return jsonify({"status": "error", "message": "Brak uprawnień"}), 403

            new_automation = request.get_json(silent=True) or {}
            required_fields = ['name', 'trigger', 'actions', 'enabled']
            if not all(field in new_automation for field in required_fields):
                return jsonify({"status": "error", "message": "Brak wymaganych pól"}), 400

            if self.multi_db and user_id:
                home_hint = new_automation.get('home_id') or preferred_home_id
                home_id = self._resolve_home_id(user_id, home_hint)
                if not home_id:
                    return jsonify({"status": "error", "message": "Nie wybrano domu"}), 400
                try:
                    automations, _ = self.get_current_home_automations(user_id, home_id)
                except PermissionError:
                    return jsonify({"status": "error", "message": "Brak dostępu do wybranego domu"}), 403

                if any(auto.get('name', '').lower() == new_automation['name'].lower() for auto in automations):
                    return jsonify({"status": "error", "message": "Automatyzacja o tej nazwie już istnieje"}), 400

                try:
                    created = self.multi_db.add_home_automation(home_id, str(user_id), new_automation)
                    automations = self.multi_db.get_home_automations(home_id, str(user_id))
                except ValueError as exc:
                    return jsonify({"status": "error", "message": str(exc)}), 400
                except PermissionError:
                    return jsonify({"status": "error", "message": "Brak dostępu do wybranego domu"}), 403

                self._emit_automation_update(home_id, automations)

                self.management_logger.log_automation_change(
                    username=session.get('username', 'unknown'),
                    action='add',
                    automation_name=new_automation['name'],
                    ip_address=request.remote_addr or ""
                )
                return jsonify({"status": "success", "automations": automations, "home_id": home_id, "created": created})

            try:
                from app_db import DATABASE_MODE
            except ImportError:
                DATABASE_MODE = False

            if DATABASE_MODE:
                self.smart_home.add_automation(
                    name=new_automation['name'],
                    trigger=new_automation['trigger'],
                    actions=new_automation['actions'],
                    enabled=new_automation['enabled']
                )
                automations = self.smart_home.automations
            else:
                self.smart_home.automations.append(new_automation)
                self.smart_home.save_config()
                automations = self.smart_home.automations

            self._emit_automation_update(None, automations)
            self.management_logger.log_automation_change(
                username=session.get('username', 'unknown'),
                action='add',
                automation_name=new_automation['name'],
                ip_address=request.remote_addr or ""
            )
            return jsonify({"status": "success", "automations": automations})

        @self.app.route('/api/automations/<int:index>', methods=['PUT', 'DELETE'])
        @self.auth_manager.login_required
        @self.auth_manager.admin_required
        def modify_automation(index):
            try:
                from app_db import DATABASE_MODE
            except ImportError:
                DATABASE_MODE = False

            user_id = session.get('user_id')
            if request.method == 'PUT':
                updated_automation = request.get_json(silent=True) or {}

                if self.multi_db and user_id:
                    home_hint = updated_automation.get('home_id') or request.args.get('home_id')
                    home_id = self._resolve_home_id(user_id, home_hint)
                    if not home_id:
                        return jsonify({"status": "error", "message": "Nie wybrano domu"}), 400
                    try:
                        automations, _ = self.get_current_home_automations(user_id, home_id)
                    except PermissionError:
                        return jsonify({"status": "error", "message": "Brak dostępu do wybranego domu"}), 403

                    if not (0 <= index < len(automations)):
                        return jsonify({"status": "error", "message": "Automation not found"}), 404

                    if 'name' in updated_automation:
                        proposed = updated_automation['name'].lower()
                        if any(i != index and auto.get('name', '').lower() == proposed for i, auto in enumerate(automations)):
                            return jsonify({"status": "error", "message": "Automatyzacja o tej nazwie już istnieje"}), 400

                    target = automations[index]
                    try:
                        self.multi_db.update_home_automation(home_id, str(user_id), target.get('id'), updated_automation)
                        automations = self.multi_db.get_home_automations(home_id, str(user_id))
                    except ValueError as exc:
                        return jsonify({"status": "error", "message": str(exc)}), 400
                    except PermissionError:
                        return jsonify({"status": "error", "message": "Brak dostępu do wybranego domu"}), 403

                    self._emit_automation_update(home_id, automations)
                    self.management_logger.log_automation_change(
                        username=session.get('username', 'unknown'),
                        action='edit',
                        automation_name=updated_automation.get('name', target.get('name', 'unknown')),
                        ip_address=request.remote_addr or ""
                    )
                    return jsonify({"status": "success"})

                if 0 <= index < len(self.smart_home.automations):
                    if updated_automation:
                        name_exists = any(
                            i != index and auto['name'].lower() == updated_automation['name'].lower()
                            for i, auto in enumerate(self.smart_home.automations)
                        )
                        if name_exists:
                            return jsonify({"status": "error", "message": "Automatyzacja o tej nazwie już istnieje"}), 400
                        if DATABASE_MODE:
                            self.smart_home.update_automation_by_index(index, updated_automation)
                        else:
                            self.smart_home.automations[index] = updated_automation
                            self.smart_home.save_config()
                        self._emit_automation_update(None, self.smart_home.automations)
                        self.management_logger.log_automation_change(
                            username=session.get('username', 'unknown'),
                            action='edit',
                            automation_name=updated_automation['name'],
                            ip_address=request.remote_addr or ""
                        )
                        return jsonify({"status": "success"})
                    return jsonify({"status": "error", "message": "Invalid data"}), 400
                return jsonify({"status": "error", "message": "Automation not found"}), 404

            # DELETE method
            if self.multi_db and user_id:
                home_id = self._resolve_home_id(user_id, request.args.get('home_id'))
                if not home_id:
                    return jsonify({"status": "error", "message": "Nie wybrano domu"}), 400
                try:
                    automations, _ = self.get_current_home_automations(user_id, home_id)
                except PermissionError:
                    return jsonify({"status": "error", "message": "Brak dostępu do wybranego domu"}), 403

                if not (0 <= index < len(automations)):
                    return jsonify({"status": "error", "message": "Automation not found"}), 404

                target = automations[index]
                automation_name = target.get('name', 'unknown')
                try:
                    self.multi_db.delete_home_automation(home_id, str(user_id), target.get('id'))
                    automations = self.multi_db.get_home_automations(home_id, str(user_id))
                except PermissionError:
                    return jsonify({"status": "error", "message": "Brak dostępu do wybranego domu"}), 403

                self._emit_automation_update(home_id, automations)
                self.management_logger.log_automation_change(
                    username=session.get('username', 'unknown'),
                    action='delete',
                    automation_name=automation_name,
                    ip_address=request.remote_addr or ""
                )
                return jsonify({"status": "success"})

            if 0 <= index < len(self.smart_home.automations):
                automation_name = self.smart_home.automations[index].get('name', 'unknown')
                if DATABASE_MODE:
                    self.smart_home.delete_automation_by_index(index)
                else:
                    del self.smart_home.automations[index]
                    self.smart_home.save_config()
                self._emit_automation_update(None, self.smart_home.automations)
                self.management_logger.log_automation_change(
                    username=session.get('username', 'unknown'),
                    action='delete',
                    automation_name=automation_name,
                    ip_address=request.remote_addr or ""
                )
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Automation not found"}), 404

        @self.app.route('/api/security', methods=['GET', 'POST'])
        @self.auth_manager.login_required
        def manage_security_state():
            """REST API endpoint for security state management"""
            try:
                if request.method == 'GET':
                    # Get current security state
                    user_id = session.get('user_id')
                    home_id = request.args.get('home_id')
                    current_state = self.smart_home.security_state

                    if self.multi_db and user_id:
                        try:
                            if not home_id:
                                home_id = session.get('current_home_id') or self.multi_db.get_user_current_home(user_id)
                            if home_id:
                                current_state = self.multi_db.get_security_state(str(home_id), str(user_id))
                        except PermissionError:
                            return jsonify({
                                "status": "error",
                                "message": "Brak dostępu do wybranego domu"
                            }), 403
                        except Exception as err:
                            self.app.logger.error(f"Failed to fetch security state for home {home_id}: {err}")

                    return jsonify({
                        "status": "success",
                        "security_state": current_state,
                        "home_id": str(home_id) if home_id else None
                    })
                
                elif request.method == 'POST':
                    # Set security state
                    data = request.get_json()
                    if not data:
                        return jsonify({"status": "error", "message": "Brak danych"}), 400
                    
                    new_state = data.get('state')
                    if new_state not in ["Załączony", "Wyłączony"]:
                        return jsonify({
                            "status": "error", 
                            "message": "Nieprawidłowy stan zabezpieczeń. Dopuszczalne wartości: 'Załączony', 'Wyłączony'"
                        }), 400
                    
                    user_id = session.get('user_id')
                    home_id = data.get('home_id') if isinstance(data, dict) else None
                    success = False

                    if self.multi_db and user_id:
                        try:
                            if not home_id:
                                home_id = session.get('current_home_id') or self.multi_db.get_user_current_home(user_id)
                            if not home_id:
                                return jsonify({
                                    "status": "error",
                                    "message": "Brak wybranego domu"
                                }), 400

                            success = self.multi_db.set_security_state(str(home_id), str(user_id), new_state, {
                                'source': 'api',
                                'timestamp': datetime.utcnow().isoformat()
                            })

                            if not success:
                                return jsonify({
                                    "status": "error",
                                    "message": "Brak uprawnień do zmiany stanu zabezpieczeń"
                                }), 403

                            if success and self.socketio:
                                self.socketio.emit('update_security_state', {
                                    'state': new_state,
                                    'home_id': str(home_id)
                                })
                        except PermissionError:
                            return jsonify({
                                "status": "error",
                                "message": "Brak uprawnień do zmiany stanu zabezpieczeń"
                            }), 403
                        except Exception as err:
                            self.app.logger.error(f"Failed to set security state for home {home_id}: {err}")
                            return jsonify({
                                "status": "error",
                                "message": "Nie udało się zaktualizować stanu zabezpieczeń"
                            }), 500
                    else:
                        # Update security state using legacy property (single-home mode)
                        self.smart_home.security_state = new_state

                        try:
                            from app_db import DATABASE_MODE
                        except ImportError:
                            DATABASE_MODE = False

                        if DATABASE_MODE:
                            success = True
                        else:
                            success = self.smart_home.save_config()
                        home_id = None
                    
                    if success:
                        # Log the action
                        user_id = session.get('user_id')
                        if user_id:
                            user_data = self.smart_home.get_user_data(user_id)
                            self.management_logger.log_device_action(
                                user=user_data.get('name', 'Unknown'),
                                device_name='Security System',
                                room='System',
                                action='set_security_state',
                                new_state={'state': new_state, 'home_id': str(home_id) if home_id else None},
                                ip_address=request.environ.get('REMOTE_ADDR', '')
                            )
                        
                        return jsonify({
                            "status": "success",
                            "message": f"Stan zabezpieczeń zaktualizowany na: {new_state}",
                            "security_state": new_state,
                            "home_id": str(home_id) if home_id else None
                        })
                    else:
                        return jsonify({
                            "status": "error", 
                            "message": "Nie udało się zapisać stanu zabezpieczeń"
                        }), 500
                        
            except Exception as e:
                self.app.logger.error(f"Error in security API: {e}")
                return jsonify({
                    "status": "error", 
                    "message": f"Błąd podczas operacji na zabezpieczeniach: {str(e)}"
                }), 500


class SocketManager:
    """Klasa zarządzająca obsługą WebSocket"""
    def __init__(self, socketio, smart_home, management_logger=None, multi_db=None):
        self.socketio = socketio
        self.smart_home = smart_home
        self.management_logger = management_logger or ManagementLogger()
        self.multi_db = multi_db
        self.register_handlers()

    def register_handlers(self):
        @self.socketio.on('connect')
        def handle_connect():
            if 'username' not in session:
                print("Brak autentykacji - odrzucenie połączenia")
                return False
            print(f"Użytkownik {session['username']} połączony przez WebSocket")
            self.socketio.emit('update_automations', self.smart_home.automations)

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f'Klient {getattr(request, "sid", "?")} rozłączony. Powód: {getattr(getattr(request, "args", None), "get", lambda x: None)("error")}')

        @self.socketio.on('set_security_state')
        def handle_set_security_state(data):
            print(f"[DEBUG] set_security_state called with data: {data}")
            print(f"[DEBUG] Session contents: {dict(session)}")
            
            # Check both username and user_id for compatibility
            if 'username' not in session and 'user_id' not in session:
                print("[DEBUG] No authentication found in session")
                return
                
            new_state = data.get('state')
            print(f"[DEBUG] Requested new state: {new_state}")
            
            if new_state in ["Załączony", "Wyłączony"]:
                try:
                    user_id = session.get('user_id') or session.get('username')
                    home_id = data.get('home_id') if isinstance(data, dict) else None
                    success = False

                    if self.multi_db and user_id:
                        try:
                            if not home_id:
                                home_id = session.get('current_home_id') or self.multi_db.get_user_current_home(str(user_id))
                            if not home_id:
                                emit('error', {'message': 'Brak wybranego domu'})
                                return
                            success = self.multi_db.set_security_state(str(home_id), str(user_id), new_state, {
                                'source': 'socket_legacy',
                                'timestamp': datetime.utcnow().isoformat()
                            })
                            if not success:
                                emit('error', {'message': 'Brak uprawnień do zmiany stanu zabezpieczeń'})
                                return
                            payload = {'state': new_state, 'home_id': str(home_id)}
                            current_state = new_state
                        except PermissionError:
                            emit('error', {'message': 'Brak dostępu do wybranego domu'})
                            return
                    else:
                        print(f"[DEBUG] Setting security state to: {new_state}")
                        self.smart_home.security_state = new_state
                        current_state = self.smart_home.security_state
                        payload = {'state': current_state, 'home_id': None}
                        
                        print(f"[DEBUG] State after setting: {current_state}")
                        
                        print(f"[DEBUG] Emitting update_security_state with: {current_state}")
                        self.socketio.emit('update_security_state', payload)
                        
                        # In database mode, saving is automatic through the property setter
                        try:
                            from app_db import DATABASE_MODE
                        except ImportError:
                            DATABASE_MODE = False
                        if not DATABASE_MODE:
                            self.smart_home.save_config()
                        return

                    self.socketio.emit('update_security_state', payload)
                except Exception as e:
                    print(f"[ERROR] Error setting security state: {e}")
            else:
                print(f"[DEBUG] Invalid state requested: {new_state}")

        @self.socketio.on('get_security_state')
        def handle_get_security_state(data=None):
            print(f"[DEBUG] get_security_state called")
            print(f"[DEBUG] Session contents: {dict(session)}")
            
            if 'username' in session or 'user_id' in session:
                user_id = session.get('user_id') or session.get('username')
                requested_home = data.get('home_id') if isinstance(data, dict) else None
                home_id = requested_home or (session.get('current_home_id') if self.multi_db else None)
                current_state = self.smart_home.security_state

                if self.multi_db and user_id:
                    try:
                        if not home_id:
                            home_id = self.multi_db.get_user_current_home(str(user_id))
                        if home_id:
                            current_state = self.multi_db.get_security_state(str(home_id), str(user_id))
                    except Exception as err:
                        print(f"[DEBUG] Failed to fetch multi-home security state: {err}")

                print(f"[DEBUG] Emitting current state: {current_state} (home: {home_id})")
                self.socketio.emit('update_security_state', {'state': current_state, 'home_id': str(home_id) if home_id else None})
            else:
                print("[DEBUG] No authentication found for get_security_state")

        @self.socketio.on('toggle_button')
        def handle_toggle_button(data):
            if 'username' not in session:
                return
            button_name = data.get('name')
            room = data.get('room')
            state = data.get('state')
            if button_name and room and isinstance(state, bool):
                button = next((b for b in self.smart_home.buttons if b['name'] == button_name and b['room'].lower() == room.lower()), None)
                if button:
                    button['state'] = state
                    self.socketio.emit('update_button', {'room': room, 'name': button_name, 'state': state})
                    self.socketio.emit('sync_button_states', {f"{b['room']}_{b['name']}": b['state'] for b in self.smart_home.buttons})
                    
                    # Log button state change
                    from flask import request
                    log_btn = getattr(self.management_logger, 'log_button_change', None)
                    if callable(log_btn):
                        log_btn(
                        username=session.get('username', 'unknown'),
                        room=room,
                        button_name=button_name,
                        new_state=state,
                        ip_address=getattr(request, 'remote_addr', 'unknown')
                    )
                    
                    # Zapisz konfigurację z obsługą błędów
                    if not self.smart_home.save_config():
                        print(f"[ERROR] Nie udało się zapisać stanu przycisku {room}_{button_name}")
                        # Wyślij powiadomienie o błędzie do klienta
                        self.socketio.emit('error_message', {
                            'message': f'Nie udało się zapisać stanu przycisku {button_name}',
                            'type': 'warning'
                        })
                    else:
                        print(f"[AUTOMATION] Wywołanie check_device_triggers dla {room}_{button_name} => {state}")
                        # check_device_triggers function is not available, skipping automation trigger
                        try:
                            # Check if automation system exists and trigger automations if available
                            if hasattr(self.smart_home, 'automations'):
                                print(f"[AUTOMATION] Checking automations for device {room}_{button_name}")
                            else:
                                print(f"[AUTOMATION] Automation system not available")
                        except Exception as e:
                            print(f"[ERROR] Błąd w automation check: {e}")
                else:
                    print(f"[ERROR] Nie znaleziono przycisku {button_name} w pokoju {room}")
                    self.socketio.emit('error_message', {
                        'message': f'Nie znaleziono przycisku {button_name}',
                        'type': 'error'
                    })

        @self.socketio.on('get_button_states')
        def handle_get_button_states():
            if 'username' in session:
                self.socketio.emit('sync_button_states', {f"{button['room']}_{button['name']}": button['state'] for button in self.smart_home.buttons})

        @self.socketio.on('set_temperature')
        def handle_set_temperature(data):
            if 'username' not in session:
                return
            control_name = data.get('name')
            temperature = data.get('temperature')
            if control_name and isinstance(temperature, int) and 16 <= temperature <= 30:
                control = next((control for control in self.smart_home.temperature_controls if control['name'] == control_name), None)
                if control:
                    control['temperature'] = temperature
                    self.socketio.emit('sync_temperature', {'name': control_name, 'temperature': temperature})
                    self.smart_home.save_config()

        @self.socketio.on('get_temperatures')
        def handle_get_temperatures():
            if 'username' in session:
                self.socketio.emit('sync_temperature', self.smart_home.temperature_states)

        @self.socketio.on('get_room_temperature_controls')
        def handle_get_room_temperature_controls(room):
            if 'username' in session:
                room_controls = [control for control in self.smart_home.temperature_controls if control.get('room') and control['room'].lower() == room.lower()]
                self.socketio.emit('update_room_temperature_controls', room_controls)

        @self.socketio.on('save_config')
        def handle_save_config():
            self.smart_home.save_config()