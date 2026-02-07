# Rozdział 12: Załączniki

Ten katalog zawiera załączniki do pracy inżynierskiej:

- Kody źródłowe wybranych modułów (fragmenty):
  - `app_db.py` – inicjalizacja aplikacji
  - `utils/multi_home_db_manager.py` – warstwa dostępu do DB
  - `utils/cache_manager.py` – warstwa cache
  - `app/simple_auth.py` – autoryzacja i role
- Diagramy architektury i ERD (Mermaid .mmd + ewentualnie PNG/SVG)
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
 │   ├─ architektura_systemu.mmd
 │   ├─ erd_smarthome.mmd
 │   ├─ sekwencje_login.mmd
 │   ├─ sekwencje_toggle_device.mmd
 │   ├─ sekwencje_home_switch.mmd
  │   ├─ sekwencje_automation.mmd
  │   ├─ deployment_docker.mmd
  │   └─ network_topology.mmd
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

## Jak renderować diagramy Mermaid

Możesz skorzystać z jednej z metod:

- Edytor online: https://mermaid.live i wklejenie zawartości plików `.mmd`
- VS Code: rozszerzenie „Markdown Preview Mermaid Support”
- CLI: `mmdc` (Mermaid CLI) do renderowania do PNG/SVG

Lista diagramów:

- `diagramy/architektura_systemu.mmd` – architektura wysokopoziomowa
- `diagramy/erd_smarthome.mmd` – schemat ERD
- `diagramy/sekwencje_login.mmd` – logowanie
- `diagramy/sekwencje_toggle_device.mmd` – zmiana stanu urządzenia
- `diagramy/sekwencje_home_switch.mmd` – przełączanie domu
- `diagramy/sekwencje_automation.mmd` – wykonanie automatyzacji
 - `diagramy/deployment_docker.mmd` – kontenery i sieci Docker
 - `diagramy/network_topology.mmd` – topologia sieci (strefy bezpieczeństwa)
