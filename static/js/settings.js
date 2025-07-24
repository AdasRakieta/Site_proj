// Helper function to show messages
function showMessage(elementId, message, isError = false) {
    // Show notification in corner
    showNotification(message, isError ? 'error' : 'success');
    // Hide container for message under form, if it exists
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = '';
        element.style.display = 'none';
    }
}

// Page initialization
function initSettingsPage() {
    // Set current theme in selector
    const themeSelect = document.querySelector('.theme-selector select');
    if (themeSelect) {
        themeSelect.value = localStorage.getItem('theme') || 'light';
    }
}

// DOM Content Loaded Event
document.addEventListener('DOMContentLoaded', () => {
    initSettingsPage();
});