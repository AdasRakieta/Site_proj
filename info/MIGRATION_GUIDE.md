# Migration Guide: Environment Configuration Update

## 🔄 Overview

This guide helps you migrate from the old multi-file environment configuration to the new unified `.env` structure.

## What Changed?

### Old Structure (Deprecated) ❌
```
├── .env (partial config)
├── db.env (database config)
├── email_conf.env (email config)
├── app.env (app config)
└── other .env files...
```

### New Structure (Current) ✅
```
├── .env (ALL config - local development)
├── .env.example (template)
└── stack.env (production deployment template)
```

---

## 📝 Migration Steps

### Step 1: Backup Current Configuration

Save your current environment files:

```bash
mkdir env_backup
cp .env env_backup/ 2>/dev/null || true
cp db.env env_backup/ 2>/dev/null || true
cp email_conf.env env_backup/ 2>/dev/null || true
cp app.env env_backup/ 2>/dev/null || true
```

### Step 2: Create New Unified `.env`

Copy the example file:

```bash
cp .env.example .env
```

### Step 3: Migrate Variables

Open your new `.env` file and fill in values from your old files:

#### From `db.env` or similar:
```env
# Old location: db.env
DB_HOST=your_value_here
DB_PORT=5432
DB_NAME=smarthome_multihouse
DB_USER=your_user
DB_PASSWORD=your_password
```

#### From `email_conf.env` or similar:
```env
# Old location: email_conf.env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ADMIN_EMAIL=admin@example.com
```

#### From `app.env` or similar:
```env
# Old location: app.env
SERVER_PORT=5000
SERVER_HOST=0.0.0.0
FLASK_ENV=development
```

#### Add New Required Variables:
```env
# New requirement - generate a random string
SECRET_KEY=generate_random_32_character_string_here
```

### Step 4: Generate SECRET_KEY

If you don't have a `SECRET_KEY`, generate one:

**Python:**
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**PowerShell:**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

Copy the output to your `.env`:
```env
SECRET_KEY=your_generated_key_here
```

### Step 5: Clean Up Old Files

After verifying the new `.env` works:

```bash
# Remove old environment files (optional)
rm db.env email_conf.env app.env

# Keep backups in env_backup/ folder
```

### Step 6: Update docker-compose (if used)

The new `docker-compose.yml` automatically uses `.env` via `env_file` directive.

**Old docker-compose.yml:**
```yaml
environment:
  - SERVER_HOST=0.0.0.0
  # hardcoded values...
```

**New docker-compose.yml:**
```yaml
env_file:
  - .env
environment:
  - SERVER_HOST=${SERVER_HOST:-0.0.0.0}
  - DB_HOST=${DB_HOST}
  # uses .env values...
```

Just pull the latest `docker-compose.yml` from the repo.

### Step 7: Test

Run the application to verify everything works:

```bash
python app_db.py
```

You should see:
```
✓ Using PostgreSQL database backend
```

---

## 🐳 Docker Migration

### For Production Deployments

1. **Update `stack.env` with your production values:**
   ```bash
   cp stack.env stack.env.backup
   nano stack.env  # or your preferred editor
   ```

2. **Update these critical values:**
   ```env
   DB_HOST=your_production_db_host
   DB_PASSWORD=secure_production_password
   SECRET_KEY=random_production_secret_key
   SMTP_PASSWORD=production_email_password
   FLASK_ENV=production
   SECURE_COOKIES=true
   ```

3. **Redeploy:**
   ```bash
   # Export environment from stack.env
   export $(cat stack.env | grep -v '^#' | xargs)
   
   # Pull latest images
   docker-compose -f docker-compose.prod.yml pull
   
   # Restart services
   docker-compose -f docker-compose.prod.yml up -d
   ```

---

## ✅ Verification Checklist

After migration, verify:

- [ ] Application starts without errors
- [ ] Database connection works (check logs)
- [ ] Email sending works (test forgot password)
- [ ] Login/logout works
- [ ] Session persistence works
- [ ] All old functionality works

### Quick Test Commands:

```bash
# Check if .env is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'DB_HOST: {os.getenv(\"DB_HOST\")}')"

# Test database connection
python -c "from utils.db_manager import get_db_connection; conn = get_db_connection(); print('✓ DB connection successful'); conn.close()"
```

---

## 🆘 Troubleshooting

### Error: "Missing DB_HOST environment variable"

**Cause:** `.env` file not loaded or doesn't contain required variables

**Fix:**
1. Ensure `.env` exists in project root
2. Check it contains `DB_HOST=your_value`
3. Restart the application

### Error: "Permission denied" on .env

**Cause:** File permissions too restrictive

**Fix:**
```bash
chmod 600 .env  # Owner read/write only (recommended)
```

### Docker can't read .env

**Cause:** `env_file` not specified in docker-compose.yml

**Fix:** Pull latest docker-compose.yml or add:
```yaml
services:
  app:
    env_file:
      - .env
```

### Still see old variable names in logs

**Cause:** Cached environment or old code

**Fix:**
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Restart application
python app_db.py
```

---

## 📞 Need Help?

If you encounter issues during migration:

1. Check `DEPLOYMENT.md` for detailed deployment instructions
2. Review `.env.example` for all available variables
3. Check application logs: `docker logs smarthome_app`
4. Verify database connectivity: `psql -h $DB_HOST -U $DB_USER -d $DB_NAME`

---

**Migration Version:** 2.0  
**Last Updated:** October 2025  
**Migrates From:** Multi-file env setup  
**Migrates To:** Unified .env + stack.env
