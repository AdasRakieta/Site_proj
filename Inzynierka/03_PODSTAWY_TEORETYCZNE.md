# Rozdział 3: Podstawy teoretyczne

Celem tego rozdziału jest przedstawienie podstaw teoretycznych stanowiących fundament projektu „SmartHome Multi-Home”. Rozdział porządkuje pojęcia, technologie i wzorce projektowe wykorzystane w implementacji systemu oraz uzasadnia ich wybór w kontekście wymagań funkcjonalnych i niefunkcjonalnych.

## 3.1. Technologie webowe

### 3.1.1. Framework Flask (Python)
Flask jest lekkim, modułowym frameworkiem do tworzenia aplikacji webowych w języku Python [11]. Jego architektura „microframework” oznacza, że dostarcza niezbędne elementy (routing, szablony, kontekst żądania), pozwalając jednocześnie na dobór bibliotek zewnętrznych dla bazy danych, sesji, cache czy uwierzytelniania.

Kluczowe cechy istotne dla systemu:
- Minimalizm i elastyczność (łatwa integracja z PostgreSQL/Redis/Socket.IO),
- Dobra czytelność kodu i niski próg wejścia,
- Dojrzały ekosystem rozszerzeń (Flask-SocketIO, Flask-Caching, itp.).

W projekcie zastosowano klasowy styl „managerów tras” (np. `RoutesManager`, `APIManager`) zamiast Blueprintów, aby uzyskać lepsze kapsułkowanie zależności (cache, auth, multi-home DB) i spójniejszy dostęp do kontekstu aplikacji (por. `app/routes.py`).

### 3.1.2. HTTP/HTTPS i REST
HTTP/1.1 oraz HTTP/2 stanowią podstawę komunikacji klient–serwer [24]. Interfejsy REST (Representational State Transfer) opierają się na identyfikacji zasobów (URI), operacjach CRUD mapowanych na metody HTTP (GET/POST/PUT/DELETE) oraz reprezentacjach (JSON) [1].

Dla systemu SmartHome REST służy do:
- zarządzania użytkownikami, domami, pokojami i urządzeniami,
- pobierania stanu oraz zmian konfiguracji,
- integracji z klientami (przeglądarka, automatyzacje, narzędzia administracyjne).

HTTPS zapewnia poufność i integralność danych w transporcie (TLS). W warstwie reverse proxy (Nginx) realizowana jest terminacja TLS oraz mechanizmy bezpieczeństwa nagłówków HTTP.

### 3.1.3. WebSocket i Socket.IO
WebSocket (RFC 6455) umożliwia dwukierunkową komunikację w czasie rzeczywistym między klientem i serwerem [22]. Socket.IO to biblioteka wysokopoziomowa, która oprócz WebSocket wspiera mechanizmy automatycznego ponownego łączenia, „rooms” i fallback do long-polling [17].

W projekcie:
- Flask-SocketIO obsługuje kanały zdarzeń; użytkownicy dołączają do pokojów `home_{home_id}`,
- aktualizacje stanu urządzeń emitowane są broadcastem do wszystkich klientów w danym domu,
- zdefiniowano wzorzec „event sourcing light” dla widoków – HTTP odpowiada za komendy, Socket.IO za natychmiastowe odświeżenia UI.

## 3.2. Bazy danych i model danych

### 3.2.1. PostgreSQL – baza relacyjna
PostgreSQL to dojrzały, transakcyjny RDBMS o pełnym wsparciu ACID i rozbudowanych możliwościach (indeksy złożone, partycjonowanie, typ `UUID`, `JSONB`) [13].

Uzasadnienie wyboru:
- naturalne odwzorowanie relacji: użytkownik–dom–członek–pokój–urządzenie,
- spójność i integralność referencyjna (FK, CHECK),
- wydajność dzięki indeksom i planom zapytań,
- elastyczność `JSONB` dla konfiguracji automatyzacji i historii.

Implementacja w projekcie jest scentralizowana w `utils/multi_home_db_manager.py` – pojedyncza warstwa dostępu do danych z kontrolą uprawnień per‑home, co zapobiega rozproszeniu SQL w kodzie i minimalizuje ryzyko błędów (SQL injection, brak izolacji). Wzorzec „Single Source of Truth” upraszcza konserwację i testy.

### 3.2.2. Projektowanie schematów i indeksowanie
Projekt ERD obejmuje m.in. tabele: `users`, `homes`, `user_homes`/`home_members`, `rooms`, `devices`, `automations`, `device_history`. Indeksy wspierają najczęstsze zapytania: listy urządzeń per dom, filtrowanie po typie urządzenia i sortowanie po `display_order` (zob. `04_ARCHITEKTURA_SYSTEMU.md`).

Zasady indeksowania stosowane w projekcie:
- indeksy na kluczach obcych (JOIN),
- indeksy złożone pod filtrację i sortowanie,
- indeksy częściowe dla często używanych warunków (np. `enabled = true`),
- „covering indexes” dla kwerend panelu.

### 3.2.3. Transakcje, spójność i migracje
Dostęp do bazy realizowany jest przez kursory w kontekście transakcji (commit/rollback). Migracje opisano jako skrypty DDL w katalogu `backups/` i wbudowane „ensure_*” w menedżerze DB, co pozwala na łagodne podnoszenie schematu na środowiskach rozwojowych.

