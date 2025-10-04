import psycopg2

conn = psycopg2.connect('dbname=smarthome_multihouse user=postgres password=Przemozeq1')
cur = conn.cursor()
cur.execute('''
    SELECT id, home_id, timestamp, level, message, event_type 
    FROM management_logs 
    ORDER BY timestamp DESC 
    LIMIT 10
''')

rows = cur.fetchall()
print('\n📊 Najnowsze 10 logów z bazy danych:\n')
print(f'{"ID":<10} {"HOME_ID":<38} {"TIMESTAMP":<28} {"LEVEL":<8} {"EVENT_TYPE":<25} {"MESSAGE"}')
print('-' * 150)

for row in rows:
    log_id = str(row[0])[:8] + '...'
    home_id = row[1] if row[1] else '❌ NULL'
    timestamp = str(row[2])
    level = row[3]
    message = row[4][:50] + '...' if len(row[4]) > 50 else row[4]
    event_type = row[5]
    print(f'{log_id:<10} {home_id:<38} {timestamp:<28} {level:<8} {event_type:<25} {message}')

conn.close()

print('\n✅ Jeśli home_id = NULL, logi NIE będą wyświetlane w dashboard!')
print('✅ Jeśli home_id = 40a67bc7-6b5d-4a88-bce1-f7ef6d06432c (Admin Home), logi będą widoczne!')
