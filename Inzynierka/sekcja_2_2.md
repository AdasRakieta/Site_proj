**2.2 Porównanie architektur — monolit vs mikroserwisy w IoT**

Wybór architektury aplikacji wpływa na wydajność, skalowalność, złożoność wdrożenia oraz możliwość ewolucji systemu. W kontekście aplikacji zarządzania inteligentnym domem kluczowe są wymagania dotyczące niskich opóźnień, niezawodności w środowisku o ograniczonych zasobach (Raspberry Pi, domowe serwery NAS) oraz prostoty administracji przez użytkowników bez doświadczenia DevOps.

Architektura monolityczna buduje aplikację jako pojedyncze wdrożenie, w którym wszystkie warstwy działają w ramach jednego procesu. W systemie SmartHome Multi-Home serwer Flask, logika zarządzania urządzeniami (`RoutesManager` w `routes.py`), warstwa dostępu do danych (`MultiHomeDBManager` w `utils/multi_home_db_manager.py`) oraz serwer WebSocket (`Flask-SocketIO`) uruchamiane są w jednym kontenerze Docker z wspólną przestrzenią pamięci.

Zalety monolitu:
- prostota wdrożenia — jedna komenda `docker-compose up` uruchamia cały system;
- transakcje atomowe obejmujące wiele tabel (np. usunięcie gospodarstwa realizowane przez punkt końcowy `/api/home/<home_id>/delete` usuwa rekordy z tabel `homes`, `user_homes`, `rooms`, `devices`, `automations` dzięki regułom CASCADE w schemacie bazy danych);
- niskie opóźnienia komunikacji w ścieżkach czasu rzeczywistego — wszystkie kroki (walidacja, odczyt stanu, aktualizacja, invalidacja cache, broadcast WebSocket) wykonywane są w tym samym procesie (średni czas odpowiedzi ~45 ms, 95. percentyl ~120 ms).

Wady monolitu:
- skalowalność horyzontalna wymaga replikowania całej aplikacji zamiast skalowania wyłącznie wąskich modułów;
- tight coupling — zmiana w module automatyzacji (`automation_executor.py`) wymaga rebuild/restart całej aplikacji;
- ryzyko single point of failure — awaria jednego modułu może spowodować restart całego procesu.

Architektura mikroserwisowa dekomponuje system na niezależne usługi (np. User Service, Home Service, Device Service, Automation Service, Notification Service) komunikujące się przez dobrze zdefiniowane API lub broker wiadomości. Zalety to niezależne skalowanie i izolacja awarii; wady — znaczna złożoność operacyjna (orchestrator, service discovery, API gateway, distributed tracing), wyższe wymagania sprzętowe oraz dodatkowa latencja związana z wywołaniami międzyserwisowymi (10–50 ms na hop w zależności od mechanizmu komunikacji), co w sumie może podnieść czas obsługi operacji sterowania do rzędu 150–300 ms.

Dla scenariusza self-hosting (instalacja na Raspberry Pi, domowym NAS) monolit warstwowy jest optymalnym wyborem: zapewnia niski footprint, prostotę administracji i zachowuje separation of concerns poprzez wyraźny podział na warstwy — prezentacji, logiki biznesowej, dostępu do danych oraz persystencji — co ułatwia przyszłą ewolucję oraz ewentualną ekstrakcję komponentów do mikroserwisów.

Rysunek 2.1 ilustruje proponowaną architekturę warstwową i przepływ żądań HTTP/WebSocket pomiędzy warstwami:

- Rysunek: [Inzynierka/figure_2_1_architektura_warstwowa.mmd](Inzynierka/figure_2_1_architektura_warstwowa.mmd)
