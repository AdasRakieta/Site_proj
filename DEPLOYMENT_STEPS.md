# 🚀 Deployment Steps - SmartHome + Journey Planner

## ✅ Status konfiguracji

- ✅ Nginx `default.conf` - skonfigurowany z routing dla obu aplikacji
- ✅ `docker-compose.yml` - volume mount dla Journey Planner odkomenty
- ✅ Journey Planner API działa na porcie 5001 (PM2)
- ⏳ Deployment na Raspberry Pi - do wykonania

---

## 📋 Kroki deployment na Raspberry Pi

### Krok 1: Commit i push zmian do GitHub

Na swoim komputerze:

```bash
cd C:\Users\pz_przybysz\Documents\git\Site_proj

# Dodaj zmienione pliki
git add docker-compose.yml nginx/default.conf NGINX_SETUP.md info/GITHUB_CONTAINER_REGISTRY.md

# Commit
git commit -m "Enable Journey Planner nginx routing and volume mount"

# Push do GitHub
git push origin main
```

---

### Krok 2: SSH do Raspberry Pi

```bash
ssh pi@malina.tail384b18.ts.net
```

---

### Krok 3: Aktualizacja SmartHome projektu

```bash
# Przejdź do katalogu projektu
cd ~/Site_proj

# Pobierz najnowsze zmiany
git pull origin main

# Sprawdź czy zmiany są widoczne
cat nginx/default.conf | grep journey
cat docker-compose.yml | grep journey-planner
```

Powinno pokazać:
- `upstream journey_planner_app` w nginx config
- `/home/pi/journey-planner/client/dist:/srv/journey-planner:ro` w docker-compose

---

### Krok 4: Sprawdź czy Journey Planner frontend jest zbudowany

```bash
# Sprawdź czy dist folder istnieje i zawiera pliki
ls -la /home/pi/journey-planner/client/dist/

# Powinno pokazać:
# - index.html
# - assets/ (z JS i CSS)
# - vite.svg (lub inne assets)
```

❌ **Jeśli folder nie istnieje lub jest pusty:**

```bash
cd /home/pi/journey-planner/client

# Upewnij się że base path jest ustawiony w vite.config.ts
cat vite.config.ts | grep base
# Powinno być: base: '/journey/',

# Build frontend
npm run build

# Sprawdź ponownie
ls -la dist/
```

---

### Krok 5: Sprawdź czy Journey Planner API działa

```bash
# Sprawdź status PM2
pm2 status

# Powinno pokazać:
# │ journey-planner-api │ online │

# Test API bezpośrednio
curl http://localhost:5001/api/health

# Powinno zwrócić JSON z statusem
```

❌ **Jeśli API nie działa:**

```bash
# Zobacz logi
pm2 logs journey-planner-api --lines 50

# Restart jeśli potrzebne
pm2 restart journey-planner-api

# Test ponownie
curl http://localhost:5001/api/health
```

---

### Krok 6: Zrestartuj nginx container z nową konfiguracją

```bash
cd ~/Site_proj

# Metoda 1: Docker Compose (zalecane)
docker-compose pull nginx    # Pobierz najnowszy obraz z GHCR
docker-compose up -d nginx   # Restart z nową konfiguracją

# Metoda 2: Jeśli używasz Portainera
# Przejdź do Portainer Web UI i zaktualizuj stack
```

---

### Krok 7: Sprawdź logi nginx

```bash
# Zobacz ostatnie logi
docker logs smarthome_nginx --tail 50

# Sprawdź czy nie ma błędów w konfiguracji
docker exec smarthome_nginx nginx -t

# Powinno pokazać:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

### Krok 8: Testowanie wszystkich endpointów

#### Test 1: SmartHome (główna aplikacja)

```bash
# Test głównej strony
curl -k https://malina.tail384b18.ts.net/ | head -20

# Test API
curl -k https://malina.tail384b18.ts.net/api/rooms

# Test health
curl -k https://malina.tail384b18.ts.net/health
```

#### Test 2: Journey Planner API

```bash
# Test przez nginx
curl -k https://malina.tail384b18.ts.net/journey/api/health

# Powinno zwrócić JSON, np:
# {"status":"ok","timestamp":"2025-11-10T..."}
```

#### Test 3: Journey Planner Frontend

```bash
# Test czy index.html jest dostępny
curl -k https://malina.tail384b18.ts.net/journey/ | head -20

# Powinno pokazać HTML z Vite app
```

#### Test 4: Management Tools

```bash
# Portainer
curl -k https://malina.tail384b18.ts.net/portainer/ | head -10

# Grafana
curl -k https://malina.tail384b18.ts.net/grafana/ | head -10
```

---

### Krok 9: Testowanie w przeglądarce

Otwórz w przeglądarce (z komputera w sieci Tailscale):

1. **SmartHome**: https://malina.tail384b18.ts.net/
   - Powinien załadować się dashboard SmartHome
   - Sprawdź login/rooms/devices

2. **Journey Planner**: https://malina.tail384b18.ts.net/journey/
   - Powinien załadować się Journey Planner UI
   - Sprawdź czy API calls działają (otwórz DevTools → Network)

3. **Portainer**: https://malina.tail384b18.ts.net/portainer/
   - Powinien pokazać Portainer UI

4. **Grafana**: https://malina.tail384b18.ts.net/grafana/
   - Powinien pokazać Grafana login

---

## 🔧 Troubleshooting

### Problem: Nginx nie startuje

```bash
# Zobacz pełne logi
docker logs smarthome_nginx

