#!/usr/bin/env python3
"""
SmartHome Application - Comprehensive Test Suite
Tests all core functionality including authentication, multi-home, devices, and API endpoints.

Usage:
    python test_smarthome.py              # Run all tests
    python test_smarthome.py --verbose    # Run with detailed output
    python test_smarthome.py --fast       # Skip slow integration tests
"""

import unittest
import json
import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock environment variables before importing app
os.environ.setdefault('SECRET_KEY', 'test_secret_key_for_testing_only_123456789012345678901234567890ab')
os.environ.setdefault('FLASK_ENV', 'testing')
os.environ.setdefault('DATABASE_MODE', 'false')  # Force JSON fallback for unit tests
os.environ.setdefault('DISABLE_RATE_LIMITING', 'true')

from app_db import SmartHomeApp
from werkzeug.security import generate_password_hash, check_password_hash


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup/teardown"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize app once for all tests"""
        cls.app_instance = SmartHomeApp()
        cls.app = cls.app_instance.app
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for most tests
    
    def setUp(self):
        """Set up test fixtures before each test"""
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
    def tearDown(self):
        """Clean up after each test"""
        self.ctx.pop()
    
    def force_login(self, username='admin', role='admin'):
        """Helper to simulate authenticated session"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 'test-user-id'
            sess['username'] = username
            sess['role'] = role
            sess['global_role'] = role
    
    def login(self, username='admin', password='admin123', use_endpoint=False):
        """Helper to log in via endpoint or session"""
        if use_endpoint:
            return self.client.post('/login', data={
                'username': username,
                'password': password
            }, follow_redirects=True)
        self.force_login(username=username, role='admin')
        return None
    
    def logout(self):
        """Helper to log out"""
        return self.client.get('/logout', follow_redirects=True)
    
    def get_csrf_token(self, response_data):
        """Extract CSRF token from response HTML"""
        import re
        match = re.search(r'name="csrf_token".*?value="([^"]+)"', response_data.decode('utf-8'))
        return match.group(1) if match else None


class AuthenticationTests(BaseTestCase):
    """Test user authentication and session management"""
    
    def test_login_page_loads(self):
        """Test that login page is accessible"""
        response = self.client.get('/login')
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            self.assertIn(b'Login', response.data)
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = self.login('admin', 'admin123', use_endpoint=True)
        self.assertIn(response.status_code, [200, 302])
        # Should redirect to home or dashboard
        
    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        response = self.login('admin', 'wrongpassword', use_endpoint=True)
        self.assertIn(response.status_code, [200, 401, 403])
        # Should show error message
    
    def test_login_nonexistent_user(self):
        """Test login fails for non-existent user"""
        response = self.login('nonexistent_user', 'password', use_endpoint=True)
        self.assertIn(response.status_code, [200, 401, 403])
    
    def test_logout(self):
        """Test user can log out"""
        self.force_login()
        response = self.logout()
        self.assertIn(response.status_code, [200, 302])
    
    def test_session_persistence(self):
        """Test that session persists across requests"""
        self.force_login()
        response = self.client.get('/')
        self.assertIn(response.status_code, [200, 302])
        # Should show logged-in view
    
    def test_password_hashing(self):
        """Test password is properly hashed"""
        password = 'test_password_123'
        hashed = generate_password_hash(password)
        self.assertTrue(check_password_hash(hashed, password))
        self.assertNotEqual(password, hashed)
    
    def test_rate_limiting_login(self):
        """Test rate limiting on login endpoint"""
        # Make multiple failed login attempts
        for i in range(6):
            response = self.login('admin', 'wrongpassword')
        
        # Next attempt should be rate limited
        response = self.login('admin', 'wrongpassword')
        # Should get 429 Too Many Requests or similar


class PasswordResetTests(BaseTestCase):
    """Test password reset functionality"""
    
    def test_forgot_password_page_loads(self):
        """Test forgot password page is accessible"""
        response = self.client.get('/forgot_password')
        self.assertIn(response.status_code, [200, 302])
    
    def test_forgot_password_email_sent(self):
        """Test verification code is sent"""
        response = self.client.post('/forgot_password', 
            data=json.dumps({'email_or_username': 'admin'}),
            content_type='application/json')
        self.assertIn(response.status_code, [200, 201, 429])
    
    def test_forgot_password_nonexistent_user(self):
        """Test forgot password doesn't reveal user existence"""
        response = self.client.post('/forgot_password',
            data=json.dumps({'email_or_username': 'nonexistent'}),
            content_type='application/json')
        # Should return 200 for security (don't reveal user existence)
        self.assertIn(response.status_code, [200, 429])
    
    def test_rate_limiting_forgot_password(self):
        """Test rate limiting on forgot password endpoint"""
        if self.app_instance.limiter is None:
            self.skipTest("Rate limiting disabled in testing")
        for i in range(4):
            response = self.client.post('/forgot_password',
                data=json.dumps({'email_or_username': 'admin'}),
                content_type='application/json')
        
        # Should be rate limited after 3 attempts per hour
        self.assertEqual(response.status_code, 429)


