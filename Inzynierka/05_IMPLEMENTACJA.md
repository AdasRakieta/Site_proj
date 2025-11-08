# Rozdział 5: Implementacja funkcjonalności

## 5.1. Zarządzanie użytkownikami

### 5.1.1. Rejestracja i logowanie

**Proces rejestracji:**

```python
# app/routes.py - RoutesManager
@self.app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 1. Walidacja danych wejściowych
        if not username or len(username) < 3:
            flash("Username must be at least 3 characters")
            return redirect(url_for('register'))
        
        if not email or '@' not in email:
            flash("Valid email required")
            return redirect(url_for('register'))
        
        if not password or len(password) < 8:
            flash("Password must be at least 8 characters")
            return redirect(url_for('register'))
        
        # 2. Sprawdzenie czy użytkownik już istnieje
        if self.smart_home.get_user_by_name(username):
            flash("Username already exists")
            return redirect(url_for('register'))
        
        if self.smart_home.get_user_by_email(email):
            flash("Email already registered")
            return redirect(url_for('register'))
        
        # 3. Haszowanie hasła (bcrypt)
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt(rounds=12)
        )
        
        # 4. Utworzenie użytkownika w bazie
        user_id = str(uuid.uuid4())
        user = {
            'id': user_id,
            'name': username,
            'email': email,
            'password_hash': password_hash.decode('utf-8'),
            'role': 'user',
            'created_at': datetime.now(timezone.utc)
        }
        
        success = self.smart_home.add_user(user)
        if not success:
            flash("Registration failed")
            return redirect(url_for('register'))
        
        # 5. Wysłanie email weryfikacyjnego
        verification_token = generate_verification_token(user_id)
        send_verification_email(email, verification_token)
        
        # 6. Automatyczne utworzenie pierwszego domu
        default_home_id = create_default_home(user_id, username)
        
        flash("Registration successful! Please verify your email.")
        return redirect(url_for('login'))
```

**Proces logowania:**

```python
@self.app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 1. Pobranie użytkownika z bazy
        user = self.smart_home.get_user_by_name(username)
        if not user:
            # Prevent username enumeration
            time.sleep(random.uniform(0.1, 0.3))
            flash("Invalid credentials")
            return redirect(url_for('login'))
        
        # 2. Weryfikacja hasła
        password_match = bcrypt.checkpw(
            password.encode('utf-8'),
            user['password_hash'].encode('utf-8')
        )
        
        if not password_match:
            # Log failed attempt
            log_failed_login(username, request.remote_addr)
            
            # Check for brute force
            attempts = get_failed_attempts(username)
            if attempts >= 5:
                send_security_alert(user['email'], 'multiple_failed_logins')
            
            flash("Invalid credentials")
            return redirect(url_for('login'))
        
        # 3. Utworzenie sesji
        session['user_id'] = user['id']
        session['username'] = user['name']
        session['role'] = user['role']
        session.permanent = True  # 24h timeout
        
        # 4. Ustawienie domyślnego domu
        homes = multi_db.get_user_homes(user['id'])
        if homes:
            # Get last selected home or first home
            last_home = multi_db.get_user_last_home(user['id'])
            current_home = last_home or homes[0]['id']
            session['current_home_id'] = current_home
        
        # 5. Log successful login
        log_management_event(
            'user_login',
            user_id=user['id'],
            ip_address=request.remote_addr
        )
        
        # 6. Redirect
        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('index'))
```

### 5.1.2. Role i uprawnienia (admin, user, sys-admin)

**Hierarchia ról:**

```
System Administrator (sys-admin)
  │
  ├─► Home Owner (owner)
  │     │
  │     └─► Home Administrator (admin)
  │           │
  │           └─► Home User (user)
  │
  └─► Global access to all homes (for maintenance)
```

**Macierz uprawnień:**

