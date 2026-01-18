from utils.json_backup_manager import JSONBackupManager
from utils.multi_home_db_manager import MultiHomeDBManager
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime, timezone, timedelta

json_backup = JSONBackupManager()
db = MultiHomeDBManager()
db.json_fallback_mode = True
db.json_backup = json_backup

# Create a user
test_user_id, home_id = db.create_user(
    username='debuginvite',
    email='debuginvite@example.com',
    password_hash=generate_password_hash('password123'),
    role='user',
    create_default_home=False
)

print(f'Created user: {test_user_id}')

# Get the config
config = json_backup.get_config()
users_map = config.get('users', {})

# Create the _find_user function like in accept_invitation
def _find_user(uid):
    if isinstance(users_map, dict):
        # Don't try to get by uid directly - users are keyed by username
        # Scan all values to find by ID
        for user in users_map.values():
            if str(user.get('id')) == str(uid):
                return user
    if isinstance(users_map, list):
        return next((u for u in users_map if str(u.get('id')) == str(uid)), None)
    return None

# Test the function
found_user = _find_user(test_user_id)
print(f'Found user: {found_user}')
if found_user:
    print(f'User email: {found_user.get("email")}')
else:
    print('User NOT found')
