| Metoda | Parametry | Typ zwracany | Opis |
|---|---|---:|---|
| `get_cursor` | `self` | context manager -> `cursor` or `None` | Zarządza cyklem życia transakcji: otwiera kursora, yielduje go, commit/rollback; zwraca `None` w trybie JSON fallback. |
| `update_device` | `self, device_id, user_id, **kwargs` | `bool` | Aktualizuje rekord urządzenia po weryfikacji dostępu użytkownika; buduje dynamiczny `UPDATE` z przekazanych pól; zwraca True gdy zmodyfikowano wiersz. |
| `get_device` | `self, device_id` | `dict` / `None` | Pobiera pojedyncze urządzenie (kolumny jako dict); zwraca `None` jeśli brak. |
| `get_devices_by_home` | `self, home_id` | `list[dict]` | Zwraca listę urządzeń należących do domu (opcjonalne filtry/paginacja). |
| `create_device` | `self, home_id, room_id, device_data` | `UUID` | Tworzy nowe urządzenie, zwraca jego `id`. |
| `get_buttons` | `self, device_id=None` | `list[dict]` | Pobiera przyciski (akcje) dla urządzeń; gdy `device_id` podane — filtrowanie. |
| `create_home` | `self, owner_user_id, home_data` | `UUID` | Tworzy nowy dom (rekord homes) i przypisuje właściciela; obsługuje inicjalizację ustawień. |
| `add_user_to_home` | `self, home_id, user_id, role` | `bool` | Dodaje użytkownika do domu z rolą (member/admin); zwraca True przy sukcesie. |
| `remove_user_from_home` | `self, home_id, user_id` | `bool` | Usuwa powiązanie użytkownika z domem, honoruje ograniczenia (np. nie usuwać ostatniego właściciela). |
| `delete_home` | `self, home_id` | `bool` | Usuwa dom z kaskadowym usunięciem powiązanych rekordów (zgodnie z FK) lub oznacza jako usunięty; zwraca True gdy usunięto. |
| `has_home_access` | `self, user_id, home_id` | `bool` | Sprawdza czy użytkownik ma dostęp do danego domu (member/admin). |
| `has_admin_access` | `self, user_id, home_id` | `bool` | Sprawdza uprawnienia administracyjne (owner/admin) dla operacji krytycznych. |
| `get_automations` | `self, home_id` | `list[dict]` | Pobiera automatyzacje powiązane z domem, wraz z warunkami/akcjami (JSONB). |
| `create_automation` | `self, home_id, automation_payload` | `UUID` | Tworzy nową automatyzację (zapis JSONB), zwraca `id`. |
| `update_automation` | `self, automation_id, user_id, **kwargs` | `bool` | Aktualizuje automatyzację po weryfikacji dostępu; zwraca True jeśli zmodyfikowano. |
| `get_rooms` | `self, home_id` | `list[dict]` | Pobiera listę pokoi w domu (używane przez UI i walidację room_id). |
| `create_room` | `self, home_id, room_data` | `UUID` | Dodaje pokój do domu; zwraca jego `id`. |

_Uwaga:_ Opisy metod są skondensowane; implementacja powinna zawsze używać `with self.get_cursor()` oraz wywołań `has_home_access`/`has_admin_access` przed modyfikacjami, aby zachować model defense-in-depth i atomowość transakcji.
