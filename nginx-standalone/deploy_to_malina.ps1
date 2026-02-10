# PowerShell script to deploy nginx configuration to Raspberry Pi
# Uruchom z folderu głównego projektu: .\nginx-standalone\deploy_to_malina.ps1

$MALINA_HOST = "192.168.1.218"
$MALINA_USER = "adas.rakieta"
$MALINA_PASSWORD = "Qwuizzy123"

Write-Host "[*] Deployment nginx configuration to Malina" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Sprawdź czy pliki istnieją
if (-not (Test-Path "nginx-standalone/conf.d/default.conf")) {
    Write-Host "[X] Blad: Nie znaleziono nginx-standalone/conf.d/default.conf" -ForegroundColor Red
    Write-Host "Upewnij sie, ze uruchamiasz skrypt z glownego folderu projektu!" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "nginx-standalone/update_nginx.sh")) {
    Write-Host "[X] Blad: Nie znaleziono nginx-standalone/update_nginx.sh" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[1/4] Kopiuje pliki na maline..." -ForegroundColor Yellow

# SCP - konfiguracja nginx
Write-Host "  -> Kopiuje default.conf..." -ForegroundColor Gray
scp nginx-standalone/conf.d/default.conf ${MALINA_USER}@${MALINA_HOST}:/tmp/default.conf

# SCP - skrypt aktualizacji
Write-Host "  -> Kopiuje update_nginx.sh..." -ForegroundColor Gray
scp nginx-standalone/update_nginx.sh ${MALINA_USER}@${MALINA_HOST}:/tmp/update_nginx.sh

Write-Host "[OK] Pliki skopiowane" -ForegroundColor Green

Write-Host ""
Write-Host "[2/4] Ustawiam uprawnienia skryptu..." -ForegroundColor Yellow

# Ustaw uprawnienia wykonywania dla skryptu
ssh ${MALINA_USER}@${MALINA_HOST} "chmod +x /tmp/update_nginx.sh"
Write-Host "[OK] Uprawnienia ustawione" -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Uruchamiam skrypt aktualizacji..." -ForegroundColor Yellow
Write-Host ""

# Uruchom skrypt na malinie
ssh ${MALINA_USER}@${MALINA_HOST} "/tmp/update_nginx.sh"

Write-Host ""
Write-Host "[4/4] Czyszcze pliki tymczasowe..." -ForegroundColor Yellow
ssh ${MALINA_USER}@${MALINA_HOST} "rm /tmp/update_nginx.sh"
Write-Host "[OK] Pliki tymczasowe usuniete" -ForegroundColor Green

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Deployment zakonczony pomyslnie!" -ForegroundColor Green
Write-Host ""
Write-Host "Co dalej:" -ForegroundColor Cyan
Write-Host "  1. Wyczysc cookies w przegladarce dla malina.tail384b18.ts.net" -ForegroundColor White
Write-Host "  2. Zaloguj sie ponownie do SmartHome" -ForegroundColor White
Write-Host "  3. Sprawdz czy sesje dzialaja poprawnie" -ForegroundColor White
Write-Host ""
Write-Host "URL: https://malina.tail384b18.ts.net/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Jesli cos nie dziala, sprawdz logi:" -ForegroundColor Yellow
Write-Host "   ssh ${MALINA_USER}@${MALINA_HOST}" -ForegroundColor Gray
Write-Host "   docker logs smarthome_app --tail 50" -ForegroundColor Gray
Write-Host "   docker logs nginx-proxy --tail 50" -ForegroundColor Gray
Write-Host "=============================================" -ForegroundColor Cyan
