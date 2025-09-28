#!/usr/bin/env python3
"""
Test pokoi multi-home
"""

from utils.multi_home_db_manager import MultiHomeDBManager
from utils.smart_home_db_manager import SmartHomeDatabaseManager

print('=== Test pokoi multi-home ===')

# Dane testowe
user_id = '727a5147-14e6-405d-921b-931fbc0397ed'
admin_home_id = '40a67bc7-6b5d-4a88-bce1-f7ef6d06432c'
main_home_id = 'eb7490c1-1028-46c1-bd7c-1900980a964e'

try:
    multi_db = MultiHomeDBManager(
        host="100.103.184.90",
        port=5432,
        user="admin", 
        password="Qwuizzy123.",
        database="smarthome_multihouse"
    )
    smart_db = SmartHomeDatabaseManager()

    print('\n1. MAIN DATABASE (wszystkie pokoje):')
    main_rooms = smart_db.get_rooms()
    print(f'   {main_rooms}')

    print('\n2. ADMIN HOME (po migracji):')
    admin_rooms = multi_db.get_home_rooms(admin_home_id, user_id)
    admin_room_names = [room['name'] for room in admin_rooms]
    print(f'   {admin_room_names}')

    print('\n3. MAIN HOME (powinien być pusty):')
    main_home_rooms = multi_db.get_home_rooms(main_home_id, user_id)
    main_home_room_names = [room['name'] for room in main_home_rooms]
    print(f'   {main_home_room_names}')

    print('\n4. AKTUALNY DOM UŻYTKOWNIKA:')
    current_home = multi_db.get_user_current_home(user_id)
    print(f'   {current_home}')
    
    print('\n5. SYMULACJA get_current_home_rooms():')
    # Symulujemy funkcję z routes.py
    def get_current_home_rooms_test(user_id, current_home_id=None):
        if not current_home_id:
            current_home_id = multi_db.get_user_current_home(user_id)
        
        if current_home_id:
            rooms_data = multi_db.get_home_rooms(current_home_id, user_id)
            return [room['name'] for room in rooms_data]
        else:
            return smart_db.get_rooms()
    
    # Test z aktualnym domem
    result = get_current_home_rooms_test(user_id)
    print(f'   Wynik dla aktualnego domu: {result}')
    
    # Test z Admin Home
    result_admin = get_current_home_rooms_test(user_id, admin_home_id)
    print(f'   Wynik dla Admin Home: {result_admin}')
    
    # Test z Main Home  
    result_main = get_current_home_rooms_test(user_id, main_home_id)
    print(f'   Wynik dla Main Home: {result_main}')

    # multi_db.close()  # Nie ma takiej metody
    
except Exception as e:
    print(f'Błąd: {e}')
    import traceback
    traceback.print_exc()