| Akcja | sys-admin | owner | admin | user |
|-------|-----------|-------|-------|------|
| Widok urządzeń | ✅ | ✅ | ✅ | ✅ |
| Sterowanie urządzeniami | ✅ | ✅ | ✅ | ✅ |
| Tworzenie automatyzacji | ✅ | ✅ | ✅ | ❌ |
| Dodawanie urządzeń | ✅ | ✅ | ✅ | ❌ |
| Usuwanie urządzeń | ✅ | ✅ | ✅ | ❌ |
| Zapraszanie użytkowników | ✅ | ✅ | ✅ | ❌ |
| Usuwanie użytkowników | ✅ | ✅ | ✅ | ❌ |
| Zmiana ról użytkowników | ✅ | ✅ | ❌ | ❌ |
| Usuwanie domu | ✅ | ✅ | ❌ | ❌ |
| Dostęp do logów zarządzania | ✅ | ✅ | ✅ | ❌ |
| Dostęp do wszystkich domów | ✅ | ❌ | ❌ | ❌ |

**Implementacja dekoratorów autoryzacji:**

```python
# app/simple_auth.py
class SimpleAuthManager:
    def login_required(self, f):
        """Require user to be logged in"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page")
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    
    def admin_required(self, f):
        """Require user to be admin or owner of current home"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user_id = session['user_id']
            home_id = session.get('current_home_id')
            
            # Sys-admin always has access
            if session.get('role') == 'sys-admin':
                return f(*args, **kwargs)
            
            # Check home-level admin access
            if not self.multi_db.has_admin_access(home_id, user_id):
                flash("Access denied. Admin privileges required.")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    def owner_required(self, f):
        """Require user to be owner of current home"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            home_id = session.get('current_home_id')
            
            # Sys-admin always has access
            if session.get('role') == 'sys-admin':
                return f(*args, **kwargs)
            
            # Check owner role
            role = self.multi_db.get_user_role_in_home(home_id, user_id)
            if role != 'owner':
                flash("Access denied. Owner privileges required.")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
```

**Użycie dekoratorów:**

```python
@self.app.route('/admin_dashboard')
@self.auth_manager.login_required
@self.auth_manager.admin_required
def admin_dashboard():
    # Only admins and owners can access
    return render_template('admin_dashboard.html')

@self.app.route('/api/home/<home_id>/delete', methods=['DELETE'])
@self.auth_manager.login_required
@self.auth_manager.owner_required
def delete_home(home_id):
    # Only owner can delete home
    success = self.multi_db.delete_home(home_id)
    return jsonify({'success': success})
```

### 5.1.3. Profil użytkownika

**Edycja profilu:**

```python
@self.app.route('/settings/profile', methods=['GET', 'POST'])
@self.auth_manager.login_required
def edit_profile():
    user_id = session['user_id']
    
    if request.method == 'GET':
        user = self.smart_home.get_user(user_id)
        return render_template('settings_profile.html', user=user)
    
    # POST - update profile
    updates = {}
    
    # Update email
    new_email = request.form.get('email')
    if new_email and new_email != user['email']:
        # Validate email not taken
        if self.smart_home.get_user_by_email(new_email):
            flash("Email already in use")
            return redirect(url_for('edit_profile'))
        
        updates['email'] = new_email
        # Send verification email to new address
        send_email_change_verification(user_id, new_email)
    
    # Update display name
    new_name = request.form.get('display_name')
    if new_name:
        updates['display_name'] = new_name
    
    # Update profile picture
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and allowed_file(file.filename):
            # Optimize and save image
            filename = f"{user_id}_{uuid.uuid4().hex[:8]}.jpg"
            filepath = optimize_and_save_image(file, filename)
            updates['profile_picture'] = filepath
    
    # Apply updates
    if updates:
        self.smart_home.update_user(user_id, updates)
        flash("Profile updated successfully")
    
    return redirect(url_for('edit_profile'))
```

**Zmiana hasła:**

```python
@self.app.route('/settings/change_password', methods=['POST'])
@self.auth_manager.login_required
def change_password():
    user_id = session['user_id']
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # 1. Validate new password
    if len(new_password) < 8:
        flash("New password must be at least 8 characters")
        return redirect(url_for('settings'))
    
    if new_password != confirm_password:
        flash("Passwords do not match")
        return redirect(url_for('settings'))
    
    # 2. Verify current password
    user = self.smart_home.get_user(user_id)
    if not bcrypt.checkpw(
        current_password.encode('utf-8'),
        user['password_hash'].encode('utf-8')
    ):
        flash("Current password is incorrect")
        return redirect(url_for('settings'))
    
    # 3. Hash and save new password
    new_hash = bcrypt.hashpw(
        new_password.encode('utf-8'),
        bcrypt.gensalt(rounds=12)
    )
    
    self.smart_home.update_user(user_id, {
        'password_hash': new_hash.decode('utf-8')
    })
    
    # 4. Log password change
    log_management_event(
        'password_changed',
        user_id=user_id,
        ip_address=request.remote_addr
    )
    
    # 5. Send notification email
    send_password_change_notification(user['email'])
    
    flash("Password changed successfully")
    return redirect(url_for('settings'))
```

