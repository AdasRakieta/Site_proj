from functools import wraps
import json
import os
from datetime import datetime
from flask import flash, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import uuid


class SmartHomeSystem:
    """Główna klasa systemu SmartHome zarządzająca wszystkimi komponentami"""
    
    def __init__(self, config_file='smart_home_config.json', save_interval=3000):
        self.config_file = config_file
        self.first_config_file = 'smart_home_1st_conf.json'
        self.save_interval = save_interval
        self.last_save_time = datetime.now()
        
        # Domyślna konfiguracja z niezahaszowanymi hasłami
        self.default_config = {
            'users': {
                'admin': {
                    'password': 'admin123',  # Niezahaszowane
                    'role': 'admin'
                },
                'user': {
                    'password': 'user123',   # Niezahaszowane
                    'role': 'user'
                }
            },
            
            'temperature_states': {
                
            },
            'security_state': "Nieznany",
            'rooms': [],
            'buttons': [],
            'temperature_controls': [],
            'automations': []
        }
        
        # Wybór konfiguracji przy starcie
        self.choose_configuration()

    def choose_configuration(self):
        """Pyta użytkownika o wybór konfiguracji przy starcie"""
        print("\n" + "="*50)
        print("Wybierz konfigurację do załadowania:")
        print("1. Użyj pierwszej konfiguracji (smart_home_1st_conf.json)")
        print("2. Użyj ostatniej konfiguracji (smart_home_config.json)")
        print("="*50)
        
        choice = input("Twój wybór (1/2): ").strip()
        if choice == '1':
            self.load_first_config()
        else:
            self.load_config()

    def load_first_config(self):
        """Wczytuje pierwszą konfigurację z niezahaszowanymi hasłami"""
        try:
            if os.path.exists(self.first_config_file):
                with open(self.first_config_file, 'r') as f:
                    config = json.load(f)
                    
                    self.users = config.get('users', self.default_config['users'].copy())
                    self.temperature_states = config.get('temperature_states', self.default_config['temperature_states'].copy())
                    self.security_state = config.get('security_state', self.default_config['security_state'])
                    self.rooms = config.get('rooms', self.default_config['rooms'].copy())
                    self.buttons = config.get('buttons', self.default_config['buttons'].copy())
                    self.temperature_controls = config.get('temperature_controls', self.default_config['temperature_controls'].copy())
                    self.automations = config.get('automations', self.default_config['automations'].copy())
                    
                    # Zahaszuj hasła w pamięci (nie zapisuj do pliku)
                    for username, data in self.users.items():
                        if not data['password'].startswith('pbkdf2:'):
                            data['password'] = generate_password_hash(data['password'])
                    
                    print(f"Załadowano pierwszą konfigurację z {self.first_config_file}")
            else:
                print(f"Plik {self.first_config_file} nie istnieje. Używam domyślnej konfiguracji.")
                self.load_default_config()
                
        except Exception as e:
            print(f"Błąd podczas wczytywania {self.first_config_file}: {str(e)}")
            self.load_default_config()

    def load_config(self):
        """Wczytuje standardową konfigurację"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                    self.users = config.get('users', self.default_config['users'].copy())
                    self.temperature_states = config.get('temperature_states', self.default_config['temperature_states'].copy())
                    self.security_state = config.get('security_state', self.default_config['security_state'])
                    self.rooms = config.get('rooms', self.default_config['rooms'].copy())
                    self.buttons = config.get('buttons', self.default_config['buttons'].copy())
                    self.temperature_controls = config.get('temperature_controls', self.default_config['temperature_controls'].copy())
                    self.automations = config.get('automations', self.default_config['automations'].copy())
                    
                    # MIGRACJA: nadaj brakujące id po wczytaniu
                    for device in self.buttons:
                        if 'id' not in device:
                            device['id'] = str(uuid.uuid4())
                    for device in self.temperature_controls:
                        if 'id' not in device:
                            device['id'] = str(uuid.uuid4())
                    
                    print(f"Załadowano konfigurację z {self.config_file}")
            else:
                print(f"Plik {self.config_file} nie istnieje. Używam domyślnej konfiguracji.")
                self.load_default_config()
                
        except Exception as e:
            print(f"Błąd podczas wczytywania {self.config_file}: {str(e)}")
            self.load_default_config()

    def load_default_config(self):
        """Ładuje domyślną konfigurację z pamięci"""
        self.users = self.default_config['users'].copy()
        self.temperature_states = self.default_config['temperature_states'].copy()
        self.security_state = self.default_config['security_state']
        self.rooms = self.default_config['rooms'].copy()
        self.buttons = self.default_config['buttons'].copy()
        self.temperature_controls = self.default_config['temperature_controls'].copy()
        
        # Zahaszuj hasła w pamięci
        for username, data in self.users.items():
            data['password'] = generate_password_hash(data['password'])
        
        print("Użyto domyślnej konfiguracji")
        self.save_config()

    def save_config(self):
        """Zapisuje aktualną konfigurację do pliku"""
        try:
            # MIGRACJA: nadaj brakujące id przed zapisem
            for device in self.buttons:
                if 'id' not in device:
                    device['id'] = str(uuid.uuid4())
            for device in self.temperature_controls:
                if 'id' not in device:
                    device['id'] = str(uuid.uuid4())
            
            config = {
                'users': {
                    username: {
                        'password': data['password'],
                        'role': data['role'],
                        'name': data.get('name', username),
                        'email': data.get('email', ''),
                        'profile_picture': data.get('profile_picture', '')
                    } for username, data in self.users.items()
                },
                'temperature_states': self.temperature_states,
                'security_state': self.security_state,
                'rooms': self.rooms,
                'buttons': self.buttons,
                'temperature_controls': self.temperature_controls,
                'automations': self.automations
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            self.last_save_time = datetime.now()
            print(f"Zapisano konfigurację do {self.config_file}")
            
        except Exception as e:
            print(f"Błąd podczas zapisywania konfiguracji: {str(e)}")

    def check_and_save(self):
        """Sprawdza czy należy zapisać konfigurację"""
        if (datetime.now() - self.last_save_time).total_seconds() >= self.save_interval:
            self.save_config()

    def fetch_weather_data(self):
        """Pobiera dane pogodowe z API IMGW"""
        url = "https://danepubliczne.imgw.pl/api/data/synop/id/12330"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        return None
    
    def add_user(self, username, password, role='user'):
        """Dodaje nowego użytkownika"""
        if username in self.users:
            return False, "Użytkownik już istnieje"
        if len(username) < 3:
            return False, "Nazwa użytkownika musi mieć co najmniej 3 znaki"
        if len(password) < 6:
            return False, "Hasło musi mieć co najmniej 6 znaków"
        if role not in ['user', 'admin']:
            return False, "Nieprawidłowa rola użytkownika"
        
        self.users[username] = {
            'password': generate_password_hash(password),
            'role': role
        }
        self.save_config()
        return True, "Użytkownik dodany pomyślnie"

    def delete_user(self, username):
        """Usuwa użytkownika"""
        if username not in self.users:
            return False, "Użytkownik nie istnieje"
        if username == 'admin':
            return False, "Nie można usunąć głównego administratora"
        
        del self.users[username]
        self.save_config()
        return True, "Użytkownik usunięty pomyślnie"

    def change_password(self, username, new_password):
        """Zmienia hasło użytkownika"""
        if username not in self.users:
            return False, "Użytkownik nie istnieje"
        if len(new_password) < 6:
            return False, "Hasło musi mieć co najmniej 6 znaków"
        
        self.users[username]['password'] = generate_password_hash(new_password)
        self.save_config()
        return True, "Hasło zmienione pomyślnie"

    def get_user_data(self, username):
        """Pobiera dane użytkownika (bez hasła)"""
        user = self.users.get(username, {})
        return {
            'username': username,
            'name': user.get('name', username),
            'email': user.get('email', ''),
            'profile_picture': user.get('profile_picture', ''),
            'role': user.get('role', 'user')
        }

    def verify_password(self, username, password):
        """Weryfikuje hasło użytkownika"""
        user = self.users.get(username)
        if user and check_password_hash(user['password'], password):
            return True
        return False

    def update_user_profile(self, username, updates):
        """Aktualizuje profil użytkownika"""
        if username not in self.users:
            return False, "Użytkownik nie istnieje"

        user = self.users[username]
        
        # Update name if provided
        if 'name' in updates:
            user['name'] = updates['name']
        
        # Update email if provided
        if 'email' in updates:
            user['email'] = updates['email']
        
        # Update password if provided
        if 'password' in updates:
            if len(updates['password']) < 6:
                return False, "Hasło musi mieć co najmniej 6 znaków"
            user['password'] = generate_password_hash(updates['password'])
        
        # Update profile picture if provided
        if 'profile_picture' in updates:
            user['profile_picture'] = updates['profile_picture']
        
        self.save_config()
        return True, "Profil zaktualizowany pomyślnie"
