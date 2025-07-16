document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('registerProfileForm');
    if (!form) return;

    function showMessage(message, type = 'error') {
        let msgDiv = document.getElementById('registerMessage');
        if (!msgDiv) {
            msgDiv = document.createElement('div');
            msgDiv.id = 'registerMessage';
            msgDiv.className = 'alert-msg';
            form.insertBefore(msgDiv, form.firstChild);
        }
        msgDiv.textContent = message;
        msgDiv.style.display = 'block';
        msgDiv.style.color = type === 'success' ? 'green' : 'crimson';
        setTimeout(() => { msgDiv.style.display = 'none'; }, 5000);
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('registerName').value.trim();
        const email = document.getElementById('registerEmail').value.trim();
        const password = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (!username || username.length < 3) {
            showMessage('Nazwa użytkownika musi mieć co najmniej 3 znaki.');
            return;
        }
        if (!email || !email.includes('@')) {
            showMessage('Podaj poprawny adres email.');
            return;
        }
        if (!password || password.length < 6) {
            showMessage('Hasło musi mieć co najmniej 6 znaków.');
            return;
        }
        if (password !== confirmPassword) {
            showMessage('Hasła nie są identyczne.');
            return;
        }

        // CSRF token
        let csrfToken = null;
        const input = document.querySelector('input[name="_csrf_token"]');
        if (input) csrfToken = input.value;
        if (!csrfToken) {
            const meta = document.querySelector('meta[name="csrf-token"]');
            if (meta) csrfToken = meta.getAttribute('content');
        }
        if (!csrfToken) {
            showMessage('Brak tokena CSRF. Odśwież stronę i spróbuj ponownie.');
            return;
        }

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify({ username, password, email })
            });
            const data = await response.json();
            if (response.ok && data.status === 'success') {
                showMessage('Rejestracja zakończona sukcesem! Możesz się zalogować.', 'success');
                setTimeout(() => { window.location.href = '/login'; }, 1500);
            } else {
                showMessage(data.message || 'Wystąpił błąd podczas rejestracji.');
            }
        } catch (error) {
            showMessage('Błąd połączenia z serwerem.');
        }
    });

    // Obsługa przycisku "Wróć"
    const returnBtn = form.querySelector('.return-button');
    if (returnBtn) {
        returnBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/login';
        });
    } else {
        console.error('Przycisk "Wróć" nie został znaleziony.');
    }
});