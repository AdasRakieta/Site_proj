import psycopg2
import psycopg2.extras
from utils.db_config import get_db_config_from_env, validate_db_config_or_raise


def get_db_connection():
    """Get a database connection. Validates configuration before connecting."""
    # Get and validate configuration
    config = get_db_config_from_env()
    validate_db_config_or_raise(config)
    
    # Create connection
    return psycopg2.connect(
        host=config['host'],
        port=config['port'],
        dbname=config['dbname'],
        user=config['user'],
        password=config['password']
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
