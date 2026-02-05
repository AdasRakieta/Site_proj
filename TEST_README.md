# SmartHome Test Suite

Comprehensive automated testing for the SmartHome application.

## Test Files

### `test_smarthome.py` - Core Application Tests
Tests fundamental application functionality without requiring database connection.

**Test Coverage:**
- ✅ Authentication (login, logout, session management)
- ✅ Password reset functionality
- ✅ Multi-home page accessibility
- ✅ Device management (buttons, temperature controls)
- ✅ Automation functionality
- ✅ Admin dashboard
- ✅ API endpoints
- ✅ CSRF protection
- ✅ Security headers
- ✅ Error handling (404, 429 rate limiting)
- ✅ Integration tests (complete user flows)

**Usage:**
```bash
# Run all tests
python test_smarthome.py

# Verbose output
python test_smarthome.py --verbose

# Fast mode (skip slow integration tests)
python test_smarthome.py --fast

# Quiet mode
python test_smarthome.py --quiet
```

### `test_database.py` - Database Integration Tests
Tests PostgreSQL database connectivity and multi-home functionality.

**Test Coverage:**
- ✅ Database connection
- ✅ Database schema verification
- ✅ Multi-home user operations
- ✅ User lookup (by username, email, alias)
- ✅ Home access verification
- ✅ Management logging
- ✅ Application login with database
- ✅ API operations with database backend

**Prerequisites:**
- PostgreSQL database running
- `DATABASE_MODE=true` in `.env`
- Database schema imported from `backups/db_schema_multihouse.sql`

**Usage:**
```bash
# Run database tests
python test_database.py

# Verbose output
python test_database.py --verbose

# Skip database schema checks
python test_database.py --skip-setup
```

## Quick Start

### 1. Set Up Environment

```bash
# Create virtual environment (if not already done)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Core Tests (No Database Required)

```bash
python test_smarthome.py
```

Expected output:
```
======================================================================
SmartHome Application - Test Suite
======================================================================
Mode: Complete
Verbosity: 2
======================================================================

test_login_page_loads (test_smarthome.AuthenticationTests) ... ok
test_login_success (test_smarthome.AuthenticationTests) ... ok
...
----------------------------------------------------------------------
Ran 45 tests in 12.345s

OK
======================================================================
Test Summary
======================================================================
Tests run: 45
Successes: 45
Failures: 0
Errors: 0
Skipped: 0
======================================================================
```

### 3. Run Database Tests (Requires PostgreSQL)

```bash
# Make sure PostgreSQL is running and configured
python test_database.py
```

Expected output:
```
======================================================================
SmartHome Database Integration Tests
======================================================================
Testing PostgreSQL connectivity and multi-home functionality
======================================================================

✅ Database connection successful

test_database_connection (test_database.DatabaseConnectionTests) ... ok
test_database_schema_exists (test_database.DatabaseConnectionTests) ... ok
...
----------------------------------------------------------------------
Ran 12 tests in 3.456s

OK
```

## Test Categories

### Authentication Tests
- Login page accessibility
- Successful login with valid credentials
- Failed login with invalid credentials
- Logout functionality
- Session persistence
- Password hashing verification
- Rate limiting on login

### Password Reset Tests
- Forgot password page accessibility
- Verification code sending
- Security (no user enumeration)
- Rate limiting on password reset

### Multi-Home Tests
- Home selection page
- Home creation page
- API home selection with authentication
- Home selection validation

### Device Management Tests
- Devices/lights page accessibility
- Temperature control page
- Button toggle API authentication
- Temperature set API authentication

### Automation Tests
- Automations page accessibility
- Automation creation authentication

### Admin Tests
- Admin dashboard authentication
- Admin role requirement
- Admin access control

### API Endpoint Tests
- Health check endpoint
- Ping endpoint
- Status endpoint authentication

### CSRF Protection Tests
- CSRF token presence in forms
- POST request validation

### Security Tests
- Security headers (X-Content-Type-Options, X-Frame-Options)
- Content Security Policy
- HTTPOnly session cookies

### Error Handling Tests
- 404 error page
- 429 rate limit error (JSON for API)

### Database Integration Tests
- Database connection verification
- Schema validation
- User lookup operations
- Multi-home operations
- Management logging

## Continuous Integration

### Running Tests in CI/CD

```yaml
# Example GitHub Actions workflow
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: smarthome_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run core tests
      run: |
        python test_smarthome.py
    
    - name: Set up database
      run: |
        psql -h localhost -U postgres -d smarthome_test -f backups/db_schema_multihouse.sql
      env:
        PGPASSWORD: postgres
    
    - name: Run database tests
      run: |
        python test_database.py
      env:
        DATABASE_MODE: true
        DB_HOST: localhost
        DB_USER: postgres
        DB_PASSWORD: postgres
        DB_NAME: smarthome_test
