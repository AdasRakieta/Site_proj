document.addEventListener('DOMContentLoaded', function () {
    loadRoomsAndButtons();
    if (window.app && app.socket) {
        app.socket.emit('get_button_states'); // Pobierz stany przycisków po załadowaniu strony
    }
});

function loadRoomsAndButtons() {
    if (!window.app) return;
    Promise.all([
        app.fetchData('/api/rooms'),
        app.fetchData('/api/buttons')
    ]).then(([rooms, buttons]) => {
        window.updateRoomsAndButtonsList(rooms, buttons);
    }).catch(error => console.error('Error:', error));
}

function toggleLight(room, buttonName, state) {
    if (window.app && app.socket && app.socket.connected) {
        // Primary method: Use WebSocket
        app.socket.emit('toggle_button', { 
            room: room, 
            name: buttonName, 
            state: state 
        });
    } else {
        // Fallback method: Use REST API
        console.log('WebSocket not available, using REST API fallback');
        toggleLightViaAPI(room, buttonName, state);
    }
}

async function toggleLightViaAPI(room, buttonName, state, attempt = 0) {
    try {
        const norm = v => (v||'').toLowerCase().trim();
        const buttons = await app.fetchData('/api/buttons');
        const roomNorm = norm(room);
        const nameNorm = norm(buttonName);
        const roomMatcher = b => norm(b?.room_name || b?.room);
        let button = Array.isArray(buttons) ? buttons.find(b => norm(b.name) === nameNorm && roomMatcher(b) === roomNorm) : null;
        if (!button && Array.isArray(buttons)) {
            const sameName = buttons.filter(b => norm(b.name) === nameNorm);
            if (sameName.length === 1) {
                button = sameName[0];
                console.warn('[fallback] Dopasowanie przycisku tylko po nazwie:', buttonName, room);
            }
        }
        if (!button) {
            if (attempt === 0) {
                console.warn('[retry] Button not found pierwsza próba, odświeżam i próbuję ponownie...', buttonName, room);
                await new Promise(r => setTimeout(r, 300));
                return toggleLightViaAPI(room, buttonName, state, attempt + 1);
            }
            console.error('Button not found po retry:', buttonName, 'room:', room);
            if (window.showNotification) window.showNotification('Nie znaleziono przycisku', 'error');
            return;
        }
        const response = await fetch(`/api/buttons/${button.id}/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
            body: JSON.stringify({ state })
        });
        const result = await response.json();
        if (result.status === 'success') {
            const switchElement = document.getElementById(`${buttonName.replace(/\s+/g, '_')}Switch`);
            if (switchElement) switchElement.checked = state;
            if (window.showNotification) window.showNotification(`${buttonName} ${state ? 'włączony' : 'wyłączony'}`, 'success');
        } else {
            console.error('Failed to toggle button:', result.message);
            if (window.showNotification) window.showNotification('Błąd przełączania przycisku: ' + result.message, 'error');
        }
    } catch (error) {
        if (attempt === 0) {
            console.warn('[retry] Error przy toggle, druga próba...', error);
            await new Promise(r => setTimeout(r, 300));
            return toggleLightViaAPI(room, buttonName, state, attempt + 1);
        }
        console.error('Error toggling light via API:', error);
        if (window.showNotification) window.showNotification('Błąd przełączania przycisku', 'error');
    }
}

// Helper function to get CSRF token
function getCSRFToken() {
    // Użyj globalnej funkcji jeśli istnieje
    if (window.getCSRFToken && typeof window.getCSRFToken === 'function') {
        // Unikaj rekursji - sprawdź czy to nie ta sama funkcja
        if (window.getCSRFToken !== getCSRFToken) {
            return window.getCSRFToken();
        }
    }
    
    let token = null;
    // Check meta tag first
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) token = meta.getAttribute('content');
    
    // Then check hidden input (nowa nazwa)
    if (!token) {
        const input = document.querySelector('input[name="csrf_token"]');
        if (input) token = input.value;
    }
    
    // Fallback do starej nazwy
    if (!token) {
        const oldInput = document.querySelector('input[name="_csrf_token"]');
        if (oldInput) token = oldInput.value;
    }
    
    // Finally check global variable
    if (!token && window.csrf_token) {
        token = window.csrf_token;
    }
    
    return token;
}
window.toggleLight = toggleLight;

if (window.app) {
    app.onRoomsUpdate = function(rooms) {
        app.fetchData('/api/buttons')
            .then(buttons => {
                window.updateRoomsAndButtonsList(rooms, buttons);
            })
            .catch(error => console.error('Error:', error));
    };
    app.onButtonsUpdate = function(buttons) {
        app.fetchData('/api/rooms')
            .then(rooms => {
                window.updateRoomsAndButtonsList(rooms, buttons);
            })
            .catch(error => console.error('Error:', error));
    };
    app.onButtonStatesSync = function(states) {
        for (const [key, state] of Object.entries(states)) {
            const switchElement = document.getElementById(`${key.replace(/\s+/g, '_')}Switch`);
            if (switchElement) {
                switchElement.checked = state;
            }
        }
    };
}