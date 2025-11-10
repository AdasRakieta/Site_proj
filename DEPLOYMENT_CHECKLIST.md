# 🚀 Deployment Checklist - SmartHome + Journey Planner

## ✅ KROK 1: Przygotowanie - Sprawdź kontenery

### 1.1 Połącz się z Raspberry Pi
```bash
ssh pi@100.103.184.90
```

### 1.2 Sprawdź działające kontenery
```bash
docker ps
```

Powinny działać:
- `journey-planner-api` (port 5001)
- `journey-planner-web` (port 5173)

Jeśli nie działają:
```bash
cd ~/journey-planner  # lub inna ścieżka
docker-compose up -d
```

### 1.3 Sprawdź sieci Docker
```bash
docker network ls | grep journey
```

Powinna istnieć: `journey-stack_journey-planner-net`

---

## ✅ KROK 2: Portainer - Pull SmartHome Stack

### 2.1 Otwórz Portainer
```
https://malina.tail384b18.ts.net/portainer/
```

### 2.2 Idź do Stacks → smarthome-stack

### 2.3 Kliknij "Pull and redeploy"
- To pobierze najnowszy obraz z GitHub Container Registry
- Zrestartuje wszystkie kontenery

### 2.4 Poczekaj na zakończenie (około 1-2 minuty)

---

## ✅ KROK 3: Weryfikacja - Sprawdź logi

### 3.1 Sprawdź logi aplikacji SmartHome
```bash
docker logs smarthome_app --tail 50
```

**Szukaj:**
```
✓ Using PostgreSQL database backend
✓ URL prefixes configured: /smarthome (static: /smarthome/static)
✓ SmartHome system initialized
```

**Jeśli widzisz błędy:**
- Sprawdź zmienne środowiskowe: `docker exec smarthome_app env | grep URL_PREFIX`
- Powinno być: `URL_PREFIX=/smarthome`

### 3.2 Sprawdź logi nginx
```bash
docker logs smarthome_nginx --tail 50
```

**Jeśli są błędy 404:**
- Sprawdź czy nginx ma dostęp do sieci: `docker inspect smarthome_nginx | grep Networks`
- Powinny być: `default` i `journey-stack_journey-planner-net`

---

## ✅ KROK 4: Testowanie - SmartHome

### 4.1 Test root redirect
```bash
curl -I https://malina.tail384b18.ts.net/
```
**Oczekiwane:** `HTTP/2 301` z `Location: https://malina.tail384b18.ts.net/smarthome/`

### 4.2 Test SmartHome login
```bash
curl -I https://malina.tail384b18.ts.net/smarthome/
```
**Oczekiwane:** `HTTP/2 200` (lub 302 redirect na `/smarthome/login`)

### 4.3 Test statycznych plików
```bash
curl -I https://malina.tail384b18.ts.net/smarthome/static/css/style.css
```
**Oczekiwane:** `HTTP/2 200` z `Content-Type: text/css`

### 4.4 Test w przeglądarce
Otwórz: `https://malina.tail384b18.ts.net/smarthome/`

**Sprawdź DevTools (F12):**
- Wszystkie pliki CSS/JS powinny ładować się bez 404
- Ścieżki powinny być: `/smarthome/static/css/...`

---

## ✅ KROK 5: Testowanie - Journey Planner

### 5.1 Test frontend
```bash
curl -I https://malina.tail384b18.ts.net/journey/
```
**Oczekiwane:** `HTTP/2 200`

Jeśli **502 Bad Gateway:**
```bash
# Sprawdź czy kontenery działają
docker ps | grep journey

# Sprawdź czy nginx widzi kontenery
docker exec smarthome_nginx ping -c 1 journey-planner-web
docker exec smarthome_nginx ping -c 1 journey-planner-api

# Jeśli ping nie działa - problem z siecią
docker network inspect journey-stack_journey-planner-net
```

### 5.2 Test API
```bash
curl -I https://malina.tail384b18.ts.net/journey/api/health
```
**Oczekiwane:** `HTTP/2 200` (lub cokolwiek co zwraca backend)

---

## 🔧 ROZWIĄZYWANIE PROBLEMÓW

### Problem 1: 404 na `/smarthome/login`

**Diagnoza:**
```bash
# Sprawdź URL_PREFIX w kontenerze
docker exec smarthome_app env | grep URL_PREFIX

# Sprawdź logi Flask
docker logs smarthome_app | grep "URL prefixes"
```

**Rozwiązanie:**
1. W Portainerze: Stacks → smarthome-stack → Environment variables
2. Dodaj: `URL_PREFIX=/smarthome`
3. Redeploy stack

### Problem 2: Pliki statyczne 404

**Diagnoza:**
```bash
# Sprawdź czy Flask otrzymuje pełną ścieżkę
docker logs smarthome_app | grep "GET /smarthome/static"
```

**Jeśli Flask otrzymuje `/static/` zamiast `/smarthome/static/`:**
- Problem z nginx `proxy_pass`
- Sprawdź `default.conf`: powinno być `proxy_pass http://smarthome_app/smarthome/;`

