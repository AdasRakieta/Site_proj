# Rozdział 12: Załączniki

Ten katalog zawiera załączniki do pracy inżynierskiej:

- Kody źródłowe wybranych modułów (fragmenty):
  - `app_db.py` – inicjalizacja aplikacji
  - `utils/multi_home_db_manager.py` – warstwa dostępu do DB
  - `utils/cache_manager.py` – warstwa cache
  - `app/simple_auth.py` – autoryzacja i role
- Diagramy architektury i ERD (PNG/SVG)
- Zrzuty ekranu interfejsu (PNG)
- Skrypty i konfiguracje (Docker, Nginx, Compose)
- Raporty testów wydajności (CSV/PNG)

Struktura przykładowa:

```
12_ZALACZNIKI/
 ├─ kod/
 │   ├─ app_db.py
 │   ├─ multi_home_db_manager.snippet.py
 │   └─ cache_manager.snippet.py
 ├─ diagramy/
 │   ├─ architektura.png
 │   └─ erd.png
 ├─ screenshots/
 │   ├─ dashboard.png
 │   └─ home_settings.png
 ├─ konfiguracja/
 │   ├─ docker-compose.prod.yml
 │   ├─ nginx.conf
 │   └─ requirements.txt
 └─ wyniki/
     ├─ k6-results.csv
     └─ p95.png
```

Wszystkie pliki binarne (obrazy, CSV) należy dodać poza repozytorium lub jako artefakty w systemie kontroli wersji zgodnie z wytycznymi promotora.
