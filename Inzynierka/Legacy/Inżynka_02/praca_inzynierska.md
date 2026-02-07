# Praca inżynierska
## Tytuł
Projekt systemu inteligentnego domu (Smart Home System) — analiza, implementacja i testowanie

## Autor
[Twoje Imię i Nazwisko]

## Promotor
[Imię i Nazwisko Promotora]

## Streszczenie
Praca opisuje projekt i implementację systemu Smart Home opartego na aplikacji webowej z komponentami czasu rzeczywistego. System umożliwia zarządzanie urządzeniami, automatyzacjami i użytkownikami w wielu domach. Praca obejmuje analizę wymagań, projekt architektury, szczegóły implementacyjne, testy oraz instrukcję użytkownika i wdrożenia.

## Słowa kluczowe
Smart Home, Flask, Socket.IO, PostgreSQL, UML, automatyzacje, architektura wielowarstwowa

---

**Spis treści**

1. Wstęp
2. Analiza wymagań
3. Projekt systemu (architektura)
4. Implementacja
5. Diagramy UML i architektury
6. Testowanie
7. Instrukcja użytkownika i wdrożenie
8. Bezpieczeństwo i prywatność
9. Wnioski i prace przyszłe
10. Bibliografia
11. Załączniki (schematy bazy, pliki konfiguracyjne)

---

## 1. Wstęp

1.1 Cel pracy

Przedmiotem pracy jest zaprojektowanie i szczegółowe opisanie systemu Smart Home, włączając w to analizę wymagań, projekt architektury, implementację modułów oraz testy. System wspiera multi-home (wiele domów), komunikację w czasie rzeczywistym i mechanizmy automatyzacji.

1.2 Zakres pracy

Praca obejmuje projektowanie architektury, implementację backendu oraz opis integracji z bazą danych, mechanizmami cache i komunikacją w czasie rzeczywistym. Nie obejmuje natomiast projektu fizycznych urządzeń (hardware).

## 2. Analiza wymagań

2.1 Wymagania funkcjonalne

- Logowanie i zarządzanie kontami użytkowników.
- Zarządzanie wieloma domami i przypisywanie użytkowników do domów.
- Zdalne sterowanie urządzeniami (przełączniki, termostaty).
- Tworzenie i zarządzanie automatyzacjami (reguły: warunek → akcja).
- Panel administracyjny z logami i metrykami.

2.2 Wymagania niefunkcjonalne

- Niezawodność i spójność danych (PostgreSQL jako źródło prawdy, fallback JSON).
- Wydajność w czasie rzeczywistym (Socket.IO dla push updates).
- Skalowalność (możliwość uruchomienia w kontenerach Docker, użycie Redis dla cache).

2.3 Ograniczenia i założenia

- System zakłada istnienie sieci oraz serwera aplikacyjnego. Urządzenia są reprezentowane w systemie poprzez API.

## 3. Projekt systemu (architektura)

3.1 Warstwowa architektura

Architektura systemu składa się z następujących warstw:

- Warstwa prezentacji (templates + statyczne assets w `templates/`, `static/`).
- Warstwa aplikacji (Flask: `app_db.py`, `routes.py`).
- Warstwa logiki biznesowej (`home_management.py`, `multi_home_context.py`).
- Warstwa dostępu do danych (`utils/multi_home_db_manager.py`, `utils/smart_home_db_manager.py`).
- Warstwa infrastruktury (PostgreSQL, Redis, Socket.IO).

3.2 Komponenty i zależności

- `app_db.py`: entrypoint programu — inicjalizuje Flask, SocketIO, menedżery i binding do DB.
- `RoutesManager` (`app/routes.py`): centralne rejestrowanie tras i integracja z Socket.IO.
- `MultiHomeDBManager` (`utils/multi_home_db_manager.py`): izolacja danych związanych z konkretnym domem.
- `SmartHomeDBManager` (`utils/smart_home_db_manager.py`): operacje CRUD na encjach (użytkownicy, domy, pokoje, urządzenia).

3.3 Wzorce projektowe

- Manager pattern do enkapsulacji działań (np. `HomeUserManager`).
- Dekoratory autoryzacji dla kontroli dostępu (`simple_auth.py`).

## 4. Implementacja

4.1 Struktura repozytorium

- `app_db.py` — inicjalizacja aplikacji
- `app/` — logika tras, zarządzanie domami i ustawieniami
- `utils/` — menedżery bazy, cache, usługi pomocnicze
- `templates/` i `static/` — frontend HTML/CSS/JS
- `backups/db_backup.sql` — schemat i dane startowe

4.2 Kluczowe moduły (szczegóły implementacyjne)

- `app_db.py`:

  - Inicjalizuje `Flask` i `SocketIO`.
  - Ładuje konfigurację (z `.env` lub zmiennych systemowych).
  - Tworzy instancje menedżerów: `multi_db`, `auth_manager`, `cache_manager`.