### Problem 3: Journey Planner 502

**Diagnoza:**
```bash
# Sprawdź czy kontenery Journey działają
docker ps | grep journey

# Sprawdź czy są w tej samej sieci
docker network inspect journey-stack_journey-planner-net | grep -A 5 "Containers"
```

**Rozwiązanie A - Kontenery nie działają:**
```bash
cd ~/ścieżka/do/journey-planner
docker-compose up -d
```

**Rozwiązanie B - Nginx nie widzi kontenerów:**
```bash
# Dodaj nginx do sieci Journey
docker network connect journey-stack_journey-planner-net smarthome_nginx

# Lub redeploy stack w Portainerze (z poprawioną konfiguracją)
```

### Problem 4: Favicon 404

To normalne - dodaj favicon do nginx:
```bash
# Skopiuj favicon do kontenera (opcjonalne)
docker cp /path/to/favicon.ico smarthome_nginx:/etc/nginx/html/favicon.ico
```

Lub zignoruj - to kosmetyczny błąd.

---

## 📊 Oczekiwany stan po deployment

### Kontenery (docker ps):
```
smarthome_app           ✅ Up (port 5000)
smarthome_nginx         ✅ Up (port 80, 443)
journey-planner-api     ✅ Up (port 5001)
journey-planner-web     ✅ Up (port 5173)
```

### Zmienne środowiskowe (docker exec smarthome_app env):
```
URL_PREFIX=/smarthome
API_PREFIX=/smarthome/api       (zbudowane przez Python)
STATIC_PREFIX=/smarthome/static (zbudowane przez Python)
SOCKET_PREFIX=/smarthome/socket.io (zbudowane przez Python)
FLASK_ENV=production
```

### Sieci Docker:
```
smarthome_nginx:
  - default (komunikacja z smarthome_app)
  - journey-stack_journey-planner-net (komunikacja z Journey)
```

### URLe działające:
```
✅ https://malina.tail384b18.ts.net/ → 301 → /smarthome/
✅ https://malina.tail384b18.ts.net/smarthome/ → login page
✅ https://malina.tail384b18.ts.net/smarthome/static/css/style.css
✅ https://malina.tail384b18.ts.net/journey/ → Journey frontend
✅ https://malina.tail384b18.ts.net/journey/api/ → Journey API
```

---

## 🆘 Ostateczna pomoc

Jeśli nic nie działa po wykonaniu wszystkich kroków:

### Kompletny restart:
```bash
# Na Raspberry Pi
cd ~/VS_Code_Proj/Site_proj  # lub ścieżka do projektu

# Zatrzymaj wszystko
docker-compose down

# Usuń kontenery i sieci
docker rm -f smarthome_app smarthome_nginx
docker network rm smarthome-stack_default 2>/dev/null

# Pobierz najnowsze obrazy
docker pull ghcr.io/adasrakieta/site_proj/smarthome_app:latest
docker pull ghcr.io/adasrakieta/site_proj/smarthome_nginx:latest

# Uruchom ponownie przez Portainer
# Stacks → smarthome-stack → Pull and redeploy
```

### Sprawdź konfigurację nginx:
```bash
# Wyświetl aktualny config
docker exec smarthome_nginx cat /etc/nginx/conf.d/default.conf

# Powinien zawierać:
# - proxy_pass http://smarthome_app/smarthome/
# - upstream journey_planner_api
# - upstream journey_planner_web
```

---

## 📞 Debug commands

Przydatne komendy do debugowania:

```bash
# Logi na żywo (Ctrl+C aby zakończyć)
docker logs -f smarthome_app
docker logs -f smarthome_nginx

# Sprawdź wszystkie zmienne środowiskowe
docker exec smarthome_app env | sort

# Sprawdź sieci kontenera
docker inspect smarthome_nginx --format '{{json .NetworkSettings.Networks}}' | jq

# Test połączenia z Journey Planner z wnętrza nginx
docker exec smarthome_nginx wget -O- http://journey-planner-web:5173 2>&1

# Sprawdź czy Flask działa
docker exec smarthome_app curl localhost:5000/smarthome/

# Sprawdź routing nginx
docker exec smarthome_nginx nginx -T | grep -A 10 "location /smarthome"
```

---

## ✅ Checklist końcowy

Po deployment sprawdź:

- [ ] SmartHome działa: `https://malina.tail384b18.ts.net/smarthome/`
- [ ] CSS/JS się ładują (brak 404 w DevTools)
- [ ] Login działa
- [ ] Redirect z `/` na `/smarthome/` działa
- [ ] Journey frontend działa: `https://malina.tail384b18.ts.net/journey/`
- [ ] Journey API działa: `https://malina.tail384b18.ts.net/journey/api/`
- [ ] Logi nginx bez błędów 502/404
- [ ] Logi Flask pokazują: `URL prefixes configured: /smarthome`

Jeśli wszystko ✅ - deployment zakończony sukcesem! 🎉
