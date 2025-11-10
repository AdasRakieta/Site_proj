# URL Prefix Configuration

## Cel

System SmartHome może działać zarówno pod rootem (`/`) jak i pod podścieżką (np. `/smarthome/`) – zależnie od konfiguracji nginx i środowiska (development/production).

Aby ułatwić przełączanie między środowiskami, wszystkie ścieżki URL (do statycznych zasobów, API, WebSocket) są konfigurowane poprzez zmienne środowiskowe.

## Zmienne środowiskowe

Dodaj do pliku `.env`:

```bash
# Production (nginx /smarthome/ path):
URL_PREFIX=/smarthome
API_PREFIX=/smarthome/api
STATIC_PREFIX=/smarthome/static
SOCKET_PREFIX=/smarthome/socket.io

# Development (root path):
# URL_PREFIX=
# API_PREFIX=/api
# STATIC_PREFIX=/static
# SOCKET_PREFIX=/socket.io
```

## Użycie w szablonach

**WAŻNE:** Flask's `url_for('static', ...)` automatycznie dodaje `/static/` do ścieżki, więc używamy `URL_PREFIX`, a nie `STATIC_PREFIX`!

Zamiast hardcoded ścieżek:

```html
<!-- ❌ Złe (hardcoded) -->
<link rel="stylesheet" href="/smarthome/static/css/style.css">
<script src="/smarthome/static/js/app.js"></script>
```

Używaj zmiennych globalnych Jinja:

```html
<!-- ✅ Dobre (konfigurowalne) -->
<link rel="stylesheet" href="{{ URL_PREFIX }}{{ url_for('static', filename='css/style.css') }}">
<script src="{{ URL_PREFIX }}{{ url_for('static', filename='js/app.js') }}">
<img src="{{ URL_PREFIX }}{{ url_for('static', filename='icons/home.png') }}">
```

**Uwaga:** Używamy `URL_PREFIX`, ponieważ `url_for('static', filename='...')` zwraca `/static/...`, więc:
- `URL_PREFIX` = `/smarthome`
- `url_for('static', filename='css/style.css')` = `/static/css/style.css`
- **Wynik:** `/smarthome/static/css/style.css` ✅

Jeśli użyjesz `STATIC_PREFIX`, otrzymasz podwójne `/static/`:
- `STATIC_PREFIX` = `/smarthome/static`
- `url_for('static', filename='css/style.css')` = `/static/css/style.css`
- **Wynik:** `/smarthome/static/static/css/style.css` ❌

## Dostępne zmienne w szablonach

- `URL_PREFIX` – główny prefix aplikacji (np. `/smarthome`)
- `API_PREFIX` – prefix dla API (np. `/smarthome/api`)
- `STATIC_PREFIX` – prefix dla statycznych zasobów (np. `/smarthome/static`)
- `SOCKET_PREFIX` – prefix dla WebSocket (np. `/smarthome/socket.io`)

## Przełączanie środowisk

### Development (lokalnie, root path)

W `.env`:
```bash
URL_PREFIX=
API_PREFIX=/api
STATIC_PREFIX=/static
SOCKET_PREFIX=/socket.io
```

Aplikacja działa pod `http://localhost:5000/`

### Production (Portainer, nginx subpath)

W `.env` lub w zmiennych środowiskowych Portainera:
```bash
URL_PREFIX=/smarthome
API_PREFIX=/smarthome/api
STATIC_PREFIX=/smarthome/static
SOCKET_PREFIX=/smarthome/socket.io
```

Aplikacja działa pod `https://malina.tail384b18.ts.net/smarthome/`

## Jak to działa

1. Zmienne środowiskowe są ładowane przez `python-dotenv` w `app_db.py`
2. Flask's `APPLICATION_ROOT` jest ustawione na podstawie `URL_PREFIX`, co sprawia, że `url_for()` i `redirect()` automatycznie dodają prefix
3. W `setup_context_processors()` przekazujemy zmienne do Jinja jako globals:
   ```python
   url_prefix = os.getenv('URL_PREFIX', '/smarthome')
   if url_prefix and url_prefix != '/':
       self.app.config['APPLICATION_ROOT'] = url_prefix
   self.app.jinja_env.globals.update(URL_PREFIX=url_prefix, ...)
   ```
4. Szablony używają `{{ URL_PREFIX }}{{ url_for('static', ...) }}`
5. Flask's `redirect(url_for('login'))` automatycznie dodaje `/smarthome/login` w produkcji
6. Zmiana wartości w `.env` → restart aplikacji → wszystkie ścieżki się aktualizują

## Zalety

- ✅ Jedna zmiana w `.env` zamiast edycji 100+ plików
- ✅ Łatwe przełączanie dev ↔ prod
- ✅ Brak hardcoded ścieżek w kodzie
- ✅ Kompatybilność z nginx path-based routing
- ✅ Łatwe testowanie lokalnie (bez nginx)

## Aktualizacja istniejących szablonów

Wszystkie główne szablony (`templates/*.html`) zostały zaktualizowane, aby używały zmiennych globalnych zamiast hardcoded `/smarthome`.

Jeśli dodajesz nowy szablon, pamiętaj:
```html
{{ STATIC_PREFIX }}{{ url_for('static', filename='...') }}
```

Nie:
```html
/smarthome/static/...
```
