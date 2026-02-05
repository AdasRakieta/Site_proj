#!/usr/bin/env python3
"""
SmartHome Database Integration Tests
Tests database connectivity and multi-home functionality.

Run these tests only when PostgreSQL database is available.

Usage:
    python test_database.py              # Run all database tests
    python test_database.py --skip-setup # Skip database schema check
"""

import unittest
import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment for database mode
os.environ['SECRET_KEY'] = 'test_secret_key_for_testing_only_123456789012345678901234567890ab'
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_MODE'] = 'true'

try:
    from app_db import SmartHomeApp
    from utils.multi_home_db_manager import MultiHomeDBManager
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure PostgreSQL is configured and DATABASE_MODE=true in .env")
    sys.exit(1)


class DatabaseConnectionTests(unittest.TestCase):
    """Test database connectivity"""
    
    @classmethod
    def setUpClass(cls):
        """Set up database connection once for all tests"""
        try:
            cls.db_manager = MultiHomeDBManager()
            cls.connection_ok = cls.db_manager.test_connection()
        except Exception as e:
            print(f"Database connection failed: {e}")
            cls.connection_ok = False
    
<<<<<<< HEAD
=======
    @classmethod
    def tearDownClass(cls):
        """Clean up database connection"""
        if hasattr(cls, 'db_manager') and hasattr(cls.db_manager, '_connection'):
            try:
                if cls.db_manager._connection:
                    cls.db_manager._connection.close()
            except Exception:
                pass
    
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a
    def test_database_connection(self):
        """Test database connection is successful"""
        self.assertTrue(self.connection_ok, "Database connection failed")
    
    def test_database_schema_exists(self):
        """Test required database tables exist"""
        if not self.connection_ok:
            self.skipTest("Database not connected")
        
        required_tables = [
            'users', 'homes', 'user_homes', 'rooms', 'devices',
            'automations', 'management_logs'
        ]
        
        with self.db_manager.get_cursor() as cursor:
            for table in required_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table,))
                exists = cursor.fetchone()[0]
                self.assertTrue(exists, f"Table '{table}' does not exist")


class MultiHomeDatabaseTests(unittest.TestCase):
    """Test multi-home database operations"""
    
    @classmethod
    def setUpClass(cls):
        """Set up database connection"""
        try:
            cls.db_manager = MultiHomeDBManager()
            if not cls.db_manager.test_connection():
                raise Exception("Database connection failed")
        except Exception as e:
            print(f"Database setup failed: {e}")
            raise
    
<<<<<<< HEAD
=======
    @classmethod
    def tearDownClass(cls):
        """Clean up database connection"""
        if hasattr(cls, 'db_manager') and hasattr(cls.db_manager, '_connection'):
            try:
                if cls.db_manager._connection:
                    cls.db_manager._connection.close()
            except Exception:
                pass
    
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a
    def test_find_user_by_username(self):
        """Test finding user by username"""
        # Try to find sysadmin user
        user = self.db_manager.find_user_by_email_or_username('sysadmin')
        self.assertIsNotNone(user, "sysadmin user not found")
        self.assertEqual(user['name'], 'sysadmin')
    
    def test_find_user_by_email(self):
        """Test finding user by email"""
        user = self.db_manager.find_user_by_email_or_username('szymon.przybysz2003@gmail.com')
        self.assertIsNotNone(user, "User not found by email")
    
    def test_sys_admin_alias(self):
        """Test sys-admin alias works"""
        user = self.db_manager.find_user_by_email_or_username('sys-admin')
        self.assertIsNotNone(user, "sys-admin alias not working")
        self.assertEqual(user['name'], 'sysadmin')
    
    def test_get_user_homes(self):
        """Test getting user's homes"""
        user = self.db_manager.find_user_by_email_or_username('sysadmin')
        if user:
            homes = self.db_manager.get_user_homes(user['id'])
            self.assertIsInstance(homes, list)
    
    def test_user_has_home_access(self):
        """Test checking user's home access"""
        user = self.db_manager.find_user_by_email_or_username('sysadmin')
        if user:
            homes = self.db_manager.get_user_homes(user['id'])
            if homes:
                has_access = self.db_manager.user_has_home_access(user['id'], homes[0]['id'])
                self.assertTrue(has_access)


