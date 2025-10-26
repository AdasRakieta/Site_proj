# TODO List - SmartHome Multi-Home

## ✅ Ostatnie zmiany (Październik 2025)

### Cache-busting i deployment fixes

- [X] Naprawiono brak aktualizacji stylów po redeploy w Portainer
- [X] Dodano `?v={{ asset_version }}` do wszystkich template'ów CSS
- [X] Zaktualizowano `home_select.html`, `home_settings.html`, `settings.html`, `invite_accept.html`, `error.html`, `edit.html`
- [X] Naprawiono przyciski w `home_select.html` (zmieniono `<button href>` na `<a href>`)
- [X] Dodano ASSET_VERSION jako build arg w GitHub Actions workflow
- [X] Zaktualizowano `Dockerfile.app` aby przyjmował ASSET_VERSION
- [X] Utworzono `PORTAINER_DEPLOYMENT.md` z pełnym przewodnikiem deployment

### Unifikacja konfiguracji środowiskowej

- [X] Zunifikowano wszystkie zmienne środowiskowe do pojedynczego `.env`
- [X] Utworzono `stack.env` dla Docker Stack deployments
- [X] Zaktualizowano `docker-compose.yml` i `docker-compose.prod.yml` aby używały `env_file`
- [X] Naprawiono błąd "Missing DB_HOST" podczas importu w kontenerach
- [X] Zmieniono `utils/db_manager.py` aby walidacja następowała przy połączeniu, nie przy imporcie
- [X] Utworzono `DEPLOYMENT.md` z pełną dokumentacją deployment
- [X] Utworzono `MIGRATION_GUIDE.md` dla migracji ze starego setupu
- [X] Zaktualizowano `.env.example` jako template
- [X] Zaktualizowano `.dockerignore` i `.gitignore`

---

## 📋 Zadania do wykonania

1. ** Admin_dashboard**

   1. [X] Błąd przy usuwaniu użytkownika na admin_dashboard:
       1. [X] Nie udało się usunąć użytkownika: too much recursion
       2. [X] api reaguje poprawnie INFO:geventwebsocket.handler:127.0.0.1 - - [2025-09-21 11:51:41] "DELETE /api/users/ff63179f-0933-4331-ad4d-659696c8faba HTTP/1.1" 200 648 0.480781 oraz wpis w bazie danych znika. Jedynie na stronie wyświetla się błędny wpis
   2. [X] Pozycjonowanie okien do dodawania nowego użytkownika
   3. [X] ujednolicenie tła i rozmieszczenia  boxów danych.

   ---
2. ** Rejestracja, restart hasła:**

   1. [X] poprawa styluprzy restarcie oraz przy rejestracji dla kodu weryfikacyjnego i przycisków
   2. [X] poprawa stylu dla przycisku powrót na rejestracji (zmieniono na btn-secondary)

   ---
3. ** Strona Edycji

   1. [X] Komunikat błedu edycji nazwy urządzeń. W bazie danych poprawnie się aktualizuje ale nie wychodzi z trybu zmiany nazwy ani po potwierdzeniu, ani po anulowaniu przyciskiem x
   2. [X] Poprawienie zmiany nazwy pokoi.
   3. [X] poprawienie usuwania pokoi

---

4. Wprowadzic zmiany do sposobu przypisywania użytkowników. - `Wprowadzone`

   1. [X] Tworząc dom użytkownik staje się automatycznie adminem tego domu,
   2. [X] role są przypisywane do domów a nie całego systemu.
   3. [X] Utworzyć nową rolę dla mnie sys-admin, którą można otrzymać tylko za pomocą bazy danych, ma dostęp do wszystkich domów i ich funkcji jako admin, ale nie wyświetla się na liście użytkowników
5. Poprawić style na stronach home

   1. Poprawić ładowanie zdjęcia profilowego w prawym górnym rogu na stronach do zarządznia domem
6. Sprawdzić wszystkie funkcjonalności dla multi home

   1. [X] edycja - ok
   2. [X] światła - ok
   3. [X] temperatura - ok
   4. [X] admin dashboard
   5. [X] ustawienia - usunięto zarządzanie użytkownikami (przeniesione do admin dashboard)
   6. [X] ustawienia użytkownika**s**
   7. [X] zabezpieczenia -ok
   8. [X] strona głowna - ok
   9. [X] strona 404
   1. [X] strony home
7. Poprawa wgrywania zdjęć prof i podstawiania danych w profilu użytkownika
8. Aktualizacja plików dot. inżynierki
9. KONIECZNE - Naprawa odczytywania urządzeń w stronie automatyzacji
