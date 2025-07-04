// Constants and global variables
// Derive the API base URL
let API_BASE_URL;
const isLocal =
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1';

if (isLocal) {
  API_BASE_URL = 'http://localhost:8000';
} else {
  API_BASE_URL = window.location.origin;
}
console.log(`[main.js] API_BASE_URL set to: ${API_BASE_URL}`); // For debugging
let authToken = localStorage.getItem('token');
let isHandlingSessionExpiration = false; // Prevent multiple simultaneous logout triggers
let currentUser = JSON.parse(localStorage.getItem('user') || 'null');
let cart = JSON.parse(localStorage.getItem('cart') || '[]');
var appliedCouponCode = null; // Holds coupon code staged during checkout
let uiVulnerabilityFeaturesEnabled = localStorage.getItem('uiVulnerabilityFeaturesEnabled') === 'true';

// DOM content loaded event to setup initial UI
document.addEventListener('DOMContentLoaded', () => {
    initializeUIVulnerabilityFeaturesToggle();
    updateNavbar();
    updateCurrentYear();
    
    // Page-specific initializations based on body ID or similar
    const path = window.location.pathname;
    
    if (path === '/') {
        initHomePage();
    } else if (path.startsWith('/products/')) {
        initProductDetailPage();
    } else if (path === '/login') {
        initLoginPage();
    } else if (path === '/register') {
        initRegisterPage();
    } else if (path === '/cart') {
        initCartPage();
    } else if (path === '/profile') {
        initProfilePage();
    } else if (path === '/checkout') {
        initCheckoutPage();
    } else if (path === '/orders') {
        initOrdersPage();
    } else if (path === '/admin') {
        initAdminPage();
    }

    updateUIVulnerabilityFeaturesDisplay(true);
});

// Helper Functions
function updateCurrentYear() {
    const el = document.getElementById('current-year');
    if (el) el.textContent = new Date().getFullYear();
}

async function apiCall(endpoint, method = 'GET', body = null, requiresAuth = true) {
    const headers = { 'Content-Type': 'application/json' };
    
    if (requiresAuth && authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const config = { method, headers };
    
    if (body && (method === 'POST' || method === 'PUT')) {
        config.body = JSON.stringify(body);
    }
    
    const fullUrl = `${API_BASE_URL}${endpoint}`;
    try {
        const response = await fetch(fullUrl, config);

        if (!response.ok) {
            if (response.status === 401 && requiresAuth && !isHandlingSessionExpiration) {
                console.warn(`API Call to ${method} ${fullUrl} resulted in 401. Session expired or invalid.`);
                handleSessionExpired();
                throw new Error('SESSION_EXPIRED');
            }

            const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status} ${response.statusText} for ${method} ${fullUrl}` }));
            console.error('API Call Error Response:', errorData);
            const msg = errorData.detail || `HTTP error! status: ${response.status} for ${method} ${fullUrl}`;
            if (response.status === 403 && /protected/i.test(msg)) {
                displayGlobalMessage(`<strong>Action Blocked:</strong> ${msg}<br><em>This is part of the demo design. Try exploiting a non-protected item or one you created.</em>`, 'warning', 8000);
            }
            throw new Error(msg);
        }

        return response.status === 204 ? null : response.json();
    } catch (error) {
        console.error(`API Call Exception at ${method} ${fullUrl}:`, error);
        if (error.message !== 'SESSION_EXPIRED') {
            // Optionally display global message but avoid noise for handled expirations
        }
        throw error;
    }
}

function displayError(message, _containerId = 'error-message-container') {
    displayGlobalMessage(`<strong>Error:</strong> ${message}`, 'error');
}

function clearError(_containerId = 'error-message-container') {
    /* Deprecated container-based errors now use global pop-ups */
}

function displaySuccess(message, _containerId = 'success-message-container') {
    displayGlobalMessage(`<strong>Success:</strong> ${message}`, 'success');
}

function clearSuccess(_containerId = 'success-message-container') {
    /* Deprecated container-based success messages now use global pop-ups */
}

function initializeUIVulnerabilityFeaturesToggle() {
    const toggleSwitch = document.getElementById('ui-vulnerability-features-toggle-switch');
    const toggleStatusText = document.getElementById('ui-vulnerability-features-toggle-status');

    if (toggleSwitch && toggleStatusText) {
        toggleSwitch.checked = uiVulnerabilityFeaturesEnabled;
        updateUIToggleStatusText(uiVulnerabilityFeaturesEnabled, toggleStatusText);

        toggleSwitch.addEventListener('change', function() {
            uiVulnerabilityFeaturesEnabled = this.checked;
            localStorage.setItem('uiVulnerabilityFeaturesEnabled', uiVulnerabilityFeaturesEnabled);
            updateUIToggleStatusText(uiVulnerabilityFeaturesEnabled, toggleStatusText);
            displayGlobalMessage(`UI Vulnerability Demos ${uiVulnerabilityFeaturesEnabled ? 'ENABLED' : 'DISABLED'}. Some changes may require a page refresh or navigation.`, uiVulnerabilityFeaturesEnabled ? 'warning' : 'success', 7000);
            updateUIVulnerabilityFeaturesDisplay();
            updateNavbar();
        });
    }
}

function updateUIToggleStatusText(isEnabled, statusElement) {
    if (statusElement) {
        statusElement.textContent = isEnabled ? 'ON' : 'OFF';
        statusElement.className = `toggle-status-text ${isEnabled ? 'ui-features-enabled-text' : 'ui-features-disabled-text'}`;
    }
}

function updateNavbar() {
    const navLinksContainer = document.getElementById('dynamic-nav-links');  // New: targets the specific div for links
    if (!navLinksContainer) {
        console.error("Navbar error: Element with ID 'dynamic-nav-links' not found.");
        return;  // Exit if the new container isn't found
    }
    
    let navLinks = `
        <a href="/">Home</a>
        <a href="/cart">Cart (<span id="cart-item-count">${getCartItemCount()}</span>)</a>
    `;
    
    if (currentUser) {
        navLinks += `
            <a href="/profile">Profile (${currentUser.username})</a>
            <a href="/orders">Orders</a>
        `;
        if (currentUser.is_admin || uiVulnerabilityFeaturesEnabled) {
            navLinks += `<a href="/admin">Admin Page ${!currentUser.is_admin && uiVulnerabilityFeaturesEnabled ? '<span class="admin-badge-nav">(Demo)</span>' : ''}</a>`;
        }
        navLinks += `<a href="#" id="logout-link">Logout</a>`;
    } else {
        navLinks += `
            <a href="/login">Login</a>
            <a href="/register">Register</a>
        `;
    }
    
    navLinksContainer.innerHTML = navLinks; // Updates only the link container
    
    if (currentUser) {
        const logoutLink = document.getElementById('logout-link');
        if (logoutLink) {
            logoutLink.addEventListener('click', handleLogout);
        }
    }
}

function handleSessionExpired() {
    if (isHandlingSessionExpiration) {
        console.log("Session expiration handling already in progress.");
        return;
    }
    isHandlingSessionExpiration = true;

    console.log("Session expired. Logging out user.");

    localStorage.removeItem('token');
    localStorage.removeItem('user');
    authToken = null;
    currentUser = null;
    cart = [];
    saveCart();

    updateNavbar();

    displayGlobalMessage('Your session has expired or is invalid. Please log in again.', 'warning', 7000);

    const currentPath = window.location.pathname;
    if (currentPath !== '/login' && currentPath !== '/register') {
        setTimeout(() => {
            window.location.href = '/login';
            isHandlingSessionExpiration = false;
        }, 2000);
    } else {
        isHandlingSessionExpiration = false;
    }
}

function handleLogout(e) {
    e.preventDefault();
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    authToken = null;
    currentUser = null;
    cart = []; // Clear cart on logout
    saveCart();
    isHandlingSessionExpiration = false;
    updateNavbar();
    window.location.href = '/login';
}

function getCartItemCount() {
    return cart.reduce((sum, item) => sum + item.quantity, 0);
}

function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
    updateNavbar();
}

function displayGlobalMessage(message, type = 'info', duration = 5000) {
    const messageContainer = document.getElementById('global-message-container') || document.body.appendChild(document.createElement('div'));
    if (messageContainer.id !== 'global-message-container') messageContainer.id = 'global-message-container';

    const messageElement = document.createElement('div');
    messageElement.className = `global-message ${type}-message`;
    messageElement.innerHTML = `<p>${message}</p><button class="close-btn" onclick="this.parentElement.remove()">×</button>`;
    messageContainer.appendChild(messageElement);
    if (duration !== 0) {
        setTimeout(() => { messageElement.remove(); }, duration);
    }
}

function handleProtectedEntityError(error) {
    if (error && error.message && /protected/i.test(error.message)) {
        const msg = error.message;
        if (/must have at least one|cannot delete the last/i.test(msg)) {
            const userNameForMsg = typeof currentlyViewedUsername !== 'undefined' && currentlyViewedUsername ? currentlyViewedUsername : 'The user';
            displayGlobalMessage(
                `${msg}<br><em><strong>Note:</strong> '${userNameForMsg}' is a protected entity for this demo. For more details on protected entities, please consult your lab guide or the project README.md.</em>`,
                'warning',
                10000
            );
        } else if (/protected default/i.test(msg)) {
            displayGlobalMessage(
                `${msg}<br><em><strong>Note:</strong> This action is restricted for demo stability. Please consult your lab guide or project README.md.</em>`,
                'warning',
                10000
            );
        } else {
            displayGlobalMessage(
                `<strong>Action Blocked:</strong> ${msg}<br><em>This is part of the demo design. Try exploiting a non-protected item or one you created.</em>`,
                'warning',
                8000
            );
        }
        return true;
    }
    return false;
}

function clearFormErrors(formId, fieldConfig) {
    fieldConfig.forEach(({ inputId, errorId }) => {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(errorId);
        if (input) input.classList.remove('is-invalid');
        if (errorEl) {
            errorEl.textContent = '';
            errorEl.style.display = 'none';
        }
    });
}

function validateAndDisplayFormErrors(formId, fieldConfig) {
    let allValid = true;
    fieldConfig.forEach((cfg) => {
        const input = document.getElementById(cfg.inputId);
        const errorEl = document.getElementById(cfg.errorId);
        if (!input) return;
        const value = input.value.trim();
        let valid = true;
        if (cfg.required && !value) valid = false;
        if (valid && cfg.validationFn && value) valid = cfg.validationFn(value);
        if (!valid) {
            allValid = false;
            input.classList.add('is-invalid');
            if (errorEl) {
                errorEl.textContent = cfg.errorMessage || 'Invalid field.';
                errorEl.style.display = 'block';
            }
        }
    });
    return allValid;
}

function showPageLoader(message = 'Loading...') {
    let loader = document.getElementById('page-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'page-loader';
        loader.className = 'loading-indicator-overlay';
        document.body.appendChild(loader);
    }
    loader.innerHTML = `<div class="loading-spinner"></div><p>${message}</p>`;
    loader.style.display = 'flex';
}

function hidePageLoader() {
    const loader = document.getElementById('page-loader');
    if (loader) loader.style.display = 'none';
}

// Full unabridged function with the specified changes, maintaining original structure for Profile Page logic.
function updateUIVulnerabilityFeaturesDisplay(skipProfileRefetch = false) {
    console.log(`UI Vulnerability Demos are now: ${uiVulnerabilityFeaturesEnabled ? 'ENABLED' : 'DISABLED'}`);
    const demoElements = document.querySelectorAll(
        '.ui-demo-dependant, .ui-demo-dependant-block, .ui-demo-dependant-flex, .ui-demo-dependant-grid, .ui-demo-dependant-inline-block'
    );
    demoElements.forEach((el) => {
        if (uiVulnerabilityFeaturesEnabled) {
            el.classList.add('demo-visible');
        } else {
            el.classList.remove('demo-visible');
        }
    });

    // --- Home Page (`index.html`) ---
    if (document.getElementById('search-info')) {
        const searchInfoDiv = document.getElementById('search-info');
        const searchTermInput = document.getElementById('search-term');
        if (searchInfoDiv && searchTermInput) {
            searchTermInput.onfocus = null;
            searchTermInput.onblur = null;

            if (uiVulnerabilityFeaturesEnabled) {
                searchTermInput.onfocus = function () {
                    searchInfoDiv.classList.add('demo-visible');
                };
                searchTermInput.onblur = function () {
                    if (this.value === '') {
                        searchInfoDiv.classList.remove('demo-visible');
                    }
                };
            } else {
                searchInfoDiv.classList.remove('demo-visible');
            }
        }
    }

    // --- Profile Page (`profile.html`) ---
    if (document.getElementById('profile-page-title')) {
        // Visibility of BOLA Demo Sections (User Discovery, Update Profile for BOLA)
        const profileBolaDemoSection = Array.from(document.querySelectorAll('.vulnerability-demo-section'))
            .find(section => section.querySelector('#discover-users-btn'));
        if (profileBolaDemoSection) {
            if (uiVulnerabilityFeaturesEnabled) {
                profileBolaDemoSection.classList.add('demo-visible');
            } else {
                profileBolaDemoSection.classList.remove('demo-visible');
            }
        }
        
        const bolaUpdateProfileDemoSection = Array.from(document.querySelectorAll('.vulnerability-demo-section h4'))
            .find(h4 => h4.textContent.includes('BOLA Demo: Update Profile'))?.closest('.vulnerability-demo-section');
        if (bolaUpdateProfileDemoSection) {
            if (uiVulnerabilityFeaturesEnabled) {
                bolaUpdateProfileDemoSection.classList.add('demo-visible');
            } else {
                bolaUpdateProfileDemoSection.classList.remove('demo-visible');
            }
        }

        // Visibility of Parameter Pollution Demo Section
        const adminEscalationDemoSection = Array.from(document.querySelectorAll('.vulnerability-demo-section h4'))
            .find(h4 => h4.textContent.includes('Parameter Pollution Demo: Admin Escalation'))?.closest('.vulnerability-demo-section');
        if (adminEscalationDemoSection) {
            if (uiVulnerabilityFeaturesEnabled) {
                adminEscalationDemoSection.classList.add('demo-visible');
            } else {
                adminEscalationDemoSection.classList.remove('demo-visible');
            }
        }

        // Control visibility of "Currently viewing" indicator
        const profileViewIndicator = document.getElementById('profile-view-indicator');
        if (profileViewIndicator) {
            if (uiVulnerabilityFeaturesEnabled) {
                // Text content is updated by fetchAndDisplayFullProfile based on currentlyViewedUserId/Username
                // This ensures if BOLA state is active, the text is correct and the indicator is shown.
                const currentViewingUsernameSpan = document.getElementById('current-viewing-username-span');
                if (currentViewingUsernameSpan && typeof currentlyViewedUsername !== 'undefined' && currentlyViewedUsername) { // Check if currentlyViewedUsername is set
                     currentViewingUsernameSpan.textContent = `${currentlyViewedUsername}'s Profile`;
                } else if (currentViewingUsernameSpan && currentUser) { // Fallback if BOLA state vars not fully set yet
                     currentViewingUsernameSpan.textContent = `${currentUser.username}'s Profile`; // Default to own profile text
                }
                profileViewIndicator.classList.add('demo-visible');
            } else {
                profileViewIndicator.classList.remove('demo-visible');
            }
        }
        
        // BOLA Active Banner (Warns when viewing another user's profile with demos ON)
        const bolaDemoActiveBanner = document.getElementById('bola-demo-active-banner');
        if (bolaDemoActiveBanner && currentUser) {
            if (uiVulnerabilityFeaturesEnabled && typeof currentlyViewedUserId !== 'undefined' && currentlyViewedUserId !== currentUser.user_id) {
                bolaDemoActiveBanner.classList.add('demo-visible');
            } else {
                bolaDemoActiveBanner.classList.remove('demo-visible');
            }
        } else if (bolaDemoActiveBanner) {
            bolaDemoActiveBanner.classList.remove('demo-visible');
        }

        // Logic for "Discover Users" and "Return to My Profile" buttons
        const discoverBtn = document.getElementById('discover-users-btn');
        const returnBtn = document.getElementById('return-to-my-profile-btn');
        const discoveredUsersContainer = document.getElementById('discovered-users-container');
        const hiddenUserIdInput = document.getElementById('currently-viewed-user-id');

        if (!uiVulnerabilityFeaturesEnabled) {
            // UI Demos are OFF
            if (discoveredUsersContainer) discoveredUsersContainer.classList.remove('demo-visible');
            if (returnBtn) returnBtn.classList.remove('demo-visible');
            if (discoverBtn) discoverBtn.classList.remove('demo-visible');

            // If demos are turned OFF while viewing another user's BOLA profile, revert view to own profile.
            if (currentUser && hiddenUserIdInput && hiddenUserIdInput.value && hiddenUserIdInput.value !== currentUser.user_id) {
                if (typeof fetchAndDisplayFullProfile === "function") {
                    // The click on returnBtn will handle resetting currentlyViewedUserId and fetching profile
                    if (returnBtn) returnBtn.click(); 
                    else { // Fallback if button somehow removed
                        currentlyViewedUserId = currentUser.user_id;
                        currentlyViewedUsername = currentUser.username;
                        hiddenUserIdInput.value = currentUser.user_id;
                        fetchAndDisplayFullProfile(currentUser.user_id); 
                        displayGlobalMessage('UI Demos disabled. Reverted to viewing your own profile.', 'info');
                    }
                }
            }
        } else {
            // UI Demos are ON
            if (discoverBtn && returnBtn) { 
                if (currentUser && hiddenUserIdInput && hiddenUserIdInput.value && hiddenUserIdInput.value !== currentUser.user_id) {
                    // Viewing another user's profile (BOLA active)
                    returnBtn.classList.add('demo-visible');
                    discoverBtn.classList.remove('demo-visible');
                    if (discoveredUsersContainer) discoveredUsersContainer.classList.remove('demo-visible');
                } else {
                    // Viewing own profile or not yet selected a victim
                    returnBtn.classList.remove('demo-visible');
                    discoverBtn.classList.add('demo-visible');
                }
            }
        }
        // Re-fetch profile to ensure all text (like escalation demo) and indicators are correct after toggle.
        if (!skipProfileRefetch && typeof currentlyViewedUserId !== 'undefined' && currentlyViewedUserId && typeof fetchAndDisplayFullProfile === "function") {
            fetchAndDisplayFullProfile(currentlyViewedUserId);
        }

    }

    // --- Admin Page (`admin_products.html`) ---
    if (document.querySelector('.admin-section h1')?.textContent === 'Admin Dashboard') {
        const ppSection = document.querySelector('.parameter-pollution-controls');
        if (ppSection) {
            if (uiVulnerabilityFeaturesEnabled) {
                ppSection.classList.add('demo-visible');
            } else {
                ppSection.classList.remove('demo-visible');
            }
        }

        if (typeof applyAdminPageDisplay === 'function') {
            applyAdminPageDisplay();
        }
    }

    // --- Product Detail Page (`product_detail.html`) ---
    if (document.getElementById('product-detail-page-body')) {
        const productPollutionDemoSection = document.querySelector('#product-detail-page-body .vulnerability-demo-section');
        if (productPollutionDemoSection) {
            if (uiVulnerabilityFeaturesEnabled) {
                productPollutionDemoSection.classList.add('demo-visible');
            } else {
                productPollutionDemoSection.classList.remove('demo-visible');
            }
        }

        const internalStatusInfoDiv = document.querySelector('.internal-status-badge'); 
        if (internalStatusInfoDiv) {
            internalStatusInfoDiv.style.display = uiVulnerabilityFeaturesEnabled ? 'inline-block' : 'none';
        }
    }

    // --- Checkout Page (`checkout.html`) ---
    if (document.getElementById('checkout-container')) {
        // Get references to all relevant elements
        const bolaDemoSection = document.getElementById('bola-demo-section');
        const normalCheckoutFields = document.getElementById('normal-checkout-fields');
        const placeOrderBtn = document.getElementById('place-order-btn');

        const bolaCheckbox = document.getElementById('order-for-other-user');
        const bolaCheckboxLabelContainer = bolaCheckbox?.closest('.form-group');
        const bolaFields = document.getElementById('bola-demo-fields');
        const bolaWarningContainer = document.getElementById('bola-warning-container');

        // Standard fields and place order button should always be visible by default
        if (normalCheckoutFields) normalCheckoutFields.style.display = 'block';
        if (placeOrderBtn) placeOrderBtn.style.display = 'inline-block';

        if (uiVulnerabilityFeaturesEnabled) {
            if (bolaDemoSection) bolaDemoSection.classList.add('demo-visible');
            if (bolaCheckboxLabelContainer) bolaCheckboxLabelContainer.classList.add('demo-visible');

            if (bolaCheckbox && bolaFields) {
                if (bolaCheckbox.checked) {
                    bolaFields.classList.add('demo-visible');
                    bolaWarningContainer?.classList.add('demo-visible');
                } else {
                    bolaFields.classList.remove('demo-visible');
                    bolaWarningContainer?.classList.remove('demo-visible');
                }
            }
        } else {
            if (bolaDemoSection) bolaDemoSection.classList.remove('demo-visible');
            if (bolaCheckboxLabelContainer) bolaCheckboxLabelContainer.classList.remove('demo-visible');
            if (bolaCheckbox) bolaCheckbox.checked = false;
            if (bolaFields) bolaFields.classList.remove('demo-visible');
            if (bolaWarningContainer) bolaWarningContainer.classList.remove('demo-visible');
        }
    }

    // --- Orders Page (`orders.html`) ---
    if (document.getElementById('orders-container')) {
        document.querySelectorAll('.vulnerability-demo-section').forEach((el) => {
            if (uiVulnerabilityFeaturesEnabled) {
                el.classList.add('demo-visible');
            } else {
                el.classList.remove('demo-visible');
            }
        });

        const currentViewingDivOrders = document.getElementById('current-viewing'); 
        if (!uiVulnerabilityFeaturesEnabled) {
            if (currentViewingDivOrders) currentViewingDivOrders.classList.remove('demo-visible');
            const targetUserIdInputInForm = document.querySelector('#view-orders-form #target-user-id');
            if (targetUserIdInputInForm) targetUserIdInputInForm.value = ''; 

            const viewingUserIdHiddenInputOrders = document.getElementById('viewing-user-id-orders');
            if (typeof fetchAndDisplayOrders === "function" && viewingUserIdHiddenInputOrders && currentUser && viewingUserIdHiddenInputOrders.value !== currentUser.user_id) {
                // Click the "Return to Your Orders" button if it exists and demos are off
                const returnToOwnOrdersBtn = document.getElementById('return-to-own-orders');
                if (returnToOwnOrdersBtn) {
                    returnToOwnOrdersBtn.click();
                } else { // Fallback if button not found
                    viewingUserIdHiddenInputOrders.value = currentUser.user_id;
                    fetchAndDisplayOrders(); 
                    displayGlobalMessage('UI Demos disabled. Reverted to viewing your own orders.', 'info');
                }
            }
        } else {
            // UI Demos are ON
            // If currently viewing another user's orders (BOLA state), ensure the "current-viewing" banner is visible.
            const viewingUserIdHiddenInputOrders = document.getElementById('viewing-user-id-orders');
            if (currentViewingDivOrders && viewingUserIdHiddenInputOrders && currentUser && viewingUserIdHiddenInputOrders.value !== currentUser.user_id) {
                currentViewingDivOrders.classList.add('demo-visible');
                // The text content of this banner is handled by fetchAndDisplayOrders
            } else if (currentViewingDivOrders) {
                currentViewingDivOrders.classList.remove('demo-visible');
            }
        }
    }
}


