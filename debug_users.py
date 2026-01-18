from utils.json_backup_manager import JSONBackupManager
from utils.multi_home_db_manager import MultiHomeDBManager
from werkzeug.security import generate_password_hash
import json

json_backup = JSONBackupManager()
db = MultiHomeDBManager()
db.json_fallback_mode = True
db.json_backup = json_backup

# Create a user
user_id, home_id = db.create_user(
    username='debugtest',
    email='debugtest@example.com',
    password_hash=generate_password_hash('password123'),
    role='user',
    create_default_home=False
)

# Check the config
config = json_backup.get_config()
users = config.get('users', {})
print('Users type:', type(users))
print('Users keys:', list(users.keys()) if isinstance(users, dict) else 'N/A')
print('User IDs in users:', [u.get('id') for u in users.values()] if isinstance(users, dict) else 'N/A')
print('Looking for user_id:', user_id)

# Try to find the user
for username, user_data in users.items():
    print(f'User {username}: id={user_data.get("id")}')
    if str(user_data.get('id')) == str(user_id):
        print(f'  --> FOUND!')
