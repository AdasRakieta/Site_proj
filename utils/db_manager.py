import psycopg2
import psycopg2.extras
import os

# Database configuration from environment variables (no defaults for security)
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Validate required environment variables only when actually trying to connect
# This allows imports without having all env vars set (for non-DB modes)
def _validate_db_config():
    """Validate that all required database environment variables are set."""
    missing = []
    if not DB_HOST:
        missing.append('DB_HOST')
    if not DB_NAME:
        missing.append('DB_NAME')
    if not DB_USER:
        missing.append('DB_USER')
def get_db_connection():
    """Get a database connection. Validates configuration before connecting."""
    _validate_db_config()
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )   )


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def get_notification_settings(home_id=None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            if home_id:
                cur.execute("SELECT key, value FROM notification_settings WHERE home_id = %s", (home_id,))
            else:
                cur.execute("SELECT key, value FROM notification_settings")
            rows = cur.fetchall()
            return {row['key']: row['value'] for row in rows}
    finally:
        conn.close()


def set_notification_settings(settings, home_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for key, value in settings.items():
                cur.execute("""
                    INSERT INTO notification_settings (home_id, key, value)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (key, home_id) DO UPDATE SET value = EXCLUDED.value
                """, (home_id, key, psycopg2.extras.Json(value)))
        conn.commit()
    finally:
        conn.close()


def get_notification_recipients(home_id=None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            if home_id:
                cur.execute("SELECT id, email, user_id, enabled FROM notification_recipients WHERE home_id = %s", (home_id,))
            else:
                cur.execute("SELECT id, email, user_id, enabled FROM notification_recipients")
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def set_notification_recipients(recipients, home_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notification_recipients WHERE home_id = %s", (home_id,))
            for rec in recipients:
                cur.execute("""
                    INSERT INTO notification_recipients (home_id, email, user_id, enabled)
                    VALUES (%s, %s, %s, %s)
                """, (home_id, rec.get('email'), rec.get('user_id'), rec.get('enabled', True)))
        conn.commit()
    finally:
        conn.close()
