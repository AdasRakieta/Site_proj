"""DB Healthcheck Script
Uruchom aby zweryfikować komunikację z bazą PostgreSQL oraz podstawowe operacje.
"""
from __future__ import annotations
import os, sys, json, time
from datetime import datetime

import psycopg2
import psycopg2.extras

DB_HOST = os.getenv('DB_HOST', '100.103.184.90')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'admin')  # uwaga: w managerze używany klucz dbname
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Qwuizzy123.')

RESULT = {"timestamp": datetime.utcnow().isoformat() + 'Z'}

def connect():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, connect_timeout=5)

def main():
    try:
        start = time.time()
        with connect() as conn:
            RESULT['connection'] = {
                'status': 'ok',
                'latency_ms': round((time.time() - start)*1000, 1),
                'host': DB_HOST,
                'db': DB_NAME
            }
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Version
                cur.execute('SELECT version();')
                RESULT['version'] = cur.fetchone()['version']
                # Present tables
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema='public' AND table_name IN (
                        'rooms','devices','automations','system_settings','room_temperature_states','users')
                    ORDER BY table_name;""")
                RESULT['tables_present'] = [r['table_name'] for r in cur.fetchall()]

                # Counts
                counts = {}
                for t in RESULT['tables_present']:
                    cur.execute(f'SELECT COUNT(*) AS c FROM {t};')
                    counts[t] = cur.fetchone()['c']
                RESULT['row_counts'] = counts

                # Sample device
                sample = None
                if 'devices' in RESULT['tables_present'] and counts.get('devices',0)>0:
                    cur.execute("SELECT id, name, state, temperature, device_type FROM devices ORDER BY updated_at DESC NULLS LAST LIMIT 1;")
                    sample = cur.fetchone()
                RESULT['sample_device'] = sample

                # Test update in rollback (safety)
                if sample:
                    try:
                        cur.execute('BEGIN;')
                        cur.execute("UPDATE devices SET state = NOT COALESCE(state,false), updated_at = NOW() WHERE id = %s RETURNING state;", (sample['id'],))
                        new_state = cur.fetchone()['state']
                        cur.execute('ROLLBACK;')
                        RESULT['update_simulation'] = {'device_id': sample['id'], 'toggled_state_preview': new_state, 'rolled_back': True}
                    except Exception as e:
                        RESULT['update_simulation'] = {'error': str(e)}

                # Security state
                if 'system_settings' in RESULT['tables_present']:
                    cur.execute("SELECT setting_value FROM system_settings WHERE setting_key='security_state';")
                    row = cur.fetchone()
                    if row:
                        raw = row['setting_value']
                        # setting_value likely jsonb already parsed by psycopg2; ensure bool
                        security_bool = raw if isinstance(raw,bool) else str(raw).lower() in ['true','1']
                        RESULT['security_state_db'] = 'Załączony' if security_bool else 'Wyłączony'
                    else:
                        RESULT['security_state_db'] = 'missing'

    except Exception as e:
        RESULT['connection'] = {'status': 'error', 'error': str(e)}

    print(json.dumps(RESULT, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
