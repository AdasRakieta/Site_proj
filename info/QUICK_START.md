
# Szybki Start - SmartHome

## 1. Przygotowanie środowiska
- Skopiuj plik `.env` i uzupełnij dane do bazy oraz emaila.
- Zainstaluj zależności:
  ```bash
  pip install -r info/requirements.txt
  ```

## 2. Minifikacja zasobów (CSS/JS)
- Dla produkcji:
  ```bash
  python utils/asset_manager.py
  ```
- Dla rozwoju (auto-watch):
  ```bash
  python utils/asset_manager.py --watch
  ```

## 3. Migracja danych (jeśli to nowa baza)
  ```bash
  python run_database_migration.py full
  ```

## 4. Uruchamianie aplikacji
- **Windows (Waitress):**
  ```cmd
  run_server_windows.bat
  ```
- **Linux (Gunicorn):**
  ```bash
  bash run_server_linux.sh
  ```

## 5. Dostęp do aplikacji
- Domyślnie: http://localhost:5001

## 6. Optymalizacja
- Szczegóły: patrz `PERFORMANCE_OPTIMIZATION.md`