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

function formatTimestamp(ts) {
    try {
        if (!ts) return '';
        const d = new Date(ts);
        if (!isNaN(d)) {
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const hh = String(d.getHours()).padStart(2, '0');
            const mm = String(d.getMinutes()).padStart(2, '0');
            return `${y}-${m}-${day} ${hh}:${mm}`;
        }
    } catch (e) {}
    if (typeof ts === 'string') {
        const m = ts.match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})/);
        if (m) return `${m[1]} ${m[2]}`;
    }
    return String(ts);
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
                        <span class="log-timestamp">${formatTimestamp(log.timestamp)}</span>
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

/* ============================== */
/*    Log Management Functions    */
/* ============================== */

function showLogManagement() {
    const panel = document.getElementById('log-management-panel');
    if (panel) {
        panel.style.display = 'block';
    }
}

function hideLogManagement() {
    const panel = document.getElementById('log-management-panel');
    if (panel) {
        panel.style.display = 'none';
    }
    
    // Reset all confirmation states
    const confirmButtons = document.querySelectorAll('.confirm-delete-btn.confirm-state');
    confirmButtons.forEach(btn => {
        btn.classList.remove('confirm-state');
        const textSpan = btn.querySelector('span');
        if (btn.id === 'delete-days-btn') {
            textSpan.textContent = 'Usuń';
        } else if (btn.id === 'delete-range-btn') {
            textSpan.textContent = 'Usuń';
        } else if (btn.id === 'clear-all-btn') {
            textSpan.textContent = 'Wyczyść wszystkie logi';
        }
    });
}

function confirmDeleteByDays(event) {
    const button = event.currentTarget;
    const buttonText = document.getElementById('delete-days-text');
    const days = document.getElementById('delete-days').value;
    
    if (!days || days < 1) {
        showNotification('Podaj poprawną liczbę dni', 'error');
        return;
    }
    
    if (button.classList.contains('confirm-state')) {
        button.disabled = true;
        buttonText.textContent = 'Usuwanie...';
        
        fetch('/api/admin/logs/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
            },
            body: JSON.stringify({ days: parseInt(days) })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showNotification(data.message, 'success');
                refreshLogs(true);
                hideLogManagement();
            } else {
                showNotification('Błąd: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting logs:', error);
            showNotification('Błąd podczas usuwania logów', 'error');
        })
        .finally(() => {
            button.disabled = false;
            buttonText.textContent = 'Usuń';
            button.classList.remove('confirm-state');
        });
    } else {
        button.classList.add('confirm-state');
        buttonText.textContent = '✓ Potwierdź usunięcie';
        setTimeout(() => {
            if (button.classList.contains('confirm-state')) {
                button.classList.remove('confirm-state');
                buttonText.textContent = 'Usuń';
            }
        }, 5000);
    }
}

function confirmDeleteByRange(event) {
    const button = event.currentTarget;
    const buttonText = document.getElementById('delete-range-text');
    const startDate = document.getElementById('delete-start-date').value;
    const endDate = document.getElementById('delete-end-date').value;
    
    if (!startDate && !endDate) {
        showNotification('Podaj co najmniej jedną datę', 'error');
        return;
    }
    
    if (button.classList.contains('confirm-state')) {
        button.disabled = true;
        buttonText.textContent = 'Usuwanie...';
        
        const requestData = {};
        if (startDate) requestData.start_date = startDate;
        if (endDate) requestData.end_date = endDate;
        
        fetch('/api/admin/logs/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showNotification(data.message, 'success');
                refreshLogs(true);
                hideLogManagement();
            } else {
                showNotification('Błąd: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting logs:', error);
            showNotification('Błąd podczas usuwania logów', 'error');
        })
        .finally(() => {
            button.disabled = false;
            buttonText.textContent = 'Usuń';
            button.classList.remove('confirm-state');
        });
    } else {
        button.classList.add('confirm-state');
        buttonText.textContent = '✓ Potwierdź usunięcie';
        setTimeout(() => {
            if (button.classList.contains('confirm-state')) {
                button.classList.remove('confirm-state');
                buttonText.textContent = 'Usuń';
            }
        }, 5000);
    }
}

function confirmClearAll(event) {
    const button = event.currentTarget;
    const buttonText = document.getElementById('clear-all-text');
    
    if (button.classList.contains('confirm-state')) {
        button.disabled = true;
        buttonText.textContent = 'Usuwanie...';
        
        fetch('/api/admin/logs/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]').getAttribute('content')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showNotification(data.message, 'success');
                refreshLogs(true);
                hideLogManagement();
            } else {
                showNotification('Błąd: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error clearing logs:', error);
            showNotification('Błąd podczas czyszczenia logów', 'error');
        })
        .finally(() => {
            button.disabled = false;
            buttonText.textContent = 'Wyczyść wszystkie logi';
            button.classList.remove('confirm-state');
        });
    } else {
        button.classList.add('confirm-state');
        buttonText.textContent = '✓ Potwierdź wyczyszczenie';
        setTimeout(() => {
            if (button.classList.contains('confirm-state')) {
                button.classList.remove('confirm-state');
                buttonText.textContent = 'Wyczyść wszystkie logi';
            }
        }, 5000);
    }
}

