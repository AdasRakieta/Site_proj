import json
import uuid

# Skrypt do migracji smart_home_config.json - dodaje unikalne id do każdego buttona i temperature_control
with open('smart_home_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

changed = False

def ensure_id(devices):
    global changed
    for device in devices:
        if 'id' not in device:
            device['id'] = str(uuid.uuid4())
            changed = True

ensure_id(config.get('buttons', []))
ensure_id(config.get('temperature_controls', []))

if changed:
    with open('smart_home_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print('Dodano brakujące id do urządzeń w smart_home_config.json')
else:
    print('Wszystkie urządzenia już mają id')
