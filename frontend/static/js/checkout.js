/**
 * Sets up BOLA vulnerability demonstration for checkout page
 */
function setupCheckoutBOLADemo() {
    const targetUserCheckbox = document.getElementById('order-for-other-user');
    if (targetUserCheckbox) {
        targetUserCheckbox.addEventListener('change', function() {
            const targetFields = document.getElementById('target-user-fields');
            if (targetFields) {
                targetFields.style.display = this.checked ? 'block' : 'none';
                
                if (this.checked) {
                    showVulnerabilityWarning(
                        'BOLA',
                        'You are attempting to place an order as another user. This demonstrates Broken Object Level Authorization.',
                        'bola-warning-container'
                    );
                } else {
                    const warningContainer = document.getElementById('bola-warning-container');
                    if (warningContainer) {
                        warningContainer.style.display = 'none';
                    }
                }
            }
        });
    }
}

/**
 * Handles the checkout form submission
 * Includes special handling for BOLA demonstration when ordering for another user
 */
async function handleCheckoutSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const orderForOtherUser = document.getElementById('order-for-other-user').checked;
    
    let userId, addressId, creditCardId;
    
    if (orderForOtherUser) {
        // Using BOLA exploit to order for another user
        userId = document.getElementById('target-user-id').value;
        addressId = document.getElementById('target-address-id').value;
        creditCardId = document.getElementById('target-credit-card-id').value;
        
        if (!userId || !addressId || !creditCardId) {
            displayError('Please enter all required target user information for the BOLA demo.');
            return;
        }
    } else {
        // Normal checkout flow
        userId = currentUser.user_id;
        addressId = document.getElementById('address-id').value;
        creditCardId = document.getElementById('credit-card-id').value;
        
        if (!addressId || !creditCardId) {
            displayError('Please select both a shipping address and payment method.');
            return;
        }
    }
    
    try {
        showLoading('checkout-loading', 'Processing order...');
        
        // Create order items from cart
        const orderItems = cart.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            price: item.price
        }));
        
        // Create the query parameters for the API call
        const queryParams = new URLSearchParams();
        queryParams.append('address_id', addressId);
        queryParams.append('credit_card_id', creditCardId);
        
        // Add product items as query parameters
        let index = 1;
        for (const item of orderItems) {
            queryParams.append(`product_id_${index}`, item.product_id);
            queryParams.append(`quantity_${index}`, item.quantity);
            index++;
        }
        
        // Debug info - log the query parameters
        console.log(`Creating order with query params: ${queryParams.toString()}`);
        
        // Submit order to API with appropriate user ID and query parameters
        await apiCall(`/api/users/${userId}/orders?${queryParams.toString()}`, 'POST', {});
        
        if (orderForOtherUser) {
            // Show BOLA exploit success message
            displayGlobalMessage(
                `<strong>BOLA Vulnerability Exploited!</strong> Order successfully placed on behalf of User ID: ${userId}`, 
                'warning'
            );
            displaySuccess(`Order successfully placed using another user's information. This demonstrates a Broken Object Level Authorization (BOLA) vulnerability.`);
        } else {
            // Show normal success message
            displaySuccess('Order placed successfully!');
        }
        
        // Clear cart and redirect
        localStorage.setItem('cart', '[]');
        cart = [];
        
        // Redirect to orders page after 2 seconds
        setTimeout(() => {
            window.location.href = '/orders';
        }, 2000);
    } catch (error) {
        displayError(`Failed to place order: ${error.message}`);
    } finally {
        hideLoading('checkout-loading');
    }
}

/**
 * Shows a loading indicator while processing
 * @param {string} id - The container ID for the loader
 * @param {string} message - The message to display
 */
function showLoading(id, message) {
    let loadingContainer = document.getElementById(id);
    if (!loadingContainer) {
        loadingContainer = document.createElement('div');
        loadingContainer.id = id;
        loadingContainer.className = 'loading-indicator-overlay';
        document.body.appendChild(loadingContainer);
    }
    loadingContainer.innerHTML = `
        <div class="loading-spinner"></div>
        <p>${message || 'Loading...'}</p>
    `;
    loadingContainer.style.display = 'flex';
}

/**
 * Hides the loading indicator
 * @param {string} id - The container ID
 */
function hideLoading(id) {
    const loadingContainer = document.getElementById(id);
    if (loadingContainer) {
        loadingContainer.style.display = 'none';
    }
}

/**
 * Shows a warning banner for vulnerability demonstrations
 * @param {string} type - Type of vulnerability (e.g., 'BOLA')
 * @param {string} message - The warning message to display
 * @param {string} containerId - Optional container ID for the warning
 */
function showVulnerabilityWarning(type, message, containerId = null) {
    // If container ID provided, try to use that specific container
    if (containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <h3>⚠️ ${type} Vulnerability Demo</h3>
                <p>${message}</p>
            `;
            container.style.display = 'block';
            return;
        }
    }
    
    // Fallback to global message
    displayGlobalMessage(`<strong>⚠️ ${type} Vulnerability Demo:</strong> ${message}`, 'warning');
}