## 5.2. System Multi-Home

### 5.2.1. Koncepcja wielu domów

**Model danych:**

```python
# User perspective
{
    "user_id": "uuid-1",
    "homes": [
        {
            "home_id": "home-A",
            "name": "Mój Dom",
            "role": "owner",
            "is_current": True
        },
        {
            "home_id": "home-B",
            "name": "Domek letniskowy",
            "role": "owner",
            "is_current": False
        },
        {
            "home_id": "home-C",
            "name": "Dom rodzinny",
            "role": "admin",
            "is_current": False
        }
    ]
}
```

**Przełączanie między domami:**

```python
# app/multi_home_routes.py
@self.app.route('/home/select/<home_id>')
@self.auth_manager.login_required
def select_home(home_id):
    user_id = session['user_id']
    
    # 1. Verify access to home
    if not self.multi_db.has_home_access(home_id, user_id):
        flash("You don't have access to this home")
        return redirect(url_for('home_select'))
    
    # 2. Update session
    session['current_home_id'] = home_id
    
    # 3. Save last selected home in database
    self.multi_db.set_user_current_home(user_id, home_id)
    
    # 4. Invalidate cache for old and new home
    old_home = session.get('previous_home_id')
    if old_home:
        self.cache_manager.invalidate_home_cache(old_home)
    self.cache_manager.invalidate_home_cache(home_id)
    
    session['previous_home_id'] = home_id
    
    # 5. Log home switch
    log_management_event(
        'home_switched',
        user_id=user_id,
        details={'from_home': old_home, 'to_home': home_id}
    )
    
    flash(f"Switched to {get_home_name(home_id)}")
    return redirect(url_for('index'))
```

### 5.2.2. Zarządzanie domami

**Tworzenie nowego domu:**

```python
@self.app.route('/api/homes', methods=['POST'])
@self.auth_manager.login_required
def create_home():
    user_id = session['user_id']
    data = request.get_json()
    
    home_name = data.get('name')
    home_description = data.get('description', '')
    
    # Validate name
    if not home_name or len(home_name) < 2:
        return jsonify({'error': 'Name too short'}), 400
    
    # Create home
    home_id = str(uuid.uuid4())
    success = self.multi_db.create_home(
        home_id=home_id,
        name=home_name,
        description=home_description,
        created_by=user_id
    )
    
    if not success:
        return jsonify({'error': 'Failed to create home'}), 500
    
    # Add creator as owner
    self.multi_db.add_home_member(
        home_id=home_id,
        user_id=user_id,
        role='owner'
    )
    
    # Create default rooms
    default_rooms = ['Salon', 'Kuchnia', 'Sypialnia', 'Łazienka']
    for room_name in default_rooms:
        self.multi_db.create_room(
            home_id=home_id,
            name=room_name
        )
    
    # Switch to new home
    session['current_home_id'] = home_id
    
    # Log
    log_management_event(
        'home_created',
        user_id=user_id,
        details={'home_id': home_id, 'name': home_name}
    )
    
    return jsonify({
        'success': True,
        'home_id': home_id,
        'message': 'Home created successfully'
    })
```

**Usuwanie domu:**

```python
@self.app.route('/api/homes/<home_id>', methods=['DELETE'])
@self.auth_manager.login_required
@self.auth_manager.owner_required
def delete_home(home_id):
    user_id = session['user_id']
    
    # Get home info before deletion
    home = self.multi_db.get_home(home_id)
    if not home:
        return jsonify({'error': 'Home not found'}), 404
    
    # Verify ownership (double check)
    if home['created_by'] != user_id and session.get('role') != 'sys-admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if it's user's last home
    user_homes = self.multi_db.get_user_homes(user_id)
    if len(user_homes) == 1:
        return jsonify({
            'error': 'Cannot delete your only home'
        }), 400
    
    # Delete home (CASCADE will delete all related data)
    success = self.multi_db.delete_home(home_id)
    if not success:
        return jsonify({'error': 'Failed to delete home'}), 500
    
    # If current home was deleted, switch to another
    if session.get('current_home_id') == home_id:
        remaining_homes = self.multi_db.get_user_homes(user_id)
        if remaining_homes:
            session['current_home_id'] = remaining_homes[0]['id']
    
    # Log
    log_management_event(
        'home_deleted',
        user_id=user_id,
        details={'home_id': home_id, 'name': home['name']}
    )
    
    # Notify all members
    members = self.multi_db.get_home_members(home_id)
    for member in members:
        if member['user_id'] != user_id:
            send_email_notification(
                member['email'],
                'home_deleted',
                {'home_name': home['name']}
            )
    
    return jsonify({'success': True})
```

