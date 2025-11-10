# 🔗 Nginx Integration: SmartHome + Journey Planner

## Obecna Sytuacja

**SmartHome:** Działa na porcie 5000, dostępny przez Nginx na `/smarthome/`
**Journey Planner:** Frontend port 5173, Backend port 5001
**Problem:** 404 na `https://malina.tail384b18.ts.net/journey/`

## 🎯 Architektura Docelowa

```
Internet → Raspberry Pi :443 (HTTPS) / :80 (HTTP)
           ↓
        Nginx Reverse Proxy
        ├─ malina.tail384b18.ts.net/
        │  └─ 301 redirect → /smarthome/
        ├─ malina.tail384b18.ts.net/smarthome/
        │  └─ proxy_pass → localhost:5000
        ├─ malina.tail384b18.ts.net/journey/
        │  └─ proxy_pass → localhost:5173
        └─ malina.tail384b18.ts.net/journey/api/
           └─ proxy_pass → localhost:5001/api/
```

## 📝 Kompletna Konfiguracja Nginx

### Opcja A: HTTPS (Z SSL/Certbot) - ZALECANA

Plik: `/etc/nginx/sites-available/projects`

```nginx
# ============================================
# SmartHome + Journey Planner - Unified Config
# ============================================

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name malina.tail384b18.ts.net;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Main HTTPS server block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name malina.tail384b18.ts.net;

    # SSL Configuration - dostosuj ścieżki!
    ssl_certificate /etc/letsencrypt/live/malina.tail384b18.ts.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/malina.tail384b18.ts.net/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logs
    access_log /var/log/nginx/projects-access.log;
    error_log /var/log/nginx/projects-error.log;

    # ============================================
    # ROOT - Redirect to SmartHome
    # ============================================
    location = / {
        return 301 https://$server_name/smarthome/;
    }

    # ============================================
    # SMARTHOME PROJECT (PORT 5000)
    # ============================================
    location /smarthome/ {
        proxy_pass http://localhost:5000/;
        proxy_http_version 1.1;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # Standard headers
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # ============================================
    # JOURNEY PLANNER - FRONTEND (PORT 5173)
    # ============================================
    location /journey/ {
        # Strip /journey prefix
        proxy_pass http://localhost:5173/;
        proxy_http_version 1.1;
        
        # Standard headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Disable buffering
        proxy_buffering off;
    }

    # ============================================
    # JOURNEY PLANNER - API (PORT 5001)
    # ============================================
    location /journey/api/ {
        # Rewrite /journey/api/xxx to /api/xxx
        rewrite ^/journey/api/(.*) /api/$1 break;
        
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        
        # Standard headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts (longer for API)
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
        proxy_read_timeout 90s;
    }
}
```

### Opcja B: HTTP Only (Bez SSL) - PROSTSZE

```nginx
# HTTP Only Configuration
server {
    listen 80;
    listen [::]:80;
    server_name malina.tail384b18.ts.net;

    # Logs
    access_log /var/log/nginx/projects-access.log;
    error_log /var/log/nginx/projects-error.log;

    # ROOT - Redirect to SmartHome
    location = / {
        return 301 http://$server_name/smarthome/;
    }

    # SMARTHOME PROJECT (PORT 5000)
    location /smarthome/ {
        proxy_pass http://localhost:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # JOURNEY PLANNER - FRONTEND (PORT 5173)
    location /journey/ {
        proxy_pass http://localhost:5173/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # JOURNEY PLANNER - API (PORT 5001)
    location /journey/api/ {
        rewrite ^/journey/api/(.*) /api/$1 break;
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🚀 Wdrożenie (12 Kroków)

### 1. Backup

```bash
ssh pi@malina.tail384b18.ts.net

sudo cp -r /etc/nginx/sites-available /etc/nginx/sites-available.backup.$(date +%Y%m%d)
sudo cp -r /etc/nginx/sites-enabled /etc/nginx/sites-enabled.backup.$(date +%Y%m%d)
```

### 2. Sprawdź Obecną Konfigurację

```bash
ls -la /etc/nginx/sites-available/
ls -la /etc/nginx/sites-enabled/

# Pokaż obecną konfigurację
sudo nginx -T | head -100
```

### 3. Utwórz Nowy Plik

```bash
sudo nano /etc/nginx/sites-available/projects

