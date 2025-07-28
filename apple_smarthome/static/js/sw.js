/**
 * Service Worker for Apple SmartHome PWA
 * Provides offline functionality and caching
 */

const CACHE_NAME = 'apple-smarthome-v1.0.0';
const API_CACHE_NAME = 'apple-smarthome-api-v1.0.0';

// Files to cache for offline functionality
const STATIC_FILES = [
    '/apple/',
    '/apple/static/css/style.css',
    '/apple/static/js/app.js',
    '/apple/static/manifest.json'
];

// API endpoints to cache
const API_ENDPOINTS = [
    '/api/buttons',
    '/api/temperature_controls',
    '/api/rooms',
    '/api/automations'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Caching static files...');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('Static files cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Error caching static files:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle requests with caching strategy
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip Chrome extension requests
    if (url.protocol === 'chrome-extension:') {
        return;
    }
    
    // Handle different types of requests
    if (isAPIRequest(url)) {
        event.respondWith(handleAPIRequest(request));
    } else if (isStaticFile(url)) {
        event.respondWith(handleStaticFile(request));
    } else {
        event.respondWith(handleOtherRequests(request));
    }
});

// Check if request is for API
function isAPIRequest(url) {
    return url.pathname.startsWith('/api/');
}

// Check if request is for static file
function isStaticFile(url) {
    return url.pathname.startsWith('/apple/static/') || 
           url.pathname === '/apple/' ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js') ||
           url.pathname.endsWith('.png') ||
           url.pathname.endsWith('.jpg') ||
           url.pathname.endsWith('.svg');
}

// Handle API requests with network-first strategy
async function handleAPIRequest(request) {
    const url = new URL(request.url);
    
    try {
        // Try network first
        const networkResponse = await fetch(request.clone());
        
        if (networkResponse.ok) {
            // Cache successful API responses
            if (shouldCacheAPIResponse(url)) {
                const cache = await caches.open(API_CACHE_NAME);
                cache.put(request.clone(), networkResponse.clone());
            }
            return networkResponse;
        }
        
        // If network fails, try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log('Serving API from cache:', url.pathname);
            return cachedResponse;
        }
        
        // Return error response if nothing available
        return new Response(
            JSON.stringify({ error: 'Brak połączenia z serwerem' }),
            {
                status: 503,
                statusText: 'Service Unavailable',
                headers: { 'Content-Type': 'application/json' }
            }
        );
        
    } catch (error) {
        console.error('API request failed:', error);
        
        // Try to serve from cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log('Serving API from cache (offline):', url.pathname);
            return cachedResponse;
        }
        
        // Return offline response
        return new Response(
            JSON.stringify({ error: 'Aplikacja jest offline' }),
            {
                status: 503,
                statusText: 'Service Unavailable',
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Handle static files with cache-first strategy
async function handleStaticFile(request) {
    try {
        // Try cache first
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // If not in cache, fetch from network
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache the response
            const cache = await caches.open(CACHE_NAME);
            cache.put(request.clone(), networkResponse.clone());
        }
        
        return networkResponse;
        
    } catch (error) {
        console.error('Static file request failed:', error);
        
        // Return fallback for main page
        if (request.url.endsWith('/apple/') || request.url.endsWith('/apple')) {
            return new Response(
                `<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>SmartHome - Offline</title>
                    <style>
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
                            display: flex; 
                            justify-content: center; 
                            align-items: center; 
                            height: 100vh; 
                            margin: 0; 
                            background: #f2f2f7; 
                            color: #000;
                        }
                        .offline-message { 
                            text-align: center; 
                            padding: 40px; 
                            background: white; 
                            border-radius: 12px; 
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                        .offline-message h1 { 
                            color: #007AFF; 
                            margin-bottom: 16px; 
                        }
                        .offline-message p { 
                            color: #8E8E93; 
                            margin-bottom: 20px; 
                        }
                        .retry-btn { 
                            background: #007AFF; 
                            color: white; 
                            border: none; 
                            padding: 12px 24px; 
                            border-radius: 8px; 
                            font-size: 16px; 
                            cursor: pointer; 
                        }
                    </style>
                </head>
                <body>
                    <div class="offline-message">
                        <h1>Aplikacja Offline</h1>
                        <p>Sprawdź połączenie internetowe i spróbuj ponownie.</p>
                        <button class="retry-btn" onclick="location.reload()">Spróbuj ponownie</button>
                    </div>
                </body>
                </html>`,
                {
                    headers: { 'Content-Type': 'text/html' }
                }
            );
        }
        
        return new Response('Plik nie dostępny offline', { status: 404 });
    }
}

// Handle other requests with network-first strategy
async function handleOtherRequests(request) {
    try {
        return await fetch(request);
    } catch (error) {
        // Return a generic offline response
        return new Response('Brak połączenia internetowego', { 
            status: 503,
            statusText: 'Service Unavailable' 
        });
    }
}

// Check if API response should be cached
function shouldCacheAPIResponse(url) {
    const cachableEndpoints = [
        '/api/rooms',
        '/api/buttons',
        '/api/temperature_controls',
        '/api/automations'
    ];
    
    return cachableEndpoints.some(endpoint => url.pathname.startsWith(endpoint));
}

// Handle background sync for offline actions
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(processOfflineActions());
    }
});

// Process actions that were queued while offline
async function processOfflineActions() {
    try {
        // Get queued actions from IndexedDB
        const actions = await getQueuedActions();
        
        for (const action of actions) {
            try {
                await fetch(action.url, action.options);
                await removeQueuedAction(action.id);
                console.log('Processed offline action:', action.type);
            } catch (error) {
                console.error('Failed to process offline action:', error);
            }
        }
    } catch (error) {
        console.error('Error processing offline actions:', error);
    }
}

// IndexedDB helpers for queuing offline actions
async function getQueuedActions() {
    // Placeholder for IndexedDB implementation
    return [];
}

async function removeQueuedAction(id) {
    // Placeholder for IndexedDB implementation
}

// Handle push notifications (future enhancement)
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        
        const options = {
            body: data.body || 'Nowe powiadomienie z SmartHome',
            icon: '/apple/static/icons/icon-192x192.png',
            badge: '/apple/static/icons/icon-72x72.png',
            tag: data.tag || 'smarthome-notification',
            requireInteraction: true,
            actions: [
                {
                    action: 'open',
                    title: 'Otwórz aplikację'
                },
                {
                    action: 'dismiss',
                    title: 'Odrzuć'
                }
            ]
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title || 'SmartHome', options)
        );
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'open') {
        event.waitUntil(
            clients.matchAll({ type: 'window', includeUncontrolled: true })
                .then((clientList) => {
                    // Check if app is already open
                    for (const client of clientList) {
                        if (client.url.includes('/apple') && 'focus' in client) {
                            return client.focus();
                        }
                    }
                    
                    // Open new window if app is not open
                    if (clients.openWindow) {
                        return clients.openWindow('/apple/');
                    }
                })
        );
    }
});

// Log service worker events for debugging
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
});

console.log('Service Worker loaded successfully');