/* ============================== */
/*   Dashboard Data Functions     */
/* ============================== */

// Global variables for preloaded data
window.preloadedDeviceStates = null;
window.preloadedManagementLogs = null;
window.preloadedUsers = null;

// Helper to read embedded JSON
const __getEmbeddedJSON = (id) => {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch { return null; }
};

// Initialize preloaded data on page load
function initPreloadedData() {
    if (typeof window.preloadedDeviceStates === 'undefined') {
        window.preloadedDeviceStates = __getEmbeddedJSON('preloadedDeviceStates');
    }
    if (typeof window.preloadedManagementLogs === 'undefined') {
        window.preloadedManagementLogs = __getEmbeddedJSON('preloadedManagementLogs');
    }
    if (typeof window.preloadedUsers === 'undefined') {
        window.preloadedUsers = __getEmbeddedJSON('preloadedUsers');
    }
}

function refreshDeviceStates(forceRefresh = false) {
    // Use pre-loaded data on initial load, fetch from API only on manual refresh
    if (!forceRefresh && window.preloadedDeviceStates && window.preloadedDeviceStates.length > 0) {
        console.log('Using pre-loaded device states data');
        updateDeviceStatesDisplay(window.preloadedDeviceStates);
        window.preloadedDeviceStates = null;
        return;
    }
    
    console.log('Fetching device states from API');
    fetch('/api/admin/device-states')
        .then(response => response.json())
        .then(data => updateDeviceStatesDisplay(data))
        .catch(error => console.error('Error refreshing device states:', error));
}

function updateDeviceStatesDisplay(data) {
    const container = document.getElementById('device-states');
    if (!container) return;
    
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

function refreshLogs(forceRefresh = false) {
    // Use pre-loaded data on initial load, fetch from API only on manual refresh
    if (!forceRefresh && window.preloadedManagementLogs && window.preloadedManagementLogs.length > 0) {
        console.log('Using pre-loaded management logs data');
        updateLogsDisplay(window.preloadedManagementLogs);
        window.preloadedManagementLogs = null;
        return;
    }
    
    console.log('Fetching logs from API');
    fetch('/api/admin/logs')
        .then(response => response.json())
        .then(data => updateLogsDisplay(data))
        .catch(error => console.error('Error refreshing logs:', error));
}

function updateLogsDisplay(data) {
    const container = document.getElementById('logs-container');
    if (!container) return;
    
    container.innerHTML = '';
    data.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="log-timestamp">${formatTimestamp(log.timestamp)}</span>
            <span class="log-level ${log.level}">${log.level.toUpperCase()}</span>
            <span class="log-message">${log.message}</span>
        `;
        container.appendChild(logEntry);
    });
}

/* ============================== */
/*      Chart Functions           */
/* ============================== */

function createEnergyChart() {
    const canvas = document.getElementById('energyChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Simulated energy usage data (last 7 days)
    const data = [12, 19, 8, 15, 25, 18, 22];
    const labels = ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'Sb', 'Nd'];
    
    const maxValue = Math.max(...data);
    const chartHeight = canvas.height - 40;
    const chartWidth = canvas.width - 40;
    const barWidth = chartWidth / data.length;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw bars
    ctx.fillStyle = '#4CAF50';
    data.forEach((value, index) => {
        const barHeight = (value / maxValue) * chartHeight;
        const x = 20 + index * barWidth;
        const y = canvas.height - 20 - barHeight;
        
        ctx.fillRect(x + 5, y, barWidth - 10, barHeight);
        
        // Labels
        ctx.fillStyle = '#666';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(labels[index], x + barWidth/2, canvas.height - 5);
        ctx.fillText(value + 'kWh', x + barWidth/2, y - 5);
        ctx.fillStyle = '#4CAF50';
    });
}

function createAutomationChart() {
    const canvas = document.getElementById('automationChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    const statsElement = document.getElementById('stats-data');
    const total = parseInt(statsElement?.dataset.automationsToday) || 0;
    const errors = parseInt(statsElement?.dataset.automationErrors) || 0;
    const successful = total - errors;
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 60;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (total > 0) {
        // Successful executions
        const successAngle = (successful / total) * 2 * Math.PI;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, successAngle);
        ctx.lineTo(centerX, centerY);
        ctx.fillStyle = '#4CAF50';
        ctx.fill();
        
        // Errors
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, successAngle, 2 * Math.PI);
        ctx.lineTo(centerX, centerY);
        ctx.fillStyle = '#f44336';
        ctx.fill();
        
        // Label
        ctx.fillStyle = '#333';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(`${successful}/${total}`, centerX, centerY);
    } else {
        ctx.fillStyle = '#ccc';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Brak danych', centerX, centerY);
    }
}

/* ============================== */
/*   Invitation Management        */
/* ============================== */

function loadPendingInvitations() {
    const homeIdElement = document.getElementById('dashboard-home-id');
    const homeId = homeIdElement?.dataset.homeId;
    if (!homeId) return;
    
    fetch(`/api/home/${homeId}/invitations`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                displayPendingInvitations(result.invitations);
            }
        })
        .catch(error => {
            console.error('Error loading invitations:', error);
        });
}

function displayPendingInvitations(invitations) {
    const container = document.getElementById('pendingInvitationsContainer');
    if (!container) return;
    
    if (!invitations || invitations.length === 0) {
        container.innerHTML = '<p style="color: #999; font-style: italic; padding: 10px;">Brak oczekujących zaproszeń</p>';
        return;
    }
    
    container.innerHTML = invitations.map(inv => `
        <div style="padding: 10px; margin: 5px 0; background: var(--bg-secondary); border-radius: 5px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>${inv.email}</strong>
                <span style="color: #999; font-size: 12px; margin-left: 10px;">
                    ${inv.role === 'admin' ? 'Administrator' : inv.role === 'member' ? 'Członek' : 'Gość'}
                </span>
                <br>
                <span style="font-size: 11px; color: #777;">
                    Kod: ${inv.invitation_code} | Wygasa: ${new Date(inv.expires_at).toLocaleDateString()}
                </span>
            </div>
            <button onclick="cancelInvitation(event, '${inv.id}')" 
                    class="confirm-delete-btn" 
                    style="padding: 5px 10px;">
                <span class="cancel-text-${inv.id}">Anuluj</span>
            </button>
        </div>
    `).join('');
}

function cancelInvitation(event, invitationId) {
    const button = event.currentTarget;
    const buttonText = button.querySelector(`.cancel-text-${invitationId}`);
    
    if (button.classList.contains('confirm-state')) {
        button.disabled = true;
        buttonText.textContent = 'Anulowanie...';
        
        const homeIdElement = document.getElementById('dashboard-home-id');
        const homeId = homeIdElement?.dataset.homeId;
        
        fetch(`/api/home/${homeId}/invitations/${invitationId}/cancel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showNotification('Zaproszenie anulowane', 'success');
                loadPendingInvitations();
            } else {
                showNotification(result.error || 'Błąd podczas anulowania', 'error');
                button.disabled = false;
                buttonText.textContent = 'Anuluj';
                button.classList.remove('confirm-state');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Błąd podczas anulowania zaproszenia', 'error');
            button.disabled = false;
            buttonText.textContent = 'Anuluj';
            button.classList.remove('confirm-state');
        });
    } else {
        button.classList.add('confirm-state');
        buttonText.textContent = '✓ Potwierdź anulowanie';
        setTimeout(() => {
            if (button.classList.contains('confirm-state')) {
                button.classList.remove('confirm-state');
                buttonText.textContent = 'Anuluj';
            }
        }, 5000);
    }
}

