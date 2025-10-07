/* ============================== */
/*   Home Settings JavaScript     */
/* ============================== */

// Initialize home settings page
function initHomeSettings() {
    const homeId = document.getElementById('home-data')?.dataset.homeId;
    if (!homeId) {
        console.error('Home ID not found');
        return;
    }

    // Home info form handler
    const homeInfoForm = document.getElementById('homeInfoForm');
    if (homeInfoForm) {
        homeInfoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                name: formData.get('name'),
                description: formData.get('description')
            };
            
            // API call to update home info
            fetch(`/api/home/${homeId}/info/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    showNotification('Informacje o domu zostały zaktualizowane', 'success');
                } else {
                    showNotification(result.error || 'Wystąpił błąd podczas aktualizacji', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Wystąpił błąd podczas aktualizacji', 'error');
            });
        });
    }

    // Invite user form handler
    const inviteUserForm = document.getElementById('inviteUserForm');
    if (inviteUserForm) {
        inviteUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                email: formData.get('email'),
                role: formData.get('role')
            };
            
            // API call to invite user
            fetch(`/api/home/${homeId}/users/invite`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    showNotification('Zaproszenie zostało wysłane', 'success');
                    this.reset();
                } else {
                    showNotification(result.error || 'Wystąpił błąd podczas wysyłania zaproszenia', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Wystąpił błąd podczas wysyłania zaproszenia', 'error');
            });
        });
    }
}

// Confirm home deletion with two-step confirmation
function confirmDeleteHome(event) {
    const button = event.currentTarget;
    const buttonText = document.getElementById('deleteHomeBtnText');
    const homeId = document.getElementById('home-data')?.dataset.homeId;
    const homeName = document.getElementById('home-data')?.dataset.homeName;
    
    if (!homeId) {
        showNotification('Nie można znaleźć ID domu', 'error');
        return;
    }
    
    // If button is already in confirm state, proceed with deletion
    if (button.classList.contains('confirm-state')) {
        button.disabled = true;
        buttonText.textContent = 'Usuwanie...';
        
        // Call delete API
        fetch(`/api/home/${homeId}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showNotification('Dom został usunięty', 'success');
                // Redirect to home selection after deletion
                setTimeout(() => {
                    window.location.href = '/home/select';
                }, 2000);
            } else {
                showNotification(result.error || 'Wystąpił błąd podczas usuwania domu', 'error');
                button.disabled = false;
                buttonText.textContent = 'Usuń dom';
                button.classList.remove('confirm-state');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Wystąpił błąd podczas usuwania domu', 'error');
            button.disabled = false;
            buttonText.textContent = 'Usuń dom';
            button.classList.remove('confirm-state');
        });
    } else {
        // First click - fetch deletion info and show warning
        fetch(`/api/home/${homeId}/deletion-info`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const info = result.data;
                // Show what will be deleted
                showNotification(
                    `Usunięcie "${homeName}" usunie: ${info.room_count} pokoi, ${info.device_count} urządzeń, ${info.user_count} użytkowników, ${info.automation_count} automatyzacji. Kliknij ponownie aby potwierdzić.`,
                    'warning'
                );
                
                // Change button to confirm state
                button.classList.add('confirm-state');
                buttonText.textContent = '✓ Potwierdź usunięcie';
                
                // Reset after 5 seconds
                setTimeout(() => {
                    if (button.classList.contains('confirm-state')) {
                        button.classList.remove('confirm-state');
                        buttonText.textContent = 'Usuń dom';
                    }
                }, 5000);
            } else {
                showNotification('Nie można pobrać informacji o domu', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Wystąpił błąd podczas pobierania informacji', 'error');
        });
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initHomeSettings);
