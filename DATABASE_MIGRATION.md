# SmartHome System - Migration do PostgreSQL

## Przegląd Migracji

System SmartHome został zmigrowany z przechowywania danych w plikach JSON do bazy danych PostgreSQL. Ta migracja zapewnia:

- **Lepszą wydajność** - szybsze zapytania i operacje na danych
- **Większą niezawodność** - transakcje ACID, kopie zapasowe
- **Skalowalność** - obsługa większej liczby użytkowników i urządzeń
- **Integrację** - łatwiejsza integracja z innymi systemami
- **Audytowalność** - kompletne logi wszystkich operacji

## Struktura Bazy Danych

### Główne Tabele

1. **users** - Użytkownicy systemu
   - UUID jako klucz główny
   - Zahaszowane hasła (scrypt)
   - Role i profile użytkowników

2. **rooms** - Pokoje w domu
   - Obsługa kolejności wyświetlania
   - Relacje z urządzeniami

3. **devices** - Urządzenia (przyciski i termostaty)
   - Zunifikowana tabela dla wszystkich typów urządzeń
   - Powiązanie z pokojami
   - Historyczne śledzenie zmian

4. **automations** - Automatyzacje
   - Konfiguracja wyzwalaczy w JSON
   - Śledzenie wykonań i błędów

5. **management_logs** - Logi zarządzania
   - Kompletny audit trail
   - Indeksowanie dla szybkich zapytań

6. **system_settings** - Ustawienia systemowe
   - Elastyczne przechowywanie konfiguracji w JSON

## Proces Migracji

### Krok 1: Przygotowanie Bazy Danych

```bash
# Połącz się z PostgreSQL i utwórz schemat
psql -h 192.168.1.219 -U admin -d admin

# Wykonaj skrypt SQL schema (dostępny w VS Code)
```

### Krok 2: Instalacja Zależności

```bash
# Zainstaluj wymagane pakiety
pip install psycopg2-binary flask flask-socketio werkzeug requests
```

### Krok 3: Migracja Danych

```bash
# Sprawdź połączenie z bazą danych
python run_database_migration.py check

# Podgląd migracji (bez zapisu)
python run_database_migration.py migrate --dry-run

# Wykonaj migrację
python run_database_migration.py migrate --force

# Lub kompletna migracja jedną komendą
python run_database_migration.py full --force
```

### Krok 4: Uruchomienie Aplikacji

```bash
# Uruchom aplikację w trybie bazy danych
python run_database_migration.py start

# Lub użyj nowego pliku aplikacji
python app_db.py
```

## Migrowane Komponenty

### ✅ Zmigrowane Funkcjonalności

1. **Zarządzanie Użytkownikami**
   - Rejestracja z weryfikacją email
   - Logowanie i sesje
   - Profile użytkowników
   - Zdjęcia profilowe
   - Role admin/user

2. **Zarządzanie Pokojami**
   - Dodawanie/usuwanie pokojów
   - Zmiana nazw pokojów
   - Kolejność wyświetlania

3. **Urządzenia IoT**
   - Przyciski/przełączniki
   - Kontrola temperatury
   - Stany urządzeń
   - Historyczne śledzenie

4. **System Automatyzacji**
   - Wyzwalacze czasowe
   - Wyzwalacze urządzeń
   - Łańcuchy akcji
   - Powiadomienia email

5. **Panel Administracyjny**
   - Zarządzanie użytkownikami
   - Logi systemowe
   - Statystyki użytkowania

6. **Ustawienia Systemowe**
   - Stan bezpieczeństwa
   - Konfiguracja motywów
   - Parametry systemowe

### 🔄 W Trakcie Migracji

1. **Cache Manager** - dostosowanie do bazy danych
2. **Mail Manager** - integracja z nowymi ustawieniami
3. **WebSocket Events** - aktualizacja dla bazy danych

## API i Kompatybilność

### Zachowana Kompatybilność

Wszystkie istniejące endpointy API pozostają niezmienione:

```
GET /api/users
POST /api/users
PUT /api/users/<id>
DELETE /api/users/<id>

GET /api/rooms
POST /api/rooms
PUT /api/rooms/<room>
DELETE /api/rooms/<room>

GET /api/buttons
POST /api/buttons
PUT /api/buttons/<id>
DELETE /api/buttons/<id>

GET /api/temperature_controls
POST /api/temperature_controls
PUT /api/temperature_controls/<id>
DELETE /api/temperature_controls/<id>

GET /api/automations
POST /api/automations
PUT /api/automations/<index>
DELETE /api/automations/<index>
```

### Nowe Funkcjonalności

```
GET /api/database/stats - Statystyki bazy danych
GET /api/database/export - Eksport do JSON
POST /api/database/backup - Kopia zapasowa
```