/* ============================== */
/*  Admin Dashboard Init          */
/* ============================== */

// Safely prime users table from preloaded data
function primeUsersFromPreload() {
    if (window.preloadedUsers && Array.isArray(window.preloadedUsers) && window.preloadedUsers.length > 0) {
        console.log('Priming users table with pre-loaded users data');
        if (typeof updateUsersTable === 'function') {
            updateUsersTable(window.preloadedUsers);
            if (typeof notificationUsersList !== 'undefined') {
                notificationUsersList = window.preloadedUsers;
            }
            if (typeof fillNotificationUserSelect === 'function') {
                fillNotificationUserSelect();
            }
        }
        window.preloadedUsers = null;
        return true;
    }
    return false;
}

// Initialize admin dashboard specific features
function initAdminDashboard() {
    console.log('Initializing admin dashboard');
    
    // Initialize preloaded data
    initPreloadedData();
    
    // Initialize charts
    createEnergyChart();
    createAutomationChart();
    
    // Use pre-loaded data for initial rendering
    refreshDeviceStates(false);
    refreshLogs(false);
    primeUsersFromPreload();
    
    // Initialize dashboard page
    if (typeof initDashboardPage === 'function') {
        initDashboardPage();
    }
    
    // Auto-refresh every 30 seconds (force refresh to get latest data)
    setInterval(() => {
        refreshDeviceStates(true);
        refreshLogs(true);
    }, 30000);
    
    // Load pending invitations
    loadPendingInvitations();
    
    // Setup Socket.IO for real-time updates
    setupSocketIO();
}

function setupSocketIO() {
    if (typeof io === 'undefined') return;
    
    const socket = io();
    const homeIdElement = document.getElementById('dashboard-home-id');
    const currentHomeId = homeIdElement?.dataset.homeId;
    
    socket.on('user_joined', function(data) {
        console.log('User joined event received:', data);
        
        if (data.home_id === currentHomeId) {
            console.log('Refreshing user list after user joined');
            if (typeof loadUsers === 'function') {
                loadUsers();
            }
            loadPendingInvitations();
        }
    });
}

// Initialize when DOM is ready (only for admin dashboard)
document.addEventListener('DOMContentLoaded', function() {
    const isAdminDashboard = document.querySelector('#stats-data') || 
                           window.preloadedUsers !== undefined || 
                           window.location.pathname.includes('/admin_dashboard');
    
    if (isAdminDashboard) {
        initAdminDashboard();
    }
});