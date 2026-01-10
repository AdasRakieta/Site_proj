# Automatyczny System Backup do JSON

## Przegląd

System SmartHome posiada teraz pełny automatyczny backup do JSON, który aktywuje się gdy PostgreSQL jest niedostępny. System ten zapewnia:

- **Automatyczne tworzenie pliku konfiguracyjnego** gdy nie istnieje
- **Generowanie bezpiecznego użytkownika sys-admin** z losowym hasłem
- **Pełną funkcjonalność systemu** bez bazy danych PostgreSQL
- **Bezproblemowy fallback** z automatycznym przełączaniem

## Główne Komponenty

### 1. JSONBackupManager (`utils/json_backup_manager.py`)

Centralny menedżer systemu backup do JSON:

**Funkcje:**
- Automatyczne tworzenie pliku `smart_home_config.json` jeśli nie istnieje
- Generowanie bezpiecznego 16-znakowego hasła dla użytkownika `sys-admin`
- Wyświetlanie hasła w logach podczas pierwszego uruchomienia
- Walidacja struktury konfiguracji
- Bezpieczny zapis z atomowym zastępowaniem plików
- Automatyczne tworzenie backupów przed każdym zapisem

**Użycie:**
```python
from utils.json_backup_manager import JSONBackupManager, ensure_json_backup

# Bezpośrednia inicjalizacja
manager = JSONBackupManager('smart_home_config.json')

# Lub przez helper
manager = ensure_json_backup()

# Pobranie konfiguracji
config = manager.get_config()

# Zapis konfiguracji
manager.save_config(config)
```

### 2. SmartHomeSystem (`app/configure.py`)

Podstawowy system JSON został zaktualizowany aby używać JSONBackupManager:

```python
class SmartHomeSystem:
    def __init__(self, config_file='smart_home_config.json', save_interval=3000):
        # Inicjalizacja JSON backup managera
        self.json_backup = JSONBackupManager(config_file)
        # ... reszta inicjalizacji
```

### 3. SmartHomeSystemDB (`app/configure_db.py`)

System bazodanowy z automatycznym fallback do JSON:

```python
def __init__(self, config_file=None, save_interval=3000):
    try:
        self.db = SmartHomeDatabaseManager()
        self.json_fallback = None
        print("✓ PostgreSQL database connected successfully")
    except (DatabaseError, Exception) as e:
        print("⚠ Failed to initialize database")
        print("⚠ Activating JSON backup fallback...")
        
        # Automatyczny fallback do JSON
        self.json_fallback = ensure_json_backup()
        self.db = None
        print("✓ JSON backup mode activated - system fully operational")
```

### 4. MultiHomeDBManager (`utils/multi_home_db_manager.py`)

Menedżer wielu domów z fallback do JSON:

```python
def __init__(self, host=None, port=None, user=None, password=None, database=None):
    # Walidacja konfiguracji
    if not self.host or not self.user or not self.password or not self.database:
        print("⚠ Missing database configuration, activating JSON fallback mode")
        self._activate_json_fallback()
        return
    
    try:
        self._ensure_connection()
        # ... inicjalizacja tabel
    except Exception as e:
        print(f"⚠ PostgreSQL connection failed: {e}")
        print("⚠ Activating JSON fallback mode for multi-home manager")
        self._activate_json_fallback()
```

### 5. SmartHomeDatabaseManager (`utils/smart_home_db_manager.py`)

Bazowy menedżer bazy danych z JSON fallback:

```python
def __init__(self, db_config=None):
    # Walidacja konfiguracji
    missing_keys = [k for k in required_keys if not self.db_config.get(k)]
    if missing_keys:
        print(f"⚠ Missing database config: {', '.join(missing_keys)}")
        print("⚠ Activating JSON fallback mode")
        self._activate_json_fallback()
        return
    
    try:
        self._initialize_connection_pool()
        self._test_connection()
    except Exception as e:
        print(f"⚠ Database connection failed: {e}")
        print("⚠ Activating JSON fallback mode")
        self._activate_json_fallback()
```

## Działanie Systemu

### Scenariusz 1: Pierwszym Uruchomienie (bez PostgreSQL)

