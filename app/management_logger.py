"""
Management Logger for SmartHome System
Handles persistent logging of management events for admin dashboard
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading


class ManagementLogger:
    """Persistent logging system for admin dashboard events"""
    
    def __init__(self, log_file: str = 'management_logs.json', max_logs: int = 1000, max_days: int = 7):
        self.log_file = log_file
        self.max_logs = max_logs
        self.max_days = max_days  # Maximum days to keep logs
        self._lock = threading.RLock()
        self._ensure_log_file_exists()
    
    def _ensure_log_file_exists(self):
        """Create log file if it doesn't exist"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _load_logs(self) -> List[Dict]:
        """Load logs from file"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object"""
        try:
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Fallback for different timestamp formats
            try:
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                return datetime.now()  # Return current time if parsing fails
    
    def _auto_cleanup_old_logs(self):
        """Remove logs older than max_days"""
        logs = self._load_logs()
        if not logs:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.max_days)
        
        # Filter out old logs
        filtered_logs = []
        for log in logs:
            log_date = self._parse_timestamp(log.get('timestamp', ''))
            if log_date >= cutoff_date:
                filtered_logs.append(log)
        
    def _save_logs(self, logs: List[Dict]):
        """Save logs to file"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    
    def log_event(self, level: str, message: str, event_type: str = 'general', 
                  user: Optional[str] = None, ip_address: Optional[str] = None, 
                  details: Optional[Dict] = None):
        """
        Log a management event
        
        Args:
            level: 'info', 'warning', 'error'
            message: Human readable message
            event_type: Type of event (login, logout, room_change, etc.)
            user: Username associated with the event
            ip_address: IP address associated with the event
            details: Additional event details
        """
        with self._lock:
            logs = self._load_logs()
            log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': level,
                'message': message,
                'event_type': event_type,
                'user': user or "",
                'ip_address': ip_address or "",
                'details': details if details is not None else {}
            }
            logs.insert(0, log_entry)
            if len(logs) > self.max_logs:
                logs = logs[:self.max_logs]
            
            self._save_logs(logs)
            
            # Auto-cleanup old logs after adding new ones
            self._auto_cleanup_old_logs()
    
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
            logs = self._load_logs()
            
            # Apply filters
            if level_filter:
                logs = [log for log in logs if log.get('level') == level_filter]
            
            if event_type_filter:
                logs = [log for log in logs if log.get('event_type') == event_type_filter]
            
            # Apply limit
            if limit:
                logs = logs[:limit]
            
            return logs
    
    def clear_logs(self):
        """Clear all logs"""
        with self._lock:
            self._save_logs([])
    
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
            logs = self._load_logs()
            original_count = len(logs)
            
            if not logs:
                return 0
            
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
            
            # Filter logs
            filtered_logs = []
            for log in logs:
                log_date = self._parse_timestamp(log.get('timestamp', ''))
                
                # Check if log should be kept
                keep_log = True
                
                if start_dt and log_date < start_dt:
                    keep_log = True  # Before start date, keep
                elif end_dt and log_date >= end_dt:
                    keep_log = True  # After end date, keep
                elif start_dt and end_dt and start_dt <= log_date < end_dt:
                    keep_log = False  # Within range, delete
                elif start_dt and not end_dt and log_date >= start_dt:
                    keep_log = False  # From start date onwards, delete
                elif end_dt and not start_dt and log_date < end_dt:
                    keep_log = False  # Up to end date, delete
                
                if keep_log:
                    filtered_logs.append(log)
            
            # Save filtered logs
            self._save_logs(filtered_logs)
            return original_count - len(filtered_logs)
    
    def delete_logs_older_than(self, days: int) -> int:
        """
        Delete logs older than specified number of days
        
        Args:
            days: Number of days to keep (delete older logs)
            
        Returns:
            Number of logs deleted
        """
        with self._lock:
            logs = self._load_logs()
            original_count = len(logs)
            
            if not logs:
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter out old logs
            filtered_logs = []
            for log in logs:
                log_date = self._parse_timestamp(log.get('timestamp', ''))
                if log_date >= cutoff_date:
                    filtered_logs.append(log)
            
            # Save filtered logs
            self._save_logs(filtered_logs)
            return original_count - len(filtered_logs)
    
    # Convenience methods for common events
    def log_login(self, username: str, ip_address: str, success: bool = True):
        """Log a login attempt"""
        if success:
            self.log_event('info', f'Użytkownik {username} zalogował się pomyślnie', 
                          'login', username, ip_address)
        else:
            self.log_event('warning', f'Nieudana próba logowania dla użytkownika {username}', 
                          'failed_login', username, ip_address)
    
    def log_logout(self, username: str, ip_address: str):
        self.log_event('info', f'Użytkownik {username or ""} wylogował się', 'logout', username or '', ip_address or '')
    
    def log_room_change(self, username: str, action: str, room_name: str, 
                       ip_address: str = "", old_name: str = ""):
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
                      {'action': action, 'room': room_name, 'old_name': old_name})
    
    def log_automation_change(self, username: str, action: str, automation_name: str, 
                             ip_address: str = ""):
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
                      {'action': action, 'automation': automation_name})
    
    def log_user_change(self, username: str, action: str, target_user: str, 
                       ip_address: str = "", details: Dict = {}):
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
                      {**({'action': action, 'target_user': target_user}), **(details or {})})
    
    def log_failed_login_with_ip(self, username: str, ip_address: str, attempt_count: int = 1):
        """Log failed login with IP tracking"""
        self.log_event('warning', 
                      f'Nieudana próba logowania dla {username} z adresu IP {ip_address} (próba #{attempt_count})', 
                      'failed_login', username, ip_address,
                      {'attempt_count': attempt_count})