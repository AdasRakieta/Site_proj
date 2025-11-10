# 🔄 Migracja do standalone nginx

## Dlaczego?

✅ **Jeden nginx dla wszystkich projektów** - SmartHome, Journey Planner, przyszłe projekty
✅ **Niezależne aktualizacje** - restart SmartHome nie zabija nginx
✅ **Łatwiejsze zarządzanie** - konfiguracja nginx w jednym miejscu
✅ **Mniejsze ryzyko downtime** - nginx działa zawsze, nawet gdy projekty się restartują
✅ **Lepsza organizacja** - każdy projekt w swoim stacku

## Obecna architektura (DO ZMIANY):

```
smarthome-stack:
  - smarthome_app (port 5000)
  - smarthome_nginx (port 80, 443) ❌ tutaj problem
```

## Nowa architektura (DOCELOWA):

```
nginx-stack (standalone):
  - nginx (port 80, 443) ✅
    ├── połączenie do smarthome-stack_default
    ├── połączenie do journey-stack_journey-planner-net
    └── połączenie do future-project-stack_default

smarthome-stack:
  - smarthome_app (port 5000)

journey-stack:
  - journey-planner-api (port 5001)
  - journey-planner-web (port 5173)
```

---

## 📋 Plan migracji - KROK PO KROKU

### ⚠️ WAŻNE: Przygotowanie

**Okno downtime:** ~2-5 minut (czas na podmianę nginx)

**Backup przed zmianami:**
```bash
# Na Raspberry Pi
cd ~/VS_Code_Proj/Site_proj
docker-compose down --volumes=false  # Tylko zatrzymaj, nie usuwaj volumes!

# Backup konfiguracji
docker inspect smarthome_nginx > nginx_backup.json
docker network ls > networks_backup.txt
```

---

### KROK 1: Utwórz strukturę katalogów nginx

```bash
# Na Raspberry Pi
cd ~
mkdir -p nginx-standalone/conf.d
mkdir -p nginx-standalone/logs
```

---

### KROK 2: Skopiuj pliki konfiguracyjne

Skopiuj z repozytorium (`nginx-standalone/`) na Raspberry Pi:

```bash
# Struktura docelowa na Pi:
~/nginx-standalone/
├── docker-compose.yml
├── nginx.conf
├── conf.d/
│   └── default.conf
└── logs/
```

**Opcja A - przez git (ZALECANE):**
```bash
cd ~
git clone https://github.com/AdasRakieta/Site_proj.git temp-repo
cp -r temp-repo/nginx-standalone/* nginx-standalone/
rm -rf temp-repo
```

**Opcja B - ręcznie przez SCP:**
```bash
# Z Windows (PowerShell):
scp -r nginx-standalone/* pi@100.103.184.90:~/nginx-standalone/
```

---

### KROK 3: Zatrzymaj obecny nginx w SmartHome stack

```bash
# W Portainerze:
# Stacks → smarthome-stack → Stop

# LUB przez SSH:
cd ~/VS_Code_Proj/Site_proj
docker-compose stop nginx
docker rm smarthome_nginx
```

---

### KROK 4: Uruchom standalone nginx

```bash
cd ~/nginx-standalone

# Sprawdź konfigurację
docker-compose config

# Uruchom nginx
docker-compose up -d

# Sprawdź logi
docker logs standalone_nginx
```

**Oczekiwany output:**
```
[notice] 1#1: nginx/1.25.x
[notice] 1#1: start worker processes
```

---

### KROK 5: Uruchom SmartHome bez nginx

**Opcja A - Portainer (ZALECANE):**

1. Stacks → smarthome-stack → Editor
2. Zamień `docker-compose.yml` na wersję bez nginx
3. Deploy stack

**Opcja B - SSH:**
```bash
cd ~/VS_Code_Proj/Site_proj

# Użyj nowego compose file (bez nginx)
docker-compose -f docker-compose-smarthome-only.yml up -d
```

---

### KROK 6: Weryfikacja

#### 6.1 Sprawdź kontenery
```bash
docker ps
```

**Powinny działać:**
- `standalone_nginx` (port 80, 443)
- `smarthome_app` (port 5000)
- `journey-planner-api` (port 5001)
- `journey-planner-web` (port 5173)

#### 6.2 Sprawdź sieci nginx
```bash
docker inspect standalone_nginx --format '{{json .NetworkSettings.Networks}}' | jq
```

**Powinny być:**
- `nginx-standalone_default`
- `smarthome-stack_default`
- `journey-stack_journey-planner-net`

#### 6.3 Test connectivity z nginx
```bash
# Test SmartHome
docker exec standalone_nginx wget -O- http://smarthome_app:5000/smarthome/ 2>&1 | head -20

# Test Journey API
docker exec standalone_nginx wget -O- http://journey-planner-api:5001/api/health 2>&1

# Test Journey Web
docker exec standalone_nginx wget -O- http://journey-planner-web:5173/ 2>&1 | head -20
```

#### 6.4 Test z przeglądarki

✅ `https://malina.tail384b18.ts.net/` → redirect → `/smarthome/`
✅ `https://malina.tail384b18.ts.net/smarthome/` → SmartHome login
✅ `https://malina.tail384b18.ts.net/smarthome/static/css/style.css` → CSS
✅ `https://malina.tail384b18.ts.net/journey/` → Journey frontend
✅ `https://malina.tail384b18.ts.net/journey/api/` → Journey API

---

## 🔧 Rozwiązywanie problemów

### Problem 1: nginx nie widzi kontenerów SmartHome