# Sprawdź konfigurację
docker exec smarthome_nginx cat /etc/nginx/conf.d/default.conf

# Test składni
docker exec smarthome_nginx nginx -t
```

**Rozwiązanie:** Jeśli błąd składni, sprawdź czy `nginx/default.conf` został poprawnie skopiowany.

---

### Problem: Journey Planner API 502 Bad Gateway

```bash
# Sprawdź czy API działa
curl http://localhost:5001/api/health

# Sprawdź logi PM2
pm2 logs journey-planner-api

# Sprawdź czy port 5001 jest otwarty
sudo lsof -i :5001
```

**Rozwiązanie:**
- Jeśli API nie działa: `pm2 restart journey-planner-api`
- Jeśli port zajęty: Sprawdź co używa portu: `sudo lsof -i :5001`

---

### Problem: Journey Planner frontend 404

```bash
# Sprawdź czy pliki są dostępne w kontenerze nginx
docker exec smarthome_nginx ls -la /srv/journey-planner/

# Sprawdź czy folder na hoście ma pliki
ls -la /home/pi/journey-planner/client/dist/
```

**Rozwiązanie:**
- Jeśli folder pusty: Zbuduj frontend: `cd /home/pi/journey-planner/client && npm run build`
- Jeśli brak dostępu: Sprawdź uprawnienia: `chmod -R 755 /home/pi/journey-planner/client/dist`

---

### Problem: SmartHome przestał działać

```bash
# Sprawdź status kontenerów
docker ps

# Zobacz logi SmartHome
docker logs smarthome_app --tail 50

# Restart jeśli potrzebne
docker-compose restart app
```

**Rozwiązanie:** SmartHome powinien działać bez zmian, ale jeśli wystąpiły problemy:
```bash
cd ~/Site_proj
docker-compose restart app nginx
```

---

### Problem: WebSocket nie działa (Socket.IO)

```bash
# Sprawdź logi nginx dla błędów WebSocket
docker logs smarthome_nginx | grep socket

# Test WebSocket endpoint
curl -k https://malina.tail384b18.ts.net/socket.io/?EIO=4&transport=polling
```

**Rozwiązanie:** Otwórz DevTools w przeglądarce → Network → WS (WebSocket) i sprawdź czy połączenie się udaje.

---

## 📊 Monitoring

### Sprawdzenie statusu wszystkich usług

```bash
# Docker containers
docker ps

# PM2 processes
pm2 status

# PostgreSQL
sudo systemctl status postgresql

# Redis (jeśli standalone)
docker ps | grep redis
```

### Logi

```bash
# SmartHome App
docker logs -f smarthome_app

# Nginx
docker logs -f smarthome_nginx

# Journey Planner API
pm2 logs journey-planner-api

# PostgreSQL (jeśli potrzebne)
sudo journalctl -u postgresql -f
```

---

## ✅ Checklist deployment

- [ ] Commit i push zmian do GitHub
- [ ] SSH do Raspberry Pi
- [ ] `git pull` w ~/Site_proj
- [ ] Sprawdzenie Journey Planner frontend build (`ls /home/pi/journey-planner/client/dist/`)
- [ ] Sprawdzenie Journey Planner API (`pm2 status` + `curl localhost:5001`)
- [ ] Restart nginx (`docker-compose up -d nginx`)
- [ ] Test SmartHome API (`curl https://malina.tail384b18.ts.net/api/rooms`)
- [ ] Test Journey Planner API (`curl https://malina.tail384b18.ts.net/journey/api/health`)
- [ ] Test Journey Planner frontend w przeglądarce
- [ ] Sprawdzenie logów (`docker logs smarthome_nginx`)

---

## 🎉 Po udanym deployment

Oba aplikacje powinny być dostępne pod:

- **SmartHome**: https://malina.tail384b18.ts.net/
- **Journey Planner**: https://malina.tail384b18.ts.net/journey/
- **Portainer**: https://malina.tail384b18.ts.net/portainer/
- **Grafana**: https://malina.tail384b18.ts.net/grafana/

WebSocket dla SmartHome: `wss://malina.tail384b18.ts.net/socket.io/`

---

## 📝 Notatki

- Journey Planner API działa przez PM2 na hoście (nie w Docker)
- Journey Planner frontend jest montowany do nginx jako volume z `/home/pi/journey-planner/client/dist`
- SmartHome działa w pełni w Docker (app + nginx)
- Nginx reverse proxy obsługuje routing dla obu aplikacji
- SSL certyfikaty z Tailscale są montowane read-only do nginx

---

**Ostatnia aktualizacja:** 2025-11-10
**Status:** Gotowe do deployment
