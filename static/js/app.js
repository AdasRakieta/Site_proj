// Helpery do normalizacji danych pokoi niezależnie od formatu API
function normalizeRoomsData(payload) {
    const source = payload && typeof payload === 'object' && Array.isArray(payload.data)
        ? payload.data
        : payload;

    if (!Array.isArray(source)) {
        return [];
    }

    return source
        .map((room, index) => {
            if (!room) return null;

            if (typeof room === 'string') {
                return {
                    id: room,
                    name: room,
                    description: null,
                    display_order: index,
                    home_id: null
                };
            }

            const name = room.name || room.room || room.title;
            if (!name) {
                return null;
            }

            const id = room.id ?? room.room_id ?? room.uuid ?? name;

            return {
                id: id != null ? String(id) : String(name),
                name: String(name),
                description: room.description ?? null,
                display_order: room.display_order != null ? room.display_order : index,
                home_id: room.home_id != null ? String(room.home_id) : null
            };
        })
        .filter(Boolean)
        .sort((a, b) => {
            const orderDiff = (a.display_order ?? 0) - (b.display_order ?? 0);
            if (orderDiff !== 0) return orderDiff;
            return a.name.localeCompare(b.name, 'pl');
        });
}

function extractRoomNames(payload) {
    return normalizeRoomsData(payload).map(room => room.name);
}

window.normalizeRoomsData = normalizeRoomsData;
window.extractRoomNames = extractRoomNames;

// Aplikacja SmartHomeApp

class SmartHomeApp {
    constructor() {
        console.log('Inicjalizacja SmartHomeApp');
        try {
            this.socket = typeof io !== 'undefined' ? io() : {
                on: () => console.warn('Socket.IO nie jest dostępny'),
                emit: () => console.warn('Socket.IO nie jest dostępny'),
                disconnect: () => {}
            };
            console.log('Socket.IO zainicjalizowany');
        } catch (error) {
            console.error('Błąd inicjalizacji Socket.IO:', error);
            this.socket = {
                on: () => console.warn('Socket.IO nie jest dostępny (try-catch)'),
                emit: () => console.warn('Socket.IO nie jest dostępny (try-catch)'),
                disconnect: () => {}
            };
        }
        
        // Inicjalizacja AutomationsManager
        this.automations = new AutomationsManager(this);
        
        this.initTheme();
        this.initMenu();
        this.bindSocketEvents();
        this.bindMenuEvents();
        this.map = null;
        this.mapInitialized = false;
    this.currentHomeId = window.currentHomeId || null;
        this.showNotification = this.showNotification.bind(this);
        this.rooms = null; // cache na listę pokoi
        console.log('SmartHomeApp gotowy');
    }

    async fetchInitialData() {
        try {
            const buttonsData = await this.fetchData('/api/buttons');
            if (buttonsData && Array.isArray(buttonsData)) {
                this.buttons = buttonsData;
            }
        } catch (error) {
            console.error('Błąd ładowania przycisków:', error);
        }
    }

    async getRooms(force = false) {
        if (!force && Array.isArray(this.rooms) && this.rooms.length > 0) {
            return this.rooms;
        }
        try {
            const response = await this.fetchData('/api/rooms');
            const normalizedRooms = normalizeRoomsData(response);
            if (response && typeof response === 'object' && response.meta && response.meta.home_id) {
                this.currentHomeId = response.meta.home_id;
            }
            this.rooms = normalizedRooms;
            return normalizedRooms;
        } catch (e) {
            return [];
        }
    }

    initMap() {
        if (this.mapInitialized || !document.getElementById('map')) return;
        const homeCoords = [52.4012124, 16.860299];
        const gymCoords = [52.39700434367431, 16.859041122186433];
        const studyCoords = [52.408577733383154, 16.89017620899486];
        const workCoords = [52.407238, 16.7850388];

        this.map = L.map('map').setView(homeCoords, 15);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);

        L.marker(homeCoords).addTo(this.map).bindPopup("<b>Nasz dom</b>").openPopup();
        L.marker(gymCoords).addTo(this.map).bindPopup("<b>Nasza siłka</b>");
        L.marker(studyCoords).addTo(this.map).bindPopup("<b>Miejsce tortur 1.</b>");
        L.marker(workCoords).addTo(this.map).bindPopup("<b>Miejsce tortur 2.</b>");

