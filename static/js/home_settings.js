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
                    showNotification('Nazwa domu została pomyślnie zaktualizowana', 'success');
                    
                    // Update the header name in settings-header
                    const headerName = document.querySelector('.settings-header h2');
                    if (headerName && result.data && result.data.name) {
                        headerName.textContent = result.data.name;
                    }
                    
                    // Update description if it exists
                    if (result.data && result.data.description !== undefined) {
                        const descriptionElement = document.querySelector('.settings-header .home-description');
                        if (result.data.description) {
                            if (descriptionElement) {
                                descriptionElement.textContent = result.data.description;
                            } else {
                                // Create description element if it doesn't exist
                                const headerLeft = document.querySelector('.settings-header .header-left');
                                const newDescription = document.createElement('p');
                                newDescription.className = 'home-description';
                                newDescription.textContent = result.data.description;
                                headerLeft.insertBefore(newDescription, headerLeft.querySelector('.header-stats'));
                            }
                        } else if (descriptionElement) {
                            // Remove description if it's empty
                            descriptionElement.remove();
                        }
                    }
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
                showNotification('Dom został pomyślnie usunięty! Przekierowywanie...', 'success');
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
                    `⚠️ Usunięcie "${homeName}" spowoduje trwałe usunięcie:\n• ${info.room_count} pokoi\n• ${info.device_count} urządzeń\n• ${info.user_count} użytkowników\n• ${info.automation_count} automatyzacji\n\nKliknij ponownie, aby potwierdzić.`,
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

