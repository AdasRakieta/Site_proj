# Architektura szczegółowa - SmartHome

Poniższy dokument rozszerza wersję roboczą pracy inżynierskiej o szczegółowe opisy modułów, cytaty z kodu źródłowego oraz wskazania, skąd pochodzi dany fragment. Wszystkie źródła kodu znajdują się w repozytorium: pliki wymienione obok są linkami do źródeł.

- Źródło: Wiki — "Architecture Overview" (projektowa dokumentacja wewnętrzna)
- Kod: [app_db.py](app_db.py)
- Kod: [app/routes.py](app/routes.py)
- Kod: [utils/multi_home_db_manager.py](utils/multi_home_db_manager.py)
- Kod: [utils/smart_home_db_manager.py](utils/smart_home_db_manager.py)
- Kod: [utils/cache_manager.py](utils/cache_manager.py)

## 1. Główne komponenty aplikacji

- `SmartHomeApp` (plik: [app_db.py](app_db.py))
  - Inicjalizuje Flask, Socket.IO, cache, menedżery i harmonogramy.
  - Fragment inicjalizacji połączenia z bazą (cytat):

```python
try:
    from app.configure_db import SmartHomeSystemDB as SmartHomeSystem
    DATABASE_MODE = True
    print("✓ Using PostgreSQL database backend")
except ImportError as e:
    print(f"⚠ Failed to import database backend: {e}")
    print("⚠ Falling back to JSON file backend")
    from app.configure import SmartHomeSystem
    DATABASE_MODE = False
```

- `RoutesManager` (plik: [app/routes.py](app/routes.py))
  - Odpowiada za rejestrację tras, obsługę kontekstu wielodomowego i emisję zdarzeń Socket.IO.
  - Przykładowe helpery do normalizacji identyfikatorów i zasięgu domu (cytat):

```python
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
```

## 2. Warstwa bazy danych

- `MultiHomeDBManager` (plik: [utils/multi_home_db_manager.py](utils/multi_home_db_manager.py))
  - Abstrahuje operacje wielodomowe: zarządzanie domami, zaproszeniami, automatyzacjami oraz konteneryzację transakcji.
  - Używa kontekstowego kursora `get_cursor()` z automatycznym commit/rollback (cytat):

```python
@contextmanager
def get_cursor(self):
    """Context manager for database cursor with automatic transaction handling."""
    cursor = None
    try:
        self._ensure_connection()
        if self._connection:
            cursor = self._connection.cursor()
            yield cursor
            self._connection.commit()
    except Exception as e:
        if self._connection:
            self._connection.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
```

- `SmartHomeDatabaseManager` (plik: [utils/smart_home_db_manager.py](utils/smart_home_db_manager.py))
  - Zastępuje JSON-owy backend PostgreSQL-em: pula połączeń, helper `_execute_query`, metody CRUD dla użytkowników, pokoi i urządzeń.
  - Fragment obsługi puli połączeń (cytat):

```python
self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=self._pool_minconn,
    maxconn=self._pool_maxconn,
    **filtered_config
)
```

## 3. Cache i strategia buforowania

- `CacheManager` (plik: [utils/cache_manager.py](utils/cache_manager.py))
  - Centralizuje polityki timeoutów i mechanizmy invalidacji.
  - Domyślne timeouty (fragment):

```python
self._cache_timeouts = {
    'user_data': 1800,
    'config': 900,
    'rooms': 1800,
    'buttons': 600,
    'temperature': 300,
    'automations': 900,
    'api_response': 600,
    'session_user': 3600
}
```

## 4. Integracja modułów i przepływy danych

- Start aplikacji (w `SmartHomeApp.__init__`) ładuje komponenty, inicjalizuje `MultiHomeDBManager` jeśli `DATABASE_MODE` i rejestruje `RoutesManager` z referencją do `multi_db`. Zależności są wstrzykiwane przez konstruktor `RoutesManager`.

- Przepływ dla akcji użytkownika (przykład: toggle przycisku)
  - Frontend wysyła żądanie → `RoutesManager` normalizuje identyfikatory → sprawdza uprawnienia przez `auth_manager` → zapisuje stan w `multi_db` → emituje `update_button` przez Socket.IO → cache invalidation dla kluczy związanych z przyciskami.

## 5. Cytowania i źródła

- Fragmenty kodu cytowane powyżej pochodzą wprost z plików źródłowych repozytorium (linki umieszczone na początku dokumentu). Dla pełnej transparentności w finalnej wersji pracy mogę wkleić dodatkowe dłuższe urywki funkcji oraz dokładne numery linii.

---
Jeśli chcesz, mogę teraz:
- wygenerować dodatkowe, szczegółowe cytaty (pełne funkcje) z podaniem numerów linii;
- skonwertować diagramy PlantUML do Mermaid i zapisać je jako pliki `.mmd` w katalogu `Inzynierka/Inżynierka_02/diagrams` (zrobię to teraz, jeśli potwierdzisz).
