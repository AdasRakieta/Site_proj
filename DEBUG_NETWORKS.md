# 🔍 Debug Network Issues - Nginx Standalone

## Błędy w logach:

```
[error] connect() failed (111: Connection refused) while connecting to upstream
request: "GET /journey/ HTTP/2.0", upstream: "http://172.20.0.3:5173/"
```

## Przyczyny:

1. **Nginx nie jest w tej samej sieci co aplikacje**
2. **Nazwy sieci Docker mogą być inne niż oczekiwane**
3. **Kontenery aplikacji nie działają**

---

## 🛠️ Krok po kroku - Diagnostyka

### 1. Sprawdź nazwy sieci Docker

```bash
# Lista wszystkich sieci
docker network ls

# Oczekiwane sieci:
# - smarthome-stack_default
# - journey-stack_journey-planner-net
# - nginx-standalone_default
```

### 2. Sprawdź czy kontenery działają

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Oczekiwane kontenery:
# - standalone_nginx (port 80, 443)
# - smarthome_app (port 5000)
# - journey-planner-api (port 5001)
# - journey-planner-web (port 5173)
```

### 3. Sprawdź do jakich sieci podłączony jest nginx

```bash
docker inspect standalone_nginx --format '{{json .NetworkSettings.Networks}}' | jq 'keys'

# Powinno zwrócić:
# [
#   "nginx-standalone_default",
#   "smarthome-stack_default",
#   "journey-stack_journey-planner-net"
# ]
```

### 4. Sprawdź rzeczywiste nazwy sieci stacków

```bash
# Dla SmartHome
docker inspect smarthome_app --format '{{json .NetworkSettings.Networks}}' | jq 'keys'

# Dla Journey Planner
docker inspect journey-planner-web --format '{{json .NetworkSettings.Networks}}' | jq 'keys'
```

### 5. Test DNS z nginx do aplikacji

```bash
# Test SmartHome
docker exec standalone_nginx ping -c 1 smarthome_app
# Jeśli DZIAŁA: OK
# Jeśli BŁĄD "bad address": nginx nie jest w sieci smarthome

# Test Journey Web
docker exec standalone_nginx ping -c 1 journey-planner-web
# Jeśli DZIAŁA: OK
# Jeśli BŁĄD "bad address": nginx nie jest w sieci journey

# Test Journey API
docker exec standalone_nginx ping -c 1 journey-planner-api
# Jeśli DZIAŁA: OK
# Jeśli BŁĄD "bad address": nginx nie jest w sieci journey
```

### 6. Test HTTP z nginx

```bash
# Test SmartHome (tylko jeśli ping działa)
docker exec standalone_nginx wget -O- http://smarthome_app:5000/ 2>&1 | head -20

# Test Journey API
docker exec standalone_nginx wget -O- http://journey-planner-api:5001/api/health 2>&1

# Test Journey Web
docker exec standalone_nginx wget -O- http://journey-planner-web:5173/ 2>&1 | head -20
```

---

## 🔧 Rozwiązanie: Ręczne podłączenie sieci

Jeśli nginx nie jest w sieciach, podłącz go ręcznie:

### Krok 1: Sprawdź dokładne nazwy sieci

```bash
# Znajdź sieć SmartHome
docker network ls | grep smarthome

# Znajdź sieć Journey
docker network ls | grep journey
```

### Krok 2: Podłącz nginx do sieci

```bash
# Przykład - zastąp RZECZYWISTĄ nazwą sieci
docker network connect smarthome-stack_default standalone_nginx
docker network connect journey-stack_journey-planner-net standalone_nginx

# LUB jeśli nazwy są inne:
docker network connect site_proj_default standalone_nginx
docker network connect journey_journey-planner-net standalone_nginx
```

### Krok 3: Zrestartuj nginx

```bash
docker restart standalone_nginx
```

### Krok 4: Weryfikacja

```bash
# Test DNS ponownie
docker exec standalone_nginx ping -c 1 smarthome_app
docker exec standalone_nginx ping -c 1 journey-planner-web

# Test HTTP
docker exec standalone_nginx wget -O- http://smarthome_app:5000/ 2>&1 | head -5
```

---

## 📝 Aktualizacja docker-compose.yml

Jeśli nazwy sieci są inne, zaktualizuj `nginx-standalone/docker-compose.yml`:

```yaml
networks:
  # ZAMIAST:
  smarthome-stack_default:
    external: true
    name: smarthome-stack_default
  
  # UŻYJ (przykład - sprawdź docker network ls):
  site_proj_default:
    external: true
    name: site_proj_default  # <- RZECZYWISTA nazwa