// Helper function to get product image filename
function getProductImageFilename(product) {
    // Early validation to prevent undefined product issues
    if (!product) {
        console.warn("Product is undefined in getProductImageFilename");
        return 'placeholder.png';
    }

    if (!product.name) {
        console.warn("Product name is undefined in getProductImageFilename for product:", product);
        return 'placeholder.png';
    }
    
    // Map product names to image files
    const imageMap = {
        // Original product names from prepopulated_data.json
        'Laptop Pro 15': 'laptop-15.png',
        'Wireless Mouse': 'ergo-mouse.png',
        'Mechanical Keyboard': 'mech-keyboard.png',
        '4K Monitor 27 inch': 'screen-27.png',
        'Gaming Headset': 'game-headset.png',
        'Smartwatch Series X': 'watch-x.png',
        'Bluetooth Speaker': 'blu-speaker.png',
        'Webcam HD 1080p': 'webcam-hd.png',
        'External SSD 1TB': 'external-ssd.png',
        'Graphics Tablet': 'graphic-tablet.png',
        'Office Chair Ergonomic': 'ergo-chair.png',
        'Noise Cancelling Headphones': 'nc-headphones.png',
        'Smartphone Model Z': 'smartphone-z.png',
        'Portable Charger 20000mAh': 'battery-20000mah.png',
        'VR Headset Advanced': 'vr-headset.png',
        'Digital Camera DSLR': 'dslr-cam.png',
        'Projector Mini HD': 'mini-projector.png',
        'Desk Lamp LED': 'desk-lamp.png',
        'Fitness Tracker Band': 'fitness-tracker.png',
        'E-Reader Pro': 'e-reader.png',
        
        // Alternative names for flexibility
        'VR Headset Pro': 'vr-headset.png',
        'VR Headset': 'vr-headset.png',
        'DSLR Camera': 'dslr-cam.png',
        'Mini Projector': 'mini-projector.png',
        'LED Desk Lamp': 'desk-lamp.png',
        'Smart Fitness Tracker': 'fitness-tracker.png',
        'Fitness Tracker': 'fitness-tracker.png',
        'E-reader 6-inch': 'e-reader.png',
        'E-reader': 'e-reader.png',
        '20000mAh Power Bank': 'battery-20000mah.png',
        'Power Bank': 'battery-20000mah.png',
    };
    
    // Return the mapped image filename or placeholder.png if not found
    return imageMap[product.name] || 'placeholder.png';
}

// Returns both WebP and PNG paths for a product image
function getImagePaths(product) {
    const pngFilename = getProductImageFilename(product);
    const baseName = pngFilename.replace(/\.[^.]+$/, '');
    const pngPath = `/static/images/products/${pngFilename}`;
    const webpPath = `/static/images/products/${baseName}.webp`;
    return { webpPath, pngPath };
}

// Page Initialization Functions
function initHomePage() {
    console.log('Initializing Home Page');
    fetchAndDisplayProducts();
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleProductSearch);
    }
    const searchInfoDiv = document.getElementById('search-info');
    const searchTermInput = document.getElementById('search-term');
    if (searchInfoDiv && searchTermInput) {
        if (uiVulnerabilityFeaturesEnabled) {
            searchTermInput.addEventListener('focus', function () {
                searchInfoDiv.classList.add('demo-visible');
            });
            searchTermInput.addEventListener('blur', function () {
                if (this.value === '') {
                    searchInfoDiv.classList.remove('demo-visible');
                }
            });
        } else {
            searchInfoDiv.classList.remove('demo-visible');
        }
    }
    updateUIVulnerabilityFeaturesDisplay(true);
}

async function handleProductSearch(e) {
    e.preventDefault();
    const searchTerm = document.getElementById('search-term').value.trim();
    const productGrid = document.getElementById('products-container');
    const loadingIndicator = productGrid.querySelector('.loading-indicator');

    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (productGrid && !loadingIndicator) productGrid.innerHTML = '<p class="loading-indicator">Searching...</p>';
    
    try {
        const endpoint = searchTerm ? `/api/products/search?name=${encodeURIComponent(searchTerm)}` : '/api/products';
        const products = await apiCall(endpoint, 'GET', null, false);
        renderProducts(products);
    } catch (error) {
        displayError(`Search error: ${error.message}`);
        if (productGrid) productGrid.innerHTML = '<p>Error loading products.</p>';
    } finally {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
    }
}

function initProductDetailPage() {
    console.log('[main.js] Initializing Product Detail Page');
    const pathParts = window.location.pathname.split('/');
    let productIdSegment = pathParts.pop(); // Get last segment
    if (productIdSegment === "" && pathParts.length > 0) { // Handle trailing slash
        productIdSegment = pathParts.pop();
    }
    
    if (!productIdSegment) {
        console.error("[main.js] Could not extract product ID segment from URL:", window.location.pathname);
        if (typeof displayError === 'function') displayError("Invalid product page URL. Cannot determine product ID.", "product-detail-container");
        else console.error("displayError function not found.");
        return;
    }

    const productId = productIdSegment.replace('.html', ''); // Remove .html if present
    console.log(`[main.js] Product ID extracted: '${productId}'`);

    if (!productId || productId.trim() === "") {
        console.error("[main.js] Product ID is empty after processing URL segment:", productIdSegment);
        if (typeof displayError === 'function') displayError("Invalid or missing product ID in URL.", "product-detail-container");
        else console.error("displayError function not found.");
        // Optionally, hide the loading skeleton if it was shown
        const loadingIndicator = document.getElementById('product-loading');
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        // Show a message in the main container
        const productDetailContainer = document.getElementById('product-detail-container');
        if(productDetailContainer) productDetailContainer.innerHTML = '<p class="error-message">Could not load product: Invalid product ID in URL.</p>';
        return;
    }

    fetchAndDisplayProductDetail(productId);

    // Setup the parameter pollution demo UI elements
    if (typeof setupParameterPollutionDemo === 'function') {
        console.log("[main.js] setupParameterPollutionDemo IS defined. Calling it.");
        setupParameterPollutionDemo(productId);
    } else {
        console.error("[main.js] CRITICAL ERROR: setupParameterPollutionDemo function is NOT defined. The product-detail.js script might not be loaded or parsed correctly.");
    }
    
    // Update visibility of UI demo features based on toggle
    if (typeof updateUIVulnerabilityFeaturesDisplay === 'function') {
        updateUIVulnerabilityFeaturesDisplay(true);
    } else {
        console.warn("[main.js] updateUIVulnerabilityFeaturesDisplay function not found.");
    }
}

function initLoginPage() {
    console.log('Initializing Login Page');
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
}

function initRegisterPage() {
    console.log('Initializing Register Page');
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegistration);
    }
}

function initCartPage() {
    console.log('Initializing Cart Page');
    displayCart();
     const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', (e) => {
            if (!currentUser) {
                e.preventDefault();
                displayGlobalMessage('Please log in to proceed to checkout.', 'error');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            }
        });
    }
}

let currentlyViewedUserId = null;
let currentlyViewedUsername = 'Your'; // Default to 'Your' for titles etc.

// --- Updated Profile Page Initialization ---
function initProfilePage() {
    console.log('Initializing Profile Page');
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }

    currentlyViewedUserId = currentUser.user_id;
    currentlyViewedUsername = currentUser.username;
    const hiddenUserIdInput = document.getElementById('currently-viewed-user-id');
    if (hiddenUserIdInput) {
        hiddenUserIdInput.value = currentlyViewedUserId;
    }


    fetchAndDisplayFullProfile(currentlyViewedUserId);
    setupProfilePageEventListeners();
    updateUIVulnerabilityFeaturesDisplay(true);
}


function setupProfilePageEventListeners() {
    // BOLA Demo Listeners
    document.getElementById('discover-users-btn')?.addEventListener('click', listAvailableVictims);
    document.getElementById('return-to-my-profile-btn')?.addEventListener('click', () => {
        currentlyViewedUserId = currentUser.user_id;
        currentlyViewedUsername = currentUser.username;
        const hiddenUserIdInput = document.getElementById('currently-viewed-user-id');
        if (hiddenUserIdInput) {
            hiddenUserIdInput.value = currentlyViewedUserId;
        }
        
        const discoveredUsersContainer = document.getElementById('discovered-users-container');
        if (discoveredUsersContainer) discoveredUsersContainer.classList.remove('demo-visible');
        
        const returnBtn = document.getElementById('return-to-my-profile-btn');
        if (returnBtn) returnBtn.classList.remove('demo-visible');
        
        const discoverBtn = document.getElementById('discover-users-btn');
        if (discoverBtn) discoverBtn.classList.add('demo-visible');

        fetchAndDisplayFullProfile(currentlyViewedUserId);
        displayGlobalMessage('Returned to viewing your own profile.', 'info');
    });

    // Edit Email Listeners
    document.getElementById('toggle-edit-email-form-btn')?.addEventListener('click', toggleEditEmailForm);
    document.getElementById('edit-email-form')?.addEventListener('submit', handleEditEmailSubmit);
    document.getElementById('cancel-edit-email-btn')?.addEventListener('click', () => {
        const editEmailForm = document.getElementById('edit-email-form');
        const toggleBtn = document.getElementById('toggle-edit-email-form-btn');
        if (editEmailForm) editEmailForm.style.display = 'none';
        if (toggleBtn) toggleBtn.style.display = 'inline-block';
    });

    // Admin Escalation Listener
    document.getElementById('attempt-admin-escalation-btn')?.addEventListener('click', attemptAdminEscalation);

    document.getElementById('update-profile-form')?.addEventListener('submit', handleUpdateProfileSubmit);

    // Address Form Listeners
    document.getElementById('toggle-address-form-btn')?.addEventListener('click', () => toggleItemForm('address'));
    document.getElementById('address-form')?.addEventListener('submit', handleAddressFormSubmit);
    document.getElementById('address-form-cancel-btn')?.addEventListener('click', () => cancelItemForm('address'));

    // Credit Card Form Listeners
    document.getElementById('toggle-card-form-btn')?.addEventListener('click', () => toggleItemForm('card'));
    document.getElementById('card-form')?.addEventListener('submit', handleCardFormSubmit);
    document.getElementById('card-form-cancel-btn')?.addEventListener('click', () => cancelItemForm('card'));
}
// --- BOLA Demo Functions ---
async function listAvailableVictims() {
    const usersListElement = document.getElementById('discovered-users-list');
    const usersContainer = document.getElementById('discovered-users-container');
    if (!usersListElement || !usersContainer) {
        console.error("Missing elements for victim discovery.");
        return;
    }

    usersListElement.innerHTML = '<li class="list-group-item">Discovering users (BFLA Exploit)... <i class="fas fa-spinner fa-spin"></i></li>';
    usersContainer.style.display = 'block';

    try {
        showPageLoader('Loading users...');
        const users = await apiCall('/api/users', 'GET');
        if (users && users.length > 0) {
            usersListElement.innerHTML = ''; 
            users.forEach(user => {
                if (user.user_id === currentUser.user_id) return; 

                const listItem = document.createElement('li');
                listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                listItem.innerHTML = `
                    <span>${user.username} (ID: <code>${user.user_id.substring(0,8)}...</code>)</span>
                    <button type="button" class="btn btn-sm btn-outline-danger select-victim-btn" data-victim-id="${user.user_id}" data-victim-name="${user.username}">
                        <i class="fas fa-eye"></i> View Profile (BOLA Exploit)
                    </button>
                `;
                usersListElement.appendChild(listItem);
            });

            document.querySelectorAll('.select-victim-btn').forEach(button => {
                button.addEventListener('click', function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                    const victimId = this.dataset.victimId;
                    const victimName = this.dataset.victimName;
                    
                    currentlyViewedUserId = victimId;
                    currentlyViewedUsername = victimName; 
                    const hiddenUserIdInput = document.getElementById('currently-viewed-user-id');
                    if (hiddenUserIdInput) {
                        hiddenUserIdInput.value = victimId;
                    }
                    
                    fetchAndDisplayFullProfile(victimId);
                    
                    document.getElementById('return-to-my-profile-btn').style.display = 'inline-block';
                    document.getElementById('discover-users-btn').style.display = 'none';
                    usersContainer.style.display = 'none'; 
                    displayGlobalMessage(`Now viewing ${victimName}'s profile. (BOLA Demo Active)`, 'warning');
                });
            });
        } else {
            usersListElement.innerHTML = '<li class="list-group-item">No other users found.</li>';
        }
    } catch (error) {
        displayGlobalMessage(`Error discovering users: ${error.message}`, 'error');
        usersListElement.innerHTML = `<li class="list-group-item text-danger">Failed to load users. Check console.</li>`;
    } finally {
        hidePageLoader();
    }
}


