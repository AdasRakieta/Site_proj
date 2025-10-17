console.log('controls.js loaded');

// --- Kontrolki do zarządzania pokojami, przyciskami i sterownikami temperatury ---

function getCSRFToken() {
    let token = null;
    // Najpierw sprawdź meta tag
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) token = meta.getAttribute('content');
    
    // Potem sprawdź hidden input
    if (!token) {
        const input = document.querySelector('input[name="_csrf_token"]');
        if (input) token = input.value;
    }
    
    // Na końcu sprawdź zmienną globalną
    if (!token && window.csrf_token) {
        token = window.csrf_token;
    }
    
    console.log('CSRF Token:', token); // debugging
    return token;
}

// --- Drag & Drop kolejności pokoi, świateł i termostatów ---
(function() {
    let dragMode = false;
    let draggedItem = null;
    let dragStartIndex = null;
    let currentLists = ["roomsList", "buttonsList", "temperatureControlsList"];

    // Dodaj przycisk na środku pod listami
    function addReorderButtonGlobal() {
        // Usuwamy stary przycisk przy pokojach jeśli istnieje
        const oldBtn = document.getElementById("reorderRoomsBtn");
        if (oldBtn && oldBtn.parentElement) oldBtn.parentElement.removeChild(oldBtn);
        // Dodajemy globalny przycisk jeśli go nie ma
        let btn = document.getElementById("reorderAllBtn");
        if (btn) return; // już jest
        btn = document.createElement("button");
        btn.id = "reorderAllBtn";
        btn.className = "rooms-button";
        btn.textContent = dragMode ? "Zakończ edycję kolejności" : "Edytuj kolejność wszystkich";
        btn.style.margin = "30px auto 0 auto";
        btn.style.display = "block";
        btn.style.fontWeight = "bold";
        btn.addEventListener("click", function() {
            if (!dragMode) {
                enableDragModeAll();
                btn.textContent = "Zakończ edycję kolejności";
            } else {
                disableDragModeAll();
                btn.textContent = "Edytuj kolejność wszystkich";
            }
        });
        // Wstaw przycisk pod grid-container-list
        const grid = document.querySelector('.grid-container-list');
        if (grid && grid.parentElement) {
            grid.parentElement.appendChild(btn);
        }
    }

    function enableDragModeAll() {
        dragMode = true;
        currentLists.forEach(listId => {
            const list = document.getElementById(listId);
            if (!list) return;
            Array.from(list.children).forEach((li, idx) => {
                li.draggable = true;
                li.style.cursor = "grab";
                li.addEventListener('dragstart', onDragStart);
                li.addEventListener('dragover', onDragOver);
                li.addEventListener('drop', onDrop);
                li.addEventListener('dragend', onDragEnd);
            });
        });
    }
    function disableDragModeAll() {
        dragMode = false;
        currentLists.forEach(listId => {
            const list = document.getElementById(listId);
            if (!list) return;
            Array.from(list.children).forEach((li) => {
                li.draggable = false;
                li.style.cursor = "";
                li.removeEventListener('dragstart', onDragStart);
                li.removeEventListener('dragover', onDragOver);
                li.removeEventListener('drop', onDrop);
                li.removeEventListener('dragend', onDragEnd);
            });
        });
        // --- ZAPISZ KOLEJNOŚĆ DO BACKENDU ---
        saveAllOrdersToBackend();
    }

    // Zapisz kolejność pokoi, przycisków i termostatów do backendu
    async function saveAllOrdersToBackend() {
        // Pokoje
        const roomsList = document.getElementById('roomsList');
        const rooms = Array.from(roomsList.children).map(li => li.querySelector('.list-item-content').textContent);
        // Przyciski
        const buttonsList = document.getElementById('buttonsList');
        const buttons = Array.from(buttonsList.children).map(li => {
            const txt = li.querySelector('.list-item-content').textContent;
            const [name, room] = txt.split(' - ');
            return { name: name?.trim(), room: room?.trim() };
        });
        // Termostaty
        const tempList = document.getElementById('temperatureControlsList');
        const tempControls = Array.from(tempList.children).map(li => {
            const txt = li.querySelector('.list-item-content').textContent;
            const [name, room] = txt.split(' - ');
            return { name: name?.trim(), room: room?.trim() };
        });
        try {
            await fetch('/api/rooms/order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify({ rooms })
            });
            await fetch('/api/buttons/order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify({ buttons })
            });
            await fetch('/api/temperature_controls/order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify({ controls: tempControls })
            });
            if (window.showNotification) window.showNotification('Kolejność zapisana!', 'success');
        } catch (e) {
            if (window.showNotification) window.showNotification('Błąd zapisu kolejności!', 'error');
        }
    }

    function onDragStart(e) {
        draggedItem = this;
        dragStartIndex = Array.from(this.parentNode.children).indexOf(this);
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }
    function onDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        const overItem = this;
        if (overItem === draggedItem) return;
        overItem.classList.add('drag-over');
    }
    function onDrop(e) {
        e.preventDefault();
        const list = this.parentNode;
        const dragOverIndex = Array.from(list.children).indexOf(this);
        if (dragStartIndex !== dragOverIndex) {
            if (dragStartIndex < dragOverIndex) {
                list.insertBefore(draggedItem, this.nextSibling);
            } else {
                list.insertBefore(draggedItem, this);
            }
        }
        this.classList.remove('drag-over');
    }
    function onDragEnd() {
        this.classList.remove('dragging');
        Array.from(this.parentNode.children).forEach(li => li.classList.remove('drag-over'));
    }

    // Po każdej aktualizacji list, przycisk jest dodawany na nowo
    const origUpdateRoomsList = window.updateRoomsList;
    window.updateRoomsList = function(rooms) {
        origUpdateRoomsList(rooms);
        window.updateRoomSelect(rooms);
        window.updateRoomSelectTemp(rooms);
        addReorderButtonGlobal();
    };
    const origUpdateButtonsList = window.updateButtonsList;
    window.updateButtonsList = function(buttons) {
        origUpdateButtonsList(buttons);
        addReorderButtonGlobal();
    };
    const origUpdateTemperatureControlsList = window.updateTemperatureControlsList;
    window.updateTemperatureControlsList = function(controls) {
        origUpdateTemperatureControlsList(controls);
        addReorderButtonGlobal();
    };

    // Minimalne style dla drag & drop
    const style = document.createElement('style');
    style.textContent = `
    .list-container .dragging { opacity: 0.5; }
    .list-container .drag-over { border: 2px dashed var(--accent); background: var(--hover); }
    `;
    document.head.appendChild(style);

    // Dodaj przycisk po załadowaniu strony (na wypadek gdyby listy były puste)
    document.addEventListener('DOMContentLoaded', addReorderButtonGlobal);

    // Upewnij się, że funkcja jest globalna
    window.addReorderButtonGlobal = addReorderButtonGlobal;

})();

