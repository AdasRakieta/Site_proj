# Przewodnik Deployment w Portainer

## 🚀 Problem z brakiem aktualizacji po redeploy

### Dlaczego zmiany nie są widoczne po redeploy?

Istnieje kilka powodów:

1. **Cache przeglądarki** - przeglądarka cache'uje stare CSS/JS
2. **Tag `latest` nie jest aktualizowany** - Docker cache używa starego obrazu
3. **Brak cache-busting** - brak parametru `?v=` w linkach do assetów
4. **Brak przebudowy obrazu** - Portainer nie pobiera nowego obrazu

---

## ✅ Rozwiązanie

### 1. Naprawiono cache-busting w szablonach

**Przed:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/home_select.css') }}">
```

**Po:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/home_select.css') }}?v={{ asset_version }}">
```

**Zaktualizowane pliki:**
- ✅ `home_select.html`
- ✅ `home_settings.html`
- ✅ `settings.html`
- ✅ `invite_accept.html`
- ✅ `error.html`
- ✅ `edit.html`

### 2. Dodano ASSET_VERSION do GitHub Actions

W `.github/workflows/docker-publish.yml` dodano:
```yaml
build-args: |
  ASSET_VERSION=${{ github.sha }}
```

Każdy build automatycznie dostaje unikalną wersję bazującą na Git commit SHA.

### 3. Zaktualizowano Dockerfile

```dockerfile
ARG ASSET_VERSION=dev
ENV ASSET_VERSION=${ASSET_VERSION}
```

Obraz Docker teraz zawiera zmienną środowiskową `ASSET_VERSION`.

---

## 📋 Instrukcja deployment w Portainer

### Metoda 1: Force Recreate (Zalecane)

1. **Wejdź do Portainer** → Stacks → `smarthome`
2. **Kliknij "Editor"**
3. **Scroll na dół**
4. **Zaznacz opcje:**
   - ✅ **Re-pull images** - pobierze najnowszy obraz z registry
   - ✅ **Force recreate** - wymuś odtworzenie kontenerów
5. **Kliknij "Update the stack"**

### Metoda 2: Używanie konkretnego SHA (Najbezpieczniejsze)

Zamiast używać `latest`, użyj konkretnego commit SHA:

1. **Sprawdź ostatni commit SHA** w GitHub:
   ```
   https://github.com/AdasRakieta/Site_proj/commits/main
   ```
   Przykład: `sha-a1b2c3d`

2. **W Portainer edytuj stack:**
   ```yaml
   services:
     app:
       image: ghcr.io/adasrakieta/site_proj/smarthome_app:sha-a1b2c3d
   ```

3. **Update stack** z opcjami:
   - ✅ Re-pull images
   - ✅ Force recreate

### Metoda 3: Poprzez Portainer Webhooks (Automatyczne)

1. **W Portainer**: Settings → Webhooks → Create Webhook
2. **Skopiuj URL webhooka**
3. **W GitHub**: Settings → Webhooks → Add webhook
   - Payload URL: `<portainer_webhook_url>`
   - Content type: `application/json`
   - Trigger: `Just the push event`
4. **Zapisz**

Teraz każdy push do `main` automatycznie redeploy'uje stack!

---

## 🔍 Weryfikacja deployment

### 1. Sprawdź wersję obrazu

```bash
docker inspect smarthome_app | grep ASSET_VERSION
```

Powinno pokazać commit SHA, np.:
```
"ASSET_VERSION=a1b2c3d4e5f6..."
```

### 2. Sprawdź w przeglądarce

1. Otwórz DevTools (F12)
2. Zakładka **Network**
3. Odśwież stronę (Ctrl+Shift+R - hard refresh)
4. Znajdź `home_select.css`
5. Sprawdź URL - powinien zawierać `?v=<sha>`

Przykład:
```
/static/css/home_select.css?v=a1b2c3d4e5f6
```

### 3. Sprawdź logi kontenera

```bash
docker logs smarthome_app | grep "ASSET_VERSION\|asset_version"
```

---

## 🛠️ Rozwiązywanie problemów

### Problem: Nadal widzę stare style