1. System próbuje połączyć się z PostgreSQL
2. Wykrywa brak zmiennych środowiskowych DB_*
3. Automatycznie aktywuje JSONBackupManager
4. Sprawdza czy plik `smart_home_config.json` istnieje
5. Jeśli nie istnieje, tworzy nowy z następującą strukturą:

```json
{
    "users": {
        "sys-admin": {
            "id": "sys-admin-uuid-<random>",
            "username": "sys-admin",
            "password": "<bcrypt-hash>",
            "role": "admin",
            "name": "System Administrator",
            "email": "admin@localhost",
            "created_at": "2026-01-10T...",
            "is_system_user": true
        }
    },
    "temperature_states": {},
    "security_state": "Wyłączony",
    "rooms": [],
    "buttons": [],
    "temperature_controls": [],
    "automations": [],
    "metadata": {
        "created_at": "2026-01-10T...",
        "backup_mode": true,
        "version": "1.0"
    }
}
```

6. Wyświetla w logach:

```
======================================================================
🔧 JSON BACKUP MODE ACTIVATED
======================================================================
📄 Configuration file created: app/smart_home_config.json
👤 Default admin user created:
   Username: sys-admin
   Password: aB3$dE7&hK9@mN2p
======================================================================
⚠️  IMPORTANT: Save these credentials! They will not be shown again.
======================================================================
```

### Scenariusz 2: PostgreSQL Niedostępny (baza istnieje, ale nie działa)

1. System próbuje połączyć się z PostgreSQL
2. Timeout połączenia lub błąd autoryzacji
3. Automatyczny fallback do JSON
4. Ładuje istniejący `smart_home_config.json`
5. Kontynuuje pracę w trybie JSON

### Scenariusz 3: PostgreSQL Dostępny

1. System łączy się z PostgreSQL
2. Inicjalizuje pule połączeń
3. Pracuje normalnie z bazą danych
4. JSON backup pozostaje nieaktywny (dostępny w razie potrzeby)

## Generowanie Hasła

System używa modułu `secrets` do generowania bezpiecznych haseł:

```python
def _generate_secure_password(self, length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password
```

**Charakterystyka hasła:**
- Długość: 16 znaków (konfigurowalny)
- Zawiera: wielkie litery, małe litery, cyfry, znaki specjalne
- Kryptograficznie bezpieczne (użycie `secrets` zamiast `random`)
- Hash: Werkzeug `generate_password_hash()` (domyślnie scrypt)

## Logi Startowe

### Z PostgreSQL:
```
✓ Using PostgreSQL database backend
✓ PostgreSQL database connected successfully
✓ SmartHome system initialized with PostgreSQL backend
📊 Database mode: PostgreSQL
```

### Z JSON Backup:
```
⚠ Failed to import database backend: Missing DB_HOST environment variable
⚠ Falling back to JSON file backend with automatic configuration
⚠ Missing database configuration, activating JSON fallback mode

======================================================================
🔧 JSON BACKUP MODE ACTIVATED
======================================================================
📄 Configuration file created: app/smart_home_config.json
👤 Default admin user created:
   Username: sys-admin
   Password: xY9@kL2$pQ5!mN8z
======================================================================
⚠️  IMPORTANT: Save these credentials! They will not be shown again.
======================================================================

✓ JSON backup system initialized
✓ SmartHome system initialized with JSON backup backend
📊 Database mode: JSON Files
```

## Testowanie

Uruchom skrypt testowy aby zweryfikować funkcjonalność:

```bash
python test_json_backup.py
```

Test sprawdza:
1. Inicjalizację JSONBackupManager
2. Tworzenie pliku konfiguracyjnego
3. Generowanie użytkownika sys-admin
4. Zapis i odczyt konfiguracji
5. Fallback SmartHomeSystemDB do JSON
6. Fallback MultiHomeDBManager do JSON

## Bezpieczeństwo

### Ochrona Hasła
- Hasło generowane tylko raz przy tworzeniu pliku
- Wyświetlane w logach tylko podczas pierwszego uruchomienia
- Natychmiast hashowane przez Werkzeug
- Nie jest nigdzie zapisywane w postaci jawnej (tylko hash w JSON)

