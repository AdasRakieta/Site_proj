# SmartHome – System Zarządzania Domem Inteligentnym

## Przegląd

SmartHome to aplikacja webowa budowana na Flasku z integracją Flask-SocketIO, która pozwala zarządzać oświetleniem, temperaturą i automatyzacjami w inteligentnym domu. Dane przechowywane są w bazie PostgreSQL poprzez warstwę `SmartHomeSystemDB`, a w trybie awaryjnym aplikacja potrafi przełączyć się na pierwotny backend plikowy JSON. Interfejs użytkownika powstaje w szablonach Jinja2, a aktualizacje stanu urządzeń są transmitowane na żywo przez WebSockety.

## Najważniejsze funkcje

- **Sterowanie w czasie rzeczywistym** – zmiany stanów urządzeń propagowane są przez Socket.IO do wszystkich klientów.
- **Edytor automatyzacji** – triggery i akcje przechowywane są w bazie i prezentowane w widoku `automations.html`.
- **Panel administratora** – zarządzanie użytkownikami, podgląd logów oraz statystyk urządzeń.
- **Caching i kolejki** – `utils/cache_manager.py` obsługuje Redis/SimpleCache, a `utils/async_manager.py` odpowiada za wysyłkę maili w tle.
- **Elastyczne logowanie** – wpisy administracyjne mogą trafiać do bazy (`DatabaseManagementLogger`) lub, w razie potrzeby, do pliku JSON.

## Architektura systemu

### Backend

- `app_db.py` – główny punkt wejścia. Tworzy aplikację Flask, rejestruje trasy, uruchamia Socket.IO, konfiguruje cache oraz logowanie.
- `app/routes.py` – rejestracja tras HTTP i Socket.IO, obsługa logiki widoków, API oraz zarządzanie danymi.
- `app/configure_db.py` – implementacja `SmartHomeSystemDB`, zapewniająca identyczny interfejs co wersja plikowa, ale oparty na PostgreSQL.
- `utils/smart_home_db_manager.py` – niskopoziomowe operacje na bazie danych (użytkownicy, urządzenia, pokoje, automatyzacje, logi).
- `utils/cache_manager.py` – integracja z Redis/SimpleCache, statystyki, invalidacja danych oraz pamięć podręczna na poziomie sesji.
- `app/mail_manager.py` + `utils/async_manager.py` – wysyłanie maili (synchronizacja i tryb asynchroniczny).

### Frontend

- Szablony Jinja2 w katalogu `templates/` (np. `index.html`, `admin_dashboard.html`, `automations.html`).
- Statyczne zasoby w `static/` (`css`, `js`, `icons`, `profile_pictures`).
- Skrypt `utils/asset_manager.py` odpowiada za minifikację CSS/JS i tryb obserwacji podczas rozwoju.

### Dane i integracje

- PostgreSQL – podstawowy magazyn danych; skrypt `backups/db_backup.sql` dostarcza pełny schemat oraz użytkownika startowego.
- Redis (opcjonalnie) – pamięć podręczna. Przy braku konfiguracji aplikacja automatycznie użyje SimpleCache w pamięci.
- SMTP – konfiguracja w `.env` obsługiwana przez `app/mail_manager.py`.

## Struktura repozytorium

| Ścieżka      | Opis                                                            |
| -------------- | --------------------------------------------------------------- |
| `app_db.py`  | Główne uruchomienie aplikacji Flask + Socket.IO               |
| `app/`       | Logika domenowa, trasy, konfiguracja systemu, logowanie         |
| `utils/`     | Cache, obsługa bazy, asset manager, utilsy pomocnicze          |
| `templates/` | Szablony HTML (Jinja2)                                          |
| `static/`    | Zasoby statyczne (CSS, JS, grafiki)                             |
| `backups/`   | Pliki pomocnicze, m.in.`db_backup.sql` i eksport konfiguracji |
| `info/`      | Dokumentacja operacyjna (Quick Start, optymalizacje)            |

## Pierwsze kroki

### 1. Wymagania

- Python 3.10+
- PostgreSQL 13+ (z dostępem sieciowym do serwera)
- Redis (opcjonalnie, dla pamięci podręcznej)
- Windows: PowerShell 5.1 (domyślny shell w repozytorium) lub nowszy

### 2. Instalacja zależności

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Konfiguracja środowiska

**📋 Szczegółowe instrukcje deployment znajdują się w [DEPLOYMENT.md](DEPLOYMENT.md)**  
**🔧 Kompletny przewodnik konfiguracji: [ENV_CONFIGURATION.md](ENV_CONFIGURATION.md)**

#### Automatyczny setup (Zalecane)

**Windows (PowerShell):**
```powershell
.\setup_env.ps1
```

**Linux/macOS (Bash):**
```bash
chmod +x setup_env.sh
./setup_env.sh
```

Skrypt automatycznie:
- Skopiuje `.env.example` do `.env`
- Wygeneruje bezpieczny `SECRET_KEY`
- Otworzy plik do edycji

#### Manualny setup

Skopiuj plik `.env.example` do `.env` i uzupełnij swoimi danymi:

```powershell
cp .env.example .env
```

Następnie edytuj plik `.env` - wymagane zmienne:

