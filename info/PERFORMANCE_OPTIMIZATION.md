**Uruchamianie produkcyjne:**
- Windows: `python -m waitress --port=5001 app_db:main`
- Linux: `gunicorn -w 4 -b 0.0.0.0:5001 'app_db:main'`

# Site_proj - Dokumentacja Optymalizacji Wydajności

**Szybki start i uruchamianie produkcyjne opisane w `QUICK_START.md`.**

Ten dokument opisuje optymalizacje wydajności zaimplementowane dla aplikacji smart home Site_proj, w tym najnowsze optymalizacje pre-loaded data dla admin dashboard.

## 📊 Najnowsze Optymalizacje

### Template-Level Pre-loading (Admin Dashboard)
**Status**: ✅ Zaimplementowane i naprawione
**Czas ładowania**: Zmniejszony z ~2.6s do ~0.87s (**70% poprawa**)

**Szczegóły implementacji**:
- **Pre-loaded Data**: Dane użytkowników, device states i management logs są ładowane na serwerze
- **Template Variables**: `window.preloadedUsers`, `window.preloadedDeviceStates`, `window.preloadedManagementLogs`
- **JavaScript Override Pattern**: Funkcje `loadUsers()`, `refreshDeviceStates()`, `refreshLogs()` używają pre-loaded data przy pierwszym ładowaniu
- **Smart Initialization**: Kontrolowane uruchamianie `initDashboardPage()` aby prevent duplicate API calls
- **Fallback System**: Automatyczny fallback do API calls dla manual refresh operations

**Rozwiązane problemy**:
- ❌ **Duplicate API calls**: Eliminated multiple `/api/users` requests during page load  
- ❌ **Conflicting initialization**: Fixed dashboard.js auto-initialization interference
- ❌ **Slow static file loading**: Improved cache headers i asset delivery
- ✅ **Result**: Single page load w <1 sekunda z pre-loaded data consumption

### Homepage Pre-loading
**Status**: ✅ Zaimplementowane w `templates/index.html`

- **Pre-loaded Rooms**: `const preloadedRooms = {{ rooms|tojson }};`
- **Eliminuje**: Początkowy AJAX call do `/api/rooms`
- **Poprawa**: Natychmiastowe renderowanie pokoi

## 📁 Struktura Plików

### Główne Pliki Aplikacji
- `app_db.py` - Główna aplikacja Flask z PostgreSQL backend
- `app/routes.py` - Trasy i endpointy z pre-loading optimization
- `app/configure_db.py` - System SmartHome z database backend
- `app/database_management_logger.py` - Database-backed logging system

### Zoptymalizowane Templates
- `templates/admin_dashboard.html` - Admin dashboard z pre-loaded data optimization
- `templates/index.html` - Homepage z pre-loaded rooms
- `templates/base.html` - Base template z responsive design

### Katalog Utils (`utils/`)
Katalog `utils/` zawiera zorganizowane moduły narzędziowe dla optymalizacji wydajności:

#### `utils/smart_home_db_manager.py`
**Cel**: PostgreSQL database manager z connection pooling

**Funkcje**:
- ThreadedConnectionPool (2-10 connections, configurable)
- Database operations dla users, rooms, devices, automations
- Automatic connection management i error handling
- Environment variables: `DB_POOL_MIN`, `DB_POOL_MAX`

**Klasy**:
- `SmartHomeDatabaseManager` - Core database operations
- `DatabaseError` - Custom exception handling

#### `utils/cache_manager.py`
**Cel**: Kompleksowa funkcjonalność cachowania dla poprawy wydajności aplikacji

**Funkcje**:
- Integracja Redis/SimpleCache przez Flask-Caching
- Automatyczna invalidacja cache przy aktualizacji danych
- Warstwa dostępu do danych cache dla encji smart home
- Dekoratory cachowania odpowiedzi API
- Zarządzanie cache specyficznym dla użytkownika
- Session-level caching z `get_session_user_data()`

**Klasy**:
- `CacheManager` - Centralne zarządzanie cache z ujednoliconym interfejsem
- `CachedDataAccess` - Dostęp z cache do pokoi, przycisków, kontrolek temperatury, automatyzacji
- `setup_smart_home_caching()` - Automatyczna integracja cache z SmartHomeSystem

