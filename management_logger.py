"""
Management Logger for SmartHome System
Handles persistent logging of management events for admin dashboard
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import threading


class ManagementLogger:
    """Persistent logging system for admin dashboard events"""
    
    def __init__(self, log_file: str = 'management_logs.json', max_logs: int = 1000):
        self.log_file = log_file
        self.max_logs = max_logs
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
                'user': user,
                'ip_address': ip_address,
                'details': details or {}
            }
            
            # Add to beginning of logs (most recent first)
            logs.insert(0, log_entry)
            
            # Limit log size
            if len(logs) > self.max_logs:
                logs = logs[:self.max_logs]
            
            self._save_logs(logs)
    
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
        """Log a logout"""
        self.log_event('info', f'Użytkownik {username} wylogował się', 
                      'logout', username, ip_address)
    
    def log_button_change(self, username: str, room: str, button_name: str, 
                         new_state: bool, ip_address: str):
        """Log a button state change"""
        state_text = 'włączony' if new_state else 'wyłączony'
        self.log_event('info', f'Przycisk {button_name} w pokoju {room} został {state_text}', 
                      'button_change', username, ip_address, 
                      {'room': room, 'button': button_name, 'state': new_state})
    
    def log_room_change(self, username: str, action: str, room_name: str, 
                       ip_address: str, old_name: str = None):
        """Log a room change"""
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
                             ip_address: str):
        """Log an automation change"""
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
                       ip_address: str, details: Dict = None):
        """Log a user data change"""
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