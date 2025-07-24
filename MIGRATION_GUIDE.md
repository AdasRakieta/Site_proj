# 🏠 SmartHome System - Migracja do PostgreSQL

## 🚀 Szybki Start

### 1. Sprawdź Status Systemu
```bash
python config_manager.py status
```

### 2. Przełącz na Tryb Bazy Danych
```bash
python config_manager.py switch database
```

### 3. Wykonaj Pełną Migrację
```bash
python run_database_migration.py full --force
```

### 4. Uruchom Aplikację
```bash
python app_db.py
```

---

## 📋 Szczegółowe Instrukcje

### Krok 1: Przygotowanie

```bash
# Sprawdź obecny status
python config_manager.py status

# Utwórz kopię zapasową plików JSON
python config_manager.py backup
```

### Krok 2: Instalacja Zależności

```bash
# Zainstaluj wymagane pakiety
python run_database_migration.py install
```

### Krok 3: Konfiguracja Bazy Danych

1. **Utwórz schemat bazy danych:**
   - Otwórz skrypt SQL w VS Code (został już utworzony)
   - Wykonaj go w swojej bazie PostgreSQL

2. **Sprawdź połączenie:**
```bash
python run_database_migration.py check
```

### Krok 4: Migracja Danych

```bash
# Podgląd migracji (bez zapisu)
python run_database_migration.py migrate --dry-run

# Wykonaj migrację
python run_database_migration.py migrate --force

# Lub wszystko jedną komendą
python run_database_migration.py full --force
```

### Krok 5: Uruchomienie

```bash
# Uruchom w trybie bazy danych
python app_db.py

# Lub
python run_database_migration.py start
```

---

## 🔧 Dostępne Komendy

### Config Manager
```bash
python config_manager.py status          # Status systemu
python config_manager.py switch database # Przełącz na bazę danych
python config_manager.py switch json     # Przełącz na JSON
python config_manager.py backup          # Kopia zapasowa JSON
python config_manager.py migrate --force # Migruj dane
```

### Database Migration
```bash
python run_database_migration.py install    # Zainstaluj pakiety
python run_database_migration.py check      # Sprawdź połączenie
python run_database_migration.py schema     # Utwórz schemat
python run_database_migration.py migrate    # Migruj dane
python run_database_migration.py start      # Uruchom aplikację
python run_database_migration.py full       # Pełny proces
```

---

## 📊 Co Zostało Zmigrowane

### ✅ Kompletnie Zmigrowane

- **👥 Użytkownicy** - profile, hasła, role, zdjęcia
- **🏠 Pokoje** - nazwy, kolejność
- **💡 Urządzenia** - przyciski, termostaty, stany
- **🤖 Automatyzacje** - wyzwalacze, akcje, harmonogramy
- **📝 Logi** - audit trail, historia zmian
- **⚙️ Ustawienia** - konfiguracja systemu, bezpieczeństwo
- **🌡️ Temperatury** - stany pokojów, docelowe temperatury

### 🔄 API Endpoints (Bez Zmian)

Wszystkie istniejące endpointy działają identycznie:
- `/api/users/*`
- `/api/rooms/*`
- `/api/buttons/*`
- `/api/temperature_controls/*`
- `/api/automations/*`

---

## 🗄️ Struktura Bazy Danych

```sql
users                    -- Użytkownicy (UUID, hasła, role)
├── rooms                -- Pokoje w domu
├── devices              -- Urządzenia (przyciski + termostaty)
├── automations          -- Automatyzacje i scenariusze
├── room_temperature_states -- Stany temperatury pokojów
├── management_logs      -- Logi zarządzania i audytu
├── system_settings      -- Ustawienia systemowe
├── notification_settings -- Konfiguracja powiadomień
├── notification_recipients -- Odbiorcy powiadomień
├── device_history       -- Historia zmian urządzeń
├── automation_executions -- Logi wykonań automatyzacji
└── session_tokens       -- Tokeny sesji użytkowników
```

---

## 🔒 Konfiguracja Bazy Danych

### Domyślne Ustawienia
```
Host: 192.168.1.219
Port: 5432
Database: admin
User: admin
Password: Qwuizzy123.
```

### Zmienne Środowiskowe (.env)
```bash
DB_HOST=192.168.1.219
DB_PORT=5432
DB_NAME=admin
DB_USER=admin
DB_PASSWORD=Qwuizzy123.
HOME_ID=auto-generated-uuid
```

---

## 🔧 Troubleshooting

### Problem: Błąd połączenia z bazą danych
```bash
# Sprawdź dostępność serwera
telnet 192.168.1.219 5432

# Sprawdź połączenie
python run_database_migration.py check
```

### Problem: Błędy podczas migracji
```bash
# Sprawdź logi szczegółowe
python migrate_to_database.py --dry-run

# Wymuś nadpisanie danych
python migrate_to_database.py --force
```

### Problem: Brakujące pakiety
```bash
# Zainstaluj wszystkie zależności
python run_database_migration.py install

# Lub ręcznie
pip install psycopg2-binary flask flask-socketio
```

### Problem: Aplikacja nie startuje
```bash
# Sprawdź status
python config_manager.py status

# Sprawdź logi
python -c "from app_db import SmartHomeApp; app = SmartHomeApp()"
```

---

## 📈 Korzyści z Migracji

### 🚀 Wydajność
- **Szybsze zapytania** dzięki indeksom
- **Lepsze cachowanie** danych
- **Transakcje ACID** zapewniają spójność

### 🔒 Bezpieczeństwo
- **Kontrola dostępu** na poziomie bazy
- **Audit trail** wszystkich operacji
- **Backup automatyczny** PostgreSQL

### 📊 Skalowalność
- **Obsługa wielu użytkowników** jednocześnie
- **Replikacja** dla wysokiej dostępności
- **Partycjonowanie** dla dużych zbiorów danych

### 🔧 Maintainability
- **Ustrukturyzowane dane** z relacjami
- **Walidacja** na poziomie bazy
- **Migracje** schematów

---

## 🔄 Powrót do JSON (jeśli potrzebny)

```bash
# Przełącz z powrotem na JSON
python config_manager.py switch json

# Uruchom oryginalną aplikację
python app.py
```

---

## 📞 Wsparcie

Jeśli napotkasz problemy:

1. **Sprawdź status:** `python config_manager.py status`
2. **Sprawdź logi** aplikacji i bazy danych
3. **Sprawdź konfigurację** połączenia z bazą
4. **Użyj dry-run** przed rzeczywistą migracją

---

## 🎉 Gotowe!

Po udanej migracji Twój system SmartHome:
- ✅ Używa PostgreSQL zamiast plików JSON
- ✅ Zachowuje pełną kompatybilność API
- ✅ Zapewnia lepszą wydajność i niezawodność
- ✅ Umożliwia łatwiejsze backup i recovery

**Aplikacja jest gotowa do użycia w trybie produkcyjnym!** 🚀
