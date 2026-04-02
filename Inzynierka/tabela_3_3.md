| Operacja | sys-admin | Owner | Admin | Member |
|---|---:|---:|---:|---:|
| Przeglądanie listy gospodarstw | Tak | Tak | Tak | Tak |
| Tworzenie nowego gospodarstwa | Tak | Tak (dla własnych) | Tak (dla własnych) | Tak (dla własnych) |
| Usuwanie gospodarstwa | Tak | Tak | Nie | Nie |
| Dodawanie użytkowników do gospodarstwa | Tak | Tak | Tak | Nie |
| Usuwanie użytkowników z gospodarstwa | Tak | Tak | Tak (nie dla adminów/owner) | Nie |
| Zmiana ról użytkowników | Tak | Tak | Tak (nie można nadać Owner) | Nie |
| Tworzenie pomieszczenia | Tak | Tak | Tak | Nie |
| Usuwanie pomieszczenia | Tak | Tak | Tak | Nie |
| Tworzenie urządzenia | Tak | Tak | Tak | Nie |
| Toggle urządzenia | Tak | Tak | Tak | Tak |
| Usuwanie urządzenia | Tak | Tak | Tak | Nie |
| Tworzenie automatyzacji | Tak | Tak | Tak | Nie |
| Enable/disable automatyzacji | Tak | Tak | Tak | Nie |
| Trigger ręczny automatyzacji | Tak | Tak | Tak | Tak |
| Zmiana stanu alarmowego | Tak | Tak | Tak | Tylko odczyt |

**Uwagi implementacyjne**
- Model RBAC jest realizowany w `utils/multi_home_db_manager.py` przez metody `has_admin_access(user_id, home_id)` oraz `get_user_role_in_home(user_id, home_id)`.
- Dekorator `@admin_required` w `app/simple_auth.py` wywołuje `has_admin_access` i zwraca przekierowanie lub 403 gdy brak uprawnień.
- Dodatkowa kolumna `user_homes.permissions` (JSONB) umożliwia granularne uprawnienia (np. `manage_users`, `delete_devices`) — infrastruktura do obsługi istnieje, obecnie domyślnie pusta.

Tabela 3.3: Macierz uprawnień dla SmartHome Multi-Home (sys-admin, Owner, Admin, Member).
