// Socket.IO fallback implementation for environments where CDN is blocked
(function(global) {
    'use strict';
    
    // Add CSRF token getter function
    function getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
    
    // Mock Socket.IO implementation for local development
    function MockSocket(url, options) {
        this.connected = false;
        this.id = Math.random().toString(36).substr(2, 9);
        this.events = {};
        
        // Auto-connect simulation
        setTimeout(() => {
            this.connected = true;
            this.emit('connect');
        }, 100);
    }
    
    MockSocket.prototype.on = function(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    };
    
    MockSocket.prototype.emit = function(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => {
                try {
                    callback(data);
                } catch (e) {
                    console.error('Socket event error:', e);
                }
            });
        }
        
        // For client-to-server events, we'll use fetch for now
        if (event !== 'connect' && event !== 'disconnect') {
            const endpoint = `/socket/${event}`;
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(data)
            }).catch(err => {
                console.warn('Socket fallback request failed:', err);
            });
        }
    };
    
    MockSocket.prototype.disconnect = function() {
        this.connected = false;
        this.emit('disconnect');
    };
    
    // Create io function that mimics socket.io client
    global.io = function(url, options) {
        return new MockSocket(url, options);
    };
    
    // Make getCSRFToken globally available
    global.getCSRFToken = getCSRFToken;
    
    console.log('Socket.IO fallback loaded');
    
})(window);