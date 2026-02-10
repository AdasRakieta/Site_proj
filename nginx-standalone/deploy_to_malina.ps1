# PowerShell script to deploy nginx configuration to Raspberry Pi
# Uruchom z folderu głównego projektu: .\nginx-standalone\deploy_to_malina.ps1

$MALINA_HOST = "192.168.1.218"
$MALINA_USER = "adas.rakieta"

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

if (-not (Test-Path "nginx-standalone/diagnose_nginx.sh")) {
    Write-Host "[X] Blad: Nie znaleziono nginx-standalone/diagnose_nginx.sh" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "nginx-standalone/fix_docker_compose.sh")) {
    Write-Host "[X] Blad: Nie znaleziono nginx-standalone/fix_docker_compose.sh" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[1/6] Kopiuje pliki na maline..." -ForegroundColor Yellow

# SCP - konfiguracja nginx
Write-Host "  -> Kopiuje default.conf..." -ForegroundColor Gray
scp nginx-standalone/conf.d/default.conf ${MALINA_USER}@${MALINA_HOST}:/tmp/default.conf

# SCP - skrypt aktualizacji
Write-Host "  -> Kopiuje update_nginx.sh..." -ForegroundColor Gray
scp nginx-standalone/update_nginx.sh ${MALINA_USER}@${MALINA_HOST}:/tmp/update_nginx.sh

# SCP - skrypt diagnostyczny
Write-Host "  -> Kopiuje diagnose_nginx.sh..." -ForegroundColor Gray
scp nginx-standalone/diagnose_nginx.sh ${MALINA_USER}@${MALINA_HOST}:/tmp/diagnose_nginx.sh

# SCP - skrypt naprawy docker-compose
Write-Host "  -> Kopiuje fix_docker_compose.sh..." -ForegroundColor Gray
scp nginx-standalone/fix_docker_compose.sh ${MALINA_USER}@${MALINA_HOST}:/tmp/fix_docker_compose.sh

Write-Host "[OK] Pliki skopiowane" -ForegroundColor Green

Write-Host ""
Write-Host "[2/6] Ustawiam uprawnienia skryptow..." -ForegroundColor Yellow

# Ustaw uprawnienia wykonywania dla skryptów
ssh ${MALINA_USER}@${MALINA_HOST} "chmod +x /tmp/update_nginx.sh /tmp/diagnose_nginx.sh /tmp/fix_docker_compose.sh"
Write-Host "[OK] Uprawnienia ustawione" -ForegroundColor Green

Write-Host ""
Write-Host "[3/6] Naprawiam docker-compose.yml (dodaje conf.d volume)..." -ForegroundColor Yellow
Write-Host ""

# Napraw docker-compose
ssh ${MALINA_USER}@${MALINA_HOST} "/tmp/fix_docker_compose.sh"

Write-Host ""
Write-Host "[4/6] Uruchamiam diagnostyke nginx..." -ForegroundColor Yellow
Write-Host ""

# Uruchom diagnostykę
ssh ${MALINA_USER}@${MALINA_HOST} "/tmp/diagnose_nginx.sh"

Write-Host ""
Write-Host "[5/6] Uruchamiam aktualizacje konfiguracji..." -ForegroundColor Yellow
Write-Host ""

# Uruchom skrypt na malinie
ssh ${MALINA_USER}@${MALINA_HOST} "/tmp/update_nginx.sh"

Write-Host ""
Write-Host "[6/6] Czyszcze pliki tymczasowe..." -ForegroundColor Yellow
ssh ${MALINA_USER}@${MALINA_HOST} "rm /tmp/update_nginx.sh /tmp/diagnose_nginx.sh /tmp/fix_docker_compose.sh"
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