```env
# Database (Required)
DB_HOST=localhost
DB_NAME=smarthome_multihouse
DB_USER=your_db_user
DB_PASSWORD=your_secure_password

# Flask (Required)
SECRET_KEY=random_32_character_secret_key

# Email (Required)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ADMIN_EMAIL=admin@example.com
```

#### Priorytet konfiguracji

Aplikacja ładuje zmienne środowiskowe w następującej kolejności:

1. **Zmienne systemowe** (najwyższy priorytet)
   - Ustawione w Portainer GUI
   - Ustawione w Docker Compose `environment:`
   - Zmienne systemowe w środowisku

2. **Plik `.env`** (fallback)
   - Używany w lokalnym developmencie
   - NIE jest kopiowany do kontenerów produkcyjnych

**Dlaczego taki priorytet?**
- Portainer może nadpisać wartości bez modyfikowania `.env`
- Lokalny development działa od razu z `.env`
- Bezpieczeństwo - `.env` nigdy nie trafia do Git

#### Walidacja konfiguracji

Po ustawieniu `.env`, zwaliduj konfigurację:

```powershell
python utils/validate_env.py
```

> **⚠️ UWAGA BEZPIECZEŃSTWA:** 
> - Plik `.env` zawiera wrażliwe dane (hasła, tokeny). **NIGDY** nie commituj go do repozytorium! Jest już w `.gitignore`.
> - W deploymencie produkcyjnym ustaw zmienne w Portainer GUI (patrz [DEPLOYMENT.md](DEPLOYMENT.md))
> - Zmień wszystkie domyślne hasła przed wdrożeniem!
> - `.env.example` jest bezpieczny do commita - zawiera tylko placeholdery

### 4. Przygotowanie bazy danych

1. Uruchom PostgreSQL i utwórz bazę wskazaną w `.env`.
2. Zastosuj schemat oraz wpis startowy:
   ```powershell
   psql -h localhost -U smarthome -d smart_home -f backups/db_backup.sql
   ```
3. Po zalogowaniu do aplikacji warto zmienić hasło konta administratora.

### 5. Uruchomienie aplikacji

- **Tryb deweloperski:**
  ```powershell
  python app_db.py
  ```
- **Tryb produkcyjny (Windows/Waitress):**
  ```powershell
  python -m waitress --port=5000 app_db:main
  ```
- **Tryb produkcyjny (Linux/Gunicorn):**
  ```bash
  gunicorn -w 4 -b 0.0.0.0:5000 "app_db:main"
  ```

Aplikacja startuje wraz z Socket.IO. Konsola wypisze tryb pracy (PostgreSQL lub JSON) oraz podstawowe statystyki.

## Narzędzia dodatkowe

- **Minifikacja zasobów:**
  ```powershell
  python utils/asset_manager.py          # jednorazowa minifikacja
  python utils/asset_manager.py --watch  # obserwacja plików podczas rozwoju
  ```
- **Statystyki cache:** po zalogowaniu jako użytkownik można wywołać `/api/cache/stats`.
- **Statystyki bazy:** endpoint `/api/database/stats` pokazuje informacje o poolu połączeń i stanie bazy.

## Interfejs i API

- UI dostępne po zalogowaniu: `/` (dashboard), `/automations`, `/edit`, `/admin_dashboard` (wymaga roli admin).
- Endpoints ułatwiające diagnostykę:
  - `/api/ping` – prosty health check.
  - `/api/status` – status aplikacji oraz informacja o trybie bazy.
  - `/api/cache/stats` – metryki pamięci podręcznej (po zalogowaniu).
  - `/api/database/stats` – metryki połączeń z bazą (po zalogowaniu).
- WebSockety (Socket.IO) obsługują m.in. zdarzenia `toggle_button`, `set_temperature`, `set_security_state`.

## Wskazówki i rozwiązywanie problemów

- **Połączenie z bazą:** sprawdź wartości `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. Przy błędach aplikacja zapisze szczegóły w konsoli i w razie potrzeby zadziała w trybie JSON.
- **Cache:** przy zmianach danych ręczne wywołanie invalidacji nie jest konieczne – `CacheManager` robi to automatycznie. W razie potrzeby można skorzystać z metod `invalidate_*` dostępnych w module.
- **Logi:** wpisy administracyjne zapisywane są przez `DatabaseManagementLogger` (tabela `management_logs`). W logach konsoli można znaleźć informacje o stanie cache, inicjalizacji komponentów oraz łączeniu z bazą.
- **Testy:** repozytorium nie zawiera obecnie pakietu testów automatycznych. Zalecane jest ręczne sprawdzenie kluczowych scenariuszy (logowanie, przełączanie urządzeń, dodawanie automatyzacji) po wdrożeniu.

## Gdzie szukać dalszych informacji

- `info/QUICK_START.md` – skrócona instrukcja uruchomienia i konfiguracji.
- `info/PERFORMANCE_OPTIMIZATION.md` – opis zastosowanych optymalizacji (cache, pre-loading, minifikacja).
- `backups/` – przykładowe kopie zapasowe, które ułatwiają start z gotową konfiguracją.

---

Jeśli napotkasz błąd lub masz pomysł na usprawnienie systemu, warto zacząć od logów w konsoli (`app_db.py`) oraz logów zarządzania dostępnych w panelu administratora.