### 5.2.3. Zaproszenia użytkowników

**Wysyłanie zaproszenia:**

```python
@self.app.route('/api/homes/<home_id>/invite', methods=['POST'])
@self.auth_manager.login_required
@self.auth_manager.admin_required
def invite_user(home_id):
    user_id = session['user_id']
    data = request.get_json()
    
    invitee_email = data.get('email')
    role = data.get('role', 'user')
    
    # Validate role
    if role not in ['admin', 'user']:
        return jsonify({'error': 'Invalid role'}), 400
    
    # Check if user exists
    invitee = self.smart_home.get_user_by_email(invitee_email)
    if not invitee:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already member
    if self.multi_db.is_home_member(home_id, invitee['id']):
        return jsonify({'error': 'User is already a member'}), 400
    
    # Create invitation
    invitation_id = str(uuid.uuid4())
    token = generate_invitation_token()
    
    invitation = {
        'id': invitation_id,
        'home_id': home_id,
        'inviter_id': user_id,
        'invitee_id': invitee['id'],
        'invitee_email': invitee_email,
        'role': role,
        'token': token,
        'status': 'pending',
        'created_at': datetime.now(timezone.utc),
        'expires_at': datetime.now(timezone.utc) + timedelta(days=7)
    }
    
    success = self.multi_db.create_invitation(invitation)
    if not success:
        return jsonify({'error': 'Failed to create invitation'}), 500
    
    # Send invitation email
    home = self.multi_db.get_home(home_id)
    inviter = self.smart_home.get_user(user_id)
    
    send_invitation_email(
        invitee_email,
        home['name'],
        inviter['name'],
        role,
        invitation_url=url_for(
            'accept_invitation',
            token=token,
            _external=True
        )
    )
    
    # Log
    log_management_event(
        'invitation_sent',
        user_id=user_id,
        details={
            'home_id': home_id,
            'invitee_email': invitee_email,
            'role': role
        }
    )
    
    return jsonify({
        'success': True,
        'invitation_id': invitation_id
    })
```

**Akceptowanie zaproszenia:**

```python
@self.app.route('/invite/accept/<token>')
@self.auth_manager.login_required
def accept_invitation(token):
    user_id = session['user_id']
    
    # Get invitation by token
    invitation = self.multi_db.get_invitation_by_token(token)
    if not invitation:
        flash("Invalid or expired invitation")
        return redirect(url_for('home_select'))
    
    # Verify invitation is for this user
    if invitation['invitee_id'] != user_id:
        flash("This invitation is not for you")
        return redirect(url_for('home_select'))
    
    # Check if already accepted
    if invitation['status'] != 'pending':
        flash("Invitation already processed")
        return redirect(url_for('home_select'))
    
    # Check expiration
    if invitation['expires_at'] < datetime.now(timezone.utc):
        flash("Invitation has expired")
        return redirect(url_for('home_select'))
    
    # Add user to home
    success = self.multi_db.add_home_member(
        home_id=invitation['home_id'],
        user_id=user_id,
        role=invitation['role']
    )
    
    if not success:
        flash("Failed to accept invitation")
        return redirect(url_for('home_select'))
    
    # Update invitation status
    self.multi_db.update_invitation_status(
        invitation['id'],
        'accepted'
    )
    
    # Log
    log_management_event(
        'invitation_accepted',
        user_id=user_id,
        details={'home_id': invitation['home_id']}
    )
    
    # Switch to new home
    session['current_home_id'] = invitation['home_id']
    
    home = self.multi_db.get_home(invitation['home_id'])
    flash(f"Welcome to {home['name']}!")
    
    return redirect(url_for('index'))
```