**Typy Cache i Timeouty**:
- Dane użytkownika: 30 minut (1800s)
- Session user data: 1 godzina (3600s)
- Konfiguracja: 15 minut (900s)
- Pokoje/Przyciski: 10 minut (600s)
- Kontrolki temperatury: 5 minut (300s)
- Automatyzacje: 5 minut (300s)
- Odpowiedzi API: 10 minut (600s)

#### `utils/async_manager.py`
**Cel**: Operacje asynchroniczne dla nieblokującego doświadczenia użytkownika

**Funkcje**:
- Asynchroniczne wysyłanie emaili z przetwarzaniem opartym na kolejce
- Zarządzanie zadaniami w tle dla operacji niekrytycznych
- Operacje kolejki bezpieczne dla wątków
- Graceful degradation do operacji synchronicznych w przypadku awarii
- Kompleksowa obsługa błędów i logowanie

**Klasy**:
- `AsyncMailManager` - Nieblokujące operacje email z wątkami roboczymi
- `BackgroundTaskManager` - Wykonywanie zadań w tle z pulą wątków

**Operacje Email**:
- Emaile weryfikacyjne → `send_verification_email_async()`
- Alerty bezpieczeństwa → `send_security_alert_async()`
- Powiadomienia o nieudanych logowaniach → `track_and_alert_failed_login_async()`


#### `utils/asset_manager.py`
**Cel**: Minifikacja CSS/JS i optymalizacja zasobów

**Jak używać:**
- Produkcja: `python utils/asset_manager.py`
- Rozwój: `python utils/asset_manager.py --watch`

**Efekty:**
- Pliki .min.js/.min.css generowane automatycznie do folderów static/js/min, static/css/min

**Nie edytuj ręcznie plików .min!**

**Funkcje**:
- Automatyczna minifikacja CSS/JS ze statystykami kompresji
- Inteligentne serwowanie zminifikowanych zasobów (fallback do oryginału jeśli niedostępne)
- Tryb obserwacji dla automatycznej re-minifikacji podczas rozwoju
- Integracja z buildem dla wdrożeń produkcyjnych

**Klasy**:
- `AssetManager` - Główny silnik minifikacji i optymalizacji
- `AssetWatcher` - Obserwator systemu plików dla trybu deweloperskiego
- `minified_url_for_helper()` - Helper szablonów Flask dla automatycznego serwowania zasobów

### Pliki Legacy (do wyczyszczenia)
- `cache_helpers.py` - Oryginalna implementacja cache (zastąpiona przez `utils/cache_manager.py`)
- `async_mail_manager.py` - Oryginalna implementacja async (zastąpiona przez `utils/async_manager.py`)
- `minify_assets.py` - Oryginalny skrypt minifikacji (zastąpiony przez `utils/asset_manager.py`)
- `app.py` - Oryginalna aplikacja (zastąpiona przez `app_db.py`)
- `configure.py` - JSON-based config (zastąpiony przez `configure_db.py`)

## 🚀 Przegląd Optymalizacji

### 1. Database Backend Migration
**Cel**: Zastąpienie JSON file storage z PostgreSQL database
**Status**: ✅ Zaimplementowane
**Korzyści**: 
- Lepsze concurrent access handling
- Transactional data integrity
- Connection pooling dla performance
- Structured data queries z indexing

### 2. Template-Level Pre-loading
**Cel**: Eliminacja AJAX calls przy pierwszym ładowaniu strony
**Status**: ✅ Zaimplementowane w admin dashboard i homepage
**Korzyści**:
- Admin dashboard: 70% poprawa czasu ładowania (2.6s → 0.87s)
- Homepage: Natychmiastowe renderowanie pokoi
- Redukcja database queries o 60-80% przy page load

### 3. JavaScript Function Override Pattern
**Cel**: Smart fallback między pre-loaded data a API calls
**Status**: ✅ Zaimplementowane
**Implementacja**:
```javascript
// Override pattern w admin_dashboard.html
function loadUsers(forceRefresh = false) {
    if (!forceRefresh && window.preloadedUsers && window.preloadedUsers.length > 0) {
        // Use pre-loaded data
        updateUsersTable(window.preloadedUsers);
        window.preloadedUsers = null; // Clear to prevent reuse
        return;
    }
    // Fallback to API call
    originalLoadUsers();
}
```

