#!/bin/bash
# Quick Deploy Script for Raspberry Pi (using GHCR images)
# Run this ON Raspberry Pi after GitHub Actions builds new image

echo "=== SmartHome Quick Deploy from GHCR ==="
echo ""

# Step 1: Pull latest image from GitHub Container Registry
echo "[1/3] Pulling latest image from GHCR..."
docker pull ghcr.io/adasrakieta/site_proj/smarthome_app:latest
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to pull image from GHCR!"
    echo "Make sure you're logged in: docker login ghcr.io -u adasrakieta"
    exit 1
fi
echo "✓ Image pulled successfully"

# Step 2: Stop containers
echo ""
echo "[2/3] Stopping containers..."
cd /opt/smarthome || cd ~/smarthome || { echo "ERROR: SmartHome directory not found!"; exit 1; }
docker-compose down

# Step 3: Start with new image
echo ""
echo "[3/3] Starting containers with new image..."
docker-compose up -d

# Show status
echo ""
echo "=== Status ==="
docker-compose ps

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo "Health check: curl http://localhost:5000/health"
echo "Or from outside: curl http://malina.tail384b18.ts.net/health"
