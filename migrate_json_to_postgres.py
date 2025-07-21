import json
import uuid
import psycopg2
from psycopg2.extras import execute_values

# Ścieżki do plików konfiguracyjnych
CONFIG_PATH = 'smart_home_config.json'
NOTIF_RECIPIENTS_PATH = 'notification_recipients.enc'  # jeśli chcesz, obsłuż dekodowanie
NOTIF_SETTINGS_PATH = 'notifications_settings.json'

# Dane do połączenia z bazą
DB_PARAMS = dict(
    dbname='postgres',  # lub inna nazwa bazy
    user='admin',    # uzupełnij
    password='Qwuizzy123',# uzupełnij
    host='localhost',   # lub inny host
    port=5432
)

def main():
    # 1. Połącz z bazą
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # 2. Stwórz dom dom_1
    home_id = str(uuid.uuid4())
    cur.execute("INSERT INTO homes (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING", (home_id, 'dom_1'))

    # 3. Wczytaj dane z JSON
    with open(CONFIG_PATH, encoding='utf-8') as f:
        config = json.load(f)

    # 4. Użytkownicy
    users = []
    for user_id, user in config.get('users', {}).items():
        users.append((user_id, home_id, user['name'], user['email'], user['password'], user.get('role', 'user'), user.get('profile_picture')))
    execute_values(cur, """
        INSERT INTO users (id, home_id, name, email, password_hash, role, profile_picture)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """, users)

    # 5. Pokoje
    room_name_to_id = {}
    for room in config.get('rooms', []):
        cur.execute("INSERT INTO rooms (home_id, name) VALUES (%s, %s) RETURNING id", (home_id, room))
        room_id = cur.fetchone()[0]
        room_name_to_id[room] = room_id

    # 6. Urządzenia (buttons + temperature_controls)
    devices = []
    for button in config.get('buttons', []):
        devices.append((str(uuid.uuid4()), home_id, button['name'], room_name_to_id.get(button['room']), 'button', button.get('state')))
    for temp in config.get('temperature_controls', []):
        devices.append((str(uuid.uuid4()), home_id, temp['name'], room_name_to_id.get(temp['room']), 'thermostat', None, temp.get('temperature')))
    for d in devices:
        if len(d) == 6:
            cur.execute("INSERT INTO devices (id, home_id, name, room_id, type, state) VALUES (%s, %s, %s, %s, %s, %s)", d)
        else:
            cur.execute("INSERT INTO devices (id, home_id, name, room_id, type, state, temperature) VALUES (%s, %s, %s, %s, %s, %s, %s)", d)

    # 7. Automatyzacje
    for automation in config.get('automations', []):
        cur.execute("INSERT INTO automations (home_id, name, trigger, actions, enabled) VALUES (%s, %s, %s, %s, %s)",
            (home_id, automation['name'], json.dumps(automation['trigger']), json.dumps(automation['actions']), automation.get('enabled', True)))

    # 8. Odbiorcy powiadomień (jeśli chcesz, obsłuż dekodowanie notification_recipients.enc)
    try:
        with open(NOTIF_RECIPIENTS_PATH, encoding='utf-8') as f:
            recipients = json.load(f)
        for rec in recipients:
            cur.execute("INSERT INTO notification_recipients (home_id, email, enabled) VALUES (%s, %s, %s)", (home_id, rec['email'], rec.get('enabled', True)))
    except Exception:
        pass

    # 9. Ustawienia powiadomień
    try:
        with open(NOTIF_SETTINGS_PATH, encoding='utf-8') as f:
            notif_settings = json.load(f)
        for k, v in notif_settings.items():
            cur.execute("INSERT INTO notification_settings (home_id, key, value) VALUES (%s, %s, %s)", (home_id, k, json.dumps(v)))
    except Exception:
        pass

    conn.commit()
    cur.close()
    conn.close()
    print('Migracja zakończona!')

if __name__ == '__main__':
    main()
