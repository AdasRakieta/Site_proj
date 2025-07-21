// static/automations.js

class AutomationsManager {
    constructor(app) {
        this.app = app;
        this.buttons = [];
        this.automations = [];
        this.globalClickListener = null;
        this.bindMethods();
    }

    bindMethods() {
        this.createAutomation = this.createAutomation.bind(this);
        this.updateAutomation = this.updateAutomation.bind(this);
        this.deleteAutomation = this.deleteAutomation.bind(this);
        this.showAutomationForm = this.showAutomationForm.bind(this);
        this.initPage = this.initPage.bind(this);
        this.renderAutomations = this.renderAutomations.bind(this);
        this.onAutomationsUpdate = this.onAutomationsUpdate.bind(this);
        this.showLoading = this.showLoading.bind(this);
        this.hideLoading = this.hideLoading.bind(this);
    }

    async initPage() {
        console.log('Inicjalizacja strony automatyzacji');
        try {
            // Najpierw ładujemy przyciski potrzebne do formularza
            await this.fetchInitialData();
            
            // Następnie ładujemy automatyzacje
            await this.loadAutomations();
            
            // Inicjalizujemy przycisk dodawania nowej automatyzacji
            const addBtn = document.getElementById('new-automation');
            if (addBtn) {
                addBtn.addEventListener('click', () => this.showAutomationForm());
            }
        } catch (error) {
            console.error('Błąd inicjalizacji strony automatyzacji:', error);
            this.app.showNotification('Błąd ładowania automatyzacji', 'error');
        }
    }

    async fetchInitialData() {
        try {
            const buttonsData = await this.app.fetchData('/api/buttons');
            if (buttonsData && Array.isArray(buttonsData)) {
                this.buttons = buttonsData;
                return true;
            }
            return false;
        } catch (error) {
            console.error('Błąd ładowania przycisków:', error);
            return false;
        }
    }

    async loadAutomations() {
        try {
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Timeout ładowania automatyzacji')), 5000);
            });
            
