# Szybki Start - System Backup JSON

## 🚀 Pierwsze Uruchomienie (bez PostgreSQL)

### Krok 1: Uruchom Aplikację
```bash
python app_db.py
```

### Krok 2: Zapisz Hasło
Aplikacja wyświetli w logach:
```
======================================================================
🔧 JSON BACKUP MODE ACTIVATED
======================================================================
📄 Configuration file created: app/smart_home_config.json
👤 Default admin user created:
   Username: sys-admin
   Password: xY9@kL2$pQ5!mN8z
======================================================================
⚠️  IMPORTANT: Save these credentials! They will not be shown again.
======================================================================
```

**⚠️ WAŻNE:** Zapisz to hasło! Nie będzie ponownie wyświetlone.

### Krok 3: Zaloguj Się
- Otwórz przeglądarkę: `http://localhost:5000`
- Username: `sys-admin`
- Password: (hasło z logów)

### Krok 4: Gotowe!
System jest w pełni funkcjonalny:
- ✅ Zarządzanie pokojami
- ✅ Sterowanie urządzeniami
- ✅ Automatyzacje
- ✅ Ustawienia bezpieczeństwa
- ✅ Wszystkie funkcje administracyjne

## 🔄 Przełączenie na PostgreSQL (później)

Gdy będziesz gotowy używać PostgreSQL:

### Krok 1: Zainstaluj PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows - pobierz installer z postgresql.org
```

### Krok 2: Utwórz Bazę Danych
```sql
CREATE DATABASE smarthome_multihouse;
CREATE USER smarthome_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE smarthome_multihouse TO smarthome_user;
```

### Krok 3: Importuj Schemat
```bash
psql -U smarthome_user -d smarthome_multihouse -f backups/db_backup.sql
```

### Krok 4: Skonfiguruj Zmienne Środowiskowe
Utwórz plik `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smarthome_multihouse
DB_USER=smarthome_user
DB_PASSWORD=secure_password
```

### Krok 5: Zrestartuj Aplikację
```bash
python app_db.py
```

Logi pokażą:
```
✓ Using PostgreSQL database backend
✓ PostgreSQL database connected successfully
✓ SmartHome system initialized with PostgreSQL backend
```

## ❓ FAQ

### Q: Zapomniałem hasła sys-admin, co robić?
**A:** Usuń plik `app/smart_home_config.json` i uruchom aplikację ponownie. Nowe hasło zostanie wygenerowane.

```bash
# Linux/macOS
rm app/smart_home_config.json
python app_db.py

# Windows
del app\smart_home_config.json
python app_db.py
```

### Q: Czy mogę zmienić hasło sys-admin?
**A:** Tak, możesz to zrobić z poziomu panelu administracyjnego po zalogowaniu, lub ręcznie edytując plik JSON (wymaga zahashowania hasła).

### Q: Gdzie są przechowywane dane w trybie JSON?
**A:** W pliku `app/smart_home_config.json`. Backup automatyczny: `app/smart_home_config.json.backup`

### Q: Czy mogę używać obu systemów jednocześnie?
**A:** System automatycznie wybiera PostgreSQL jeśli jest dostępny. JSON jest używany jako backup/fallback.

### Q: Co się stanie z danymi JSON gdy przejdę na PostgreSQL?
**A:** Dane JSON pozostają nietknięte. Musisz ręcznie przenieść dane jeśli chcesz je zachować. Możesz też użyć obu systemów niezależnie.

### Q: Jak sprawdzić w jakim trybie pracuje system?
**A:** Sprawdź logi startowe:
- PostgreSQL: `✓ Using PostgreSQL database backend`
- JSON: `⚠ Falling back to JSON file backend`

### Q: Czy JSON backup jest bezpieczny dla produkcji?
**A:** JSON backup jest bezpieczny ale:
- ✅ Dobry dla małych instalacji (1-5 użytkowników)
- ✅ Dobry dla developmentu i testowania
- ⚠️ Nie zalecany dla dużych instalacji (>10 użytkowników)
- ⚠️ Brak transakcji (ryzyko przy współbieżnym zapisie)
- ⚠️ PostgreSQL daje lepszą wydajność i bezpieczeństwo

## 🔧 Rozwiązywanie Problemów

### Problem: "Permission denied" przy zapisie pliku JSON
```bash
# Linux/macOS
chmod 666 app/smart_home_config.json

