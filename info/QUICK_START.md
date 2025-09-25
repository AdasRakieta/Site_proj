# Szybki Start – SmartHome

Ten dokument opisuje najszybszą ścieżkę uruchomienia aplikacji wraz z bazą PostgreSQL i opcjonalnym cache Redis. Dla wygody wszystkie polecenia podane są w wersji PowerShell (Windows). 

## 1. Przygotowanie środowiska
1. **Klon repozytorium** i przejdź do katalogu z projektem.
2. **Utwórz wirtualne środowisko** i zainstaluj zależności:
   ```powershell
   python -m venv .venv
   . .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. (Opcjonalnie) Zainstaluj i uruchom Redis, jeśli chcesz korzystać z zewnętrznego cache.

## 2. Konfiguracja pliku `.env`
Utwórz w katalogu głównym plik `.env` – poniższy przykład można dostosować do własnego środowiska.
```env
# Serwer aplikacji
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

# Konfiguracja PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smart_home
DB_USER=smarthome
DB_PASSWORD=haslo
DB_POOL_MIN=2
DB_POOL_MAX=10

# Cache (opcjonalnie Redis)
REDIS_URL=redis://localhost:6379/0
# lub alternatywnie
# REDIS_HOST=localhost
# REDIS_PORT=6379

# Ustawienia maila (MailManager)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=twoj_email
SMTP_PASSWORD=haslo_aplikacyjne
ADMIN_EMAIL=admin@example.com
```
> Gdy połączenie z bazą nie powiedzie się (np. brak PostgreSQL), aplikacja automatycznie przełączy się na tryb plikowy JSON, dzięki czemu interfejs pozostaje dostępny do testów.

## 3. Przygotowanie bazy danych
1. Upewnij się, że PostgreSQL jest uruchomiony.
2. Utwórz bazę o nazwie podanej w `DB_NAME`.
3. Zastosuj schemat z kopii zapasowej:
   ```powershell
   psql -h localhost -U smarthome -d smart_home -f backups/db_backup.sql
   ```
   Skrypt tworzy wszystkie tabele oraz konto administratora. Po pierwszym logowaniu zmień domyślne hasło.

## 4. Minifikacja zasobów (opcjonalne)
Dla środowiska produkcyjnego warto zbudować zminifikowane wersje CSS/JS:
```powershell
python utils/asset_manager.py
```
W trybie deweloperskim możesz uruchomić tryb obserwacji:
```powershell
python utils/asset_manager.py --watch
```

## 5. Uruchamianie aplikacji
- **Tryb deweloperski** (Socket.IO + Flask):
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
Aplikacja będzie dostępna pod adresem `http://localhost:5000` (lub na porcie określonym w `.env`).

## 6. Kontrola działania
Po uruchomieniu zaloguj się kontem administratora utworzonym w skrypcie SQL. W panelu możesz sprawdzić logi urządzeń, automatyzacje i użytkowników.

Przydatne endpointy diagnostyczne (wymagają zalogowania jako użytkownik):
- `GET /api/cache/stats` – statystyki pamięci podręcznej (liczba trafień/missów, typ cache).
- `GET /api/database/stats` – status połączenia z bazą i konfiguracja puli.
- `GET /api/ping` lub `/api/status` – proste sprawdzenie, czy serwer działa.

## 7. Rozwiązywanie problemów
- **Błąd połączenia z bazą:** sprawdź wartości `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. W logach konsoli pojawią się komunikaty o ewentualnym przełączeniu na tryb JSON.
- **Brak Redis:** to nie błąd – aplikacja samoczynnie użyje `SimpleCache` i poinformuje o tym w logach startowych.
- **Assets bez minifikacji:** aplikacja serwuje oryginalne pliki, jeśli `.min.css`/`.min.js` nie istnieją.
- **Maile nie wychodzą:** upewnij się, że dane SMTP w `.env` są poprawne; w logach pojawią się informacje o próbie wysyłki.

Po wykonaniu powyższych kroków aplikacja jest gotowa do dalszej konfiguracji oraz rozbudowy (np. edycja automatyzacji, dodawanie urządzeń, integracja mobilna).