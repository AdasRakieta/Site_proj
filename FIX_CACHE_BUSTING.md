# Fix: Brak aktualizacji stylów po redeploy w Portainer

## 🎯 Problem

Po push'niu zmian do `main` i redeploy w Portainer, **style i przyciski nie aktualizowały się** na stronie `/home/select`.

---

## 🔍 Przyczyny

1. **Brak cache-busting** - template'y nie miały `?v={{ asset_version }}` w linkach CSS
2. **Cache przeglądarki** - przeglądarka używała starego CSS z cache
3. **Brak ASSET_VERSION** - obraz Docker nie miał zmiennej środowiskowej z wersją
4. **Nieprawidłowe przyciski** - `<button href>` zamiast `<a href>`

---

## ✅ Rozwiązanie

### 1. Dodano cache-busting do wszystkich template'ów

**Przed:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/home_select.css') }}">
```

**Po:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/home_select.css') }}?v={{ asset_version }}">
```

**Zaktualizowane pliki:**
- `templates/home_select.html`
- `templates/home_settings.html`
- `templates/settings.html`
- `templates/invite_accept.html`
- `templates/error.html`
- `templates/edit.html`

### 2. Naprawiono przyciski w home_select.html

**Przed:**
```html
<button href="/home/create" class="btn-primary">
```

**Po:**
```html
<a href="/home/create" class="btn-primary">
```

### 3. Dodano ASSET_VERSION do GitHub Actions

W `.github/workflows/docker-publish.yml`:
```yaml
build-args: |
  ASSET_VERSION=${{ github.sha }}
```

### 4. Zaktualizowano Dockerfile.app

```dockerfile
ARG ASSET_VERSION=dev
ENV ASSET_VERSION=${ASSET_VERSION}
```

---

## 📝 Jak działa teraz

1. **Push do GitHub** → GitHub Actions buduje obraz z unikalnym SHA
2. **Docker image** zawiera `ASSET_VERSION=<commit_sha>`
3. **Template'y** generują linki z `?v=<commit_sha>`
4. **Przeglądarka** widzi nowy URL i pobiera świeże pliki CSS/JS

**Przykład:**
```
/static/css/home_select.css?v=a1b2c3d4e5f6
```

Każdy commit ma unikalną wersję → cache przeglądarki jest automatycznie invalidowany!

---

## 🚀 Instrukcja deployment w Portainer

### Krok 1: Push zmian
```bash
git add .
git commit -m "Your changes"
git push origin main
```

### Krok 2: Poczekaj na GitHub Actions
Sprawdź status: https://github.com/AdasRakieta/Site_proj/actions

### Krok 3: Update w Portainer
1. Stacks → `smarthome` → Editor
2. Zaznacz:
   - ✅ **Re-pull images**
   - ✅ **Force recreate**
3. Kliknij **Update the stack**

### Krok 4: Hard refresh w przeglądarce
- Windows: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

---

## ✅ Weryfikacja

### Sprawdź w przeglądarce (DevTools)

1. Otwórz DevTools (F12)
2. Network tab
3. Odśwież stronę
4. Znajdź `home_select.css`
5. Sprawdź URL - powinien mieć `?v=<sha>`

### Sprawdź w kontenerze

```bash
docker exec smarthome_app env | grep ASSET_VERSION
```

Powinno zwrócić:
```
ASSET_VERSION=a1b2c3d4e5f6...
```

---

## 📚 Dodatkowe zasoby

- **[PORTAINER_DEPLOYMENT.md](PORTAINER_DEPLOYMENT.md)** - Pełny przewodnik deployment
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Dokumentacja ogólna
- **[CHANGELOG_ENV_UNIFICATION.md](CHANGELOG_ENV_UNIFICATION.md)** - Historia zmian

---

## 🎉 Rezultat

✅ **Style aktualizują się automatycznie** po każdym deploy  
✅ **Przyciski działają poprawnie**  
✅ **Cache przeglądarki nie jest problemem**  
✅ **Proces deployment jest prosty i przewidywalny**

---

**Data:** 16 października 2025  
**Status:** ✅ Naprawione i przetestowane  
**Dotyczy:** SmartHome Multi-Home v2.0+