// Full unabridged function with the specified changes
async function fetchAndDisplayFullProfile(userId) {
    // Close any open forms when switching profiles
    cancelItemForm('address');
    cancelItemForm('card');
    const editEmailForm = document.getElementById('edit-email-form');
    if (editEmailForm) editEmailForm.style.display = 'none';
    const toggleEditEmailBtn = document.getElementById('toggle-edit-email-form-btn');
    if (toggleEditEmailBtn) toggleEditEmailBtn.style.display = 'inline-block';


    const profileInfoContent = document.getElementById('profile-info-content');
    const addressListContainer = document.getElementById('address-list-container');
    const cardListContainer = document.getElementById('card-list-container');
    const profilePageTitle = document.getElementById('profile-page-title');
    const userInfoHeader = document.getElementById('user-info-header');
    const addressesHeader = document.getElementById('addresses-header'); // Target for "Addresses" header
    const creditCardsHeader = document.getElementById('credit-cards-header'); // Target for "Credit Cards" header
    const profileViewIndicator = document.getElementById('profile-view-indicator'); 
    const currentViewingUsernameSpan = document.getElementById('current-viewing-username-span');
    const bolaDemoActiveBanner = document.getElementById('bola-demo-active-banner');
    const escalationTargetUsernameStrong = document.getElementById('escalation-target-username'); 
    const escalationTargetBtnUsernameSpan = document.getElementById('escalation-target-btn-username'); 
    const hiddenUserIdInput = document.getElementById('currently-viewed-user-id');


    if (profileInfoContent) profileInfoContent.innerHTML = '<p class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading profile...</p>';
    if (addressListContainer) addressListContainer.innerHTML = '<p class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading addresses...</p>';
    if (cardListContainer) cardListContainer.innerHTML = '<p class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading cards...</p>';
    
    if (hiddenUserIdInput) hiddenUserIdInput.value = userId;


    try {
        showPageLoader('Loading profile...');
        const userDetails = await apiCall(`/api/users/${userId}`, 'GET');
        currentlyViewedUsername = userDetails.username; 

        const possessiveName = `${userDetails.username}'s`; 
        const displayNameForUserInfoHeader = userDetails.username; // Keep this for the "User Information" header

        if (profilePageTitle) profilePageTitle.textContent = `${possessiveName} Profile`;
        if (userInfoHeader) userInfoHeader.textContent = `${displayNameForUserInfoHeader}'s Information`; // User specific for main info header

        // --- Change Applied Here ---
        // Make "Addresses" and "Credit Cards" headers static
        if (addressesHeader) addressesHeader.innerHTML = `<i class="fas fa-map-marker-alt address-icon"></i> Addresses`;
        if (creditCardsHeader) creditCardsHeader.innerHTML = `<i class="fas fa-credit-card card-icon"></i> Credit Cards`;
        // --- End of Change ---
        
        if(profileViewIndicator && currentViewingUsernameSpan) {
            currentViewingUsernameSpan.textContent = `${userDetails.username}'s Profile`; 
            if (uiVulnerabilityFeaturesEnabled) {
                profileViewIndicator.style.display = 'block';
            } else {
                profileViewIndicator.style.display = 'none';
            }
        }

        if(bolaDemoActiveBanner) {
            bolaDemoActiveBanner.style.display = (uiVulnerabilityFeaturesEnabled && currentUser && userId !== currentUser.user_id) ? 'block' : 'none';
        }
        
        if (escalationTargetUsernameStrong && escalationTargetBtnUsernameSpan) {
            escalationTargetUsernameStrong.textContent = `${userDetails.username}'s profile`;
            escalationTargetBtnUsernameSpan.textContent = userDetails.username;
        }


        if (profileInfoContent) {
            profileInfoContent.innerHTML = `
                <p><strong>Username:</strong> ${userDetails.username} ${userDetails.is_admin ? '<span class="admin-badge">Admin</span>' : ''}</p>
                <p><strong>Email:</strong> <span id="current-email-display">${userDetails.email}</span></p>
                <p><strong>User ID:</strong> <code>${userDetails.user_id}</code></p>
            `;
            const newEmailInput = document.getElementById('new-email-input');
            if (newEmailInput) newEmailInput.value = userDetails.email;
        }

        const addresses = await apiCall(`/api/users/${userId}/addresses`, 'GET');
        renderAddresses(addresses, addressListContainer);

        const cards = await apiCall(`/api/users/${userId}/credit-cards`, 'GET');
        renderCreditCards(cards, cardListContainer);

    } catch (error) {
        displayGlobalMessage(`Error loading profile for User ID ${userId.substring(0,8)}...: ${error.message}`, 'error');
        if (profileInfoContent) profileInfoContent.innerHTML = '<p class="text-danger">Could not load profile information.</p>';
        if (addressListContainer) addressListContainer.innerHTML = '<p class="text-danger">Could not load addresses.</p>';
        if (cardListContainer) cardListContainer.innerHTML = '<p class="text-danger">Could not load credit cards.</p>';
        
        if (currentUser && userId !== currentUser.user_id) {
            displayGlobalMessage("Failed to load target user's profile. Returning to your profile.", "error");
            const returnBtn = document.getElementById('return-to-my-profile-btn');
            if(returnBtn) returnBtn.click(); 
        } else if (!currentUser && userId) { 
             console.error("Trying to load profile without a logged-in user context and failed.");
        }
    } finally {
        const victimEls = [
            document.getElementById('address-form-container'),
            document.getElementById('card-form-container'),
            document.getElementById('address-list-container'),
            document.getElementById('card-list-container')
        ];
        if (uiVulnerabilityFeaturesEnabled && currentUser && userId !== currentUser.user_id) {
            victimEls.forEach(el => el && el.classList.add('victim-data-active'));
        } else {
            victimEls.forEach(el => el && el.classList.remove('victim-data-active'));
        }
        hidePageLoader();
    }
}

// --- Email Edit Functions ---
function toggleEditEmailForm() {
    const form = document.getElementById('edit-email-form');
    const button = document.getElementById('toggle-edit-email-form-btn');
    const currentEmailDisplay = document.getElementById('current-email-display');
    
    if (!form || !button || !currentEmailDisplay) return;

    const currentEmail = currentEmailDisplay.textContent;
    const newEmailInput = document.getElementById('new-email-input');
    if (newEmailInput) newEmailInput.value = currentEmail;
    
    if (form.style.display === 'none') {
        form.style.display = 'block';
        button.style.display = 'none';
    } else {
        form.style.display = 'none';
        button.style.display = 'inline-block';
    }
}

async function handleEditEmailSubmit(event) {
    event.preventDefault();
    const newEmailInput = document.getElementById('new-email-input');
    if (!newEmailInput) return;
    const newEmail = newEmailInput.value.trim();

    if (!newEmail) {
        displayGlobalMessage('Email cannot be empty.', 'error');
        return;
    }

    const userIdToUpdate = document.getElementById('currently-viewed-user-id').value;
    if (!userIdToUpdate) {
        displayGlobalMessage('Error: No user context for updating email.', 'error');
        return;
    }
    
    const endpoint = `/api/users/${userIdToUpdate}?email=${encodeURIComponent(newEmail)}`;

    try {
        showPageLoader('Updating email...');
        await apiCall(endpoint, 'PUT', null, true);
        displayGlobalMessage(`Email for ${currentlyViewedUsername} updated successfully!`, 'success');
        await fetchAndDisplayFullProfile(userIdToUpdate);
        
        if (userIdToUpdate === currentUser.user_id) {
            currentUser.email = newEmail;
            localStorage.setItem('user', JSON.stringify(currentUser));
            updateNavbar(); 
        }
    } catch (error) {
        displayGlobalMessage(`Failed to update email for ${currentlyViewedUsername}: ${error.message}`, 'error');
    } finally {
        hidePageLoader();
    }
}

async function handleUpdateProfileSubmit(event) {
    event.preventDefault();
    const userIdToUpdate = document.getElementById('currently-viewed-user-id').value;
    const username = document.getElementById('update-username-input')?.value.trim();
    const email = document.getElementById('update-email-input')?.value.trim();
    if (!userIdToUpdate) {
        displayGlobalMessage('Error: No user context for profile update.', 'error');
        return;
    }
    const params = new URLSearchParams();
    if (username) params.append('username', username);
    if (email) params.append('email', email);
    if ([...params].length === 0) {
        displayGlobalMessage('Provide a username or email to update.', 'error');
        return;
    }
    const endpoint = `/api/users/${userIdToUpdate}?${params.toString()}`;
    try {
        showPageLoader('Updating profile...');
        await apiCall(endpoint, 'PUT', null, true);
        displayGlobalMessage(`Profile for ${currentlyViewedUsername} updated.`, 'success');
        await fetchAndDisplayFullProfile(userIdToUpdate);
        if (userIdToUpdate === currentUser.user_id) {
            if (username) currentUser.username = username;
            if (email) currentUser.email = email;
            localStorage.setItem('user', JSON.stringify(currentUser));
            updateNavbar();
        }
    } catch (error) {
        displayGlobalMessage(`Failed to update profile: ${error.message}`, 'error');
    } finally {
        hidePageLoader();
    }
}
// --- Parameter Pollution: Admin Escalation ---
// Full unabridged function with the specified changes
async function attemptAdminEscalation() {
    const userIdToEscalate = document.getElementById('currently-viewed-user-id').value;
    if (!userIdToEscalate) {
        displayGlobalMessage('Error: No user context for admin escalation.', 'error');
        return;
    }

    // Determine the name for confirmation message - uses currentlyViewedUsername which is updated by fetchAndDisplayFullProfile
    const userToEscalateName = (typeof currentlyViewedUsername !== 'undefined' && currentlyViewedUsername) ? currentlyViewedUsername : "the selected user";
    
    if (!confirm(`Attempt to make ${userToEscalateName} an admin? This demonstrates Parameter Pollution.`)) return;

    const endpoint = `/api/users/${userIdToEscalate}?is_admin=true`;

    try {
        showPageLoader('Attempting admin escalation...');
        const updatedUserObject = await apiCall(endpoint, 'PUT', null, true); // Capture the returned updated user

        if (updatedUserObject) {
            displayGlobalMessage(`Admin escalation attempt successful for ${userToEscalateName}. Refreshing profile...`, 'success');

            // Check if the escalated user is the currently logged-in user
            if (currentUser && updatedUserObject.user_id === currentUser.user_id) {
                // Update the global currentUser object and localStorage
                currentUser = updatedUserObject; // Update with the full new user object
                localStorage.setItem('user', JSON.stringify(currentUser));
                
                // Immediately update the navbar
                updateNavbar();
                
                displayGlobalMessage(`Your privileges have been updated to ${currentUser.is_admin ? 'Admin' : 'User'}. Navbar updated.`, 'success', 7000);
            }
            
            // Refresh the profile view to show the admin badge (or lack thereof)
            // and ensure all other profile details are current.
            // fetchAndDisplayFullProfile will also use the latest currentlyViewedUsername.
            await fetchAndDisplayFullProfile(userIdToEscalate);
        } else {
            // This case should ideally not happen if the API always returns the updated user on success.
            displayGlobalMessage(`Admin escalation attempt sent for ${userToEscalateName}. Refreshing profile (API did not return updated user)...`, 'warning');
            await fetchAndDisplayFullProfile(userIdToEscalate);
        }

    } catch (error) {
        displayGlobalMessage(`Admin escalation attempt failed for ${userToEscalateName}: ${error.message}`, 'error');
    } finally {
        hidePageLoader();
    }
}


// --- Generic Item Form Toggle and Cancel ---
function toggleItemForm(itemType) { 
    const formContainer = document.getElementById(`${itemType}-form-container`);
    const toggleBtn = document.getElementById(`toggle-${itemType}-form-btn`);
    const editModeIndicator = document.getElementById(`${itemType}-edit-mode-indicator`);

    if (!formContainer || !toggleBtn) return;

    const isOpen = formContainer.classList.toggle('open');
    toggleBtn.classList.toggle('active', isOpen);
    const icon = toggleBtn.querySelector('i');
    const span = toggleBtn.querySelector('span');

    if (isOpen) {
        if (icon) icon.className = 'fas fa-minus';
        if (span) span.textContent = 'Cancel';
        formContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        if (icon) icon.className = 'fas fa-plus';
        if (span) span.textContent = toggleBtn.dataset.addText || `Add New ${itemType.charAt(0).toUpperCase() + itemType.slice(1)}`;
        if (editModeIndicator) editModeIndicator.style.display = 'none';
        
        const form = document.getElementById(`${itemType}-form`);
        if (form) form.reset();
        
        const hiddenIdInput = document.getElementById(`${itemType}-id-hidden`);
        if (hiddenIdInput) hiddenIdInput.value = '';
        
        const submitBtn = document.getElementById(`${itemType}-form-submit-btn`);
        if (submitBtn) submitBtn.textContent = `Add ${itemType.charAt(0).toUpperCase() + itemType.slice(1)}`;
        
        if (itemType === 'card') { 
            const cardNumberInput = document.getElementById('card-number-input');
            const cardCvvInput = document.getElementById('card-cvv-input');
            if(cardNumberInput) {
                cardNumberInput.placeholder = 'Required for new cards';
                cardNumberInput.disabled = false;
            }
            if(cardCvvInput) {
                cardCvvInput.placeholder = 'Required for new cards';
                cardCvvInput.disabled = false;
            }
        }
    }
}

function cancelItemForm(itemType) {
    const formContainer = document.getElementById(`${itemType}-form-container`);
    const toggleBtn = document.getElementById(`toggle-${itemType}-form-btn`);
    const editModeIndicator = document.getElementById(`${itemType}-edit-mode-indicator`);

    if (formContainer) formContainer.classList.remove('open');
    if (toggleBtn) {
        toggleBtn.classList.remove('active');
        const icon = toggleBtn.querySelector('i');
        const span = toggleBtn.querySelector('span');
        if (icon) icon.className = 'fas fa-plus';
        if (span) span.textContent = toggleBtn.dataset.addText || `Add New ${itemType.charAt(0).toUpperCase() + itemType.slice(1)}`;
    }
    if (editModeIndicator) editModeIndicator.style.display = 'none';
    
    const form = document.getElementById(`${itemType}-form`);
    if(form) form.reset();

    const hiddenIdInput = document.getElementById(`${itemType}-id-hidden`);
    if(hiddenIdInput) hiddenIdInput.value = '';
    
    const submitBtn = document.getElementById(`${itemType}-form-submit-btn`);
    if(submitBtn) submitBtn.textContent = `Add ${itemType.charAt(0).toUpperCase() + itemType.slice(1)}`;

    if (itemType === 'card') {
        const cardNumberInput = document.getElementById('card-number-input');
        const cardCvvInput = document.getElementById('card-cvv-input');
        if(cardNumberInput) {
            cardNumberInput.placeholder = 'Required for new cards';
            cardNumberInput.disabled = false;
        }
        if(cardCvvInput) {
            cardCvvInput.placeholder = 'Required for new cards';
            cardCvvInput.disabled = false;
        }
    }

    if (itemType === 'address') {
        clearFormErrors('address-form', [
            { inputId: 'address-street', errorId: 'address-street-error' },
            { inputId: 'address-city', errorId: 'address-city-error' },
            { inputId: 'address-country', errorId: 'address-country-error' },
            { inputId: 'address-zip', errorId: 'address-zip-error' },
        ]);
    } else if (itemType === 'card') {
        clearFormErrors('card-form', [
            { inputId: 'card-cardholder-name', errorId: 'card-cardholder-name-error' },
            { inputId: 'card-number-input', errorId: 'card-number-input-error' },
            { inputId: 'card-expiry-month', errorId: 'card-expiry-month-error' },
            { inputId: 'card-expiry-year', errorId: 'card-expiry-year-error' },
            { inputId: 'card-cvv-input', errorId: 'card-cvv-input-error' },
        ]);
    }
}


// --- Address Management Functions ---
function renderAddresses(addresses, container) {
    if (!container) return;
    // const userIdForRequest = document.getElementById('currently-viewed-user-id').value; // Not needed if onclick calls global currentlyViewedUserId

    if (!addresses || addresses.length === 0) {
        container.innerHTML = `<div class="empty-state"><i class="fas fa-map-marker-alt"></i><p>No addresses found for ${currentlyViewedUsername}.</p></div>`;
        return;
    }
    let html = addresses.map(addr => `
        <div class="item-card address-card" id="address-item-${addr.address_id.substring(0,8)}">
            <div class="item-card-header">
                <i class="fas fa-map-marker-alt"></i>
                <h4>${addr.street}${addr.is_protected ? ' <span class="protected-indicator" title="This item is protected for core demo stability. Destructive actions are limited.">🛡️ Protected</span>' : ''}
                    ${addr.is_default ? '<span class="default-badge">Default</span>' : `<button class="btn-xs set-default-btn" onclick="setDefaultAddress('${addr.address_id}')">Set Default</button>`}
                </h4>
            </div>
            <div class="item-card-content">
                <p><i class="fas fa-city"></i> ${addr.city}, ${addr.country}</p>
                <p><i class="fas fa-mail-bulk"></i> ${addr.zip_code}</p>
                <p class="text-muted"><small>ID: ${addr.address_id.substring(0,8)}...</small></p>
            </div>
            <div class="item-actions">
                <button class="btn btn-sm btn-secondary edit-address-btn" data-address-id="${addr.address_id}" data-is-protected="${addr.is_protected}"><i class="fas fa-pen"></i> Edit</button>
                <button class="btn btn-sm btn-danger delete-address-btn" data-address-id="${addr.address_id}" data-is-protected="${addr.is_protected}"><i class="fas fa-trash"></i> Delete</button>
            </div>
        </div>
    `).join('');
    container.innerHTML = html;

    document.querySelectorAll('.edit-address-btn').forEach(btn =>
        btn.addEventListener('click', () => populateAddressFormForEdit(btn.dataset.addressId, addresses))
    );
    document.querySelectorAll('.delete-address-btn').forEach(btn =>
        btn.addEventListener('click', () => handleDeleteAddress(btn.dataset.addressId, btn.dataset.isProtected === 'true'))
    );
}

function initCheckoutPage() {
    console.log('Initializing Checkout Page');
    if (!currentUser) {
        displayGlobalMessage('Please log in to proceed to checkout.', 'error');
        setTimeout(() => { window.location.href = '/login'; }, 2000);
        return;
    }
    if (cart.length === 0) {
        displayGlobalMessage('Your cart is empty. Go shop!', 'info');
        setTimeout(() => { window.location.href = '/'; }, 2000);
        return;
    }

    displayCheckoutItems(); 
    populateAddressDropdown();  
    populateCreditCardDropdown(); 
    
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function (e) {
            if (e.submitter && e.submitter.id !== 'place-order-btn') {
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            handleOrderSubmission(e);
        });
    }
    
    const bolaCheckbox = document.getElementById('order-for-other-user');
    const bolaFields = document.getElementById('bola-demo-fields'); 
    const targetUserIdInput = document.getElementById('target-user-id');
    const targetAddressIdInput = document.getElementById('target-address-id');
    const targetCreditCardIdInput = document.getElementById('target-credit-card-id');
    const bolaWarningContainerOnCheckout = document.getElementById('bola-warning-container'); // Specific warning div on checkout.html

    if (bolaCheckbox) {
        bolaCheckbox.addEventListener('change', function() {
            if (bolaFields) {
                bolaFields.classList.toggle('demo-visible', this.checked);
            }
            
            if (targetUserIdInput) {
                targetUserIdInput.disabled = !this.checked;
                if (!this.checked) targetUserIdInput.value = ''; 
            }
            if (targetAddressIdInput) {
                targetAddressIdInput.disabled = !this.checked;
                if (!this.checked) targetAddressIdInput.value = ''; 
            }
            if (targetCreditCardIdInput) {
                targetCreditCardIdInput.disabled = !this.checked;
                if (!this.checked) targetCreditCardIdInput.value = ''; 
            }
            
            if (bolaWarningContainerOnCheckout) {
                 bolaWarningContainerOnCheckout.classList.toggle('demo-visible', this.checked);
                 if (this.checked) {
                    bolaWarningContainerOnCheckout.innerHTML = `
                        <h3>⚠️ BOLA Vulnerability Exploit Mode Active!</h3>
                        <p>You are now configuring an order that may use another user's details or payment methods.
                           Proceed with caution for demonstration purposes.</p>
                        <p>If Target User ID is left blank, the order will be placed for <strong>you (${currentUser.username})</strong>.</p>
                        <p>If Target Address ID is left blank, your selected/default address will be used for shipping.</p>
                        <p><strong>You MUST select/enter a Target Credit Card ID to demonstrate payment theft.</strong></p>
                    `;
                 } else {
                    bolaWarningContainerOnCheckout.innerHTML = '';
                 }
            }

            if (!this.checked) {
                const userSearchResults = document.getElementById('user-search-results');
                if (userSearchResults) userSearchResults.style.display = 'none';
                
                const addressSearchResults = document.getElementById('address-search-results');
                if (addressSearchResults) addressSearchResults.style.display = 'none';

                const cardSearchResults = document.getElementById('card-search-results');
                if (cardSearchResults) cardSearchResults.style.display = 'none';
                
                const theftPreview = document.getElementById('theft-preview');
                if (theftPreview) {
                    theftPreview.innerHTML = '<div class="no-theft-selected alert alert-secondary">Enable BOLA exploit and select a target card to see preview.</div>';
                }
            }

            if (typeof updateUIVulnerabilityFeaturesDisplay === 'function') {
                updateUIVulnerabilityFeaturesDisplay(true);
            }
        });
    }
    
    document.getElementById('search-users-btn')?.addEventListener('click', searchUsers);
    document.getElementById('search-addresses-btn')?.addEventListener('click', searchAddressesForBola);
    document.getElementById('search-cards-btn')?.addEventListener('click', searchCreditCards);
    
    const theftPreview = document.getElementById('theft-preview');
    if (theftPreview) {
        theftPreview.innerHTML = '<div class="no-theft-selected alert alert-secondary">Enable BOLA exploit and select a target card to see preview.</div>';
    }
    updateUIVulnerabilityFeaturesDisplay(true);
}