            const response = await Promise.race([
                this.app.fetchData('/api/automations'),
                timeoutPromise
            ]);
            // ... reszta kodu
        } catch (error) {
            console.error('Błąd ładowania automatyzacji:', error);
            this.renderAutomations([]);
            return false;
        }
    }

    onAutomationsUpdate(data) {
        console.log('Aktualizacja automatyzacji:', data);
        if (Array.isArray(data)) {
            this.automations = data;
            this.renderAutomations(data);
        }
    }

    renderAutomations(automations) {
        const container = document.querySelector('.automations-container');
        if (!container) return;

        // Usuń stary listener jeśli istnieje
        if (this.globalClickListener) {
            document.removeEventListener('click', this.globalClickListener);
        }

        let list = document.getElementById('automations-list');
        if (!list) {
            list = this.app.createElement('div', { id: 'automations-list' });
            container.appendChild(list);
        }

        // Wyczyść listę i ukryj loader
        list.innerHTML = '';
        const loader = document.getElementById('loading-indicator');
        if (loader) loader.style.display = 'none';

        if (!automations || automations.length === 0) {
            list.appendChild(this.app.createElement('p', {
                class: 'no-automations',
                textContent: 'Brak zdefiniowanych automatyzacji'
            }));
            return;
        }

        automations.forEach((automation, index) => {
            const automationElement = this.createAutomationCard(automation, index);
            list.appendChild(automationElement);
        });

        this.setupGlobalClickListener();
    }

    createAutomationCard(automation, index) {
        // Kontener na przyciski akcji
        const actionsContainer = this.app.createElement('div', {
            class: 'automation-actions'
        });

        // Przycisk Edytuj
        const editBtn = this.app.createElement('button', {
            class: 'edit-automation btn-secondary',
            textContent: 'Edytuj'
        });

        // Przycisk Usuń
        const deleteBtn = this.app.createElement('button', {
            class: 'delete-automation btn-secondary',
            textContent: 'Usuń'
        });

        // Przycisk Potwierdź (początkowo ukryty)
        const confirmBtn = this.app.createElement('button', {
            class: 'confirm-delete-btn btn-danger hidden',
            textContent: 'Potwierdź'
        });

        // Dodaj przyciski do kontenera
        actionsContainer.appendChild(editBtn);
        actionsContainer.appendChild(deleteBtn);
        actionsContainer.appendChild(confirmBtn);

        // Karta automatyzacji
        const automationElement = this.app.createElement('div', {
            class: 'automation-card',
            'data-index': index
        }, [
            this.app.createElement('h3', { textContent: automation.name }),
            this.app.createElement('p', { textContent: `Wyzwalacz: ${this.formatTrigger(automation.trigger)}` }),
            this.app.createElement('p', { textContent: `Akcje: ${automation.actions.length}` }),
            this.app.createElement('div', {
                class: `status-badge ${automation.enabled ? 'enabled' : 'disabled'}`,
                textContent: automation.enabled ? 'Aktywna' : 'Nieaktywna'
            }),
            actionsContainer
        ]);

        // Obsługa przycisku Edytuj
        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showAutomationForm(automation, index);
        });

        // Obsługa przycisku Usuń
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteBtn.classList.add('hidden');
            confirmBtn.classList.remove('hidden');
            
            setTimeout(() => {
                if (!confirmBtn.classList.contains('hidden')) {
                    confirmBtn.classList.add('hidden');
                    deleteBtn.classList.remove('hidden');
                }
            }, 5000);
        });

        // Obsługa przycisku Potwierdź
        confirmBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            await this.deleteAutomation(index);
        });

        return automationElement;
    }

    setupGlobalClickListener() {
        this.globalClickListener = (e) => {
            if (!e.target.closest('.delete-btn-container')) {
                document.querySelectorAll('.delete-btn-container').forEach(container => {
                    container.querySelector('.delete-automation').classList.remove('hidden');
                    container.querySelector('.confirm-delete-btn').classList.add('hidden');
                });
            }
        };
        document.addEventListener('click', this.globalClickListener);
    }

    formatTrigger(trigger) {
        if (!trigger) return 'Nieznany wyzwalacz';
        switch (trigger.type) {
            case 'time':
                if (Array.isArray(trigger.days) && trigger.days.length > 0) {
                    const dayLabels = {
                        mon: 'Pn', tue: 'Wt', wed: 'Śr', thu: 'Cz', fri: 'Pt', sat: 'Sb', sun: 'Nd'
                    };
                    const daysStr = trigger.days.map(d => dayLabels[d] || d).join(', ');
                    return `W ${daysStr} o ${trigger.time}`;
                } else {
                    return `Codziennie o ${trigger.time}`;
                }
            case 'device':
                const [room, device] = trigger.device.split('_');
                return `Gdy ${device} w ${room} jest ${trigger.state === 'on' ? 'włączony' : trigger.state === 'off' ? 'wyłączony' : 'przełączony'}`;
            case 'sensor':
                return `Gdy ${trigger.sensor} jest ${trigger.condition === 'above' ? 'powyżej' : 'poniżej'} ${trigger.value}°C`;
            default:
                return trigger.type;
        }
    }

    showAutomationForm(automation = null, index = null) {
        const formContainer = document.getElementById('automation-form-container') || 
            this.app.createElement('div', { id: 'automation-form-container' });
        
        formContainer.innerHTML = `
            <h3>${automation ? 'Edytuj automatyzację' : 'Nowa automatyzacja'}</h3>
            <form id="automation-form">
                <div class="form-group">
                    <label for="automation-name">Nazwa:</label>
                    <input type="text" id="automation-name" required 
                           value="${automation?.name || ''}">
                </div>
                <div class="form-group">
                    <label>Wyzwalacz:</label>
                    <select id="trigger-type">
                        <option value="time" ${automation?.trigger?.type === 'time' ? 'selected' : ''}>Czas</option>
                        <option value="device" ${automation?.trigger?.type === 'device' ? 'selected' : ''}>Urządzenie</option>
                        <option value="sensor" ${automation?.trigger?.type === 'sensor' ? 'selected' : ''}>Czujnik</option>
                    </select>
                    <div id="trigger-params"></div>
                </div>
                <div class="form-group">
                    <label>Akcje:</label>
                    <div id="actions-container"></div>
                    <button type="button" id="add-action" class="btn-secondary">Dodaj akcję</button>
                </div>
                <div class="form-group">
                    <label>Włącz automatyzację:</label>
                    <div class="center-container">
                        <label class="switch">
                            <input type="checkbox" id="automation-enabled" 
                                   ${automation?.enabled ? 'checked' : ''}>
                            <span class="slider round"></span>
                        </label>
                    </div>
                </div>
                <div class="center-container"> 
                    <div class="form-buttons">
                        <button type="submit" class="btn-primary">Zapisz</button>
                        <button type="button" id="cancel-form" class="btn-secondary">Anuluj</button>
                    </div>
                </div>
            </form>
        `;

        document.querySelector('.automations-container').appendChild(formContainer);

        // Inicjalizacja formularza
        this.initFormEvents(formContainer, automation, index);
        
        // Wypełnij początkowe wartości
        if (automation) {
            this.updateTriggerParams(automation.trigger.type, automation.trigger);
            this.populateActions(automation.actions);
        } else {
            this.updateTriggerParams('time');
        }
    }

    initFormEvents(formContainer, automation, index) {
        document.getElementById('trigger-type').addEventListener('change', (e) => {
            this.updateTriggerParams(e.target.value, automation?.trigger);
        });

        document.getElementById('add-action').addEventListener('click', () => {
            this.addActionToForm(null);
        });

        document.getElementById('cancel-form').addEventListener('click', () => {
            formContainer.remove();
        });

        document.getElementById('automation-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const automationData = this.getFormData();
            
            // Client-side validation
            const validationErrors = this.validateFormData(automationData);
            if (validationErrors.length > 0) {
                const errorMessage = 'Błędy walidacji:\n• ' + validationErrors.join('\n• ');
                this.app.showNotification(errorMessage, 'error');
                return;
            }
            
            try {
                if (index !== null) {
                    await this.updateAutomation(index, automationData);
                } else {
                    await this.createAutomation(automationData);
                }
                formContainer.remove();
            } catch (error) {
                console.error('Błąd zapisywania automatyzacji:', error);
                // Error is already handled in the create/update methods
            }
        });
    }

    updateTriggerParams(triggerType, existingTrigger = null) {
        const container = document.getElementById('trigger-params');
        if (!container) return;
        
        container.innerHTML = '';
        let html = '';

        switch (triggerType) {
            case 'time':
                // Stylowane checkboxy dni tygodnia
                const days = [
                    { key: 'mon', label: 'Poniedziałek' },
                    { key: 'tue', label: 'Wtorek' },
                    { key: 'wed', label: 'Środa' },
                    { key: 'thu', label: 'Czwartek' },
                    { key: 'fri', label: 'Piątek' },
                    { key: 'sat', label: 'Sobota' },
                    { key: 'sun', label: 'Niedziela' }
                ];
                let daysHtml = '<div style="margin-top:20px;margin-bottom:10px;font-weight:bold;">Dni tygodnia:</div>';
                daysHtml += '<div class="weekdays-checkbox-group">';
                daysHtml += `<svg class='inline-svg'><symbol id='check-4' viewBox='0 0 12 10'><polyline points='1.5 6 4.5 9 10.5 1'></polyline></symbol></svg>`;
                days.forEach((d, i) => {
                    const checked = existingTrigger?.days?.includes(d.key) ? 'checked' : '';
                    const id = `trigger-day-${d.key}`;
                    daysHtml += `
                    <input class="weekday-checkbox-input trigger-day" id="${id}" type="checkbox" value="${d.key}" ${checked}/>
                    <label class="weekday-checkbox-label" for="${id}"><span>
                    <svg width="12px" height="10px"><use xlink:href="#check-4"></use></svg></span><span>${d.label}</span></label>
                    `;
                });
                daysHtml += '</div>';
                html = `
                    <label for="trigger-time">Godzina:</label>
                    <input type="time" id="trigger-time" required value="${existingTrigger?.time || ''}">
                    ${daysHtml}
                `;
                break;
            case 'device':
                html = `
                    <label for="trigger-device">Urządzenie:</label>
                    <select id="trigger-device" required>
                        ${this.buttons.map(btn => 
                            `<option value="${btn.room}_${btn.name}" 
                                    ${existingTrigger?.device === `${btn.room}_${btn.name}` ? 'selected' : ''}>
                                ${btn.room} - ${btn.name}
                            </option>`
                        ).join('')}
                    </select>
                    <label for="trigger-device-state">Stan:</label>
                    <select id="trigger-device-state" required>
                        <option value="on" ${existingTrigger?.state === 'on' ? 'selected' : ''}>Włączony</option>
                        <option value="off" ${existingTrigger?.state === 'off' ? 'selected' : ''}>Wyłączony</option>
                        <option value="toggle" ${existingTrigger?.state === 'toggle' ? 'selected' : ''}>Przełączenie</option>
                    </select>
                `;
                break;
            case 'sensor':
                html = `
                    <label for="trigger-sensor">Czujnik:</label>
                    <select id="trigger-sensor" required>
                        <option value="temperature" ${existingTrigger?.sensor === 'temperature' ? 'selected' : ''}>Temperatura</option>
                        <option value="humidity" ${existingTrigger?.sensor === 'humidity' ? 'selected' : ''}>Wilgotność</option>
                    </select>
                    <label for="trigger-sensor-value">Wartość:</label>
                    <input type="number" id="trigger-sensor-value" required value="${existingTrigger?.value || ''}">
                    <select id="trigger-sensor-condition">
                        <option value="above" ${existingTrigger?.condition === 'above' ? 'selected' : ''}>Powyżej</option>
                        <option value="below" ${existingTrigger?.condition === 'below' ? 'selected' : ''}>Poniżej</option>
                    </select>
                `;
                break;
        }

        container.innerHTML = html;
    }

    populateActions(actions = []) {
        const container = document.getElementById('actions-container');
        if (!container) return;
        
        container.innerHTML = '';
        actions.forEach(action => {
            this.addActionToForm(action);
        });
    }

    addActionToForm(existingAction = null) {
        const container = document.getElementById('actions-container');
        if (!container) return;

        const actionIndex = container.children.length;
        const actionElement = this.app.createElement('div', {
            class: 'action',
            'data-index': actionIndex
        });

        const typeSelect = this.app.createElement('select', {
            class: 'action-type',
            name: `actions[${actionIndex}][type]`
        }, [
            this.app.createElement('option', { value: 'device', textContent: 'Urządzenie' }),
            this.app.createElement('option', { value: 'notification', textContent: 'Powiadomienie' })
        ]);

        const paramsContainer = this.app.createElement('div', { class: 'action-params' });
        const removeButton = this.app.createElement('button', {
            class: 'remove-action',
            type: 'button',
            textContent: 'Usuń'
        });

        actionElement.appendChild(typeSelect);
        actionElement.appendChild(paramsContainer);
        actionElement.appendChild(removeButton);
        container.appendChild(actionElement);

        if (existingAction) {
            typeSelect.value = existingAction.type;
        }

        this.updateActionParams(actionElement, existingAction);

        typeSelect.addEventListener('change', () => {
            this.updateActionParams(actionElement);
        });

        removeButton.addEventListener('click', () => {
            actionElement.remove();
            this.renumberActions();
        });
    }

    renumberActions() {
        const container = document.getElementById('actions-container');
        if (!container) return;

        Array.from(container.children).forEach((actionElement, index) => {
            actionElement.dataset.index = index;
            const typeSelect = actionElement.querySelector('.action-type');
            if (typeSelect) {
                typeSelect.name = `actions[${index}][type]`;
            }
            this.updateActionParams(actionElement);
        });
    }

    updateActionParams(actionElement, existingAction = null) {
        const paramsContainer = actionElement.querySelector('.action-params');
        if (!paramsContainer) return;

        const actionType = actionElement.querySelector('.action-type').value;
        const actionIndex = actionElement.dataset.index || 0;
        paramsContainer.innerHTML = '';

        switch (actionType) {
            case 'device':
                if (!this.buttons || this.buttons.length === 0) {
                    paramsContainer.textContent = 'Brak dostępnych urządzeń';
                    return;
                }

                const deviceSelect = this.app.createElement('select', {
                    class: 'action-device',
                    name: `actions[${actionIndex}][device]`,
                    required: true
                });

                this.buttons.forEach(button => {
                    deviceSelect.appendChild(this.app.createElement('option', {
                        value: `${button.room}_${button.name}`,
                        textContent: `${button.room} - ${button.name}`,
                        selected: existingAction?.device === `${button.room}_${button.name}`
                    }));
                });

                const stateSelect = this.app.createElement('select', {
                    class: 'action-device-state',
                    name: `actions[${actionIndex}][state]`,
                    required: true
                }, [
                    this.app.createElement('option', {
                        value: 'on',
                        textContent: 'Włącz',
                        selected: existingAction?.state === 'on'
                    }),
                    this.app.createElement('option', {
                        value: 'off',
                        textContent: 'Wyłącz',
                        selected: existingAction?.state === 'off'
                    }),
                    this.app.createElement('option', {
                        value: 'toggle',
                        textContent: 'Przełącz',
                        selected: existingAction?.state === 'toggle'
                    })
                ]);

                paramsContainer.appendChild(deviceSelect);
                paramsContainer.appendChild(stateSelect);
                break;

            case 'notification':
                const messageInput = this.app.createElement('input', {
                    type: 'text',
                    class: 'action-notification-message',
                    id: `action-notification-message-id`,
                    name: `actions[${actionIndex}][message]`,
                    placeholder: 'Treść powiadomienia',
                    value: existingAction?.message || '',
                    required: true
                });
                paramsContainer.appendChild(messageInput);
                break;
        }
    }

    getFormData() {
        const formData = {
            name: document.getElementById('automation-name').value,
            trigger: {
                type: document.getElementById('trigger-type').value
            },
            actions: [],
            enabled: document.getElementById('automation-enabled').checked
        };

        switch (formData.trigger.type) {
            case 'time':
                formData.trigger.time = document.getElementById('trigger-time').value;
                // Pobierz wybrane dni tygodnia
                formData.trigger.days = Array.from(document.querySelectorAll('.trigger-day:checked')).map(cb => cb.value);
                break;
            case 'device':
                formData.trigger.device = document.getElementById('trigger-device').value;
                formData.trigger.state = document.getElementById('trigger-device-state').value;
                break;
            case 'sensor':
                formData.trigger.sensor = document.getElementById('trigger-sensor').value;
                formData.trigger.value = parseFloat(document.getElementById('trigger-sensor-value').value);
                formData.trigger.condition = document.getElementById('trigger-sensor-condition').value;
                break;
        }

        document.querySelectorAll('#actions-container .action').forEach(actionElement => {
            const actionType = actionElement.querySelector('.action-type').value;
            const action = { type: actionType };

            switch (actionType) {
                case 'device':
                    action.device = actionElement.querySelector('.action-device').value;
                    action.state = actionElement.querySelector('.action-device-state').value;
                    break;
                case 'notification':
                    action.message = actionElement.querySelector('.action-notification-message').value;
                    break;
            }

            formData.actions.push(action);
        });

        return formData;
    }

    validateFormData(formData) {
        const errors = [];
        
        // Validate name
        if (!formData.name || formData.name.trim().length === 0) {
            errors.push('Nazwa automatyzacji jest wymagana.');
        } else if (formData.name.trim().length < 3) {
            errors.push('Nazwa automatyzacji musi mieć co najmniej 3 znaki.');
        } else if (formData.name.trim().length > 50) {
            errors.push('Nazwa automatyzacji nie może przekraczać 50 znaków.');
        }
        
        // Validate trigger
        if (!formData.trigger || !formData.trigger.type) {
            errors.push('Typ wyzwalacza jest wymagany.');
        } else {
            switch (formData.trigger.type) {
                case 'time':
                    if (!formData.trigger.time) {
                        errors.push('Godzina wyzwalacza jest wymagana.');
                    }
                    // Validate time format
                    if (formData.trigger.time && !/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/.test(formData.trigger.time)) {
                        errors.push('Nieprawidłowy format godziny (wymagany HH:MM).');
                    }
                    break;
                case 'device':
                    if (!formData.trigger.device) {
                        errors.push('Urządzenie wyzwalacza jest wymagane.');
                    }
                    if (!formData.trigger.state || !['on', 'off', 'toggle'].includes(formData.trigger.state)) {
                        errors.push('Stan urządzenia wyzwalacza jest wymagany.');
                    }
                    break;
                case 'sensor':
                    if (!formData.trigger.sensor) {
                        errors.push('Czujnik wyzwalacza jest wymagany.');
                    }
                    if (formData.trigger.value === undefined || formData.trigger.value === null || isNaN(formData.trigger.value)) {
                        errors.push('Wartość czujnika jest wymagana i musi być liczbą.');
                    }
                    if (!formData.trigger.condition || !['above', 'below'].includes(formData.trigger.condition)) {
                        errors.push('Warunek czujnika jest wymagany.');
                    }
                    break;
            }
        }
        
        // Validate actions
        if (!formData.actions || formData.actions.length === 0) {
            errors.push('Co najmniej jedna akcja jest wymagana.');
        } else {
            formData.actions.forEach((action, index) => {
                if (!action.type) {
                    errors.push(`Typ akcji #${index + 1} jest wymagany.`);
                } else {
                    switch (action.type) {
                        case 'device':
                            if (!action.device) {
                                errors.push(`Urządzenie dla akcji #${index + 1} jest wymagane.`);
                            }
                            if (!action.state || !['on', 'off', 'toggle'].includes(action.state)) {
                                errors.push(`Stan urządzenia dla akcji #${index + 1} jest wymagany.`);
                            }
                            break;
                        case 'notification':
                            if (!action.message || action.message.trim().length === 0) {
                                errors.push(`Treść powiadomienia dla akcji #${index + 1} jest wymagana.`);
                            } else if (action.message.trim().length > 200) {
                                errors.push(`Treść powiadomienia dla akcji #${index + 1} nie może przekraczać 200 znaków.`);
                            }
                            break;
                    }
                }
            });
        }
        
        return errors;
    }

    async createAutomation(automationData) {
        try {
            this.showLoading('Tworzenie automatyzacji...');
            const response = await this.app.postData('/api/automations', automationData);
            if (response.status === 'success') {
                this.app.showNotification('Automatyzacja została utworzona', 'success');
                return response;
            } else {
                let errorMessage = response.message || 'Błąd podczas tworzenia automatyzacji';
                this.app.showNotification(errorMessage, 'error');
                throw new Error(response.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Błąd tworzenia automatyzacji:', error);
            let errorMessage = 'Błąd podczas tworzenia automatyzacji';
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage = 'Błąd połączenia z serwerem. Sprawdź połączenie internetowe.';
            } else if (error.message.includes('403')) {
                errorMessage = 'Brak uprawnień do tworzenia automatyzacji.';
            } else if (error.message.includes('400')) {
                errorMessage = 'Nieprawidłowe dane automatyzacji. Sprawdź wszystkie pola.';
            } else if (error.message) {
                errorMessage += ': ' + error.message;
            }
            
            this.app.showNotification(errorMessage, 'error');
            throw error;
        } finally {
            this.hideLoading();
        }
    }

    async updateAutomation(index, automationData) {
        try {
            this.showLoading('Aktualizowanie automatyzacji...');
            const response = await this.app.putData(`/api/automations/${index}`, automationData);
            if (response.status === 'success') {
                this.app.showNotification('Automatyzacja została zaktualizowana', 'success');
                return response;
            } else {
                let errorMessage = response.message || 'Błąd podczas aktualizacji automatyzacji';
                this.app.showNotification(errorMessage, 'error');
                throw new Error(response.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Błąd aktualizacji automatyzacji:', error);
            let errorMessage = 'Błąd podczas aktualizacji automatyzacji';
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage = 'Błąd połączenia z serwerem. Sprawdź połączenie internetowe.';
            } else if (error.message.includes('403')) {
                errorMessage = 'Brak uprawnień do edycji automatyzacji.';
            } else if (error.message.includes('404')) {
                errorMessage = 'Automatyzacja nie została znaleziona.';
            } else if (error.message.includes('400')) {
                errorMessage = 'Nieprawidłowe dane automatyzacji. Sprawdź wszystkie pola.';
            } else if (error.message) {
                errorMessage += ': ' + error.message;
            }
            
            this.app.showNotification(errorMessage, 'error');
            throw error;
        } finally {
            this.hideLoading();
        }
    }

    async deleteAutomation(index) {
        try {
            this.showLoading('Usuwanie automatyzacji...');
            const response = await this.app.deleteData(`/api/automations/${index}`);
            
            if (response.status === 'success') {
                this.app.showNotification('Automatyzacja została usunięta', 'success');
            } else {
                this.app.showNotification(response.message || 'Błąd podczas usuwania automatyzacji', 'error');
                const card = document.querySelector(`.automation-card[data-index="${index}"]`);
                if (card) {
                    const container = card.querySelector('.delete-btn-container');
                    if (container) {
                        const deleteBtn = container.querySelector('.delete-automation');
                        const confirmBtn = container.querySelector('.confirm-delete-btn');
                        if (deleteBtn) deleteBtn.classList.remove('hidden');
                        if (confirmBtn) confirmBtn.classList.add('hidden');
                    }
                }
            }
        } catch (error) {
            console.error('Błąd usuwania automatyzacji:', error);
            let errorMessage = 'Błąd podczas usuwania automatyzacji';
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage = 'Błąd połączenia z serwerem. Sprawdź połączenie internetowe.';
            } else if (error.message.includes('403')) {
                errorMessage = 'Brak uprawnień do usuwania automatyzacji.';
            } else if (error.message.includes('404')) {
                errorMessage = 'Automatyzacja nie została znaleziona.';
            } else if (error.message) {
                errorMessage += ': ' + error.message;
            }
            
            this.app.showNotification(errorMessage, 'error');
            
            // Reset delete button state on error
            const card = document.querySelector(`.automation-card[data-index="${index}"]`);
            if (card) {
                const container = card.querySelector('.delete-btn-container');
                if (container) {
                    const deleteBtn = container.querySelector('.delete-automation');
                    const confirmBtn = container.querySelector('.confirm-delete-btn');
                    if (deleteBtn) deleteBtn.classList.remove('hidden');
                    if (confirmBtn) confirmBtn.classList.add('hidden');
                }
            }
        } finally {
            this.hideLoading();
        }
    }

    showLoading(message = 'Ładowanie...') {
        let loader = document.getElementById('automation-loading-indicator');
        if (!loader) {
            loader = this.app.createElement('div', {
                id: 'automation-loading-indicator',
                class: 'loading-indicator'
            }, [
                this.app.createElement('div', { class: 'spinner' }),
                this.app.createElement('div', { textContent: message })
            ]);
            
            const container = document.querySelector('.automations-container');
            if (container) {
                container.appendChild(loader);
            }
        } else {
            loader.querySelector('div:last-child').textContent = message;
            loader.style.display = 'flex';
        }
    }

    hideLoading() {
        const loader = document.getElementById('automation-loading-indicator');
        if (loader) {
            loader.style.display = 'none';
        }
    }
}