## 5.3. Zarządzanie urządzeniami

### 5.3.1. Pokoje i ich organizacja

**Tworzenie pokoju:**

```python
@self.app.route('/api/rooms', methods=['POST'])
@self.auth_manager.login_required
@self.auth_manager.admin_required
def create_room():
    home_id = session['current_home_id']
    data = request.get_json()
    
    room_name = data.get('name')
    if not room_name or len(room_name) < 2:
        return jsonify({'error': 'Name too short'}), 400
    
    # Check for duplicate name in this home
    existing_rooms = self.multi_db.get_rooms(home_id)
    if any(r['name'].lower() == room_name.lower() for r in existing_rooms):
        return jsonify({'error': 'Room name already exists'}), 400
    
    # Create room
    room_id = str(uuid.uuid4())
    display_order = len(existing_rooms)
    
    success = self.multi_db.create_room(
        room_id=room_id,
        home_id=home_id,
        name=room_name,
        display_order=display_order
    )
    
    if not success:
        return jsonify({'error': 'Failed to create room'}), 500
    
    # Invalidate cache
    self.cache_manager.invalidate_rooms_cache(home_id)
    
    # Emit Socket.IO update
    self.socketio.emit(
        'update_rooms',
        {'rooms': self.multi_db.get_rooms(home_id)},
        room=f"home_{home_id}"
    )
    
    return jsonify({
        'success': True,
        'room_id': room_id,
        'message': 'Room created successfully'
    })
```

**Sortowanie pokojów (drag & drop):**

```python
@self.app.route('/api/rooms/reorder', methods=['POST'])
@self.auth_manager.login_required
@self.auth_manager.admin_required
def reorder_rooms():
    home_id = session['current_home_id']
    data = request.get_json()
    
    # Expect array of room IDs in new order
    room_ids = data.get('room_ids', [])
    
    # Update display_order for each room
    for index, room_id in enumerate(room_ids):
        self.multi_db.update_room_order(
            room_id=room_id,
            display_order=index
        )
    
    # Invalidate cache
    self.cache_manager.invalidate_rooms_cache(home_id)
    
    # Emit update
    self.socketio.emit(
        'update_rooms',
        {'rooms': self.multi_db.get_rooms(home_id)},
        room=f"home_{home_id}"
    )
    
    return jsonify({'success': True})
```

### 5.3.2. Urządzenia przełącznikowe (przyciski)

**Dodawanie przycisku:**

```python
@self.app.route('/api/devices/buttons', methods=['POST'])
@self.auth_manager.login_required
@self.auth_manager.admin_required
def create_button():
    home_id = session['current_home_id']
    data = request.get_json()
    
    button_name = data.get('name')
    room_id = data.get('room_id')
    
    # Validate
    if not button_name or len(button_name) < 2:
        return jsonify({'error': 'Name too short'}), 400
    
    if room_id:
        # Verify room belongs to this home
        room = self.multi_db.get_room(room_id)
        if not room or room['home_id'] != home_id:
            return jsonify({'error': 'Invalid room'}), 400
    
    # Create device
    device_id = str(uuid.uuid4())
    device = {
        'id': device_id,
        'home_id': home_id,
        'room_id': room_id,
        'name': button_name,
        'device_type': 'button',
        'state': False,
        'enabled': True
    }
    
    success = self.multi_db.create_device(device)
    if not success:
        return jsonify({'error': 'Failed to create device'}), 500
    
    # Invalidate cache
    self.cache_manager.invalidate_devices_cache(home_id)
    
    # Emit update
    self.socketio.emit(
        'update_devices',
        {'devices': self.multi_db.get_devices(home_id)},
        room=f"home_{home_id}"
    )
    
    return jsonify({
        'success': True,
        'device_id': device_id
    })
```

**Przełączanie stanu przycisku:**

