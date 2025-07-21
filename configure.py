import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import uuid
import threading
import time


class SmartHomeSystem:
    """Główna klasa systemu SmartHome zarządzająca wszystkimi komponentami"""
    
    def __init__(self, config_file='smart_home_config.json', save_interval=3000):
        # Ustal katalog bazowy na podstawie lokalizacji tego pliku
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.base_dir, config_file)
        self.first_config_file = os.path.join(self.base_dir, 'smart_home_1st_conf.json')
        self.save_interval = save_interval
        self.last_save_time = datetime.now()
        
        # Dodanie blokady dla zapisu konfiguracji
        self._save_lock = threading.RLock()
        self._save_in_progress = False
        
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
        self.load_config()
        # self.choose_configuration()

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
                    # MIGRACJA użytkowników na UUID
                    self.migrate_users_to_uuid()
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
        # Ensure automations is initialized
        if not hasattr(self, 'automations'):
            self.automations = self.default_config['automations'].copy()
        self.save_config()

    def save_config(self):
        """Zapisuje aktualną konfigurację do pliku z obsługą współbieżności"""
        with self._save_lock:
            if self._save_in_progress:
                print("Zapis konfiguracji już w toku, pomijam duplikujący zapis")
                return True
            
            self._save_in_progress = True
            max_retries = 3
            retry_delay = 0.1
            
            try:
                # MIGRACJA: nadaj brakujące id przed zapisem
                for device in self.buttons:
                    if 'id' not in device:
                        device['id'] = str(uuid.uuid4())
                for device in self.temperature_controls:
                    if 'id' not in device:
                        device['id'] = str(uuid.uuid4())
                
                config = {
                    'users': self.users,
                    'temperature_states': self.temperature_states,
                    'security_state': self.security_state,
                    'rooms': self.rooms,
                    'buttons': self.buttons,
                    'temperature_controls': self.temperature_controls,
                    'automations': self.automations
                }
                
                # Spróbuj zapisać z mechanizmem ponawiania
                for attempt in range(max_retries):
                    try:
                        # Zapisz do tymczasowego pliku, potem przenieś
                        temp_file = self.config_file + '.tmp'
                        with open(temp_file, 'w') as f:
                            json.dump(config, f, indent=4, ensure_ascii=False)
                        
                        # Atomowe przeniesienie pliku
                        os.replace(temp_file, self.config_file)
                        
                        self.last_save_time = datetime.now()
                        print(f"Zapisano konfigurację do {self.config_file} (próba {attempt + 1})")
                        return True
                        
                    except (OSError, IOError, json.JSONEncodeError) as e:
                        print(f"Błąd podczas zapisywania konfiguracji (próba {attempt + 1}/{max_retries}): {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (attempt + 1))  # Zwiększaj opóźnienie
                        else:
                            print("Nie udało się zapisać konfiguracji po wszystkich próbach")
                            return False
                
            except Exception as e:
                print(f"Krytyczny błąd podczas zapisywania konfiguracji: {str(e)}")
                return False
            finally:
                self._save_in_progress = False

    def check_and_save(self):
        """Sprawdza czy należy zapisać konfigurację"""
        if (datetime.now() - self.last_save_time).total_seconds() >= self.save_interval:
            self.save_config()

    def validate_and_fix_data(self):
        """Sprawdza i naprawia strukturę danych"""
        # Fix rooms - ensure it's a list of strings
        if not isinstance(self.rooms, list):
            self.rooms = []
        else:
            self.rooms = [room for room in self.rooms if isinstance(room, str) and room.strip()]
        
        # Fix buttons - ensure proper structure
        if not isinstance(self.buttons, list):
            self.buttons = []
        
        # Fix temperature_controls - ensure proper structure
        if not isinstance(self.temperature_controls, list):
            self.temperature_controls = []
            
        # Fix automations - ensure proper structure
        if not isinstance(self.automations, list):
            self.automations = []
            
        print(f"[INFO] Data validation completed. Rooms: {len(self.rooms)}, Buttons: {len(self.buttons)}, Controls: {len(self.temperature_controls)}")

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
    
    def add_user(self, username, password, role='user', email=''):
        """Dodaje nowego użytkownika (login w 'name', klucz to UUID)"""
        # Sprawdź czy login już istnieje
        for user in self.users.values():
            if user.get('name') == username:
                return False, "Użytkownik już istnieje"
        if len(username) < 3:
            return False, "Nazwa użytkownika musi mieć co najmniej 3 znaki"
        if len(password) < 6:
            return False, "Hasło musi mieć co najmniej 6 znaków"
        if role not in ['user', 'admin']:
            return False, "Nieprawidłowa rola użytkownika"
        # Email is now required
        if not email or not email.strip():
            return False, "Adres email jest wymagany"
        # Validate email format
        if '@' not in email or '.' not in email.split('@')[1]:
            return False, "Nieprawidłowy format adresu email"
        # Check if email already exists
        for user in self.users.values():
            if user.get('email') == email:
                return False, "Adres email jest już używany"
        user_id = str(uuid.uuid4())
        self.users[user_id] = {
            'name': username,
            'password': generate_password_hash(password),
            'role': role,
            'email': email,
            'profile_picture': ''
        }
        if not self.save_config():
            return False, "Błąd podczas zapisywania konfiguracji"
        return True, "Użytkownik dodany pomyślnie"

    def delete_user(self, user_id):
        """Usuwa użytkownika po user_id (UUID)"""
        user = self.users.get(user_id)
        if not user:
            return False, "Użytkownik nie istnieje"
        if user.get('role') == 'admin':
            # Nie pozwól usunąć ostatniego admina
            admin_count = sum(1 for u in self.users.values() if u.get('role') == 'admin')
            if admin_count <= 1:
                return False, "Nie można usunąć głównego administratora"
        del self.users[user_id]
        if not self.save_config():
            return False, "Błąd podczas zapisywania konfiguracji"
        return True, "Użytkownik usunięty pomyślnie"

    def change_password(self, user_id, new_password):
        """Zmienia hasło użytkownika po user_id (UUID)"""
        user = self.users.get(user_id)
        if not user:
            return False, "Użytkownik nie istnieje"
        if len(new_password) < 6:
            return False, "Hasło musi mieć co najmniej 6 znaków"
        user['password'] = generate_password_hash(new_password)
        if not self.save_config():
            return False, "Błąd podczas zapisywania konfiguracji"
        return True, "Hasło zmienione pomyślnie"

    def update_user_profile(self, user_id, updates):
        """Aktualizuje profil użytkownika po user_id (UUID), w tym login (pole 'name')"""
        user = self.users.get(user_id)
        if not user:
            return False, "Użytkownik nie istnieje"
        new_username = updates.get('username')
        # Jeśli zmieniamy login (nazwę użytkownika)
        if new_username and new_username != user.get('name'):
            # Sprawdź czy login już istnieje
            for u in self.users.values():
                if u.get('name') == new_username:
                    return False, "Taki użytkownik już istnieje"
            user['name'] = new_username
        for key in ['email', 'profile_picture']:
            if key in updates:
                user[key] = updates[key]
        if 'password' in updates:
            if len(updates['password']) < 6:
                return False, "Hasło musi mieć co najmniej 6 znaków"
            user['password'] = generate_password_hash(updates['password'])
        if not self.save_config():
            return False, "Błąd podczas zapisywania konfiguracji"
        return True, "Profil zaktualizowany pomyślnie"

    def migrate_users_to_uuid(self):
        """Migracja użytkowników: klucze na UUID, login w polu 'name'"""
        new_users = {}
        for old_key, user in self.users.items():
            # Jeśli już jest UUID (ma pole 'name' różne od klucza), pomiń
            if user.get('name') and old_key != user.get('name') and self.is_uuid(old_key):
                new_users[old_key] = user
                continue
            # Wygeneruj UUID
            new_id = str(uuid.uuid4())
            # Przenieś login do pola 'name'
            user = user.copy()
            user['name'] = user.get('name', old_key)
            new_users[new_id] = user
        self.users = new_users

    @staticmethod
    def is_uuid(val):
        try:
            uuid.UUID(str(val))
            return True
        except Exception:
            return False

    def get_user_data(self, user_id):
        """Pobiera dane użytkownika (bez hasła) na podstawie user_id (klucz w users)"""
        user = self.users.get(user_id, {})
        return {
            'user_id': user_id,
            'name': user.get('name', user_id),
            'email': user.get('email', ''),
            'profile_picture': user.get('profile_picture', ''),
            'role': user.get('role', 'user')
        }

    def verify_password(self, user_id, password):
        """Weryfikuje hasło użytkownika po user_id"""
        user = self.users.get(user_id)
        if user and check_password_hash(user['password'], password):
            return True
        return False

    def update_user_profile(self, username, updates):
        """Aktualizuje profil użytkownika, w tym login (nazwę użytkownika)"""
        if username not in self.users:
            return False, "Użytkownik nie istnieje"

        user = self.users[username]
        new_username = updates.get('username')
        # Jeśli zmieniamy login (nazwę użytkownika)
        if new_username and new_username != username:
            if new_username in self.users:
                return False, "Taki użytkownik już istnieje"
            # Przenieś WSZYSTKIE dane pod nowy klucz
            self.users[new_username] = user.copy()
            # Zaktualizuj tylko te pola, które są w updates
            for key in ['name', 'email', 'profile_picture']:
                if key in updates:
                    self.users[new_username][key] = updates[key]
            if 'password' in updates:
                if len(updates['password']) < 6:
                    return False, "Hasło musi mieć co najmniej 6 znaków"
                self.users[new_username]['password'] = generate_password_hash(updates['password'])
            # Usuń starego użytkownika
            del self.users[username]
            self.save_config()
            self.load_config()  # Dodaj: odśwież użytkowników w pamięci po zmianie loginu
            return True, "Login użytkownika został zmieniony"
        # Standardowa aktualizacja bez zmiany loginu
        for key in ['name', 'email', 'profile_picture']:
            if key in updates:
                user[key] = updates[key]
        if 'password' in updates:
            if len(updates['password']) < 6:
                return False, "Hasło musi mieć co najmniej 6 znaków"
            user['password'] = generate_password_hash(updates['password'])
        self.save_config()
        return True, "Profil zaktualizowany pomyślnie"

    def get_user_by_login(self, login):
        """Zwraca (user_id, user_dict) na podstawie loginu (pola name)"""
        for user_id, user in self.users.items():
            if user.get('name') == login:
                return user_id, user
        return None, None
