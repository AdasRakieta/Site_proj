| Endpoint | Method | Request Body | Response | Auth | Opis |
|---|---:|---|---|---|---|
| /login | POST | {username, password} | redirect to `/` or {status: "error", message: ...} | None | Logowanie użytkownika, ustawia `session['user_id']` przy sukcesie.
| /register | POST | {username, email, password} | redirect to `/login` or {status: "error", message: ...} | None | Rejestracja nowego konta, hashowanie hasła bcrypt.
| /api/rooms | GET | — | {status: "success", rooms: [...]} | login_required | Zwraca listę pokoi dla aktywnego `current_home_id`.
| /api/room/create | POST | {name, home_id, description?} | {status: "success", room_id: "..."} (201) | admin_required | Tworzy nowy pokój w gospodarstwie; waliduje uprawnienia.
| /api/devices | GET | — | {status: "success", devices: [...]} | login_required | Zwraca listę urządzeń dla aktywnego gospodarstwa.
| /api/device/toggle | POST | {device_id, home_id} | {status: "success", device: {...}} | login_required | Przełącza stan urządzenia; zwraca zaktualizowany rekord i emituje WebSocket.
| /api/device/create | POST | {name, type, room_id, home_id} | {status: "success", device_id: "..."} (201) | admin_required | Tworzy nowe urządzenie powiązane z `home_id` i `room_id`.
| /api/device/<id> | DELETE | — | {status: "success"} (200) / {status: "error", message: ...} | admin_required | Usuwa urządzenie z danego `home_id` (home_id z session lub argumentu).
| /api/automations | GET | — | {status: "success", automations: [...]} | login_required | Pobiera reguły automatyzacji dla aktywnego gospodarstwa.
| /api/automation/create | POST | {name, trigger, actions, home_id} | {status: "success", automation_id: "..."} (201) | admin_required | Tworzy automatyzację przypisaną do gospodarstwa.
| /api/home/users | GET | — | {status: "success", users: [...]} | login_required | Lista użytkowników przypisanych do aktywnego gospodarstwa.
| /api/home/user/add | POST | {email, role, home_id} | {status: "success"} | admin_required | Zaprasza/dodaje użytkownika do gospodarstwa z rolą (owner/admin/member).
| /api/home/user/remove | DELETE | {user_id, home_id} | {status: "success"} | owner_required | Usuwa użytkownika z gospodarstwa (wymagany właściciel).
| /api/home/<home_id> | DELETE | — | {status: "success"} | owner_required | Usuwa całe gospodarstwo (owner only), kasuje powiązane zasoby.
| /api/security/state | GET | — | {status: "success", state: "armed|disarmed", mode: ...} | login_required | Zwraca aktualny stan systemu bezpieczeństwa dla gospodarstwa.

Opis uwag:
- Walidacja payloadów realizowana jest przez `request.get_json()` oraz sprawdzenie wymaganych kluczy i typów (np. `isinstance(...)`).
- Kody HTTP: 200 OK dla sukcesu, 201 Created dla POST tworzących zasoby, 400 dla walidacji, 401/403 dla auth/authz, 404 dla brakujących zasobów.
- Wszystkie endpointy modyfikujące dane wymagają `home_id` lub korzystają z `session['current_home_id']` w celu zachowania izolacji między gospodarstwami; operacje DB zawsze wykonują WHERE home_id = %s.
