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

// Create confirmation button for delete actions
function createConfirmButton(username, deleteBtn) {
    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'confirm-delete-btn';
    confirmBtn.textContent = 'Potwierdź';
    confirmBtn.dataset.username = username;
    deleteBtn.classList.add('hidden');
    confirmBtn.addEventListener('click', () => {
        performUserDeletion(username);
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

// Load users list
let notificationUsersList = [];

async function loadUsers() {
    try {
        const response = await app.fetchData('/api/users');
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
        // Change password button
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
                        const response = await fetch(`/api/users/${user.username}/password`, {
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
        if (user.username !== 'admin') {
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-button';
            deleteBtn.textContent = 'Usuń';
            deleteBtn.addEventListener('click', (e) => deleteUser(user.username, e));
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
        const response = await app.postData('/api/users', { username, password, role });
        if (response.status === 'success') {
            showMessage('addUserMessage', `Użytkownik ${username} został dodany pomyślnie`);
            showNotification(`Użytkownik ${username} został dodany`, 'success');
            document.getElementById('newUsername').value = '';
            document.getElementById('newPassword').value = '';
            loadUsers();
        } else {
            throw new Error(response.message || 'Nieznany błąd');
        }
    } catch (error) {
        console.error('Błąd dodawania użytkownika:', error);
        showMessage('addUserMessage', `Nie udało się dodać użytkownika: ${error.message}`, true);
        showNotification(`Nie udało się dodać użytkownika: ${error.message}`, 'error');
    }
}

// Delete user flow
function deleteUser(username, event) {
    if (!username) return;
    const deleteBtn = event.target;
    const actionsDiv = deleteBtn.parentNode;
    const confirmBtn = createConfirmButton(username, deleteBtn);
    actionsDiv.appendChild(confirmBtn);
}

// Perform user deletion
async function performUserDeletion(username) {
    try {
        const response = await app.deleteData(`/api/users/${username}`);
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
        const users = await app.fetchData('/api/users');
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
        const response = await app.fetchData('/api/notifications/settings');
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
        const response = await app.postData('/api/notifications/settings', {
            recipients: notificationRecipients
        });
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
        const response = await app.postData('/api/notifications/settings', {
            recipients: notificationRecipients
        });
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