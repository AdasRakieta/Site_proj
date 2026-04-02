## 5.1 Konfiguracja środowiska produkcyjnego

### 5.1.1 Wymagania sprzętowe

Poniższa sekcja przedstawia minimalne oraz rekomendowane wymagania sprzętowe dla uruchomienia systemu SmartHome, opracowane na podstawie testów przeprowadzonych na platformie Raspberry Pi 5 (8GB RAM). System jest zoptymalizowany pod kątem architektur ARM64 oraz x86_64.

Minimalne wymagania:

- CPU: ARM Cortex-A72 (quad-core 1.5GHz) lub x86_64 dual-core 2.0GHz
- RAM: 2GB (4GB rekomendowane dla > 50 urządzeń)
- Dysk: 8GB wolnej przestrzeni (16GB zalecane dla logów i kopii zapasowych)
- Sieć: 100 Mbps Ethernet lub WiFi 802.11ac

Rekomendowane wymagania produkcyjne:

- CPU: 4 rdzenie ARM64/x86_64 @ 2.0GHz lub szybsze
- RAM: 4GB (pozwala na Redis cache + PostgreSQL connection pooling)
- Dysk: 32GB SSD (zalecane IOPS > 3000 dla PostgreSQL WAL)
- Sieć: 1 Gbps Ethernet

Testy wydajnościowe przeprowadzono na urządzeniu Raspberry Pi 5 z następującą konfiguracją produkcyjną:

- Platforma: Raspberry Pi 5 (8GB RAM)
- CPU: Broadcom BCM2712 (quad-core Cortex-A76 @ 2.4GHz)
- RAM: 8GB LPDDR4X-4267
- Dysk: SSD NVMe 256GB przez adapter USB 3.0
- OS: Raspberry Pi OS 64-bit (Debian Bookworm)
- Python: 3.11.2
- PostgreSQL: 15.4 (ustawienia testowe: shared_buffers=256MB, max_connections=50)
- Redis: 7.0.11 (maxmemory=128MB)
- Gunicorn: 21.2.0 (-w 2 -k eventlet -b 0.0.0.0:5000)

Wyniki testów (przykładowe miary po 100 requestów na endpoint, wartości w ms):

- GET /lights (cache hit): średnia 95, P95 180, P99 320
- GET /lights (cache miss): średnia 340, P95 620, P99 890
- GET /api/rooms (cache hit): średnia 12, P95 28, P99 45
- GET /api/rooms (cache miss): średnia 145, P95 285, P99 450
- POST /api/buttons/toggle (DB write): średnia 85, P95 195, P99 310
- WebSocket emit (in-memory): średnia 35, P95 95, P99 165
- Automation check (JSONB + Python): średnia 180, P95 340, P99 520

Obserwacje i zalecenia konfiguracji:

- Cache Redis znacząco redukuje czasy odpowiedzi dla często odczytywanych zasobów (~70% redukcji czasu dla endpointów typu GET przy trafieniach cache). W środowiskach o ograniczonej pamięci ustawienie `maxmemory` Redis na 128MB jest rozsądnym kompromisem.
- Aby uniknąć przeciążenia CPU na platformach z ograniczoną liczbą rdzeni (np. Raspberry Pi), użyto 2 workerów Gunicorn z `eventlet` zamiast większej liczby workerów procesowych.
- Parametry PostgreSQL (np. `shared_buffers`, `max_connections`) należy dostosować do dostępnej pamięci — w testach ustawiono `shared_buffers=256MB`, `max_connections=50` jako wartości bezpieczne dla urządzeń z 8GB RAM.
- Monitorować wskaźnik trafień cache (`/api/cache/stats`) — w testach stabilizował się na poziomie 87–91% po ~1 godzinie działania.
- Przy planowaniu produkcji uwzględnić miejsce na logi i backupy — rekomendowane co najmniej dodatkowe 8–16GB poza przestrzenią systemową.

Tabela 5.1 — Wymagania sprzętowe

| Komponent | Minimum | Rekomendowane | Testowane platformy |
|---|---:|---:|---|
| CPU | ARM Cortex-A72 (4×1.5GHz) / x86_64 2×2.0GHz | 4 rdzenie ARM64/x86_64 @ 2.0GHz+ | Raspberry Pi 5 (BCM2712, 4×Cortex‑A76 @2.4GHz) |
| RAM | 2 GB | 4 GB (dla >50 urządzeń) | 8 GB (Raspberry Pi 5) |
| Dysk | 8 GB wolnego | 32 GB SSD (IOPS > 3000) | 256 GB NVMe (USB3 adapter) |
| Sieć | 100 Mbps | 1 Gbps Ethernet | Gigabit Ethernet (testy lokalne) |
| Inne | -- | Redis (128MB+), PostgreSQL, Gunicorn (2 workers, eventlet) | Redis 7.0.11 (128MB), PostgreSQL 15.4 |

Jeśli chcesz, mogę:

- wygenerować grafikę (Tabela 5.1) w formacie PNG/SVG do wkładu do PDF, lub
- dodać konkretne polecenia instalacyjne i przykładowy `systemd` unit/service dla uruchomienia aplikacji w produkcji.
