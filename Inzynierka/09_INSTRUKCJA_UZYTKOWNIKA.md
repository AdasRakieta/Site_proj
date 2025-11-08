# Rozdział 9: Instrukcja użytkownika

Ten rozdział stanowi praktyczny przewodnik po najważniejszych funkcjach systemu SmartHome Multi-Home. Obejmuje: pierwsze uruchomienie, typowe scenariusze oraz rozwiązywanie problemów.

## 9.1. Wymagania wstępne

- Przeglądarka: Chrome / Firefox / Edge (ostatnie wersje)
- Konto użytkownika (rejestracja wymaga prawidłowego adresu email)
- Dostęp do instancji systemu (URL HTTPS)

## 9.2. Rejestracja i logowanie

1. Otwórz stronę logowania (`/login`).
2. Kliknij „Rejestracja” → wypełnij formularz: email, hasło, potwierdzenie.
3. Po rejestracji zaloguj się używając email + hasło.
4. W razie utraty hasła użyj „Zapomniałem hasła” (`/forgot_password`).

Bezpieczeństwo: hasła są haszowane, sesje wygasają automatycznie po 24h nieaktywności.

## 9.3. Tworzenie i wybór domu

1. Po zalogowaniu wybierz opcję „Dodaj dom” (`/home_create`).
2. Nadaj nazwę i opis (opcjonalny).
3. Wybór aktywnego domu: ekran `home_select.html` – kliknij kafelek.
4. Przełączenie domu powoduje odświeżenie widoków (real-time sync).

## 9.4. Zarządzanie członkami domu

1. Wejdź w „Ustawienia domu” → sekcja „Członkowie”.
2. Wygeneruj zaproszenie: wybierz rolę (member/admin), czas ważności.
3. Udostępnij link zaproszenia nowemu użytkownikowi.
4. Akceptacja: użytkownik loguje się, otwiera link, potwierdza dołączenie.
5. Usunięcie członka: właściciel/admin może usunąć przedawnione lub niechciane konta.

## 9.5. Pokoje i urządzenia

1. Dodaj pokój (nazwa, typ). Sortowanie przeciągnij–upuść.
2. Dodaj urządzenie (typ: światło, sensor temperatury, przycisk).
3. Zmień stan urządzenia klikając ikonę (natychmiastowa propagacja przez Socket.IO).
4. Historia zmian dostępna w szczegółach urządzenia.

## 9.6. Automatyzacje

1. Otwórz „Automatyzacje”.
2. Dodaj nową: wybierz trigger (czas / urządzenie / sensor), akcję (zmiana stanu / email).
3. Dodaj warunek (opcjonalnie) – np. temperatura > 25°C.
4. Zapisz – automatyzacja pojawi się na liście aktywnych.
5. Podgląd logów wykonania: sekcja „Historia automatyzacji”.

## 9.7. Panel administratora

Panel pokazuje:
- Listę użytkowników i ich role.
- Logi zmian (dodanie/usunięcie urządzenia, zaproszenia).
- (Planowane) metryki wydajności w czasie rzeczywistym.

## 9.8. Profil użytkownika

- Zmiana nickname, email (jeśli dozwolone), hasła.
- Upload zdjęcia profilowego (automatyczna optymalizacja i resize).
- Preferencje powiadomień (email on/off).

## 9.9. Powiadomienia email

System wysyła wiadomości przy:
- Zaproszeniu do domu.
- Resetowaniu hasła.
- Alarmach bezpieczeństwa (opcjonalne).

Email może trafić do folderu „Spam” – dodaj nadawcę do zaufanych.

## 9.10. Rozwiązywanie problemów (FAQ)

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| Brak aktualizacji stanu urządzenia | Utracone połączenie Socket.IO | Odśwież stronę; sprawdź Internet; sprawdź czy serwer działa |
| Nie mogę zaakceptować zaproszenia | Token wygasł | Właściciel musi wygenerować nowe zaproszenie |
| Błędny czas odpowiedzi | Wysokie obciążenie lub brak cache | Kontakt z administratorem; sprawdź logi wydajności |
| Nie ładuje się panel admina | Brak roli admin | Sprawdź rolę w ustawieniach domu |
| Nie działa upload zdjęcia | Format nieobsługiwany / zbyt duży | Użyj JPG/PNG < 2MB |

## 9.11. Bezpieczeństwo dla użytkownika

- Używaj silnych haseł (≥12 znaków, litery/cyfry/znaki).
- Nie udostępniaj linków zaproszeń osobom trzecim.
- Wyloguj się na urządzeniach publicznych.
- Aktualizuj przeglądarkę dla najnowszych zabezpieczeń.

## 9.12. Eksport i kopie zapasowe (zaawansowane)

- Backup bazy wykonywany codziennie (admin systemu).
- Możliwy eksport CSV (planowane) – lista urządzeń, logi.
- Przy migracji – skrypty DDL i data dump w `backups/`.

## 9.13. Dalsze funkcje (planowane)

- Edytor zaawansowanych automatyzacji (wizualny).
- Powiadomienia push (mobile/PWA).
- Integracje z asystentami głosowymi.
- Statystyki zużycia energii.

## 9.14. Podsumowanie

Instrukcja pokrywa najczęstsze scenariusze użytkowania systemu. Projekt pozostaje rozwojowy – nowe funkcje zwiększą ergonomię (edytor automatyzacji, powiadomienia push, energia). Użytkownik ma pełną kontrolę nad wieloma domami z jednego panelu, a aktualizacje są natychmiastowe dzięki WebSocket.