## Konfiguracja Środowiska

### Zmienne Środowiskowe

```bash
# Baza danych
export DB_HOST=192.168.1.219
export DB_PORT=5432
export DB_NAME=admin
export DB_USER=admin
export DB_PASSWORD=Qwuizzy123.
export HOME_ID=your-unique-home-id

# Email (bez zmian)
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your_email@gmail.com
export SMTP_PASSWORD=your_app_password
```

### Plik .env

```
DB_HOST=192.168.1.219
DB_PORT=5432
DB_NAME=admin
DB_USER=admin
DB_PASSWORD=Qwuizzy123.
HOME_ID=auto-generated-uuid
```

## Wydajność i Optymalizacja

### Indeksy Bazy Danych

- `idx_users_name` - szybkie wyszukiwanie użytkowników
- `idx_devices_room` - filtrowanie urządzeń po pokojach
- `idx_logs_timestamp` - chronologiczne sortowanie logów
- `idx_automations_enabled` - filtrowanie aktywnych automatyzacji

### Cache Strategy

- Cache użytkowników na 1 godzinę
- Cache pokojów na 30 minut
- Cache urządzeń na 15 minut
- Natychmiastowa inwaliacja przy zmianach

## Monitoring i Diagnostyka

### Logi Aplikacji

```python
# Włącz szczegółowe logowanie
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Statystyki Bazy Danych

```python
from utils.smart_home_db_manager import SmartHomeDatabaseManager

db = SmartHomeDatabaseManager()
stats = db.get_stats()
print(f"Database stats: {stats}")
```

### Health Check

```bash
# Sprawdź status systemu
curl http://localhost:5000/api/health

# Sprawdź połączenie z bazą
python -c "from utils.smart_home_db_manager import SmartHomeDatabaseManager; SmartHomeDatabaseManager()"
```

## Kopie Zapasowe

### Automatyczne Kopie

Baza danych PostgreSQL zapewnia:
- Automatyczne WAL (Write-Ahead Logging)
- Point-in-time recovery
- Replications (jeśli skonfigurowane)

### Ręczne Kopie

```bash
# Backup całej bazy
pg_dump -h 192.168.1.219 -U admin admin > backup_$(date +%Y%m%d).sql

# Backup tylko danych aplikacji
pg_dump -h 192.168.1.219 -U admin admin --data-only > data_backup_$(date +%Y%m%d).sql
```

### Eksport do JSON (kompatybilność wsteczna)

```python
from configure_db import SmartHomeSystemDB

smart_home = SmartHomeSystemDB()
json_data = smart_home.export_to_json()

# Zapisz kopię zapasową w formacie JSON
import json
with open('backup.json', 'w') as f:
    json.dump(json_data, f, indent=2)
```

## Troubleshooting

### Problemy z Połączeniem

1. **Sprawdź parametry połączenia**
   ```bash
   telnet 192.168.1.219 5432
   ```

2. **Sprawdź uprawnienia użytkownika**
   ```sql
   \du
   ```

3. **Sprawdź dostępność bazy**
   ```sql
   \l
   ```

### Problemy z Migracją

1. **Konflikt danych** - użyj `--force`
2. **Błędy UUID** - sprawdź format w plikach JSON
3. **Brakujące kolumny** - wykonaj ponownie skrypt schema

### Problemy z Aplikacją

1. **Import Error** - sprawdź zainstalowane pakiety
2. **Database Error** - sprawdź połączenie
3. **Permission Error** - sprawdź uprawnienia użytkownika DB

## Następne Kroki

### Planowane Usprawnienia

1. **Connection Pooling** - zarządzanie połączeniami
2. **Read Replicas** - skalowanie odczytu
3. **Automated Backups** - zaplanowane kopie zapasowe
4. **Metrics & Monitoring** - szczegółowa telemetria
5. **Multi-tenant Support** - obsługa wielu domów

### Rekomendacje Produkcyjne

1. **SSL/TLS** - szyfrowane połączenia
2. **Firewall Rules** - ograniczony dostęp do bazy
3. **Regular Backups** - codzienne kopie zapasowe
4. **Monitoring Alerts** - powiadomienia o problemach
5. **Load Balancing** - przy większym ruchu

---

## Podsumowanie

Migracja do PostgreSQL znacząco poprawia możliwości systemu SmartHome:

- ✅ **Niezawodność** - transakcje ACID
- ✅ **Wydajność** - indeksowane zapytania  
- ✅ **Skalowalność** - obsługa wielu użytkowników
- ✅ **Bezpieczeństwo** - proper authentication
- ✅ **Audytowalność** - kompletne logi
- ✅ **Kompatybilność** - zachowanie API

System jest teraz gotowy na production i dalszy rozwój!
