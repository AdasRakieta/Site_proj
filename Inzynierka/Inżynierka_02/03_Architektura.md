# 3. Architektura systemu — szczegółowy opis

Ten rozdział opisuje projekt architektury systemu SmartHome na poziomie logicznym i fizycznym, wyjaśnia kluczowe decyzje projektowe, formaty wymiany danych oraz schematy integracji komponentów.

3.1 Warstwy i odpowiedzialności
- Warstwa kliencka (Frontend): aplikacja webowa (JS/HTML/CSS) inicjuje żądania REST oraz zdarzenia WebSocket (Flask-SocketIO). UI obsługuje wybór aktywnego domu (multi-home) i renderuje listę pokojów, urządzeń i automatyzacji.
- Warstwa prezentacji / API: `RoutesManager` w `app/routes.py` jest pojedynczym punktem wejścia dla endpointów HTTP oraz logiki pomocniczej (normalizacja identyfikatorów, rozwiązywanie kontekstu domu, serializacja odpowiedzi).
- Warstwa logiki biznesowej: `SmartHomeSystem` (zastępuje starą JSON-ową implementację) oraz menedżery automatyzacji (`AutomationScheduler`, `AutomationExecutor`) — tutaj implementowane są reguły automatyzacji i harmonogramy.
- Warstwa danych: `MultiHomeDBManager` / `SmartHomeDatabaseManager` (PostgreSQL). Zastosowano puli połączeń, transakcyjne kursory i tabele dedykowane per-home dla automations, invitations i security state.
- Infrastruktur: `CacheManager` (Redis lub SimpleCache), asynchroniczny menedżer wysyłki e-maili (`AsyncMailManager`), Socket.IO do rozgłaszania zdarzeń.

3.2 Kluczowe decyzje projektowe
- Multi-home: każdy dom jest izolowany w DB przez `home_id`; zapytania i indeksy optymalizują odczyty per-home.
- Real-time + trwałe zapisy: operacje sterujące (toggle/set) są zapisywane w DB przez `MultiHomeDBManager`, a równocześnie rozgłaszane przez Socket.IO, co zapewnia spójność i historię zmian.
- Cache: wykorzystywany do przyspieszania odczytów (rooms, buttons, automations). Kluczowa jest strategia invalidacji po aktualizacjach, zaimplementowana w `CacheManager`.

3.3 Diagramy i zasoby
Pliki diagramów (Mermaid) dostępne w repozytorium:
- `Inzynierka/Inżynierka_02/diagrams/database_layer.mmd` — zależności aplikacja ↔ baza.
- `Inzynierka/Inżynierka_02/diagrams/client_connection.mmd` — sekwencja połączenia klienta i pobrania stanu.
- `Inzynierka/Inżynierka_02/diagrams/websocket_control_flow.mmd` — obsługa akcji toggle przez WebSocket.
- `Inzynierka/Inżynierka_02/diagrams/automation_execution.mmd` — scheduler -> executor -> DB -> emit.
- `Inzynierka/Inżynka_02/diagrams/automation_trigger.mmd` — wyzwalanie automatyzacji na zdarzeniach.
- `Inzynierka/Inżynierka_02/diagrams/device_model.mmd` — diagram klas domenowych (Button, TemperatureControl, Automation, Home).
- Dodatkowe, bardziej szczegółowe diagramy dostępne w `Inzynierka/Inżynierka_01/12_ZALACZNIKI/diagramy/` (ERD, sekwencje login/toggle/automation, deployment Docker).

3.4 Model danych (ERD) — krótkie streszczenie
- Główne tabele: `homes`, `users`, `user_homes` (relacja użytkownik-dom z rolami/permission), `rooms`, `devices`/`buttons`, `home_automations`, `home_invitations`, `home_security_states`.
- Indeksy: unikalne indeksy per-home (np. `home_automations (home_id, name_normalized)`) oraz indeksy warunkowe (`home_invitations (invitation_code) WHERE status='pending'`) dla szybkiego wyszukiwania aktywnych zaproszeń.

3.5 Przepływy sekwencyjne (wybrane)
- Połączenie klienta: handshake Socket.IO → `handle_connect()` → pobranie stanu z DB lub cache → emit `initial_state`.
- Toggle urządzenia: frontend emituje `toggle_button` → backend zapisuje w DB (`update_button_state`) → invalidacja cache → emit `update_button` do klientów.
- Wykonanie automatyzacji: `AutomationScheduler` wywołuje `AutomationExecutor`, który zapisuje metadane wykonania w DB, uruchamia akcje (np. toggle urządzeń) i emituje eventy.

3.6 Odniesienia do implementacji
- Inicjalizacja trybu bazy danych i fallbacku do JSON: [app_db.py](app_db.py)
- Główne klasy DB i kursory: [utils/multi_home_db_manager.py](utils/multi_home_db_manager.py), [utils/smart_home_db_manager.py](utils/smart_home_db_manager.py)
- Polityki cache: [utils/cache_manager.py](utils/cache_manager.py)
