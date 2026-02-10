# 🚀 Quick Deploy Guide - Grafana Fix

## ✅ Naprawione problemy
- `/health` endpoint już **NIE jest blokowany** przez rate limiting
- `/api/status` i `/api/ping` też wyłączone z limitów
- Grafana będzie mogła odpytywać co 15 sekund bez problemu

---

## 📋 Deployment Steps

### KROK 1: Commit i push zmian (na Windows)
```powershell
cd C:\Users\szymo\Git_proj\Site_proj
git add app_db.py
git commit -m "fix: exempt health/status endpoints from rate limiting for Grafana"
git push origin main
```

### KROK 2: Czekaj na GitHub Actions (~5 min)
- Otwórz: https://github.com/adasrakieta/Site_proj/actions
- Workflow "Build and Publish Docker images" musi się zakończyć ✅
- Buduje obrazy dla **linux/arm64** (Raspberry Pi)

### KROK 3: Deploy na Raspberry Pi
```bash
# SSH do Raspberry Pi
ssh adas.rakieta@192.168.1.218

# Przejdź do katalogu SmartHome
cd /opt/smarthome  # lub ~/smarthome

# Pull nowego obrazu z GHCR
docker-compose pull

# Restart kontenerów
docker-compose down
docker-compose up -d

# Sprawdź status
docker-compose ps
curl http://localhost:5000/health
```

---

## 🔍 Weryfikacja

### 1. Endpoint działa bez limitów
```bash
# Uruchom 20 requestów pod rząd (wcześniej by zablokowało)
for i in {1..20}; do 
    curl -s http://malina.tail384b18.ts.net/health | jq .status
    sleep 0.5
done
```

Powinieneś dostać 20x `"healthy"` bez błędów 429.

### 2. Grafana pokazuje UP
- Otwórz panel Grafany
- Status SmartHome powinien zmienić się z 🔴 DOWN → 🟢 UP
- Health check interval: 15s

---

## ⚡ Alternatywnie: Lokalna budowa (jeśli GitHub Actions nie działa)

```powershell
# Uruchom skrypt rebuild_and_deploy.ps1
.\rebuild_and_deploy.ps1
```

Ten skrypt:
1. Zbuduje obraz lokalnie
2. Wyeksportuje do tar (może być duży, ~500MB)
3. Skopiuje przez SCP do Raspberry Pi
4. Załaduje i zrestartuje kontenery

**Uwaga:** Lokalna budowa na Windows tworzy obraz `linux/amd64`, ale Raspberry Pi potrzebuje `linux/arm64`. Używaj GitHub Actions dla najlepszej kompatybilności.

---

## 📊 Co się zmieniło w kodzie?

### app_db.py (linie 673-677)
```python
# Wyłączone z rate limitingu (było: tylko CSRF exempt)
self.limiter.exempt('health_check')    # /health
self.limiter.exempt('api_status')      # /api/status  
self.limiter.exempt('api_ping')        # /api/ping
```

### Wcześniej:
- Grafana odpytywała `/health` co 15s
- Rate limiter: 10000 req/day dla authenticated, 1000/day dla anonymous
- Grafana używała IP address → szybko przekraczała limity
- Dostawała 429 Too Many Requests → status DOWN

### Teraz:
- Endpointy monitorujące **całkowicie wyłączone** z limitów
- Grafana może odpytywać dowolnie często
- Status: 🟢 UP

---

## 🛠️ Troubleshooting

### Grafana nadal pokazuje DOWN po deploymencie
```bash
# Sprawdź logi kontenera
docker logs smarthome_app --tail 50

# Sprawdź czy endpoint odpowiada
curl -v http://localhost:5000/health

# Sprawdź konfigurację Grafany (datasource health check URL)
# Powinno być: http://malina.tail384b18.ts.net/health
```

### GitHub Actions failed
- Sprawdź: https://github.com/adasrakieta/Site_proj/actions
- Błędy buildowania Docker powinny być widoczne w logach
- Jeśli problem z uprawnieniami GHCR → użyj lokalnej budowy

### Docker pull fails on Raspberry Pi
```bash
# Login do GHCR (jednorazowo)
docker login ghcr.io -u adasrakieta
# Password: GitHub Personal Access Token (PAT)
```

---

## ✅ Expected Result
- Grafana status: 🟢 UP
- Health check endpoint: odpowiada w <100ms
- Rate limiting: NIE blokuje monitoringu
- Aplikacja: działa normalnie
