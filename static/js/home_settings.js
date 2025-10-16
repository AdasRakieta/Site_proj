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
        
        // Search cities as user types
        cityInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const searchTerm = this.value.trim();
            
            if (searchTerm.length < 2) {
                suggestionsDiv.innerHTML = '';
                suggestionsDiv.style.display = 'none';
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
        }
        
        // Select a city from suggestions
        function selectCity(city) {
            selectedCity = city;
            cityInput.value = city.name;
            document.getElementById('homeLatitude').value = city.latitude ? city.latitude.toFixed(6) : '';
            document.getElementById('homeLongitude').value = city.longitude ? city.longitude.toFixed(6) : '';
            document.getElementById('homeCountry').value = 'Poland';
            suggestionsDiv.style.display = 'none';
            
            showNotification(`Wybrano: ${city.name}${city.admin_name ? ', woj. ' + city.admin_name : ''}`, 'success');
        }
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!cityInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
                suggestionsDiv.style.display = 'none';
            }
        });
    }
    
    // Home location form handler
    const homeLocationForm = document.getElementById('homeLocationForm');
    if (homeLocationForm) {
        homeLocationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                city: formData.get('city') || null,
                address: formData.get('address') || null,
                latitude: formData.get('latitude') || null,
                longitude: formData.get('longitude') || null,
                country: formData.get('country') || null
            };
            
            // Validate that city is selected
            if (!data.latitude || !data.longitude) {
                showNotification('Proszę wybrać miasto z listy', 'warning');
                return;
            }
            
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
                if (result.success) {
                    showNotification('Lokalizacja domu została zaktualizowana', 'success');
                } else {
                    showNotification(result.error || 'Wystąpił błąd podczas aktualizacji lokalizacji', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
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

                    // Update form fields
                    document.getElementById('homeLatitude').value = lat.toFixed(6);
                    document.getElementById('homeLongitude').value = lon.toFixed(6);
                    document.getElementById('homeCountry').value = 'Poland';

                    // Find nearest city from our database
                    try {
                        const response = await fetch('/api/cities/search?limit=184');
                        const result = await response.json();
                        
                        if (result.success && result.cities.length > 0) {
                            // Calculate distance to each city and find nearest
                            const nearestCity = result.cities.reduce((nearest, city) => {
                                const distance = calculateDistance(lat, lon, city.latitude, city.longitude);
                                if (!nearest || distance < nearest.distance) {
                                    return { ...city, distance };
                                }
                                return nearest;
                            }, null);
                            
                            if (nearestCity) {
                                document.getElementById('homeCity').value = nearestCity.name;
                                showNotification(`Najbliższe miasto: ${nearestCity.name}${nearestCity.admin_name ? ', woj. ' + nearestCity.admin_name : ''} (${nearestCity.distance.toFixed(1)} km)`, 'success');
                            }
                        } else {
                            showNotification('Współrzędne pobrane pomyślnie', 'success');
                        }
                    } catch (error) {
                        console.error('Error finding nearest city:', error);
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
    
    // City autocomplete handler
    initCityAutocomplete();
}

// Initialize city autocomplete with dropdown
function initCityAutocomplete() {
    const cityInput = document.getElementById('homeCity');
    if (!cityInput) return;
    
    let debounceTimer;
    let autocompleteList = null;
    
    // Create autocomplete dropdown container
    const wrapper = document.createElement('div');
    wrapper.className = 'autocomplete-wrapper';
    wrapper.style.position = 'relative';
    cityInput.parentNode.insertBefore(wrapper, cityInput);
    wrapper.appendChild(cityInput);
    
    cityInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.trim();
        
        // Clear existing timer
        clearTimeout(debounceTimer);
        
        // Remove old autocomplete list
        if (autocompleteList) {
            autocompleteList.remove();
            autocompleteList = null;
        }
        
        if (searchTerm.length < 2) return;
        
        // Debounce API calls
        debounceTimer = setTimeout(() => {
            fetch(`/api/cities/search?q=${encodeURIComponent(searchTerm)}&limit=10`)
                .then(response => response.json())
                .then(result => {
                    if (result.success && result.cities.length > 0) {
                        showCityAutocomplete(result.cities);
                    }
                })
                .catch(error => {
                    console.error('Error fetching cities:', error);
                });
        }, 300);
    });
    
    function showCityAutocomplete(cities) {
        // Remove old list
        if (autocompleteList) {
            autocompleteList.remove();
        }
        
        // Create new list
        autocompleteList = document.createElement('div');
        autocompleteList.className = 'autocomplete-list';
        autocompleteList.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--secondary);
            border: 1px solid var(--border);
            border-radius: 5px;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        `;
        
        cities.forEach(city => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.style.cssText = `
                padding: 10px 15px;
                cursor: pointer;
                border-bottom: 1px solid var(--border);
                transition: background 0.2s;
            `;
            
            // Display city name with country
            const displayName = city.country ? `${city.name}, ${city.country}` : city.name;
            item.innerHTML = `
                <div style="font-weight: 500;">${displayName}</div>
                ${city.population ? `<div style="font-size: 0.85em; opacity: 0.7;">Pop: ${city.population.toLocaleString()}</div>` : ''}
            `;
            
            item.addEventListener('mouseenter', function() {
                this.style.background = 'var(--accent)';
            });
            
            item.addEventListener('mouseleave', function() {
                this.style.background = '';
            });
            
            item.addEventListener('click', function() {
                // Fill in the form fields
                document.getElementById('homeCity').value = city.name;
                if (city.latitude && city.longitude) {
                    document.getElementById('homeLatitude').value = city.latitude.toFixed(6);
                    document.getElementById('homeLongitude').value = city.longitude.toFixed(6);
                }
                
                // Try to build address from city and country
                const address = city.country ? `${city.name}, ${city.country}` : city.name;
                document.getElementById('homeAddress').value = address;
                
                // Remove autocomplete list
                autocompleteList.remove();
                autocompleteList = null;
                
                showNotification(`Wybrano: ${displayName}`, 'success');
            });
            
            autocompleteList.appendChild(item);
        });
        
        wrapper.appendChild(autocompleteList);
    }
    
    // Close autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (autocompleteList && !wrapper.contains(e.target)) {
            autocompleteList.remove();
            autocompleteList = null;
        }
    });
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
