# Rozdział 6: Deployment i infrastruktura

## 6.1. Przygotowanie środowiska produkcyjnego

### 6.1.1. Konfiguracja serwera

**Wymagania systemowe:**
- **System operacyjny:** Ubuntu Server 22.04 LTS lub nowszy
- **CPU:** Min. 2 vCPU (rekomendowane: 4 vCPU)
- **RAM:** Min. 4 GB (rekomendowane: 8 GB)
- **Dysk:** Min. 20 GB SSD
- **Sieć:** Publiczny adres IP lub dostęp przez VPN/Tailscale

**Instalacja podstawowych pakietów:**

```bash
# Aktualizacja systemu
sudo apt update && sudo apt upgrade -y

# Instalacja Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Dodanie użytkownika do grupy docker
sudo usermod -aG docker $USER

# Instalacja Docker Compose
sudo apt install docker-compose-plugin

# Instalacja pomocniczych narzędzi
sudo apt install git curl wget htop nano ufw
```

**Konfiguracja firewall:**

```bash
# Podstawowa konfiguracja UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Zezwolenie na SSH
sudo ufw allow 22/tcp

# Zezwolenie na HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Zezwolenie na PostgreSQL (tylko z zaufanych IP)
sudo ufw allow from 192.168.1.0/24 to any port 5432

# Włączenie firewall
sudo ufw enable
```

### 6.1.2. Zmienne środowiskowe

**Struktura pliku `.env` (produkcyjny):**

```env
# ============================================================================
# SmartHome Multi-Home - Production Environment Configuration
# ============================================================================

# PostgreSQL Database
DB_HOST=postgres_container
DB_PORT=5432
DB_NAME=smarthome_prod
DB_USER=smarthome_prod_user
DB_PASSWORD=SUPER_SECURE_PASSWORD_CHANGE_ME_123!@#

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=RANDOM_64_CHARACTER_SECRET_KEY_CHANGE_ME_IN_PRODUCTION_XYZ123

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

# Email Configuration (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-app-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
ADMIN_EMAIL=admin@yourdomain.com

# Redis Configuration
REDIS_HOST=redis_container
REDIS_PORT=6379

# Asset Versioning (for cache-busting)
ASSET_VERSION=v1.2.3

# Image Tag for Docker
IMAGE_TAG=latest

# Security Settings
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Logging
LOG_LEVEL=INFO

# Feature Flags
ENABLE_REGISTRATION=true
ENABLE_MULTI_HOME=true

# GitHub Integration (optional)
GITHUB_TOKEN=
GITHUB_REPO_OWNER=YourUsername
GITHUB_REPO_NAME=YourRepo
```

**Generowanie bezpiecznego SECRET_KEY:**

```bash
# Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL
openssl rand -hex 32

# PowerShell
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

**Walidacja zmiennych środowiskowych:**

```python
# utils/validate_env.py
import os
import sys

REQUIRED_VARS = [
    'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD',
    'SECRET_KEY', 'SMTP_USERNAME', 'SMTP_PASSWORD',
    'ADMIN_EMAIL'
]

def validate_environment():
    """Validate that all required environment variables are set"""
    missing = []
    
    for var in REQUIRED_VARS:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        sys.exit(1)
    
    # Check SECRET_KEY length
    secret_key = os.getenv('SECRET_KEY')
    if len(secret_key) < 32:
        print("⚠️  WARNING: SECRET_KEY should be at least 32 characters")
    
    # Check password strength
    db_password = os.getenv('DB_PASSWORD')
    if len(db_password) < 12:
        print("⚠️  WARNING: DB_PASSWORD should be at least 12 characters")
    
    print("✅ Environment validation passed")

if __name__ == '__main__':
    validate_environment()
```

### 6.1.3. Secrets management

**Dla Portainer (zalecane):**

1. W Portainer GUI przejdź do: **Settings → Variables**
2. Dodaj zmienne jako **Secret** (nie Environment Variable)
3. Zmienne Secret są szyfrowane w bazie Portainer

**Dla Docker Swarm:**

```bash
# Utworzenie secret
echo "super_secure_password" | docker secret create db_password -

