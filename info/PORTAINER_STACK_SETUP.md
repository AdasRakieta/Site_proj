# Instrukcja deployment w Portainer Stack

## ⚠️ WAŻNE: Portainer Stack nie używa plików `.env`!

Portainer Stack **nie czyta** plików `env_file` (jak `stack.env`) automatycznie.  
Zmienne środowiskowe muszą być ustawione **ręcznie w UI Portainera**.

---

## 📋 Wymagane zmienne środowiskowe

### Krok 1: Przejdź do Environment Variables w Portainer

1. Otwórz **Portainer**
2. Wybierz **Stacks** → Twój stack (np. `smarthome`)
3. Scroll w dół do sekcji **Environment variables**
4. Kliknij **+ Add environment variable**

### Krok 2: Dodaj następujące zmienne

Skopiuj i wklej te zmienne (zastąp wartości swoimi):

```
DB_HOST=100.103.184.90
DB_PORT=5432
DB_NAME=smarthome_multihouse
DB_USER=admin
DB_PASSWORD=Qwuizzy123.

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=smarthome.alertmail@gmail.com
SMTP_PASSWORD=pqvg eabu bmka mggk
ADMIN_EMAIL=szymon.przybysz2003@gmail.com

FLASK_ENV=production
SECRET_KEY=wygeneruj_losowy_32_znakowy_klucz

SERVER_HOST=0.0.0.0
SERVER_PORT=5000

IMAGE_TAG=latest
```

### Krok 3: Opcjonalne zmienne

```
REDIS_HOST=redis
REDIS_PORT=6379
ENABLE_REGISTRATION=true
ENABLE_MULTI_HOME=true
ASSET_VERSION=
```

---

## 🔧 Jak dodać zmienne w Portainer UI

### Metoda 1: Przez Web UI (łatwiejsza)

1. **Stacks** → **smarthome** → **Editor**
2. Scroll do **Environment variables**
3. Dla każdej zmiennej:
   - Name: `DB_HOST`
   - Value: `100.103.184.90`
   - Kliknij **+ Add**
4. Powtórz dla wszystkich zmiennych
5. Kliknij **Update the stack**

### Metoda 2: Przez plik .env lokalnie (docker-compose)

Jeśli używasz `docker-compose` lokalnie (nie przez Portainer Stack):

```bash
# Użyj pliku .env
docker-compose -f docker-compose.prod.yml --env-file .env up -d
```

Ale w **Portainer Stack to NIE DZIAŁA** - musisz użyć Metody 1!

---

## 🚀 Proces pełnego deployment w Portainer

### 1. Pierwszy deployment (setup)

```bash
# 1. Push kod do GitHub
git add .
git commit -m "Update"
git push origin main

# 2. Poczekaj na GitHub Actions (~3-5 min)
# Sprawdź: https://github.com/AdasRakieta/Site_proj/actions

# 3. W Portainer:
#    - Stacks → Add stack
#    - Name: smarthome
#    - Build method: Repository
#    - Repository URL: https://github.com/AdasRakieta/Site_proj
#    - Repository reference: refs/heads/main
#    - Compose path: docker-compose.prod.yml
#    
#    Environment variables (dodaj wszystkie):
#    DB_HOST=100.103.184.90
#    DB_NAME=smarthome_multihouse
#    ... (reszta zmiennych)
#
#    Deploy the stack
```

### 2. Aktualizacja (redeploy)

```bash
# 1. Push zmiany
git push origin main

# 2. Poczekaj na GitHub Actions

# 3. W Portainer:
#    Stacks → smarthome → ⟳ Update the stack
#    
#    Zaznacz:
#    ✅ Pull latest image versions
#    ✅ Re-pull image
#    ✅ Force redeployment
#
#    Update the stack
```

---

## 📝 Template zmiennych dla Portainer

Skopiuj to i wklej do notatnika, zastąp wartości, potem dodaj w Portainer:

