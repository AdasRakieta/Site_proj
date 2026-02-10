# Szybkie polecenia do aktualizacji nginx na malinie

## 🚀 OPCJA 1: Automatyczny deployment z Windows (NAJŁATWIEJSZY)

Uruchom jeden skrypt PowerShell, który zrobi wszystko za Ciebie:

```powershell
.\nginx-standalone\deploy_to_malina.ps1
```

Skrypt:
- Skopiuje pliki na malinę
- Wykona backup
- Sprawdzi składnię
- Przeładuje nginx
- Zrestartuje SmartHome

---

## 🔧 OPCJA 2: Ręczna aktualizacja (krok po kroku)

### A) Skopiuj pliki z Windows:

```powershell
# Konfiguracja nginx
scp nginx-standalone/conf.d/default.conf adas.rakieta@192.168.1.218:/tmp/default.conf

# Skrypt aktualizacji
scp nginx-standalone/update_nginx.sh adas.rakieta@192.168.1.218:/tmp/update_nginx.sh
```

Hasło: `Qwuizzy123`

### B) Zaloguj się na malinę i uruchom skrypt:

```bash
ssh adas.rakieta@192.168.1.218
chmod +x /tmp/update_nginx.sh
/tmp/update_nginx.sh
```

---

## ⚡ OPCJA 3: Jedno wielkie polecenie (dla zaawansowanych)

Wklej to bezpośrednio w PowerShell (wszystko w jednym):

```powershell
scp nginx-standalone/conf.d/default.conf adas.rakieta@192.168.1.218:/tmp/default.conf; `
scp nginx-standalone/update_nginx.sh adas.rakieta@192.168.1.218:/tmp/update_nginx.sh; `
ssh adas.rakieta@192.168.1.218 "chmod +x /tmp/update_nginx.sh && /tmp/update_nginx.sh && rm /tmp/update_nginx.sh"
```

---

## 📝 OPCJA 4: Manualnie przez SSH (bez skryptów)

```bash
# 1. Zaloguj się
ssh adas.rakieta@192.168.1.218

# 2. Backup
sudo cp /opt/nginx/conf.d/default.conf /opt/nginx/conf.d/default.conf.backup.$(date +%Y%m%d_%H%M%S)

# 3. Edytuj plik (nano lub vim)
sudo nano /opt/nginx/conf.d/default.conf

# Znajdź linię:
#     proxy_set_header X-Forwarded-Proto $scheme;
# I dodaj ZARAZ PO NIEJ:
#     proxy_set_header X-Forwarded-Host $host;  # CRITICAL for session cookies

# 4. Sprawdź składnię
docker exec nginx-proxy nginx -t

# 5. Przeładuj nginx
docker exec nginx-proxy nginx -s reload

# 6. Restart SmartHome
docker restart smarthome_app
```

---

## ✅ Weryfikacja po aktualizacji

```bash
# Sprawdź logi SmartHome (szukaj "ProxyFix")
docker logs smarthome_app | grep ProxyFix

# Sprawdź logi nginx
docker logs nginx-proxy --tail 50

# Sprawdź status kontenerów
docker ps
```

---

## 🧹 Czyszczenie cookies w przeglądarce

### Chrome/Edge:
1. F12 (DevTools)
2. Application → Cookies
3. Usuń wszystkie dla `malina.tail384b18.ts.net`

### Firefox:
1. F12 (DevTools)
2. Storage → Cookies
3. Usuń wszystkie dla `malina.tail384b18.ts.net`

---

## 🆘 Troubleshooting

### Jeśli SCP nie działa:
```powershell
# Upewnij się że masz SSH client zainstalowany
Get-Command ssh
Get-Command scp

# Jeśli nie, zainstaluj OpenSSH Client w Windows Settings:
# Settings → Apps → Optional Features → Add a feature → OpenSSH Client
```

### Jeśli sesje nadal nie działają:
1. Sprawdź czy SmartHome został przebudowany z ProxyFix middleware
2. Sprawdź czy `SECRET_KEY` jest ustawiony w env SmartHome
3. Sprawdź czy `FLASK_ENV=production`
4. Wyczyść WSZYSTKIE cookies (nie tylko session)

### Przywrócenie backup jeśli coś poszło nie tak:
```bash
# Lista backupów
ls -la /opt/nginx/conf.d/default.conf.backup.*

# Przywróć (zmień datę na swoją)
sudo cp /opt/nginx/conf.d/default.conf.backup.20260210_120000 /opt/nginx/conf.d/default.conf
docker restart nginx-proxy
```

---

## 🎯 TL;DR - Najmniej kroków:

Jeśli chcesz po prostu "zrobić to teraz":

```powershell
# Z Windows PowerShell w folderze projektu:
.\nginx-standalone\deploy_to_malina.ps1
```

Potem wyczyść cookies i zaloguj się ponownie.

**GOTOWE!** 🎉