```

## Troubleshooting

### Tests Fail with "SECRET_KEY not set"

**Solution:** Tests automatically set a test SECRET_KEY. If this error occurs, check that the test file is being run directly:

```bash
python test_smarthome.py
```

### Database Tests Fail with Connection Error

**Solution:**
1. Check PostgreSQL is running:
   ```bash
   # Windows
   sc query postgresql-x64-15
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Verify database credentials in `.env`:
   ```
   DATABASE_MODE=true
   DB_HOST=localhost
   DB_USER=admin
   DB_PASSWORD=your_password
   DB_NAME=smarthome_multihouse
   ```

3. Import database schema:
   ```bash
   psql -U admin -d smarthome_multihouse -f backups/db_schema_multihouse.sql
   ```

### Rate Limiting Tests Fail

**Solution:** Rate limits persist across test runs. Wait 1 hour or clear rate limit cache:

```bash
# If using Redis for rate limiting
redis-cli FLUSHDB

# Otherwise, restart the Flask application
```

### CSRF Tests Fail

**Solution:** CSRF tests are enabled by default in test_smarthome.py. If Flask-WTF is not installed:

```bash
pip install Flask-WTF
```

## Test Configuration

Tests can be configured via environment variables:

```bash
# Use JSON fallback mode (no database)
export DATABASE_MODE=false
python test_smarthome.py

# Use database mode
export DATABASE_MODE=true
python test_database.py

# Set custom database credentials
export DB_HOST=custom_host
export DB_USER=custom_user
export DB_PASSWORD=custom_pass
export DB_NAME=custom_db
python test_database.py
```

## Coverage Reports

To generate code coverage reports:

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run -m pytest test_smarthome.py test_database.py

# Generate report
coverage report

# Generate HTML report
coverage html
# Open htmlcov/index.html in browser
```

## Writing New Tests

### Example Test Case

```python
import unittest
from test_smarthome import BaseTestCase

class MyNewTests(BaseTestCase):
    """Test my new feature"""
    
    def test_my_feature(self):
        """Test that my feature works"""
        self.login()
        response = self.client.get('/my-new-endpoint')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Expected Content', response.data)
```

### Best Practices

1. **Inherit from BaseTestCase** - Automatic setup/teardown
2. **Use descriptive test names** - `test_what_it_does_when_condition`
3. **Test one thing per test** - Focused tests are easier to debug
4. **Use assertions** - Clear expected vs actual values
5. **Clean up after tests** - Don't leave test data in database

## Automated Testing Schedule

Recommended testing schedule:

- **Before commit:** Run `python test_smarthome.py --fast`
- **Before push:** Run `python test_smarthome.py`
- **Before deploy:** Run both `test_smarthome.py` and `test_database.py`
- **After deploy:** Run smoke tests on production environment
- **Nightly:** Full test suite with coverage reports

## Support

For issues with tests:
1. Check this README for troubleshooting
2. Review test output for specific errors
3. Check application logs in `management_logs.json`
4. Verify database schema is up to date

---

**Last Updated:** 2025-01-05  
**Test Suite Version:** 1.0.0