async function searchUsers() {
    const userList = document.getElementById('user-list');
    const resultsContainer = document.getElementById('user-search-results');
    if (!userList || !resultsContainer) return;
    
    userList.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Searching for users...</p>';
    resultsContainer.style.display = 'block';

    try {
        const users = await apiCall('/api/users', 'GET'); 
        if (!users || users.length === 0) {
            userList.innerHTML = '<p class="text-muted">No other users found to target.</p>';
            return;
        }
        
        let usersHTML = '<ul class="demo-result-list">';
        users.forEach(user => {
            if (user.user_id === currentUser.user_id) return; 
            usersHTML += `
                <li class="demo-user-item">
                    <div>
                        <strong>${user.username}</strong><br>
                        <small>ID: <code>${user.user_id.substring(0,8)}...</code></small>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-primary select-user-btn"
                            data-user-id="${user.user_id}"
                            data-username="${user.username}">Select User</button>
                </li>`;
        });
        usersHTML += '</ul>';
        userList.innerHTML = usersHTML;
        
        document.querySelectorAll('.select-user-btn').forEach(btn => {
            btn.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                document.getElementById('target-user-id').value = this.getAttribute('data-user-id');
                displayGlobalMessage(`Target user set to: ${this.getAttribute('data-username')}`, 'info');
                document.getElementById('search-addresses-btn')?.click();
                document.getElementById('search-cards-btn')?.click();
            });
        });
    } catch (error) {
        userList.innerHTML = `<p class="text-danger">Error loading users: ${error.message}</p>`;
    }
}

async function searchCreditCards() {
    const targetUserIdInput = document.getElementById('target-user-id');
    const targetUserId = targetUserIdInput ? targetUserIdInput.value.trim() : null;
    const cardListDiv = document.getElementById('card-list');
    const resultsContainer = document.getElementById('card-search-results');
    const theftPreview = document.getElementById('theft-preview');

    if (!cardListDiv || !resultsContainer) return;

    const userIdToSearchCards = targetUserId || (currentUser ? currentUser.user_id : null);

    if (!userIdToSearchCards) {
        cardListDiv.innerHTML = '<p class="text-danger">Please select or enter a Target User ID first to search for their cards.</p>';
        resultsContainer.style.display = 'block';
        if (theftPreview) theftPreview.innerHTML = '<div class="no-theft-selected alert alert-secondary">Select a target user and then search for their cards.</div>';
        return;
    }

    cardListDiv.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Searching for credit cards...</p>';
    resultsContainer.style.display = 'block';
    if (theftPreview) theftPreview.innerHTML = '<div class="alert alert-info">Searching for payment methods for the target user...</div>';

    try {
        let targetUserNameForDisplay = "Target User"; 
        try {
            const userInfo = await apiCall(`/api/users/${userIdToSearchCards}`, 'GET', null, true);
            if (userInfo && userInfo.username) targetUserNameForDisplay = userInfo.username;
        } catch (e) { console.warn("Couldn't fetch target user details:", e); }

        const cards = await apiCall(`/api/users/${userIdToSearchCards}/credit-cards`, 'GET', null, true);
        if (!cards || cards.length === 0) {
            cardListDiv.innerHTML = `<p class="text-muted">No credit cards found for ${targetUserNameForDisplay}.</p>`;
            if (theftPreview) theftPreview.innerHTML = `<div class="no-theft-selected alert alert-secondary">No cards found for ${targetUserNameForDisplay}.</div>`;
            return;
        }
        
        if (theftPreview) {
             theftPreview.innerHTML = `
                <div class="alert alert-secondary">
                    <h4 class="alert-heading">Configuring BOLA Payment Exploit</h4>
                    <p>Select a card below to use for the order. The order will be placed by <strong>${currentUser.username}</strong> (you).</p>
                    <p><strong>Targeting cards of:</strong> ${targetUserNameForDisplay} (ID: ${userIdToSearchCards.substring(0,8)}...)</p>
                </div>
            `;
        }

        let cardsHTML = '<ul class="demo-card-list">';
        cards.forEach(card => {
            const isDefaultBadge = card.is_default ? '<span class="default-badge">Default</span>' : '';
            cardsHTML += `
                <li class="demo-card-item ${card.is_default ? 'is-default' : ''}">
                    <div class="demo-card-info">
                        <strong>${card.cardholder_name}</strong> ${isDefaultBadge}<br>
                        <small>Card: •••• ${card.card_last_four} | Expires: ${card.expiry_month}/${card.expiry_year.substring(2)}</small><br>
                        <small>ID: <code>${card.card_id.substring(0,8)}...</code></small>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger select-card-btn"
                            data-card-id="${card.card_id}"
                            data-last-four="${card.card_last_four}"
                            data-cardholder-name="${card.cardholder_name}"
                            data-owner-name="${targetUserNameForDisplay}">
                        Use This Card
                    </button>
                </li>`;
        });
        cardsHTML += '</ul>';
        cardListDiv.innerHTML = cardsHTML;

        document.querySelectorAll('.select-card-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const cardId = this.getAttribute('data-card-id');
                const lastFour = this.getAttribute('data-last-four');
                const cardholderName = this.getAttribute('data-cardholder-name');
                const ownerName = this.getAttribute('data-owner-name'); 

                document.getElementById('target-credit-card-id').value = cardId;

                document.querySelectorAll('#card-list .demo-card-item.selected').forEach(item => item.classList.remove('selected'));
                this.closest('.demo-card-item').classList.add('selected');
                
                if (theftPreview) {
                    theftPreview.innerHTML = `
                        <div class="card-theft-preview">
                             <h4><span class="exploit-indicator">EXPLOIT READY</span> Payment Method Selected for BOLA:</h4>
                             <div class="stolen-card-details">
                                <p class="card-detail-row"><span class="card-detail-label">Victim Cardholder:</span> <span class="card-detail-value">${cardholderName} (${ownerName})</span></p>
                                <p class="card-detail-row"><span class="card-detail-label">Card:</span> <span class="card-detail-value">•••• •••• •••• ${lastFour}</span> <span class="stolen-badge">VICTIM'S</span></p>
                                <p class="card-detail-row"><span class="card-detail-label">Card ID:</span> <code>${cardId.substring(0,8)}...</code></p>
                             </div>
                             <p class="mt-2">Order will be placed by <strong>${currentUser.username}</strong>. Shipping address will be based on your selection in the main form or the BOLA address field (if filled).</p>
                             <p>Click "Place Order" to execute.</p>
                        </div>
                    `;
                }
            });
        });
    } catch (error) {
        cardListDiv.innerHTML = `<p class="text-danger">Error loading credit cards: ${error.message}</p>`;
        if (theftPreview) theftPreview.innerHTML = '<div class="alert alert-danger">Error fetching cards.</div>';
    }
}


async function updateTargetUserInfo() {
    const targetUserId = document.getElementById('target-user-id').value.trim();
    const userInfoContainer = document.getElementById('target-user-info');
    const userInfoContent = document.getElementById('user-info-content');
    
    if (!targetUserId || !userInfoContainer || !userInfoContent) {
        if (userInfoContainer) userInfoContainer.style.display = 'none';
        return;
    }
    
    userInfoContent.innerHTML = '<p>Loading user information...</p>';
    userInfoContainer.style.display = 'block';
    
    try {
        // Attempt to fetch the target user's information (BOLA vulnerability)
        const user = await apiCall(`/api/users/${targetUserId}`, 'GET', null, true);
        
        if (!user) {
            userInfoContent.innerHTML = '<p>User not found.</p>';
            return;
        }
        
        // Fetch the user's addresses and default payment method
        let addresses = [];
        let cards = [];
        
        try {
            addresses = await apiCall(`/api/users/${targetUserId}/addresses`, 'GET', null, true);
        } catch (error) {
            console.warn(`Could not fetch addresses for user ${targetUserId}:`, error);
        }
        
        try {
            cards = await apiCall(`/api/users/${targetUserId}/credit-cards`, 'GET', null, true);
        } catch (error) {
            console.warn(`Could not fetch credit cards for user ${targetUserId}:`, error);
        }
        
        // Find default address and card
        const defaultAddress = addresses.find(addr => addr.is_default);
        const defaultCard = cards.find(card => card.is_default);
        
        // Display user info
        let infoHTML = `
            <div class="user-preview">
                <p><strong>Username:</strong> ${user.username}</p>
                <p><strong>Email:</strong> ${user.email}</p>
                
                <div class="user-preview-details">
                    <div class="preview-section">
                        <h5>Default Address:</h5>
                        ${defaultAddress ? 
                            `<p>${defaultAddress.street}, ${defaultAddress.city}, ${defaultAddress.country}</p>` :
                            '<p>No default address</p>'}
                    </div>
                    
                    <div class="preview-section">
                        <h5>Default Payment:</h5>
                        ${defaultCard ? 
                            `<p>Card ending in ${defaultCard.card_last_four} (${defaultCard.cardholder_name})</p>` :
                            '<p>No default payment method</p>'}
                    </div>
                </div>
                
                <div class="vulnerability-alert">
                    <p>⚠️ <strong>BOLA Vulnerability:</strong> You're accessing another user's data!</p>
                </div>
            </div>
        `;
        
        userInfoContent.innerHTML = infoHTML;
        
    } catch (error) {
        userInfoContent.innerHTML = `<p>Error loading user information: ${error.message}</p>`;
    }
}


async function searchAddressesForBola() {
    const targetUserIdInput = document.getElementById('target-user-id');
    const targetUserId = targetUserIdInput ? targetUserIdInput.value.trim() : null;
    const addressListDiv = document.getElementById('address-list');
    const resultsContainer = document.getElementById('address-search-results');

    if (!addressListDiv || !resultsContainer) {
        console.error("Address search result containers not found.");
        return;
    }

    if (!targetUserId) {
        addressListDiv.innerHTML = '<p class="text-danger">Please select or enter a Target User ID first to search for their addresses.</p>';
        resultsContainer.style.display = 'block';
        return;
    }

    addressListDiv.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Searching for addresses...</p>';
    resultsContainer.style.display = 'block';

    try {
        const addresses = await apiCall(`/api/users/${targetUserId}/addresses`, 'GET', null, true); 
        
        if (!addresses || addresses.length === 0) {
            addressListDiv.innerHTML = '<p class="text-muted">No addresses found for this user.</p>';
            return;
        }

        let addressesHTML = '<ul class="demo-result-list">';
        addresses.forEach(addr => {
            const isDefaultBadge = addr.is_default ? '<span class="default-badge">Default</span>' : '';
            addressesHTML += `
                <li class="demo-card-item">
                    <div class="demo-card-info">
                        <strong>${addr.street}</strong>, ${addr.city} ${isDefaultBadge}<br>
                        <small>${addr.country}, ${addr.zip_code}</small><br>
                        <small>ID: <code>${addr.address_id.substring(0,8)}...</code></small>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-warning select-address-btn"
                            data-address-id="${addr.address_id}">Use This Address</button>
                </li>`;
        });
        addressesHTML += '</ul>';
        addressListDiv.innerHTML = addressesHTML;

        document.querySelectorAll('.select-address-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const selectedAddressId = this.getAttribute('data-address-id');
                const targetAddressIdInputEl = document.getElementById('target-address-id');
                if (targetAddressIdInputEl) {
                    targetAddressIdInputEl.value = selectedAddressId;
                }
                displayGlobalMessage(`Target Address ID set to: ${selectedAddressId.substring(0,8)}...`, 'info');
                
                document.querySelectorAll('#address-list .demo-card-item.selected').forEach(item => item.classList.remove('selected'));
                this.closest('.demo-card-item').classList.add('selected');
            });
        });

    } catch (error) {
        addressListDiv.innerHTML = `<p class="text-danger">Error loading addresses: ${error.message}</p>`;
        console.error("Error in searchAddressesForBola:", error);
    }
}


function initOrdersPage() {
    console.log('Initializing Orders Page');
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }
    
    const bolaTargetUserIdFromStorage = sessionStorage.getItem('view_orders_for_user_id');
    const bolaTargetUsernameFromStorage = sessionStorage.getItem('view_orders_for_username');

    let viewingUserIdInput = document.getElementById('viewing-user-id-orders');
    if (!viewingUserIdInput) {
        viewingUserIdInput = document.createElement('input');
        viewingUserIdInput.type = 'hidden';
        viewingUserIdInput.id = 'viewing-user-id-orders';
        const demoSection = document.getElementById('view-orders-form'); 
        if (demoSection) demoSection.appendChild(viewingUserIdInput);
        else document.body.appendChild(viewingUserIdInput);
    }

    viewingUserIdInput.value = bolaTargetUserIdFromStorage || currentUser.user_id;
    
    const targetUserIdFieldOnPage = document.getElementById('target-user-id');
    const detailUserIdInput = document.getElementById('detail-user-id');
    const selectedViewSpan = document.getElementById('selected-target-view-orders');
    const selectedDetailSpan = document.getElementById('selected-target-order-detail');
    if (targetUserIdFieldOnPage && bolaTargetUserIdFromStorage) {
        targetUserIdFieldOnPage.value = bolaTargetUserIdFromStorage;
        if (selectedViewSpan) {
            const dName = bolaTargetUsernameFromStorage || bolaTargetUserIdFromStorage.substring(0,8)+"...";
            selectedViewSpan.textContent = `(Selected: ${dName})`;
        }
    }
    if (detailUserIdInput && bolaTargetUserIdFromStorage) {
        detailUserIdInput.value = bolaTargetUserIdFromStorage;
        if (selectedDetailSpan) {
            const dName = bolaTargetUsernameFromStorage || bolaTargetUserIdFromStorage.substring(0,8)+"...";
            selectedDetailSpan.textContent = `(Selected: ${dName})`;
        }
    }

    fetchAndDisplayOrders(); 

    if (bolaTargetUserIdFromStorage && bolaTargetUserIdFromStorage !== currentUser.user_id) {
        const displayUsername = bolaTargetUsernameFromStorage || `User ID ${bolaTargetUserIdFromStorage.substring(0,8)}...`;
        displayGlobalMessage(`BOLA Context: Displaying orders for ${displayUsername}.`, 'warning', 7000);
    }
    
    // Clear immediately after use for this page load only
    sessionStorage.removeItem('view_orders_for_user_id');
    sessionStorage.removeItem('view_orders_for_username');

    const viewOrdersForm = document.getElementById('view-orders-form');
    const returnButton = document.getElementById('return-to-own-orders');

    if (viewOrdersForm && targetUserIdFieldOnPage && viewingUserIdInput) {
        viewOrdersForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const targetId = targetUserIdFieldOnPage.value.trim();
            if (targetId) {
                viewingUserIdInput.value = targetId; 
                fetchAndDisplayOrders();
            } else {
                displayGlobalMessage('Please enter a User ID to view their orders.', 'error');
            }
        });
    }
    if (returnButton && viewingUserIdInput && targetUserIdFieldOnPage) {
        returnButton.addEventListener('click', function() {
            viewingUserIdInput.value = currentUser.user_id;
            targetUserIdFieldOnPage.value = '';
            const currentViewingDiv = document.getElementById('current-viewing');
            if(currentViewingDiv) currentViewingDiv.style.display = 'none';
            fetchAndDisplayOrders();
            displayGlobalMessage('Returned to viewing your own orders.', 'info');
        });
    }

    // Delegated listener for selecting a user from the list
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.select-user-for-orders-bola-btn');
        if (!btn) return;
        e.preventDefault();
        e.stopPropagation();
        const selectedUserId = btn.dataset.userId;
        const selectedUsername = btn.dataset.username;
        if (targetUserIdFieldOnPage) targetUserIdFieldOnPage.value = selectedUserId;
        if (detailUserIdInput) detailUserIdInput.value = selectedUserId;
        if (selectedViewSpan) selectedViewSpan.textContent = `(Selected: ${selectedUsername})`;
        if (selectedDetailSpan) selectedDetailSpan.textContent = `(Selected: ${selectedUsername})`;
        const usersList = document.getElementById('users-list');
        if (usersList) {
            usersList.querySelectorAll('.selected-victim-item').forEach(item => item.classList.remove('selected-victim-item'));
            const li = btn.closest('li');
            if (li) li.classList.add('selected-victim-item');
        }
        displayGlobalMessage(`Target for BOLA order demos set to: ${selectedUsername} (ID: ${selectedUserId.substring(0,8)}...)`, 'info');
    });

    targetUserIdFieldOnPage?.addEventListener('input', function() {
        if (!this.value.trim() && selectedViewSpan) {
            selectedViewSpan.textContent = '';
            const usersList = document.getElementById('users-list');
            if (usersList) usersList.querySelectorAll('.selected-victim-item').forEach(item => item.classList.remove('selected-victim-item'));
        }
    });

    detailUserIdInput?.addEventListener('input', function() {
        if (!this.value.trim() && selectedDetailSpan) {
            selectedDetailSpan.textContent = '';
        }
    });

    document.getElementById('list-users-btn')?.addEventListener('click', listUsersForOrders);
    document.getElementById('order-detail-form')?.addEventListener('submit', fetchOrderDetail);
    updateUIVulnerabilityFeaturesDisplay(true);
}

function initAdminPage() {
    console.log('Initializing Admin Page');
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }
    setupAdminInterface();
    updateUIVulnerabilityFeaturesDisplay(true);
}

// Product handling functions
async function fetchAndDisplayProducts() {
    try {
        // Show loading skeletons
        const loadingIndicator = document.getElementById('loading-indicator');
        const productsContainer = document.getElementById('products-container');
        const noProductsMessage = document.getElementById('no-products-message');
        
        if (loadingIndicator) loadingIndicator.style.display = 'grid';
        if (productsContainer) productsContainer.style.display = 'none';
        if (noProductsMessage) noProductsMessage.style.display = 'none';
        
        const products = await apiCall('/api/products', 'GET', null, false);
        renderProducts(products);
    } catch (error) {
        displayError(`Failed to load products: ${error.message}`);
        const productsContainer = document.getElementById('products-container');
        if (productsContainer) productsContainer.innerHTML = '<p>Error loading products.</p>';
    } finally {
        // Hide loading skeletons
        const loadingIndicator = document.getElementById('loading-indicator');
        const productsContainer = document.getElementById('products-container');
        
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (productsContainer) productsContainer.style.display = 'grid';
    }
}

