# Superpowers for Copilot in This Codebase

Data analizy: 2026-04-02
Zrodlo: https://github.com/obra/superpowers

## Co zostalo pobrane do repo

- Skille: `.github/skills/*` (pelny zestaw Superpowers)
- Agent: `.github/agents/code-reviewer.agent.md`
- Hooki: `.github/hooks/hooks.json`, `.github/hooks/run-hook.cmd`, `.github/hooks/session-start`

## Co jest najbardziej przydatne dla projektu SmartHome

### Priorytet A (warto uzywac od razu)

- `systematic-debugging`
  - Najwieksza wartosc przy bledach Flask/Socket.IO, problemach DB fallback i niestabilnych zachowaniach runtime.
- `verification-before-completion`
  - Dobrze pasuje do pracy w tym repo, gdzie czesto sa szybkie iteracje i latwo o "dziala u mnie" bez twardego potwierdzenia.
- `requesting-code-review`
  - Pomaga wymuszac kontrole regresji po zmianach w trasach, auth i cache.
- `receiving-code-review`
  - Uporzadkowuje odpowiadanie na uwagi i zmniejsza ryzyko powierzchownych poprawek.

### Priorytet B (bardzo przydatne przy wiekszych zadaniach)

- `writing-plans`
  - Dobre przy przebudowie flow multi-home i tras API.
- `subagent-driven-development`
  - Przydatne, gdy rozbijasz task na niezalezne kroki (np. backend + templates + testy).
- `dispatching-parallel-agents`
  - Sensowne, gdy zadania sa niezalezne (np. dokumentacja i refactor osobnych modulow).

### Priorytet C (uzywac selektywnie)

- `brainstorming`
  - Silnie procesowy i moze byc ciezki przy drobnych poprawkach. Najlepszy dla nowych funkcji, nie dla malych fixow.
- `test-driven-development`
  - Wartosc wysoka, ale wymaga dyscypliny i czasu; najlepiej przy nowej logice, nie kazdej mikropoprawce.
- `using-git-worktrees`
  - Dobre przy duzych feature branchach; mniej potrzebne przy pojedynczych, krotkich zmianach.
- `finishing-a-development-branch`
  - Uzyteczne glownie przy formalnym domykaniu wiekszych partii prac.

### Niska wartosc dla tego repo

- `writing-skills`
  - Potrzebne glownie do tworzenia nowych skilli, nie do codziennego developmentu aplikacji.
- `using-superpowers`
  - Meta-skill bootstrappingowy; potrzebny jako punkt startu systemu, ale nie jako codzienna "procedura" biznesowa.

## Uwagi kompatybilnosciowe

- Hook `session-start` ma logike zgodna z Copilot CLI (`additionalContext`).
- W tym repo hook odczytuje bootstrap skill z lokalnej sciezki `.github/skills/using-superpowers/SKILL.md`.
- `run-hook.cmd` wymaga dostepnego `bash` (np. Git for Windows). Bez `bash` hook konczy sie cicho i nie blokuje pracy.

## Co jeszcze moze byc przydatne z upstream, ale nie bylo importowane

- Katalog `commands/` w upstream jest oznaczony jako deprecated i tylko przekierowuje do skilli.
- Pliki pluginowe dla innych platform (`.cursor-plugin`, `.claude-plugin`, `.opencode`) nie sa potrzebne do lokalnej customizacji Copilot w tym repo.
- Dokumentacje migracyjne (`docs/README.codex.md`, `docs/README.opencode.md`) sa pomocnicze, ale nie wymagane do dzialania skilli.

## Szybki sposob pracy w tym repo

1. Start tasku: `writing-plans` (dla wiekszych zmian) albo od razu implementacja przy malym fixie.
2. Gdy pojawia sie blad: `systematic-debugging`.
3. Przed zamknieciem: `verification-before-completion`.
4. Przed scaleniem: `requesting-code-review` + `receiving-code-review`.
