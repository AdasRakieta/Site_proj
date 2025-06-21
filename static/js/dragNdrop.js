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
    const kanbanContainer = document.getElementById('kanbanContainer');

    if (controlPanel) {
        if (enabled) {
            controlPanel.classList.add('active');
            editButton.style.display = 'none';
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

        // Add room name in h3
        const roomNameH3 = document.createElement('h3');
        roomNameH3.style.margin = '0';
        roomNameH3.textContent = roomName;
        header.appendChild(roomNameH3);

        if (roomName !== 'Nieprzypisane') {
            // Container for edit controls
            const buttonContainer = document.createElement('div');
            buttonContainer.style.position = 'absolute';
            buttonContainer.style.right = '8px';
            buttonContainer.style.top = '50%';
            buttonContainer.style.transform = 'translateY(-50%)';
            buttonContainer.style.display = 'flex';
            buttonContainer.style.gap = '4px';
            buttonContainer.style.alignItems = 'center';

            // Edit button (ołówek)
            const editBtn = document.createElement('button');
            editBtn.className = 'edit-room-button';
            editBtn.title = 'Edytuj nazwę pokoju';
            editBtn.innerHTML = '⁝';
            editBtn.style.background = 'none';
            editBtn.style.border = 'none';
            editBtn.style.cursor = 'pointer';
            editBtn.style.fontSize = '1.1em';

            // Input for editing name (hidden by default)
            const roomNameInputEdit = document.createElement('input');
            roomNameInputEdit.type = 'text';
            roomNameInputEdit.className = 'room-name-input-edit';
            roomNameInputEdit.value = roomName;
            roomNameInputEdit.style.display = 'none';

            // Kontener na przyciski edycji
            const editActionsDiv = document.createElement('div');
            editActionsDiv.className = 'room-edit-container';

            // Save button (✔)
            const saveBtnEdit = document.createElement('button');
            saveBtnEdit.className = 'save-room-button-edit';
            saveBtnEdit.title = 'Zapisz';
            saveBtnEdit.innerHTML = '✔';
            

            // Cancel button (✖)
            const cancelBtnEdit = document.createElement('button');
            cancelBtnEdit.className = 'cancel-room-button-edit';
            cancelBtnEdit.title = 'Anuluj';
            cancelBtnEdit.innerHTML = '✖';
            

            // Delete button (🗑)
            const deleteRoomBtnEdit = document.createElement('button');
            deleteRoomBtnEdit.className = 'delete-room-button-edit';
            deleteRoomBtnEdit.title = 'Usuń pokój';
            deleteRoomBtnEdit.innerHTML = '🗑';

            // Show edit controls
            editBtn.onclick = (e) => {
                e.stopPropagation();
                roomNameH3.style.display = 'none';
                editBtn.style.display = 'none';
                roomNameInputEdit.style.display = '';
                editActionsDiv.style.display = 'flex';
                
                roomNameInputEdit.focus();
            };

            // Save new name
            saveBtnEdit.onclick = async (e) => {
                e.stopPropagation();
                const newName = roomNameInputEdit.value.trim();
                if (newName && newName !== roomNameH3.textContent) {
                    const roomId = columnElement.getAttribute('data-room-id');
                    try {
                        await fetch(`/api/rooms/${roomId}`, {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': window.getCSRFToken()
                            },
                            body: JSON.stringify({ name: newName })
                        });
                        roomNameH3.textContent = newName;
                        if (window.updateRoomSelect) window.updateRoomSelect();
                    } catch (error) {
                        alert('Nie udało się zmienić nazwy pokoju');
                    }
                }
                // Exit edit mode
                roomNameH3.style.display = '';
                editBtn.style.display = '';
                roomNameInputEdit.style.display = 'none';
                editActionsDiv.style.display = 'none';
            };

            // Cancel editing
            cancelBtnEdit.onclick = (e) => {
                e.stopPropagation();
                roomNameInputEdit.value = roomNameH3.textContent;
                roomNameH3.style.display = '';
                editBtn.style.display = '';
                roomNameInputEdit.style.display = 'none';
                editActionsDiv.style.display = 'none';
            };

            // Delete room
            deleteRoomBtnEdit.onclick = async (e) => {
                e.stopPropagation();
                // Zamień śmietnik na haczyk potwierdzenia
                deleteRoomBtnEdit.style.display = 'none';
                // Dodaj przycisk potwierdzenia
                const confirmBtnEdit = document.createElement('button');
                confirmBtnEdit.className = 'confirm-delete-button-edit';
                confirmBtnEdit.title = 'Potwierdź usunięcie pokoju';
                confirmBtnEdit.innerHTML = '✔';
                // Po kliknięciu haczyka - usuń pokój
                confirmBtnEdit.onclick = async (ev) => {
                    ev.stopPropagation();
                    try {
                        await deleteRoom(columnElement);
                        if (window.showNotification) window.showNotification('Pokój usunięty!', 'success');
                    } catch (err) {
                        if (window.showNotification) window.showNotification('Nie udało się usunąć pokoju', 'error');
                    }
                    confirmBtnEdit.remove();
                };
                // Po 5 sekundach przywróć śmietnik jeśli nie kliknięto
                const timeout = setTimeout(() => {
                    confirmBtnEdit.remove();
                    deleteRoomBtnEdit.style.display = '';
                }, 5000);
                confirmBtnEdit.onclick = (ev) => {
                    clearTimeout(timeout);
                    confirmBtnEdit.remove();
                    deleteRoomBtnEdit.style.display = '';
                    // ...usuwanie pokoju jak wyżej...
                    (async () => {
                        try {
                            await deleteRoom(columnElement);
                            if (window.showNotification) window.showNotification('Pokój usunięty!', 'success');
                        } catch (err) {
                            if (window.showNotification) window.showNotification('Nie udało się usunąć pokoju', 'error');
                        }
                    })();
                };
                // Dodaj haczyk obok śmietnika
                editActionsDiv.appendChild(confirmBtnEdit);
            };

            // Keyboard shortcuts
            roomNameInputEdit.onkeydown = (e) => {
                if (e.key === 'Enter') saveBtnEdit.onclick(e);
                if (e.key === 'Escape') cancelBtnEdit.onclick(e);
            };

            // Dodaj przyciski do kontenera edycji
            editActionsDiv.appendChild(saveBtnEdit);
            editActionsDiv.appendChild(cancelBtnEdit);
            editActionsDiv.appendChild(deleteRoomBtnEdit);

            // Dodaj elementy do głównego kontenera
            buttonContainer.appendChild(editBtn);
            buttonContainer.appendChild(roomNameInputEdit);
            buttonContainer.appendChild(editActionsDiv);

            header.appendChild(buttonContainer);
        }
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

async function deleteRoom(columnElement) {
    // Try to get the room name from .room-name, fallback to h3, fallback to 'Pokój'
    let roomName = null;
    const nameSpan = columnElement.querySelector('.room-name');
    if (nameSpan) {
        roomName = nameSpan.textContent;
    } else {
        // Fallback: try h3
        const h3 = columnElement.querySelector('h3');
        if (h3) {
            roomName = h3.textContent;
        } else {
            roomName = 'Pokój';
        }
    }
        
        try {
            const roomId = columnElement.getAttribute('data-room-id');
            const response = await fetch(`/api/rooms/${roomId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': window.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete room');
            }

            // Update pendingChanges to track room deletion
            if (pendingChanges.columnMoves) {
                pendingChanges.columnMoves = pendingChanges.columnMoves.filter(room => room.id !== roomId);
            }

            // Remove the column from DOM
            columnElement.remove();

            // Update room select dropdown if the function exists
            if (window.updateRoomSelect) {
                window.updateRoomSelect();
            }
        } catch (error) {
            console.error('Error deleting room:', error);
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