function renderProducts(products) {
    const productsContainer = document.getElementById('products-container');
    const noProductsMessage = document.getElementById('no-products-message');
    
    if (!productsContainer) {
        console.error('Products container not found.');
        return;
    }
    
    if (!products || products.length === 0) {
        productsContainer.style.display = 'none';
        if (noProductsMessage) noProductsMessage.style.display = 'block';
        return;
    }

    if (noProductsMessage) noProductsMessage.style.display = 'none';
    productsContainer.style.display = 'grid';
    
    let renderPromises = [];
    
    for (const product of products) {
        renderPromises.push((async () => {
            let stockInfo = { quantity: 0 };
            try {
                stockInfo = await apiCall(`/api/products/${product.product_id}/stock`, 'GET', null, false);
            } catch (error) {
                console.warn(`Failed to fetch stock for product ${product.product_id}: ${error.message}`);
            }
            
            const { webpPath, pngPath } = getImagePaths(product);
            
            // Determine stock status for styling
            let stockClass = 'out-of-stock';
            let stockText = '<span class="out-of-stock-text">Out of stock</span>';
            
            if (stockInfo.quantity > 10) {
                stockClass = 'in-stock';
                stockText = `<span class="in-stock-text">${stockInfo.quantity} in stock</span>`;
            } else if (stockInfo.quantity > 0) {
                stockClass = 'low-stock';
                stockText = `<span class="low-stock-text">Only ${stockInfo.quantity} left!</span>`;
            }
            
            // Format description to limit length
            const shortDescription = product.description 
                ? (product.description.length > 100 
                    ? product.description.substring(0, 97) + '...' 
                    : product.description)
                : 'No description available';
            
            return `
                <article class="product-card" data-product-id="${product.product_id}" data-testid="product-card">
                    <div class="product-card-image">
                        <a href="/products/${product.product_id}.html" class="image-container">
                            <picture>
                                <source srcset="${webpPath}" type="image/webp">
                                <source srcset="${pngPath}" type="image/png">
                                <img src="${pngPath}" alt="${product.name}" class="product-image" loading="lazy"
                                     onerror="this.onerror=null; this.src='/static/images/placeholder.png';">
                            </picture>
                            <div class="overlay-icons">
                                <span class="quick-view-icon" title="Quick View">🔍</span>
                            </div>
                        </a>
                    </div>
                    
                    <div class="product-card-content">
                        <a href="/products/${product.product_id}.html" class="product-title-link">
                            <h3 class="product-title">${product.name}</h3>
                        </a>
                        
                        <p class="description" title="${product.description || ''}">${shortDescription}</p>
                        
                        <div class="product-meta">
                            <div class="price-container">
                                <p class="price" data-testid="product-price">$${product.price.toFixed(2)}</p>
                            </div>
                            <p class="stock ${stockClass}" data-testid="product-stock">${stockText}</p>
                        </div>
                        
                        <button class="add-to-cart-btn ${stockInfo.quantity <= 0 ? 'disabled' : ''}" 
                            data-testid="add-to-cart-button"
                            data-product-id="${product.product_id}" 
                            data-product-name="${product.name}" 
                            data-product-price="${product.price}"
                            ${stockInfo.quantity <= 0 ? 'disabled' : ''}>
                            <svg class="cart-icon" viewBox="0 0 24 24" width="18" height="18">
                                <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49A1 1 0 0 0 20 4H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>
                            </svg>
                            Add to Cart
                            <span class="btn-feedback"></span>
                        </button>
                    </div>
                </article>
            `;
        })());
    }
    
    Promise.all(renderPromises).then(resolvedHtmlArray => {
        productsContainer.innerHTML = resolvedHtmlArray.join('');
        
        // Add event listeners to all Add to Cart buttons
        document.querySelectorAll('.add-to-cart-btn').forEach(button => {
            if (!button.disabled) {
                button.addEventListener('click', function(e) {
                    const productId = this.getAttribute('data-product-id');
                    const productName = this.getAttribute('data-product-name');
                    const productPrice = parseFloat(this.getAttribute('data-product-price'));
                    
                    // Add visual feedback
                    this.classList.add('clicked');
                    setTimeout(() => {
                        this.classList.remove('clicked');
                    }, 300);
                    
                    // Show ripple effect
                    const btnFeedback = this.querySelector('.btn-feedback');
                    if (btnFeedback) {
                        btnFeedback.style.left = (e.offsetX) + 'px';
                        btnFeedback.style.top = (e.offsetY) + 'px';
                        btnFeedback.classList.add('active');
                        setTimeout(() => {
                            btnFeedback.classList.remove('active');
                        }, 500);
                    }
                    
                    addToCart({ product_id: productId, name: productName, price: productPrice, quantity: 1 });
                });
            }
        });
    }).catch(error => {
        console.error("Error rendering products with stock:", error);
        productsContainer.innerHTML = "<p>Error displaying products.</p>";
    });
}


// Cart handling functions
function addToCart(item) {
    const existingItemIndex = cart.findIndex(cartItem => cartItem.product_id === item.product_id);
    if (existingItemIndex !== -1) {
        cart[existingItemIndex].quantity += item.quantity;
    } else {
        cart.push(item);
    }
    saveCart();
    displayGlobalMessage(`Added ${item.quantity} "${item.name}" to cart.`, 'success');
}

function updateCartItemQuantity(productId, newQuantity) {
    const itemIndex = cart.findIndex(item => item.product_id === productId);
    if (itemIndex !== -1) {
        if (newQuantity <= 0) {
            removeCartItem(productId);
        } else {
            cart[itemIndex].quantity = newQuantity;
            saveCart();
        }
    }
}

function removeCartItem(productId) {
    cart = cart.filter(item => item.product_id !== productId);
    saveCart();
}

function displayCart() {
    const cartContainer = document.getElementById('cart-items-container');
    const cartTotalElement = document.getElementById('cart-total');
    const cartSubtotalElement = document.getElementById('cart-subtotal');
    const cartShippingElement = document.getElementById('cart-shipping');
    const loadingElement = document.getElementById('cart-loading');
    
    if (!cartContainer) {
        console.error('Cart container not found.');
        return;
    }
    
    // Show loading state
    if (loadingElement) loadingElement.style.display = 'flex';
    
    // Short timeout to show loading state (simulates network delay)
    setTimeout(() => {
        if (loadingElement) loadingElement.style.display = 'none';
        
        if (cart.length === 0) {
            cartContainer.innerHTML = `
                <div class="empty-cart" data-testid="empty-cart">
                    <svg class="empty-cart-icon" viewBox="0 0 24 24" width="64" height="64">
                        <path d="M16.4 15c-0.7 0-1.2 0.5-1.2 1.2s0.5 1.2 1.2 1.2 1.2-0.5 1.2-1.2-0.6-1.2-1.2-1.2zM9 15c-0.7 0-1.2 0.5-1.2 1.2s0.5 1.2 1.2 1.2 1.2-0.5 1.2-1.2-0.6-1.2-1.2-1.2zM20 4h-2.4c-0.4-1.2-1.5-2-2.8-2h-5.6c-1.3 0-2.4 0.8-2.8 2h-2.4c-0.5 0-1 0.4-1 1s0.5 1 1 1h16c0.5 0 1-0.4 1-1s-0.5-1-1-1zM9.2 4c0.3-0.6 0.9-1 1.6-1h2.4c0.7 0 1.3 0.4 1.6 1h-5.6zM18.8 7h-13.6l1.3 7.3c0 1.8 0.8 4.7 4.5 4.7h2.2c3.5 0 4.5-2.7 4.5-4.7l1.1-7.3zM15.5 14.4c0 1.1-0.5 2.6-2.5 2.6h-2.2c-1.8 0-2.5-1.5-2.5-2.6l-1-5.4h9.1l-0.9 5.4z"></path>
                    </svg>
                    <p>Your cart is empty</p>
                    <a href="/" class="btn btn-primary">Start Shopping</a>
                </div>`;
            
            // Update total, subtotal, shipping
            if (cartTotalElement) cartTotalElement.textContent = '$0.00';
            if (cartSubtotalElement) cartSubtotalElement.textContent = '$0.00';
            if (cartShippingElement) cartShippingElement.textContent = '$0.00';
            
            // Hide checkout button
            const checkoutBtn = document.getElementById('checkout-btn');
            if (checkoutBtn) checkoutBtn.classList.add('disabled');
            
            return;
        }
        
        // Calculate cart totals
        let cartSubtotal = 0;
        cart.forEach(item => {
            cartSubtotal += item.price * item.quantity;
        });
        
        // Calculate shipping (free over $50)
        const shipping = cartSubtotal >= 50 ? 0 : 5;
        const cartTotal = cartSubtotal + shipping;
        
        // Update cart summary
        if (cartTotalElement) cartTotalElement.textContent = `$${cartTotal.toFixed(2)}`;
        if (cartSubtotalElement) cartSubtotalElement.textContent = `$${cartSubtotal.toFixed(2)}`;
        if (cartShippingElement) cartShippingElement.textContent = `$${shipping.toFixed(2)}`;
        
        // Enable checkout button
        const checkoutBtn = document.getElementById('checkout-btn');
        if (checkoutBtn) checkoutBtn.classList.remove('disabled');
        
        // Build cart items HTML
        let cartItemsHTML = `
            <div class="cart-items" data-testid="cart-items">
                <table class="cart-table" id="cart-table">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Price</th>
                            <th>Quantity</th>
                            <th>Total</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>`;
        
        cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            const { webpPath, pngPath } = getImagePaths({ name: item.name, product_id: item.product_id });
            
            cartItemsHTML += `
                <tr class="cart-item" data-product-id="${item.product_id}" data-testid="cart-item">
                    <td class="product-info">
                        <div class="cart-product">
                            <div class="cart-product-image">
                                <picture>
                                    <source srcset="${webpPath}" type="image/webp">
                                    <source srcset="${pngPath}" type="image/png">
                                    <img src="${pngPath}" alt="${item.name}"
                                         onerror="this.onerror=null; this.src='/static/images/placeholder.png';">
                                </picture>
                            </div>
                            <div class="cart-product-details">
                                <h4>${item.name}</h4>
                                <p class="cart-product-id">ID: ${item.product_id.substring(0,8)}...</p>
                            </div>
                        </div>
                    </td>
                    <td class="product-price" data-testid="product-price">$${item.price.toFixed(2)}</td>
                    <td class="product-quantity">
                        <div class="cart-quantity-control">
                            <button type="button" class="quantity-btn decrease" data-testid="decrease-quantity" aria-label="Decrease quantity">
                                <svg viewBox="0 0 24 24" width="16" height="16">
                                    <path d="M19 13H5v-2h14v2z" fill="currentColor"></path>
                                </svg>
                            </button>
                            <input type="number" class="quantity-input cart-quantity" data-testid="cart-quantity" 
                                   value="${item.quantity}" min="1" max="99">
                            <button type="button" class="quantity-btn increase" data-testid="increase-quantity" aria-label="Increase quantity">
                                <svg viewBox="0 0 24 24" width="16" height="16">
                                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"></path>
                                </svg>
                            </button>
                        </div>
                    </td>
                    <td class="product-total" data-testid="product-total">$${itemTotal.toFixed(2)}</td>
                    <td class="product-actions">
                        <button type="button" class="remove-item-btn" data-testid="remove-item">
                            <svg viewBox="0 0 24 24" width="16" height="16">
                                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" fill="currentColor"></path>
                            </svg>
                            Remove
                        </button>
                    </td>
                </tr>`;
        });
        
        cartItemsHTML += `
                    </tbody>
                </table>
            </div>`;
            
        cartContainer.innerHTML = cartItemsHTML;
        
        // Setup event listeners for cart actions
        setupCartEventListeners();
    }, 300); // Small timeout to show loading state
}

function setupCartEventListeners() {
    // Quantity change event listeners
    document.querySelectorAll('.cart-quantity').forEach(input => {
        input.addEventListener('change', function() {
            const newQuantity = parseInt(this.value);
            if (isNaN(newQuantity) || newQuantity < 1) {
                this.value = 1;
                return;
            }
            
            const productId = this.closest('tr').dataset.productId;
            updateCartItemQuantity(productId, newQuantity);
            
            // Visual feedback
            const row = this.closest('tr');
            row.classList.add('updating');
            setTimeout(() => {
                row.classList.remove('updating');
                displayCart();
            }, 300);
        });
    });
    
    // Decrease quantity buttons
    document.querySelectorAll('.quantity-btn.decrease').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('.quantity-input');
            let val = parseInt(input.value) - 1;
            if (val < 1) val = 1;
            input.value = val;
            
            const productId = this.closest('tr').dataset.productId;
            updateCartItemQuantity(productId, val);
            
            // Visual feedback
            const row = this.closest('tr');
            row.classList.add('updating');
            setTimeout(() => {
                row.classList.remove('updating');
                displayCart();
            }, 300);
        });
    });
    
    // Increase quantity buttons
    document.querySelectorAll('.quantity-btn.increase').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('.quantity-input');
            const newVal = parseInt(input.value) + 1;
            input.value = newVal;
            
            const productId = this.closest('tr').dataset.productId;
            updateCartItemQuantity(productId, newVal);
            
            // Visual feedback
            const row = this.closest('tr');
            row.classList.add('updating');
            setTimeout(() => {
                row.classList.remove('updating');
                displayCart();
            }, 300);
        });
    });
    
    // Remove item buttons
    document.querySelectorAll('.remove-item-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const row = this.closest('tr');
            const productId = row.dataset.productId;
            const productName = row.querySelector('.cart-product-details h4').textContent;
            
            // Visual feedback before removal
            row.classList.add('removing');
            
            // Confirmation dialog
            if (confirm(`Remove ${productName} from cart?`)) {
                setTimeout(() => {
                    removeCartItem(productId);
                    displayCart();
                }, 300);
            } else {
                setTimeout(() => {
                    row.classList.remove('removing');
                }, 300);
            }
        });
    });
}

async function fetchAndDisplayProductDetail(productId) {
    console.log(`[main.js] fetchAndDisplayProductDetail called for productId: '${productId}'`);
    const loadingIndicator = document.getElementById('product-loading');
    const productDetailContainer = document.getElementById('product-detail-container');
    const errorContainerOnPage = document.getElementById('error-message-container'); 

    if (!productDetailContainer) {
        console.error('[main.js] CRITICAL: Product detail container (ID: "product-detail-container") not found.');
        return;
    }
    if (errorContainerOnPage) errorContainerOnPage.style.display = 'none'; 

    try {
        if (loadingIndicator) loadingIndicator.style.display = 'flex';
        productDetailContainer.style.display = 'none';
        productDetailContainer.innerHTML = ''; 

        if (typeof apiCall !== 'function') {
            console.error("[main.js] CRITICAL: apiCall function is not defined!");
            throw new Error("API call function is missing, cannot fetch product data.");
        }
        
        console.log(`[main.js] Fetching product data for ID: ${productId} from /api/products/${productId}`);
        const product = await apiCall(`/api/products/${productId}`, 'GET', null, false);
        
        let stockInfo = { quantity: 0, last_updated: new Date().toISOString() }; 
        try {
            console.log(`[main.js] Fetching stock data for ID: ${productId} from /api/products/${productId}/stock`);
            stockInfo = await apiCall(`/api/products/${productId}/stock`, 'GET', null, false);
        } catch (stockError) {
            console.warn(`[main.js] Could not fetch stock info for product ${productId}:`, stockError.message, "Using default stock (0).");
        }

        console.log("[main.js] Product data received:", product);
        console.log("[main.js] Stock data received:", stockInfo);

        document.title = `${product.name || 'Product Details'} - Radware Demo E-Commerce`;
        const breadcrumbCurrentPage = document.querySelector('.breadcrumb .current-page');
        if (breadcrumbCurrentPage) breadcrumbCurrentPage.textContent = product.name || 'Product';

        let stockBadgeClass = 'badge-danger';
        let stockText = 'Out of stock';
        if (stockInfo.quantity > 10) {
            stockBadgeClass = 'badge-success';
            stockText = `${stockInfo.quantity} in stock`;
        } else if (stockInfo.quantity > 0) {
            stockBadgeClass = 'badge-warning';
            stockText = `Only ${stockInfo.quantity} left!`;
        }

        const imageFilename = (typeof getProductImageFilename === 'function') ? getProductImageFilename(product) : 'placeholder.png';
        const { webpPath, pngPath } = getImagePaths(product);
        console.log(`[main.js] Determined image path: ${pngPath}`);

        productDetailContainer.innerHTML = `
            <div class="product-detail-layout">
                <div class="product-detail-images">
                    <div class="main-image-container">
                        <picture>
                            <source srcset="${webpPath}" type="image/webp">
                            <source srcset="${pngPath}" type="image/png">
                            <img src="${pngPath}" alt="${product.name || 'Product Image'}" id="product-image-detail" class="main-product-image"
                                 onerror="this.onerror=null; this.src='/static/images/placeholder.png'; console.error('Failed to load product image: ${pngPath}');">
                        </picture>
                    </div>
                </div>
                <div class="product-detail-info">
                    <h1 id="product-name-detail" data-testid="product-title">${product.name || 'N/A'}${product.is_protected ? ' <span class="protected-indicator" title="This item is protected for core demo stability. Destructive actions are limited.">🛡️ Protected</span>' : ''}</h1>
                    <div class="product-meta">
                        <span class="product-category">${product.category || 'Uncategorized'}</span>
                        <div class="product-status-tags">
                            <span class="stock-badge ${stockBadgeClass}" data-testid="stock-badge">${stockText}</span>
                            ${product.internal_status ? `<span class="internal-status-badge" data-testid="internal-status-badge">${product.internal_status}</span>` : ''}
                        </div>
                    </div>
                    <div class="product-price-container">
                        <p class="product-price" id="product-price-detail" data-testid="product-price">$${(product.price || 0).toFixed(2)}</p>
                    </div>
                    <div class="product-description-container">
                        <h3>Description</h3>
                        <p class="product-description" id="product-description-detail" data-testid="product-description">
                            ${product.description || 'No description available for this product.'}
                        </p>
                    </div>
                    <div class="product-actions">
                        <form id="add-to-cart-form" class="add-to-cart-form" data-testid="add-to-cart-form">
                            <div class="quantity-selector">
                                <label for="quantity-detail">Quantity:</label>
                                <div class="quantity-control">
                                    <button type="button" class="quantity-btn decrease" data-testid="decrease-quantity" aria-label="Decrease quantity">
                                        <svg viewBox="0 0 24 24" width="16" height="16"><path d="M19 13H5v-2h14v2z" fill="currentColor"></path></svg>
                                    </button>
                                    <input type="number" id="quantity-detail" class="quantity-input" data-testid="quantity-input" 
                                        value="1" min="1" max="${stockInfo.quantity || 0}" ${stockInfo.quantity <= 0 ? 'disabled' : ''}>
                                    <button type="button" class="quantity-btn increase" data-testid="increase-quantity" aria-label="Increase quantity">
                                        <svg viewBox="0 0 24 24" width="16" height="16"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"></path></svg>
                                    </button>
                                </div>
                            </div>
                            <button type="submit" id="add-to-cart-btn-detail" class="add-to-cart-btn ${stockInfo.quantity <= 0 ? 'disabled' : ''}"
                                data-testid="add-to-cart-button"
                                data-product-id="${product.product_id}" 
                                data-product-name="${product.name || 'Product'}" 
                                data-product-price="${product.price || 0}"
                                ${stockInfo.quantity <= 0 ? 'disabled' : ''}>
                                <svg class="cart-icon" viewBox="0 0 24 24" width="20" height="20"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49A1 1 0 0 0 20 4H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/></svg>
                                ${stockInfo.quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
                                <span class="btn-feedback"></span>
                            </button>
                        </form>
                    </div>
                    <div class="extra-info">
                        <div class="accordion">
                            <div class="accordion-item">
                                <button class="accordion-header" id="shipping-header" aria-expanded="false" aria-controls="shipping-content">
                                    Shipping Information <span class="accordion-icon">+</span>
                                </button>
                                <div class="accordion-content" id="shipping-content">
                                    <p>Free shipping on orders over $50. Standard delivery 3-5 business days.</p>
                                </div>
                            </div>
                            <div class="accordion-item">
                                <button class="accordion-header" id="returns-header" aria-expanded="false" aria-controls="returns-content">
                                    Returns & Warranty <span class="accordion-icon">+</span>
                                </button>
                                <div class="accordion-content" id="returns-content">
                                    <p>30-day money-back guarantee. 1-year limited warranty on all products.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        if (loadingIndicator) loadingIndicator.style.display = 'none';
        productDetailContainer.style.display = 'block';
        console.log("[main.js] Product details rendered.");

        const quantityInput = document.getElementById('quantity-detail');
        const decreaseBtn = productDetailContainer.querySelector('.quantity-btn.decrease');
        const increaseBtn = productDetailContainer.querySelector('.quantity-btn.increase');
        
        if (quantityInput && decreaseBtn) {
            decreaseBtn.addEventListener('click', () => {
                let currentValue = parseInt(quantityInput.value);
                if (currentValue > 1) {
                    quantityInput.value = currentValue - 1;
                }
            });
        } else { console.warn("[main.js] Decrease quantity button or input not found after render."); }
        
        if (quantityInput && increaseBtn) {
            increaseBtn.addEventListener('click', () => {
                const maxQuantity = parseInt(quantityInput.max);
                let currentValue = parseInt(quantityInput.value);
                if (currentValue < maxQuantity) {
                    quantityInput.value = currentValue + 1;
                }
            });
        } else { console.warn("[main.js] Increase quantity button or input not found after render."); }
        
        const addToCartForm = document.getElementById('add-to-cart-form');
        if (addToCartForm) {
            addToCartForm.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log("[main.js] Add to cart form submitted.");
                const btn = document.getElementById('add-to-cart-btn-detail');
                if (!btn || btn.disabled) {
                    console.warn("[main.js] Add to cart button is disabled or not found.");
                    return;
                }

                const currentProductId = btn.dataset.productId;
                const currentProductName = btn.dataset.productName;
                const currentProductPrice = parseFloat(btn.dataset.productPrice);
                const quantity = parseInt(document.getElementById('quantity-detail').value);
                
                if (quantity > 0 && quantity <= (stockInfo.quantity || 0)) {
                    btn.classList.add('clicked');
                    setTimeout(() => btn.classList.remove('clicked'), 300);
                    
                    const feedbackEl = btn.querySelector('.btn-feedback');
                    if(feedbackEl){
                        feedbackEl.style.left = (e.offsetX || 0) + 'px'; 
                        feedbackEl.style.top = (e.offsetY || 0) + 'px'; 
                        feedbackEl.classList.add('active');
                        setTimeout(() => feedbackEl.classList.remove('active'), 500);
                    }

                    if (typeof addToCart === 'function') {
                        addToCart({ 
                            product_id: currentProductId, 
                            name: currentProductName, 
                            price: currentProductPrice, 
                            quantity: quantity 
                        });
                    } else {
                        console.error("[main.js] CRITICAL: addToCart function is not defined.");
                    }
                } else { 
                    const msg = 'Invalid quantity or product is out of stock.';
                    if (typeof displayGlobalMessage === 'function') displayGlobalMessage(msg, 'error');
                    else console.error(msg);
                }
            });
            console.log("[main.js] Add to cart form event listener attached.");
        } else { console.error("[main.js] CRITICAL: Add to cart form not found after render."); }
        
        document.querySelectorAll('.accordion-header').forEach(header => {
            header.addEventListener('click', function() {
                const content = this.nextElementSibling;
                const icon = this.querySelector('.accordion-icon');
                const isExpanded = this.getAttribute('aria-expanded') === 'true';

                this.setAttribute('aria-expanded', String(!isExpanded));
                this.classList.toggle('active', !isExpanded);
                if (icon) icon.textContent = isExpanded ? '+' : '-';
                
                if (content) { 
                    if (!isExpanded) { 
                        content.style.padding = "15px";
                        content.style.maxHeight = Math.round(content.scrollHeight * 1.67) + "px"; // 54 * 1.67 ≈ 90
                    } else { 
                        content.style.maxHeight = null;
                        setTimeout(() => { content.style.padding = "0 15px"; }, 300); 
                    }
                } else {
                    console.warn("[main.js] Accordion content not found for header:", this.id);
                }
            });
        });
        console.log("[main.js] Accordion event listeners attached.");

    } catch (error) {
        console.error("[main.js] Overall error in fetchAndDisplayProductDetail:", error);
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        productDetailContainer.style.display = 'block';
        const errorMsgHtml = `
            <div class="error-state">
                <svg class="error-icon" viewBox="0 0 24 24" width="48" height="48"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                <p>Sorry, we couldn't load the product details.</p>
                <p><small>Error: ${error.message || 'The product might not exist or there was a network issue.'}</small></p>
                <a href="/" class="btn btn-primary retry-btn">Back to Home</a>
            </div>`;
        productDetailContainer.innerHTML = errorMsgHtml;
        
        if (typeof displayGlobalMessage === 'function') {
            displayGlobalMessage(`Error loading product: ${error.message || 'Product not found or API error.'}`, 'error');
        }
    }
}


// Authentication Functions
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    if (!username || !password) { displayError('Enter username and password.'); return; }
    
    try {
        const loginEndpoint = `/api/auth/login?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;
        const response = await apiCall(loginEndpoint, 'POST', null, false);
        authToken = response.access_token;
        localStorage.setItem('token', authToken);
        
        const tokenParts = authToken.split('.');
        if (tokenParts.length === 3) {
            const tokenPayload = JSON.parse(atob(tokenParts[1]));
            if (tokenPayload && tokenPayload.user_id) {
                const userProfile = await apiCall(`/api/users/${tokenPayload.user_id}`, 'GET', null, true);
                localStorage.setItem('user', JSON.stringify(userProfile));
                currentUser = userProfile;
            }
        }
        updateNavbar();
        displaySuccess('Login successful! Redirecting...');
        setTimeout(() => { window.location.href = '/'; }, 1500);
    } catch (error) { displayError(`Login failed: ${error.message}`); }
}