### 4. Minifikacja CSS/JS

**Pliki**: Pliki oryginalne (edytowalne) → Pliki zminifikowane (auto-generowane)

```
static/css/style.css      → static/css/min/style.min.css      (36.7% mniejsze)
static/js/app.js          → static/js/min/app.min.js          (35.3% mniejsze)
```

**Proces**:
- **RĘCZNIE**: Edytuj oryginalne pliki (`style.css`, `app.js`, itp.)
- **AUTOMATYCZNIE**: Uruchom skrypt minifikacji aby wygenerować pliki `.min.css` i `.min.js`
- **SERWOWANIE**: Aplikacja automatycznie serwuje zminifikowane wersje gdy dostępne

**Komendy Użycia**:
```bash
# Jednorazowa minifikacja
python utils/asset_manager.py

# Tryb deweloperski z auto-minifikacją
python utils/asset_manager.py --watch

# Wyczyść i regeneruj wszystkie zminifikowane zasoby
python utils/asset_manager.py --clean

# Szczegółowe wyjście
python utils/asset_manager.py --verbose
```

**Proces Aktualizacji Plików**:
1. Edytujesz `static/css/style.css` (lub dowolny oryginalny plik CSS/JS)
2. Uruchamiasz `python utils/asset_manager.py` aby wygenerować `static/css/min/style.min.css`
3. Aplikacja automatycznie serwuje zminifikowaną wersję
4. Brak konieczności ręcznej interwencji dla serwowania zasobów

### 2. System Cachowania

**Implementacja**: Lokalny SimpleCache (kompatybilny z Redis)

**Dane Cachowane**:
- Informacje o użytkownikach (TTL 10 min)
- Konfiguracja smart home (TTL 5 min)
- Pokoje i przyciski (TTL 5 min)
- Kontrolki temperatury (TTL 10 min)
- Automatyzacje (TTL 5 min)
- Odpowiedzi API (TTL 5 min)

**Funkcje**:
- Automatyczna invalidacja cache przy aktualizacji danych
- Przezroczyste cachowanie - brak potrzeby zmian w kodzie
- Statystyki cache i monitoring
- Graceful degradation jeśli cache zawiedzie

### 3. Operacje Asynchroniczne

**Implementacja**: Przetwarzanie w tle oparte na kolejce

**Operacje Async**:
- Wysyłanie emaili (weryfikacja, alerty)
- Powiadomienia bezpieczeństwa
- Śledzenie nieudanych logowań
- Zapisywanie konfiguracji w tle

**Korzyści**:
- Natychmiastowa odpowiedź UI (brak czekania na dostarczenie emaila)
- Lepsze doświadczenie użytkownika
- Poprawiona responsywność aplikacji
- Automatyczne ponowienie przy awarii

## 🛠️ Instrukcje Użycia

### Dla Deweloperów

#### Uruchamianie Aplikacji
```bash
# Uruchom z PostgreSQL backend
python app_db.py

# Sprawdź status połączenia z bazą danych
# Sprawdź logi startowe dla connection pool status
```

#### Template Pre-loading (Development)
```bash
# Admin dashboard automatycznie używa pre-loaded data
# Sprawdź console.log w DevTools dla confirmation:
# "Using pre-loaded users data"
# "Using pre-loaded device states data"
# "Using pre-loaded management logs data"

# Do debugowania performance:
# 1. Otwórz DevTools → Network tab
# 2. Załaduj /admin_dashboard
# 3. Sprawdź że nie ma redundant /api/users calls
# 4. Page load powinien być < 1 sekunda
```

#### Zarządzanie Zasobami
```bash
# Podczas rozwoju - obserwuj zmiany i auto-minifikuj
python utils/asset_manager.py --watch

# Przed wdrożeniem - zminifikuj wszystkie zasoby
python utils/asset_manager.py
```

