// Helper function to show messages
function showMessage(elementId, message, isError = false) {
    // Pokazuj tylko powiadomienie w rogu, nie wyświetlaj komunikatu pod formularzem
    showNotification(message, isError ? 'error' : 'success');
    // Ukryj kontener na komunikat pod formularzem, jeśli istnieje
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = '';
        element.style.display = 'none';
    }
}

// Helper function to get CSRF token
function getCSRFToken() {
    let csrfToken = null;
    const input = document.querySelector('input[name="_csrf_token"]');
    if (input) csrfToken = input.value;
    if (!csrfToken) {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) csrfToken = meta.getAttribute('content');
    }
    if (!csrfToken && window.csrf_token) csrfToken = window.csrf_token;
    return csrfToken;
}

// Create confirmation button for delete actions
function createConfirmButton(user_id, username, deleteBtn) {
    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'confirm-delete-btn';
    confirmBtn.textContent = 'Potwierdź';
    confirmBtn.dataset.userId = user_id;
    confirmBtn.dataset.username = username;
    deleteBtn.classList.add('hidden');
    confirmBtn.addEventListener('click', () => {
        performUserDeletion(user_id, username);
        confirmBtn.remove();
        deleteBtn.classList.remove('hidden');
    });
    const timeoutId = setTimeout(() => {
        if (confirmBtn.parentNode) {
            confirmBtn.remove();
            deleteBtn.classList.remove('hidden');
        }
    }, 5000);
    confirmBtn.addEventListener('click', () => clearTimeout(timeoutId));
    return confirmBtn;
}

// Helper function to make API calls without app object
async function makeApiCall(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            ...options.headers
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
}

// Helper function to wait for app to be initialized
function waitForApp() {
    return new Promise((resolve) => {
        if (window.app) {
            resolve(window.app);
        } else {
            const checkApp = () => {
                if (window.app) {
                    resolve(window.app);
                } else {
                    setTimeout(checkApp, 100);
                }
            };
            checkApp();
        }
    });
}

// Load users list
let notificationUsersList = [];

async function loadUsers() {
    try {
        let response;
        if (window.app) {
            response = await window.app.fetchData('/api/users');
        } else {
            response = await makeApiCall('/api/users');
        }
        
        if (Array.isArray(response)) {
            updateUsersTable(response);
            notificationUsersList = response;
            fillNotificationUserSelect();
        } else if (response.status === 'error') {
            throw new Error(response.message);
        } else {
            throw new Error('Nieprawidłowy format odpowiedzi');
        }
    } catch (error) {
        console.error('Błąd ładowania użytkowników:', error);
        showMessage('userActionMessage', 'Nie udało się załadować listy użytkowników: ' + error.message, true);
    }
}

