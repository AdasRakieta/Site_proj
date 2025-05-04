document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('userProfileForm');
    const profilePictureInput = document.getElementById('profilePictureInput');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    // Handle profile picture change
    profilePictureInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('profile_picture', file);

        try {
            const response = await fetch('/api/user/profile-picture', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            });

            const data = await response.json();
            
            if (response.ok) {
                // Update the profile picture in the UI
                document.getElementById('profilePicture').src = data.profile_picture_url;
                showMessage('Zdjęcie profilowe zostało zaktualizowane.', 'success');
            } else {
                showMessage(data.message || 'Wystąpił błąd podczas aktualizacji zdjęcia.', 'error');
            }
        } catch (error) {
            showMessage('Wystąpił błąd podczas wysyłania zdjęcia.', 'error');
            console.error('Error:', error);
        }
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = {
            name: document.getElementById('userName').value,
            email: document.getElementById('userEmail').value
        };

        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        // Add password change if provided
        if (currentPassword || newPassword || confirmPassword) {
            if (!currentPassword) {
                showMessage('Wprowadź aktualne hasło.', 'error');
                return;
            }
            if (!newPassword) {
                showMessage('Wprowadź nowe hasło.', 'error');
                return;
            }
            if (newPassword !== confirmPassword) {
                showMessage('Nowe hasło i potwierdzenie nie są identyczne.', 'error');
                return;
            }
            formData.current_password = currentPassword;
            formData.new_password = newPassword;
        }

        try {
            const response = await fetch('/api/user/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
            if (response.ok) {
                showMessage('Profil został zaktualizowany pomyślnie.', 'success');
                // Clear password fields
                document.getElementById('currentPassword').value = '';
                document.getElementById('newPassword').value = '';
                document.getElementById('confirmPassword').value = '';
            } else {
                showMessage(data.message || 'Wystąpił błąd podczas aktualizacji profilu.', 'error');
            }
        } catch (error) {
            showMessage('Wystąpił błąd podczas zapisywania zmian.', 'error');
            console.error('Error:', error);
        }
    });

    // Helper function to show messages
    function showMessage(message, type) {
        const existingMessage = document.querySelector('.message');
        if (existingMessage) {
            existingMessage.remove();
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}-message`;
        messageElement.textContent = message;

        form.insertBefore(messageElement, form.firstChild);

        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }
});