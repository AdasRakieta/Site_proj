console.log('dragNdrop.js loaded');
console.log('dragula available?', typeof dragula !== 'undefined');

// Edit mode state and changes tracking
window.editMode = false;
let pendingChanges = {
    // Używamy obiektu zamiast tablicy aby przechowywać tylko ostatnią zmianę dla każdego ID
    deviceMoves: {},
    columnMoves: null
};

// Dynamic Kanban Dragula initialization for room columns
window.initDynamicKanbanDragula = function(onDropHandler) {
    console.log('dragNdrop.js - initDynamicKanbanDragula start');
    var kanbanContainer = document.getElementById('kanbanContainer');
    if (!kanbanContainer) {
        console.error('No kanbanContainer found');
        return;
    }
    
    var columns = kanbanContainer.querySelectorAll('.kanban-list');
    console.log('Found columns:', columns.length);
    if (!columns.length) return;

    if (window.kanbanDragulaInstance && window.kanbanDragulaInstance.destroy) {
        window.kanbanDragulaInstance.destroy();
    }

    // Dodanie debounce dla obsługi przeciągania
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Konfiguracja Dragula z optymalizacją wydajności
    window.kanbanDragulaInstance = dragula(Array.from(columns), {
        moves: function (el, container, handle) {
            if (!window.editMode) return false;
            if (!el || !container) return false;
            if (el.classList.contains('kanban-add-card')) return false;
            return true;
        },
        accepts: function (el, target, source, sibling) {
            if (!window.editMode) return false;
            if (!el || !target) return false;
            return true;
        },
        invalid: function (el, handle) {
            return false;
        },
        direction: 'vertical',
        removeOnSpill: false,
        revertOnSpill: true,
        mirrorContainer: kanbanContainer,
        deadzone: 5,
        throttleTimer: 50
    });

    window.kanbanDragulaInstance
        .on('drag', function(el) {
            if (!el || !window.editMode) return;
            requestAnimationFrame(() => {
                el.classList.add('is-moving');
            });
        })
        .on('drop', function(el, target, source, sibling) {
            if (!el || !target || !window.editMode) return;
            
            const deviceId = el.getAttribute('data-id');
            const deviceType = el.getAttribute('data-type');
            const newRoom = target.parentElement.querySelector('h3')?.textContent;
            const actualRoom = newRoom === 'Nieprzypisane' ? null : newRoom;
            
            // Store only the latest change for each device
            if (deviceId && deviceType) {
                pendingChanges.deviceMoves[deviceId] = {
                    id: deviceId,
                    type: deviceType,
                    newRoom: actualRoom,
                    target: target
                };
            }
        })
        .on('dragend', function(el) {
            if (!el || !window.editMode) return;
            el.classList.remove('is-moving');
            requestAnimationFrame(() => {
                el.classList.add('is-moved');
                setTimeout(() => {
                    el.classList.remove('is-moved');
                }, 300);
            });
        })
        .on('cancel', function(el) {
            if (!el || !window.editMode) return;
            el.classList.remove('is-moving');
        });

    console.log('Dragula initialized with', columns.length, 'columns');
    return window.kanbanDragulaInstance;
};

// Funkcja do włączania/wyłączania trybu edycji
window.toggleEditMode = function(enabled) {
    window.editMode = enabled;
    const controlPanel = document.querySelector('.control-panel');
    const editButton = document.getElementById('editModeButton');
    const saveButton = document.getElementById('saveModeButton');
    const cancelButton = document.getElementById('cancelModeButton');
    const kanbanContainer = document.getElementById('kanbanContainer');

    if (controlPanel) {
        if (enabled) {
            controlPanel.classList.add('active');
            editButton.style.display = 'none';
            saveButton.style.display = 'block';
            cancelButton.style.display = 'block';
            if (kanbanContainer) {
                kanbanContainer.classList.add('edit-mode');
            }
            // Reset pending changes
            pendingChanges = {
                deviceMoves: {},
                columnMoves: null
            };
        } else {
            controlPanel.classList.remove('active');
            editButton.style.display = 'block';
            saveButton.style.display = 'none';
            cancelButton.style.display = 'none';
            if (kanbanContainer) {
                kanbanContainer.classList.remove('edit-mode');
            }
        }
    }
};