# Wklej konfigurację (HTTPS lub HTTP)
# Ctrl+O, Enter, Ctrl+X
```

### 4. Wyłącz Starą Konfigurację

```bash
# Usuń stare symlinki
sudo rm /etc/nginx/sites-enabled/default
sudo rm /etc/nginx/sites-enabled/smarthome  # jeśli istnieje
```

### 5. Włącz Nową Konfigurację

```bash
sudo ln -s /etc/nginx/sites-available/projects /etc/nginx/sites-enabled/

ls -la /etc/nginx/sites-enabled/
# Powinno pokazać symlink do projects
```

### 6. Test Składni

```bash
sudo nginx -t

# Expected output:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 7. Reload Nginx

```bash
sudo systemctl reload nginx

# Sprawdź status
sudo systemctl status nginx
# Powinno być: active (running)
```

### 8. Sprawdź Kontenery

```bash
# Journey Planner
docker ps | grep journey-planner

# SmartHome
docker ps | grep smarthome
# LUB
netstat -tlnp | grep 5000
```

### 9. Test Lokalny (Na Pi)

```bash
# Frontend
curl -I http://localhost:5173/
# Expected: HTTP/1.1 200 OK

# Backend
curl http://localhost:5001/api/health
# Expected: {"status":"healthy"}

# SmartHome
curl -I http://localhost:5000/
# Expected: HTTP/1.1 200 OK
```

### 10. Test Przez Nginx (Na Pi)

```bash
curl -I http://localhost/smarthome/
curl -I http://localhost/journey/
curl http://localhost/journey/api/health
```

### 11. Test z Twojego Komputera

```powershell
# Windows PowerShell

curl -I https://malina.tail384b18.ts.net/smarthome/
curl -I https://malina.tail384b18.ts.net/journey/
curl https://malina.tail384b18.ts.net/journey/api/health
```

### 12. Test w Przeglądarce

- SmartHome: `https://malina.tail384b18.ts.net/smarthome/` ✅
- Journey: `https://malina.tail384b18.ts.net/journey/` ✅
- F12 → Console - brak błędów ✅

## 🐛 Troubleshooting

### 404 Not Found

```bash
# Sprawdź symlink
ls -la /etc/nginx/sites-enabled/

# Upewnij się że istnieje
sudo ln -sf /etc/nginx/sites-available/projects /etc/nginx/sites-enabled/

# Reload
sudo systemctl reload nginx
```

### 502 Bad Gateway

```bash
# Sprawdź kontenery
docker ps | grep journey-planner

# Sprawdź porty
netstat -tlnp | grep -E '5001|5173'

# Logi Nginx
sudo tail -f /var/log/nginx/projects-error.log

# Restart kontenerów
cd ~/journey-planner
docker-compose restart
```

### CORS Errors

Upewnij się w `nginix.env`:
```env
CORS_ORIGIN=https://malina.tail384b18.ts.net
```
(BEZ `/journey/`!)

Przebuduj:
```bash
cd ~/journey-planner
docker-compose down
docker-compose up -d
```

### CSS/JS 404

```bash
# Sprawdź assets w kontenerze
docker exec journey-planner-web ls -la /usr/share/nginx/html/assets/

# Przebuduj
cd ~/journey-planner
docker-compose down
docker-compose pull
docker-compose up -d
```

## ✅ Checklist

- [ ] SmartHome: `https://malina.tail384b18.ts.net/smarthome/` ✅
- [ ] Journey: `https://malina.tail384b18.ts.net/journey/` ✅
- [ ] Journey API: `curl https://malina.tail384b18.ts.net/journey/api/health` ✅
- [ ] `sudo nginx -t` - OK ✅
- [ ] `docker ps` - wszystkie kontenery "Up (healthy)" ✅
- [ ] F12 Console - brak błędów ✅
- [ ] F12 Network - wszystkie requesty 200 OK ✅

## 🔧 Maintenance

```bash
# Nginx status
sudo systemctl status nginx

# Reload (graceful)
sudo systemctl reload nginx

# Restart (downtime)
sudo systemctl restart nginx

# Logi
sudo tail -f /var/log/nginx/projects-error.log

# Docker logi
docker logs journey-planner-web --tail 50 -f
docker logs journey-planner-api --tail 50 -f
```

## 🎉 Success!

Obydwa projekty działają pod jednym Nginx:
- ✅ SmartHome: `/smarthome/`
- ✅ Journey Planner: `/journey/`
