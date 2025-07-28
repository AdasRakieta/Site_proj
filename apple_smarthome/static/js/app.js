/**
 * Apple SmartHome PWA Application
 * Optimized for iOS Safari and mobile devices
 */

class AppleSmartHomeApp {
    constructor() {
        this.apiBase = '';
        this.socket = null;
        this.isAuthenticated = false;
        this.currentUser = null;
        this.devices = {
            lights: [],
            temperature: []
        };
        this.rooms = [];
        this.automations = [];
        
        // Connection status
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.init();
    }
    
    async init() {
        try {
            await this.setupServiceWorker();
            this.setupEventListeners();
            this.setupTabNavigation();
            this.checkAuthStatus();
            this.showToast('Aplikacja załadowana', 'success');
        } catch (error) {
            console.error('Error initializing app:', error);
            this.showToast('Błąd ładowania aplikacji', 'error');
        } finally {
            this.hideLoadingScreen();
        }
    }
    
    // Service Worker Setup for PWA functionality
    async setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/apple/static/js/sw.js');
                console.log('Service Worker registered:', registration);
                
                // Listen for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showToast('Nowa wersja dostępna. Odśwież aplikację.', 'info');
                        }
                    });
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }
    
    // Event Listeners Setup
    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        
        // Header buttons
        const refreshBtn = document.getElementById('refresh-btn');
        const logoutBtn = document.getElementById('logout-btn');
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }
        
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }
        
        // Haptic feedback for iOS
        this.setupHapticFeedback();
        
        // Handle app visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isAuthenticated) {
                this.refreshData();
            }
        });
        
        // Handle online/offline status
        window.addEventListener('online', () => {
            this.handleConnectionChange(true);
        });
        
        window.addEventListener('offline', () => {
            this.handleConnectionChange(false);
        });
    }
    
    // Tab Navigation Setup
    setupTabNavigation() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                
                // Update active tab button
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Update active tab content
                tabContents.forEach(content => content.classList.remove('active'));
                const activeContent = document.getElementById(`${tabName}-tab`);
                if (activeContent) {
                    activeContent.classList.add('active');
                }
                
                // Load data for the active tab
                this.loadTabData(tabName);
                
                // Trigger haptic feedback
                this.triggerHaptic('light');
            });
        });
    }
    
    // Haptic Feedback for iOS
    setupHapticFeedback() {
        // Add haptic feedback to interactive elements
        document.addEventListener('touchstart', (e) => {
            const element = e.target.closest('.device-card, .room-card, .automation-toggle, .temp-btn, .login-btn');
            if (element) {
                this.triggerHaptic('light');
            }
        });
    }
    
    triggerHaptic(type = 'light') {
        if ('haptic' in navigator && navigator.haptic) {
            navigator.haptic.vibrate(type);
        } else if ('vibrate' in navigator) {
            // Fallback for devices without haptic feedback
            const patterns = {
                light: [10],
                medium: [20],
                heavy: [30]
            };
            navigator.vibrate(patterns[type] || patterns.light);
        }
    }
    
    // Authentication
    async checkAuthStatus() {
        try {
            const response = await fetch('/api/user/profile');
            if (response.ok) {
                const userData = await response.json();
                this.currentUser = userData;
                this.isAuthenticated = true;
                this.showMainScreen();
                this.setupWebSocket();
                this.loadInitialData();
            } else {
                this.showLoginScreen();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.showLoginScreen();
        }
    }
    
    async handleLogin(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const username = formData.get('username');
        const password = formData.get('password');
        
        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: username,
                    password: password
                })
            });
            
            if (response.ok) {
                this.isAuthenticated = true;
                this.showMainScreen();
                this.setupWebSocket();
                this.loadInitialData();
                this.showToast('Zalogowano pomyślnie', 'success');
            } else {
                const errorText = await response.text();
                this.showLoginError('Nieprawidłowe dane logowania');
            }
        } catch (error) {
            console.error('Login failed:', error);
            this.showLoginError('Błąd połączenia z serwerem');
        }
    }
    
    async handleLogout() {
        try {
            await fetch('/logout', { method: 'POST' });
            this.isAuthenticated = false;
            this.currentUser = null;
            this.disconnectWebSocket();
            this.showLoginScreen();
            this.showToast('Wylogowano', 'success');
        } catch (error) {
            console.error('Logout failed:', error);
        }
    }
    
    // WebSocket Setup for real-time updates
    setupWebSocket() {
        try {
            // Use the same protocol as the page (http/https)
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const socketUrl = `${protocol}//${window.location.host}/socket.io/`;
            
            this.socket = io(socketUrl, {
                transports: ['websocket', 'polling'],
                timeout: 5000
            });
            
            this.socket.on('connect', () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            });
            
            this.socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            });
            
            this.socket.on('update_button', (data) => {
                this.updateDeviceState('light', data);
            });
            
            this.socket.on('update_temperature', (data) => {
                this.updateDeviceState('temperature', data);
            });
            
            this.socket.on('automation_updated', (data) => {
                this.updateAutomation(data);
            });
            
        } catch (error) {
            console.error('WebSocket setup failed:', error);
        }
    }
    
    disconnectWebSocket() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts && this.isAuthenticated) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.setupWebSocket();
            }, 2000 * this.reconnectAttempts);
        }
    }
    
    // Data Loading
    async loadInitialData() {
        await Promise.all([
            this.loadDevices(),
            this.loadRooms(),
            this.loadAutomations()
        ]);
    }
    
    async loadTabData(tabName) {
        switch (tabName) {
            case 'devices':
                await this.loadDevices();
                break;
            case 'rooms':
                await this.loadRooms();
                break;
            case 'automations':
                await this.loadAutomations();
                break;
        }
    }
    
    async loadDevices() {
        try {
            const [lightsResponse, temperatureResponse] = await Promise.all([
                fetch('/api/buttons'),
                fetch('/api/temperature_controls')
            ]);
            
            if (lightsResponse.ok && temperatureResponse.ok) {
                this.devices.lights = await lightsResponse.json();
                this.devices.temperature = await temperatureResponse.json();
                this.renderDevices();
            }
        } catch (error) {
            console.error('Failed to load devices:', error);
            this.showToast('Błąd ładowania urządzeń', 'error');
        }
    }
    
    async loadRooms() {
        try {
            const response = await fetch('/api/rooms');
            if (response.ok) {
                this.rooms = await response.json();
                this.renderRooms();
            }
        } catch (error) {
            console.error('Failed to load rooms:', error);
            this.showToast('Błąd ładowania pokojów', 'error');
        }
    }
    
    async loadAutomations() {
        try {
            const response = await fetch('/api/automations');
            if (response.ok) {
                this.automations = await response.json();
                this.renderAutomations();
            }
        } catch (error) {
            console.error('Failed to load automations:', error);
            this.showToast('Błąd ładowania automatyki', 'error');
        }
    }
    
    // Device Control
    async toggleLight(deviceId, currentState) {
        try {
            const response = await fetch(`/api/buttons/${deviceId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ state: !currentState })
            });
            
            if (response.ok) {
                this.triggerHaptic('medium');
                // Update will come via WebSocket
            } else {
                this.showToast('Błąd sterowania światłem', 'error');
            }
        } catch (error) {
            console.error('Failed to toggle light:', error);
            this.showToast('Błąd połączenia', 'error');
        }
    }
    
    async setTemperature(deviceId, temperature) {
        try {
            const response = await fetch(`/api/temperature_controls/${deviceId}/temperature`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ temperature: temperature })
            });
            
            if (response.ok) {
                this.triggerHaptic('medium');
                // Update will come via WebSocket
            } else {
                this.showToast('Błąd sterowania temperaturą', 'error');
            }
        } catch (error) {
            console.error('Failed to set temperature:', error);
            this.showToast('Błąd połączenia', 'error');
        }
    }
    
    async toggleAutomation(index, currentState) {
        try {
            const response = await fetch(`/api/automations/${index}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled: !currentState })
            });
            
            if (response.ok) {
                this.triggerHaptic('medium');
                await this.loadAutomations();
            } else {
                this.showToast('Błąd sterowania automatyką', 'error');
            }
        } catch (error) {
            console.error('Failed to toggle automation:', error);
            this.showToast('Błąd połączenia', 'error');
        }
    }
    
    // Rendering Methods
    renderDevices() {
        this.renderLights();
        this.renderTemperature();
    }
    
    renderLights() {
        const container = document.getElementById('lights-container');
        if (!container) return;
        
        container.innerHTML = this.devices.lights.map(light => `
            <div class="device-card ${light.state ? 'active' : ''}" 
                 onclick="app.toggleLight('${light.id}', ${light.state})">
                <div class="device-icon">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C8.13 2 5 5.13 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.87-3.13-7-7-7zM9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1z"/>
                    </svg>
                </div>
                <div class="device-name">${light.name}</div>
                <div class="device-room">${light.room}</div>
            </div>
        `).join('');
    }
    
    renderTemperature() {
        const container = document.getElementById('temperature-container');
        if (!container) return;
        
        container.innerHTML = this.devices.temperature.map(device => `
            <div class="temperature-card">
                <div class="device-name">${device.name}</div>
                <div class="device-room">${device.room}</div>
                <div class="temperature-value">${device.temperature}°C</div>
                <div class="temperature-controls">
                    <button class="temp-btn" onclick="app.setTemperature('${device.id}', ${device.temperature - 1})">-</button>
                    <button class="temp-btn" onclick="app.setTemperature('${device.id}', ${device.temperature + 1})">+</button>
                </div>
            </div>
        `).join('');
    }
    
    renderRooms() {
        const container = document.getElementById('rooms-container');
        if (!container) return;
        
        container.innerHTML = this.rooms.map(room => {
            const roomDevices = [
                ...this.devices.lights.filter(d => d.room === room),
                ...this.devices.temperature.filter(d => d.room === room)
            ];
            
            return `
                <div class="room-card">
                    <div class="room-header">
                        <div class="room-name">${room}</div>
                        <div class="room-device-count">${roomDevices.length} urządzeń</div>
                    </div>
                    <div class="room-devices">
                        ${roomDevices.map(device => `
                            <div class="room-device">${device.name}</div>
                        `).join('')}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    renderAutomations() {
        const container = document.getElementById('automations-container');
        if (!container) return;
        
        container.innerHTML = this.automations.map((automation, index) => `
            <div class="automation-card">
                <div class="automation-header">
                    <div class="automation-name">${automation.name}</div>
                    <button class="automation-toggle ${automation.enabled ? 'enabled' : 'disabled'}"
                            onclick="app.toggleAutomation(${index}, ${automation.enabled})">
                    </button>
                </div>
                <div class="automation-description">
                    ${this.getAutomationDescription(automation)}
                </div>
            </div>
        `).join('');
    }
    
    getAutomationDescription(automation) {
        const trigger = automation.trigger;
        let description = '';
        
        if (trigger.type === 'time') {
            description = `Codziennie o ${trigger.time}`;
        } else if (trigger.type === 'device') {
            description = `Gdy ${trigger.device} zostanie ${trigger.state === 'on' ? 'włączone' : 'wyłączone'}`;
        } else if (trigger.type === 'sensor') {
            description = `Gdy ${trigger.sensor} ${trigger.condition === 'above' ? 'przekroczy' : 'spadnie poniżej'} ${trigger.value}`;
        }
        
        return description;
    }
    
    // UI State Management
    showLoadingScreen() {
        document.getElementById('loading-screen').classList.remove('hidden');
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('main-screen').classList.add('hidden');
    }
    
    hideLoadingScreen() {
        document.getElementById('loading-screen').classList.add('hidden');
    }
    
    showLoginScreen() {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('main-screen').classList.add('hidden');
        this.hideLoginError();
    }
    
    showMainScreen() {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('main-screen').classList.remove('hidden');
    }
    
    showLoginError(message) {
        const errorElement = document.getElementById('login-error');
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }
    
    hideLoginError() {
        const errorElement = document.getElementById('login-error');
        errorElement.classList.add('hidden');
    }
    
    // Connection Status
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        const textElement = document.getElementById('connection-text');
        
        if (connected) {
            statusElement.classList.remove('disconnected');
            statusElement.classList.add('connected');
            textElement.textContent = 'Połączono';
            setTimeout(() => statusElement.classList.add('hidden'), 2000);
        } else {
            statusElement.classList.remove('connected', 'hidden');
            statusElement.classList.add('disconnected');
            textElement.textContent = 'Rozłączono';
        }
    }
    
    handleConnectionChange(online) {
        if (online) {
            this.showToast('Połączenie przywrócone', 'success');
            if (this.isAuthenticated) {
                this.refreshData();
            }
        } else {
            this.showToast('Brak połączenia internetowego', 'error');
        }
    }
    
    // Utility Methods
    async refreshData() {
        if (this.isAuthenticated) {
            await this.loadInitialData();
            this.showToast('Dane odświeżone', 'success');
        }
    }
    
    updateDeviceState(type, data) {
        if (type === 'light') {
            const device = this.devices.lights.find(d => d.id === data.id || d.name === data.name);
            if (device) {
                device.state = data.state;
                this.renderLights();
            }
        } else if (type === 'temperature') {
            const device = this.devices.temperature.find(d => d.id === data.id || d.name === data.name);
            if (device) {
                device.temperature = data.temperature;
                this.renderTemperature();
            }
        }
    }
    
    updateAutomation(data) {
        if (data.index !== undefined && this.automations[data.index]) {
            this.automations[data.index] = { ...this.automations[data.index], ...data };
            this.renderAutomations();
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Hide and remove toast
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 300);
        }, 3000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AppleSmartHomeApp();
});

// Handle app installation prompt
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show custom install prompt after a delay
    setTimeout(() => {
        if (window.app) {
            window.app.showToast('Dodaj aplikację do ekranu głównego', 'info');
        }
    }, 30000);
});

window.addEventListener('appinstalled', () => {
    if (window.app) {
        window.app.showToast('Aplikacja została zainstalowana', 'success');
    }
    deferredPrompt = null;
});