# 5. Testy i walidacja — szczegółowy plan

5.1 Filozofia testów
- Testy powinny obejmować warstwę jednostkową (logika pomocnicza), integracyjną (RoutesManager + DB + Cache) oraz end-to-end (symulacja klienta Socket.IO). Dodatkowo testy obciążeniowe sprawdzą skalowalność Socket.IO i pulę połączeń DB.

5.2 Testy jednostkowe (pytest)
- Przykłady testów funkcjonalnych:

`tests/test_utils.py`
```python
from app.routes import normalize_device_id

def test_normalize_device_id_numeric():
        assert normalize_device_id(' 123 ') == 123

def test_normalize_device_id_string():
        assert normalize_device_id('abc') == 'abc'

def test_normalize_device_id_none():
        assert normalize_device_id(None) is None
```

5.3 Testy integracyjne
- Ustawienie środowiska testowego:
    - Uruchomić lokalną bazę PostgreSQL (docker-compose lub testcontainers)
    - Użyć rzeczywistego `MultiHomeDBManager` i `CacheManager` z `NullCache` lub `Redis`.

- Scenariusz: toggle przycisku
    1. Zainicjuj `SmartHomeApp` w trybie testowym.
    2. Wywołaj endpoint lub zasymuluj zdarzenie Socket.IO `toggle_button`.
    3. Sprawdź, czy DB zawiera oczekiwany stan oraz czy `CacheManager` unieważnił odpowiednie klucze.

5.4 Testy obciążeniowe i wydajnościowe
- Narzędzia: `locust`, `wrk`, `k6`.
- Przykładowe zadanie `locust` symulujące N klientów łączących się via Socket.IO i wysyłających `toggle_button` co 5s.

5.5 Automatyzacja i CI
- Uruchamianie testów w CI (GitHub Actions):
    - Job `unit-tests`: uruchom `pytest` na Python 3.10
    - Job `integration`: uruchom kontenery (Postgres, Redis) i testy integracyjne
    - Job `load-test` (opcjonalny): uruchom `locust` w trybie non-interactive