async function handleRegistration(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    if (!username || !email || !password || !confirmPassword) { displayError('Fill all fields.'); return; }
    if (password !== confirmPassword) { displayError('Passwords do not match.'); return; }
    
    try {
        const registerEndpoint = `/api/auth/register?username=${encodeURIComponent(username)}&email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
        await apiCall(registerEndpoint, 'POST', null, false);
        displaySuccess('Registration successful! Please log in.');
        setTimeout(() => { window.location.href = '/login'; }, 1500);
    } catch (error) { displayError(`Registration failed: ${error.message}`); }
}

async function fetchAndDisplayOrders() {
    if (!currentUser) { window.location.href = '/login'; return; }
    
    const ordersContainer = document.getElementById('orders-container');
    if (!ordersContainer) { console.error('Orders container not found.'); return; }
    ordersContainer.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading orders...</div>';
    
    const currentViewingDiv = document.getElementById('current-viewing');
    const viewingUsernameSpan = document.getElementById('viewing-username-display'); 
    const viewingUserIdCode = document.getElementById('viewing-user-id-display-code');

    try {
        const userIdToFetch = document.getElementById('viewing-user-id-orders')?.value || currentUser.user_id;
        const orders = await apiCall(`/api/users/${userIdToFetch}/orders`, 'GET', null, true);
        
        // Ensure renderOrders is defined and handles the `orders` array
        if (typeof renderOrders === 'function') {
            renderOrders(orders, ordersContainer); 
        } else {
            console.error('renderOrders function is not defined.');
            ordersContainer.innerHTML = '<p class="text-danger">Error: UI rendering function is missing.</p>';
        }


        if (userIdToFetch !== currentUser.user_id) {
            let fetchedTargetUsername = "Target User"; 
            try {
                const targetUser = await apiCall(`/api/users/${userIdToFetch}`, 'GET', null, true);
                if (targetUser && targetUser.username) fetchedTargetUsername = targetUser.username;
            } catch (e) { console.warn("Could not fetch target username for display on orders page", e); }

            if (currentViewingDiv && viewingUsernameSpan && viewingUserIdCode) {
                viewingUsernameSpan.textContent = fetchedTargetUsername;
                viewingUserIdCode.textContent = userIdToFetch.substring(0,8)+"...";
                currentViewingDiv.style.display = 'flex'; 
            }
        } else {
            if (currentViewingDiv) currentViewingDiv.style.display = 'none';
        }

    } catch (error) {
        ordersContainer.innerHTML = ''; 
        displayGlobalMessage(`Failed to load orders: ${error.message}`, 'error');
         if (currentViewingDiv) currentViewingDiv.style.display = 'none';
    }
}

function renderOrders(orders, container) {
    orders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)); // Sort orders: newest first
    if (!orders || orders.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-receipt"></i><p>No orders found.</p></div>';
        return;
    }
    let ordersHTML = `
        <table class="orders-table table table-striped table-hover">
            <thead class="thead-light">
                <tr>
                    <th>Order ID</th>
                    <th>Date &amp; Time</th>
                    <th>Status</th>
                    <th class="text-right">Total</th>
                    <th class="text-center">Card Used</th>
                    <th class="text-center">Items</th>
                </tr>
            </thead>
            <tbody>`;
    orders.forEach(order => {
        const orderDateTime = order.created_at ? new Date(order.created_at) : null;
        const formattedDateTime = orderDateTime ? `${orderDateTime.toLocaleDateString()} ${orderDateTime.toLocaleTimeString()}` : 'N/A';
        let totalAmount = order.total_amount || 0;
        if(order.items && order.items.length > 0 && totalAmount === 0) { // Recalculate if needed
            totalAmount = order.items.reduce((sum, item) => sum + (item.price_at_purchase * item.quantity), 0);
        }
        const itemCount = order.items ? order.items.length : 0;
        const cardLastFour = order.credit_card_last_four ? `\u2022\u2022\u2022\u2022 ${order.credit_card_last_four}` : 'N/A';

        ordersHTML += `
            <tr data-order-id="${order.order_id}">
                <td><code>${order.order_id.substring(0,8)}...</code></td>
                <td>${formattedDateTime}</td>
                <td><span class="badge badge-info order-status ${order.status.toLowerCase()}">${order.status}</span></td>
                <td class="text-right">$${totalAmount.toFixed(2)}</td>
                <td class="text-center">${cardLastFour}</td>
                <td class="text-center">${itemCount}</td>
            </tr>`;
    });
    ordersHTML += `</tbody></table>`;
    container.innerHTML = ordersHTML;
}

async function listUsersForOrders() {
    const listEl = document.getElementById('users-list');
    if (!listEl) return;
    listEl.innerHTML = '<li class="list-group-item">Loading users...</li>';
    try {
        const users = await apiCall('/api/users', 'GET');
        listEl.innerHTML = '';
        users.forEach(u => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.innerHTML = `<span>${u.username} (ID: <code>${u.user_id}</code>)</span>`;
            if (!currentUser || u.user_id !== currentUser.user_id) {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'btn btn-sm btn-outline-primary select-user-for-orders-bola-btn';
                btn.dataset.userId = u.user_id;
                btn.dataset.username = u.username;
                btn.textContent = 'Select';
                li.appendChild(btn);
            }
            listEl.appendChild(li);
        });
    } catch (error) {
        listEl.innerHTML = '';
        displayGlobalMessage(`Failed to list users: ${error.message}`, 'error');
    }
}

async function fetchOrderDetail(event) {
    event.preventDefault();
    const userId = document.getElementById('detail-user-id')?.value.trim();
    const orderId = document.getElementById('detail-order-id')?.value.trim();
    const result = document.getElementById('order-detail-result');
    if (!userId || !orderId) {
        displayGlobalMessage('Both User ID and Order ID are required.', 'error');
        return;
    }
    if (result) result.innerHTML = '<p class="loading-indicator">Loading...</p>';
    try {
        const order = await apiCall(`/api/users/${userId}/orders/${orderId}`, 'GET');
        if (!result) return;
        let html = `<h4>Order ${order.order_id.substring(0,8)}...</h4>`;
        html += `<p>Status: ${order.status}</p>`;
        if (order.items && order.items.length > 0) {
            html += '<ul>';
            order.items.forEach(it => {
                const name = it.product_name || it.product_id.substring(0,8);
                html += `<li>${it.quantity} x ${name}</li>`;
            });
            html += '</ul>';
        }
        result.innerHTML = html;
    } catch (error) {
        if (result) result.innerHTML = '';
        displayGlobalMessage(`Failed to fetch order: ${error.message}`, 'error');
    }
}

// Profile page functions
async function fetchAndDisplayUserProfile() {
    if (!currentUser) { window.location.href = '/login'; return; }

    const profileContainer = document.getElementById('profile-container');
    const addressesContainer = document.getElementById('addresses-container');
    const creditCardsContainer = document.getElementById('creditcards-container');

    if (!profileContainer || !addressesContainer || !creditCardsContainer) {
        console.error('Profile page containers not found.'); return;
    }

    profileContainer.innerHTML = '<div class="loading-indicator">Loading profile...</div>';
    addressesContainer.innerHTML = '<div class="loading-indicator">Loading addresses...</div>'; 
    creditCardsContainer.innerHTML = '<div class="loading-indicator">Loading cards...</div>';

    try {
        const userIdToFetch = document.getElementById('viewing-user-id')?.value || currentUser.user_id;
        const userProfile = await apiCall(`/api/users/${userIdToFetch}`, 'GET', null, true);
        const addresses = await apiCall(`/api/users/${userIdToFetch}/addresses`, 'GET', null, true);
        const cards = await apiCall(`/api/users/${userIdToFetch}/credit-cards`, 'GET', null, true);

        let profileHTML = `
            <h2>User Information</h2>
            <p><strong>Username:</strong> ${userProfile.username}</p>
            <p><strong>Email:</strong> <span id="display-email">${userProfile.email}</span></p>
            <button id="edit-email-btn" class="btn btn-sm btn-primary">Edit Email</button>
            <div id="edit-email-form" style="display:none;margin-top:8px;" class="inline-edit-form">
                <input type="email" id="edit-email-input" class="form-control" value="${userProfile.email}">
                <div style="margin-top:6px;">
                    <button type="button" id="save-email-btn" class="btn btn-sm btn-primary">Save</button>
                    <button type="button" id="cancel-email-btn" class="btn btn-sm btn-secondary">Cancel</button>
                </div>
            </div>
            <button id="admin-escalate-btn" class="btn btn-danger" style="margin-top:10px;">Try to Make ${userProfile.username} Admin</button>`;
        profileContainer.innerHTML = profileHTML;
        
        const bolaBanner = document.getElementById('bola-demo-banner');
        const viewProfileBtn = document.getElementById('view-profile-btn');
        const returnToProfileBtn = document.getElementById('return-to-profile-btn');

        if (userIdToFetch !== currentUser.user_id) {
            if (bolaBanner) {
                bolaBanner.style.display = 'block';
                bolaBanner.innerHTML = `<strong>⚠️ Viewing ${userProfile.username}'s Profile (BOLA DEMO)!</strong>`;
            }
            if(viewProfileBtn) viewProfileBtn.style.display = 'none';
            if(returnToProfileBtn) returnToProfileBtn.style.display = 'inline-block';
        } else {
            if (bolaBanner) bolaBanner.style.display = 'none';
            if(viewProfileBtn) viewProfileBtn.style.display = 'inline-block';
            if(returnToProfileBtn) returnToProfileBtn.style.display = 'none';
        }

        // Email edit interactions
        const editBtn = document.getElementById('edit-email-btn');
        const editForm = document.getElementById('edit-email-form');
        const saveBtn = document.getElementById('save-email-btn');
        const cancelBtn = document.getElementById('cancel-email-btn');

        if (editBtn && editForm && saveBtn && cancelBtn) {
            editBtn.addEventListener('click', () => {
                editForm.style.display = 'block';
                document.getElementById('edit-email-input').focus();
            });
            cancelBtn.addEventListener('click', () => {
                editForm.style.display = 'none';
            });
            saveBtn.addEventListener('click', async () => {
                const newEmail = document.getElementById('edit-email-input').value.trim();
                if (!newEmail) { displayError('Please enter an email.'); return; }
                try {
                    await apiCall(`/api/users/${userIdToFetch}?email=${encodeURIComponent(newEmail)}`, 'PUT', null, true);
                    displaySuccess('Email updated successfully!');
                    if (userIdToFetch === currentUser.user_id) {
                        currentUser.email = newEmail;
                        localStorage.setItem('user', JSON.stringify(currentUser));
                        updateNavbar();
                    }
                    fetchAndDisplayUserProfile();
                } catch (err) {
                    displayError(`Failed to update email: ${err.message}`);
                }
            });
        }

        const adminBtn = document.getElementById('admin-escalate-btn');
        if (adminBtn) {
            adminBtn.addEventListener('click', async () => {
                try {
                    await apiCall(`/api/users/${userIdToFetch}?is_admin=true`, 'PUT', null, true);
                    displaySuccess(`Exploit sent! Check if ${userProfile.username} is now admin.`);
                    fetchAndDisplayUserProfile();
                } catch (err) {
                    displayError(`Admin escalation failed: ${err.message}`);
                }
            });
        }
        
        document.getElementById('add-address-form').removeAttribute('data-editing-id');
        const addressSubmitBtn = document.getElementById('add-address-form-submit-btn');
        if (addressSubmitBtn) addressSubmitBtn.textContent = 'Add Address';
        
        document.getElementById('add-creditcard-form').removeAttribute('data-editing-id');
        const cardSubmitBtn = document.getElementById('add-creditcard-form-submit-btn');
        if (cardSubmitBtn) cardSubmitBtn.textContent = 'Add Credit Card';

        let addressesHTML = '';
        if (addresses && addresses.length > 0) {
            addresses.forEach(addr => {
                addressesHTML += `
                    <div class="address-card item-card" id="address-${addr.address_id.substring(0,8)}">
                        <div class="item-card-header">
                            <i class="fas fa-map-marker-alt"></i>
                            <h4>${addr.street} 
                                ${addr.is_default ? 
                                    '<span class="item-badge badge-primary">Default</span>' : 
                                    '<button class="btn-xs set-default-btn" data-address-id="' + addr.address_id + '">Set Default</button>'}
                            </h4>
                        </div>
                        <div class="item-card-content">
                            <p><i class="fas fa-city"></i> ${addr.city}, ${addr.country}</p>
                            <p><i class="fas fa-mail-bulk"></i> ${addr.zip_code}</p>
                            <p class="text-muted"><small>ID: ${addr.address_id.substring(0,8)}...</small></p>
                        </div>
                        <div class="item-actions">
                            <button class="btn-sm btn-secondary edit-address-btn" data-address-id="${addr.address_id}">
                                <i class="fas fa-pen"></i> Edit
                            </button>
                            <button class="btn-sm btn-danger delete-address-btn" data-address-id="${addr.address_id}">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>`;
            });
        } else { 
            addressesHTML = `
                <div class="empty-state">
                    <i class="fas fa-map-marker-alt"></i>
                    <p>No addresses found. Add your first address to get started.</p>
                </div>`;
        }
        addressesContainer.innerHTML = addressesHTML;

        let cardsHTML = '';
        if (cards && cards.length > 0) {
            cards.forEach(card => {
                cardsHTML += `
                    <div class="credit-card-card item-card" id="card-${card.card_id.substring(0,8)}">
                        <div class="item-card-header">
                            <i class="fas fa-credit-card"></i>
                            <h4>${card.cardholder_name} 
                                ${card.is_default ? 
                                    '<span class="item-badge badge-primary">Default</span>' : 
                                    '<button class="btn-xs set-default-btn" data-card-id="' + card.card_id + '">Set Default</button>'}
                            </h4>
                        </div>
                        <div class="item-card-content">
                            <p><span class="card-detail-text">Number:</span> •••• •••• •••• ${card.card_last_four}</p>
                            <p><span class="card-detail-text">Expires:</span> ${card.expiry_month}/${card.expiry_year.substring(2)}</p>
                            <p class="text-muted"><small>ID: ${card.card_id.substring(0,8)}...</small></p>
                        </div>
                        <div class="item-actions">
                            <button class="btn-sm btn-secondary edit-card-btn" data-card-id="${card.card_id}">
                                <i class="fas fa-pen"></i> Edit
                            </button>
                            <button class="btn-sm btn-danger delete-card-btn" data-card-id="${card.card_id}">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>`;
            });
        } else { 
            cardsHTML = `
                <div class="empty-state">
                    <i class="fas fa-credit-card"></i>
                    <p>No credit cards found. Add your first card to get started.</p>
                </div>`;
        }
        creditCardsContainer.innerHTML = cardsHTML;

        document.querySelectorAll('.edit-address-btn').forEach(btn => {
            btn.addEventListener('click', () => populateAddressFormForEdit(btn.dataset.addressId, addresses));
        });
        document.querySelectorAll('.delete-address-btn').forEach(btn => {
            btn.addEventListener('click', () => handleDeleteAddress(btn.dataset.addressId));
        });
        document.querySelectorAll('button[data-address-id].set-default-btn').forEach(btn => {
            btn.addEventListener('click', () => setDefaultAddress(btn.dataset.addressId));
        });
        
        document.querySelectorAll('.edit-card-btn').forEach(btn => {
            btn.addEventListener('click', () => populateCardFormForEdit(btn.dataset.cardId, cards));
        });
        document.querySelectorAll('.delete-card-btn').forEach(btn => {
            btn.addEventListener('click', () => handleDeleteCreditCard(btn.dataset.cardId));
        });
        document.querySelectorAll('button[data-card-id].set-default-btn').forEach(btn => {
            btn.addEventListener('click', () => setDefaultCard(btn.dataset.cardId));
        });

    } catch (error) {
        profileContainer.innerHTML = addressesContainer.innerHTML = creditCardsContainer.innerHTML = '';
        displayError(`Failed to load profile data: ${error.message}`);
    }
}