**Rozwiązanie:**

1. **Hard refresh w przeglądarce:**
   - Chrome/Edge: `Ctrl+Shift+R` (Windows) lub `Cmd+Shift+R` (Mac)
   - Firefox: `Ctrl+F5`

2. **Wyczyść cache przeglądarki:**
   - Chrome: Settings → Privacy → Clear browsing data → Cached images and files

3. **Sprawdź czy nowy obraz został pobrany:**
   ```bash
   docker images | grep smarthome_app
   ```
   
   Jeśli są 2 obrazy z tym samym tagiem ale różnymi ID, usuń stary:
   ```bash
   docker image prune -a
   ```

4. **Wymuś restart kontenera:**
   ```bash
   docker restart smarthome_app
   ```

### Problem: Portainer nie pobiera nowego obrazu

**Przyczyna:** Używasz tagu `latest` i Docker myśli, że już go ma.

**Rozwiązanie:**

1. **Zatrzymaj stack w Portainer**

2. **Usuń stare obrazy:**
   ```bash
   docker rmi ghcr.io/adasrakieta/site_proj/smarthome_app:latest
   docker rmi ghcr.io/adasrakieta/site_proj/smarthome_nginx:latest
   ```

3. **Uruchom stack ponownie** z opcją "Re-pull images"

### Problem: GitHub Actions nie zbudował nowego obrazu

**Sprawdź:**

1. **GitHub Actions status:**
   ```
   https://github.com/AdasRakieta/Site_proj/actions
   ```

2. **Czy workflow się wykonał?**
   - Jeśli nie, wykonaj ręcznie: Actions → Build and Publish → Run workflow

3. **Czy jest nowy tag SHA w registry?**
   ```
   https://github.com/AdasRakieta/Site_proj/pkgs/container/site_proj%2Fsmarthome_app
   ```

---

## 📝 Checklist przed każdym deployment

- [ ] Commitnij i pushuj zmiany do `main`
- [ ] Poczekaj aż GitHub Actions zakończy build (~3-5 minut)
- [ ] W Portainer: Re-pull images + Force recreate
- [ ] Po deployment: Hard refresh w przeglądarce (Ctrl+Shift+R)
- [ ] Zweryfikuj w DevTools czy nowe pliki są załadowane

---

## 💡 Best Practices

### 1. Używaj konkretnych tagów SHA w produkcji

Zamiast:
```yaml
image: ghcr.io/.../smarthome_app:latest
```

Użyj:
```yaml
image: ghcr.io/.../smarthome_app:sha-a1b2c3d
```

### 2. Zawsze używaj Force Recreate przy update

W Portainer **ZAWSZE** zaznaczaj:
- ✅ Re-pull images
- ✅ Force recreate

### 3. Monitoruj logi podczas deployment

```bash
docker logs -f smarthome_app
```

### 4. Testuj lokalnie przed push

```bash
docker-compose -f docker-compose.prod.yml up --build
```

---

## 🔄 Workflow deployment

```
1. Edytuj kod lokalnie
   ↓
2. Commit & Push do GitHub
   ↓
3. GitHub Actions buduje nowy obraz
   ↓
4. W Portainer: Update stack
   - Re-pull images ✓
   - Force recreate ✓
   ↓
5. Hard refresh w przeglądarce (Ctrl+Shift+R)
   ↓
6. ✅ Gotowe!
```

---

## 📞 Szybka pomoc

**Szybkie komendy:**

```bash
# Sprawdź czy kontener używa nowego obrazu
docker inspect smarthome_app | grep -A 5 Image

# Sprawdź ASSET_VERSION
docker exec smarthome_app env | grep ASSET_VERSION

# Wymuszony restart
docker restart smarthome_app

# Wyczyść cache Docker
docker system prune -a

# Pobierz najnowszy obraz ręcznie
docker pull ghcr.io/adasrakieta/site_proj/smarthome_app:latest
```

---

**Ostatnia aktualizacja:** 16 października 2025  
**Dotyczy wersji:** 2.0+  
**Status:** ✅ Wszystkie problemy cache-busting naprawione
