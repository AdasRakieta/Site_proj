# Resetowanie Hasła Admin w Trybie JSON Fallback

## Problem
Gdy system działa w trybie JSON fallback (brak dostępu do bazy danych), hasło administratora `sys-admin` jest generowane losowo i wyświetlane tylko raz podczas pierwszej inicjalizacji. Email admina (`admin@localhost`) jest fikcyjny, więc funkcja resetowania hasła przez email nie działa.

## Rozwiązanie

### Opcja 1: Użyj skryptu resetowania hasła (ZALECANE)

Uruchom skrypt `reset_admin_password.py`:

```bash
python reset_admin_password.py
```

Skrypt:
1. Znajdzie użytkownika sys-admin w pliku konfiguracyjnym JSON
2. Wyświetli informacje o koncie
3. Poprosi o nowe hasło (minimum 8 znaków)
4. Zaktualizuje hasło w `app/smart_home_config.json`

**Przykład użycia:**
```
======================================================================
🔐 Reset Admin Password - JSON Fallback Mode
======================================================================

Found admin user:
  Username: sys-admin
  Email: admin@localhost
  User ID: xxx-xxx-xxx

Enter new password for sys-admin: ********
Confirm new password: ********

======================================================================
✓ Password successfully updated!
======================================================================

You can now login with:
  Username: sys-admin
  Password: YourNewPassword

⚠️  IMPORTANT: Save this password securely!
======================================================================
```

### Opcja 2: Edycja manualna (dla zaawansowanych)

Jeśli potrzebujesz bezpośrednio edytować konfigurację:

1. Otwórz plik `app/smart_home_config.json`
2. Znajdź sekcję `users.sys-admin`
3. Wygeneruj nowy hash hasła używając Python:

```python
from werkzeug.security import generate_password_hash
new_hash = generate_password_hash('TwojeNoweHaslo')
print(new_hash)
```

4. Zastąp wartość pola `password` nowym hashem
5. Zapisz plik

### Opcja 3: Usuń plik konfiguracyjny i rozpocznij od nowa

```bash
# UWAGA: To usunie wszystkie dane!
rm app/smart_home_config.json
python app_db.py
```

System utworzy nowy plik konfiguracyjny i **wyświetli nowe hasło admina**.

## Informacje podczas startupu

Gdy system startuje w JSON fallback mode, wyświetla:

```
======================================================================
🔐 ADMIN CREDENTIALS (JSON FALLBACK MODE)
======================================================================

   Username: sys-admin
   Role: admin
   Email: admin@localhost

⚠️  If you don't know the password, you can reset it:
   Run: python reset_admin_password.py
======================================================================
```

## Bezpieczeństwo

- Hasła są przechowywane jako bezpieczne hashe (Werkzeug PBKDF2)
- Oryginalne hasło NIE jest zapisywane w plain text
- Skrypt resetowania wymaga bezpośredniego dostępu do pliku konfiguracyjnego
- Nowe hasło jest wyświetlane tylko raz po resecie

## Troubleshooting

**Problem: `✗ Configuration file not found`**
- System nie działa w JSON fallback mode
- Sprawdź czy plik `app/smart_home_config.json` istnieje

**Problem: `✗ sys-admin user not found`**
- Plik konfiguracyjny jest uszkodzony
- Rozważ usunięcie pliku i restart systemu (UWAGA: utrata danych!)

**Problem: `✗ Password must be at least 8 characters long`**
- Hasło musi mieć minimum 8 znaków
- Użyj silnego hasła z kombinacją liter, cyfr i znaków specjalnych
