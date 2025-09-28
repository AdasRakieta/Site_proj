"""
Script to create new database for multi-home system
"""
import psycopg2
import sys
import os

def create_multihouse_database():
    try:
        # Connection parameters
        conn_params = {
            'host': '100.103.184.90',
            'port': '5432',
            'user': 'admin',
            'password': 'Qwuizzy123.',
            'database': 'postgres'  # Connect to default postgres database
        }
        
        print("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True  # Required for CREATE DATABASE
        
        cursor = conn.cursor()
        
        # Check if database already exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'smarthome_multihouse'")
        if cursor.fetchone():
            print("Database 'smarthome_multihouse' already exists!")
            return True
        
        # Create new database
        print("Creating database 'smarthome_multihouse'...")
        cursor.execute("""
            CREATE DATABASE smarthome_multihouse 
            WITH 
                OWNER = admin
                ENCODING = 'UTF8'
                TEMPLATE = template0
                CONNECTION LIMIT = -1
        """)
        
        print("✅ Database 'smarthome_multihouse' created successfully!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_multihouse_database()
    sys.exit(0 if success else 1)