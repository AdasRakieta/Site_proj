# Environment Configuration Guide

## Overview

SmartHome Multi-Home system uses a **single `.env` file** in the project root for configuration. This file is **never committed to Git** for security reasons.

## Configuration Priority

The application loads environment variables with the following priority:

1. **System Environment Variables** (highest priority)
   - Set directly in Portainer GUI
   - Set in Docker Compose `environment:` section
   - Set in container runtime

2. **`.env` File** (fallback)
   - Located in project root
   - Used for local development
   - Not present in production containers

## File Structure

```
Site_proj/
├── .env                    # Main configuration (NOT in Git)
├── .env.example           # Template (in Git)
├── app_db.py             # Application entry point
└── docker-compose.yml    # Docker configuration
```

## Local Development Setup

### 1. Create `.env` File

Copy the example and fill in your values:

```bash
cp .env.example .env
```

### 2. Edit `.env` with Your Settings

```properties
# PostgreSQL Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smarthome_multihouse
DB_USER=admin
DB_PASSWORD=your_secure_password

# Server Configuration
SERVER_PORT=5000
SERVER_HOST=0.0.0.0

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ADMIN_EMAIL=admin@yourdomain.com

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=dev_secret_key_change_in_production

# Optional Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Run the Application

```bash
python app_db.py
```

The application will:
1. Check for system environment variables (none in local dev)
2. Load values from `.env` file
3. Start the server

## Production Deployment (Portainer)

### Method 1: Portainer Stack GUI (Recommended)

1. **Navigate to Stacks** → Add Stack
2. **Paste `docker-compose.prod.yml`** content
3. **Set Environment Variables** in Portainer GUI:

```
DB_HOST=100.103.184.90
DB_PORT=5432
DB_NAME=smarthome_multihouse
DB_USER=admin
DB_PASSWORD=Qwuizzy123.
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=smarthome.alertmail@gmail.com
SMTP_PASSWORD=pqvg eabu bmka mggk
ADMIN_EMAIL=szymon.przybysz2003@gmail.com
FLASK_ENV=production
SECRET_KEY=production_secret_minimum_32_chars
IMAGE_TAG=latest
```

4. **Deploy Stack**

### Method 2: Docker Compose with .env

For local Docker testing:

```bash
# .env file present in directory
docker-compose -f docker-compose.yml up -d
```

## How It Works

### Application Startup (`app_db.py`)

```python
from dotenv import load_dotenv

# Load .env file but DON'T override existing environment variables
# Priority: System env vars > .env file
load_dotenv(override=False)

# Now all modules can use os.getenv()
```

### Database Manager (`utils/db_manager.py`)

```python
import os

# Read from environment (set by load_dotenv or system)
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
```

## Security Best Practices

### ✅ DO:
- Keep `.env` file **only on your local machine**
- Use **different passwords** for development and production
- Set production variables **directly in Portainer GUI**
- Use `.env.example` as a template (safe to commit)
- Generate strong `SECRET_KEY` for production

### ❌ DON'T:
- **Never commit `.env`** to Git (already in `.gitignore`)
- Don't share `.env` file via email/chat
- Don't use development passwords in production
- Don't hardcode secrets in Python files

## Troubleshooting

### Issue: "Missing DB_HOST environment variable"

**Cause**: No `.env` file and no system environment variables set

**Solution**:
- **Local**: Create `.env` file from `.env.example`
- **Portainer**: Set variables in Stack GUI

### Issue: Application uses wrong database

**Cause**: System environment variables override `.env`

**Solution**:
```bash
# Check what's actually set
python -c "import os; from dotenv import load_dotenv; load_dotenv(override=False); print(f'DB_HOST: {os.getenv(\"DB_HOST\")}')"
```

### Issue: Changes to `.env` not taking effect

**Cause**: System environment variables have priority

**Solution**:
1. Check system environment: `echo $DB_HOST` (Linux) or `$env:DB_HOST` (Windows)
2. Unset system variable or restart terminal
3. Restart application

## Migration from Old System

If you previously used `stack.env`:

### Old Structure (Deprecated):
```
.env              # Local development
stack.env         # Production template (in Git)
```

### New Structure (Current):
```
.env              # Both local dev and template (NOT in Git)
.env.example      # Template (in Git)
```

### Migration Steps:

1. **Copy your production values** from `stack.env` to safe location
2. **Delete `stack.env`** (no longer needed)
3. **Update your local `.env`** with development values
4. **Set production values** in Portainer GUI
5. **Commit changes** to Git

```bash
# Remove stack.env from Git
git rm stack.env
git commit -m "Remove deprecated stack.env - use Portainer GUI for production config"
git push
```

## Docker Configuration Files

### `docker-compose.yml` (Local Development)

```yaml
services:
  app:
    env_file:
      - .env  # Loads .env file
    environment:
      # Variables from .env are available here
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
```

### `docker-compose.prod.yml` (Production/Portainer)

```yaml
services:
  app:
    # NO env_file directive (Portainer doesn't support it)
    environment:
      # Set directly in Portainer GUI
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
```

## Environment Variable Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL server address | `100.103.184.90` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `smarthome_multihouse` |
| `DB_USER` | Database username | `admin` |
| `DB_PASSWORD` | Database password | `SecurePass123` |
| `SMTP_SERVER` | Email server | `smtp.gmail.com` |
| `SMTP_PORT` | Email port | `587` |
| `SMTP_USERNAME` | Email account | `app@gmail.com` |
| `SMTP_PASSWORD` | Email password/app key | `abcd efgh ijkl` |
| `ADMIN_EMAIL` | Admin notifications | `admin@domain.com` |
| `SECRET_KEY` | Flask session key | `random_32_char_string` |
| `FLASK_ENV` | Environment mode | `production` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SERVER_HOST` | Bind address | `0.0.0.0` | `0.0.0.0` |
| `SERVER_PORT` | Application port | `5000` | `5000` |
| `REDIS_HOST` | Redis server | None | `redis` |
| `REDIS_PORT` | Redis port | `6379` | `6379` |
| `ASSET_VERSION` | Cache-busting version | Git SHA | `abc123def` |
| `IMAGE_TAG` | Docker image tag | `latest` | `v1.2.3` |

## Quick Reference

### Check Current Configuration

```bash
# Python
python -c "import os; from dotenv import load_dotenv; load_dotenv(override=False); print('DB_HOST:', os.getenv('DB_HOST'))"

# PowerShell
$env:DB_HOST

# Bash
echo $DB_HOST
```

### Update Production Configuration

1. **Portainer** → Stacks → Your Stack
2. Click **Editor** tab
3. Scroll to bottom → **Environment variables**
4. Update values
5. Click **Update the stack**

### Generate Secure SECRET_KEY

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

## Summary

- ✅ **One `.env` file** in project root
- ✅ **Never committed** to Git (security)
- ✅ **System environment variables** override `.env` (Portainer priority)
- ✅ **`.env.example`** serves as template (safe to commit)
- ✅ **Production**: Set variables in Portainer GUI
- ✅ **Development**: Use `.env` file locally

---

**Last Updated**: October 2025  
**Version**: 2.0 (Unified Configuration)