// Save changes function
window.saveChanges = async function() {
    console.log('Saving changes:', pendingChanges);
    
    // Save column order if changed
    if (pendingChanges.columnMoves) {
        try {
            const response = await fetch('/api/rooms/order', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCSRFToken()
                },
                body: JSON.stringify({ rooms: pendingChanges.columnMoves })
            });
            const data = await response.json();
            console.log('Room order updated:', data);
        } catch (error) {
            console.error('Error saving room order:', error);
        }
    }

    // Save device moves - now only the last change for each device
    const deviceMoves = Object.values(pendingChanges.deviceMoves);
    for (const move of deviceMoves) {
        try {
            const endpoint = move.type === 'light' ? `/api/buttons/${move.id}` : `/api/temperature_controls/${move.id}`;
            await fetch(endpoint, {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCSRFToken()
                },
                body: JSON.stringify({ room: move.newRoom })
            });
            if (window.updateDeviceOrders) {
                window.updateDeviceOrders(move.target, move.newRoom);
            }
        } catch (error) {
            console.error('Error saving device move:', error);
        }
    }

    // Clear pending changes
    pendingChanges = {
        deviceMoves: {},
        columnMoves: null
    };

    // Exit edit mode
    window.toggleEditMode(false);
    
    // Reload kanban to show updated state
    if (window.loadKanban) {
        window.loadKanban();
    }
};

// Cancel changes function
window.cancelChanges = function() {
    // Clear pending changes
    pendingChanges = {
        deviceMoves: {},
        columnMoves: null
    };
    
    // Exit edit mode and reload data from server to restore original state
    window.toggleEditMode(false);
    
    // Przeładuj dane z serwera aby przywrócić oryginalny stan
    Promise.all([
        fetch('/api/rooms').then(r => r.json()),
        fetch('/api/buttons').then(r => r.json()),
        fetch('/api/temperature_controls').then(r => r.json())
    ]).then(([rooms, buttons, controls]) => {
        if (window.loadKanban) {
            // Add types to devices for proper rendering
            buttons.forEach(button => button.type = 'light');
            controls.forEach(control => control.type = 'thermostat');
            
            // Update room select and render kanban
            if (window.updateRoomSelect) {
                window.updateRoomSelect(rooms);
            }
            window.loadKanban();
        }
    }).catch(error => {
        console.error('Error restoring original state:', error);
    });
};

// Store column moves
window.storeColumnMove = function(roomOrder) {
    pendingChanges.columnMoves = roomOrder;
};

// Room management functions
function updateColumnHeader(columnElement, roomName) {
    const header = columnElement.querySelector('.kanban-column-header');
    if (header) {
        // Clear existing content
        header.innerHTML = '';
        
        // Add room name
        const roomNameSpan = document.createElement('span');
        roomNameSpan.className = 'room-name';
        roomNameSpan.textContent = roomName;
        header.appendChild(roomNameSpan);
        
        // Add name edit input (initially hidden)
        const roomNameInput = document.createElement('input');
        roomNameInput.type = 'text';
        roomNameInput.className = 'room-name-input';
        roomNameInput.value = roomName;
        header.appendChild(roomNameInput);

        // Add context menu button
        const menuBtn = document.createElement('button');
        menuBtn.className = 'room-menu-btn';
        menuBtn.textContent = '⁝';
        menuBtn.onclick = (e) => {
            e.stopPropagation();
            toggleRoomContextMenu(columnElement);
        };
        header.appendChild(menuBtn);

        // Add context menu
        const contextMenu = document.createElement('div');
        contextMenu.className = 'room-context-menu';
        
        const renameBtn = document.createElement('button');
        renameBtn.textContent = 'Zmień nazwę';
        renameBtn.onclick = () => startRenameRoom(columnElement);
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Usuń pokój';
        deleteBtn.onclick = () => deleteRoom(columnElement);
        
        contextMenu.appendChild(renameBtn);
        contextMenu.appendChild(deleteBtn);
        header.appendChild(contextMenu);
    }
}

function toggleRoomContextMenu(columnElement) {
    const allMenus = document.querySelectorAll('.room-context-menu');
    allMenus.forEach(menu => {
        if (menu !== columnElement.querySelector('.room-context-menu')) {
            menu.classList.remove('active');
        }
    });

    const menu = columnElement.querySelector('.room-context-menu');
    menu.classList.toggle('active');

    // Close menu when clicking outside
    const closeMenu = (e) => {
        if (!menu.contains(e.target) && !columnElement.querySelector('.room-menu-btn').contains(e.target)) {
            menu.classList.remove('active');
            document.removeEventListener('click', closeMenu);
        }
    };
    document.addEventListener('click', closeMenu);
}

