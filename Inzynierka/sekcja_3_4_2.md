**3.4.2 Izolacja danych między gospodarstwami**

Izolacja danych między gospodarstwami realizowana jest na trzech poziomach: sesji użytkownika, zapytań SQL oraz cache.

Poziom sesji: Flask przechowuje aktywne gospodarstwo w zmiennej `session['current_home_id']`, ustawianej podczas wyboru gospodarstwa (endpoint POST `/api/home/select` z parametrem `home_id`). Konfiguracja sesji znajduje się w `app_db.py` (SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_HTTPONLY=True, `SESSION_COOKIE_SECURE=True` w produkcji). `SECRET_KEY` ładowany z zmiennej środowiskowej i walidowany pod kątem długości >= 32 znaków zapewnia integralność i autentyczność sesji.

Po zalogowaniu system tworzy rekord w tabeli `session_tokens` (schemat w `backups/db_schema_multihouse.sql`) zawierający `current_home_id`. Middleware weryfikuje token sesji przy każdym żądaniu i aktualizuje `last_activity`. Proces background task co godzinę usuwa wygasłe lub nieaktywne tokeny (`expires_at < NOW()` lub `last_activity < NOW() - INTERVAL '24 hours'`).

Poziom zapytań SQL: wszystkie metody warstwy dostępu do danych wymagają jawnego `home_id` i walidują membership przed wykonaniem zapytania. Przykład w `MultiHomeDBManager`:

- metoda `get_devices(home_id, user_id)` najpierw wykonuje `SELECT 1 FROM user_homes WHERE user_id = %s AND home_id = %s` i przy braku wyniku podnosi `PermissionError("User not member of this home")`, następnie `SELECT * FROM devices WHERE home_id = %s AND enabled = TRUE ...` zwracając tylko urządzenia danego gospodarstwa.
- metoda `delete_device(device_id, home_id, user_id)` wykonuje `DELETE FROM devices WHERE id = %s AND home_id = %s`, co chroni przed usunięciem zasobu należącego do innego gospodarstwa nawet przy znanym `device_id`.

Poziom cache: klucze Redis zawierające dane gospodarstwa umieszczają `home_id` w nazwie, np. `home:{home_id}:devices`, `home:{home_id}:rooms`, `home:{home_id}:automations`. `CacheManager` (`utils/cache_manager.py`) implementuje `invalidate_cache(pattern)` używając `SCAN` do znalezienia pasujących kluczy i ich `DEL`. Operacje modyfikujące stan gospodarstwa (np. `toggle_device`, `create_room`, `delete_automation`) wywołują `invalidate_cache(f"home:{home_id}:*")` przed zwróceniem odpowiedzi, zapewniając, że kolejny odczyt pobierze świeże dane z PostgreSQL.

Kod zabezpieczający poziom aplikacji (dekorator `home_required`) znajduje się w `simple_auth.py` — fragment tego dekoratora pokazano w Listing 3.3.

- Listing: [Inzynierka/listing_3_3.md](Inzynierka/listing_3_3.md)
