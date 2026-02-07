# 4. Implementacja — szczegółowy opis modułów i fragmenty kodu

W tym rozdziale prezentowane są szczegóły implementacyjne: struktura modułów, kluczowe fragmenty kodu, schematy inicjalizacji oraz przykładowe zapytania SQL i polityki transakcyjne.

4.1 Diagramy implementacyjne i zasoby
- Szczegółowe diagramy implementacyjne (sekcje sekwencji i ERD) dostępne są w `Inzynierka/Inżynierka_01/12_ZALACZNIKI/diagramy/` (m.in. `erd_smarthome.mmd`, `sekwencje_toggle_device.mmd`, `sekwencje_automation.mmd`) oraz w `Inzynierka/Inżynierka_02/diagrams`.

4.2 Inicjalizacja aplikacji (`SmartHomeApp`)
- `app_db.py` tworzy obiekt Flask, inicjalizuje Socket.IO, cache i menedżery. Kluczowe kroki:
  1. Wczytaj zmienne środowiskowe i spróbuj zainicjalizować backend PostgreSQL (`SmartHomeSystemDB`), w przeciwnym razie fallback do JSON.
  2. Inicjalizuj `MultiHomeDBManager` gdy `DATABASE_MODE`.
  3. Zarejestruj `RoutesManager` z referencją do `multi_db`, cache i socketio.

Fragment (inicjalizacja multi_db):

```python
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
self.multi_db = MultiHomeDBManager(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
```

4.3 MultiHomeDBManager — transakcje i migracje schematu
- `utils/multi_home_db_manager.py` używa kontekstowego kursora `get_cursor()` (automatyczny commit/rollback) oraz metod `_ensure_*_table()` do bezpiecznego utrzymania schematu.

Przykładowy fragment tworzenia tabeli `home_invitations` i migracji kolumn (upraszczając):

```sql
CREATE TABLE IF NOT EXISTS home_invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  home_id UUID NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL CHECK (role IN ('admin','member','guest')),
  invitation_code VARCHAR(20) UNIQUE NOT NULL,
  invited_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
)
```

4.4 Bezpieczne wykonanie zapytań i `_execute_query`
- `utils/smart_home_db_manager.py` implementuje `_execute_query(query, params, fetch)` z obsługą połączeń z puli, cursor_factory=RealDictCursor, rollback na wyjątku oraz logowaniem błędów. Dzięki temu wszystkie zapytania są parametryzowane (psycopg2) co zabezpiecza przed SQL injection.

Fragment uproszczony `_execute_query`:

```python
conn = self._get_connection()
with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    cur.execute(query, params)
    if fetch == 'one':
        return dict(cur.fetchone())
    elif fetch == 'all':
        return [dict(r) for r in cur.fetchall()]
    else:
        conn.commit()
        return cur.rowcount
```

4.5 Integracja z Cache i Socket.IO
- Po każdej operacji modyfikującej stan urządzeń backend wykonuje:
  1. Zapis w DB (w tranzakcji)
  2. Unieważnienie odpowiednich kluczy w `CacheManager` (np. `buttons_list`)
  3. Rozgłoszenie zdarzenia WebSocket: `update_button`/`update_rooms` itp.

4.6 Przykładowy scenariusz: toggle przycisku (implementacja)
1. Frontend emituje `toggle_button` z identyfikatorem i nowym stanem.
2. `RoutesManager` normalizuje identyfikator (`normalize_device_id`) i rozwiązuje `home_id`.
3. `MultiHomeDBManager.update_button_state` zapisuje nowy stan w tabeli `devices` lub `buttons` w ramach kursora.
4. `CacheManager.invalidate('buttons_list')` usuwa zbuforowane odczyty.
5. `socketio.emit('update_button', payload)` rozsyła aktualizację do wszystkich klientów.

4.7 Testy integracyjne i hooki
- Moduły DB i Cache mają punkty rozszerzeń do testów integracyjnych: możliwość podłączenia SQLite/mocked DB lub wstrzyknięcie cache `NullCache` dla izolacji testów.