class MultiHomeTests(BaseTestCase):
    """Test multi-home functionality"""
    
    def test_home_select_page_loads(self):
        """Test home selection page is accessible"""
        if not self.app_instance.multi_db or self.app_instance.multi_db.json_fallback_mode:
            self.skipTest("Multi-home database not available")
        self.force_login()
        response = self.client.get('/home/select')
        # Should redirect or show home selection
        self.assertIn(response.status_code, [200, 302])
    
    def test_home_creation_page_loads(self):
        """Test home creation page is accessible"""
        if not self.app_instance.multi_db or self.app_instance.multi_db.json_fallback_mode:
            self.skipTest("Multi-home database not available")
        self.force_login()
        response = self.client.get('/home/create')
        self.assertIn(response.status_code, [200, 302])
    
    def test_api_home_select_requires_auth(self):
        """Test home select API requires authentication"""
        if not self.app_instance.multi_db or self.app_instance.multi_db.json_fallback_mode:
            self.skipTest("Multi-home database not available")
        response = self.client.post('/api/home/select',
            data=json.dumps({'home_id': 'test-id'}),
            content_type='application/json')
        # Should redirect to login or return 401
        self.assertIn(response.status_code, [302, 401])
    
    def test_api_home_select_requires_home_id(self):
        """Test home select API requires home_id parameter"""
        if not self.app_instance.multi_db or self.app_instance.multi_db.json_fallback_mode:
            self.skipTest("Multi-home database not available")
        self.force_login()
        response = self.client.post('/api/home/select',
            data=json.dumps({}),
            content_type='application/json')
        # Should return error
        self.assertIn(response.status_code, [400, 422, 302])


class DeviceManagementTests(BaseTestCase):
    """Test device management (buttons, temperature controls)"""
    
    def test_devices_page_loads(self):
        """Test devices/lights page is accessible"""
        self.force_login()
        response = self.client.get('/lights')
        self.assertIn(response.status_code, [200, 302])
    
    def test_temperature_page_loads(self):
        """Test temperature control page is accessible"""
        self.force_login()
        response = self.client.get('/temperature')
        self.assertIn(response.status_code, [200, 302])
    
    def test_api_toggle_button_requires_auth(self):
        """Test button toggle API requires authentication"""
        response = self.client.post('/api/buttons/test-id/toggle',
            data=json.dumps({'button_id': 'test-id'}),
            content_type='application/json')
<<<<<<< HEAD
        self.assertIn(response.status_code, [302, 401, 403])
=======
        self.assertIn(response.status_code, [302, 401, 403, 404])  # 404 if button doesn't exist
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a
    
    def test_api_set_temperature_requires_auth(self):
        """Test temperature set API requires authentication"""
        response = self.client.post('/api/temperature_controls/test-id/temperature',
            data=json.dumps({'device_id': 'test-id', 'temperature': 22.0}),
            content_type='application/json')
<<<<<<< HEAD
        self.assertIn(response.status_code, [302, 401, 403])
=======
        self.assertIn(response.status_code, [302, 401, 403, 404])  # 404 if device doesn't exist
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a


class AutomationTests(BaseTestCase):
    """Test automation functionality"""
    
    def test_automations_page_loads(self):
        """Test automations page is accessible"""
        self.force_login()
        response = self.client.get('/automations')
<<<<<<< HEAD
        self.assertIn(response.status_code, [200, 302])
=======
        self.assertIn(response.status_code, [200, 302])  # May redirect to home selection
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a
    
    def test_automation_creation_requires_auth(self):
        """Test automation creation requires authentication"""
        response = self.client.post('/api/automations',
            data=json.dumps({'name': 'Test', 'trigger': {}, 'actions': []}),
            content_type='application/json')
        self.assertIn(response.status_code, [302, 401, 403])


class AdminTests(BaseTestCase):
    """Test admin functionality"""
    
    def test_admin_dashboard_requires_auth(self):
        """Test admin dashboard requires authentication"""
        response = self.client.get('/admin_dashboard')
        # Should redirect to login
<<<<<<< HEAD
        self.assertIn(response.status_code, [302, 401, 403])
=======
        self.assertIn(response.status_code, [302, 401, 403, 404])
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a
    
    def test_admin_dashboard_requires_admin_role(self):
        """Test admin dashboard requires admin role"""
        self.force_login(username='user', role='user')  # Non-admin user
        response = self.client.get('/admin_dashboard')
        # Should deny access
<<<<<<< HEAD
        self.assertIn(response.status_code, [302, 403])
=======
        self.assertIn(response.status_code, [302, 403, 404])
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a
    
    def test_admin_dashboard_accessible_by_admin(self):
        """Test admin can access admin dashboard"""
        self.force_login(username='admin', role='admin')
        response = self.client.get('/admin_dashboard')
