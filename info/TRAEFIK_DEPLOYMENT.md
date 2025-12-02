# Traefik Deployment Guide - SmartHome Stack

## 🎯 Cel

Deployment SmartHome z Traefik jako reverse proxy z SSL (Tailscale) i automatycznym routingiem.

## 📋 Wymagania

- ✅ Traefik stack już działający
- ✅ Sieć Docker `web` utworzona
- ✅ PostgreSQL dostępny (zewnętrzny lub osobny stack)
- ✅ Tailscale SSL certificates dla domeny `malina.tail384b18.ts.net`

## 🚀 Quick Start

### 1. Upewnij się, że sieć `web` istnieje

```bash
docker network create web
```

### 2. Skopiuj docker-compose.yml do Portainera

Użyj pliku `docker-compose.yml` z tego repozytorium.

**Kluczowe elementy:**
- ✅ Redis włączony do stacka (nie potrzebny osobny compose)
- ✅ Health checks dla redis i app
- ✅ Dwie sieci: `web` (Traefik) + `smarthome-net` (internal)
- ✅ Traefik labels z middleware `stripprefix`

### 3. Skonfiguruj zmienne środowiskowe

W Portainer Stack → Environment variables:

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
SECRET_KEY=wygeneruj_losowy_32_znakowy_klucz

# === Docker Configuration ===
IMAGE_TAG=latest

# === URL Prefixes (EMPTY for Traefik!) ===
URL_PREFIX=
API_PREFIX=
STATIC_PREFIX=
SOCKET_PREFIX=
```

**⚠️ WAŻNE:** Wszystkie `*_PREFIX` muszą być **puste**! Traefik middleware `stripprefix` usuwa `/smarthome` przed przekazaniem do aplikacji.

### 4. Deploy Stack

W Portainer:
1. Stacks → Add stack → **Name:** `smarthome`
2. Wklej `docker-compose.yml`
3. Dodaj zmienne środowiskowe
4. **Deploy the stack**

### 5. Weryfikacja

```bash
# Sprawdź kontenery
docker ps | grep smarthome

# Sprawdź logi app
docker logs smarthome_app

# Sprawdź logi redis
docker logs smarthome_redis_standalone

# Sprawdź health
docker inspect smarthome_app | grep -A 10 Health
```

**Oczekiwane kontenery:**
- `smarthome_app` (healthy)
- `smarthome_redis_standalone` (healthy)

**Oczekiwane sieci:**
- `web` (external, połączenie z Traefik)
- `smarthome-net` (internal, app ↔ redis)

## 🌐 Dostęp

Aplikacja dostępna pod:
```
https://malina.tail384b18.ts.net/smarthome/
```

**Routing przez Traefik:**
1. User → `https://malina.tail384b18.ts.net/smarthome/` (HTTPS, Tailscale SSL)
2. Traefik → router `smarthome` (rule: `Host + PathPrefix(/smarthome)`)
3. Middleware `stripprefix` → usuwa `/smarthome`
4. `smarthome_app:5000` → otrzymuje request na `/` ✅

## 🔧 Traefik Labels Explained

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=web"
  
  # Routing rule: Host + Path
  - "traefik.http.routers.smarthome.rule=Host(`malina.tail384b18.ts.net`) && PathPrefix(`/smarthome`)"
  - "traefik.http.routers.smarthome.entrypoints=websecure"
  - "traefik.http.routers.smarthome.tls=true"
  - "traefik.http.routers.smarthome.priority=150"
  
  # Backend service
  - "traefik.http.services.smarthome.loadbalancer.server.port=5000"
  
  # Middleware: strip /smarthome prefix
  - "traefik.http.middlewares.smarthome-strip.stripprefix.prefixes=/smarthome"
  - "traefik.http.routers.smarthome.middlewares=smarthome-strip"
```

**Dlaczego `stripprefix`?**
- Flask generuje ścieżki: `/static/...`, `/api/...`, `/login`, etc.
- Bez stripprefix: Traefik wysyła `/smarthome/login` → Flask nie zna tej ścieżki ❌
- Z stripprefix: Traefik wysyła `/login` → Flask rozpoznaje ścieżkę ✅

## 📦 Volumes

Stack tworzy dwa lokalne volumes:
- `static_uploads` → zdjęcia profilowe użytkowników
- `redis_data` → Redis persistence (AOF)

**Backup:**
```bash
# Static uploads
docker run --rm -v smarthome_static_uploads:/data -v $(pwd):/backup alpine tar czf /backup/static_uploads.tar.gz -C /data .

# Redis data
docker run --rm -v smarthome_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
```

## 🐛 Troubleshooting

### Problem: 404 Not Found

**Przyczyna:** Traefik nie usuwa prefiksu `/smarthome`

**Rozwiązanie:** Sprawdź czy middleware jest poprawnie przypisany:
```bash
docker logs traefik | grep smarthome
```

### Problem: Static assets 404

**Przyczyna:** Niepoprawne `URL_PREFIX` w zmiennych środowiskowych

**Rozwiązanie:** Upewnij się, że `URL_PREFIX=` (pusty!)
```bash
docker exec smarthome_app env | grep PREFIX
```

### Problem: Redis connection refused

**Przyczyna:** Redis nie jest healthy lub app nie jest w sieci `smarthome-net`

**Rozwiązanie:**
```bash
# Sprawdź health redis
docker inspect smarthome_redis_standalone | grep -A 10 Health

# Sprawdź sieci app
docker inspect smarthome_app | grep -A 20 Networks
```

### Problem: SocketIO nie działa

**Przyczyna:** WebSocket upgrade nie działa przez Traefik

**Rozwiązanie:** Traefik automatycznie obsługuje WebSocket upgrade. Sprawdź logi:
```bash
docker logs smarthome_app | grep -i socket
```

## 🔄 Aktualizacja aplikacji

### Pull nowego image z GitHub Container Registry

```bash
# Portainer: Edit stack → zwiększ IMAGE_TAG
IMAGE_TAG=v1.2.3

# Lub użyj :latest
IMAGE_TAG=latest
```

### Restart stacka

```bash
docker-compose up -d --force-recreate
```

## 📚 Dokumentacja powiązana

- [URL Prefix Configuration](./URL_PREFIX_CONFIGURATION.md) - szczegóły dotyczące prefixów URL
- [Quick Start](./QUICK_START.md) - ogólny przewodnik deployment
- [Portainer Stack Setup](./PORTAINER_STACK_SETUP.md) - deployment przez Portainer

## ✅ Checklist przed deploymentem

- [ ] Sieć `web` utworzona i działa
- [ ] Traefik stack działa i nasłuchuje na `websecure`
- [ ] PostgreSQL dostępny i dane połączenia poprawne
- [ ] Zmienne środowiskowe skonfigurowane (SECRET_KEY, hasła DB, SMTP)
- [ ] Wszystkie `*_PREFIX` są **puste**
- [ ] IMAGE_TAG wskazuje na poprawną wersję image
- [ ] Tailscale SSL certificates skonfigurowane w Traefik

## 🎉 Po deployment

Aplikacja powinna być dostępna pod:
```
https://malina.tail384b18.ts.net/smarthome/
```

Login: użyj konta utworzonego w PostgreSQL lub zarejestruj nowe.

**Socket.IO:** Powinna automatycznie połączyć się i wyświetlać live updates (np. zmiana światła, temperatura).

**Health endpoint:** Dostępny pod:
```
https://malina.tail384b18.ts.net/smarthome/health
```

---

**Powodzenia! 🚀**
