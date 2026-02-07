# Plan realizacji pracy inżynierskiej — Smart Home System

Poniżej znajduje się szczegółowy plan krok po kroku do wykonania, weryfikacji i wygenerowania finalnej pracy inżynierskiej.

1. Zbierz dokumentację projektu
   - Cel: zebrać wszystkie opisy modułów, pliki konfiguracyjne i schemat bazy danych.
   - Akcja: użyj `mcp_deepwiki_ask_question` i przejrzyj `backups/db_backup.sql`, `app/` i `utils/`.

2. Przeanalizuj kod źródłowy
   - Cel: zrozumieć kluczowe moduły: `app_db.py`, `routes.py`, `multi_home_db_manager.py`, `smart_home_db_manager.py`, `utils/cache_manager.py`.
   - Akcja: wypisz interfejsy publiczne i punkty wejścia (endpoints, socket events).

3. Szkic spisu treści
   - Cel: przygotować strukturę rozdziałów (Wstęp, Analiza wymagań, Architektura, Implementacja, Testy, Instrukcja użytkownika, Wnioski).

4. Przygotuj diagramy UML (PlantUML)
   - Diagramy: diagram wdrożeniowy (deployment), diagram klas (class), diagram sekwencji (sequence) dla scenariusza toggle button.
   - Akcja: umieścić pliki `.puml` w `diagrams/`.

5. Napisz rozdziały techniczne
   - Każdy rozdział ma strukturę: cele, wymagania, szczegóły implementacyjne, odniesienia do kodu (linki do plików), fragmenty kodu.

6. Instrukcja instalacji i uruchomienia
   - Zawiera: wymagania systemowe, zmienne środowiskowe, kroki inicjalizacji bazy (import `backups/db_backup.sql`), uruchomienie lokalne i produkcyjne.

7. Testowanie
   - Przygotuj scenariusze testowe (manualne), przykładowe skrypty testowe (pytest) i instrukcję ich uruchomienia.

8. Korekta i finalizacja
   - Przegląd merytoryczny, poprawki językowe, uzupełnienie bibliografii, wygenerowanie PDF.

9. Przekazanie wyników
   - Wygeneruj finalny `praca_inzynierska.md` oraz `praca_inzynierska.pdf` (opcjonalnie).

Komendy pomocnicze

Instalacja zależności (virtualenv):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Uruchomienie lokalne (deweloperskie):

```powershell
python app_db.py
```

Render diagramów PlantUML (lokalnie):

1. Zainstaluj PlantUML i Graphviz.
2. Renderuj: `plantuml diagrams/class_diagram.puml`.

Generowanie PDF z Markdown:

```powershell
pandoc praca_inzynierska.md -o praca_inzynierska.pdf --from markdown --pdf-engine=xelatex
```

Kontrole jakości i security (zalecane):

- Przed dodaniem nowych zależności uruchom skaner luk (np. Trivy) zgodnie z wewnętrznymi procedurami.
