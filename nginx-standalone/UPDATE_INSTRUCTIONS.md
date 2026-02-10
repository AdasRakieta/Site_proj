# Instrukcje aktualizacji Nginx na Malinie

## 🔧 Co zostało zmienione?

Dodano **KRYTYCZNY** header `X-Forwarded-Host` do proxy SmartHome, który jest wymagany przez Flask ProxyFix middleware aby sesje działały poprawnie z `SESSION_COOKIE_SECURE=True`.

## 📋 Krok po kroku:

### 1. Skopiuj zaktualizowany plik na malinę

Użyj SCP aby przesłać zaktualizowany plik konfiguracji:

```bash
scp nginx-standalone/conf.d/default.conf adas.rakieta@192.168.1.218:/tmp/default.conf
```

Hasło: `Qwuizzy123`

### 2. Zaloguj się na malinę

```bash
ssh adas.rakieta@192.168.1.218
```

### 3. Utwórz backup obecnej konfiguracji

```bash
sudo cp /opt/nginx/conf.d/default.conf /opt/nginx/conf.d/default.conf.backup.$(date +%Y%m%d_%H%M%S)
```

### 4. Skopiuj nowy plik konfiguracji

```bash
sudo mv /tmp/default.conf /opt/nginx/conf.d/default.conf
sudo chown root:root /opt/nginx/conf.d/default.conf
sudo chmod 644 /opt/nginx/conf.d/default.conf
```

### 5. Sprawdź czy konfiguracja jest poprawna

```bash
docker exec nginx-proxy nginx -t
```

Powinno wyświetlić:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 6. Przeładuj nginx

```bash
docker exec nginx-proxy nginx -s reload
```

LUB restart całego kontenera (jeśli reload nie zadziała):

```bash
docker restart nginx-proxy
```

### 7. Sprawdź logi

```bash
docker logs nginx-proxy --tail 50
```

### 8. Sprawdź czy strona działa

Otwórz w przeglądarce: https://malina.tail384b18.ts.net/

## ✅ Weryfikacja

Po aktualizacji nginx, musisz również:

1. **Zrestartować kontener SmartHome** (aby ProxyFix zadziałał):
   ```bash
   docker restart smarthome_app
   ```

2. **Wyczyścić cookies w przeglądarce** (stare sesje mogą być nieprawidłowe):
   - Chrome/Edge: F12 → Application → Cookies → usuń wszystkie dla malina.tail384b18.ts.net
   - Firefox: F12 → Storage → Cookies → usuń wszystkie

3. **Zaloguj się ponownie** do SmartHome

## 📊 Co się zmieniło w konfiguracji?

### PRZED:
```nginx
location / {
    proxy_pass http://smarthome_app:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    # BRAKUJE X-Forwarded-Host!
```

### PO:
```nginx
location / {
    proxy_pass http://smarthome_app:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;  # ✅ DODANE!
```

## ⚠️ Troubleshooting

### Jeśli sesje nadal nie działają:

1. Sprawdź czy SmartHome ma ProxyFix middleware:
   ```bash
   docker logs smarthome_app | grep "ProxyFix"
   ```
   Powinno być: `✓ ProxyFix middleware enabled for reverse proxy support`

2. Sprawdź czy SECRET_KEY jest ustawiony:
   ```bash
   docker exec smarthome_app printenv | grep SECRET_KEY
   ```

3. Sprawdź czy FLASK_ENV=production:
   ```bash
   docker exec smarthome_app printenv | grep FLASK_ENV
   ```

### Jeśli nginx nie startuje:

1. Sprawdź składnię ponownie:
   ```bash
   docker exec nginx-proxy nginx -t
   ```

2. Przywróć backup:
   ```bash
   sudo cp /opt/nginx/conf.d/default.conf.backup.XXXXXXXX /opt/nginx/conf.d/default.conf
   docker restart nginx-proxy
   ```

## 🔐 Bezpieczeństwo

**WAŻNE:** Po zakończeniu zmian, rozważ:

1. Zmianę hasła SSH na silniejsze
2. Skonfigurowanie klucza SSH zamiast hasła
3. Wyłączenie logowania hasłem w SSH

```bash
# Generuj klucz SSH na swoim komputerze (Windows):
ssh-keygen -t ed25519 -C "adas.rakieta@malina"

# Skopiuj klucz na malinę:
ssh-copy-id -i ~/.ssh/id_ed25519.pub adas.rakieta@192.168.1.218
```

## 📞 Kontakt

Jeśli coś nie działa, sprawdź:
- Logi SmartHome: `docker logs smarthome_app --tail 100`
- Logi nginx: `docker logs nginx-proxy --tail 100`
- Status kontenerów: `docker ps -a`