```python
@self.socketio.on('toggle_device')
def handle_toggle_device(data):
    if 'user_id' not in session:
        return
    
    device_id = data.get('device_id')
    user_id = session['user_id']
    home_id = session['current_home_id']
    
    # Get device
    device = self.multi_db.get_device(device_id)
    if not device or device['home_id'] != home_id:
        emit('error', {'message': 'Device not found'})
        return
    
    # Toggle state
    new_state = not device['state']
    
    # Save to database
    success = self.multi_db.update_device_state(
        device_id=device_id,
        state=new_state,
        changed_by=user_id,
        change_reason='manual_toggle'
    )
    
    if not success:
        emit('error', {'message': 'Failed to toggle device'})
        return
    
    # Save to history
    self.multi_db.add_device_history(
        device_id=device_id,
        old_state={'state': device['state']},
        new_state={'state': new_state},
        changed_by=user_id,
        change_reason='manual_toggle'
    )
    
    # Invalidate cache
    self.cache_manager.invalidate_device_cache(device_id)
    
    # Emit to all clients in this home
    self.socketio.emit(
        'device_state_changed',
        {
            'device_id': device_id,
            'state': new_state,
            'changed_by': session['username']
        },
        room=f"home_{home_id}"
    )
```

---

**Podsumowanie części 5.1-5.3:**

Rozdział implementacji szczegółowo opisuje kluczowe funkcjonalności systemu. Przedstawiono proces rejestracji i logowania użytkowników z haszowaniem bcrypt, system ról i uprawnień z trzema poziomami (sys-admin, owner, admin, user), oraz zarządzanie profilami użytkowników.

Sekcja multi-home opisuje koncepcję wielu domów, przełączanie między nimi oraz mechanizm zaproszeń z tokenami i expiracją. Zaprezentowano również implementację zarządzania pokojami i urządzeniami z real-time synchronizacją przez Socket.IO.

W dalszej części rozdziału zostaną opisane automatyzacje, panel administratora oraz system powiadomień.

## 5.4. Warstwa automatyzacji i harmonogram

### 5.4.1. Model automatyzacji

Automatyzacja składa się logicznie z trzech części:
- `trigger_config` – definicja warunku (czas, stan urządzenia, przyszłościowo: warunek złożony)
- `actions_config` – lista akcji (ustawienie stanu urządzenia, wysłanie maila, w przyszłości: webhook)
- `enabled` – flaga aktywności

Przykładowa struktura w bazie (`jsonb`):
```json
{
  "trigger": {"type": "time", "cron": "0 7 * * *"},
  "actions": [
    {"type": "device_state", "device_id": "<uuid>", "state": true},
    {"type": "email", "template": "automation_executed"}
  ]
}
```

### 5.4.2. Scheduler w tle

Harmonogram uruchamiany przy starcie aplikacji (np. w `background_scheduler.py`) period ycznie wykonuje pętlę:
1. Pobierz aktywne automatyzacje (`enabled = true`)
2. Odfiltruj te, których `trigger` pasuje do czasu lub stanu
3. Wykonaj akcje – każda akcja jest strategią (wzorzec Strategy)
4. Zaloguj wykonanie / zapisz historię
5. Emituj aktualizację Socket.IO jeśli zmienia się stan urządzenia

### 5.4.3. Wzorzec strategii dla akcji

```python
class ActionExecutor:
    def __init__(self, multi_db, cache_manager, socketio, mail_manager):
        self.multi_db = multi_db
        self.cache = cache_manager
        self.socketio = socketio
        self.mail = mail_manager

    def execute(self, action, context):
        atype = action.get('type')
        if atype == 'device_state':
            return self._exec_device_state(action, context)
        if atype == 'email':
            return self._exec_email(action, context)
        # przyszłościowo: webhook, queue publish
        return False

    def _exec_device_state(self, action, context):
        device_id = action['device_id']
        state = action['state']
        device = self.multi_db.get_device(device_id)
        if not device:
            return False
        if device['state'] == state:
            return True  # idempotencja
        self.multi_db.update_device_state(
            device_id=device_id,
            state=state,
            changed_by=context.get('system_user', 'automation'),
            change_reason='automation'
        )
        self.cache.invalidate_device_cache(device_id)
        self.socketio.emit('device_state_changed', {
            'device_id': device_id,
            'state': state,
            'changed_by': 'automation'
        }, room=f"home_{device['home_id']}")
        return True

    def _exec_email(self, action, context):
        self.mail.enqueue_email(
            to=context['user_email'],
            subject='Automation executed',
            template=action.get('template', 'generic'),
            variables={'ts': datetime.utcnow().isoformat()}
        )
        return True
```

### 5.4.4. Odporność i idempotencja