```

Po zmianie:
```bash
cd ~/nginx-standalone
docker-compose down
docker-compose up -d
```

---

## 🚨 Najczęstsze problemy

### Problem 1: Sieć nie istnieje

```
ERROR: Network smarthome-stack_default declared as external, but could not be found
```

**Rozwiązanie:**
```bash
# Znajdź rzeczywistą nazwę
docker network ls | grep -i smart
docker network ls | grep -i journey

# Użyj znalezionej nazwy w docker-compose.yml
```

### Problem 2: Kontener aplikacji nie działa

```
docker exec standalone_nginx ping -c 1 smarthome_app
ping: bad address 'smarthome_app'
```

**Diagnoza:**
```bash
# Sprawdź czy kontener istnieje
docker ps -a | grep smarthome_app

# Jeśli nie działa - uruchom SmartHome stack
cd ~/VS_Code_Proj/Site_proj
docker-compose up -d
```

### Problem 3: Port zajęty

```
Error starting userland proxy: listen tcp4 0.0.0.0:443: bind: address already in use
```

**Rozwiązanie:**
```bash
# Znajdź co używa portu
sudo netstat -tlnp | grep ':443'

# Zatrzymaj stary nginx (jeśli był w SmartHome stack)
docker rm -f smarthome_nginx

# Uruchom standalone nginx
cd ~/nginx-standalone
docker-compose up -d
```

---

## ✅ Checklist weryfikacji

Po naprawie sprawdź:

- [ ] `docker ps` - wszystkie kontenery działają (nginx, smarthome_app, journey-*)
- [ ] `docker network ls` - sieci istnieją
- [ ] `docker inspect standalone_nginx` - nginx podłączony do wszystkich sieci
- [ ] `ping smarthome_app` z nginx - działa
- [ ] `ping journey-planner-web` z nginx - działa
- [ ] `wget http://smarthome_app:5000/` z nginx - zwraca HTML
- [ ] `https://malina.tail384b18.ts.net/` - SmartHome login
- [ ] `https://malina.tail384b18.ts.net/journey/` - Journey Planner
- [ ] Logi nginx bez błędów: `docker logs standalone_nginx --tail 50`

---

## 📊 Przykładowe prawidłowe wyjście

### docker network ls
```
NETWORK ID     NAME                              DRIVER    SCOPE
abc123def456   bridge                            bridge    local
789ghi012jkl   site_proj_default                 bridge    local
345mno678pqr   journey-stack_journey-planner-net bridge    local
901stu234vwx   nginx-standalone_default          bridge    local
```

### docker inspect standalone_nginx (sieci)
```json
{
  "nginx-standalone_default": { ... },
  "site_proj_default": { ... },
  "journey-stack_journey-planner-net": { ... }
}
```

### docker exec standalone_nginx ping smarthome_app
```
PING smarthome_app (172.18.0.3): 56 data bytes
64 bytes from 172.18.0.3: seq=0 ttl=64 time=0.123 ms
--- smarthome_app ping statistics ---
1 packets transmitted, 1 packets received, 0% packet loss
```

---

## 🎯 Szybkie komendy - wszystko w jednym

```bash
#!/bin/bash
# Quick diagnostic script

echo "=== Docker Networks ==="
docker network ls

echo -e "\n=== Running Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo -e "\n=== Nginx Networks ==="
docker inspect standalone_nginx --format '{{json .NetworkSettings.Networks}}' | jq 'keys'

echo -e "\n=== SmartHome Networks ==="
docker inspect smarthome_app --format '{{json .NetworkSettings.Networks}}' | jq 'keys'

echo -e "\n=== Journey Networks ==="
docker inspect journey-planner-web --format '{{json .NetworkSettings.Networks}}' | jq 'keys' 2>/dev/null || echo "Journey container not found"

echo -e "\n=== DNS Test from Nginx ==="
docker exec standalone_nginx ping -c 1 smarthome_app 2>&1 | head -3
docker exec standalone_nginx ping -c 1 journey-planner-web 2>&1 | head -3

echo -e "\n=== HTTP Test from Nginx ==="
docker exec standalone_nginx wget -O- --timeout=2 http://smarthome_app:5000/ 2>&1 | head -5
```

Zapisz jako `debug-docker-networks.sh` i uruchom:
```bash
chmod +x debug-docker-networks.sh
./debug-docker-networks.sh
```