```env
# === Database Configuration ===
DB_HOST=100.103.184.90
DB_PORT=5432
DB_NAME=smarthome_multihouse
DB_USER=admin
DB_PASSWORD=Qwuizzy123.

# === Email Configuration ===
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=smarthome.alertmail@gmail.com
SMTP_PASSWORD=pqvg eabu bmka mggk
ADMIN_EMAIL=szymon.przybysz2003@gmail.com

# === Flask Configuration ===
FLASK_ENV=production
SECRET_KEY=CHANGE_THIS_32_CHAR_KEY_NOW

# === Server Configuration ===
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

# === Docker Configuration ===
IMAGE_TAG=latest

# === Optional Redis ===
REDIS_HOST=
REDIS_PORT=6379

# === Optional Features ===
ENABLE_REGISTRATION=true
ENABLE_MULTI_HOME=true
ASSET_VERSION=
```

---

## ✅ Checklist przed deployment

- [ ] Wszystkie zmienne środowiskowe dodane w Portainer UI
- [ ] `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` ustawione poprawnie
- [ ] `SECRET_KEY` wygenerowany (min 32 znaki, losowy)
- [ ] `SMTP_*` skonfigurowane dla emaili
- [ ] GitHub Actions zakończył build (status ✓)
- [ ] W Portainer zaznaczone: Pull + Re-pull + Force redeployment

---

## 🔍 Weryfikacja po deployment

### 1. Sprawdź logi kontenera

```bash
docker logs smarthome_app
```

Powinno być:
```
✓ Using PostgreSQL database backend
✓ Multi-home context processor registered
✓ Connection pool initialized
🚀 Starting SmartHome Application
```

### 2. Sprawdź zmienne środowiskowe

```bash
docker exec smarthome_app env | grep -E "DB_HOST|ASSET_VERSION|SECRET_KEY"
```

### 3. Sprawdź czy działa

```bash
curl http://your-server:5000/api/ping
```

Powinno zwrócić: `{"status": "ok"}`

---

## ❌ Typowe błędy

### "Missing DB_HOST environment variable"

**Przyczyna:** Nie dodałeś zmiennych środowiskowych w Portainer UI

**Rozwiązanie:**
1. Stacks → smarthome → Editor
2. Scroll do Environment variables
3. Dodaj wszystkie wymagane zmienne
4. Update the stack

### "Cannot connect to database"

**Przyczyna:** Błędne dane w `DB_HOST`, `DB_USER` lub `DB_PASSWORD`

**Rozwiązanie:**
1. Sprawdź wartości zmiennych w Portainer
2. Przetestuj połączenie:
   ```bash
   docker exec smarthome_app python -c "from utils.db_manager import get_db_connection; get_db_connection()"
   ```

### Style nie aktualizują się

**Przyczyna:** Brak cache-busting lub stary obraz

**Rozwiązanie:**
1. W Portainer: ✅ Pull latest + ✅ Force redeployment
2. W przeglądarce: `Ctrl+Shift+R` (hard refresh)
3. Sprawdź `ASSET_VERSION`:
   ```bash
   docker exec smarthome_app env | grep ASSET_VERSION
   ```

---

## 🔐 Bezpieczeństwo

### NIGDY nie commituj prawdziwych wartości!

Plik `stack.env` w repo powinien mieć tylko **placeholdery**:

```env
DB_PASSWORD=CHANGE_THIS_SECURE_PASSWORD  # ← OK
SECRET_KEY=CHANGE_THIS_32_CHAR_KEY       # ← OK
```

Prawdziwe wartości **tylko w Portainer UI**!

### Generowanie SECRET_KEY

**Python:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**PowerShell:**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

Skopiuj output i wklej jako `SECRET_KEY` w Portainer.

---

## 📞 Quick Reference

**Portainer UI:**
```
Stacks → smarthome → Editor → Environment variables → Add
```

**Update stack:**
```
✅ Pull latest image versions
✅ Re-pull image  
✅ Force redeployment
→ Update the stack
```

**Weryfikacja:**
```bash
docker logs smarthome_app
docker exec smarthome_app env
curl http://localhost:5000/api/ping
```

---

**Ostatnia aktualizacja:** 16 października 2025  
**Dotyczy:** Portainer Stacks + docker-compose.prod.yml  
**Wersja:** 2.0
