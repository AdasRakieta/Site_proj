# Rozdział 8: Testy i optymalizacja wydajności

Celem rozdziału jest przedstawienie strategii testowania, przykładowych scenariuszy testowych oraz metodologii pomiaru wydajności wraz z wynikami i wnioskami.

## 8.1. Strategia testowania

- Testy jednostkowe (unit): logika biznesowa (np. uprawnienia, walidacja danych, kalkulacja stanów), mock DB/Redis.
- Testy integracyjne: realne połączenie z PostgreSQL (testowa baza) i Redis (lokalny), sprawdzenie spójności transakcji.
- Testy end‑to‑end (E2E): Selenium/Playwright – krytyczne ścieżki (logowanie, przełączanie domu, CRUD urządzeń, zaproszenia).
- Testy bezpieczeństwa: próby SQLi/XSS, brute-force, analiza nagłówków i TLS.
- Testy wydajnościowe: k6/Locust – obciążenie REST/Socket.IO, testy soak i stress.

## 8.2. Przykładowe przypadki testowe

### 8.2.1. RBAC i izolacja multi‑home (integracyjne)
- Given: Użytkownik A (owner w Home1, brak dostępu do Home2), Użytkownik B (owner w Home2).
- When: A próbuje pobrać urządzenia z Home2.
- Then: API zwraca 403; log nie zawiera danych Home2.

### 8.2.2. Zaproszenia i akceptacja (integracyjne/E2E)
- Generate: token zaproszenia z ważnością 24h dla roli `member`.
- Accept: nowy użytkownik akceptuje token → staje się członkiem domu.
- Re-accept: ponowna próba użycia tokenu → 410 Gone.

### 8.2.3. Cache invalidation (jednostkowe/integracyjne)
- Update: Zmiana nazwy pokoju.
- Assert: Inwalidacja kluczy `rooms:{home_id}` i `devices:{home_id}:*`.
- Reload: Pierwszy odczyt – pudło w cache; kolejne – hit.

### 8.2.4. WebSocket sync (E2E)
- Two clients in `home_{id}`.
- Toggle device on client A → event emit.
- Client B receives update < 200 ms; UI odświeżony.

## 8.3. Metodologia pomiarów wydajności

- Środowisko: Docker Compose (app, postgres, redis, nginx), 2 vCPU, 4 GB RAM.
- Cold vs warm cache: oddzielne pomiary.
- metryki: p50/p95/p99 response time, WebSocket latency, throughput req/s, CPU/RAM, connection pool.
- Narzędzia: k6/Locust + Grafana/Prometheus (opcjonalnie).

## 8.4. Wyniki (streszczenie)

- API p95 < 150 ms, WebSocket latency ~50 ms (szczegóły w Rozdziale 10).
- Cache hit rate ~85% dla często odczytywanych endpointów.
- Stabilność podczas soak (24h): brak wycieków pamięci, stałe czasy odpowiedzi.
- Przy stress 500 req/s: degradacja łagodna, timeouts kontrolowane przez Nginx.

## 8.5. Optymalizacje zastosowane w projekcie

- Indeksowanie SQL pod najczęstsze kwerendy; ograniczenie N+1.
- Cache‑aside + invalidate‑on‑write; klucze per‑home.
- Asynchroniczna wysyłka maili; ograniczenie blokujących operacji w request‑thread.
- Minifikacja i bundling assetów; `ASSET_VERSION` dla cache‑bustingu.
- Gzip/Brotli w Nginx; HTTP/2; długie max‑age dla statyków.

## 8.6. Profilowanie i monitoring

- Profilowanie: `cProfile`/`py-spy` dla endpointów o wysokim p95.
- Monitoring: logi zarządzania i aplikacyjne, health checks, metryki kontenerów.
- Alerting: proste progi (CPU > 80%, pamięć > 80%, errors > N/min).

## 8.7. Wnioski

Zastosowane techniki testowe i optymalizacyjne umożliwiły osiągnięcie zakładanych celów niefunkcjonalnych (responsywność, skalowalność, dostępność). Kluczowe były: właściwe indeksy, skuteczne cache’owanie oraz minimalizacja pracy w ścieżce requestu. Dalsze prace: adapter Redis dla Socket.IO (skalowanie horyzontalne) i rozszerzenie E2E o więcej scenariuszy.