Kluczowe założenia:
- Brak duplikacji akcji – identyfikacja przez `(automation_id, window_ts)`
- Zabezpieczenie przed nakładaniem – lock w Redis (przyszłościowo)
- Re-try polityka: tylko akcje komunikacyjne (email/webhook)

## 5.5. Panel administratora

Panel agreguje dane z kilku managerów i prezentuje je (role: admin/owner/sys-admin):
- Liczba użytkowników w domu
- Liczba urządzeń / pokojów
- Ostatnie logi zarządzania (tabela `management_logs` – przyszłościowo)
- Wskaźnik cache hit rate (jeśli Redis aktywny)

Przykładowy endpoint (szkic):
```python
@self.app.route('/api/admin/metrics')
@self.auth_manager.login_required
@self.auth_manager.admin_required
def admin_metrics():
    home_id = session['current_home_id']
    return jsonify({
        'users': len(self.multi_db.get_home_members(home_id)),
        'rooms': len(self.multi_db.get_rooms(home_id)),
        'devices': len(self.multi_db.get_devices(home_id)),
        'automations': len(self.multi_db.get_automations(home_id)),
        # 'cache_hit_rate': self.cache_manager.hit_rate()  # jeśli zaimplementowano
    })
```

## 5.6. System powiadomień

Aktualnie powiadomienia ograniczają się do wysyłki email (asynchronicznie) dla wybranych zdarzeń (np. alert bezpieczeństwa, wykonanie automatyzacji). Struktura kolejki (minimalistyczna): lista w pamięci z workerem w wątku.

Przyszłe rozszerzenia:
- Kanały: WebPush, mobilne powiadomienia (PWA), webhooki
- Reguły filtrowania per użytkownik
- Agregacja (throttling) – łączenie wielu zdarzeń w jedno powiadomienie

## 5.7. (Przyszłość) Adapter Device Interface – projekt rozszerzeń IoT

W bieżącej wersji brak bezpośredniego połączenia z fizycznymi urządzeniami. Aby umożliwić przyszłą integrację w sposób modularny zaprojektowano koncepcję „Adapter Device Interface”.

### 5.7.1. Cele
- Izolacja różnic protokołów (MQTT, Zigbee, Z-Wave, Matter, BLE)
- Plug-in architecture – hot-plug adapterów bez modyfikacji core
- Jednolity model stanu urządzenia (`{id, type, state, meta}`)

### 5.7.2. Interfejs bazowy (propozycja)
```python
class DeviceAdapter(Protocol):
    def connect(self) -> None: ...
    def list_devices(self) -> list[dict]: ...
    def get_state(self, device_id: str) -> dict: ...
    def set_state(self, device_id: str, state: dict) -> bool: ...
    def subscribe(self, callback: Callable[[dict], None]) -> None: ...
```

### 5.7.3. Mock adapter (testy bez sprzętu)
```python
class MockAdapter:
    def __init__(self):
        self._devices = {
            'mock-1': {'id': 'mock-1', 'type': 'button', 'state': {'on': False}},
        }
        self._callbacks = []

    def connect(self):
        return True

    def list_devices(self):
        return list(self._devices.values())

    def get_state(self, device_id):
        return self._devices[device_id]['state']

    def set_state(self, device_id, state):
        self._devices[device_id]['state'] = state
        event = {'device_id': device_id, 'state': state}
        for cb in self._callbacks:
            cb(event)
        return True

    def subscribe(self, callback):
        self._callbacks.append(callback)
```

### 5.7.4. Integracja z istniejącym kodem (plan)
1. Warstwa adapterów rejestrowana przy starcie (fabryka)
2. Cykl życia: `connect()` -> enumeracja -> mapowanie do tabeli `devices`
3. Zmiany stanu → adapter → event → aktualizacja DB + Socket.IO emit
4. Akcje użytkownika → DB update → (opcjonalnie) adapter `set_state`

### 5.7.5. Bezpieczeństwo i sandbox
- Oddzielne procesy / kontenery dla adapterów
- Whitelist protokołów i portów
- Walidacja payloadów JSON

---

**Podsumowanie części 5.4–5.7:**

Dodano opis logiki automatyzacji opartej o scheduler i strategię akcji, panelu administratora z metrykami oraz systemu powiadomień. Zaprojektowano przyszłościowy interfejs adapterów urządzeń umożliwiający rozszerzenie platformy bez zmian w rdzeniu.