function populateAddressFormForEdit(addressId, allAddresses) {
    const address = allAddresses.find(a => a.address_id === addressId);
    if (!address) {
        displayGlobalMessage("Address not found for editing.", "error");
        return;
    }

    document.getElementById('address-id-hidden').value = address.address_id;
    document.getElementById('address-street').value = address.street; // HTML ID
    document.getElementById('address-city').value = address.city;
    document.getElementById('address-country').value = address.country;
    document.getElementById('address-zip').value = address.zip_code; // HTML ID
    document.getElementById('address-form-submit-btn').textContent = 'Update Address';

    const protectedNote = document.getElementById('address-protected-note');
    if (protectedNote) {
        protectedNote.style.display = address.is_protected ? 'block' : 'none';
    }
    
    const editIndicator = document.getElementById('address-edit-mode-indicator');
    if (editIndicator) {
        editIndicator.innerHTML = `<i class="fas fa-pen"></i> Editing Address: <strong>${address.street}</strong>`; // Update innerHTML directly
        editIndicator.style.display = 'flex'; // Or 'block'
    }
    
    const formContainer = document.getElementById('address-form-container');
    if (formContainer && !formContainer.classList.contains('open')) {
        toggleItemForm('address');
    }
    if(formContainer) formContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function handleAddOrUpdateAddress(e) {
    e.preventDefault();
    if (!currentUser) return;

    const form = e.target;
    const editingAddressId = form.getAttribute('data-editing-id');
    const isEditing = !!editingAddressId;

    const street = document.getElementById('address-line1').value;
    const city = document.getElementById('address-city').value;
    const country = document.getElementById('address-country').value;
    const zip_code = document.getElementById('address-postal-code').value;

    if (!street || !city || !country || !zip_code) {
        displayError("Fill all required address fields.");
        return;
    }
    
    const queryParams = `street=${encodeURIComponent(street)}&city=${encodeURIComponent(city)}&country=${encodeURIComponent(country)}&zip_code=${encodeURIComponent(zip_code)}`;
    const userIdForAction = document.getElementById('viewing-user-id')?.value || currentUser.user_id;

    try {
        let newAddressId = editingAddressId;
        if (isEditing) {
            await apiCall(`/api/users/${userIdForAction}/addresses/${editingAddressId}?${queryParams}`, 'PUT', null, true);
            displaySuccess('Address updated successfully!');
        } else {
            const response = await apiCall(`/api/users/${userIdForAction}/addresses?${queryParams}`, 'POST', null, true);
            newAddressId = response.address_id;
            displaySuccess('Address added successfully!');
        }
        
        form.reset();
        form.removeAttribute('data-editing-id');
        const submitBtn = document.getElementById('add-address-form-submit-btn');
        if (submitBtn) submitBtn.textContent = 'Add Address';
        
        document.getElementById('address-edit-mode')?.classList.remove('active');
        const formContainer = document.getElementById('address-form-container');
        formContainer?.classList.remove('open');
        
        const toggleBtn = document.getElementById('toggle-address-form-btn');
        if (toggleBtn) {
            toggleBtn.classList.remove('active');
            const icon = toggleBtn.querySelector('i');
            if (icon) { icon.className = 'fas fa-plus'; }
            const span = toggleBtn.querySelector('span');
            if (span) { span.textContent = 'Add New Address'; }
        }
        
        showFormSuccessIndicator('add-address-form');
        await fetchAndDisplayUserProfile();
        if (newAddressId) {
            highlightElement(`address-${newAddressId.substring(0,8)}`);
        }
        
    } catch (error) {
        displayError(`Failed to ${isEditing ? 'update' : 'add'} address: ${error.message}`);
    }
}

async function handleAddressFormSubmit(event) {
    event.preventDefault();
    const addressId = document.getElementById('address-id-hidden').value;
    const isEditing = !!addressId;

    const addressFields = [
        { inputId: 'address-street', errorId: 'address-street-error', required: true, errorMessage: 'Street is required.' },
        { inputId: 'address-city', errorId: 'address-city-error', required: true, errorMessage: 'City is required.' },
        { inputId: 'address-country', errorId: 'address-country-error', required: true, errorMessage: 'Country is required.' },
        { inputId: 'address-zip', errorId: 'address-zip-error', required: true, errorMessage: 'Zip code is required.' },
    ];

    clearFormErrors('address-form', addressFields);
    if (!validateAndDisplayFormErrors('address-form', addressFields)) return;

    const street = document.getElementById('address-street').value.trim(); // HTML ID
    const city = document.getElementById('address-city').value.trim();
    const country = document.getElementById('address-country').value.trim();
    const zip_code = document.getElementById('address-zip').value.trim(); // HTML ID
    
    const userIdForRequest = document.getElementById('currently-viewed-user-id').value;
    let queryParams = `street=${encodeURIComponent(street)}&city=${encodeURIComponent(city)}&country=${encodeURIComponent(country)}&zip_code=${encodeURIComponent(zip_code)}`;
    const method = isEditing ? 'PUT' : 'POST';
    const endpoint = isEditing ? `/api/users/${userIdForRequest}/addresses/${addressId}?${queryParams}` : `/api/users/${userIdForRequest}/addresses?${queryParams}`;
    const actionText = isEditing ? 'updated' : 'added';

    try {
        showPageLoader(isEditing ? 'Updating address...' : 'Adding address...');
        const response = await apiCall(endpoint, method, null);
        displayGlobalMessage(`Address for ${currentlyViewedUsername} ${actionText} successfully!`, 'success');
        
        const newOrUpdatedAddressId = isEditing ? addressId : response.address_id;
        
        await fetchAndDisplayFullProfile(userIdForRequest); 
        cancelItemForm('address'); 
        if (newOrUpdatedAddressId) {
            highlightElement(`address-item-${newOrUpdatedAddressId.substring(0,8)}`);
        }
    } catch (error) {
        displayGlobalMessage(`Error ${actionText} address for ${currentlyViewedUsername}: ${error.message}`, 'error');
    } finally {
        hidePageLoader();
    }
}

async function handleDeleteAddress(addressId, isProtected = false) {
    const userIdForRequest = document.getElementById('currently-viewed-user-id').value;
    const confirmMsg = `Are you sure you want to delete this address from ${currentlyViewedUsername}'s profile?`;
    if (!confirm(confirmMsg)) return;

    try {
        await apiCall(`/api/users/${userIdForRequest}/addresses/${addressId}`, 'DELETE');
        displayGlobalMessage(`Address deleted successfully for ${currentlyViewedUsername}!`, 'success');
        fetchAndDisplayFullProfile(userIdForRequest);
    } catch (error) {
        if (!handleProtectedEntityError(error)) {
            displayGlobalMessage(`Error deleting address for ${currentlyViewedUsername}: ${error.message}`, 'error');
        }
    }
}


// --- Credit Card Management Functions ---
function renderCreditCards(cards, container) {
    if (!container) return;
    // const userIdForRequest = document.getElementById('currently-viewed-user-id').value; // Not needed if onclick uses global

    if (!cards || cards.length === 0) {
        container.innerHTML = `<div class="empty-state"><i class="fas fa-credit-card"></i><p>No credit cards found for ${currentlyViewedUsername}.</p></div>`;
        return;
    }
    let html = cards.map(card => `
        <div class="item-card credit-card-card" id="card-item-${card.card_id.substring(0,8)}">
            <div class="item-card-header">
                <i class="fas fa-credit-card"></i>
                <h4>${card.cardholder_name}${card.is_protected ? ' <span class="protected-indicator" title="This item is protected for core demo stability. Destructive actions are limited.">🛡️ Protected</span>' : ''}
                    ${card.is_default ? '<span class="default-badge">Default</span>' : `<button class="btn-xs set-default-btn" onclick="setDefaultCard('${card.card_id}')">Set Default</button>`}
                </h4>
            </div>
            <div class="item-card-content">
                <p><span class="card-detail-text">Number:</span> •••• •••• •••• ${card.card_last_four}</p>
                <p><span class="card-detail-text">Expires:</span> ${card.expiry_month}/${card.expiry_year.substring(2)}</p>
                <p class="text-muted"><small>ID: ${card.card_id.substring(0,8)}...</small></p>
            </div>
            <div class="item-actions">
                <button class="btn btn-sm btn-secondary edit-card-btn" data-card-id="${card.card_id}" data-is-protected="${card.is_protected}"><i class="fas fa-pen"></i> Edit</button>
                <button class="btn btn-sm btn-danger delete-card-btn" data-card-id="${card.card_id}" data-is-protected="${card.is_protected}"><i class="fas fa-trash"></i> Delete</button>
            </div>
        </div>
    `).join('');
    container.innerHTML = html;

    document.querySelectorAll('.edit-card-btn').forEach(btn =>
        btn.addEventListener('click', () => populateCardFormForEdit(btn.dataset.cardId, cards))
    );
    document.querySelectorAll('.delete-card-btn').forEach(btn =>
        btn.addEventListener('click', () => handleDeleteCreditCard(btn.dataset.cardId, btn.dataset.isProtected === 'true'))
    );
}

function populateCardFormForEdit(cardId, allCards) {
    const card = allCards.find(c => c.card_id === cardId);
    if (!card) {
        displayGlobalMessage("Credit card not found for editing.", "error");
        return;
    }

    document.getElementById('card-id-hidden').value = card.card_id;
    document.getElementById('card-cardholder-name').value = card.cardholder_name;
    document.getElementById('card-expiry-month').value = card.expiry_month;
    document.getElementById('card-expiry-year').value = card.expiry_year;
    
    const cardNumberInput = document.getElementById('card-number-input');
    const cardCvvInput = document.getElementById('card-cvv-input');

    const cardholderInput = document.getElementById('card-cardholder-name');
    const expiryMonthInput = document.getElementById('card-expiry-month');
    const expiryYearInput = document.getElementById('card-expiry-year');
    const protectedNote = document.getElementById('card-protected-note');

    if (cardNumberInput) {
        cardNumberInput.value = '';
        cardNumberInput.placeholder = 'Not updatable';
        cardNumberInput.disabled = true;
    }
    if (cardCvvInput) {
        cardCvvInput.value = '';
        cardCvvInput.placeholder = 'Not updatable';
        cardCvvInput.disabled = true;
    }

    if (protectedNote) protectedNote.style.display = card.is_protected ? 'block' : 'none';
    if (cardholderInput) cardholderInput.disabled = false;
    if (expiryMonthInput) expiryMonthInput.disabled = false;
    if (expiryYearInput) expiryYearInput.disabled = false;
    
    document.getElementById('card-form-submit-btn').textContent = 'Update Card';
    
    const editIndicator = document.getElementById('card-edit-mode-indicator');
    if (editIndicator) {
        editIndicator.innerHTML = `<i class="fas fa-pen"></i> Editing Card: <strong>Ending in ${card.card_last_four}</strong>`; // Update innerHTML
        editIndicator.style.display = 'flex'; // Or 'block'
    }
    
    const formContainer = document.getElementById('card-form-container');
    if (formContainer && !formContainer.classList.contains('open')) {
        toggleItemForm('card');
    }
    if(formContainer) formContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function handleAddOrUpdateCreditCard(e) {
    e.preventDefault();
    if (!currentUser) return;

    const form = e.target;
    const editingCardId = form.getAttribute('data-editing-id');
    const isEditing = !!editingCardId;

    const cardNumber = document.getElementById('card-number').value;
    const cardholderName = document.getElementById('card-name').value;
    const expiry = document.getElementById('card-expiry').value;
    const cvv = document.getElementById('card-cvv').value;

    if (!cardholderName || !expiry ) {
        displayError("Cardholder name and expiry are required.");
        return;
    }
    
    if (!isEditing && (!cardNumber || !cvv)) {
        displayError("Card number and CVV are required for new cards.");
        return;
    }
    
    const [expiryMonth, expiryYearSuffix] = expiry.split('/');
    if (!expiryMonth || !expiryYearSuffix || expiryMonth.length > 2 || expiryYearSuffix.length !== 2) {
        displayError("Expiry date must be in MM/YY format (e.g., 06/27).");
        return;
    }
    
    const expiryYear = `20${expiryYearSuffix}`;
    const userIdForAction = document.getElementById('viewing-user-id')?.value || currentUser.user_id;
    
    try {
        let newCardId = editingCardId;
        let queryParams = `cardholder_name=${encodeURIComponent(cardholderName)}&expiry_month=${encodeURIComponent(expiryMonth.padStart(2,'0'))}&expiry_year=${encodeURIComponent(expiryYear)}`;
        
        if (isEditing) {
            // Note: Backend PUT /credit-cards/{card_id} does not take card_number or cvv
            await apiCall(`/api/users/${userIdForAction}/credit-cards/${editingCardId}?${queryParams}`, 'PUT', null, true);
            displaySuccess('Credit card updated successfully!');
        } else {
            queryParams += `&card_number=${encodeURIComponent(cardNumber)}&cvv=${encodeURIComponent(cvv)}`;
            const response = await apiCall(`/api/users/${userIdForAction}/credit-cards?${queryParams}`, 'POST', null, true);
            newCardId = response.card_id;
            displaySuccess('Credit card added successfully!');
        }
        
        form.reset();
        form.removeAttribute('data-editing-id');
        document.getElementById('card-number').placeholder = 'e.g., 4111111111111111';
        document.getElementById('card-cvv').placeholder = 'e.g., 123';
        
        const submitBtn = document.getElementById('add-creditcard-form-submit-btn');
        if (submitBtn) submitBtn.textContent = 'Add Credit Card';
        
        document.getElementById('card-edit-mode')?.classList.remove('active');
        const formContainer = document.getElementById('creditcard-form-container');
        formContainer?.classList.remove('open');
        
        const toggleBtn = document.getElementById('toggle-creditcard-form-btn');
        if (toggleBtn) {
            toggleBtn.classList.remove('active');
            const icon = toggleBtn.querySelector('i');
            if (icon) { icon.className = 'fas fa-plus'; }
            const span = toggleBtn.querySelector('span');
            if (span) { span.textContent = 'Add New Card'; }
        }
        
        showFormSuccessIndicator('add-creditcard-form');
        await fetchAndDisplayUserProfile();
        if (newCardId) {
            highlightElement(`card-${newCardId.substring(0,8)}`);
        }
        
    } catch (error) {
        displayError(`Failed to ${isEditing ? 'update' : 'add'} credit card: ${error.message}`);
    }
}

async function handleCardFormSubmit(event) {
    event.preventDefault();
    const cardIdHiddenInput = document.getElementById('card-id-hidden');
    const cardId = cardIdHiddenInput ? cardIdHiddenInput.value : null;
    const isEditing = !!cardId;

    const cardholderNameInput = document.getElementById('card-cardholder-name');
    const expiryMonthInput = document.getElementById('card-expiry-month');
    const expiryYearInput = document.getElementById('card-expiry-year');
    const cardNumberInput = document.getElementById('card-number-input');
    const cvvInput = document.getElementById('card-cvv-input');

    if (!cardholderNameInput || !expiryMonthInput || !expiryYearInput || !cardNumberInput || !cvvInput) {
        displayGlobalMessage('One or more card form fields are missing from the page.', 'error');
        console.error('Card form input elements not found.');
        return;
    }

    const cardFields = [
        { inputId: 'card-cardholder-name', errorId: 'card-cardholder-name-error', required: true, errorMessage: 'Cardholder name is required.' },
        { inputId: 'card-number-input', errorId: 'card-number-input-error', required: !isEditing, validationFn: v => /^\d{12,19}$/.test(v), errorMessage: 'Valid card number is required for new cards.' },
        { inputId: 'card-expiry-month', errorId: 'card-expiry-month-error', required: true, validationFn: v => /^(0[1-9]|1[0-2])$/.test(v), errorMessage: 'Valid month (MM) required.' },
        { inputId: 'card-expiry-year', errorId: 'card-expiry-year-error', required: true, validationFn: v => /^20[2-9][0-9]$/.test(v), errorMessage: 'Valid year (YYYY) required.' },
        { inputId: 'card-cvv-input', errorId: 'card-cvv-input-error', required: !isEditing, validationFn: v => /^\d{3,4}$/.test(v), errorMessage: 'CVV required for new cards.' },
    ];

    clearFormErrors('card-form', cardFields);
    if (!validateAndDisplayFormErrors('card-form', cardFields)) return;

    const cardholder_name = cardholderNameInput.value.trim();
    const expiry_month = expiryMonthInput.value.trim();
    const expiry_year = expiryYearInput.value.trim();

    const card_number = cardNumberInput.value.trim();
    const cvv = cvvInput.value.trim();

    const userIdForRequest = document.getElementById('currently-viewed-user-id').value;
    if (!userIdForRequest) {
        displayGlobalMessage('Cannot process card: User context is missing.', 'error');
        return;
    }
    
    let queryParams = `cardholder_name=${encodeURIComponent(cardholder_name)}&expiry_month=${encodeURIComponent(expiry_month)}&expiry_year=${encodeURIComponent(expiry_year)}`;
    
    let method = 'POST';
    let endpoint = `/api/users/${userIdForRequest}/credit-cards?${queryParams}`; // Base for POST
    let actionText = 'added';

    if (isEditing) {
        method = 'PUT';
        // For PUT, card_number and cvv are not included in queryParams as per backend (user_profile_router.py)
        endpoint = `/api/users/${userIdForRequest}/credit-cards/${cardId}?${queryParams}`;
        actionText = 'updated';
    } else {
        // For new cards (POST), add card_number and cvv
        queryParams += `&card_number=${encodeURIComponent(card_number)}&cvv=${encodeURIComponent(cvv)}`;
        endpoint = `/api/users/${userIdForRequest}/credit-cards?${queryParams}`; // Re-assign endpoint with new params
    }
    
    try {
        showPageLoader(isEditing ? 'Updating card...' : 'Adding card...');
        const response = await apiCall(endpoint, method, null); // Body is null as data is in query params
        displayGlobalMessage(`Credit card for ${currentlyViewedUsername} ${actionText} successfully!`, 'success');
        
        const newOrUpdatedCardId = isEditing ? cardId : response.card_id;

        await fetchAndDisplayFullProfile(userIdForRequest); // Refresh the entire profile view
        cancelItemForm('card'); // Close and reset the form
        
        if (newOrUpdatedCardId) {
            highlightElement(`card-item-${newOrUpdatedCardId.substring(0,8)}`);
        }
    } catch (error) {
        displayGlobalMessage(`Error ${actionText} card for ${currentlyViewedUsername}: ${error.message}`, 'error');
    } finally {
        hidePageLoader();
    }
}

async function handleDeleteCreditCard(cardId, isProtected = false) {
    const userIdForRequest = document.getElementById('currently-viewed-user-id').value;
    const confirmMsg = `Are you sure you want to delete this credit card from ${currentlyViewedUsername}'s profile?`;
    if (!confirm(confirmMsg)) return;

    try {
        await apiCall(`/api/users/${userIdForRequest}/credit-cards/${cardId}`, 'DELETE');
        displayGlobalMessage(`Credit card deleted successfully for ${currentlyViewedUsername}!`, 'success');
        fetchAndDisplayFullProfile(userIdForRequest);
    } catch (error) {
        if (!handleProtectedEntityError(error)) {
            displayGlobalMessage(`Error deleting credit card: ${error.message}`, 'error');
        }
    }
}

function setupFormToggles() {
    // This function was intended for the profile page collapsible forms.
    // The initializeProfilePageInteractions function now handles this.
    // If you have other general form toggles, they can go here.
}

function initializeProfilePageInteractions() {
    const toggleAddressFormBtn = document.getElementById('toggle-address-form-btn');
    const addressFormContainer = document.getElementById('address-form-container');
    const toggleCreditcardFormBtn = document.getElementById('toggle-creditcard-form-btn');
    const creditcardFormContainer = document.getElementById('creditcard-form-container');
    const addressEditMode = document.getElementById('address-edit-mode');
    const cardEditMode = document.getElementById('card-edit-mode');
    const cancelAddressEditBtn = document.getElementById('cancel-address-edit-btn');
    const cancelCardEditBtn = document.getElementById('cancel-card-edit-btn');

    function setupToggle(toggleBtn, formContainer) {
        if (toggleBtn && formContainer) {
            toggleBtn.addEventListener('click', function() {
                formContainer.classList.toggle('open');
                this.classList.toggle('active');
                const icon = this.querySelector('i');
                const span = this.querySelector('span');
                if (formContainer.classList.contains('open')) {
                    if(icon) icon.className = 'fas fa-minus';
                    if(span) span.textContent = 'Cancel';
                } else {
                    if(icon) icon.className = 'fas fa-plus';
                    if(span) span.textContent = this.dataset.addText || 'Add New'; // Use a data attribute for original text
                    // Also reset edit mode if cancelling by closing
                    if (formContainer.id === 'address-form-container' && addressEditMode) addressEditMode.classList.remove('active');
                    if (formContainer.id === 'creditcard-form-container' && cardEditMode) cardEditMode.classList.remove('active');
                }
            });
        }
    }

    setupToggle(toggleAddressFormBtn, addressFormContainer);
    setupToggle(toggleCreditcardFormBtn, creditcardFormContainer);
    
    if (cancelAddressEditBtn && addressFormContainer && toggleAddressFormBtn && addressEditMode) {
        cancelAddressEditBtn.addEventListener('click', function() {
            addressFormContainer.classList.remove('open');
            toggleAddressFormBtn.classList.remove('active');
            addressEditMode.classList.remove('active');
            document.getElementById('add-address-form').reset();
            document.getElementById('add-address-form').removeAttribute('data-editing-id');
            document.getElementById('add-address-form-submit-btn').textContent = 'Add Address';
            const icon = toggleAddressFormBtn.querySelector('i');
            if(icon) icon.className = 'fas fa-plus';
            const span = toggleAddressFormBtn.querySelector('span');
            if(span) span.textContent = toggleAddressFormBtn.dataset.addText || 'Add New Address';
        });
    }

    if (cancelCardEditBtn && creditcardFormContainer && toggleCreditcardFormBtn && cardEditMode) {
        cancelCardEditBtn.addEventListener('click', function() {
            creditcardFormContainer.classList.remove('open');
            toggleCreditcardFormBtn.classList.remove('active');
            cardEditMode.classList.remove('active');
            document.getElementById('add-creditcard-form').reset();
            document.getElementById('add-creditcard-form').removeAttribute('data-editing-id');
            document.getElementById('add-creditcard-form-submit-btn').textContent = 'Add Credit Card';
            document.getElementById('card-number').placeholder = 'e.g., 4111111111111111';
            document.getElementById('card-cvv').placeholder = 'e.g., 123';
            const icon = toggleCreditcardFormBtn.querySelector('i');
            if(icon) icon.className = 'fas fa-plus';
            const span = toggleCreditcardFormBtn.querySelector('span');
            if(span) span.textContent = toggleCreditcardFormBtn.dataset.addText || 'Add New Card';
        });
    }
}

function highlightElement(elementId, duration = 2000) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.classList.add('highlight');
    setTimeout(() => {
        element.classList.remove('highlight');
    }, duration);
}

// animateNewItem not currently used, can be removed or kept for future.
// function animateNewItem(element) { ... }

function showFormSuccessIndicator(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    let indicator = form.querySelector('.form-success-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'form-success-indicator';
        form.appendChild(indicator);
    }
    indicator.innerHTML = '<i class="fas fa-check-circle"></i> Saved successfully!';
    indicator.style.opacity = '1'; // Ensure it's visible
    
    setTimeout(() => {
        indicator.style.opacity = '0';
        setTimeout(() => {
            if (indicator.parentNode === form) { // Check if it wasn't removed by other logic
                indicator.remove();
            }
        }, 500);
    }, 1500);
}

async function setDefaultAddress(addressId) {
    const userIdForRequest = document.getElementById('currently-viewed-user-id').value;
    try {
        const addresses = await apiCall(`/api/users/${userIdForRequest}/addresses`, 'GET');
        for (const addr of addresses) {
            const isTarget = addr.address_id === addressId;
            const params = `street=${encodeURIComponent(addr.street)}&city=${encodeURIComponent(addr.city)}&country=${encodeURIComponent(addr.country)}&zip_code=${encodeURIComponent(addr.zip_code)}&is_default=${isTarget}`;
            await apiCall(`/api/users/${userIdForRequest}/addresses/${addr.address_id}?${params}`, 'PUT', null);
        }
        displayGlobalMessage(`Default address for ${currentlyViewedUsername} updated!`, 'success');
        await fetchAndDisplayFullProfile(userIdForRequest);
        highlightElement(`address-item-${addressId.substring(0,8)}`);
    } catch (error) {
        if (!handleProtectedEntityError(error)) {
            displayGlobalMessage(`Error setting default address for ${currentlyViewedUsername}: ${error.message}`, 'error');
        }
    }
}

async function setDefaultCard(cardId) {
    const userIdForRequest = document.getElementById('currently-viewed-user-id').value;
    try {
        const cards = await apiCall(`/api/users/${userIdForRequest}/credit-cards`, 'GET');
        for (const card of cards) {
            const isTarget = card.card_id === cardId;
            const params = `cardholder_name=${encodeURIComponent(card.cardholder_name)}&expiry_month=${encodeURIComponent(card.expiry_month)}&expiry_year=${encodeURIComponent(card.expiry_year)}&is_default=${isTarget}`;
            await apiCall(`/api/users/${userIdForRequest}/credit-cards/${card.card_id}?${params}`, 'PUT', null);
        }
        displayGlobalMessage(`Default credit card for ${currentlyViewedUsername} updated!`, 'success');
        fetchAndDisplayFullProfile(userIdForRequest);
    } catch (error) {
        if (!handleProtectedEntityError(error)) {
            displayGlobalMessage(`Error setting default credit card: ${error.message}`, 'error');
        }
    }
}



// Checkout Page Functions
function displayCheckoutItems() {
    const container = document.getElementById('cart-summary'); 
    if (!container) {
        console.error('Checkout items container (#cart-summary) not found');
        const mainCheckoutArea = document.querySelector('#checkout-form'); 
        if (mainCheckoutArea) {
            displayError('Could not display cart summary. Element missing.', 'checkout-error');
        }
        return;
    }

    if (cart.length === 0) {
        container.innerHTML = '<p>Your cart is empty. <a href="/cart">Go to cart</a></p>';
        const placeOrderBtn = document.getElementById('place-order-btn');
        if (placeOrderBtn) {
            placeOrderBtn.disabled = true;
        }
        return;
    }

    let itemsHTML = `
        <table class="checkout-items-table table">
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Price</th>
                    <th class="text-center">Quantity</th>
                    <th class="text-right">Total</th>
                </tr>
            </thead>
            <tbody>
    `;
    let cartTotal = 0;
    cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        cartTotal += itemTotal;
        itemsHTML += `
            <tr>
                <td>${item.name}</td>
                <td>$${item.price.toFixed(2)}</td>
                <td class="text-center">${item.quantity}</td>
                <td class="text-right">$${itemTotal.toFixed(2)}</td>
            </tr>
        `;
    });
    itemsHTML += `
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="3" class="text-right"><strong>Grand Total</strong></td>
                    <td class="text-right"><strong id="checkout-grand-total">$${cartTotal.toFixed(2)}</strong></td>
                </tr>
            </tfoot>
        </table>
    `;
    container.innerHTML = itemsHTML;
}