// Handle location form and geolocation
function initLocationHandlers(homeId) {
    let citiesCache = [];
    let selectedCity = null;
    
    // City autocomplete functionality
    const cityInput = document.getElementById('homeCity');
    const suggestionsDiv = document.getElementById('citySuggestions');
    
    if (cityInput && suggestionsDiv) {
        let searchTimeout;
        const wrapper = cityInput.closest('.autocomplete-wrapper');
        
        // Search cities as user types
        cityInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const searchTerm = this.value.trim();
            
            if (searchTerm.length < 2) {
                suggestionsDiv.innerHTML = '';
                suggestionsDiv.style.display = 'none';
                if (wrapper) wrapper.classList.remove('active');
                return;
            }
            
            searchTimeout = setTimeout(() => {
                fetch(`/api/cities/search?q=${encodeURIComponent(searchTerm)}&limit=10`)
                    .then(response => response.json())
                    .then(result => {
                        if (result.success && result.cities.length > 0) {
                            displayCitySuggestions(result.cities);
                        } else {
                            suggestionsDiv.innerHTML = '<div class="suggestion-item no-results">Nie znaleziono miast</div>';
                            suggestionsDiv.style.display = 'block';
                            if (wrapper) wrapper.classList.add('active');
                        }
                    })
                    .catch(error => {
                        console.error('Error searching cities:', error);
                    });
            }, 300);
        });
        
        // Display city suggestions
        function displayCitySuggestions(cities) {
            suggestionsDiv.innerHTML = '';
            
            cities.forEach(city => {
                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.innerHTML = `
                    <div class="city-name">${city.name}, ${city.admin_name || 'Polska'}</div>
                    <div class="city-info">${city.population ? city.population.toLocaleString() + ' mieszkańców' : ''}</div>
                `;
                
                item.addEventListener('click', () => {
                    selectCity(city);
                });
                
                suggestionsDiv.appendChild(item);
            });
            
            suggestionsDiv.style.display = 'block';
            if (wrapper) wrapper.classList.add('active');
        }
        
        // Select a city from suggestions
        function selectCity(city) {
            selectedCity = city;
            cityInput.value = city.name;
            document.getElementById('homeLatitude').value = city.latitude ? city.latitude.toFixed(6) : '';
            document.getElementById('homeLongitude').value = city.longitude ? city.longitude.toFixed(6) : '';
            document.getElementById('homeCountry').value = 'Poland';
            suggestionsDiv.style.display = 'none';
            if (wrapper) wrapper.classList.remove('active');
            
            showNotification(`Wybrano: ${city.name}${city.admin_name ? ', woj. ' + city.admin_name : ''}`, 'success');
        }
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!cityInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
                suggestionsDiv.style.display = 'none';
                if (wrapper) wrapper.classList.remove('active');
            }
        });
        
        // Keyboard navigation
        let selectedIndex = -1;
        cityInput.addEventListener('keydown', function(e) {
            const items = suggestionsDiv.querySelectorAll('.suggestion-item:not(.no-results)');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                updateSelectedItem(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                updateSelectedItem(items);
            } else if (e.key === 'Enter' && selectedIndex >= 0) {
                e.preventDefault();
                items[selectedIndex].click();
                selectedIndex = -1;
            } else if (e.key === 'Escape') {
                suggestionsDiv.style.display = 'none';
                if (wrapper) wrapper.classList.remove('active');
                selectedIndex = -1;
            }
        });
        
        function updateSelectedItem(items) {
            items.forEach((item, index) => {
                if (index === selectedIndex) {
                    item.classList.add('active');
                    item.scrollIntoView({ block: 'nearest' });
                } else {
                    item.classList.remove('active');
                }
            });
        }
    }
    
    // Home location form handler
    const homeLocationForm = document.getElementById('homeLocationForm');
    if (homeLocationForm) {
        homeLocationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                city: formData.get('city') || null,
                street: formData.get('street') || null,
                house_number: formData.get('house_number') || null,
                apartment_number: formData.get('apartment_number') || null,
                postal_code: formData.get('postal_code') || null,
                latitude: formData.get('latitude') || null,
                longitude: formData.get('longitude') || null,
                country: formData.get('country') || 'Poland',
                use_geocoding: true  // Enable geocoding by default
            };
            
            // Validate required field
            if (!data.city) {
                showNotification('Miasto jest wymagane', 'warning');
                return;
            }
            
            // Validate postal code format if provided
            if (data.postal_code && !/^\d{2}-\d{3}$/.test(data.postal_code)) {
                showNotification('Nieprawidłowy format kodu pocztowego (wymagany: XX-XXX)', 'warning');
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Zapisywanie...';
            
            // API call to update home location
            fetch(`/api/home/${homeId}/location/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;

                const ok = result && (result.success === true || result.status === 'success');
                if (ok) {
                    // Update coordinates in form if geocoding was used
                    if (result.data && result.data.geocoding_used) {
                        if (result.data.latitude) {
                            document.getElementById('homeLatitude').value = result.data.latitude.toFixed(6);
                        }
                        if (result.data.longitude) {
                            document.getElementById('homeLongitude').value = result.data.longitude.toFixed(6);
                        }
                        showNotification('Lokalizacja zapisana (współrzędne określone automatycznie)', 'success');
                    }
                    // Always confirm success, even if geocoding not used
                    showNotification('Lokalizacja domu została zapisana', 'success');
                } else {
                    showNotification(result?.error || 'Wystąpił błąd podczas aktualizacji lokalizacji', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
                showNotification('Wystąpił błąd podczas aktualizacji lokalizacji', 'error');
            });
        });
    }

    // Use my location button handler
    const useMyLocationBtn = document.getElementById('useMyLocationBtn');
    if (useMyLocationBtn) {
        useMyLocationBtn.addEventListener('click', function() {
            if (!navigator.geolocation) {
                showNotification('Geolokalizacja nie jest wspierana przez Twoją przeglądarkę', 'error');
                return;
            }

            // Show loading state
            this.disabled = true;
            this.textContent = '⏳ Pobieranie lokalizacji...';

            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;

                    // Validate Poland boundaries
                    if (lat < 49.0 || lat > 54.9 || lon < 14.1 || lon > 24.2) {
                        showNotification('Twoja lokalizacja jest poza Polską', 'warning');
                        this.disabled = false;
                        this.textContent = '📍 Użyj mojej lokalizacji';
                        return;
                    }

                    // Update coordinates immediately
                    document.getElementById('homeLatitude').value = lat.toFixed(6);
                    document.getElementById('homeLongitude').value = lon.toFixed(6);
                    document.getElementById('homeCountry').value = 'Poland';

                    // Reverse geocode to get address
                    try {
                        const response = await fetch('/api/geocode/reverse', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ latitude: lat, longitude: lon })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success && result.data) {
                            const data = result.data;
                            
                            // Fill in address fields from reverse geocoding
                            if (data.city) {
                                document.getElementById('homeCity').value = data.city;
                            }
                            if (data.street) {
                                document.getElementById('homeStreet').value = data.street;
                            }
                            if (data.house_number) {
                                document.getElementById('homeHouseNumber').value = data.house_number;
                            }
                            if (data.postal_code) {
                                document.getElementById('homePostalCode').value = data.postal_code;
                            }
                            
                            const addressParts = [data.city, data.state].filter(Boolean);
                            showNotification(`Lokalizacja: ${addressParts.join(', ')}`, 'success');
                        } else {
                            showNotification('Współrzędne pobrane pomyślnie', 'success');
                        }
                    } catch (error) {
                        console.error('Error in reverse geocoding:', error);
                        showNotification('Współrzędne pobrane pomyślnie', 'success');
                    }

                    this.disabled = false;
                    this.textContent = '📍 Użyj mojej lokalizacji';
                },
                (error) => {
                    console.error('Geolocation error:', error);
                    let message = 'Nie udało się pobrać lokalizacji';
                    
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            message = 'Odmówiono dostępu do lokalizacji. Sprawdź ustawienia przeglądarki.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            message = 'Lokalizacja niedostępna';
                            break;
                        case error.TIMEOUT:
                            message = 'Przekroczono czas oczekiwania na lokalizację';
                            break;
                    }
                    
                    showNotification(message, 'error');
                    this.disabled = false;
                    this.textContent = '📍 Użyj mojej lokalizacji';
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        });
    }
    
    // Add live geocoding when street/house number changes
    const streetInput = document.getElementById('homeStreet');
    const houseNumberInput = document.getElementById('homeHouseNumber');
    const postalCodeInput = document.getElementById('homePostalCode');
    
    if (streetInput && houseNumberInput && cityInput) {
        // Debounce geocoding requests
        let geocodeTimeout;
        
        function triggerGeocoding() {
            clearTimeout(geocodeTimeout);
            
            const city = cityInput.value.trim();
            const street = streetInput.value.trim();
            const houseNumber = houseNumberInput.value.trim();
            const postalCode = postalCodeInput ? postalCodeInput.value.trim() : '';
            
            // Only geocode if we have at least city and street
            if (!city || !street) {
                return;
            }
            
            geocodeTimeout = setTimeout(() => {
                // Show loading indicator
                const latInput = document.getElementById('homeLatitude');
                const lonInput = document.getElementById('homeLongitude');
                
                if (latInput && lonInput) {
                    latInput.value = '⏳ Pobieranie...';
                    lonInput.value = '⏳ Pobieranie...';
                }
                
                // Build geocoding request
                const geocodeData = {
                    city: city,
                    street: street,
                    house_number: houseNumber || null,
                    postal_code: postalCode || null,
                    country: 'Poland'
                };
                
                // Call backend geocoding (we'll create this endpoint)
                fetch('/api/geocode/address', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(geocodeData)
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success && result.data) {
                        if (latInput && lonInput) {
                            latInput.value = result.data.latitude.toFixed(6);
                            lonInput.value = result.data.longitude.toFixed(6);
                        }
                        console.log('✓ Geocoded:', result.data.display_name);
                    } else {
                        if (latInput && lonInput) {
                            latInput.value = '';
                            lonInput.value = '';
                        }
                        console.log('⚠ Geocoding failed');
                    }
                })
                .catch(error => {
                    console.error('Error geocoding:', error);
                    if (latInput && lonInput) {
                        latInput.value = '';
                        lonInput.value = '';
                    }
                });
            }, 1000); // Wait 1 second after user stops typing
        }
        
        streetInput.addEventListener('input', triggerGeocoding);
        houseNumberInput.addEventListener('input', triggerGeocoding);
        if (postalCodeInput) {
            postalCodeInput.addEventListener('input', triggerGeocoding);
        }
    }
}

// Calculate distance between two coordinates in km (Haversine formula)
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initHomeSettings();
    const homeElement = document.getElementById('home-data');
    if (homeElement) {
        const homeId = homeElement.dataset.homeId;
        initLocationHandlers(homeId);
    }
});