**Diagnoza:**
```bash
docker exec standalone_nginx ping -c 1 smarthome_app
# ping: bad address 'smarthome_app'
```

**Rozwiązanie:**
```bash
# Dodaj nginx do sieci SmartHome
docker network connect smarthome-stack_default standalone_nginx

# Restart nginx
docker restart standalone_nginx
```

### Problem 2: nginx nie widzi Journey Planner

**Rozwiązanie:**
```bash
# Dodaj nginx do sieci Journey
docker network connect journey-stack_journey-planner-net standalone_nginx

# Restart nginx
docker restart standalone_nginx
```

### Problem 3: Port 80/443 zajęty

**Diagnoza:**
```bash
docker logs standalone_nginx
# [emerg] bind() to 0.0.0.0:443 failed (98: Address already in use)
```

**Rozwiązanie:**
```bash
# Sprawdź co używa portów
sudo netstat -tlnp | grep ':80\|:443'

# Jeśli to stary nginx ze SmartHome stack:
docker rm -f smarthome_nginx

# Restart standalone nginx
docker restart standalone_nginx
```

### Problem 4: 502 Bad Gateway

**Diagnoza:**
```bash
# Sprawdź logi nginx
docker logs standalone_nginx --tail 50

# Sprawdź czy aplikacje działają
docker ps | grep -E "smarthome_app|journey"
```

**Możliwe przyczyny:**
1. Kontenery aplikacji nie działają → uruchom je
2. Nginx nie jest w tej samej sieci → `docker network connect`
3. Zła nazwa kontenera w upstream → sprawdź `docker ps`

---

## 🎯 Dodawanie nowych projektów

Teraz dodanie nowego projektu jest proste!

### Przykład: Dodanie nowego projektu "Portfolio"

1. **Uruchom projekt w swoim stacku:**
```yaml
# portfolio-stack/docker-compose.yml
version: '3.8'
services:
  portfolio-web:
    image: portfolio:latest
    container_name: portfolio_web
    ports:
      - "3000:3000"
```

2. **Dodaj konfigurację do nginx:**
```bash
# Edytuj ~/nginx-standalone/conf.d/default.conf
```

```nginx
# Dodaj upstream
upstream portfolio_web {
    server portfolio_web:3000;
}

# Dodaj location w server block
location /portfolio/ {
    proxy_pass http://portfolio_web/;
    # ... standardowe proxy headers
}
```

3. **Podłącz nginx do sieci projektu:**
```bash
# Jeśli portfolio ma swoją sieć
docker network connect portfolio-stack_default standalone_nginx
```

4. **Reload nginx:**
```bash
docker exec standalone_nginx nginx -s reload
```

✅ Portfolio dostępne: `https://malina.tail384b18.ts.net/portfolio/`

---

## 📊 Porównanie: Przed vs Po

### PRZED (nginx w SmartHome stack):

❌ Restart SmartHome = downtime nginx → wszystkie projekty offline
❌ Update konfiguracji nginx = rebuild całego SmartHome obrazu
❌ Dodanie nowego projektu = modyfikacja SmartHome stack
❌ Trudne zarządzanie wieloma projektami
❌ Brak centralizacji konfiguracji SSL

### PO (standalone nginx):

✅ Restart SmartHome = nginx działa → inne projekty online
✅ Update konfiguracji nginx = `nginx -s reload` (zero downtime)
✅ Dodanie nowego projektu = edycja conf + `reload`
✅ Łatwe zarządzanie wszystkimi projektami
✅ Centralna konfiguracja SSL dla wszystkich

---

## 🔄 Rollback (gdyby coś poszło nie tak)

Jeśli migracja się nie powiedzie, możesz wrócić do starego setup:

```bash
# Zatrzymaj standalone nginx
cd ~/nginx-standalone
docker-compose down

# Uruchom stary SmartHome stack (z nginx)
cd ~/VS_Code_Proj/Site_proj
docker-compose up -d

# W Portainerze: Pull and redeploy smarthome-stack
```

---

## 📝 Checklist końcowy

Po migracji sprawdź:

- [ ] `docker ps` - nginx działa jako `standalone_nginx`
- [ ] `docker ps` - SmartHome działa bez własnego nginx
- [ ] `docker network inspect` - nginx podłączony do wszystkich sieci
- [ ] SmartHome działa: `https://malina.tail384b18.ts.net/smarthome/`
- [ ] Journey działa: `https://malina.tail384b18.ts.net/journey/`
- [ ] Portainer działa: `https://malina.tail384b18.ts.net/portainer/`
- [ ] Logi nginx bez błędów: `docker logs standalone_nginx`
- [ ] Logi SmartHome bez błędów: `docker logs smarthome_app`

Jeśli wszystko ✅ - migracja zakończona sukcesem! 🎉

---

## 💡 Przyszłe ulepszenia

Po stabilizacji standalone nginx, możesz dodać:

1. **Certbot dla Let's Encrypt** (jeśli chcesz publiczny SSL zamiast Tailscale)
2. **Rate limiting** (ochrona przed abuse)
3. **WAF (Web Application Firewall)** (modsecurity)
4. **Centralne logowanie** (wysyłka logów do Grafana/Loki)
5. **Load balancing** (jeśli uruchomisz wiele instancji aplikacji)

---

## 📚 Dokumentacja

Po migracji zaktualizuj:

1. `README.md` - nowa architektura
2. `DEPLOYMENT_CHECKLIST.md` - nowe kroki deployment
3. `docker-compose.yml` (SmartHome) - usuń sekcję nginx

Powodzenia! 🚀
