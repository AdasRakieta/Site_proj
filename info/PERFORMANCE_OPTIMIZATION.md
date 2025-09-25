# Optymalizacje Wydajności – SmartHome

Dokument zbiera najważniejsze rozwiązania wpływające na wydajność aplikacji w jej aktualnej wersji. Wszystkie opisane mechanizmy znajdują się w repozytorium i są aktywne po standardowym uruchomieniu `app_db.py`.

## 1. Warstwa danych i cache
- **PostgreSQL + Connection Pool** – `utils/smart_home_db_manager.py` korzysta z `ThreadedConnectionPool` (parametry sterowane przez `DB_POOL_MIN` / `DB_POOL_MAX`). Gdy inicjalizacja bazy się nie powiedzie, aplikacja informuje w logach i przełącza się na backend JSON.
- **CacheManager** – `utils/cache_manager.py` udostępnia cache dla użytkowników, pokoi, urządzeń, automatyzacji oraz sesji. Domyślnie wykorzystywany jest Redis (jeśli skonfigurowany), a w przeciwnym razie `SimpleCache`. Statystyki dostępne są pod `GET /api/cache/stats`.
- **Wstępne ocieplenie cache** – podczas startu `SmartHomeApp` wywołuje `_warm_up_cache`, który ładuje do cache listy pokoi, przycisków, sterowników temperatury i automatyzacji.

## 2. Szybkie renderowanie widoków
- **Pre-loading danych w szablonach** – w `routes.py` kluczowe widoki (`index`, `admin_dashboard`, `automations`) renderują dane jeszcze przed załadowaniem klienta. Skrypty JS wykorzystują je przy pierwszym wejściu i wykonują zapytania AJAX dopiero przy odświeżeniu.
- **Kanban/edytor urządzeń** – `CachedDataAccess` dostarcza filtrowanie urządzeń per pokój, redukując liczbę bezpośrednich zapytań do bazy.

## 3. Reakcja w czasie rzeczywistym
- **Socket.IO** – zdarzenia `toggle_button`, `set_temperature`, `set_security_state` aktualizują stan urządzeń w bazie i jednocześnie wysyłają broadcast do wszystkich klientów. 
- **Invalidacja cache po akcjach** – w handlerach Socket.IO usuwane są klucze cache dla zmodyfikowanych danych (`buttons_list`, `buttons_room_<room>`, `temp_controls_room_<room>` itp.).
- **Redukcja hałasu logów** – `SmartHomeApp._configure_logging()` ustawia poziom logowania dla `geventwebsocket`, `engineio`, `socketio` i `werkzeug` na `WARNING`, dzięki czemu logi koncentrują się na realnych problemach.

## 4. Obsługa zadań w tle
- **AsyncMailManager** – `utils/async_manager.py` przenosi wysyłkę maili i inne zadania niekrytyczne do wątków roboczych, co skraca czas odpowiedzi HTTP.
- **Management logger** – `app/database_management_logger.py` zapisuje operacje administracyjne w bazie. W przypadku błędu automatycznie wybierana jest wersja plikowa `ManagementLogger`.

## 5. Zasoby statyczne
- **Minifikacja CSS/JS** – `utils/asset_manager.py` generuje pliki `.min.css` i `.min.js`. Aplikacja automatycznie serwuje wersje zminifikowane, jeśli istnieją. Tryb `--watch` pozwala utrzymać optymalizacje podczas pracy deweloperskiej.
- **Wersjonowanie zasobów** – context processor `inject_asset_version` w `routes.py` dodaje parametr wersji oparty o zmienne środowiskowe (`ASSET_VERSION`/`IMAGE_TAG`), ułatwiając busting cache przeglądarki.

## 6. Jak monitorować efekty
- **Logi startowe** – `app_db.py` wyświetla informacje o trybie pracy (PostgreSQL/JSON), użytym cache oraz wyniku testu połączenia z bazą.
- **Endpointy diagnostyczne**:
  - `GET /api/cache/stats` – sprawdza trafienia/missy cache.
  - `GET /api/database/stats` – potwierdza aktywność puli połączeń i zbiera statystyki z `SmartHomeSystemDB`.
  - `GET /api/ping` lub `/api/status` – proste sprawdzenie dostępności serwera.
- **Konsola przeglądarki** – w widokach admina logowane są komunikaty o użyciu pre-loaded data; brak dodatkowych zapytań przy pierwszym wejściu oznacza, że optymalizacje działają poprawnie.

## 7. Rekomendacje operacyjne
- **Przed wdrożeniem** uruchom `python utils/asset_manager.py`, aby wygenerować zminifikowane zasoby.
- **Monitoruj rozmiar cache Redis** – w środowiskach produkcyjnych warto ustawić TTL zgodnie z potrzebami oraz obserwować statystyki (np. `redis-cli info`).
- **Analizuj logi zarządzania** – panel admina wykorzystuje dane z bazy do prezentacji ostatnich działań; to szybki sposób na wychwycenie problematycznych akcji użytkowników.

Zastosowanie powyższych mechanizmów zapewnia szybkie ładowanie widoków (szczególnie dashboardu administratora), ogranicza obciążenie bazy i utrzymuje płynną komunikację z klientami czasu rzeczywistego.