class MultiHomeApplicationTests(unittest.TestCase):
    """Test application functionality with database"""
    
    @classmethod
    def setUpClass(cls):
        """Set up application"""
        try:
            cls.app_instance = SmartHomeApp()
            cls.app = cls.app_instance.app
            cls.app.config['TESTING'] = True
            cls.app.config['WTF_CSRF_ENABLED'] = False
            cls.client = cls.app.test_client()
        except Exception as e:
            print(f"Application setup failed: {e}")
            raise
    
    def test_login_with_database(self):
        """Test login with database backend"""
        response = self.client.post('/login', data={
            'username': 'sysadmin',
            'password': 'Qwuizzy123.'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_login_with_alias(self):
        """Test login with sys-admin alias"""
        response = self.client.post('/login', data={
            'username': 'sys-admin',
            'password': 'Qwuizzy123.'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_home_select_after_login(self):
        """Test accessing home select page after login"""
        # Login first
        self.client.post('/login', data={
            'username': 'sysadmin',
            'password': 'Qwuizzy123.'
        })
        
        # Access home select
        response = self.client.get('/home/select')
        self.assertIn(response.status_code, [200, 302])
    
    def test_api_home_select_with_csrf(self):
        """Test home select API with CSRF token"""
        # Login first
        self.client.post('/login', data={
            'username': 'sysadmin',
            'password': 'Qwuizzy123.'
        })
        
        # Get user's homes
        db_manager = MultiHomeDBManager()
        user = db_manager.find_user_by_email_or_username('sysadmin')
        if user:
            homes = db_manager.get_user_homes(user['id'])
            if homes:
                # Try to select home
                response = self.client.post('/api/home/select',
                    data=json.dumps({'home_id': homes[0]['id']}),
                    content_type='application/json')
                
                # Should succeed or fail with reasonable error
                self.assertIn(response.status_code, [200, 400, 401])
    
    def test_password_reset_with_database(self):
        """Test password reset flow with database"""
        response = self.client.post('/forgot_password',
            data=json.dumps({'email_or_username': 'sysadmin'}),
            content_type='application/json')
        
<<<<<<< HEAD
        # Should not fail catastrophically
        self.assertIn(response.status_code, [200, 429])
=======
        # Should not fail catastrophically (500 is acceptable if email not configured)
        self.assertIn(response.status_code, [200, 429, 500])
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a


class ManagementLogTests(unittest.TestCase):
    """Test management logging functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up database connection"""
        cls.db_manager = MultiHomeDBManager()
    
<<<<<<< HEAD
=======
    @classmethod
    def tearDownClass(cls):
        """Clean up database connection"""
        if hasattr(cls.db_manager, '_connection') and cls.db_manager._connection:
            try:
                cls.db_manager._connection.close()
            except Exception:
                pass
    
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a
    def test_add_management_log_with_home(self):
        """Test adding management log with home_id"""
        user = self.db_manager.find_user_by_email_or_username('sysadmin')
        if user:
            homes = self.db_manager.get_user_homes(user['id'])
            if homes:
                try:
                    self.db_manager.add_home_management_log(
                        home_id=homes[0]['id'],
                        level='info',
                        message='Test log entry',
                        event_type='test',
                        user_id=user['id'],
                        username='sysadmin',
                        ip_address='127.0.0.1',
                        details={'test': 'data'}
                    )
                    # Should not raise exception
                    self.assertTrue(True)
                except Exception as e:
                    self.fail(f"Logging failed: {e}")
    
    def test_get_home_management_logs(self):
        """Test retrieving management logs"""
        user = self.db_manager.find_user_by_email_or_username('sysadmin')
        if user:
            homes = self.db_manager.get_user_homes(user['id'])
            if homes:
                logs = self.db_manager.get_home_management_logs(
                    home_id=homes[0]['id'],
<<<<<<< HEAD
=======
                    admin_user_id=user['id'],
>>>>>>> 584e16bc4200d64a2952fdaa6f7778f695b79d3a
                    limit=10
                )
                self.assertIsInstance(logs, list)


def run_database_tests(verbosity=2):
    """Run database test suite"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        DatabaseConnectionTests,
        MultiHomeDatabaseTests,
        MultiHomeApplicationTests,
        ManagementLogTests,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='SmartHome Database Tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--skip-setup', action='store_true',
                       help='Skip database schema checks')
    
    args = parser.parse_args()
    
    verbosity = 2 if args.verbose else 1
    
    print("="*70)
    print("SmartHome Database Integration Tests")
    print("="*70)
    print("Testing PostgreSQL connectivity and multi-home functionality")
    print("="*70)
    print()
    
    # Check database is available
    try:
        db = MultiHomeDBManager()
        if not db.test_connection():
            print("❌ Database connection failed!")
            print("Make sure PostgreSQL is running and DATABASE_MODE=true in .env")
            sys.exit(1)
        print("✅ Database connection successful")
        print()
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        sys.exit(1)
    
    result = run_database_tests(verbosity=verbosity)
    
    print()
    print("="*70)
    print("Database Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    sys.exit(0 if result.wasSuccessful() else 1)