// --- Kanban/DragNDrop rendering for edit.html ---
window.renderKanbanLists = function renderKanbanLists(rooms, buttons, controls) {
    console.log('renderKanbanLists called');
    const kanbanContainer = document.getElementById('kanbanContainer');
    kanbanContainer.innerHTML = '';
    
    // Wrapper dla kolumn z nowymi stylami
    const columnsWrapper = document.createElement('div');
    columnsWrapper.id = 'kanbanColumnsWrapper';
    columnsWrapper.style.display = 'flex';
    columnsWrapper.style.flexWrap = 'wrap';
    columnsWrapper.style.gap = '20px';
    columnsWrapper.style.justifyContent = 'center';
    columnsWrapper.style.alignItems = 'flex-start';
    columnsWrapper.style.maxWidth = '1200px';
    columnsWrapper.style.margin = '0 auto';
    columnsWrapper.style.padding = '20px';

    kanbanContainer.appendChild(columnsWrapper);

    // Zbuduj zestaw istniejących nazw pokoi, aby wykrywać urządzenia z nieistniejącymi już nazwami
    const roomNameSet = new Set(
        rooms.map(r => (typeof r === 'string' ? r : (r && r.name ? r.name : r))).filter(Boolean)
    );
    const roomIdSet = new Set(
        rooms
            .map(r => (typeof r === 'object' && r !== null && r.id != null ? String(r.id) : null))
            .filter(Boolean)
    );

    // Rozdziel urządzenia na przypisane poprawnie i do przeniesienia do "Nieprzypisane"
    const unassignedButtons = [];
    const unassignedControls = [];
    const assignedButtons = [];
    const assignedControls = [];

    (buttons || []).forEach(b => {
        const buttonRoomName = b.room_name || b.room;
        const buttonRoomId = b.room_id != null ? String(b.room_id) : null;
        const hasNameMatch = buttonRoomName ? roomNameSet.has(buttonRoomName) : false;
        const hasIdMatch = buttonRoomId ? roomIdSet.has(buttonRoomId) : false;
        if (!hasNameMatch && !hasIdMatch) {
            unassignedButtons.push(b);
        } else {
            assignedButtons.push(b);
        }
    });
    (controls || []).forEach(c => {
        const controlRoomName = c.room_name || c.room;
        const controlRoomId = c.room_id != null ? String(c.room_id) : null;
        const hasNameMatch = controlRoomName ? roomNameSet.has(controlRoomName) : false;
        const hasIdMatch = controlRoomId ? roomIdSet.has(controlRoomId) : false;
        if (!hasNameMatch && !hasIdMatch) {
            unassignedControls.push(c);
        } else {
            assignedControls.push(c);
        }
    });

    // Najpierw dodaj stały kontener "Nieprzypisane" (także te z nieistniejącymi już nazwami pokoi)
    const unassignedColumn = createKanbanColumn('Nieprzypisane', 
        unassignedButtons, 
        unassignedControls,
        true
    );
    columnsWrapper.appendChild(unassignedColumn);

    // Dodaj pozostałe pokoje
    rooms.forEach(room => {
        // If room is an object, pass as is; if string, wrap as {name: room, id: room}
        let roomObj = room;
        if (typeof room === 'string') {
            roomObj = { name: room, id: room };
        }
        const column = createKanbanColumn(
            roomObj,
            assignedButtons.filter(button => {
                const buttonRoomName = button.room_name || button.room;
                const buttonRoomId = button.room_id;
                return (buttonRoomName && buttonRoomName === roomObj.name) ||
                       (buttonRoomId != null && roomObj.id != null && String(buttonRoomId) === String(roomObj.id));
            }),
            assignedControls.filter(control => {
                const controlRoomName = control.room_name || control.room;
                const controlRoomId = control.room_id;
                return (controlRoomName && controlRoomName === roomObj.name) ||
                       (controlRoomId != null && roomObj.id != null && String(controlRoomId) === String(roomObj.id));
            })
        );
        columnsWrapper.appendChild(column);
    });

    // Aktualizacja stylów kolumn dla lepszego układu
    const columns = columnsWrapper.querySelectorAll('.kanban-column');
    columns.forEach(col => {
        col.style.flex = '0 0 calc(25% - 15px)';
        col.style.minWidth = '280px';
        col.style.maxWidth = '300px';
    });

    // Inicjalizacja Dragula dla urządzeń
    if (window.initDynamicKanbanDragula) {
        console.log('Setting up Dragula handlers');
        const allLists = document.querySelectorAll('.kanban-list');
        window.initDynamicKanbanDragula(function onDropHandler(el, target, source, sibling) {
            // No need for immediate API calls - changes are stored in pendingChanges
            console.log('Device moved - changes will be stored until save');
        });
    }

    // Inicjalizacja Dragula dla kolumn
    if (window.columnsDragulaInstance && window.columnsDragulaInstance.destroy) {
        window.columnsDragulaInstance.destroy();
    }

    window.columnsDragulaInstance = dragula([columnsWrapper], {
        moves: function(el, container, handle) {
            if (!window.editMode) return false;
            if (!handle || !handle.closest) return false;
            const header = handle.closest('.kanban-column-header');
            return el.classList.contains('kanban-column') && 
                   !el.hasAttribute('data-fixed') && 
                   header !== null;
        },
        direction: 'horizontal'
    });

    window.columnsDragulaInstance.on('drop', function(el, target, source, sibling) {
        if (!window.editMode) return;
        console.log('Column moved - storing new order');
        const columns = Array.from(columnsWrapper.children);
        const roomOrder = columns
            .filter(col => !col.hasAttribute('data-fixed'))
            .map(col => ({
                id: col.getAttribute('data-room-id') || null,
                name: col.getAttribute('data-room-name') || (col.querySelector('h3') ? col.querySelector('h3').textContent : null)
            }));
        
        // Store the column order instead of sending it immediately
        if (window.storeColumnMove) {
            window.storeColumnMove(roomOrder);
        }
    });
}

