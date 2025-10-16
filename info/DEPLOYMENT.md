# Deployment Guide - SmartHome Multi-Home System

## Environment Configuration Files

This project uses a unified environment configuration system with the following files:

### 📁 Files Overview

| File | Purpose | Git Status | Usage |
|------|---------|-----------|-------|
| `.env` | Local development configuration | **IGNORED** (not in repo) | Development & testing |
| `.env.example` | Template for `.env` | **TRACKED** | Copy to create `.env` |
| `stack.env` | Docker Stack deployment template | **TRACKED** | Production deployment |

---

## 🚀 Quick Start

### Local Development

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your local settings:**
   ```bash
   # Update database credentials
   DB_HOST=localhost
   DB_NAME=smarthome_multihouse
   DB_USER=your_user
   DB_PASSWORD=your_password
   
   # Update email settings
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```

3. **Run the application:**
   ```bash
   python app_db.py
   ```

---

## 🐳 Docker Deployment

### Using Docker Compose (Development)

1. **Ensure `.env` exists** (copy from `.env.example` if needed)

2. **Run with docker-compose:**
   ```bash
   docker-compose up -d
   ```
   
   This uses the `.env` file automatically via `env_file: .env`

### Using Docker Stack (Production)

1. **Edit `stack.env` with production credentials:**
   ```bash
   # IMPORTANT: Update these values before deploying!
   DB_HOST=your_production_postgres_host
   DB_PASSWORD=SECURE_PASSWORD_HERE
   SECRET_KEY=RANDOM_32_CHAR_STRING_HERE
   SMTP_PASSWORD=production_email_password
   ```

2. **Deploy the stack:**
   ```bash
   # Export environment variables from stack.env
   export $(cat stack.env | grep -v '^#' | xargs)
   
   # Deploy using docker-compose.prod.yml
   docker-compose -f docker-compose.prod.yml up -d
   ```

   Or for Docker Swarm:
   ```bash
   docker stack deploy -c docker-compose.prod.yml smarthome
   ```

---

## 🔐 Security Best Practices

### ⚠️ NEVER commit sensitive data!

- `.env` is in `.gitignore` - **never remove it!**
- `stack.env` is committed as a **template only**
- Update `stack.env` values **on the server**, not in the repository

### 🔑 Required Environment Variables

All deployments must set these variables:

```bash
# Database (Required)
DB_HOST=          # PostgreSQL host
DB_NAME=          # Database name
DB_USER=          # Database user
DB_PASSWORD=      # Database password (KEEP SECRET!)

# Flask (Required)
SECRET_KEY=       # Random 32+ character string (KEEP SECRET!)

# Email (Required)
SMTP_USERNAME=    # Email account
SMTP_PASSWORD=    # Email password or app-specific password (KEEP SECRET!)
ADMIN_EMAIL=      # Admin contact email
```

### 🛡️ Production Security Checklist

- [ ] Change `DB_PASSWORD` from default
- [ ] Generate random `SECRET_KEY` (32+ characters)
- [ ] Use app-specific password for `SMTP_PASSWORD`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `SECURE_COOKIES=true`
- [ ] Verify `stack.env` has production values
- [ ] Never expose `.env` files to public

---

## 🔄 Migration from Old Setup

If you have multiple `.env` files (e.g., `db.env`, `email_conf.env`):

1. **Merge all variables into single `.env`:**
   ```bash
   # Old setup (deprecated):
   # - db.env
   # - email_conf.env
   # - app.env
   
   # New setup (use this):
   # - .env (for all variables)
   ```

2. **Use the provided `.env.example` as reference** to ensure all variables are included

3. **Delete old environment files** to avoid confusion

---

## 📋 Variable Reference

See `.env.example` for complete list of all available environment variables with descriptions.

### Core Variables:
- **Database**: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **Server**: `SERVER_HOST`, `SERVER_PORT`, `FLASK_ENV`
- **Email**: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `ADMIN_EMAIL`
- **Security**: `SECRET_KEY`, `SECURE_COOKIES`
- **Optional**: `REDIS_HOST`, `REDIS_PORT`, `ASSET_VERSION`, `IMAGE_TAG`

---

## 🐛 Troubleshooting

### Error: "Missing DB_HOST environment variable"

**Cause**: Environment variables not loaded

**Solutions**:
1. Ensure `.env` file exists in project root
2. Verify `.env` contains `DB_HOST=your_host`
3. For Docker: check `env_file` is set in `docker-compose.yml`
4. For production: verify `stack.env` has correct values

### Error: "Cannot connect to database"

**Cause**: Database credentials incorrect or DB not accessible

**Solutions**:
1. Verify database is running: `psql -h $DB_HOST -U $DB_USER -d $DB_NAME`
2. Check network connectivity to `DB_HOST`
3. Verify credentials in `.env` match database
4. For Docker: ensure DB host is accessible from container network

### Docker containers can't read .env

**Cause**: `.env` not mounted or `env_file` not configured

**Solution**:
```yaml
# In docker-compose.yml
services:
  app:
    env_file:
      - .env  # ← Ensure this line exists
```

---

## 📞 Support

For issues or questions:
- Check logs: `docker logs smarthome_app`
- Review `.env.example` for required variables
- Ensure all secret values are updated in production

---

**Last Updated**: October 2025  
**Version**: 2.0 (Unified Environment Configuration)
