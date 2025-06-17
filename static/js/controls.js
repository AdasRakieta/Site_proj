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
function renderKanbanLists(rooms, buttons, controls) {
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

    // Najpierw dodaj stały kontener "Nieprzypisane"
    const unassignedColumn = createKanbanColumn('Nieprzypisane', 
        buttons.filter(b => !b.room), 
        controls.filter(c => !c.room),
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
        const column = createKanbanColumn(roomObj, 
            buttons.filter(button => button.room === roomObj.name),
            controls.filter(control => control.room === roomObj.name)
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
            .map(col => col.querySelector('h3').textContent);
        
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
    column.style.display = 'flex';
    column.style.flexDirection = 'column';
    column.style.margin = '10px';
    column.style.padding = '10px';
    column.style.background = isFixed ? 'rgba(0,0,0,0.2)' : 'rgba(0,0,0,0.1)';
    column.style.borderRadius = '8px';
    column.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
    column.style.minWidth = '250px';
    column.style.cursor = 'default';

    const header = document.createElement('div');
    header.className = 'kanban-column-header';
    header.style.textAlign = 'center';
    header.style.marginBottom = '10px';
    header.style.padding = '8px';
    header.style.borderRadius = '4px';
    header.style.background = isFixed ? 'rgba(0,0,0,0.15)' : 'rgba(0,0,0,0.1)';
    header.style.cursor = isFixed ? 'default' : 'move';
    // Use room.name if room is an object, otherwise use room as string
    const roomName = typeof room === 'object' && room !== null ? room.name : room;
    header.innerHTML = `<h3 style="margin:0;">${roomName}</h3>`;
    if (!isFixed) {
        header.setAttribute('data-drag-handle', 'true');
        if (window.updateColumnHeader) {
            setTimeout(() => window.updateColumnHeader(column, roomName), 0);
        }
        // Set data-room-id to room.id if available, else to name
        const roomId = typeof room === 'object' && room !== null && room.id ? room.id : roomName;
        column.setAttribute('data-room-id', roomId);
    }
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
        li.style.display = 'flex';
        li.style.flexDirection = 'column';
        li.style.justifyContent = 'center';
        li.style.alignItems = 'center';
        li.style.width = '90%';
        li.style.height = '100px';
        li.style.background = 'rgba(0,0,0,0.4)';
        li.style.borderRadius = '8px';
        li.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
        li.style.margin = '10px';
        li.innerHTML = `<span class="kanban-card-content" style="font-size:1.1em;font-weight:500;">${device.name} - ${device.type}</span>`;
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
function updateDeviceOrders(targetList, room) {
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
            body: JSON.stringify({ room: room, order: lightsOrder })
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
            body: JSON.stringify({ room: room, order: thermostatsOrder })
        }).then(r => r.json())
          .then(data => console.log('Thermostats order updated:', data));
    }
}

// Funkcje obsługi dodawania z Kanban
window.addDeviceFromKanban = function(name, type, room) {
    const endpoint = type === 'light' ? '/api/buttons' : '/api/temperature_controls';
    fetch(endpoint, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ name, room })
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
        if (data.status === 'success') window.loadKanban();
        else alert('Błąd usuwania urządzenia: ' + (data.message || 'Nieznany błąd'));
    });
};

// Edycja inline w stylu Kanban
function startEditDeviceKanban(device, li) {
    li.innerHTML = `<input type='text' class='kanban-edit-input' value='${device.name}'/><div class='kanban-edit-btns' ><button class='kanban-save-btn'>💾</button><button class='kanban-cancel-btn'>✖</button></div>`;
    li.querySelector('.kanban-save-btn').onclick = () => {
        const newName = li.querySelector('input').value.trim();
        if (!newName || newName === device.name) return window.loadKanban();
        const endpoint = device.type === 'light' ? `/api/buttons/${device.id}` : `/api/temperature_controls/${device.id}`;
        fetch(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
            body: JSON.stringify({ name: newName })
        }).then(r => r.json()).then(() => window.loadKanban());
    };
    li.querySelector('.kanban-cancel-btn').onclick = () => window.loadKanban();
}

// Aktualizacja selectboxa z pokojami
function updateRoomSelect(rooms) {
    const select = document.getElementById('newDeviceRoom');
    if (!select) return;

    // Zachowaj pierwszy option (Nieprzypisane)
    const firstOption = select.firstChild;
    select.innerHTML = '';
    select.appendChild(firstOption);

    // Dodaj pozostałe pokoje
    rooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room;
        option.textContent = room;
        select.appendChild(option);
    });
}

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
            window.loadKanban(); // Przeładuj kanban
        } else {
            alert(data.message || 'Błąd podczas dodawania pokoju');
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
    
    if (!name || !type) return;
    
    const endpoint = type === 'light' ? '/api/buttons' : '/api/temperature_controls';
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ name, room })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            nameInput.value = ''; // Wyczyść pole nazwy
            window.loadKanban(); // Przeładuj kanban
        } else {
            alert(data.message || 'Błąd podczas dodawania urządzenia');
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
        buttons.forEach(button => button.type = 'light');
        controls.forEach(control => control.type = 'thermostat');
        updateRoomSelect(rooms); // Aktualizuj selectbox
        renderKanbanLists(rooms, buttons, controls);
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