- `utils/multi_home_db_manager.py`:

  - Zarządza modelami per-home: homes, rooms, devices, users.
  - Metody pomocnicze: `get_cursor`, `has_admin_access`, `set_user_current_home`.

- `routes.py` / `home_management.py`:

  - Rejestruje trasy dla CRUD, endpoints API i widoków HTML.
  - Używa `RoutesManager` zamiast Blueprintów aby centralnie obsługiwać routing i SocketIO.

4.3 Integracja czasu rzeczywistego

Zdarzenia Socket.IO:

- `toggle_button` — klient wysyła żądanie przełączenia stanu urządzenia; serwer aktualizuje DB i rozsyła `update_button`.
- `update_automation` — klient aktualizuje regułę automatyzacji; serwer potwierdza i synchronizuje klientów.

4.4 Konfiguracja i zmienne środowiskowe

Wymagane zmienne środowiskowe (przykłady):

- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `SECRET_KEY`
- `REDIS_URL` (opcjonalnie)

## 5. Diagramy UML i architektury

Poniżej dołączone są pliki PlantUML znajdujące się w katalogu `diagrams/`. Można je renderować narzędziem PlantUML.

5.1 Diagram wdrożeniowy (deployment)

Zawiera elementy: przeglądarka (client), serwer aplikacji Flask + Socket.IO, baza PostgreSQL, Redis (cache), opcjonalny serwer SMTP.

5.2 Diagram klas (class)

Model pokazuje klasy/managery takie jak `SmartHomeApp`, `RoutesManager`, `MultiHomeDBManager`, `Home`, `Room`, `Device`, `User`.

5.3 Diagram sekwencji (toggle)

Scenariusz: użytkownik klik -> żądanie Socket.IO `toggle_button` -> serwer aktualizuje DB -> serwer emituje `update_button` -> klient aktualizuje UI.

Szczegółowe pliki diagramów znajdują się w `diagrams/`.

## 6. Testowanie

6.1 Strategia testów

- Testy jednostkowe: logiczne funkcje w `utils/` i menedżerach DB.
- Testy integracyjne: symulacja przepływu żądań HTTP i Socket.IO.
- Testy manualne: scenariusze w UI (logowanie, dodanie domu, toggle urządzenia, reguła automatyzacji).

6.2 Przykładowe scenariusze testowe (manualne)

1. Rejestracja i logowanie użytkownika (rola: owner i member).
2. Dodanie domu i przypisanie użytkownika.
3. Dodanie pokoju i urządzenia.
4. Przełączenie stanu urządzenia i weryfikacja zdarzeń Socket.IO.
5. Tworzenie automatyzacji: warunek czasowy → akcja toggle.

6.3 Automatyzacja testów

- Proponowane narzędzia: `pytest` dla backendu, `selenium` lub `playwright` dla testów UI, `socketio` client do testowania zdarzeń realtime.

## 7. Instrukcja użytkownika i wdrożenie

7.1 Wymagania

- Python 3.10+, PostgreSQL, (opcjonalnie) Redis, Graphviz do generowania diagramów.

7.2 Krok po kroku - uruchomienie lokalne

1. Sklonuj repozytorium.
2. Utwórz wirtualne środowisko i zainstaluj zależności.
3. Utwórz bazę danych PostgreSQL i zaimportuj `backups/db_backup.sql`.
4. Ustaw zmienne środowiskowe.
5. Uruchom `python app_db.py`.

7.3 Wdrożenie produkcyjne

- Zastosuj serwer WSGI (Gunicorn/nginx lub Waitress na Windows).
- Użyj Docker / docker-compose do uruchomienia zależności (PostgreSQL, Redis).

## 8. Bezpieczeństwo i prywatność

8.1 Autoryzacja

Użyć dekoratorów `admin_required` i `api_admin_required` dla krytycznych endpointów. Logowanie wykorzystuje sesje Flask i bezpieczny `SECRET_KEY`.

8.2 Bezpieczeństwo danych

Szyfrowanie haseł (bcrypt), ograniczony dostęp do plików konfiguracyjnych oraz użycie TLS dla komunikacji sieciowej.

8.3 Wycieki i ochrona prywatności

Minimalizować logowanie wrażliwych danych i zapewnić politykę retencji logów.

## 9. Wnioski i prace przyszłe

- Rozszerzenie testów automatycznych.
- Integracja z protokołami IoT (MQTT) oraz autentykacja urządzeń.
- Skalowanie horyzontalne (kubernetes) i CI/CD.

## 10. Bibliografia

- Dokumentacja Flask, Flask-SocketIO
- Dokumentacja PostgreSQL
- PlantUML — do diagramów UML

## 11. Załączniki

- `backups/db_backup.sql` — schemat bazy danych i dane startowe.
- Pliki konfiguracyjne Docker: `Dockerfile.app`, `docker-compose.yml`.
