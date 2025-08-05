
# Szybki Start - SmartHome

## 1. Przygotowanie środowiska
- Skopiuj plik `.env` i uzupełnij dane do bazy oraz emaila:
  ```bash
  # Database Configuration (PostgreSQL)
  DB_HOST=localhost
  DB_PORT=5432
  DB_NAME=smart_home
  DB_USER=your_username
  DB_PASSWORD=your_password
  
  # Connection Pool Settings
  DB_POOL_MIN=2
  DB_POOL_MAX=10
  
  # Cache Configuration (optional Redis)
  REDIS_URL=redis://localhost:6379/0
  # lub:
  REDIS_HOST=localhost
  REDIS_PORT=6379
  
  # Email Configuration
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USERNAME=your-email@gmail.com
  SMTP_PASSWORD=your-app-password
  ADMIN_EMAIL=admin@example.com
  ```

- Zainstaluj zależności:
  ```bash
  pip install -r info/requirements.txt
  ```

## 2. Konfiguracja bazy danych
- Upewnij się że PostgreSQL jest uruchomiony
- Stwórz bazę danych o nazwie określonej w `DB_NAME`
- Sprawdź połączenie uruchamiając aplikację (powinien pojawić się komunikat "Database connection test successful")

## 3. Migracja danych (jeśli to nowa instalacja)
  ```bash
  python run_database_migration.py full
  ```

## 4. Minifikacja zasobów (CSS/JS)
- Dla produkcji:
  ```bash
  python utils/asset_manager.py
  ```
- Dla rozwoju (auto-watch):
  ```bash
  python utils/asset_manager.py --watch
  ```

## 5. Uruchamianie aplikacji
- **Tryb rozwojowy (development):**
  ```bash
  python app_db.py
  ```
  
- **Tryb produkcyjny (Waitress, Windows):**
  ```bash
  python -m waitress --port=5001 app_db:main
  ```
- **Tryb produkcyjny (Gunicorn, Linux):**
  ```bash
  gunicorn -w 4 -b 0.0.0.0:5001 'app_db:main'
  ```

## 6. Dostęp do aplikacji
- Domyślnie: http://localhost:5000 (development) lub http://localhost:5001 (production)
- Admin dashboard: http://localhost:5000/admin_dashboard (po zalogowaniu jako admin)

## 7. Weryfikacja optymalizacji
- **Admin Dashboard Performance**: Czas ładowania powinien być < 1 sekunda
- **Cache Hit Rate**: Sprawdź `curl http://localhost:5000/api/cache/stats` (powinno być > 80%)
- **Database Connection Pool**: Sprawdź startup logs dla "Connection pool initialized"
- **Pre-loaded Data**: Sprawdź DevTools Console dla komunikatów "Using pre-loaded ... data"

## 8. Troubleshooting

### Android App - Gradle Problem
**Error**: `JVM runtime version 11 required, but using Java 8`

**Fix**: Już naprawione w projekcie - używamy Gradle 8.0.2 kompatybilne z Java 8
- `android_app/build.gradle`: Android Gradle Plugin 8.0.2
- `android_app/gradle/wrapper/gradle-wrapper.properties`: Gradle 8.0.2

### Performance Issues
- **Wolny admin dashboard**: Sprawdź console logs dla "Using pre-loaded data"
- **Database errors**: Zweryfikuj PostgreSQL connection i environment variables
- **Cache miss**: Sprawdź Redis/SimpleCache configuration

## 9. Optymalizacja
- Szczegóły: patrz `PERFORMANCE_OPTIMIZATION.md`