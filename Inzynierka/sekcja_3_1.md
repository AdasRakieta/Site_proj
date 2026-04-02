**3.1 Architektura ogólna systemu**

System SmartHome Multi-Home zbudowany został zgodnie z architekturą warstwową, w której każda warstwa realizuje odrębną odpowiedzialność i komunikuje się z warstwami sąsiednimi przez ściśle określone interfejsy. Podejście to zapewnia separation of concerns oraz ułatwia testowanie i utrzymanie poszczególnych komponentów niezależnie od siebie.

Przepływ żądania użytkownika rozpoczyna się w przeglądarce webowej i odbywa się dwoma kanałami: żądaniami HTTP oraz połączeniem WebSocket. Żądania HTTP trafiają najpierw do reverse proxy Nginx, które terminuję połączenia SSL/TLS, obsługuje kompresję gzip oraz przekierowuje ruch do aplikacji Flask działającej na porcie 5000. Konfiguracja Nginx obsługuje również upgrade WebSocket, co pozwala na bezproblemową pracę `Flask-SocketIO`.

Warstwa prezentacji odpowiada za renderowanie interfejsu i interakcję z użytkownikiem. Szablony Jinja2 znajdują się w katalogu `templates` i dziedziczą z `base.html`, który definiuje strukturę HTML, nawigację i mechanizm wersjonowania assetów (`?v={{asset_version}}`). Assety statyczne (JS/CSS/ikony) przechowywane są w `static/` — moduły JavaScript (`common.js`, `controls.js`, `automations.js`) obsługują logikę klienta, Fetch API i eventy Socket.IO.

Warstwa logiki biznesowej zaimplementowana jest przez `RoutesManager` (`app/routes.py`), który agreguje zależności aplikacji: `smart_home` (konfiguracja), `auth_manager` (autoryzacja), `mail_manager` (wysyłka e-mail), `cache` (Redis), `multi_db` (dostęp do danych), `socketio` (realtime) oraz `limiter` (rate limiting). `RoutesManager` rejestruje endpointy HTTP i handler-y Socket.IO, wykorzystując helpery z `MultiHomeHelpersMixin` do rozwiązywania aktywnego gospodarstwa oraz normalizacji odpowiedzi.

Warstwa dostępu do danych enkapsuluje SQL w `MultiHomeDBManager` (`utils/multi_home_db_manager.py`). Klasa ta udostępnia `get_cursor()` (context manager) zapewniający commit/rollback transakcji oraz wymaga `home_id` jako pierwszego parametru w publicznych metodach, gwarantując izolację danych między gospodarstwami. Przykład `toggle_device(home_id, device_id, user_id)`: walidacja uprawnień, odczyt aktualnego stanu, `UPDATE devices SET state = NOT state WHERE id = %s AND home_id = %s`, zwrot zaktualizowanego rekordu.

Warstwa persystencji oferuje dwa backendy: PostgreSQL 16 (preferowany) oraz JSON fallback (plik `smart_home_config.json`) aktywowany automatycznie w przypadku braku połączenia z bazą. Wybór backendu odbywa się w `app_db.py` — w trybie fallback `MultiHomeDBManager` dostosowuje logikę, używając mechanizmów plikowych zamiast kursora SQL.

Integracje zewnętrzne:
- Redis: cache (timeouty konfigurowane w `utils/cache_manager.py`: `user_data:1800s`, `rooms:1800s`, `buttons:600s`, `temperature:300s`) z mechanizmem invalidacji kluczy per-gospodarstwo (`home:{home_id}:*`).
- SMTP: konfiguracja przez zmienne środowiskowe (`SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`) i asynchroniczne wysyłanie maili przez `AsyncMailManager` (`utils/async_manager.py`).
- Nginx: reverse proxy terminujące SSL/TLS (Let's Encrypt), gzip oraz WebSocket upgrade headers.

Rysunek 3.1: [Inzynierka/figure_3_1_architektura_wysokopoziomowa.mmd](Inzynierka/figure_3_1_architektura_wysokopoziomowa.mmd)
