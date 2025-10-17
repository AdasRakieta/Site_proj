# Migration: Unified .env Configuration

## Summary of Changes

**Date**: October 2025  
**Change**: Unified environment configuration to single `.env` file

### What Changed

**Before**:
```
.env         # Local development (not in Git)
stack.env    # Production template (in Git)
```

**After**:
```
.env         # All environments (not in Git)
.env.example # Template (in Git)
```

## Migration Steps

### Step 1: Backup Current Configuration

```powershell
# If you have production values in stack.env, save them
cp stack.env stack.env.backup
```

### Step 2: Update Application Code

The following files were updated to use unified `.env`:

- ✅ `app_db.py` - Uses `load_dotenv(override=False)` for proper priority
- ✅ `fetch_geonames_cities.py` - Same priority logic
- ✅ `.gitignore` - Updated comment about configuration
- ✅ `docker-compose.yml` - Added clarifying comments

### Step 3: Remove Deprecated Files

```bash
git rm stack.env
```

### Step 4: Local Development

```bash
# Copy template
cp .env.example .env

# Edit with your local values
# Then run:
python app_db.py
```

### Step 5: Production (Portainer)

**Don't upload `.env` to production!**

Instead, set environment variables in Portainer GUI:

1. Open Portainer → Stacks → Your Stack
2. Click "Editor" tab
3. Scroll to bottom → "Environment variables" section
4. Add all required variables:
   - `DB_HOST`
   - `DB_PORT`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`
   - `SMTP_SERVER`
   - `SMTP_PORT`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`
   - `ADMIN_EMAIL`
   - `FLASK_ENV=production`
   - `SECRET_KEY` (generate new secure key!)
   - `IMAGE_TAG=latest`
5. Update the stack

## Key Benefits

### 🔒 Security
- ✅ `.env` never committed to Git
- ✅ Production secrets only in Portainer
- ✅ No sensitive data in repository

### 🎯 Simplicity
- ✅ One configuration file to manage
- ✅ Same format for all environments
- ✅ Clear priority: System env > .env file

### 🔧 Flexibility
- ✅ Portainer GUI overrides `.env`
- ✅ Easy local development setup
- ✅ No file uploads needed in production

## Configuration Priority

```
┌─────────────────────────────────────┐
│  1. System Environment Variables    │  ← Highest Priority
│     (Portainer GUI, Docker env:)    │
├─────────────────────────────────────┤
│  2. .env File                       │  ← Fallback
│     (Local development)             │
└─────────────────────────────────────┘
```

**How it works**:

```python
# In app_db.py
from dotenv import load_dotenv

# override=False means: don't replace existing env vars
load_dotenv(override=False)

# Result:
# - Portainer vars are preserved
# - .env fills in missing values
# - Local dev works without Portainer
```

## Troubleshooting

### Q: Application still uses old values?

**A**: Restart the container/application after changing environment variables.

```bash
# Portainer: Update the stack (auto-restart)
# Docker Compose: 
docker-compose restart app
```

### Q: How to check which values are active?

**A**: Add debug print in `app_db.py`:

```python
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
```

### Q: `.env` changes not taking effect?

**A**: Make sure no system environment variables are set:

```powershell
# PowerShell - check
$env:DB_HOST

# PowerShell - clear
Remove-Item Env:\DB_HOST
```

## Files Modified

| File | Change |
|------|--------|
| `app_db.py` | Added `override=False` to `load_dotenv()` |
| `fetch_geonames_cities.py` | Added `override=False` to `load_dotenv()` |
| `.gitignore` | Updated comments |
| `docker-compose.yml` | Added clarifying comments |
| `stack.env` | Removed from Git tracking |

## Rollback Plan

If you need to rollback:

```bash
# Restore stack.env
git checkout HEAD~1 -- stack.env

# Revert app_db.py
git checkout HEAD~1 -- app_db.py

# Revert fetch_geonames_cities.py
git checkout HEAD~1 -- fetch_geonames_cities.py
```

## Validation

After migration, verify:

1. ✅ Local development works with `.env`
2. ✅ Production works with Portainer GUI variables
3. ✅ `.env` is not in Git (check with `git status`)
4. ✅ Application logs show correct configuration on startup

```bash
# Should show: ✓ Using PostgreSQL database backend
python app_db.py
```

## Documentation

See comprehensive guide: `info/ENV_CONFIGURATION.md`

---

**Migration completed**: October 2025  
**Breaking changes**: None (backward compatible)  
**Action required**: Update Portainer Stack with environment variables
