"""
Database Management Logger for SmartHome System
Handles persistent logging of management events using PostgreSQL database
This replaces the JSON-based logging system with database storage.
Supports multi-home logging by using MultiHomeDBManager when available.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import uuid
import os
from utils.smart_home_db_manager import SmartHomeDatabaseManager, DatabaseError


class DatabaseManagementLogger:
    """Database-backed logging system for admin dashboard events"""
    
    def __init__(self, max_logs: int = 1000, max_days: int = 7, multi_db=None):
        """
        Initialize database logger
        
        Args:
            max_logs: Maximum number of logs to keep (for compatibility)
            max_days: Maximum days to keep logs (for auto-cleanup)
            multi_db: Optional MultiHomeDBManager for multi-home support
        """
        self.max_logs = max_logs
        self.max_days = max_days
        self.multi_db = multi_db
        self._lock = threading.RLock()
        
        # Initialize database manager (fallback for single-home mode)
        try:
            self.db = SmartHomeDatabaseManager()
        except DatabaseError as e:
            print(f"Failed to initialize database for logging: {e}")
            raise
    
    def log_event(self, level: str, message: str, event_type: str = 'general', 
                  user: Optional[str] = None, ip_address: Optional[str] = None, 
                  details: Optional[Dict] = None, home_id: Optional[str] = None):
        """
        Log a management event to database
        
        Args:
            level: 'info', 'warning', 'error'
            message: Human readable message
            event_type: Type of event (login, logout, room_change, etc.)
            user: Username associated with the event
            ip_address: IP address associated with the event
            details: Additional event details
            home_id: Optional home ID for multi-home logging
        """
        with self._lock:
            try:
                # Get user_id if user is provided
                user_id = None
                if user:
                    if self.multi_db:
                        user_data = self.multi_db.find_user_by_email_or_username(user)
                        if user_data:
                            user_id = user_data.get('id')
                    else:
                        user_data = self.db.get_user_by_login(user)
                        if user_data and len(user_data) >= 2 and user_data[0] and user_data[1]:
                            user_id = user_data[0]
                
                # Use multi-home logging if home_id is provided and multi_db is available
                if home_id and self.multi_db:
                    self.multi_db.add_home_management_log(
                        home_id=home_id,
                        level=level,
                        message=message,
                        event_type=event_type,
                        user_id=user_id,
                        username=user or "",
                        ip_address=ip_address or "",
                        details=details or {}
                    )
                else:
                    # Fallback to single-home logging
                    self.db.add_management_log(
                        level=level,
                        message=message,
                        event_type=event_type,
                        user_id=user_id,
                        username=user or "",
                        ip_address=ip_address or "",
                        details=details or {}
                    )
                
                # Auto-cleanup old logs if enabled
                self._auto_cleanup_old_logs()
                
            except Exception as e:
                print(f"Failed to log event: {e}")
                import traceback
                traceback.print_exc()
                # Don't raise exception to avoid breaking the main application
    
    def _auto_cleanup_old_logs(self):
        """Remove logs older than max_days"""
        try:
            if self.max_days > 0:
                # Use the database method to delete old logs
                cutoff_date = datetime.now() - timedelta(days=self.max_days)
                # We can implement this cleanup in the database manager if needed
                # For now, we'll skip auto-cleanup to avoid complexity
                pass
        except Exception as e:
            print(f"Failed to cleanup old logs: {e}")
    
    def get_logs(self, limit: Optional[int] = None, 
                 level_filter: Optional[str] = None,
                 event_type_filter: Optional[str] = None) -> List[Dict]:
        """
        Retrieve logs with optional filtering
        
        Args:
            limit: Maximum number of logs to return
            level_filter: Filter by log level
            event_type_filter: Filter by event type
        """
        with self._lock:
            try:
                # Use database method with filters
                logs = self.db.get_management_logs(
                    limit=limit or 100,
                    level=level_filter,
                    event_type=event_type_filter
                )
                
                # Convert database format to match JSON format for compatibility
                converted_logs = []
                for log in logs:
                    # Handle timestamp conversion
                    timestamp_str = ''
                    if log.get('timestamp'):
                        if hasattr(log['timestamp'], 'strftime'):
                            timestamp_str = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            timestamp_str = str(log['timestamp'])
                    
                    converted_log = {
                        'timestamp': timestamp_str,
                        'level': log.get('level', ''),
                        'message': log.get('message', ''),
                        'event_type': log.get('event_type', ''),
                        'user': log.get('username', ''),
                        'ip_address': str(log.get('ip_address', '')),
                        'details': log.get('details', {})
                    }
                    converted_logs.append(converted_log)
                
                return converted_logs
                
            except Exception as e:
                print(f"Failed to get logs: {e}")
                return []
    
    def clear_logs(self):
        """Clear all logs"""
        with self._lock:
            try:
                self.db.clear_management_logs()
            except Exception as e:
                print(f"Failed to clear logs: {e}")
    
    def delete_logs_by_date_range(self, start_date: str = "", end_date: str = "") -> int:
        """
        Delete logs within a specific date range
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format (inclusive)
            end_date: End date in 'YYYY-MM-DD' format (inclusive)
            
        Returns:
            Number of logs deleted
        """
        with self._lock:
            try:
                # For now, we'll implement a simple approach
                # Get current logs count
                current_logs = self.db.get_management_logs(limit=10000)
                original_count = len(current_logs)
                
                # Parse date parameters
                start_dt = None
                end_dt = None
                
                if start_date:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    except ValueError:
                        raise ValueError("start_date must be in YYYY-MM-DD format")
                
                if end_date:
                    try:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date
                    except ValueError:
                        raise ValueError("end_date must be in YYYY-MM-DD format")
                
                # This is a simplified implementation
                # In a production system, you would want to implement direct SQL DELETE with date conditions
                # For now, return 0 to indicate the operation was received but not fully implemented
                print(f"Date range deletion requested: {start_date} to {end_date}")
                return 0
                
            except Exception as e:
                print(f"Failed to delete logs by date range: {e}")
                return 0
    
    def delete_logs_older_than(self, days: int) -> int:
        """
        Delete logs older than specified number of days
        
        Args:
            days: Number of days to keep (delete older logs)
            
        Returns:
            Number of logs deleted
        """
        with self._lock:
            try:
                # Get current logs count
                current_logs = self.db.get_management_logs(limit=10000)
                original_count = len(current_logs)
                
                # This is a simplified implementation
                # In a production system, you would want to implement direct SQL DELETE
                # For now, return 0 to indicate the operation was received but not fully implemented
                print(f"Delete logs older than {days} days requested")
                return 0
                
            except Exception as e:
                print(f"Failed to delete old logs: {e}")
                return 0
    
    # Convenience methods for common events (same interface as original ManagementLogger)
    def log_login(self, username: str, ip_address: str, success: bool = True, home_id: Optional[str] = None):
        """Log a login attempt"""
        if success:
            self.log_event('info', f'Użytkownik {username} zalogował się pomyślnie', 
                          'login', username, ip_address, home_id=home_id)
        else:
            self.log_event('warning', f'Nieudana próba logowania dla użytkownika {username}', 
                          'failed_login', username, ip_address, home_id=home_id)
    
    def log_logout(self, username: str, ip_address: str, home_id: Optional[str] = None):
        self.log_event('info', f'Użytkownik {username or ""} wylogował się', 'logout', username or '', ip_address or '', home_id=home_id)
    
    def log_room_change(self, username: str, action: str, room_name: str, 
                       ip_address: str = "", old_name: str = "", home_id: Optional[str] = None):
        """Log a room change"""
        ip_address = ip_address or ""
        if old_name is None:
            old_name = ""
        if action == 'add':
            message = f'Dodano nowy pokój: {room_name}'
        elif action == 'delete':
            message = f'Usunięto pokój: {room_name}'
        elif action == 'rename':
            message = f'Zmieniono nazwę pokoju z {old_name} na {room_name}'
        else:
            message = f'Zmodyfikowano pokój: {room_name}'
        self.log_event('info', message, 'room_change', username, ip_address,
                      {'action': action, 'room': room_name, 'old_name': old_name}, home_id=home_id)
    
    def log_automation_change(self, username: str, action: str, automation_name: str, 
                             ip_address: str = "", home_id: Optional[str] = None):
        """Log an automation change"""
        ip_address = ip_address or ""
        if action == 'add':
            message = f'Dodano nową automatyzację: {automation_name}'
        elif action == 'delete':
            message = f'Usunięto automatyzację: {automation_name}'
        elif action == 'edit':
            message = f'Zmodyfikowano automatyzację: {automation_name}'
        elif action == 'enable':
            message = f'Włączono automatyzację: {automation_name}'
        elif action == 'disable':
            message = f'Wyłączono automatyzację: {automation_name}'
        else:
            message = f'Zmieniono automatyzację: {automation_name}'
        
        self.log_event('info', message, 'automation_change', username, ip_address,
                      {'action': action, 'automation': automation_name}, home_id=home_id)
    
    def log_user_change(self, username: str, action: str, target_user: str, 
                       ip_address: str = "", details: Dict = {}, home_id: Optional[str] = None):
        if details is None:
            details = {}
        """Log a user data change"""
        ip_address = ip_address or ""
        if action == 'register':
            message = f'Nowy użytkownik zarejestrował się: {target_user}'
        elif action == 'add':
            message = f'Administrator {username} dodał użytkownika: {target_user}'
        elif action == 'delete':
            message = f'Administrator {username} usunął użytkownika: {target_user}'
        elif action == 'edit':
            message = f'Użytkownik {target_user} zaktualizował swoje dane'
        elif action == 'password_change':
            message = f'Użytkownik {target_user} zmienił hasło'
        else:
            message = f'Zmieniono dane użytkownika: {target_user}'
        
        self.log_event('info', message, 'user_change', username, ip_address,
                      {**({'action': action, 'target_user': target_user}), **(details or {})}, home_id=home_id)
    
    def log_failed_login_with_ip(self, username: str, ip_address: str, attempt_count: int = 1, home_id: Optional[str] = None):
        """Log failed login with IP tracking"""
        self.log_event('warning', 
                      f'Nieudana próba logowania dla {username} z adresu IP {ip_address} (próba #{attempt_count})', 
                      'failed_login', username, ip_address,
                      {'attempt_count': attempt_count}, home_id=home_id)
    
    def log_device_action(self, user: str, device_name: str, room: str, action: str, new_state, ip_address: Optional[str] = None, home_id: Optional[str] = None):
        """Log device action (button toggle, temperature change, etc.)"""
        details = {
            'device_name': device_name,
            'room': room,
            'action': action,
            'new_state': new_state
        }
        message = f'{user} wykonał akcję "{action}" na urządzeniu "{device_name}" w pokoju "{room}". Nowy stan: {new_state}'
        self.log_event('info', message, 'device_action', user, ip_address or '', details, home_id=home_id)