// Update users table
function updateUsersTable(users) {
    const tableBody = document.getElementById('usersTableBody');
    if (!tableBody) return;
    tableBody.innerHTML = '';
    users.forEach(user => {
        const row = document.createElement('tr');
        row.className = 'user-row';
        // Username
        const usernameCell = document.createElement('td');
        usernameCell.textContent = user.username;
        row.appendChild(usernameCell);

        // Role
        const roleCell = document.createElement('td');
        roleCell.textContent = user.role === 'admin' ? 'Administrator' : 'Użytkownik';
        row.appendChild(roleCell);
        // Actions
        const actionsCell = document.createElement('td');
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'action-buttons';
        
        // Edit username button
        const editNameBtn = document.createElement('button');
        editNameBtn.className = 'change-button';
        editNameBtn.textContent = 'Edytuj nazwę';
        editNameBtn.addEventListener('click', () => {
            if (actionsDiv.querySelector('.edit-generic-form')) return;
            Array.from(actionsDiv.children).forEach(child => {
                if (child !== editNameBtn) child.style.display = 'none';
            });
            editNameBtn.style.display = 'none';
            window.createEditForm({
                fields: [
                    { name: 'newUsername', type: 'text', required: true, minLength: 3, placeholder: 'Nowa nazwa użytkownika', id: 'username_change', className: 'input-edit', removeDefaultMargin: true, value: user.username }
                ],
                parent: actionsDiv,
                saveText: 'Zapisz',
                cancelText: 'Anuluj',
                onSave: async (values) => {
                    const newUsername = values.newUsername;
                    if (!newUsername || newUsername.length < 3) {
                        showNotification('Nazwa użytkownika musi mieć co najmniej 3 znaki', 'error');
                        return;
                    }
                    try {
                        const response = await fetch(`/api/users/${user.user_id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                            body: JSON.stringify({ username: newUsername })
                        });
                        const data = await response.json();
                        if (!response.ok) throw new Error(data.message || 'Nieznany błąd');
                        showNotification(`Nazwa użytkownika zmieniona na ${newUsername}`, 'success');
                        loadUsers();
                    } catch (error) {
                        showNotification(`Nie udało się zmienić nazwy użytkownika: ${error.message}`, 'error');
                    }
                },
                onCancel: () => {
                    loadUsers();
                }
            });
        });
        actionsDiv.appendChild(editNameBtn);
        // Edit role button (if not current user)
        if (user.role !== 'admin' || user.username !== 'admin') {
            const editRoleBtn = document.createElement('button');
            editRoleBtn.className = 'change-button';
            editRoleBtn.textContent = 'Zmień rolę';
            editRoleBtn.addEventListener('click', () => {
                if (actionsDiv.querySelector('.edit-generic-form')) return;
                Array.from(actionsDiv.children).forEach(child => {
                    if (child !== editRoleBtn) child.style.display = 'none';
                });
                editRoleBtn.style.display = 'none';
                window.createEditForm({
                    fields: [
                        { 
                            name: 'newRole', 
                            type: 'select', 
                            required: true, 
                            placeholder: 'Wybierz rolę', 
                            id: 'role_change', 
                            className: 'input-edit', 
                            removeDefaultMargin: true,
                            options: [
                                { value: 'user', text: 'Użytkownik' },
                                { value: 'admin', text: 'Administrator' }
                            ],
                            value: user.role
                        }
                    ],
                    parent: actionsDiv,
                    saveText: 'Zapisz',
                    cancelText: 'Anuluj',
                    onSave: async (values) => {
                        const newRole = values.newRole;
                        if (!newRole || !['user', 'admin'].includes(newRole)) {
                            showNotification('Nieprawidłowa rola', 'error');
                            return;
                        }
                        try {
                            const response = await fetch(`/api/users/${user.user_id}`, {
                                method: 'PUT',
                                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                                body: JSON.stringify({ role: newRole })
                            });
                            const data = await response.json();
                            if (!response.ok) throw new Error(data.message || 'Nieznany błąd');
                            showNotification(`Rola użytkownika ${user.username} zmieniona na ${newRole === 'admin' ? 'Administrator' : 'Użytkownik'}`, 'success');
                            loadUsers();
                        } catch (error) {
                            showNotification(`Nie udało się zmienić roli: ${error.message}`, 'error');
                        }
                    },
                    onCancel: () => {
                        loadUsers();
                    }
                });
            });
            actionsDiv.appendChild(editRoleBtn);
        }
        const changePassBtn = document.createElement('button');
        changePassBtn.className = 'change-button';
        changePassBtn.textContent = 'Zmień hasło';
        changePassBtn.addEventListener('click', () => {
            if (actionsDiv.querySelector('.edit-generic-form')) return;
            Array.from(actionsDiv.children).forEach(child => {
                if (child !== changePassBtn) child.style.display = 'none';
            });
            changePassBtn.style.display = 'none';
            window.createEditForm({
                fields: [
                    { name: 'newPassword', type: 'password', required: true, minLength: 6, placeholder: 'Nowe hasło', id: 'password_change', className: 'input-edit', removeDefaultMargin: true }
                ],
                parent: actionsDiv,
                saveText: 'Zapisz',
                cancelText: 'Anuluj',
                onSave: async (values) => {
                    const newPassword = values.newPassword;
                    if (!newPassword || newPassword.length < 6) {
                        showNotification('Hasło musi mieć co najmniej 6 znaków', 'error');
                        return;
                    }
                    try {
                        const response = await fetch(`/api/users/${user.user_id}/password`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                            body: JSON.stringify({ new_password: newPassword })
                        });
                        const data = await response.json();
                        if (!response.ok) throw new Error(data.message || 'Nieznany błąd');
                        showNotification(`Hasło dla użytkownika ${user.username} zostało zmienione`, 'success');
                        loadUsers();
                    } catch (error) {
                        showNotification(`Nie udało się zmienić hasła: ${error.message}`, 'error');
                    }
                },
                onCancel: () => {
                    loadUsers();
                }
            });
        });
        actionsDiv.appendChild(changePassBtn);
        // Delete button (if not admin)
        if (user.role !== 'admin') {
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-button';
            deleteBtn.textContent = 'Usuń';
            deleteBtn.addEventListener('click', (e) => deleteUser(user.user_id, user.username, e));
            actionsDiv.appendChild(deleteBtn);
        }
        actionsCell.appendChild(actionsDiv);
        row.appendChild(actionsCell);
        tableBody.appendChild(row);
    });
}

// Add new user
async function addUser() {
    const username = document.getElementById('newUsername')?.value.trim();
    const password = document.getElementById('newPassword')?.value;
    const role = document.getElementById('userRole')?.value;
    if (!username || username.length < 3) {
        showMessage('addUserMessage', 'Nazwa użytkownika musi mieć co najmniej 3 znaki', true);
        return;
    }
    if (!password || password.length < 6) {
        showMessage('addUserMessage', 'Hasło musi mieć co najmniej 6 znaków', true);
        return;
    }
    try {
        // Pobierz token CSRF z inputa (najpewniejsze źródło dla Flask)
        let csrfToken = null;
        const input = document.querySelector('input[name="_csrf_token"]');
        if (input) csrfToken = input.value;
        if (!csrfToken) {
            const meta = document.querySelector('meta[name="csrf-token"]');
            if (meta) csrfToken = meta.getAttribute('content');
        }
        if (!csrfToken && window.csrf_token) csrfToken = window.csrf_token;

        if (!csrfToken) {
            showMessage('addUserMessage', 'Brak tokena CSRF. Odśwież stronę i spróbuj ponownie.', true);
            return;
        }

        // DEBUG: log request before sending
        // console.log('Sending addUser POST', { username, password, role, csrfToken });

        // Wyślij żądanie POST z CSRF tokenem
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin',
            body: JSON.stringify({ username, password, role })
        });

        // Sprawdź, czy fetch został zablokowany przez przeglądarkę (np. przez CORS, brak sesji, itp.)
        if (response.type === 'opaque' || response.status === 0) {
            showMessage('addUserMessage', 'Żądanie zostało zablokowane przez przeglądarkę lub serwer. Sprawdź CORS, cookies i sesję.', true);
            throw new Error('Żądanie zostało zablokowane przez przeglądarkę lub serwer. Sprawdź CORS, cookies i sesję.');
        }

        // Jeśli odpowiedź nie jest ok, spróbuj pobrać tekst błędu
        if (!response.ok) {
            let msg = '';
            try {
                msg = await response.text();
            } catch {}
            throw new Error(msg || `HTTP ${response.status}`);
        }

        let data;
        try {
            data = await response.json();
        } catch (e) {
            throw new Error('Serwer nie zwrócił poprawnego JSON');
        }

        if (data.status === 'success') {
            showMessage('addUserMessage', `Użytkownik ${username} został dodany pomyślnie`);
            showNotification(`Użytkownik ${username} został dodany`, 'success');
            document.getElementById('newUsername').value = '';
            document.getElementById('newPassword').value = '';
            loadUsers();
        } else {
            throw new Error(data.message || 'Nieznany błąd');
        }
    } catch (error) {
        console.error('Błąd dodawania użytkownika:', error);
        showMessage('addUserMessage', `Nie udało się dodać użytkownika: ${error.message}`, true);
        showNotification(`Nie udało się dodać użytkownika: ${error.message}`, 'error');
    }
}

// Delete user flow
function deleteUser(user_id, username, event) {
    if (!user_id || !username) return;
    const deleteBtn = event.target;
    const actionsDiv = deleteBtn.parentNode;
    const confirmBtn = createConfirmButton(user_id, username, deleteBtn);
    actionsDiv.appendChild(confirmBtn);
}

// Perform user deletion
async function performUserDeletion(user_id, username) {
    try {
        let response;
        if (window.app) {
            response = await window.app.deleteData(`/api/users/${user_id}`);
        } else {
            response = await makeApiCall(`/api/users/${user_id}`, { method: 'DELETE' });
        }
        
        if (response.status === 'success') {
            showMessage('userActionMessage', `Użytkownik ${username} został usunięty`);
            showNotification(`Użytkownik ${username} został usunięty`, 'success');
            loadUsers();
        } else {
            throw new Error(response.message || 'Nieznany błąd');
        }
    } catch (error) {
        console.error('Błąd usuwania użytkownika:', error);
        showMessage('userActionMessage', `Nie udało się usunąć użytkownika: ${error.message}`, true);
        showNotification(`Nie udało się usunąć użytkownika: ${error.message}`, 'error');
    }
}

// --- Notification settings logic (admin only) ---
let notificationRecipients = [];

function createConfirmRemoveRecipientButton(idx, removeBtn) {
    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'confirm-delete-btn';
    confirmBtn.textContent = 'Potwierdź';
    confirmBtn.dataset.idx = idx;
    removeBtn.classList.add('hidden');
    confirmBtn.addEventListener('click', async () => {
        notificationRecipients.splice(idx, 1);
        await saveNotificationRecipientsOnly();
        await loadNotificationSettings();
        showNotification('Odbiorca został usunięty', 'success');
        confirmBtn.remove();
        removeBtn.classList.remove('hidden');
    });
    const timeoutId = setTimeout(() => {
        if (confirmBtn.parentNode) {
            confirmBtn.remove();
            removeBtn.classList.remove('hidden');
        }
    }, 5000);
    confirmBtn.addEventListener('click', () => clearTimeout(timeoutId));
    return confirmBtn;
}

function renderNotificationRecipients() {
    const tableBody = document.getElementById('notificationRecipientsTableBody');
    tableBody.innerHTML = '';
    if (notificationRecipients.length === 0) {
        const row = document.createElement('tr');
        row.className = 'no-recipients-row';
        const cell = document.createElement('td');
        cell.colSpan = 4;
        cell.style.color = '#888';
        cell.textContent = 'Brak dodatkowych odbiorców';
        row.appendChild(cell);
        tableBody.appendChild(row);
        return;
    }
    notificationRecipients.forEach((recipient, idx) => {
        const row = document.createElement('tr');
        // E-mail
        const emailCell = document.createElement('td');
        emailCell.textContent = recipient.email || '';
        row.appendChild(emailCell);
        // Użytkownik
        const userCell = document.createElement('td');
        userCell.textContent = recipient.user || '';
        row.appendChild(userCell);
        // Powiadomienia (checkbox)
        const notifyCell = document.createElement('td');
        const notifyLabel = document.createElement('label');
        notifyLabel.className = 'checkbox-notification-label';
        notifyLabel.style.display = 'flex';
        notifyLabel.style.alignItems = 'center';
        notifyLabel.style.justifyContent = 'center';
        notifyLabel.style.gap = '6px';
        const notifyCheckbox = document.createElement('input');
        notifyCheckbox.type = 'checkbox';
        notifyCheckbox.className = 'checkbox-notification';
        notifyCheckbox.checked = recipient.enabled === undefined ? true : !!recipient.enabled;
        notifyCheckbox.addEventListener('change', async () => {
            notificationRecipients[idx].enabled = notifyCheckbox.checked;
            await saveNotificationRecipientsOnly();
        });
        const customSpan = document.createElement('span');
        customSpan.className = 'checkbox-notification-custom';
        customSpan.innerHTML = '<svg viewBox="0 0 13 10"><polyline points="1 5.5 5 9 12 1"></polyline></svg>';
        const textSpan = document.createElement('span');
        textSpan.className = 'checkbox-notification-text';
        textSpan.textContent = 'Włącz powiadomienia';
        notifyLabel.appendChild(notifyCheckbox);
        notifyLabel.appendChild(customSpan);
        notifyLabel.appendChild(textSpan);
        notifyCell.appendChild(notifyLabel);
        row.appendChild(notifyCell);
        // Akcja
        const actionCell = document.createElement('td');
        const removeBtn = document.createElement('button');
        removeBtn.textContent = 'Usuń';
        removeBtn.className = 'delete-button';
        removeBtn.addEventListener('click', () => {
            const confirmBtn = createConfirmRemoveRecipientButton(idx, removeBtn);
            actionCell.appendChild(confirmBtn);
        });
        actionCell.appendChild(removeBtn);
        row.appendChild(actionCell);
        tableBody.appendChild(row);
    });
}

// Dodawanie odbiorcy z checkboxem
function getAddRecipientEnabledValue() {
    const el = document.getElementById('notificationRecipientEnabled');
    return el ? el.checked : true;
}

async function fillNotificationUserSelect() {
    try {
        let users;
        if (window.app) {
            users = await window.app.fetchData('/api/users');
        } else {
            users = await makeApiCall('/api/users');
        }
        
        const select = document.getElementById('notificationRecipientUser');
        if (select) {
            select.innerHTML = '';
            users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.username;
                option.textContent = user.username;
                select.appendChild(option);
            });
        }
    } catch (e) {
        // fallback: zostaw pusty select
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const addBtn = document.getElementById('addNotificationRecipientBtn');
    if (addBtn) {
        addBtn.addEventListener('click', async () => {
            const email = document.getElementById('notificationRecipientEmail').value.trim();
            const user = document.getElementById('notificationRecipientUser').value;
            const enabled = getAddRecipientEnabledValue();
            if (!email || !user) return;
            // Jeśli już istnieje taki email+user, nie dodawaj duplikatu
            if (notificationRecipients.some(r => r.email === email && r.user === user)) return;
            notificationRecipients.push({ email, user, enabled });
            document.getElementById('notificationRecipientEmail').value = '';
            renderNotificationRecipients();
            await saveNotificationRecipientsOnly();
            await loadNotificationSettings();
            showNotification('Odbiorca został dodany', 'success');
        });
    }
    // Załaduj aktualne ustawienia powiadomień i użytkowników
    loadNotificationSettings();
    fillNotificationUserSelect();
});

async function loadNotificationSettings() {
    try {
        let response;
        if (window.app) {
            response = await window.app.fetchData('/api/notifications/settings');
        } else {
            response = await makeApiCall('/api/notifications/settings');
        }
        
        if (Array.isArray(response.recipients)) {
            notificationRecipients = response.recipients;
            renderNotificationRecipients();
        }
        if (notificationRecipients.length > 0) {
            document.getElementById('notificationRecipientEmail').value = notificationRecipients[notificationRecipients.length-1].email;
            document.getElementById('notificationRecipientUser').value = notificationRecipients[notificationRecipients.length-1].user;
        }
    } catch (error) {
        showMessage('notificationsMessage', 'Nie udało się pobrać ustawień powiadomień', true);
    }
}

async function saveNotificationSettings() {
    try {
        let response;
        if (window.app) {
            response = await window.app.postData('/api/notifications/settings', {
                recipients: notificationRecipients
            });
        } else {
            response = await makeApiCall('/api/notifications/settings', {
                method: 'POST',
                body: JSON.stringify({ recipients: notificationRecipients })
            });
        }
        
        if (response.status === 'success') {
            showMessage('notificationsMessage', 'Ustawienia powiadomień zapisane');
        } else {
            throw new Error(response.message || 'Nieznany błąd');
        }
    } catch (error) {
        showMessage('notificationsMessage', 'Błąd zapisu ustawień powiadomień: ' + error.message, true);
    }
}

async function saveNotificationRecipientsOnly() {
    try {
        let response;
        if (window.app) {
            response = await window.app.postData('/api/notifications/settings', {
                recipients: notificationRecipients
            });
        } else {
            response = await makeApiCall('/api/notifications/settings', {
                method: 'POST',
                body: JSON.stringify({ recipients: notificationRecipients })
            });
        }
        
        if (response.status !== 'success') {
            throw new Error(response.message || 'Nieznany błąd');
        }
    } catch (error) {
        showMessage('notificationsMessage', 'Błąd zapisu odbiorców powiadomień: ' + error.message, true);
    }
}

function initNotificationSettings() {
    if (window.sessionRole === 'admin') {
        const saveBtn = document.getElementById('saveNotificationsBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveNotificationSettings);
        }
        loadNotificationSettings();
    }
}

// Page initialization
function initSettingsPage() {
    // Set current theme in selector
    const themeSelect = document.querySelector('.theme-selector select');
    if (themeSelect) {
        themeSelect.value = localStorage.getItem('theme') || 'light';
    }
    // Initialize for admin users
    if (window.sessionRole === 'admin') {
        const addUserBtn = document.getElementById('addUserBtn');
        if (addUserBtn) {
            addUserBtn.addEventListener('click', addUser);
        }
        loadUsers();
        initNotificationSettings();
    }
}

document.addEventListener('DOMContentLoaded', initSettingsPage);