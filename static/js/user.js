document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('userProfileForm');
    const profilePictureInput = document.getElementById('profilePictureInput');

    // Aktualizuj dane w menu użytkownika i avatarze po zmianie profilu lub zdjęcia
    function updateUserMenu({ name, profile_picture, role }) {
        // Zaktualizuj avatar w menu (prawy górny róg)
        const avatarImg = document.querySelector('#user-menu-handle .user-avatar');
        if (avatarImg && profile_picture) {
            avatarImg.src = profile_picture;
            // Add error handler for dynamically loaded images
            avatarImg.onerror = function() {
                this.onerror = null;
                this.src = '/static/profile_pictures/podstawowe.jpg';
            };
        }
        // Zaktualizuj nazwę i rolę w dropdownie
        const menuUsername = document.querySelector('#user-menu .user-menu-username');
        if (menuUsername && name) {
            menuUsername.textContent = name;
        }
        const menuRole = document.querySelector('#user-menu .user-menu-role');
        if (menuRole && role) {
            menuRole.textContent = 'Uprawnienia: ' + role;
        }
    }

    // Pobierz aktualne dane użytkownika z backendu i zaktualizuj menu/avatar
    async function refreshUserData() {
        try {
            const response = await fetch('/api/user/profile', {
                method: 'GET',
                headers: { 'X-CSRFToken': window.getCSRFToken() }
            });
            if (response.ok) {
                const data = await response.json();
                updateUserMenu({
                    name: data.name,
                    profile_picture: data.profile_picture,
                    role: data.role
                });
                // Zaktualizuj pole loginu i avatar na stronie profilu
                if (document.getElementById('userName')) {
                    document.getElementById('userName').value = data.name;
                }
                if (document.getElementById('profilePicture')) {
                    const profilePic = document.getElementById('profilePicture');
                    profilePic.src = data.profile_picture;
                    // Add error handler for dynamically loaded images
                    profilePic.onerror = function() {
                        this.onerror = null;
                        this.src = '/static/profile_pictures/podstawowe.jpg';
                    };
                }
            }
        } catch (e) { /* ignore */ }
    }

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
                    'X-CSRFToken': window.getCSRFToken()
                },
                body: formData
            });

            const data = await response.json();
            
            if (response.ok) {
                await refreshUserData();
                showNotification(data.message || 'Zdjęcie profilowe zostało zaktualizowane.', 'success');
            } else {
                showNotification(data.message || 'Wystąpił błąd podczas aktualizacji zdjęcia.', 'error');
            }
        } catch (error) {
            showNotification('Wystąpił błąd podczas wysyłania zdjęcia.', 'error');
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
                showNotification('Wprowadź aktualne hasło.', 'error');
                return;
            }
            if (!newPassword) {
                showNotification('Wprowadź nowe hasło.', 'error');
                return;
            }
            if (newPassword !== confirmPassword) {
                showNotification('Nowe hasło i potwierdzenie nie są identyczne.', 'error');
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
                    'X-CSRFToken': window.getCSRFToken()
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            if (response.ok && data.logout) {
                window.location.href = '/logout?changed=1';
                return;
            } else if (response.ok) {
                showNotification(data.message || 'Zapisano zmiany.', 'success');
                await refreshUserData();
            } else {
                showNotification(data.message || 'Wystąpił błąd podczas aktualizacji profilu.', 'error');
            }
        } catch (error) {
            showNotification('Wystąpił błąd podczas zapisywania zmian.', 'error');
            console.error('Error:', error);
        }
    });

});