#### Database Operations
```bash
# Environment variables dla database connection:
export DB_HOST="localhost"
export DB_PORT="5432"  
export DB_NAME="smart_home"
export DB_USER="username"
export DB_PASSWORD="password"

# Connection pool configuration:
export DB_POOL_MIN="2"    # Minimum connections
export DB_POOL_MAX="10"   # Maximum connections

# Cache configuration (optional Redis):
export REDIS_URL="redis://localhost:6379/0"
# lub:
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
```

#### Performance Monitoring
```bash
# Sprawdź cache statistics:
curl http://localhost:5000/api/cache/stats

# Sprawdź database connection status:
curl http://localhost:5000/api/database/stats

# Run performance test:
python test_performance.py

# Run cache comparison:
python performance_comparison.py
```

#### Workflow Edycji Plików
1. Edytuj oryginalne pliki w `static/css/` i `static/js/`
2. Zminifikowane pliki są automatycznie generowane gdy uruchamiasz asset manager
3. Aplikacja automatycznie serwuje zoptymalizowane wersje
4. **Brak potrzeby ręcznej aktualizacji zminifikowanych plików**

#### Zarządzanie Cache
```python
# Cache jest automatycznie zarządzany, ale możesz z nim współpracować:
from utils.cache_manager import CacheManager

# Ręczna invalidacja cache
cache_manager.invalidate_config_cache()
cache_manager.invalidate_user_cache(user_id)

# Statystyki cache
stats = cache_manager.get_statistics()
```

#### Operacje Async
```python
# Operacje email są automatycznie async w trasach logowania
# Ale możesz ich użyć ręcznie:
async_mail_manager.send_verification_email_async(email, code)
async_mail_manager.send_security_alert_async(event_type, details)
```

### Dla Wdrożenia Produkcyjnego

1. **Skonfiguruj environment variables**:
   ```bash
   # Database
   export DB_HOST="production_host"
   export DB_NAME="smart_home_prod"
   export DB_USER="prod_user"
   export DB_PASSWORD="secure_password"
   export DB_POOL_MIN="5"
   export DB_POOL_MAX="20"
   
   # Cache (jeśli używasz Redis)
   export REDIS_URL="redis://production_redis:6379/0"
   ```

2. **Zbuduj zasoby**:
   ```bash
   python utils/asset_manager.py
   ```

3. **Uruchom aplikację**:
   ```bash
   # Windows (Waitress)
   python -m waitress --port=5001 app_db:main
   
   # Linux (Gunicorn)
   gunicorn -w 4 -b 0.0.0.0:5001 'app_db:main'
   ```

4. **Monitoruj wydajność**:
   - Sprawdź współczynniki trafień cache w logach aplikacji
   - Monitoruj connection pool usage w database logs
   - Sprawdź że pre-loaded data optimization działa (brak redundant API calls)
   - Zweryfikuj że zminifikowane zasoby są serwowane

## 🔧 Debugging i Troubleshooting

### Performance Issues
```bash
# Sprawdź page load times w Network tab DevTools
# Admin dashboard powinien ładować się < 1 sekunda

# Sprawdź console logs dla pre-loading:
# "Using pre-loaded users data" - OK
# "Fetching users from API" - Problem z pre-loading

# Sprawdź cache hit rate:
curl http://localhost:5000/api/cache/stats
# hit_rate_percentage powinno być > 80%
```

### Database Issues
```bash
# Sprawdź connection pool status w startup logs:
# "✓ Connection pool initialized with X-Y connections" - OK
# "⚠ Failed to initialize connection pool" - Problem

# Test database connectivity:
# App startup powinien pokazać "Database connection test successful"
```

### Template Pre-loading Debugging
```bash
# Sprawdź że template variables są correctly set:
# Otwórz DevTools → Console
# Sprawdź: window.preloadedUsers, window.preloadedDeviceStates, etc.
# Powinny zawierać data objects, nie undefined
```

## 📊 Korzyści Wydajnościowe

### Template-Level Pre-loading (Najnowsze Optymalizacje)
- **Admin Dashboard**: 70% poprawa czasu ładowania (2.6s → 0.87s)
- **Homepage**: Natychmiastowe renderowanie pokoi (eliminacja AJAX delay)
- **Database Queries**: 60-80% redukcja przy page load
- **User Experience**: Eliminacja loading indicators dla podstawowych danych

