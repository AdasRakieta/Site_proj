1. ** Admin_dashboard**

   1. [X] Błąd przy usuwaniu użytkownika na admin_dashboard:
       1. [X] Nie udało się usunąć użytkownika: too much recursion
       2. [X] api reaguje poprawnie INFO:geventwebsocket.handler:127.0.0.1 - - [2025-09-21 11:51:41] "DELETE /api/users/ff63179f-0933-4331-ad4d-659696c8faba HTTP/1.1" 200 648 0.480781 oraz wpis w bazie danych znika. Jedynie na stronie wyświetla się błędny wpis
   2. [X] Pozycjonowanie okien do dodawania nowego użytkownika
   3. [X] ujednolicenie tła i rozmieszczenia  boxów danych.

   ---
2. ** Rejestracja, restart hasła:**

   1. [X] poprawa styluprzy restarcie oraz przy rejestracji dla kodu weryfikacyjnego i przycisków

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
   4. [ ] admin dashboard
   5. [ ] ustawienia
   6. [ ] ustawienia użytkownika**s**
   7. [X] zabezpieczenia -ok
   8. [X] strona głowna - ok
   9. [ ] strona 404
   1. [ ] strony home
7. Poprawa wgrywania zdjęć prof i podstawiania danych w profilu użytkownika
8. Aktualizacja plików dot. inżynierki
