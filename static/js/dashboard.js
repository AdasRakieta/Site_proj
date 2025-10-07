/* ============================== */
/*   Admin Dashboard JavaScript   */
/* ============================== */

// Helper function to show messages
function showMessage(elementId, message, isError = false) {
    // Show notification in corner, don't display message under form
    showNotification(message, isError ? 'error' : 'success');
    // Hide container for message under form, if it exists
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

/* ============================== */
/*      User Management           */
/* ============================== */

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
        row.dataset.userId = user.user_id;
        row.dataset.editing = 'false';
        
        // Username
        const usernameCell = document.createElement('td');
        usernameCell.className = 'username-cell';
        usernameCell.innerHTML = `<span class="display-value">${user.username}</span>`;
        row.appendChild(usernameCell);

        // Email
        const emailCell = document.createElement('td');
        emailCell.className = 'email-cell';
        emailCell.innerHTML = `<span class="display-value">${user.email || ''}</span>`;
        row.appendChild(emailCell);

        // Role - display proper role names
        const roleCell = document.createElement('td');
        roleCell.className = 'role-cell';
        let roleName = 'Użytkownik';
        if (user.role === 'owner') {
            roleName = 'Właściciel';
        } else if (user.role === 'admin') {
            roleName = 'Administrator';
        } else if (user.role === 'member') {
            roleName = 'Członek';
        } else if (user.role === 'guest') {
            roleName = 'Gość';
        }
        roleCell.innerHTML = `<span class="display-value">${roleName}</span>`;
        row.appendChild(roleCell);

        // Actions
        const actionsCell = document.createElement('td');
        actionsCell.className = 'actions-cell';
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'action-buttons';
        
        // Delete button with X icon (cannot delete owner)
        if (user.role !== 'owner') {
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'icon-button delete-button confirm-delete-btn';
            deleteBtn.innerHTML = '✕';
            deleteBtn.title = user.role === 'admin' ? 'Usuń administratora' : 'Usuń użytkownika';
            deleteBtn.addEventListener('click', (e) => deleteUser(user.user_id, user.username, e));
            actionsDiv.appendChild(deleteBtn);
        } else {
            // Show info that owner cannot be deleted
            const ownerInfo = document.createElement('span');
            ownerInfo.style.fontSize = '11px';
            ownerInfo.style.color = '#999';
            ownerInfo.textContent = '(nie można usunąć)';
            actionsDiv.appendChild(ownerInfo);
        }

        actionsCell.appendChild(actionsDiv);
        row.appendChild(actionsCell);
        tableBody.appendChild(row);
    });
}

// Create confirmation button for delete actions
// Delete user flow with confirmation state
function deleteUser(user_id, username, event) {
    if (!user_id || !username) return;
    const button = event.target;
    
    // If already in confirm state, proceed with deletion
    if (button.classList.contains('confirm-state')) {
        button.textContent = 'Usuwanie...';
        button.disabled = true;
        performUserDeletion(user_id, username).finally(() => {
            button.classList.remove('confirm-state');
            button.textContent = '✕';
            button.title = 'Usuń użytkownika';
            button.disabled = false;
        });
        return;
    }
    
    // First click: show confirmation
    button.classList.add('confirm-state');
    button.textContent = '✓';
    button.title = 'Potwierdź usunięcie';
    
    // Auto-reset after 5 seconds
    const timeoutId = setTimeout(() => {
        if (button.classList.contains('confirm-state')) {
            button.classList.remove('confirm-state');
            button.textContent = '✕';
            button.title = 'Usuń użytkownika';
        }
    }, 5000);
    
    // Store timeout ID to clear it if confirmed before timeout
    button.dataset.timeoutId = timeoutId;
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

/* ============================== */
/*    Notification Management     */
/* ============================== */

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
    if (!tableBody) return;
    
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
        customSpan.style.width = '22px';
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

// Adding recipient with checkbox
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
        // fallback: leave empty select
    }
}

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
            const emailInput = document.getElementById('notificationRecipientEmail');
            const userSelect = document.getElementById('notificationRecipientUser');
            if (emailInput) emailInput.value = notificationRecipients[notificationRecipients.length-1].email;
            if (userSelect) userSelect.value = notificationRecipients[notificationRecipients.length-1].user;
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

/* ============================== */
/*     Dashboard Functions        */
/* ============================== */

// Functions for refreshing dashboard data
function refreshDeviceStates() {
    fetch('/api/admin/device-states')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('device-states');
            if (container) {
                container.innerHTML = '';
                data.forEach(device => {
                    const deviceItem = document.createElement('div');
                    deviceItem.className = 'device-item';
                    deviceItem.innerHTML = `
                        <span>${device.name} (${device.room})</span>
                        <span class="device-status ${device.state ? 'online' : 'offline'}">
                            ${device.state ? 'Włączone' : 'Wyłączone'}
                        </span>
                    `;
                    container.appendChild(deviceItem);
                });
            }
        })
        .catch(error => console.error('Error refreshing device states:', error));
}

function refreshLogs() {
    fetch('/api/admin/logs')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('logs-container');
            if (container) {
                container.innerHTML = '';
                data.forEach(log => {
                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';
                    logEntry.innerHTML = `
                        <span class="log-timestamp">${log.timestamp}</span>
                        <span class="log-level ${log.level}">${log.level.toUpperCase()}</span>
                        <span class="log-message">${log.message}</span>
                    `;
                    container.appendChild(logEntry);
                });
            }
        })
        .catch(error => console.error('Error refreshing logs:', error));
}

/* ============================== */
/*       Page Initialization      */
/* ============================== */

// Initialize dashboard page
function initDashboardPage() {
    // Initialize admin dashboard
    // Note: Access to /admin_dashboard is already protected by @admin_required decorator
    // so if this code runs, user definitely has admin access in current home
    loadUsers();
    initNotificationSettings();
    fillNotificationUserSelect();
}

// Add notification recipient
function addNotificationRecipient() {
    const email = document.getElementById('notificationRecipientEmail').value.trim();
    const user = document.getElementById('notificationRecipientUser').value;
    const enabled = getAddRecipientEnabledValue();
    
    if (!email || !user) {
        showNotification('Podaj email i wybierz użytkownika', 'error');
        return;
    }
    
    // If already exists such email+user, don't add duplicate
    if (notificationRecipients.some(r => r.email === email && r.user === user)) {
        showNotification('Taki odbiorca już istnieje', 'error');
        return;
    }
    
    notificationRecipients.push({ email, user, enabled });
    document.getElementById('notificationRecipientEmail').value = '';
    renderNotificationRecipients();
    saveNotificationRecipientsOnly().then(() => {
        loadNotificationSettings();
        showNotification('Odbiorca został dodany', 'success');
    });
}

// DOM Content Loaded Event
document.addEventListener('DOMContentLoaded', () => {
    // Only auto-initialize if not on admin dashboard (admin dashboard handles its own initialization)
    // Check for admin dashboard specific elements or data attributes
    const isAdminDashboard = document.querySelector('#stats-data') || 
                           window.preloadedUsers !== undefined || 
                           window.location.pathname.includes('/admin_dashboard');
    
    if (!isAdminDashboard) {
        initDashboardPage();
    }
    
    // Handle user form submission
    const userForm = document.querySelector('.user-form form');
    if (userForm) {
        userForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await addUser();
        });
    }
    
    // Handle add notification recipient button
    const addBtn = document.getElementById('addNotificationRecipientBtn');
    if (addBtn) {
        addBtn.addEventListener('click', addNotificationRecipient);
    }
});