        this.mapInitialized = true;
    }

    toggleMap() {
        const mapContainer = document.getElementById('map-container');
        const toggleBtn = document.getElementById('toggleMap');
        if (!mapContainer || !toggleBtn) return;

        if (mapContainer.style.display === 'none') {
            mapContainer.style.display = 'block';
            toggleBtn.textContent = 'Ukryj mapę';
            if (!this.mapInitialized) {
                this.loadLeaflet().then(() => this.initMap());
            }
        } else {
            mapContainer.style.display = 'none';
            toggleBtn.textContent = 'Pokaż mapę';
        }
    }

    loadLeaflet() {
        return new Promise((resolve, reject) => {
            if (typeof L !== 'undefined') {
                resolve();
                return;
            }
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            css.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
            css.crossOrigin = '';
            document.head.appendChild(css);

            const js = document.createElement('script');
            js.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
            js.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
            js.crossOrigin = '';
            js.onload = resolve;
            js.onerror = reject;
            document.head.appendChild(js);
        });
    }

    initTheme() {
        this.savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', this.savedTheme);
        // Ustaw ikony natychmiast po załadowaniu motywu, zanim pojawi się DOMContentLoaded
        this.setInitialMenuIcons(this.savedTheme);
        this.updateMenuIcons(this.savedTheme);
        this.updateSideMenuIcons(this.savedTheme);
    }

    setInitialMenuIcons(theme) {
        // Ustaw src ikon menu bocznego zgodnie z motywem już na starcie
        const iconMap = {
            'menu-icon': 'menu_icon',
            'menu-icon-side': 'menu_icon',
            'home-icon': 'home_icon',
            'lights-icon': 'lights_icon',
            'temperature-icon': 'temperature_icon',
            'security-icon': 'security_icon',
            'settings-icon': 'settings_icon',
            'dashboard-icon': 'settings_icon',
            'automations-icon': 'automations_icon',
            'edit-icon': 'edit_icon',
            'user-menu-settings-icon': 'settings_icon',
            'user-menu-user-icon': 'user_icon'
        };
        Object.entries(iconMap).forEach(([id, name]) => {
            const el = document.getElementById(id);
            if (el) {
                el.src = `/static/icons/${name}_${theme}.png`;
            }
        });
    }

    changeTheme(theme) {
        console.log('Zmiana motywu na:', theme);
        this.savedTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.updateMenuIcons(theme);
        this.updateSideMenuIcons(theme);
    }

    updateMenuIcons(theme) {
        const iconSrc = theme === 'dark' 
            ? "/static/icons/menu_icon_dark.png" 
            : "/static/icons/menu_icon_light.png";
        [document.getElementById('menu-icon'), 
         document.getElementById('menu-icon-side'),
         document.getElementById('menu-icon-header')]
            .filter(Boolean)
            .forEach(el => el.src = iconSrc);
    }

    updateSideMenuIcons(theme) {
        const iconMap = {
            'home-icon': 'home_icon',
            'lights-icon': 'lights_icon',
            'temperature-icon': 'temperature_icon',
            'security-icon': 'security_icon',
            'settings-icon': 'settings_icon',
            'dashboard-icon': 'settings_icon',
            'automations-icon': 'automations_icon',
            'edit-icon': 'edit_icon',
            'user-menu-settings-icon': 'settings_icon',
            'user-menu-user-icon': 'user_icon'
        };
        Object.entries(iconMap).forEach(([id, name]) => {
            const element = document.getElementById(id);
            if (element) {
                element.src = theme === 'dark' 
                    ? `/static/icons/${name}_dark.png` 
                    : `/static/icons/${name}_light.png`;
            }
        });
    }

    initMenu() {
        this.sideMenu = document.getElementById('sideMenu');
        if (this.sideMenu) {
            this.sideMenu.style.left = '-260px';
            this.sideMenu.style.transition = 'left 0.3s ease-in-out';
        }
    }

    bindMenuEvents() {
        document.querySelectorAll('.close-btn').forEach(button => {
            button.addEventListener('click', () => this.toggleMenu());
        });
        const toggleMapBtn = document.getElementById('toggleMap');
        if (toggleMapBtn) {
            toggleMapBtn.addEventListener('click', () => this.toggleMap());
        }
    }

    toggleMenu() {
        if (!this.sideMenu) {
            console.warn('Menu boczne nie zostało znalezione');
            return;
        }
        const isVisible = this.sideMenu.style.left === '0px';
        this.sideMenu.style.left = isVisible ? '-260px' : '0px';
    }

    bindSocketEvents() {
        if (!this.socket) {
            console.warn('Socket.IO nie jest dostępny - pomijanie bindSocketEvents');
            return;
        }
        const events = {
            'update_rooms': 'onRoomsUpdate',
            'update_buttons': 'onButtonsUpdate',
            'update_temperature_controls': 'onTemperatureControlsUpdate',
            'sync_button_states': 'onButtonStatesSync',
            'update_security_state': 'onSecurityStateUpdate',
            'update_automations': data => this.automations.onAutomationsUpdate(data)
        };
        Object.entries(events).forEach(([event, handler]) => {
            this.socket.on(event, (data) => {
                if (typeof handler === 'function') {
                    handler(data);
                } else if (this[handler]) {
                    this[handler](data);
                } else {
                    console.warn(`Brak handlera dla eventu ${event}`);
                }
            });
        });
        // --- DODANE: nasłuchiwanie na update_button i aktualizacja switcha na stronie ---
        this.socket.on('update_button', (data) => {
            // Obsługa dla lights.html, room.html i innych stron z przełącznikami
            // Zakładamy id w formacie: `${room}_${name}Switch` lub `${name}Switch`
            let switchId = `${data.room}_${data.name.replace(/\s+/g, '_')}Switch`;
            let switchElement = document.getElementById(switchId);
            if (!switchElement) {
                // Spróbuj bez room (np. w room.html)
                switchId = `${data.name.replace(/\s+/g, '_')}Switch`;
                switchElement = document.getElementById(switchId);
            }
            if (switchElement) {
                switchElement.checked = data.state;
            }
        });
        // Dodaj obsługę update_rooms do cache
        this.socket.on('update_rooms', (roomsPayload) => {
            if (roomsPayload && typeof roomsPayload === 'object' && roomsPayload.meta && roomsPayload.meta.home_id) {
                this.currentHomeId = roomsPayload.meta.home_id;
            }
            const normalizedRooms = normalizeRoomsData(roomsPayload);
            this.rooms = normalizedRooms;
            if (typeof this.onRoomsUpdate === 'function') {
                this.onRoomsUpdate(normalizedRooms);
            }
        });
        
        // Dodaj obsługę update_buttons
        this.socket.on('update_buttons', (buttons) => {
            if (typeof this.onButtonsUpdate === 'function') {
                this.onButtonsUpdate(buttons);
            }
        });
        
        // Dodaj obsługę update_temperature_controls
        this.socket.on('update_temperature_controls', (controls) => {
            if (typeof this.onTemperatureControlsUpdate === 'function') {
                this.onTemperatureControlsUpdate(controls);
            }
        });
    }

    async fetchData(url) {
        try {
            const response = await fetch(url, {
                headers: { 'X-CSRFToken': getCSRFToken() }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Błąd fetchData:', error);
            return { status: 'error', message: error.message };
        }
    }

    async postData(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Błąd postData:', error);
            return { status: 'error', message: error.message };
        }
    }

    async deleteData(url) {
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCSRFToken() }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Błąd deleteData:', error);
            return { status: 'error', message: error.message };
        }
    }

    async putData(url, data) {
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Błąd putData:', error);
            return { status: 'error', message: error.message };
        }
    }

    createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'class') {
                element.className = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else {
                element.setAttribute(key, value);
            }
        });
        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else {
                element.appendChild(child);
            }
        });
        return element;
    }

    checkAuth() {
        this.socket.on('auth_required', () => {
            window.location.href = '/login';
        });
    }

    disconnect() {
        if (this.socket && this.socket.disconnect) {
            this.socket.disconnect();
        }
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notifications-container') || document.body;
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `<span>${message}</span><button class="notification-close" title="Zamknij">&times;</button>`;
        notification.style.opacity = '0';
        notification.querySelector('.notification-close').onclick = () => notification.remove();
        container.appendChild(notification);
        // Animacja pojawiania się
        setTimeout(() => {
            notification.style.opacity = '1';
        }, 10);
        // Automatyczne zniknięcie po 5 sekundach
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }

    onSecurityStateUpdate(data) {
        /**
         * Handle security state updates from the backend
         * @param {Object} data - Security state data from backend
         * @param {string} data.state - Security state ("Załączony" or "Wyłączony")
         */
        console.log('Global security state update received:', data);

        const eventHomeId = data && typeof data === 'object' ? data.home_id ?? null : null;
        if (this.currentHomeId && eventHomeId && String(eventHomeId) !== String(this.currentHomeId)) {
            console.log('Ignoring security update for different home', eventHomeId, this.currentHomeId);
            return;
        }
        
        // Update main status element if it exists
        const statusElement = document.getElementById('securityStatus');
        const statusValueElement = document.getElementById('statusValue');
        
        if (data && data.state) {
            // Update the status text
            if (statusValueElement) {
                statusValueElement.textContent = data.state;
            } else if (statusElement) {
                statusElement.textContent = `Aktualny status: ${data.state}`;
            }
            
            // Update visual feedback based on state
            if (statusElement) {
                statusElement.classList.remove('active', 'inactive', 'unknown');
                if (data.state === 'Załączony') {
                    statusElement.classList.add('active');
                } else if (data.state === 'Wyłączony') {
                    statusElement.classList.add('inactive');
                } else {
                    statusElement.classList.add('unknown');
                }
            }
        }
    }
    
    // Event handlers for Socket.IO updates
    onButtonsUpdate(buttons) {
        // Default handler for buttons update - can be overridden by specific pages
        console.log('Buttons updated:', buttons);
        // Trigger kanban refresh if available
        if (typeof window.loadKanban === 'function') {
            window.loadKanban();
        }
    }

    onButtonStatesSync(states) {
        if (!states || typeof states !== 'object') {
            console.warn('Nieprawidłowe dane sync_button_states:', states);
            return;
        }

        Object.entries(states).forEach(([key, state]) => {
            if (!key) return;
            const normalizedKey = String(key).replace(/\s+/g, '_');
            const switchId = `${normalizedKey}Switch`;
            const switchElement = document.getElementById(switchId) || document.getElementById(normalizedKey);
            if (switchElement && 'checked' in switchElement) {
                switchElement.checked = !!state;
            }
        });
    }
    
    onTemperatureControlsUpdate(controls) {
        // Default handler for temperature controls update - can be overridden by specific pages
        console.log('Temperature controls updated:', controls);
        // Trigger kanban refresh if available
        if (typeof window.loadKanban === 'function') {
            window.loadKanban();
        }
    }
}