### Database Migration Benefits
- **PostgreSQL Backend**: Zastąpienie JSON file storage
- **Connection Pooling**: 2-10 concurrent connections
- **Data Integrity**: Transactional operations z rollback support
- **Query Performance**: Database indexing i optimized queries

### Optymalizacja Zasobów
- **CSS**: 36.7% redukcji rozmiaru
- **JS**: 35.3% redukcji rozmiaru
- **Łącznie**: 109KB mniej transferu danych
- **Rezultat**: Szybsze ładowanie stron, zmniejszone użycie przepustowości

### Korzyści Cachowania
- **Session-level User Data**: 95% redukcja database queries dla aktywnych użytkowników
- **API Responses**: Natychmiastowa odpowiedź dla danych z cache (< 1ms vs 50-200ms)
- **Room/Device Data**: 80% mniej database calls dla często accessed data
- **Overall Performance**: 2500-10000x improvement dla cached data

### Operacje Async
- **Wysyłanie emaili**: Nieblokujące (natychmiastowa odpowiedź UI)
- **Zadania w tle**: Poprawiona responsywność
- **Doświadczenie użytkownika**: Brak czekania na wolne operacje

## 🔧 Konfiguracja

### Konfiguracja Cache (app.py)
```python
app.config['CACHE_TYPE'] = 'SimpleCache'  # lub 'RedisCache'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
```

### Konfiguracja Asset Manager
Edytuj wartości timeout w `utils/cache_manager.py`:
```python
self._cache_timeouts = {
    'user_data': 600,       # 10 minut
    'config': 300,          # 5 minut
    'rooms': 300,           # 5 minut
    # ... itp
}
```

## 🧪 Testowanie

### Weryfikacja Minifikacji
```bash
# Sprawdź czy zminifikowane pliki istnieją
ls static/css/min/*.min.css
ls static/js/min/*.min.js

# Testuj serwowanie zasobów
curl -I http://localhost:5000/static/css/style.css
# Powinno serwować css/min/style.min.css jeśli dostępny
```

### Weryfikacja Cachowania
```bash
# Pierwsze żądanie (cache miss)
curl http://localhost:5000/api/rooms

# Drugie żądanie (cache hit - powinno być szybsze)
curl http://localhost:5000/api/rooms
```

### Weryfikacja Operacji Async
```bash
# Testuj async email (powinno zwrócić natychmiast)
curl -X POST http://localhost:5000/send-test-email
# Sprawdź logi dla przetwarzania emaila w tle
```

## 🚨 Ważne Uwagi

### Workflow Aktualizacji Plików
- **Edytuj**: Oryginalne pliki (`style.css`, `app.js`)
- **Generuj**: Zminifikowane pliki używając `python utils/asset_manager.py`
- **Serwuj**: Aplikacja automatycznie używa zminifikowanych wersji
- **NIE**: Nie edytuj ręcznie plików `.min.css` lub `.min.js`

### Invalidacja Cache
- Cache jest automatycznie invalidowany przy aktualizacji danych
- Ręczna invalidacja dostępna przez metody CacheManager
- Używany lokalny SimpleCache dla prostoty (kompatybilny z Redis)

### Operacje Async
- Wszystkie operacje email są automatycznie async
- Graceful degradation do trybu sync przy błędach
- Zadania w tle są przetwarzane przez pulę wątków

### Rozwój vs Produkcja
- **Rozwój**: Użyj trybu `--watch` dla automatycznej regeneracji zasobów
- **Produkcja**: Uruchom minifikację raz przed wdrożeniem
- **Monitoring**: Sprawdź logi dla trafień cache i statystyk operacji async

## 🛡️ Kompatybilność Wsteczna

Wszystkie optymalizacje zachowują 100% kompatybilności wstecznej:
- Oryginalna funkcjonalność zachowana 1:1
- Mechanizmy fallback dla wszystkich optymalizacji
- Brak zmian w istniejącym API lub interfejsie użytkownika
- Bezpieczne wyłączenie optymalizacji bez psucia funkcjonalności