function startRenameRoom(columnElement) {
    const header = columnElement.querySelector('.kanban-column-header');
    const nameSpan = header.querySelector('.room-name');
    const nameInput = header.querySelector('.room-name-input');
    const menu = header.querySelector('.room-context-menu');

    nameSpan.style.display = 'none';
    nameInput.classList.add('active');
    nameInput.focus();
    menu.classList.remove('active');

    function saveRoomName() {
        const newName = nameInput.value.trim();
        if (newName && newName !== nameSpan.textContent) {
            const roomId = columnElement.getAttribute('data-room-id');
            fetch(`/api/rooms/${roomId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCSRFToken()
                },
                body: JSON.stringify({ name: newName })
            })
            .then(response => response.json())
            .then(() => {
                nameSpan.textContent = newName;
                if (window.updateRoomSelect) {
                    window.updateRoomSelect();
                }
            })
            .catch(error => {
                console.error('Error updating room name:', error);
                alert('Nie udało się zmienić nazwy pokoju');
            });
        }
        nameSpan.style.display = '';
        nameInput.classList.remove('active');
    }

    nameInput.onblur = saveRoomName;
    nameInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
            saveRoomName();
        } else if (e.key === 'Escape') {
            nameInput.value = nameSpan.textContent;
            nameSpan.style.display = '';
            nameInput.classList.remove('active');
        }
    };
}

function deleteRoom(columnElement) {
    const roomName = columnElement.querySelector('.room-name').textContent;
    if (confirm(`Czy na pewno chcesz usunąć pokój "${roomName}"? Wszystkie przypisane urządzenia zostaną przeniesione do nieprzypisanych.`)) {
        const roomId = columnElement.getAttribute('data-room-id');
        fetch(`/api/rooms/${roomId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': window.getCSRFToken()
            }
        })
        .then(response => {
            if (response.ok) {
                columnElement.remove();
                if (window.updateRoomSelect) {
                    window.updateRoomSelect();
                }
            } else {
                throw new Error('Failed to delete room');
            }
        })
        .catch(error => {
            console.error('Error deleting room:', error);
            alert('Nie udało się usunąć pokoju');
        });
    }
}

// Inicjalizacja przycisków trybu edycji
document.addEventListener('DOMContentLoaded', function() {
    const editButton = document.getElementById('editModeButton');
    const saveButton = document.getElementById('saveModeButton');
    const cancelButton = document.getElementById('cancelModeButton');

    if (editButton) {
        editButton.addEventListener('click', function() {
            window.toggleEditMode(true);
        });
    }

    if (saveButton) {
        saveButton.addEventListener('click', window.saveChanges);
    }

    if (cancelButton) {
        cancelButton.addEventListener('click', window.cancelChanges);
    }
});

var createOptions = (function() {
    var dragOptions = document.querySelectorAll('.drag-options');
    
    // these strings are used for the checkbox labels
    var options = ['Research', 'Strategy', 'Inspiration', 'Execution'];
    
    // create the checkbox and labels here, just to keep the html clean. append the <label> to '.drag-options'
    function create() {
        for (var i = 0; i < dragOptions.length; i++) {

            options.forEach(function(item) {
                var checkbox = document.createElement('input');
                var label = document.createElement('label');
                var span = document.createElement('span');
                checkbox.setAttribute('type', 'checkbox');
                span.innerHTML = item;
                label.appendChild(span);
                label.insertBefore(checkbox, label.firstChild);
                label.classList.add('drag-options-label');
                dragOptions[i].appendChild(label);
            });

        }
    }
    
    return {
        create: create
    }
    
    
}());

var showOptions = (function () {
    
    // the 3 dot icon
    var more = document.querySelectorAll('.drag-header-more');
    
    function show() {
        // show 'drag-options' div when the more icon is clicked
        var target = this.getAttribute('data-target');
        var options = document.getElementById(target);
        options.classList.toggle('active');
    }
    
    
    function init() {
        for (i = 0; i < more.length; i++) {
            more[i].addEventListener('click', show, false);
        }
    }
    
    return {
        init: init
    }
}());

createOptions.create();
showOptions.init();
