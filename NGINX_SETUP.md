# Nginx Configuration for Journey Planner + SmartHome Apps

This document explains the nginx configuration for serving both the Journey Planner and SmartHome applications under `malina.tail384b18.ts.net`.

## Architecture Overview

Both applications are accessible through the same Tailscale domain using path-based routing:
- **SmartHome app** (główna): `https://malina.tail384b18.ts.net/` (root path)
- **Journey Planner**: `https://malina.tail384b18.ts.net/journey/`
- **Portainer**: `https://malina.tail384b18.ts.net/portainer/`
- **Grafana**: `https://malina.tail384b18.ts.net/grafana/`

## Current Nginx Configuration

The nginx configuration is located in `nginx/default.conf` and includes:

### Upstream Definitions
```nginx
upstream smarthome_app {
    server app:5000;  # SmartHome Flask container
}

upstream journey_planner_app {
    server 172.17.0.1:5001;  # Journey Planner running on host
}
```

### SmartHome Routes (Main Application)
- `/` - SmartHome main application (default)
- `/api/` - SmartHome REST API
- `/socket.io/` - SmartHome WebSocket (real-time updates)
- `/static/` - SmartHome static files (CSS, JS, images, profile pictures)

### Journey Planner Routes
- `/journey/` - Journey Planner frontend (static files)
- `/journey/api/` - Journey Planner REST API

### Management Tools
- `/portainer/` - Portainer container management
- `/grafana/` - Grafana monitoring dashboards
- `/health` - Health check endpoint

## Docker Compose Configuration

The `docker-compose.yml` includes volume mounts for:
- `static_uploads` - SmartHome profile pictures
- `/etc/ssl/tailscale` - SSL certificates (read-only)
- `/home/pi/journey-planner/client/dist` - Journey Planner frontend build (read-only)

## Port Allocation

- **SmartHome Flask App**: Port 5000 (Docker container `app:5000`)
- **Journey Planner API**: Port 5001 (Host process `172.17.0.1:5001`)
- **PostgreSQL**: Port 5432 (external or host)
- **Redis**: Port 6379 (external container `smarthome_redis_standalone`)
- **Nginx**: Ports 80/443 (HTTP/HTTPS)
- **Portainer**: Port 9000 (Docker host)
- **Grafana**: Port 3000 (Docker host)

## Steps to Deploy Journey Planner on Raspberry Pi

### 1. Clone Journey Planner Repository
```bash
cd /home/pi
git clone <journey-planner-repo-url> journey-planner
cd journey-planner
```

### 2. Set up PostgreSQL Database
```bash
sudo -u postgres psql
CREATE DATABASE journey_planner;
CREATE USER journey_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE journey_planner TO journey_user;
\q
```

### 3. Configure Backend Environment
```bash
cd /home/pi/journey-planner/server
cp .env.example .env
nano .env
```

Update `.env` with:
```env
PORT=5001
DATABASE_URL=postgresql://journey_user:your_secure_password@localhost:5432/journey_planner
NODE_ENV=production
```

### 4. Configure Frontend Environment
```bash
cd /home/pi/journey-planner/client
cp .env.example .env.production
nano .env.production
```

Update `.env.production` with:
```env
VITE_API_URL=/journey/api
```

Also update `client/vite.config.ts` to set base path:
```typescript
export default defineConfig({
  base: '/journey/',
  // ... other config
})
```

### 5. Install Dependencies and Build
```bash
# Backend
cd /home/pi/journey-planner/server
npm install
npm run build

# Frontend
cd /home/pi/journey-planner/client
npm install
npm run build
```

### 6. Set up PM2 Process Manager
```bash
# Install PM2 globally if not already installed
sudo npm install -g pm2

# Start Journey Planner API
cd /home/pi/journey-planner/server
pm2 start dist/index.js --name journey-planner-api

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Follow the instructions provided by the command above
```

### 7. Update SmartHome Docker Stack

The nginx configuration has already been updated in this repository. To apply changes:

```bash
cd /home/pi/Site_proj  # or wherever your SmartHome project is located

# Pull latest changes (if you pushed nginx/default.conf changes)
git pull

# Rebuild and restart nginx container
docker-compose build nginx
docker-compose up -d nginx

# Or if using Portainer, update the stack with new docker-compose.yml
```

### 8. Verify Deployment

Check that all services are running:

```bash
# Journey Planner API
pm2 status
pm2 logs journey-planner-api

# Test Journey Planner API directly
curl http://localhost:5001/api/health

# Test through nginx
curl https://malina.tail384b18.ts.net/journey/api/health

# Check SmartHome is still working
curl https://malina.tail384b18.ts.net/api/rooms
```