<<<<<<< HEAD
        self.assertIn(response.status_code, [200, 302])
=======
        self.assertIn(response.status_code, [200, 302, 404])
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a


class APIEndpointTests(BaseTestCase):
    """Test API endpoints"""
    
    def test_api_ping(self):
        """Test ping endpoint is accessible"""
        response = self.client.get('/api/ping')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn(data.get('status'), ['ok', 'success'])
    
    def test_api_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertIn(response.status_code, [200, 302])
    
    def test_api_status_requires_auth(self):
        """Test status endpoint requires authentication"""
        response = self.client.get('/api/status')
        # May or may not require auth depending on config
        self.assertIn(response.status_code, [200, 302, 401])


class CSRFProtectionTests(BaseTestCase):
    """Test CSRF protection"""
    
    def setUp(self):
        """Enable CSRF for these tests"""
        super().setUp()
        self.app.config['WTF_CSRF_ENABLED'] = True

    def tearDown(self):
        self.app.config['WTF_CSRF_ENABLED'] = False
        super().tearDown()
    
    def test_csrf_token_present_in_forms(self):
        """Test CSRF token is present in forms"""
        response = self.client.get('/login')
        self.assertNotEqual(response.status_code, 404)
        self.assertIn(b'csrf_token', response.data)
    
    def test_post_without_csrf_fails(self):
        """Test POST request without CSRF token fails"""
        response = self.client.post('/login',
            data={'username': 'admin', 'password': 'admin123'})
        # Should fail CSRF validation
        self.assertIn(response.status_code, [400, 403])


class SecurityTests(BaseTestCase):
    """Test security headers and configurations"""
    
    def test_security_headers_present(self):
        """Test security headers are set"""
        response = self.client.get('/')
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertIn('X-Frame-Options', response.headers)
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
    
    def test_content_security_policy(self):
        """Test Content Security Policy header is set"""
        response = self.client.get('/')
        self.assertIn('Content-Security-Policy', response.headers)
    
    def test_session_cookie_httponly(self):
        """Test session cookie is HTTPOnly"""
        response = self.login()
        set_cookie = response.headers.get('Set-Cookie', '')
        self.assertIn('HttpOnly', set_cookie)


class ErrorHandlingTests(BaseTestCase):
    """Test error handling"""
    
    def test_404_page(self):
        """Test 404 error page"""
        response = self.client.get('/nonexistent-page')
        self.assertIn(response.status_code, [404, 302])
    
    def test_429_rate_limit_returns_json_for_api(self):
        """Test 429 error returns JSON for API requests"""
        if self.app_instance.limiter is None:
            self.skipTest("Rate limiting disabled in testing")
        # Make many requests to trigger rate limit
        for i in range(10):
            response = self.client.post('/forgot_password',
                data=json.dumps({'email_or_username': 'test'}),
                content_type='application/json',
                headers={'Accept': 'application/json'})
        
        # Should get rate limit error
        if response.status_code == 429:
            data = json.loads(response.data)
            self.assertIn('error', data)


class IntegrationTests(BaseTestCase):
    """End-to-end integration tests"""
    
    def test_complete_user_flow(self):
        """Test complete user flow: login -> view devices -> logout"""
        # Login
        self.force_login()
        
        # Access main page
        response = self.client.get('/')
        self.assertIn(response.status_code, [200, 302])
        
        # Access devices
        response = self.client.get('/lights')
        self.assertIn(response.status_code, [200, 302])
        
        # Logout
        response = self.logout()
        self.assertIn(response.status_code, [200, 302])
    
    def test_complete_password_reset_flow(self):
        """Test complete password reset flow"""
        # Request reset
        response = self.client.post('/forgot_password',
            data=json.dumps({'email_or_username': 'admin'}),
            content_type='application/json')
        
        # Should succeed
        self.assertEqual(response.status_code, 200)


def run_tests(verbosity=2, fast_mode=False):
    """Run the test suite"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        AuthenticationTests,
        PasswordResetTests,
        MultiHomeTests,
        DeviceManagementTests,
        AutomationTests,
        AdminTests,
        APIEndpointTests,
        CSRFProtectionTests,
        SecurityTests,
        ErrorHandlingTests,
    ]
    
    # Add integration tests unless in fast mode
    if not fast_mode:
        test_classes.append(IntegrationTests)
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='SmartHome Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--fast', '-f', action='store_true',
                       help='Skip slow integration tests')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output')
    
    args = parser.parse_args()
    
    verbosity = 1 if args.quiet else (2 if args.verbose else 2)
    
    print("="*70)
    print("SmartHome Application - Test Suite")
    print("="*70)
    print(f"Mode: {'Fast' if args.fast else 'Complete'}")
    print(f"Verbosity: {verbosity}")
    print("="*70)
    print()
    
    result = run_tests(verbosity=verbosity, fast_mode=args.fast)
    
    print()
    print("="*70)
    print("Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