function getCSRFToken() {
    // Pobierz token CSRF z ciasteczka lub z meta-tag (jeśli dodasz do base.html)
    // Tu pobieramy z sesji przez szablon lub z inputa, jeśli jest na stronie
    let token = null;
    const input = document.querySelector('input[name="_csrf_token"]');
    if (input) token = input.value;
    if (!token && window.csrf_token) token = window.csrf_token;
    return token;
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notifications-container') || document.body;
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `<span>${message}</span><button class="notification-close" title="Zamknij">&times;</button>`;
    notification.style.opacity = '0';
    notification.querySelector('.notification-close').onclick = () => notification.remove();
    container.appendChild(notification);
    // Animacja pojawiania się
    setTimeout(() => {
        notification.style.opacity = '1';
    }, 10);
    // Automatyczne zniknięcie po 5 sekundach
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

window.showNotification = showNotification;

// Funkcja do aktualizacji listy pokoi i przycisków (przeniesiona z lights.js)
window.updateRoomsAndButtonsList = function(rooms, buttons) {
    const container = document.getElementById("roomsAndButtonsList");
    if (!container) return;
    container.innerHTML = "";
    const normalizedRooms = window.normalizeRoomsData ? window.normalizeRoomsData(rooms) : [];
    const normalizedButtons = (buttons && Array.isArray(buttons.data)) ? buttons.data : (Array.isArray(buttons) ? buttons : []);
    const preparedButtons = normalizedButtons.map(button => {
        const mapped = { ...button };
        if (!mapped.room_name) {
            mapped.room_name = mapped.room || null;
        }
        if (mapped.room_id != null) {
            mapped.room_id = String(mapped.room_id);
        } else if (mapped.room && typeof mapped.room === 'object' && mapped.room.id != null) {
            mapped.room_id = String(mapped.room.id);
        } else {
            mapped.room_id = null;
        }
        return mapped;
    });

    const matchedButtonKeys = new Set();
    const buttonKey = (button) => {
        if (!button) return null;
        if (button.id != null) {
            return `id:${button.id}`;
        }
        const roomPart = button.room_name || 'null';
        return `name:${button.name}|room:${roomPart}`;
    };

    normalizedRooms.forEach((room) => {
        const roomName = room && room.name ? room.name : String(room || '');
        const roomId = room && room.id != null ? String(room.id) : null;
        if (!roomName && !roomId) {
            return;
        }
        const roomContainer = document.createElement("div");
        roomContainer.classList.add("lights-container");
        const roomHeader = document.createElement("h2");
        roomHeader.textContent = `${roomName || 'Nieprzypisane'}:`;
        roomContainer.appendChild(roomHeader);
        const buttonsContainer = document.createElement("div");
        buttonsContainer.classList.add("center-container");
        const roomButtons = preparedButtons.filter(button => {
            const matchesId = roomId && button.room_id && button.room_id === roomId;
            const matchesName = roomName && button.room_name && button.room_name === roomName;
            return matchesId || matchesName;
        });
        roomButtons.forEach(button => {
            const key = buttonKey(button);
            if (key) {
                matchedButtonKeys.add(key);
            }
            const buttonName = document.createElement("div");
            buttonName.textContent = button.name;
            buttonName.className = "light-button-label";
            buttonsContainer.appendChild(buttonName);
            const switchLabel = document.createElement("label");
            switchLabel.classList.add("switch");
            const switchInput = document.createElement("input");
            switchInput.type = "checkbox";
            const roomKey = (roomId || roomName || 'unassigned').toString().replace(/\s+/g, '_');
            switchInput.id = `${roomKey}_${button.name.replace(/\s+/g, '_')}Switch`;
            switchInput.checked = button.state;
            switchInput.addEventListener('change', function() {
                const targetRoom = button.room_name || roomName || null;
                if (window.toggleLight) window.toggleLight(targetRoom, button.name, this.checked);
            });
            const switchSlider = document.createElement("span");
            switchSlider.classList.add("slider");
            switchLabel.appendChild(switchInput);
            switchLabel.appendChild(switchSlider);
            buttonsContainer.appendChild(switchLabel);
        });
        roomContainer.appendChild(buttonsContainer);
        container.appendChild(roomContainer);
    });

    const unassignedButtons = preparedButtons.filter(button => {
        const key = buttonKey(button);
        return key && !matchedButtonKeys.has(key);
    });

    if (unassignedButtons.length > 0) {
        const roomContainer = document.createElement("div");
        roomContainer.classList.add("lights-container");
        const roomHeader = document.createElement("h2");
        roomHeader.textContent = "Nieprzypisane:";
        roomContainer.appendChild(roomHeader);
        const buttonsContainer = document.createElement("div");
        buttonsContainer.classList.add("center-container");

        unassignedButtons.forEach(button => {
            const buttonName = document.createElement("div");
            buttonName.textContent = button.name;
            buttonName.className = "light-button-label";
            buttonsContainer.appendChild(buttonName);

            const switchLabel = document.createElement("label");
            switchLabel.classList.add("switch");
            const switchInput = document.createElement("input");
            switchInput.type = "checkbox";
            const targetRoom = button.room_name || (typeof button.room === 'string' ? button.room : null) || 'Nieprzypisane';
            const roomKey = (button.room_id || targetRoom || 'unassigned').toString().replace(/\s+/g, '_');
            switchInput.id = `${roomKey}_${button.name.replace(/\s+/g, '_')}Switch`;
            switchInput.checked = button.state;
            switchInput.addEventListener('change', function() {
                if (window.toggleLight) window.toggleLight(targetRoom, button.name, this.checked);
            });
            const switchSlider = document.createElement("span");
            switchSlider.classList.add("slider");
            switchLabel.appendChild(switchInput);
            switchLabel.appendChild(switchSlider);
            buttonsContainer.appendChild(switchLabel);
        });

        roomContainer.appendChild(buttonsContainer);
        container.appendChild(roomContainer);
    }
};

function initializeApp() {
    if (typeof io === 'undefined') {
        console.warn('Socket.IO nie jest załadowany - ponawianie próby...');
        setTimeout(initializeApp, 100);
        return;
    }
    try {
        window.app = new SmartHomeApp();
        console.log('Aplikacja zainicjalizowana:', window.app);

        window.addEventListener('beforeunload', () => {
            if (window.app) {
                window.app.disconnect();
            }
        });

        if (typeof initPage === 'function') {
            console.log('Wywołanie initPage');
            initPage();
        }
    } catch (error) {
        console.error('Błąd inicjalizacji aplikacji:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM załadowany - rozpoczynanie inicjalizacji');
    initializeApp();
});


// Wywołaj animateMenuItemsOnOpen() po otwarciu menu (np. po dodaniu klasy .active do .main-menu)
// Przykład:
// document.querySelector('.main-menu').classList.add('active');
// animateMenuItemsOnOpen();