# Użycie w docker-compose:
services:
  app:
    secrets:
      - db_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    external: true
```

**Dla Kubernetes:**

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: smarthome-secrets
type: Opaque
data:
  db-password: BASE64_ENCODED_PASSWORD
  secret-key: BASE64_ENCODED_SECRET_KEY
```

## 6.2. Konteneryzacja Docker

### 6.2.1. Dockerfile dla aplikacji

**Dockerfile.app:**

```dockerfile
# Multi-stage build for smaller image size
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Accept build arguments
ARG ASSET_VERSION=latest
ENV ASSET_VERSION=${ASSET_VERSION}

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd -m -u 1000 smarthome && \
    mkdir -p /srv/static/profile_pictures && \
    chown -R smarthome:smarthome /srv

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/smarthome/.local

# Copy application code
COPY --chown=smarthome:smarthome . .

# Create necessary directories
RUN mkdir -p /app/logs && \
    chown -R smarthome:smarthome /app

# Switch to non-root user
USER smarthome

# Add local binaries to PATH
ENV PATH=/home/smarthome/.local/bin:$PATH

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/api/ping')" || exit 1

# Run application
CMD ["python", "app_db.py"]
```

**Optymalizacje:**
- Multi-stage build redukuje rozmiar obrazu o ~40%
- Non-root user zwiększa bezpieczeństwo
- HEALTHCHECK umożliwia automatyczny restart przy awarii
- Build args dla ASSET_VERSION (cache-busting)

### 6.2.2. Dockerfile dla Nginx

**Dockerfile.nginx:**

```dockerfile
FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/conf.d/smarthome.conf /etc/nginx/conf.d/

# Create directories for static files
RUN mkdir -p /srv/static/profile_pictures && \
    chown -R nginx:nginx /srv

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf:**

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript 
               application/xml+rss application/rss+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    include /etc/nginx/conf.d/*.conf;
}
```

**smarthome.conf:**

```nginx
upstream flask_app {
    server app:5000 fail_timeout=10s max_fails=3;
    keepalive 32;
}

# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com;

    # Allow Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/ssl/tailscale/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/tailscale/yourdomain.com.key;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Static files with aggressive caching
    location /static/ {
        alias /srv/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Profile pictures
    location /static/profile_pictures/ {
        alias /srv/static/profile_pictures/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    # Proxy to Flask app
    location / {
        proxy_pass http://flask_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # WebSocket specific location
    location /socket.io/ {
        proxy_pass http://flask_app/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket specific timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
}
```

### 6.2.3. Docker Compose configuration

**docker-compose.prod.yml:**

```yaml
version: '3.8'

services:
  app:
    image: ghcr.io/yourusername/smarthome_app:${IMAGE_TAG:-latest}
    container_name: smarthome_app
    restart: unless-stopped
    environment:
      - SERVER_HOST=${SERVER_HOST:-0.0.0.0}
      - SERVER_PORT=${SERVER_PORT:-5000}
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT:-5432}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
      - SMTP_SERVER=${SMTP_SERVER}
      - SMTP_PORT=${SMTP_PORT:-587}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - ADMIN_EMAIL=${ADMIN_EMAIL}
      - REDIS_HOST=${REDIS_HOST:-redis}
      - REDIS_PORT=${REDIS_PORT:-6379}
      - ASSET_VERSION=${ASSET_VERSION:-}
      - FLASK_ENV=production
    volumes:
      - static_uploads:/srv/static/profile_pictures
      - app_logs:/app/logs
    networks:
      - smarthome_network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:5000/api/ping')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: ghcr.io/yourusername/smarthome_nginx:${IMAGE_TAG:-latest}
    container_name: smarthome_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - static_uploads:/srv/static/profile_pictures:ro
      - /etc/ssl/tailscale:/etc/ssl/tailscale:ro
      - nginx_logs:/var/log/nginx
    networks:
      - smarthome_network
    depends_on:
      - app
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  postgres:
    image: postgres:15-alpine
    container_name: smarthome_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - smarthome_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
    ports:
      - "127.0.0.1:5432:5432"  # Only localhost access

  redis:
    image: redis:7-alpine
    container_name: smarthome_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - smarthome_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  static_uploads:
    driver: local
  app_logs:
    driver: local
  nginx_logs:
    driver: local

networks:
  smarthome_network:
    driver: bridge
```

