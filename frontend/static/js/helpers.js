// Helper functions for UI enhancements

/**
 * Displays a toast-style global message notification
 * @param {string} message - The message to display
 * @param {string} type - The type of message: 'info', 'success', 'error', or 'warning'
 * @param {number} duration - Time in milliseconds before auto-removing the message (0 = don't auto-remove)
 */
function displayGlobalMessage(message, type = 'info', duration = 5000) {
    const container = document.querySelector('body');
    if (!container) return;
    
    // Check if we already have a messages container
    let messagesContainer = document.getElementById('global-message-container');
    
    if (!messagesContainer) {
        messagesContainer = document.createElement('div');
        messagesContainer.id = 'global-message-container';
        container.appendChild(messagesContainer);
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = `global-message ${type}-message`;
    messageElement.innerHTML = `
        ${message}
        <button class="close-btn">&times;</button>
    `;
    
    // Add close button functionality
    const closeBtn = messageElement.querySelector('.close-btn');
    closeBtn.addEventListener('click', function() {
        messagesContainer.removeChild(messageElement);
        if (messagesContainer.children.length === 0) {
            container.removeChild(messagesContainer);
        }
    });
    
    messagesContainer.appendChild(messageElement);
    
    // Auto remove after specified duration (if not 0)
    if (duration > 0) {
        setTimeout(() => {
            if (messageElement.parentNode === messagesContainer) {
                messagesContainer.removeChild(messageElement);
                if (messagesContainer.children.length === 0 && messagesContainer.parentNode === container) {
                    container.removeChild(messagesContainer);
                }
            }
        }, duration);
    }
}

/**
 * Displays a success message in a dedicated container
 * @param {string} message - The success message to display
 * @param {string} containerId - The ID of the container to place the message in
 */
function displaySuccess(message, containerId = 'success-message-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="success-message"><strong>Success:</strong> ${message}</div>`;
        container.style.display = 'block';
        
        // Auto-clear after 5 seconds
        setTimeout(() => {
            clearSuccess(containerId);
        }, 5000);
    } else {
        // Fallback: use global message system
        displayGlobalMessage(message, 'success');
    }
}

/**
 * Clears a success message container
 * @param {string} containerId - The ID of the container to clear
 */
function clearSuccess(containerId = 'success-message-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }
}

/**
 * Shows a banner warning specifically for vulnerability demonstrations
 * @param {string} vulnerability - The type of vulnerability being demonstrated (BOLA, BFLA, etc.)
 * @param {string} message - Specific details about the exploitation
 * @param {string} containerId - Where to place the warning (defaults to global message)
 */
function showVulnerabilityWarning(vulnerability, message, containerId = null) {
    const warningMessage = `
        <strong>⚠️ ${vulnerability} Vulnerability Demonstration Active</strong><br>
        ${message}
    `;
    
    if (containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `<div class="vulnerability-warning">${warningMessage}</div>`;
            container.style.display = 'block';
            return;
        }
    }
    
    // Fallback to global message with no auto-removal (duration = 0)
    displayGlobalMessage(warningMessage, 'warning', 0);
}

/**
 * Shows a loading indicator in the specified container
 * @param {string} containerId - The ID of the container to show loading in
 * @param {string} message - Optional message to display with the spinner
 */
function showLoading(containerId, message = 'Loading...') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="loading-indicator">${message}</div>`;
        container.style.display = 'block';
    }
}

/**
 * Hides a loading indicator in the specified container
 * @param {string} containerId - The ID of the container with the loading indicator
 */
function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        const loadingEl = container.querySelector('.loading-indicator');
        if (loadingEl) {
            loadingEl.remove();
        }
    }
}