// Pomocnicza funkcja do tworzenia kolumny Kanban
function createKanbanColumn(room, roomButtons, roomControls, isFixed = false) {
    const column = document.createElement('div');
    column.className = 'kanban-column';
    if (isFixed) column.setAttribute('data-fixed', 'true');

    const header = document.createElement('div');
    header.className = 'kanban-column-header';;
    // Use room.name if room is an object, otherwise use room as string
    const roomName = typeof room === 'object' && room !== null ? room.name : room;
    header.innerHTML = `<h3 style="margin:0;">${roomName}</h3>`;
    if (!isFixed) {
        header.setAttribute('data-drag-handle', 'true');
        if (window.updateColumnHeader) {
            setTimeout(() => window.updateColumnHeader(column, roomName), 0);
        }
        // Set data-room-id to room.id if available, else to name
        const rawRoomId = typeof room === 'object' && room !== null && room.id != null ? room.id : null;
        const resolvedRoomId = rawRoomId != null ? String(rawRoomId) : null;
        if (resolvedRoomId) {
            column.setAttribute('data-room-id', resolvedRoomId);
        } else {
            column.removeAttribute('data-room-id');
        }
        column.setAttribute('data-room-name', roomName || '');
    }
    column.setAttribute('data-room-name', roomName || '');
    column.appendChild(header);

    const list = document.createElement('ul');
    list.className = 'kanban-list';
    list.style.listStyle = 'none';
    list.style.padding = '0';
    list.style.margin = '0';
    list.style.display = 'flex';
    list.style.flexDirection = 'column';
    list.style.alignItems = 'center';
    list.style.minHeight = '100px';

    // Dodaj urządzenia do listy
    [...roomButtons, ...roomControls].forEach(device => {
        const li = document.createElement('li');
        li.className = 'kanban-card';
        li.innerHTML = `<span class="kanban-card-content">${device.name} - ${device.type}</span>`;
        li.setAttribute('data-id', device.id);
        li.setAttribute('data-type', device.type);

        const btns = document.createElement('div');
        btns.style.display = 'flex';
        btns.style.gap = '4px';
        btns.style.marginTop = '8px';

        const editBtn = document.createElement('button');
        editBtn.className = 'kanban-edit-btn';
        editBtn.innerHTML = '✎';
        editBtn.title = 'Edytuj';
        editBtn.onclick = () => startEditDeviceKanban(device, li);

        const removeBtn = document.createElement('button');
        removeBtn.className = 'kanban-remove-btn';
        removeBtn.innerHTML = '✖';
        removeBtn.title = 'Usuń';
        removeBtn.onclick = () => window.deleteDevice(device);

        btns.appendChild(editBtn);
        btns.appendChild(removeBtn);
        li.appendChild(btns);
        list.appendChild(li);
    });

    column.appendChild(list);
    return column;
}

