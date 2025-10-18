/**
 * Home Page (index.html) JavaScript
 * Handles room display and weather updates
 */

/* ============================== */
/*      Room Display Functions     */
/* ============================== */

/**
 * Render rooms in grid layout
 * @param {Array} rooms - Array of room names
 */
function renderRooms(rooms) {
    const roomSelect = document.getElementById('roomSelect');
    if (!roomSelect) return;
    
    roomSelect.innerHTML = '';
    
    // Adjust container width based on room count
    if (rooms.length > 8) {
        roomSelect.classList.add('wide');
    } else {
        roomSelect.classList.remove('wide');
    }

    // Determine how many rooms per row based on total count
    const roomsPerRow = rooms.length > 8 ? 3 : 2;

    for (let i = 0; i < rooms.length; i += roomsPerRow) {
        const row = document.createElement('div');
        row.className = roomsPerRow === 3 ? 'grid-container-list' : 'grid-container';

        // Create and add buttons for each room in this row
        for (let j = 0; j < roomsPerRow && i + j < rooms.length; j++) {
            const roomButton = document.createElement('a');
            roomButton.href = `/${rooms[i + j].toLowerCase()}`;
            roomButton.className = 'rooms-button';
            roomButton.textContent = rooms[i + j];
            row.appendChild(roomButton);
        }

        roomSelect.appendChild(row);
        const hr = document.createElement('hr');
        roomSelect.appendChild(hr);
    }
}

/**
 * Load rooms via AJAX (fallback for updates)
 */
function loadRooms() {
    if (typeof app !== 'undefined' && typeof app.getRooms === 'function') {
        app.getRooms().then(rooms => {
            renderRooms(rooms);
        });
    }
}

/* ============================== */
/*   Weather/Temperature Functions */
/* ============================== */

/**
 * Fetch current temperature from weather station
 */
function fetchTemperature() {
    if (typeof app === 'undefined' || typeof app.fetchData !== 'function') {
        console.warn('app.fetchData not available');
        return;
    }
    
    app.fetchData('/weather')
        .then(data => {
            const stationElement = document.getElementById('statShow');
            const temperatureElement = document.getElementById('tempShow');

            if (!stationElement || !temperatureElement) return;

            if (data.stacja && data.temperatura !== undefined) {
                // Check if weather is from a nearby city (not exact location)
                if (data.nearest_city && data.distance_km) {
                    stationElement.textContent = `${data.stacja} (${data.distance_km} km): `;
                    stationElement.title = `Pogoda z najbliższego miasta - ${data.distance_km} km od domu`;
                } else {
                    stationElement.textContent = `${data.stacja}: `;
                    stationElement.title = '';
                }
                
                // Display temperature with weather description if available
                let tempText = `${data.temperatura} °C`;
                if (data.opis) {
                    tempText += ` (${data.opis})`;
                }
                temperatureElement.textContent = tempText;
            } else {
                stationElement.textContent = 'Brak danych';
                temperatureElement.textContent = '';
            }
        })
        .catch(error => {
            console.error('Błąd podczas pobierania danych pogodowych:', error);
            const stationElement = document.getElementById('statShow');
            const temperatureElement = document.getElementById('tempShow');
            if (stationElement) stationElement.textContent = 'Błąd pobierania';
            if (temperatureElement) temperatureElement.textContent = '';
        });
}

/**
 * Start auto-refresh for temperature (every 5 minutes)
 */
function startTemperatureAutoRefresh() {
    fetchTemperature();
    setInterval(fetchTemperature, 300000); // 5 minutes
}

/* ============================== */
/*      Initialization            */
/* ============================== */

/**
 * Initialize home page
 */
function initHomePage() {
    // Read preloaded rooms from JSON script tag
    const preloadedRoomsElement = document.getElementById('preloadedRooms');
    if (preloadedRoomsElement) {
        try {
            const preloadedRooms = JSON.parse(preloadedRoomsElement.textContent);
            renderRooms(preloadedRooms);
        } catch (error) {
            console.error('Error parsing preloaded rooms:', error);
            // Fallback to AJAX load
            loadRooms();
        }
    } else {
        // No preloaded data, load via AJAX
        loadRooms();
    }
    
    // Start temperature auto-refresh
    startTemperatureAutoRefresh();
    
    // Listen for room updates (real-time via Socket.IO)
    if (typeof app !== 'undefined' && app.onRoomsUpdate) {
        app.onRoomsUpdate = function(rooms) {
            loadRooms();
        };
    }
}

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', initHomePage);