**Uruchomienie stacku:**

```bash
# Utworzenie pliku .env z produkcyjnymi wartościami
cp .env.example .env
nano .env  # Edycja wartości

# Walidacja konfiguracji
docker-compose -f docker-compose.prod.yml config

# Uruchomienie stacku
docker-compose -f docker-compose.prod.yml up -d

# Sprawdzenie statusu
docker-compose -f docker-compose.prod.yml ps

# Podgląd logów
docker-compose -f docker-compose.prod.yml logs -f

# Restart pojedynczego serwisu
docker-compose -f docker-compose.prod.yml restart app
```

## 6.3. CI/CD Pipeline

### 6.3.1. GitHub Actions workflow

**.github/workflows/docker-build-push.yml:**

```yaml
name: Build and Push Docker Images

on:
  push:
    branches:
      - main
      - develop
    tags:
      - 'v*'
  pull_request:
    branches:
      - main

env:
  REGISTRY: ghcr.io
  IMAGE_NAME_APP: ${{ github.repository }}/smarthome_app
  IMAGE_NAME_NGINX: ${{ github.repository }}/smarthome_nginx

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata for App
        id: meta-app
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_APP }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Extract metadata for Nginx
        id: meta-nginx
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_NGINX }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push App image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile.app
          push: true
          tags: ${{ steps.meta-app.outputs.tags }}
          labels: ${{ steps.meta-app.outputs.labels }}
          build-args: |
            ASSET_VERSION=${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push Nginx image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile.nginx
          push: true
          tags: ${{ steps.meta-nginx.outputs.tags }}
          labels: ${{ steps.meta-nginx.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Create deployment artifact
        if: github.ref == 'refs/heads/main'
        run: |
          echo "Deployment successful for commit ${{ github.sha }}"
          echo "App image: ${{ steps.meta-app.outputs.tags }}"
          echo "Nginx image: ${{ steps.meta-nginx.outputs.tags }}"
```

### 6.3.2. Automatyczne budowanie obrazów

**Proces budowania:**

1. **Trigger:** Push do branch `main` lub tag `v*`
2. **Checkout:** Pobieranie kodu z repozytorium
3. **Buildx:** Setup Docker Buildx dla multi-platform builds
4. **Login:** Logowanie do GitHub Container Registry
5. **Metadata:** Generowanie tagów (latest, sha, version)
6. **Build:** Budowanie obrazów z cache
7. **Push:** Wysyłanie obrazów do registry
8. **Artifact:** Utworzenie podsumowania deployment

**Tagi obrazów:**
- `latest` - najnowszy build z main
- `v1.2.3` - wersja semantyczna (z tagu Git)
- `sha-abc1234` - commit SHA dla rollback
- `pr-123` - build z Pull Request

### 6.3.3. Testy automatyczne

**.github/workflows/tests.yml:**

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: test_db
          DB_USER: test_user
          DB_PASSWORD: test_password
          REDIS_HOST: localhost
          REDIS_PORT: 6379
          SECRET_KEY: test_secret_key_for_ci
        run: |
          pytest tests/ --cov=app --cov=utils --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

---

**Podsumowanie rozdziału 6:**

Rozdział deployment opisuje kompletny proces wdrażania systemu SmartHome Multi-Home w środowisku produkcyjnym. Przedstawiono konfigurację serwera, zarządzanie zmiennymi środowiskowymi i secrets, konteneryzację aplikacji z Docker oraz konfigurację Nginx jako reverse proxy.

Szczególną uwagę poświęcono bezpieczeństwu (firewall, non-root user, SSL/TLS) oraz optymalizacji (multi-stage build, health checks, caching). Opisano również CI/CD pipeline z GitHub Actions automatycznie budujący i publikujący obrazy Docker.

W następnym rozdziale zostaną omówione aspekty bezpieczeństwa systemu zgodnie ze standardami OWASP.