## 3.3. Warstwa cache i strategie

### 3.3.1. Redis jako cache
Redis to in‑memory data store klasy Key‑Value, wykorzystywany w projekcie jako warstwa przyspieszająca dostęp do danych często czytanych [14]. W połączeniu z Flask‑Caching umożliwia:
- cache list pomieszczeń i urządzeń,
- cache konfiguracji i danych użytkownika,
- TTL per typ zasobu (zdefiniowane w `CacheManager`).

Strategie:
- „cache‑aside” – odczyt z cache, przy pudle pobranie ze źródła i zapis z TTL,
- „invalidate‑on‑write” – kasowanie kluczy po modyfikacjach (`update_device`, zmiany konfiguracji),
- klucze per home dla izolacji multi‑tenant.

Warstwa cache została zaimplementowana w `utils/cache_manager.py` oraz „podpięta” przez funkcję `setup_smart_home_caching`, która monkey‑patchuje wybrane metody, gwarantując spójność bez zmiany publicznego API menedżerów.

### 3.3.2. Odporność i degradacja
System zapewnia „graceful degradation”: przy braku Redis mechanizmy spadają do `SimpleCache`. Zgodnie z NFR dostępność i wydajność nie powinny ulec dramatycznemu pogorszeniu, a konsystencja danych pozostaje zachowana (źródłem prawdy jest PostgreSQL).

## 3.4. Architektura aplikacji webowych

### 3.4.1. MVC i warstwowość
Zastosowano architekturę wielowarstwową: reverse proxy (Nginx) → aplikacja (Flask/Socket.IO) → dane (PostgreSQL/Redis). Warstwa aplikacji dzieli się na menedżery tras (HTTP/WS), logikę biznesową (SmartHomeSystemDB, MultiHomeDBManager, CacheManager, AuthManager) oraz warstwy pomocnicze (mail, asset, async).

### 3.4.2. Wzorce projektowe
- Manager Pattern (rejestracja tras i handlerów),
- Singleton (SmartHomeSystemDB),
- Strategy (wybór backendu cache),
- Factory (tworzenie wyspecjalizowanych menedżerów),
- Decorator (cache JSON responses, wymagania autoryzacyjne).

## 3.5. Konteneryzacja i inżynieria wdrożeń

### 3.5.1. Docker i Docker Compose
Docker umożliwia izolację środowiska uruchomieniowego i reprodukowalność buildów [15]. Zastosowano „multi‑stage build” dla obrazu aplikacji (mniejszy rozmiar i brak kompilatorów w warstwie runtime) oraz osobny obraz Nginx. `docker-compose.prod.yml` definiuje orkiestrację usług: app, nginx, postgres, redis.

### 3.5.2. Nginx jako reverse proxy
Nginx odpowiada za terminację TLS, serwowanie statyk, ochronę i buforowanie. Konfiguracja zawiera sekcję WebSocket (`/socket.io/`) z odpowiednimi nagłówkami i timeoutami. Zastosowano nagłówki bezpieczeństwa i Gzip.

### 3.5.3. CI/CD
GitHub Actions realizuje pipeline: checkout → buildx → login → build → push do GHCR → artifact z podsumowaniem. Osobny workflow uruchamia testy i zapewnia szybki feedback deweloperski [32].

## 3.6. Internet Rzeczy (IoT) – kontekst
System koncentruje się na warstwie zarządzania i prezentacji, abstrahując warstwę komunikacji z urządzeniami. Integracje (np. TinyTuya, MQTT) są projektowane jako rozszerzenia logiki, a stany urządzeń są utrwalane w DB i propagowane w UI przez Socket.IO. Taki podział umożliwia testowanie bez sprzętu oraz wymianę adapterów urządzeń bez ingerencji w UI.

## 3.7. Bezpieczeństwo – wprowadzenie

### 3.7.1. Uwierzytelnianie i autoryzacja
- Haszowanie haseł algorytmem bcrypt (cost ≥ 12),
- Sesje HTTP‑Only, SameSite, z czasem życia (24h),
- Kontrola dostępu w oparciu o role (RBAC): `owner`, `admin`, `member/guest`, `sys‑admin` (globalnie),
- Dekoratory `login_required`, `admin_required`, `owner_required` powiązane z `multi_db.has_admin_access`.

### 3.7.2. Ochrona aplikacyjna
- CSRF protection dla formularzy,
- Walidacja danych wejściowych i parametryzacja zapytań SQL,
- Zasady minimalizacji uprawnień oraz izolacja home w każdej kwerendzie DB,
- Zasady cache’owania bez danych wrażliwych oraz bezpieczna invalidacja.

Szczegółowe omówienie zawiera rozdział 7.

## 3.8. Podsumowanie
Przedstawione podstawy teoretyczne uzasadniają dobór technologii i wzorców pod wymagania systemu: real‑time, multi‑tenant, bezpieczeństwo, wydajność i łatwość utrzymania. Flask + PostgreSQL + Redis + Socket.IO + Docker tworzą spójny, produkcyjny stack dla nowoczesnej aplikacji zarządzającej inteligentnym domem.

---

Bibliografia: [1], [11], [13]–[15], [17], [21]–[25], [32]
