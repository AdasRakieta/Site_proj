# SmartHome Quick Rebuild and Deploy Script
# Rebuilds Docker images and deploys to Raspberry Pi

Write-Host "=== SmartHome Rebuild & Deploy ===" -ForegroundColor Cyan

# Step 1: Rebuild Docker image
Write-Host "`n[1/4] Building Docker image..." -ForegroundColor Yellow
docker-compose -f docker-compose_smarthome+nginix.yml build app
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Image built successfully" -ForegroundColor Green

# Step 2: Save image to tar file
Write-Host "`n[2/4] Exporting image to tar file..." -ForegroundColor Yellow
docker save -o smarthome-app.tar smarthome-app:latest
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to export image!" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Image exported: smarthome-app.tar ($(((Get-Item smarthome-app.tar).Length / 1MB).ToString('F2')) MB)" -ForegroundColor Green

# Step 3: Copy to Raspberry Pi
Write-Host "`n[3/4] Copying image to Raspberry Pi..." -ForegroundColor Yellow
Write-Host "This may take a few minutes depending on image size and network speed..." -ForegroundColor Gray
scp smarthome-app.tar adas.rakieta@192.168.1.218:/tmp/
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to copy image to Raspberry Pi!" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Image copied to malina:/tmp/" -ForegroundColor Green

# Step 4: Load image and restart containers on Raspberry Pi
Write-Host "`n[4/4] Deploying on Raspberry Pi..." -ForegroundColor Yellow
ssh adas.rakieta@192.168.1.218 @"
echo 'Loading Docker image...'
docker load -i /tmp/smarthome-app.tar
echo 'Stopping containers...'
cd /opt/smarthome
docker-compose down
echo 'Starting containers with new image...'
docker-compose up -d
echo 'Cleaning up...'
rm /tmp/smarthome-app.tar
echo 'Deployment complete!'
docker-compose ps
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deployment failed on Raspberry Pi!" -ForegroundColor Red
    exit 1
}

# Cleanup local tar file
Write-Host "`nCleaning up local files..." -ForegroundColor Gray
Remove-Item smarthome-app.tar -ErrorAction SilentlyContinue

Write-Host "`n=== DEPLOYMENT SUCCESSFUL ===" -ForegroundColor Green
Write-Host "Grafana should now show 'UP' status" -ForegroundColor Cyan
Write-Host "Monitor health endpoint: curl http://malina.tail384b18.ts.net/health" -ForegroundColor Gray