// Pomocnicza funkcja do aktualizacji kolejności urządzeń
function updateDeviceOrders(targetList, room, roomId = null) {
    const allLis = Array.from(targetList.querySelectorAll('li.kanban-card'));
    const lightsOrder = allLis
        .filter(li => li.getAttribute('data-type') === 'light')
        .map(li => li.getAttribute('data-id'));
    const thermostatsOrder = allLis
        .filter(li => li.getAttribute('data-type') === 'thermostat')
        .map(li => li.getAttribute('data-id'));

    if (lightsOrder.length > 0) {
        fetch('/api/buttons/order', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ room: room, room_id: roomId, order: lightsOrder })
        }).then(r => r.json())
          .then(data => console.log('Lights order updated:', data));
    }

    if (thermostatsOrder.length > 0) {
        fetch('/api/temperature_controls/order', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ room: room, room_id: roomId, order: thermostatsOrder })
        }).then(r => r.json())
          .then(data => console.log('Thermostats order updated:', data));
    }
}

// Funkcje obsługi dodawania z Kanban
window.addDeviceFromKanban = function(name, type, room) {
    let roomName = null;
    let roomId = null;
    if (room && typeof room === 'object') {
        roomName = room.name || null;
        roomId = room.id || room.room_id || null;
    } else {
        roomName = room || null;
    }
    const endpoint = type === 'light' ? '/api/buttons' : '/api/temperature_controls';
    fetch(endpoint, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ name, room: roomName, room_id: roomId })
    }).then(r => r.json()).then(() => window.loadKanban());
};