# Windows (PowerShell jako Admin)
icacls app\smart_home_config.json /grant Users:F
```

### Problem: System nie przełącza się na JSON
**Sprawdź:**
1. Czy plik `utils/json_backup_manager.py` istnieje?
2. Czy wszystkie zależności są zainstalowane?
   ```bash
   pip install -r requirements.txt
   ```
3. Sprawdź logi - czy są błędy importu?

### Problem: Hasło nie pojawia się w logach
**Przyczyna:** Plik `smart_home_config.json` już istniał przed uruchomieniem.

**Rozwiązanie:** Usuń plik i uruchom ponownie (patrz FAQ powyżej).

## 📊 Przykłady Użycia

### Przykład 1: Dodanie Pokoju
Po zalogowaniu jako sys-admin:
1. Przejdź do "Zarządzanie Pokojami"
2. Kliknij "Dodaj Pokój"
3. Wpisz nazwę pokoju
4. Kliknij "Zapisz"

Dane zapisują się automatycznie w `app/smart_home_config.json`.

### Przykład 2: Dodanie Urządzenia
1. Przejdź do wybranego pokoju
2. Kliknij "Dodaj Urządzenie"
3. Wybierz typ (Przycisk/Termostat)
4. Wpisz nazwę
5. Kliknij "Zapisz"

### Przykład 3: Tworzenie Automatyzacji
1. Przejdź do "Automatyzacje"
2. Kliknij "Nowa Automatyzacja"
3. Ustaw wyzwalacz (np. "Przycisk włączony")
4. Ustaw akcję (np. "Włącz światło")
5. Kliknij "Zapisz"

## 🎯 Najlepsze Praktyki

### ✅ DO
- Zapisz hasło sys-admin w bezpiecznym miejscu
- Regularnie twórz backupy pliku JSON
- Używaj PostgreSQL w środowisku produkcyjnym
- Testuj na JSON przed wdrożeniem PostgreSQL

### ❌ DON'T
- Nie commituj pliku `smart_home_config.json` do Git (zawiera hashe haseł)
- Nie udostępniaj pliku JSON publicznie
- Nie edytuj ręcznie JSON bez backupu
- Nie używaj JSON dla >10 współbieżnych użytkowników

## 📚 Dalsze Czytanie

- [Pełna Dokumentacja JSON Backup](JSON_BACKUP_SYSTEM.md)
- [Quick Start Guide](QUICK_START.md)
- [PostgreSQL Setup Guide](POSTGRESQL_SETUP.md)
- [API Documentation](API_DOCUMENTATION.md)

## 💡 Wskazówki

### Backup Ręczny
```bash
# Utwórz backup przed ważnymi zmianami
cp app/smart_home_config.json app/smart_home_config.json.manual-backup
```

### Import Danych z JSON do PostgreSQL
```python
# Skrypt pomocniczy (przykład)
from utils.json_backup_manager import JSONBackupManager
from utils.smart_home_db_manager import SmartHomeDatabaseManager

# Wczytaj z JSON
json_mgr = JSONBackupManager()
config = json_mgr.get_config()

# Zapisz do PostgreSQL
db_mgr = SmartHomeDatabaseManager()
# ... kod importu danych ...
```

### Monitoring
```bash
# Sprawdź rozmiar pliku JSON
du -h app/smart_home_config.json

# Ostatnia modyfikacja
ls -lh app/smart_home_config.json
```

## 🆘 Potrzebujesz Pomocy?

- 📧 Email: support@example.com
- 💬 Discord: [Link do serwera]
- 🐛 Issues: [GitHub Issues](https://github.com/...)
- 📖 Wiki: [GitHub Wiki](https://github.com/.../wiki)

---

**Autor:** SmartHome Team  
**Wersja:** 1.0.0  
**Data:** 2026-01-10