Access applications:
- SmartHome: `https://malina.tail384b18.ts.net/`
- Journey Planner: `https://malina.tail384b18.ts.net/journey/`

## Troubleshooting

1. **Port conflicts**: Make sure port 5001 is available:
   ```bash
   sudo lsof -i :5001
   ```

2. **PostgreSQL connection issues**:
   ```bash
   sudo systemctl status postgresql
   sudo -u postgres psql -l  # List databases
   ```

3. **Nginx logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   sudo tail -f /var/log/nginx/access.log
   ```

4. **Application logs**:
   ```bash
   pm2 logs journey-planner-api
   ```

## Troubleshooting

### Port Conflicts
Check if port 5001 is available:
```bash
sudo lsof -i :5001
# If something is using it, stop that process or choose different port
```

### PostgreSQL Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# List databases
sudo -u postgres psql -l

# Test connection
psql -h localhost -U journey_user -d journey_planner
```

### Journey Planner API Issues
```bash
# Check PM2 process status
pm2 status

# View logs
pm2 logs journey-planner-api

# Restart if needed
pm2 restart journey-planner-api

# Check if API is responding
curl http://localhost:5001/api/health
```

### Nginx Issues
```bash
# Test nginx configuration
sudo docker exec smarthome_nginx nginx -t

# View nginx logs
docker logs smarthome_nginx

# Restart nginx container
docker-compose restart nginx
```

### SmartHome Not Working After Changes
```bash
# Check SmartHome container
docker ps | grep smarthome_app

# View SmartHome logs
docker logs smarthome_app

# Restart SmartHome if needed
docker-compose restart app

# Test SmartHome API
curl https://malina.tail384b18.ts.net/api/rooms
```

### Journey Planner Frontend Not Loading
```bash
# Check if files exist and have correct permissions
ls -la /home/pi/journey-planner/client/dist/

# Check nginx can read the files
sudo docker exec smarthome_nginx ls -la /srv/journey-planner/

# Rebuild frontend if needed
cd /home/pi/journey-planner/client
npm run build
```

### WebSocket Connection Issues (SmartHome)
If Socket.IO real-time updates aren't working:
```bash
# Check if WebSocket headers are properly set in nginx
docker exec smarthome_nginx cat /etc/nginx/conf.d/default.conf | grep -A5 "socket.io"

# Check browser console for WebSocket connection errors
# Should connect to: wss://malina.tail384b18.ts.net/socket.io/
```

### SSL Certificate Issues
```bash
# Check if Tailscale certificates are valid
ls -la /etc/ssl/tailscale/

# Renew Tailscale certificates if needed
sudo tailscale cert malina.tail384b18.ts.net
```

## Monitoring and Logs

### View All Application Logs
```bash
# SmartHome App
docker logs -f smarthome_app

# Nginx
docker logs -f smarthome_nginx

# Journey Planner
pm2 logs journey-planner-api --lines 100

# Follow all PM2 logs
pm2 logs
```

### Health Checks
Test all services:
```bash
# SmartHome API
curl -k https://malina.tail384b18.ts.net/api/rooms

# Journey Planner API (via nginx)
curl -k https://malina.tail384b18.ts.net/journey/api/health

# Journey Planner API (direct)
curl http://localhost:5001/api/health

# Nginx health endpoint
curl -k https://malina.tail384b18.ts.net/health
```

## File Structure

```
/home/pi/
├── Site_proj/                          # SmartHome project (Docker)
│   ├── docker-compose.yml             # Updated with journey-planner volume
│   ├── nginx/
│   │   └── default.conf               # Updated nginx config
│   └── app_db.py                      # SmartHome Flask app
│
└── journey-planner/                    # Journey Planner project (PM2)
    ├── server/
    │   ├── dist/                      # Built backend
    │   ├── .env                       # Backend environment (PORT=5001)
    │   └── package.json
    └── client/
        ├── dist/                      # Built frontend (mounted to nginx)
        ├── .env.production            # VITE_API_URL=/journey/api
        ├── vite.config.ts             # base: '/journey/'
        └── package.json
```

## Quick Reference Commands

```bash
# Restart everything
docker-compose restart nginx app
pm2 restart journey-planner-api

# View status
docker-compose ps
pm2 status

# Update nginx config
cd /home/pi/Site_proj
git pull
docker-compose up -d nginx

# Rebuild Journey Planner
cd /home/pi/journey-planner/client
npm run build
pm2 restart journey-planner-api
```