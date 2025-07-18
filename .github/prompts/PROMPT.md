# Smart Home Flask System - AI Assistant Prompt

## Projekt Overview
Jesteś ekspertem w systemie Smart Home opartym na Flask, który obejmuje zarządzanie urządzeniami IoT, automatyzacjami, użytkownikami i powiadomieniami w czasie rzeczywistym.

## Kluczowe komponenty architektury

### 1. **Struktura główna**
- **`app.py`**: Punkt wejścia, konfiguracja Flask, CSRF, autentykacja, background tasks
- **`routes.py`**: Główna logika aplikacji z trzema managerami:
  - `RoutesManager`: Trasy HTML i podstawowe endpointy
  - `APIManager`: REST API dla CRUD operacji
  - `SocketManager`: Obsługa WebSocket/SocketIO w czasie rzeczywistym
- **`configure.py`**: `SmartHomeSystem` klasa - singleton zarządzający stanem systemu
- **`mail_manager.py`**: System powiadomień email i alertów bezpieczeństwa

### 2. **Wzorce architektoniczne**
- **Manager Pattern**: Zamiast Flask Blueprints, używamy klas Manager z metodą `register_routes()`
- **Singleton State**: `SmartHomeSystem` jako centralne repozytorium stanu
- **Session-based Auth**: Autentykacja przez Flask session z dekoratorami `@login_required`, `@admin_required`
- **Real-time Sync**: SocketIO events dla synchronizacji stanu (`update_buttons`, `update_rooms`, etc.)

### 3. **Struktura danych**
```python
# Użytkownicy - klucze UUID, login w polu 'name'
users = {
    "uuid-string": {
        "name": "admin",  # login
        "password": "hashed_password",
        "role": "admin|user",
        "email": "...",
        "profile_picture": "URL"
    }
}

# Pokoje, przyciski, kontrolery temperatury
rooms = ["Salon", "Kuchnia", ...]
buttons = [{"id": "uuid", "name": "Światło", "room": "Salon", "state": bool}]
temperature_controls = [{"id": "uuid", "name": "Termostat", "room": "Salon", "temperature": int}]

# Automatyzacje
automations = [{
    "name": "Wieczorne światła",
    "enabled": bool,
    "trigger": {"type": "time|device|sensor", "time": "20:00", "days": ["mon", "tue"]},
    "actions": [{"type": "device", "device": "Salon_Światło", "state": "on"}]
}]
```

## Konwencje specyficzne dla projektu

### 4. **Identyfikatory i klucze**
- **Zawsze używaj `user_id` (UUID)** do wyszukiwania użytkowników, nie `username`
- **Device identifiers**: Format `{room}_{button_name}` dla przycisków
- **UUID dla nowych elementów**: `str(uuid.uuid4())` dla buttons/controls

### 5. **Autoryzacja i bezpieczeństwo**
- **CSRF Protection**: Zaimplementowany custom w `is_trusted_host()` - dodawaj nowe IP/sieci tutaj
- **Role-based access**: `session['role']` i dekoratory `@admin_required`
- **Trusted hosts**: Zaktualizuj `is_trusted_host()` dla nowych podsieci (np. 172.17.240.*)

### 6. **Real-time komunikacja**
```python
# Kluczowe SocketIO events
socketio.emit('update_rooms', rooms)
socketio.emit('update_buttons', buttons)
socketio.emit('update_temperature_controls', controls)
socketio.emit('sync_button_states', {f"{room}_{name}": state})
socketio.emit('update_automations', automations)
```

### 7. **API Patterns**
- **GET**: Zwraca JSON z danymi (`smart_home.buttons`, `smart_home.rooms`)
- **POST**: Tworzy nowy element, emituje SocketIO update, save_config()
- **PUT**: Aktualizuje element, emituje update
- **DELETE**: Usuwa element, emituje update

## Typowe workflow

### 8. **Dodawanie nowego API endpoint**
```python
# W APIManager.register_routes()
@self.app.route('/api/my-endpoint', methods=['GET', 'POST'])
@self.auth_manager.login_required
def my_endpoint():
    if request.method == 'GET':
        return jsonify(self.smart_home.my_data)
    elif request.method == 'POST':
        # Walidacja danych
        new_item = request.json
        if 'id' not in new_item:
            new_item['id'] = str(uuid.uuid4())
        
        # Dodaj do stanu
        self.smart_home.my_data.append(new_item)
        
        # Emituj update
        self.socketio.emit('update_my_data', self.smart_home.my_data)
        
        # Zapisz konfigurację
        self.smart_home.save_config()
        
        return jsonify({"status": "success", "id": new_item['id']})
```

### 9. **Dodawanie nowego SocketIO handler**
```python
# W SocketManager.register_handlers()
@self.socketio.on('my_event')
def handle_my_event(data):
    if 'username' not in session:
        return
    
    # Przetwórz dane
    result = process_data(data)
    
    # Emituj odpowiedź
    self.socketio.emit('my_response', result)
    
    # Zapisz stan jeśli potrzeba
    self.smart_home.save_config()
```

### 10. **Automatyzacje i triggery**
- **Time triggers**: `{"type": "time", "time": "HH:MM", "days": ["mon", "tue"]}`
- **Device triggers**: `{"type": "device", "device": "Room_Device", "state": "on|off|toggle"}`
- **Sensor triggers**: `{"type": "sensor", "sensor": "sensor_name", "condition": "above|below", "value": float}`

### 11. **Debugowanie i logi**
- **Background tasks**: `execute_automations()` i `periodic_save()` w background
- **CSRF debugging**: Logi w `csrf_protect()` z IP i tokenami
- **SocketIO debugging**: Logi połączeń w `handle_connect()`

## Najczęstsze operacje

### 12. **CRUD dla rooms/buttons/controls**
```python
# GET: Zwróć listę
return jsonify(smart_home.buttons)

# POST: Utwórz nowy (admin only)
if session.get('role') != 'admin':
    return jsonify({"error": "Brak uprawnień"}), 403

# PUT/DELETE: Znajdź po ID
idx = next((i for i, item in enumerate(items) if str(item.get('id')) == str(id)), None)
if idx is None:
    return jsonify({'error': 'Not found'}), 404
```

### 13. **Email notifications**
```python
# Użyj mail_manager do alertów
mail_manager.send_security_alert('failed_login', {
    'username': 'user',
    'ip_address': '127.0.0.1',
    'attempt_count': 3
})
```

### 14. **Config persistence**
- **Auto-save**: Okresowe zapisywanie w `periodic_save()`
- **Manual save**: `smart_home.save_config()` po każdej zmianie stanu
- **Config files**: `smart_home_config.json`, `notifications_settings.json`

## Pliki kluczowe dla referencji
- **Routing logic**: `routes.py` - wszystkie HTTP i SocketIO routes
- **State management**: `configure.py` - SmartHomeSystem
- **Auth decorators**: `app.py` - AuthManager
- **Frontend assets**: `static/js/app.js` - SmartHomeApp class
- **Email logic**: `mail_manager.py` - MailManager

## Zasady development
1. **Zawsze używaj UUID** dla user_id, button_id, control_id
2. **Emituj SocketIO events** po każdej zmianie stanu
3. **Sprawdź role** dla operacji admin (`session['role']`)
4. **Zapisuj config** po modyfikacjach (`save_config()`)
5. **Waliduj dane** w API endpoints
6. **Używaj managerów** - nie dodawaj routes bezpośrednio do app.py

Kiedy pracujesz z tym systemem, pamiętaj o real-time nature aplikacji - każda zmiana stanu powinna być propagowana przez SocketIO do wszystkich podłączonych klientów.