async function populateAddressDropdown() {
    const addressSelect = document.getElementById('address-id');
    if (!addressSelect || !currentUser) return;
    addressSelect.innerHTML = '<option value="">Loading addresses...</option>';
    try {
        const addresses = await apiCall(`/api/users/${currentUser.user_id}/addresses`, 'GET', null, true);
        if (addresses && addresses.length > 0) {
            addressSelect.innerHTML = '<option value="">Select an address</option>';
            addresses.forEach(addr => {
                const option = document.createElement('option');
                option.value = addr.address_id;
                option.textContent = `${addr.street}, ${addr.city}, ${addr.country} ${addr.zip_code}`;
                if (addr.is_default) { option.textContent += ' (Default)'; option.selected = true; }
                addressSelect.appendChild(option);
            });
        } else {
            addressSelect.innerHTML = '<option value="">No addresses. Please add one in profile.</option>';
        }
    } catch (error) {
        console.error('Failed to load addresses for checkout:', error);
        addressSelect.innerHTML = '<option value="">Error loading addresses</option>';
        displayError('Could not load addresses.', 'checkout-error');
    }
}

async function populateCreditCardDropdown() {
    const paymentMethodSelect = document.getElementById('credit-card-id');
    if (!paymentMethodSelect || !currentUser) return;
    paymentMethodSelect.innerHTML = '<option value="">Loading payment methods...</option>';
    try {
        const cards = await apiCall(`/api/users/${currentUser.user_id}/credit-cards`, 'GET', null, true);
        if (cards && cards.length > 0) {
            paymentMethodSelect.innerHTML = '<option value="">Select a payment method</option>';
            cards.forEach(card => {
                const option = document.createElement('option');
                option.value = card.card_id;
                option.textContent = `Card ending in ${card.card_last_four} (${card.cardholder_name}), Expires: ${card.expiry_month}/${card.expiry_year.substring(2)}`;
                if (card.is_default) { option.textContent += ' (Default)'; option.selected = true; }
                paymentMethodSelect.appendChild(option);
            });
        } else {
            paymentMethodSelect.innerHTML = '<option value="">No payment methods. Please add one in profile.</option>';
        }
    } catch (error) {
        console.error('Failed to load credit cards for checkout:', error);
        paymentMethodSelect.innerHTML = '<option value="">Error loading payment methods</option>';
        displayError('Could not load payment methods.', 'checkout-error');
    }
}


async function handleOrderSubmission(e) {
    e.preventDefault();
    const submitButton = document.getElementById('place-order-btn');
    const originalButtonText = submitButton.textContent;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    submitButton.disabled = true;

    try {
        // Get user's selected address and card
        let addressId = document.getElementById('address-id')?.value;
        let creditCardId = document.getElementById('credit-card-id')?.value;

        // --- BOLA Demo Elements ---
        const bolaMode = document.getElementById('order-for-other-user')?.checked;
        const targetUserId = document.getElementById('target-user-id')?.value.trim();
        const targetAddressId = document.getElementById('target-address-id')?.value.trim();
        const targetCardId = document.getElementById('target-credit-card-id')?.value.trim();

        let pathUserId = currentUser.user_id;

        if (bolaMode) {
            if (!targetCardId) {
                displayGlobalMessage('Target Credit Card ID is required for BOLA exploit.', 'error');
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                return;
            }

            // For demo purposes we keep the path user ID as the current user.
            // Swap to `targetUserId` here if the demo expects path tampering.
            if (targetAddressId) addressId = targetAddressId;
            creditCardId = targetCardId;
        }

        if (!addressId || !creditCardId) {
            throw new Error('Please select a shipping address and payment method.');
        }

        // Build the base order creation endpoint
        let orderEndpoint = `/api/users/${pathUserId}/orders?address_id=${addressId}&credit_card_id=${creditCardId}`;
        cart.forEach((item, index) => {
            orderEndpoint += `&product_id_${index + 1}=${item.product_id}&quantity_${index + 1}=${item.quantity}`;
        });

        // 1. Create the order first
        const newOrder = await apiCall(orderEndpoint, 'POST', null, true);
        let finalOrder = newOrder;

        // 2. If a coupon was staged, apply it now to the newly created order
        if (typeof appliedCouponCode !== 'undefined' && appliedCouponCode) {
            console.log(`Applying staged coupon '${appliedCouponCode}' to new order ${newOrder.order_id}`);
            const couponEndpoint = `/api/users/${pathUserId}/orders/${newOrder.order_id}/apply-coupon?coupon_code=${appliedCouponCode}`;
            finalOrder = await apiCall(couponEndpoint, 'POST', null, true);
        }

        // Success
        displayGlobalMessage(`Order ${finalOrder.order_id.substring(0,8)}... placed successfully!`, 'success');
        cart = [];
        saveCart();
        appliedCouponCode = null; // Reset coupon after successful order

        submitButton.innerHTML = '<i class="fas fa-check-circle"></i> Order Placed!';
        setTimeout(() => { window.location.href = '/orders'; }, 2000);

    } catch (error) {
        displayGlobalMessage(`Failed to place order: ${error.message}`, 'error');
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
    }
}

// Admin page functions
function setupAdminInterface() {
    if (currentUser && !currentUser.is_admin) {
        displayGlobalMessage("BFLA Vulnerability Demo: You are accessing admin functions as a regular user!", "warning");
    }
    fetchAdminProducts();
}

async function fetchAdminProducts() {
    const productsContainer = document.getElementById('admin-products-container');
    const loadingIndicator = document.getElementById('products-loading');
    if (!productsContainer || !loadingIndicator) {
        console.error('Admin products DOM elements not found'); return;
    }
    loadingIndicator.style.display = 'block';
    productsContainer.innerHTML = '';

    try {
        let queryParams = '?role=user';
        const adminEscalation = document.getElementById('admin-escalation')?.checked;
        const revealInternal = document.getElementById('reveal-internal')?.checked;

        if (adminEscalation) queryParams += '&role=admin';
        if (revealInternal) queryParams += '&status=internal';

        // Add '/api' prefix to API endpoint paths
        const products = await apiCall(`/api/products${queryParams}`, 'GET', null, true);

        if (!products || products.length === 0) {
            productsContainer.innerHTML = '<p>No products found or access denied.</p>';
            return;
        }
        let tableHTML = `<table class="admin-products-table table"><thead><tr><th>ID</th><th>Name</th><th>Price</th><th>Category</th><th>Internal Status</th><th>Stock</th><th>Actions</th></tr></thead><tbody>`;
        for (const product of products) {
            let stock = { quantity: "N/A" };
             try {
                // Add '/api' prefix to stock endpoint
                stock = await apiCall(`/api/products/${product.product_id}/stock`, 'GET', null, false);
            } catch(e) { console.warn("Could not fetch stock for " + product.product_id)}

            tableHTML += `
                <tr>
                    <td>${product.product_id.substring(0,8)}...</td>
                    <td>${product.name}</td>
                    <td>$${product.price.toFixed(2)}</td>
                    <td>${product.category || 'N/A'}</td>
                    <td>${product.internal_status || 'N/A'}</td>
                    <td class="text-center">${stock.quantity}</td>
                    <td>
                        <button class="btn btn-sm btn-danger delete-product-btn" data-product-id="${product.product_id}">Del</button>
                    </td>
                </tr>`;
        }
        tableHTML += `</tbody></table>`;
        productsContainer.innerHTML = tableHTML;

        document.querySelectorAll('.delete-product-btn').forEach(btn => {
            btn.addEventListener('click', async function() {
                const productId = this.dataset.productId;
                if (confirm(`BFLA DEMO: Delete product ${productId}? (Normally admin only)`)) {
                    try {
                        // Add '/api' prefix to delete endpoint
                        await apiCall(`/api/products/${productId}`, 'DELETE', null, true);
                        displaySuccess(`Product ${productId} deleted via BFLA.`);
                        fetchAdminProducts();
                    } catch (err) { displayError(`Delete failed: ${err.message}`); }
                }
            });
        });

    } catch (error) {
        displayError(`Failed to load admin products: ${error.message}.`);
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

function addExploitSuccessStyles() {
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .vulnerability-exploit-success {
            background-color: #f8f9fa;
            border: 2px solid var(--danger-color);
            border-radius: 8px;
            padding: 2rem;
            margin: 2rem 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .exploit-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 1.5rem;
        }
        
        .exploit-icon {
            font-size: 2.5rem;
            line-height: 1;
            animation: bounce 1s infinite alternate;
        }
        
        .exploit-header h3 {
            color: var(--danger-color);
            margin: 0;
            font-size: 1.5rem;
        }
        
        .exploit-details {
            background-color: white;
            padding: 1.5rem;
            border-radius: 6px;
            border-left: 5px solid var(--danger-color);
        }
        
        .exploit-details ul {
            margin-bottom: 1.5rem;
        }
        
        .stolen-card-summary {
            background-color: #f8d7da;
            border-radius: 6px;
            padding: 1rem;
            margin: 1.5rem 0;
        }
        
        .stolen-card-summary h4 {
            color: var(--danger-hover);
            margin-top: 0;
            margin-bottom: 0.75rem;
            font-size: 1.1rem;
        }
        
        .card-theft-details {
            background-color: rgba(255, 255, 255, 0.6);
            padding: 0.75rem;
            border-radius: 4px;
        }
        
        .card-theft-details p {
            margin: 5px 0;
        }
        
        .security-impact-large {
            display: flex;
            align-items: center;
            margin: 1.5rem 0;
            gap: 12px;
        }
        
        .security-impact-large .impact-meter {
            padding: 6px 15px;
            font-size: 1rem;
        }
        
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 1.5rem;
        }
        
        @keyframes bounce {
            from { transform: translateY(0); }
            to { transform: translateY(-10px); }
        }
    `;
    document.head.appendChild(styleElement);
}

// Call this function when the DOM loads to ensure the styles are added
document.addEventListener('DOMContentLoaded', function() {
    // Add the exploit success styles
    addExploitSuccessStyles();
    
    // ...rest of your existing DOMContentLoaded code...
});