### Backupy
- Przed każdym zapisem tworzony jest backup: `smart_home_config.json.backup`
- Reset do domyślnych tworzy timestampowany backup: `smart_home_config.json.reset-20260110-192945`

### Atomowy Zapis
```python
# Zapis do tymczasowego pliku
with open(temp_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=4, ensure_ascii=False)

# Atomowe zastąpienie (bezpieczne)
os.replace(temp_file, self.config_file)
```

## API Reference

### JSONBackupManager

#### `__init__(config_file: str = 'smart_home_config.json')`
Inicjalizuje menedżer backup do JSON.

#### `get_config() -> Dict[str, Any]`
Zwraca aktualną konfigurację.

#### `save_config(config: Dict[str, Any]) -> bool`
Zapisuje konfigurację do pliku.

#### `update_metadata(key: str, value: Any) -> bool`
Aktualizuje metadane w konfiguracji.

#### `get_admin_credentials() -> Optional[Dict[str, str]]`
Zwraca dane logowania sys-admin (tylko jeśli właśnie wygenerowane).

#### `reset_to_defaults() -> bool`
Resetuje konfigurację do domyślnej (z backupem).

### Helper Functions

#### `ensure_json_backup() -> JSONBackupManager`
Zapewnia dostępność JSON backup i zwraca instancję menedżera.

## Migracja z Istniejącego Systemu

Jeśli masz już plik `smart_home_config.json`:

1. System automatycznie go rozpozna
2. Nie będzie generował nowego użytkownika sys-admin
3. Będzie używał istniejącej konfiguracji
4. Logi pokażą: `✓ Loaded existing JSON configuration from app/smart_home_config.json`

## Zmienne Środowiskowe

System sprawdza następujące zmienne dla PostgreSQL:
- `DB_HOST` - adres serwera PostgreSQL
- `DB_PORT` - port (domyślnie: 5432)
- `DB_USER` - użytkownik bazy danych
- `DB_PASSWORD` - hasło do bazy danych
- `DB_NAME` - nazwa bazy danych

Jeśli którakolwiek z nich brakuje, system automatycznie przełącza się na JSON backup.

## Zalety Rozwiązania

✅ **Automatyzacja** - Zero konfiguracji manualnej  
✅ **Bezpieczeństwo** - Kryptograficznie bezpieczne hasła  
✅ **Niezawodność** - Fallback na wszystkich poziomach  
✅ **Przejrzystość** - Jasne logi informujące o stanie  
✅ **Kompatybilność** - Działa z istniejącymi konfiguracjami  
✅ **Testowalne** - Dedykowany skrypt testowy  
✅ **Backup** - Automatyczne kopie zapasowe  

## Rozwiązywanie Problemów

### Problem: Nie widzę hasła sys-admin
**Rozwiązanie:** Hasło jest wyświetlane tylko raz podczas pierwszego uruchomienia. Jeśli go przegapiłeś, możesz:
1. Usunąć plik `app/smart_home_config.json`
2. Zrestartować aplikację
3. Nowe hasło zostanie wygenerowane i wyświetlone

### Problem: System nie przełącza się na JSON
**Rozwiązanie:** Sprawdź logi. Jeśli widzisz błędy importu, upewnij się że:
1. Plik `utils/json_backup_manager.py` istnieje
2. Wszystkie zależności są zainstalowane (`pip install -r requirements.txt`)

### Problem: Nie mogę się zalogować
**Rozwiązanie:** 
1. Sprawdź logi startowe - znajdź wygenerowane hasło
2. Użyj username: `sys-admin`
3. Jeśli nadal nie działa, zresetuj konfigurację (punkt 1 powyżej)

## Changelog

### v1.0 (2026-01-10)
- ✨ Dodano JSONBackupManager
- ✨ Automatyczne generowanie użytkownika sys-admin
- ✨ Fallback w SmartHomeSystemDB
- ✨ Fallback w MultiHomeDBManager
- ✨ Fallback w SmartHomeDatabaseManager
- ✨ Skrypt testowy `test_json_backup.py`
- 📝 Pełna dokumentacja