// Funkcje obsługi usuwania z Kanban
window.deleteDevice = function(device) {
    const endpoint = device.type === 'light' ? `/api/buttons/${device.id}` : `/api/temperature_controls/${device.id}`;
    fetch(endpoint, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCSRFToken() }
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            if (window.showNotification) window.showNotification('Urządzenie usunięte!', 'success');
            window.loadKanban();
        }
        else {
            if (window.showNotification) window.showNotification('Błąd usuwania urządzenia: ' + (data.message || 'Nieznany błąd'), 'error');
        }
    });
};

// Edycja inline w stylu Kanban
function startEditDeviceKanban(device, li) {
    li.innerHTML = `<input type='text' class='kanban-edit-input' value='${device.name}'/><div class='kanban-edit-btns'><button class='kanban-save-btn'>✔</button><button class='kanban-cancel-btn'>✖</button></div>`;
    const input = li.querySelector('input');
    const btns = li.querySelector('.kanban-edit-btns');
    const saveBtn = li.querySelector('.kanban-save-btn');
    const cancelBtn = li.querySelector('.kanban-cancel-btn');

    function exitEditMode(newName) {
        // Restore normal display (reload Kanban)
        window.loadKanban();
    }

    saveBtn.onclick = () => {
        const newName = input.value.trim();
        if (!newName || newName === device.name) return exitEditMode(device.name);
        const endpoint = device.type === 'light' ? `/api/buttons/${device.id}` : `/api/temperature_controls/${device.id}`;
        fetch(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
            body: JSON.stringify({ name: newName })
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                if (window.showNotification) window.showNotification('Nazwa urządzenia zaktualizowana!', 'success');
            } else {
                if (window.showNotification) window.showNotification('Błąd podczas aktualizacji nazwy: ' + (data.message || 'Nieznany błąd'), 'error');
            }
            exitEditMode(newName);
        })
        .catch(error => {
            if (window.showNotification) window.showNotification('Błąd sieci podczas aktualizacji nazwy', 'error');
            exitEditMode(device.name);
        });
    };

    cancelBtn.onclick = () => {
        exitEditMode(device.name);
    };

    input.onkeydown = (e) => {
        if (e.key === 'Enter') saveBtn.onclick();
        if (e.key === 'Escape') cancelBtn.onclick();
    };
}

// Aktualizacja selectboxa z pokojami
window.updateRoomSelect = function updateRoomSelect(rooms) {
    const select = document.getElementById('newDeviceRoom');
    if (!select) return;

    // Zachowaj opcję "Nieprzypisane" (jeśli istnieje) lub utwórz nową
    const existingPlaceholder = select.querySelector('option[value=""]');
    const placeholderOption = existingPlaceholder
        ? existingPlaceholder.cloneNode(true)
        : (() => {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Nieprzypisane';
            return option;
        })();

    placeholderOption.selected = true;

    select.innerHTML = '';
    select.appendChild(placeholderOption);

    // Dodaj pozostałe pokoje
    const normalizedRooms = window.normalizeRoomsData ? window.normalizeRoomsData(rooms) : rooms;
    (normalizedRooms || []).forEach(room => {
        const roomName = room && room.name ? room.name : String(room || '');
        if (!roomName) return;
        const option = document.createElement('option');
        option.value = roomName;
        option.textContent = roomName;
        if (room && room.id) {
            option.dataset.roomId = room.id;
        }
        select.appendChild(option);
    });
};

// Dodawanie nowego pokoju
window.addNewRoom = function() {
    const input = document.getElementById('newRoomName');
    const name = input.value.trim();
    
    if (!name) return;
    
    fetch('/api/rooms', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ room: name })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            input.value = ''; // Wyczyść pole
            if (window.showNotification) window.showNotification('Pokój dodany!', 'success');
            window.loadKanban(); // Przeładuj kanban
        } else {
            if (window.showNotification) window.showNotification(data.message || 'Błąd podczas dodawania pokoju', 'error');
        }
    });
};

// Dodawanie nowego urządzenia
window.addNewDevice = function() {
    const nameInput = document.getElementById('newDeviceName');
    const typeSelect = document.getElementById('newDeviceType');
    const roomSelect = document.getElementById('newDeviceRoom');
    
    const name = nameInput.value.trim();
    const type = typeSelect.value;
    const room = roomSelect.value || null; // null dla "Nieprzypisane"
    const selectedOption = roomSelect.options[roomSelect.selectedIndex];
    const roomId = selectedOption && selectedOption.dataset ? selectedOption.dataset.roomId || null : null;
    
    if (!name || !type) return;
    
    const endpoint = type === 'light' ? '/api/buttons' : '/api/temperature_controls';
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ name, room, room_id: roomId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            nameInput.value = ''; // Wyczyść pole nazwy
            if (window.showNotification) window.showNotification('Urządzenie dodane!', 'success');
            window.loadKanban(); // Przeładuj kanban
        } else {
            if (window.showNotification) window.showNotification(data.message || 'Błąd podczas dodawania urządzenia', 'error');
        }
    });
};

// --- Nadpisanie ładowania list na Kanban ---
window.loadKanban = function() {
    console.log('window.loadKanban called');
    Promise.all([
        window.app.getRooms(true),
        fetch('/api/buttons').then(r => r.json()),
        fetch('/api/temperature_controls').then(r => r.json())
    ]).then(([rooms, buttons, controls]) => {
        console.log('Promise.all resolved', rooms, buttons, controls);
        // Handle API responses that return {data: [...], status: 'success'}
        const normalizedRooms = window.normalizeRoomsData ? window.normalizeRoomsData(rooms) : (Array.isArray(rooms) ? rooms : []);
        let normalizedButtons = (buttons && Array.isArray(buttons.data)) ? buttons.data : (Array.isArray(buttons) ? buttons : []);
        let normalizedControls = (controls && Array.isArray(controls.data)) ? controls.data : (Array.isArray(controls) ? controls : []);

        normalizedButtons = normalizedButtons.map(button => ({ ...button, type: 'light' }));
        normalizedControls = normalizedControls.map(control => ({ ...control, type: 'thermostat' }));

        window.updateRoomSelect(normalizedRooms); // Aktualizuj selectbox
        window.renderKanbanLists(normalizedRooms, normalizedButtons, normalizedControls);
    }).catch(e => {
        console.error('Promise.all error', e);
    });
};

document.addEventListener('DOMContentLoaded', function () {
    window.loadKanban();
});

// --- Obsługa socket.io dla aktualizacji na żywo (jeśli jest dostępny socket) ---
if (window.io) {
    const socket = io();
    // Zamiast updateRoomsList itp. wywołuj window.loadKanban
    socket.on('update_rooms', function (rooms) {
        window.loadKanban();
    });
    socket.on('update_buttons', function (buttons) {
        window.loadKanban();
    });
    socket.on('update_temperature_controls', function (controls) {
        window.loadKanban();
    });
}