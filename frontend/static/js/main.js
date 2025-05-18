// Constants and global variables
const API_BASE_URL = 'http://localhost:8000'; // Correct API base URL
let authToken = localStorage.getItem('token');
let currentUser = JSON.parse(localStorage.getItem('user') || 'null');
let cart = JSON.parse(localStorage.getItem('cart') || '[]');

// DOM content loaded event to setup initial UI
document.addEventListener('DOMContentLoaded', () => {
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
            const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status} ${response.statusText} for ${method} ${fullUrl}` }));
            console.error('API Call Error Response:', errorData);
            throw new Error(errorData.detail || `HTTP error! status: ${response.status} for ${method} ${fullUrl}`);
        }
        
        return response.status === 204 ? null : response.json();
    } catch (error) {
        console.error(`API Call Exception at ${method} ${fullUrl}:`, error);
        throw error;
    }
}

function displayError(message, containerId = 'error-message-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="error-message"><strong>Error:</strong> ${message}</div>`;
        container.style.display = 'block';
        setTimeout(() => { clearError(containerId); }, 8000);
    } else {
        displayGlobalMessage(message, 'error');
    }
}

function clearError(containerId = 'error-message-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }
    const genericErrorContainer = document.getElementById('global-error-container');
    if (genericErrorContainer) {
        genericErrorContainer.innerHTML = '';
        genericErrorContainer.style.display = 'none';
    }
}

function displaySuccess(message, containerId = 'success-message-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="success-message"><strong>Success:</strong> ${message}</div>`;
        container.style.display = 'block';
        setTimeout(() => { clearSuccess(containerId); }, 5000);
    } else {
        displayGlobalMessage(message, 'success');
    }
}

function clearSuccess(containerId = 'success-message-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
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
        navLinks += `<a href="/admin">Admin Demo</a>`;
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

function handleLogout(e) {
    e.preventDefault();
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    authToken = null;
    currentUser = null;
    cart = []; // Clear cart on logout
    saveCart();
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

function displayGlobalMessage(message, type = 'info') {
    const messageContainer = document.getElementById('global-message-container') || document.body.appendChild(document.createElement('div'));
    if(messageContainer.id !== 'global-message-container') messageContainer.id = 'global-message-container';

    const messageElement = document.createElement('div');
    messageElement.className = `global-message ${type}-message`;
    messageElement.innerHTML = `<p>${message}</p><button class="close-btn" onclick="this.parentElement.remove()">×</button>`;
    messageContainer.appendChild(messageElement);
    setTimeout(() => { messageElement.remove(); }, 5000);
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
        'Laptop Pro 15': 'laptop 15.png',
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

// Page Initialization Functions
function initHomePage() {
    console.log('Initializing Home Page');
    fetchAndDisplayProducts();
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleProductSearch);
    }
}

async function handleProductSearch(e) {
    e.preventDefault();
    const searchTerm = document.getElementById('search-term').value.trim();
    const productGrid = document.getElementById('products-container');
    const loadingIndicator = productGrid.querySelector('.loading-indicator');

    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (productGrid && !loadingIndicator) productGrid.innerHTML = '<p class="loading-indicator">Searching...</p>';
    
    try {
        const endpoint = searchTerm ? `/api/products/search/?name=${encodeURIComponent(searchTerm)}` : '/api/products';
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
    console.log('Initializing Product Detail Page');
    const pathParts = window.location.pathname.split('/');
    const productIdWithSuffix = pathParts[pathParts.length - 1];
    const productId = productIdWithSuffix.replace('.html', '');
    fetchAndDisplayProductDetail(productId);
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

function initProfilePage() {
    console.log('Initializing Profile Page');
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }
    let viewingUserIdInput = document.getElementById('viewing-user-id');
    if (!viewingUserIdInput) {
        viewingUserIdInput = document.createElement('input');
        viewingUserIdInput.type = 'hidden';
        viewingUserIdInput.id = 'viewing-user-id';
        document.body.appendChild(viewingUserIdInput);
    }
    viewingUserIdInput.value = currentUser.user_id;

    fetchAndDisplayUserProfile();
    initializeProfilePageInteractions(); 

    const viewProfileBtn = document.getElementById('view-profile-btn');
    const returnToProfileBtn = document.getElementById('return-to-profile-btn');
    const targetUserIdField = document.getElementById('target-user-id');

    if (viewProfileBtn && targetUserIdField && viewingUserIdInput) {
        viewProfileBtn.addEventListener('click', () => {
            const targetId = targetUserIdField.value.trim();
            if (targetId) {
                viewingUserIdInput.value = targetId;
                fetchAndDisplayUserProfile();
            } else {
                displayError('Please enter a User ID to view.');
            }
        });
    }

    if (returnToProfileBtn && viewingUserIdInput && targetUserIdField) {
        returnToProfileBtn.addEventListener('click', () => {
            viewingUserIdInput.value = currentUser.user_id;
            targetUserIdField.value = '';
            fetchAndDisplayUserProfile();
        });
    }

    const addAddressForm = document.getElementById('add-address-form');
    if (addAddressForm) {
        addAddressForm.addEventListener('submit', handleAddOrUpdateAddress);
    }

    const addCreditCardForm = document.getElementById('add-creditcard-form');
    if (addCreditCardForm) {
        addCreditCardForm.addEventListener('submit', handleAddOrUpdateCreditCard);
    }
    
    // setupFormToggles(); // This was called here but might be redundant if initializeProfilePageInteractions covers it
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

    displayCheckoutItems(); // This is the function that was missing
    populateAddressDropdown(); 
    populateCreditCardDropdown(); 
    
    // Add event listener for checkout form submission
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', handleOrderSubmission);
    }
    
    // Initialize BOLA demo checkbox if it exists
    const bolaCheckbox = document.getElementById('order-for-other-user');
    const bolaFields = document.getElementById('bola-demo-fields');
    const userIdInput = document.getElementById('target-user-id');
    const creditCardIdInput = document.getElementById('target-credit-card-id');
    const vulnerabilityBanner = document.getElementById('bola-vulnerability-banner');
    
    if (bolaCheckbox) {
        bolaCheckbox.addEventListener('change', function() {
            if (bolaFields) {
                bolaFields.style.display = this.checked ? 'block' : 'none';
            }
            
            if (userIdInput) {
                userIdInput.disabled = !this.checked;
            }
            
            if (creditCardIdInput) {
                creditCardIdInput.disabled = !this.checked;
            }
            
            if (vulnerabilityBanner) {
                vulnerabilityBanner.style.display = this.checked ? 'block' : 'none';
            }
            
            if (!this.checked) {
                if (userIdInput) userIdInput.value = '';
                if (creditCardIdInput) creditCardIdInput.value = '';
                
                // Hide results and user info when checkbox is unchecked
                const userSearchResults = document.getElementById('user-search-results');
                const cardSearchResults = document.getElementById('card-search-results');
                const targetUserInfo = document.getElementById('target-user-info');
                
                if (userSearchResults) userSearchResults.style.display = 'none';
                if (cardSearchResults) cardSearchResults.style.display = 'none';
                if (targetUserInfo) targetUserInfo.style.display = 'none';
            }
        });
    }
    
    // Initialize search buttons
    const searchUsersBtn = document.getElementById('search-users-btn');
    if (searchUsersBtn) {
        searchUsersBtn.addEventListener('click', searchUsers);
    }
    
    const searchCardsBtn = document.getElementById('search-cards-btn');
    if (searchCardsBtn) {
        searchCardsBtn.addEventListener('click', searchCreditCards);
    }
    
    // Add event listener for when target user ID changes
    if (userIdInput) {
        userIdInput.addEventListener('change', updateTargetUserInfo);
    }
}

async function searchUsers() {
    const userList = document.getElementById('user-list');
    const resultsContainer = document.getElementById('user-search-results');
    
    if (!userList || !resultsContainer)
        return;
    
    userList.innerHTML = '<p>Searching for users...</p>';
    resultsContainer.style.display = 'block';
    
    try {
        const users = await apiCall('/api/users', 'GET');
        if (!users || users.length === 0) {
            userList.innerHTML = '<p class="text-muted">No users found.</p>';
            return;
        }
        
        let usersHTML = '<div class="vulnerability-warning mb-3">' +
                        '<strong>⚠️ BOLA Vulnerability:</strong> You can see and select other users\' IDs!' +
                        '</div><ul class="list-group">';
        
        users.forEach(user => {
            const isCurrentUser = currentUser && user.user_id === currentUser.user_id;
            const userClass = isCurrentUser ? 'list-group-item-primary' : 'list-group-item-warning';
            const userLabel = isCurrentUser ? ' (Your Account)' : ' (Another User)';
            
            usersHTML += `
                <li class="list-group-item ${userClass}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${user.username}</strong>${userLabel}<br>
                            <small>User ID: <code>${user.user_id}</code></small>
                        </div>
                        <button class="btn btn-sm btn-outline-danger select-user-btn" 
                                data-user-id="${user.user_id}" 
                                data-username="${user.username}">
                            Select as Target
                        </button>
                    </div>
                </li>
            `;
        });
        
        usersHTML += '</ul>';
        userList.innerHTML = usersHTML;
        
        // Add click handlers to select buttons
        document.querySelectorAll('.select-user-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const userId = this.getAttribute('data-user-id');
                const username = this.getAttribute('data-username');
                document.getElementById('target-user-id').value = userId;
                
                // Show success message
                displayGlobalMessage(`Selected user: ${username} (ID: ${userId})`, 'warning');
                
                // Also update the theft preview if it exists
                const theftPreview = document.getElementById('theft-preview');
                if (theftPreview) {
                    theftPreview.innerHTML = `<div class="alert alert-danger">
                        <strong>⚠️ Target Selected:</strong> ${username} (ID: ${userId})
                    </div>`;
                }
                
                // Try to auto-search for credit cards for this user
                const searchCardsBtn = document.getElementById('search-cards-btn');
                if (searchCardsBtn) {
                    searchCardsBtn.click();
                }
            });
        });
    } catch (error) {
        userList.innerHTML = `<p class="text-danger">Error loading users: ${error.message}</p>`;
    }
}

async function searchCreditCards() {
    const targetUserId = document.getElementById('target-user-id').value.trim();
    const cardList = document.getElementById('card-list');
    const resultsContainer = document.getElementById('card-search-results');
    const theftPreview = document.getElementById('theft-preview');
    
    if (!cardList || !resultsContainer)
        return;
    
    if (!targetUserId) {
        cardList.innerHTML = '<p class="text-danger">Please select a target user first.</p>';
        resultsContainer.style.display = 'block';
        return;
    }
    
    // Show loading state
    cardList.innerHTML = '<p>Searching for credit cards to steal...</p>';
    resultsContainer.style.display = 'block';
    
    if (theftPreview) {
        theftPreview.innerHTML = '<div class="alert alert-info">Searching for payment methods...</div>';
    }
    
    try {
        // Get user info for better context
        let targetUserName = "Unknown User";
        try {
            const userInfo = await apiCall(`/api/users/${targetUserId}`, 'GET');
            if (userInfo && userInfo.username) {
                targetUserName = userInfo.username;
            }
        } catch (e) {
            console.warn("Couldn't fetch user details:", e);
        }
        
        // Highlight the vulnerability
        const isCurrentUser = currentUser && targetUserId === currentUser.user_id;
        const targetUserLabel = isCurrentUser ? 'YOUR OWN' : 'ANOTHER USER\'S';
        
        // Now get the credit cards
        const cards = await apiCall(`/api/users/${targetUserId}/credit-cards`, 'GET');
        if (!cards || cards.length === 0) {
            cardList.innerHTML = `<p class="text-muted">No credit cards found for ${targetUserName}.</p>`;
            return;
        }
        
        // Update the theft preview first with stronger warning
        if (theftPreview) {
            theftPreview.innerHTML = `
                <div class="alert alert-danger">
                    <h4 class="alert-heading">⚠️ BOLA Vulnerability Demo</h4>
                    <p>You are about to place an order using ${targetUserLabel} payment method.</p>
                    <p><strong>Target User:</strong> ${targetUserName} (ID: ${targetUserId})</p>
                    <hr>
                    <p class="mb-0">This demonstrates a Broken Object Level Authorization (BOLA) vulnerability where you can charge purchases to another user's payment method.</p>
                </div>
            `;
        }
        
        let cardsHTML = `
            <div class="vulnerability-warning mb-3">
                <strong>⚠️ BOLA Vulnerability:</strong> You can see and use ${targetUserLabel} credit cards!
            </div>
            <div class="alert alert-${isCurrentUser ? 'info' : 'danger'} mb-3">
                Viewing credit cards belonging to: <strong>${targetUserName}</strong> (ID: ${targetUserId})
            </div>
            <ul class="list-group">
        `;
        
        cards.forEach(card => {
            const cardOwnership = isCurrentUser ? 'YOUR OWN CARD' : 'ANOTHER USER\'S CARD';
            const cardClass = isCurrentUser ? 'list-group-item-info' : 'list-group-item-danger';
            
            cardsHTML += `
                <li class="list-group-item ${cardClass}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge badge-warning">${cardOwnership}</span>
                            <br>
                            <strong>${card.cardholder_name}</strong><br>
                            <small>Card ending in: ${card.card_last_four}</small><br>
                            <small>Expires: ${card.expiry_month}/${card.expiry_year.substring(2)}</small><br>
                            <small>Card ID: <code>${card.card_id}</code></small>
                        </div>
                        <button class="btn btn-sm btn-outline-danger select-card-btn" 
                                data-card-id="${card.card_id}"
                                data-last-four="${card.card_last_four}"
                                data-owner-name="${targetUserName}">
                            Use This Card
                        </button>
                    </div>
                </li>
            `;
        });
        
        cardsHTML += '</ul>';
        cardList.innerHTML = cardsHTML;
        
        // Add click handlers to select buttons
        document.querySelectorAll('.select-card-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const cardId = this.getAttribute('data-card-id');
                const lastFour = this.getAttribute('data-last-four');
                const ownerName = this.getAttribute('data-owner-name');
                document.getElementById('target-credit-card-id').value = cardId;
                
                // Show stronger warning message
                if (isCurrentUser) {
                    displayGlobalMessage(`Selected your own card ending in ${lastFour}`, 'info');
                } else {
                    displayGlobalMessage(`⚠️ VULNERABILITY DEMO: Selected ${ownerName}'s card ending in ${lastFour}`, 'warning');
                    
                    // Show a larger warning in the theft preview
                    if (theftPreview) {
                        theftPreview.innerHTML += `
                            <div class="alert alert-warning">
                                <strong>Card Selected:</strong> ${ownerName}'s card ending in ${lastFour}
                                <hr>
                                <p>You can now complete the order charging to this card!</p>
                            </div>
                        `;
                    }
                }
            });
        });
    } catch (error) {
        cardList.innerHTML = `<p class="text-danger">Error loading credit cards: ${error.message}</p>`;
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

function initOrdersPage() {
    console.log('Initializing Orders Page');
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }
    
    // Check if we were viewing another user's orders after BOLA exploit
    const storedTargetUserId = sessionStorage.getItem('view_orders_for_user_id');
    const storedTargetUsername = sessionStorage.getItem('view_orders_for_username');
    
    let viewingUserIdInput = document.getElementById('viewing-user-id-orders');
    if (!viewingUserIdInput) {
        viewingUserIdInput = document.createElement('input');
        viewingUserIdInput.type = 'hidden';
        viewingUserIdInput.id = 'viewing-user-id-orders';
        const demoSection = document.querySelector('.vulnerability-demo-section');
        if (demoSection) {
            demoSection.appendChild(viewingUserIdInput);
        } else {
            document.body.appendChild(viewingUserIdInput);
        }
    }
    
    // If we have a stored target user ID from the checkout BOLA exploit, use it
    if (storedTargetUserId) {
        viewingUserIdInput.value = storedTargetUserId;
        
        // Also populate the target user ID field for visibility
        const targetUserIdField = document.getElementById('target-user-id');
        if (targetUserIdField) {
            targetUserIdField.value = storedTargetUserId;
        }
        
        // Show a message that we're viewing another user's orders
        displayGlobalMessage(`BOLA Vulnerability Demo: Viewing orders for user ${storedTargetUsername || storedTargetUserId}`, 'warning');
        
        // Clear the stored values after using them
        sessionStorage.removeItem('view_orders_for_user_id');
        sessionStorage.removeItem('view_orders_for_username');
    } else {
        viewingUserIdInput.value = currentUser.user_id;
    }

    fetchAndDisplayOrders();

    const viewOrdersForm = document.getElementById('view-orders-form');
    const targetUserIdField = document.getElementById('target-user-id');
    const returnButton = document.getElementById('return-to-own-orders');

    if (viewOrdersForm && targetUserIdField && viewingUserIdInput) {
        viewOrdersForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const targetId = targetUserIdField.value.trim();
            if (targetId) {
                viewingUserIdInput.value = targetId;
                fetchAndDisplayOrders();
            } else {
                displayError('Please enter a User ID to view their orders.');
            }
        });
    }
    if (returnButton && viewingUserIdInput && targetUserIdField) {
         returnButton.addEventListener('click', function() {
            viewingUserIdInput.value = currentUser.user_id;
            targetUserIdField.value = '';
            document.getElementById('current-viewing').style.display = 'none';
            fetchAndDisplayOrders();
            displayGlobalMessage('Returned to your own orders', 'info');
        });
    }
}

function initAdminPage() {
    console.log('Initializing Admin Page');
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }
    setupAdminInterface();
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
    
    let renderPromises = [];
    
    for (const product of products) {
        renderPromises.push((async () => {
            let stockInfo = { quantity: 0 };
            try {
                stockInfo = await apiCall(`/api/products/${product.product_id}/stock`, 'GET', null, false);
            } catch (error) {
                console.warn(`Failed to fetch stock for product ${product.product_id}: ${error.message}`);
            }
            
            const imagePath = `/static/images/products/${getProductImageFilename(product)}`;
            
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
                            <img src="${imagePath}" alt="${product.name}" class="product-image" loading="lazy"
                                 onerror="this.onerror=null; this.src='/static/images/placeholder.png';">
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
            const imagePath = `/static/images/products/${getProductImageFilename({name: item.name, product_id: item.product_id})}`;
            
            cartItemsHTML += `
                <tr class="cart-item" data-product-id="${item.product_id}" data-testid="cart-item">
                    <td class="product-info">
                        <div class="cart-product">
                            <div class="cart-product-image">
                                <img src="${imagePath}" alt="${item.name}" 
                                     onerror="this.onerror=null; this.src='/static/images/placeholder.png';">
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
    const loadingIndicator = document.getElementById('product-loading');
    const productDetailContainer = document.getElementById('product-detail-container');
    
    if (!productDetailContainer) {
        console.error('Product detail container not found');
        return;
    }
    
    try {
        if (loadingIndicator) loadingIndicator.style.display = 'flex';
        if (productDetailContainer) productDetailContainer.style.display = 'none';
        
        // Fetch product data
        const product = await apiCall(`/api/products/${productId}`, 'GET', null, false);
        
        // Fetch stock data
        let stockInfo = { quantity: 0 };
        try {
            stockInfo = await apiCall(`/api/products/${productId}/stock`, 'GET', null, false);
        } catch (err) { 
            console.warn(`Stock info for ${productId} not found.`); 
        }

        // Determine stock status for styling
        let stockClass = 'out-of-stock';
        let stockText = 'Out of stock';
        let stockBadgeClass = 'badge-danger';
        
        if (stockInfo.quantity > 10) {
            stockClass = 'in-stock';
            stockText = `${stockInfo.quantity} in stock`;
            stockBadgeClass = 'badge-success';
        } else if (stockInfo.quantity > 0) {
            stockClass = 'low-stock';
            stockText = `Only ${stockInfo.quantity} left!`;
            stockBadgeClass = 'badge-warning';
        }

        const imagePath = `/static/images/products/${getProductImageFilename(product)}`;

        // Update page title dynamically
        document.title = `${product.name} - Radware Demo E-Commerce`;
        
        // Update breadcrumb
        const breadcrumb = document.querySelector('.breadcrumb .current-page');
        if (breadcrumb) {
            breadcrumb.textContent = product.name;
        }
        
        productDetailContainer.innerHTML = `
            <div class="product-detail-layout">
                <div class="product-detail-images">
                    <div class="main-image-container">
                        <img src="${imagePath}" alt="${product.name}" id="product-image-detail" class="main-product-image" 
                             onerror="this.onerror=null; this.src='/static/images/placeholder.png';">
                    </div>
                </div>

                <div class="product-detail-info">
                    <h1 id="product-name-detail" data-testid="product-title">${product.name}</h1>

                    <div class="product-meta">
                        <span class="product-category">${product.category || 'Uncategorized'}</span>
                        <div class="product-status-tags">
                            <span class="stock-badge ${stockBadgeClass}" data-testid="stock-badge">${stockText}</span>
                            ${product.internal_status ? `<span class="internal-status-badge">${product.internal_status}</span>` : ''}
                        </div>
                    </div>
                    
                    <div class="product-price-container">
                        <p class="product-price" id="product-price-detail" data-testid="product-price">$${product.price.toFixed(2)}</p>
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
                                    <button type="button" class="quantity-btn decrease" data-testid="decrease-quantity">
                                        <svg viewBox="0 0 24 24" width="16" height="16">
                                            <path d="M19 13H5v-2h14v2z" fill="currentColor"></path>
                                        </svg>
                                    </button>
                                    <input type="number" id="quantity-detail" class="quantity-input" data-testid="quantity-input" 
                                        value="1" min="1" max="${stockInfo.quantity}" 
                                        ${stockInfo.quantity <= 0 ? 'disabled' : ''}>
                                    <button type="button" class="quantity-btn increase" data-testid="increase-quantity">
                                        <svg viewBox="0 0 24 24" width="16" height="16">
                                            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"></path>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                            
                            <button type="submit" id="add-to-cart-btn-detail" class="add-to-cart-btn ${stockInfo.quantity <= 0 ? 'disabled' : ''}"
                                data-testid="add-to-cart-button"
                                data-product-id="${productId}" 
                                data-product-name="${product.name}" 
                                data-product-price="${product.price}"
                                ${stockInfo.quantity <= 0 ? 'disabled' : ''}>
                                <svg class="cart-icon" viewBox="0 0 24 24" width="20" height="20">
                                    <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49A1 1 0 0 0 20 4H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>
                                </svg>
                                ${stockInfo.quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
                                <span class="btn-feedback"></span>
                            </button>
                        </form>
                    </div>
                    
                    <div class="extra-info">
                        <div class="accordion">
                            <div class="accordion-item">
                                <button class="accordion-header" id="shipping-header">
                                    Shipping Information
                                    <span class="accordion-icon">+</span>
                                </button>
                                <div class="accordion-content">
                                    <p>Free shipping on orders over $50. Standard delivery 3-5 business days.</p>
                                </div>
                            </div>
                            <div class="accordion-item">
                                <button class="accordion-header" id="returns-header">
                                    Returns & Warranty
                                    <span class="accordion-icon">+</span>
                                </button>
                                <div class="accordion-content">
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
        
        // Setup quantity controls
        const quantityInput = document.getElementById('quantity-detail');
        const decreaseBtn = document.querySelector('#product-detail-container .quantity-btn.decrease');
        const increaseBtn = document.querySelector('#product-detail-container .quantity-btn.increase');
        
        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', () => {
                if (parseInt(quantityInput.value) > 1) {
                    quantityInput.value = parseInt(quantityInput.value) - 1;
                }
            });
        }
        
        if (increaseBtn) {
            increaseBtn.addEventListener('click', () => {
                const maxQuantity = parseInt(quantityInput.max);
                if (parseInt(quantityInput.value) < maxQuantity) {
                    quantityInput.value = parseInt(quantityInput.value) + 1;
                }
            });
        }
        
        // Setup add to cart form
        const addToCartForm = document.getElementById('add-to-cart-form');
        if (addToCartForm) {
            addToCartForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const quantity = parseInt(quantityInput.value);
                
                if (quantity > 0 && quantity <= stockInfo.quantity) {
                    // Visual feedback
                    const addToCartBtn = document.getElementById('add-to-cart-btn-detail');
                    addToCartBtn.classList.add('clicked');
                    
                    setTimeout(() => {
                        addToCartBtn.classList.remove('clicked');
                    }, 300);
                    
                    // Add to cart
                    addToCart({ 
                        product_id: productId, 
                        name: product.name, 
                        price: product.price, 
                        quantity: quantity 
                    });
                } else { 
                    displayError('Invalid quantity or out of stock.'); 
                }
            });
        }
        
        // Setup accordion functionality
        document.querySelectorAll('.accordion-header').forEach(header => {
            header.addEventListener('click', function() {
                this.classList.toggle('active');
                const content = this.nextElementSibling;
                const icon = this.querySelector('.accordion-icon');
                
                if (content.style.maxHeight) {
                    content.style.maxHeight = null;
                    icon.textContent = '+';
                } else {
                    content.style.maxHeight = content.scrollHeight + 'px';
                    icon.textContent = '-';
                }
            });
        });
        
    } catch (error) {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        displayError(`Failed to load product details: ${error.message}`);
        productDetailContainer.innerHTML = `
            <div class="error-state">
                <svg class="error-icon" viewBox="0 0 24 24" width="48" height="48">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                </svg>
                <p>Error loading product details.</p>
                <button class="btn btn-primary retry-btn" onclick="fetchAndDisplayProductDetail('${productId}')">
                    Try Again
                </button>
            </div>
        `;
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
    ordersContainer.innerHTML = '<div class="loading-indicator">Loading orders...</div>';
    
    try {
        const userIdToFetch = document.getElementById('viewing-user-id-orders')?.value || currentUser.user_id;
        const orders = await apiCall(`/api/users/${userIdToFetch}/orders`, 'GET', null, true);
        
        renderOrders(orders, ordersContainer);

        const currentViewingDiv = document.getElementById('current-viewing');
        // const viewOrdersForm = document.getElementById('view-orders-form'); 

        if (userIdToFetch !== currentUser.user_id) {
            const targetUser = await apiCall(`/api/users/${userIdToFetch}`, 'GET', null, true);
            if (currentViewingDiv) {
                document.getElementById('viewing-username').textContent = targetUser.username;
                document.getElementById('viewing-user-id-display').textContent = userIdToFetch;
                currentViewingDiv.style.display = 'flex';
            }
            displayGlobalMessage(`BOLA: Viewing orders for ${targetUser.username}`, 'warning');
        } else {
            if (currentViewingDiv) currentViewingDiv.style.display = 'none';
        }

    } catch (error) {
        ordersContainer.innerHTML = '';
        displayError(`Failed to load orders: ${error.message}`);
    }
}

function renderOrders(orders, container) {
    if (!orders || orders.length === 0) {
        container.innerHTML = '<p>No orders found.</p>';
        return;
    }
    let ordersHTML = `
        <table class="orders-table table">
            <thead><tr><th>Order ID</th><th>Date</th><th>Status</th><th>Total</th><th>Items</th></tr></thead>
            <tbody>`;
    orders.forEach(order => {
        const orderDate = order.created_at ? new Date(order.created_at).toLocaleDateString() : 'N/A';
        let totalAmount = order.total_amount || 0;
        if(order.items && order.items.length > 0 && totalAmount === 0) {
            totalAmount = order.items.reduce((sum, item) => sum + (item.price_at_purchase * item.quantity), 0);
        }

        ordersHTML += `
            <tr data-order-id="${order.order_id}">
                <td>${order.order_id.substring(0,8)}...</td><td>${orderDate}</td>
                <td><span class="order-status ${order.status.toLowerCase()}">${order.status}</span></td>
                <td>$${totalAmount.toFixed(2)}</td>
                <td class="text-center">${order.items.length}</td>
            </tr>`;
    });
    ordersHTML += `</tbody></table>`;
    container.innerHTML = ordersHTML;
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
            <p><strong>Email:</strong> ${userProfile.email}</p>`;
        profileContainer.innerHTML = profileHTML;
        
        const bolaBanner = document.getElementById('bola-demo-banner');
        const viewProfileBtn = document.getElementById('view-profile-btn');
        const returnToProfileBtn = document.getElementById('return-to-profile-btn');

        if (userIdToFetch !== currentUser.user_id) {
            if(bolaBanner) bolaBanner.style.display = 'block';
            if(viewProfileBtn) viewProfileBtn.style.display = 'none';
            if(returnToProfileBtn) returnToProfileBtn.style.display = 'inline-block';
        } else {
            if(bolaBanner) bolaBanner.style.display = 'none';
            if(viewProfileBtn) viewProfileBtn.style.display = 'inline-block';
            if(returnToProfileBtn) returnToProfileBtn.style.display = 'none';
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
    const addressToEdit = allAddresses.find(addr => addr.address_id === addressId);
    if (!addressToEdit) {
        displayError('Address not found for editing.');
        return;
    }

    document.getElementById('address-line1').value = addressToEdit.street;
    document.getElementById('address-city').value = addressToEdit.city;
    document.getElementById('address-country').value = addressToEdit.country;
    document.getElementById('address-postal-code').value = addressToEdit.zip_code;

    const form = document.getElementById('add-address-form');
    form.setAttribute('data-editing-id', addressId);
    
    const submitBtn = document.getElementById('add-address-form-submit-btn');
    if (submitBtn) submitBtn.textContent = 'Update Address';
    
    const formContainer = document.getElementById('address-form-container');
    if (formContainer && !formContainer.classList.contains('open')) {
        formContainer.classList.add('open');
        const toggleBtn = document.getElementById('toggle-address-form-btn');
        if (toggleBtn) {
            toggleBtn.classList.add('active');
            const icon = toggleBtn.querySelector('i');
            if (icon) { icon.className = 'fas fa-minus'; }
            const span = toggleBtn.querySelector('span');
            if (span) { span.textContent = 'Cancel'; }
        }
    }
    
    const editMode = document.getElementById('address-edit-mode');
    if (editMode) {
        editMode.classList.add('active');
        editMode.innerHTML = `<i class="fas fa-pen"></i> Editing Address: <strong>${addressToEdit.street}</strong>`;
    }
    formContainer?.scrollIntoView({ behavior: 'smooth' });
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

async function handleDeleteAddress(addressId) {
    if (!confirm('Are you sure you want to delete this address?')) return;
    
    const userIdForAction = document.getElementById('viewing-user-id')?.value || currentUser.user_id;
    const addressElement = document.getElementById(`address-${addressId.substring(0,8)}`);
    
    try {
        if (addressElement) {
            highlightElement(`address-${addressId.substring(0,8)}`);
            addressElement.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            addressElement.style.opacity = '0.5';
            addressElement.style.transform = 'translateX(10px)';
        }
        
        await apiCall(`/api/users/${userIdForAction}/addresses/${addressId}`, 'DELETE', null, true);
        displaySuccess('Address deleted successfully!');
        fetchAndDisplayUserProfile();
    } catch (error) {
        displayError(`Failed to delete address: ${error.message}`);
        if (addressElement) {
            addressElement.style.opacity = '1';
            addressElement.style.transform = 'translateX(0)';
        }
    }
}

function populateCardFormForEdit(cardId, allCards) {
    const cardToEdit = allCards.find(card => card.card_id === cardId);
    if (!cardToEdit) {
        displayError('Credit card not found for editing.');
        return;
    }

    document.getElementById('card-name').value = cardToEdit.cardholder_name;
    document.getElementById('card-expiry').value = `${cardToEdit.expiry_month}/${cardToEdit.expiry_year.substring(2)}`;
    
    document.getElementById('card-number').value = '';
    document.getElementById('card-number').placeholder = 'Leave blank to keep current';
    document.getElementById('card-cvv').value = '';
    document.getElementById('card-cvv').placeholder = 'Leave blank to keep current';

    const form = document.getElementById('add-creditcard-form');
    form.setAttribute('data-editing-id', cardId);
    
    const submitBtn = document.getElementById('add-creditcard-form-submit-btn');
    if (submitBtn) submitBtn.textContent = 'Update Credit Card';
    
    const formContainer = document.getElementById('creditcard-form-container');
    if (formContainer && !formContainer.classList.contains('open')) {
        formContainer.classList.add('open');
        const toggleBtn = document.getElementById('toggle-creditcard-form-btn');
        if (toggleBtn) {
            toggleBtn.classList.add('active');
            const icon = toggleBtn.querySelector('i');
            if (icon) { icon.className = 'fas fa-minus'; }
            const span = toggleBtn.querySelector('span');
            if (span) { span.textContent = 'Cancel'; }
        }
    }
    
    const editMode = document.getElementById('card-edit-mode');
    if (editMode) {
        editMode.classList.add('active');
        editMode.innerHTML = `<i class="fas fa-pen"></i> Editing Card: <strong>${cardToEdit.cardholder_name}'s Card</strong>`;
    }
    formContainer?.scrollIntoView({ behavior: 'smooth' });
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

async function handleDeleteCreditCard(cardId) {
    if (!confirm('Are you sure you want to delete this credit card?')) return;
    
    const userIdForAction = document.getElementById('viewing-user-id')?.value || currentUser.user_id;
    const cardElement = document.getElementById(`card-${cardId.substring(0,8)}`);

    try {
        if (cardElement) {
            highlightElement(`card-${cardId.substring(0,8)}`);
            cardElement.style.transition = 'opacity 0.5s ease';
            cardElement.style.opacity = '0.5';
        }
        
        await apiCall(`/api/users/${userIdForAction}/credit-cards/${cardId}`, 'DELETE', null, true);
        displaySuccess('Credit card deleted successfully!');
        fetchAndDisplayUserProfile();
    } catch (error) {
        displayError(`Failed to delete credit card: ${error.message}`);
        if (cardElement) {
            cardElement.style.opacity = '1';
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
    const userIdForAction = document.getElementById('viewing-user-id')?.value || currentUser.user_id;
    try {
        // The backend /users/{user_id}/addresses/{address_id} PUT endpoint handles is_default.
        // We need to fetch the address, set is_default to true, and PUT all fields.
        const addresses = await apiCall(`/users/${userIdForAction}/addresses`, 'GET', null, true);
        const addressToSetDefault = addresses.find(a => a.address_id === addressId);
        if (!addressToSetDefault) throw new Error("Address not found");

        let queryParams = `street=${encodeURIComponent(addressToSetDefault.street)}&city=${encodeURIComponent(addressToSetDefault.city)}&country=${encodeURIComponent(addressToSetDefault.country)}&zip_code=${encodeURIComponent(addressToSetDefault.zip_code)}&is_default=true`;
        
        await apiCall(`/api/users/${userIdForAction}/addresses/${addressId}?${queryParams}`, 'PUT', null, true);
        displaySuccess('Default address updated successfully');
        await fetchAndDisplayUserProfile();
        highlightElement(`address-${addressId.substring(0,8)}`);
    } catch (error) {
        displayError(`Could not set default address: ${error.message}`);
    }
}

async function setDefaultCard(cardId) {
    const userIdForAction = document.getElementById('viewing-user-id')?.value || currentUser.user_id;
    try {
        // Similar to address, PUT to the card with is_default=true
        const cards = await apiCall(`/users/${userIdForAction}/credit-cards`, 'GET', null, true);
        const cardToSetDefault = cards.find(c => c.card_id === cardId);
        if (!cardToSetDefault) throw new Error("Card not found");

        let queryParams = `cardholder_name=${encodeURIComponent(cardToSetDefault.cardholder_name)}&expiry_month=${encodeURIComponent(cardToSetDefault.expiry_month)}&expiry_year=${encodeURIComponent(cardToSetDefault.expiry_year)}&is_default=true`;

        await apiCall(`/api/users/${userIdForAction}/credit-cards/${cardId}?${queryParams}`, 'PUT', null, true);
        displaySuccess('Default payment method updated successfully');
        await fetchAndDisplayUserProfile();
        highlightElement(`card-${cardId.substring(0,8)}`);
    } catch (error) {
        displayError(`Could not set default card: ${error.message}`);
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
                    <td class="text-right"><strong>$${cartTotal.toFixed(2)}</strong></td>
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
    // Defensive: check for error/success containers before using them
    const errorContainer = document.getElementById('checkout-error');
    const successContainer = document.getElementById('checkout-success');
    if (errorContainer) {
        errorContainer.style.display = 'none';
        errorContainer.innerHTML = '';
    }
    if (successContainer) {
        successContainer.style.display = 'none';
        successContainer.innerHTML = '';
    }
    // Show loading state
    const submitButton = document.getElementById('place-order-btn');
    const originalButtonText = submitButton.innerHTML;
    submitButton.innerHTML = 'Processing...';
    submitButton.disabled = true;
    
    const addressId = document.getElementById('address-id').value;
    const creditCardId = document.getElementById('credit-card-id').value;
    
    // Check if form is valid
    const bolaCheckbox = document.getElementById('order-for-other-user');
    const targetUserId = document.getElementById('target-user-id');
    const targetCreditCardId = document.getElementById('target-credit-card-id');
    if (bolaCheckbox && bolaCheckbox.checked) {
        // BOLA mode: require victim user and card
            if (!targetUserId || !targetCreditCardId || !targetUserId.value.trim() || !targetCreditCardId.value.trim()) {
            displayError('Please select a victim user AND a victim credit card for the BOLA exploit.');
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
            return;
        }
    } else {
        // Normal mode: require own address/card
        if (!addressId || !creditCardId) {
            displayError('Please select both a shipping address and payment method.');
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
            return;
        }
    }
    
    try {
        // Check if we're using BOLA demo to order for another user
        const bolaCheckbox = document.getElementById('order-for-other-user');
        const targetUserId = document.getElementById('target-user-id');
        const targetCreditCardId = document.getElementById('target-credit-card-id');
        
        // Determine which user ID to use for the order
        let userIdForOrder = currentUser.user_id;
        let creditCardIdForOrder = creditCardId;
        let exploitedUserName = '';
        let exploitedCardDetails = null;
        
        // Check if BOLA exploit is active
        if (bolaCheckbox && bolaCheckbox.checked) {
            // Get victim user info if available
            if (targetUserId && targetUserId.value.trim()) {
                try {
                    const targetUserInfo = await apiCall(`/api/users/${targetUserId.value.trim()}`, 'GET', null, true);
                    if (targetUserInfo) {
                        exploitedUserName = targetUserInfo.username;
                        userIdForOrder = targetUserId.value.trim();
                    }
                } catch (error) {
                    console.warn("Could not fetch target user info:", error);
                }
            }
            
            // If target credit card ID is provided, use it (this demonstrates the BOLA vulnerability)
            if (targetCreditCardId && targetCreditCardId.value.trim()) {
                try {
                    // Get details about the stolen card for better feedback
                    const allCards = await apiCall(`/api/users/${userIdForOrder}/credit-cards`, 'GET', null, true);
                    exploitedCardDetails = allCards.find(card => card.card_id === targetCreditCardId.value.trim());
                    
                    creditCardIdForOrder = targetCreditCardId.value.trim();
                    console.warn('BOLA VULNERABILITY DEMONSTRATED: Using another user\'s credit card:', creditCardIdForOrder);
                } catch (error) {
                    console.warn("Could not fetch details of stolen card:", error);
                }
            }
        }
        
        // Construct API URL with query parameters
        let orderEndpoint = `/api/users/${userIdForOrder}/orders?address_id=${addressId}&credit_card_id=${creditCardIdForOrder}`;
        
        // Add all cart items to the query parameters
        cart.forEach((item, index) => {
            const i = index + 1; // 1-based index for API
            orderEndpoint += `&product_id_${i}=${item.product_id}&quantity_${i}=${item.quantity}`;
        });
        
        // Call the API to create the order
        const newOrder = await apiCall(orderEndpoint, 'POST', null, true);
        
        // Clear the cart after successful order
        cart = [];
        saveCart();
        
        // Show success message with vulnerability notice if applicable
        let successMessage = `Order placed successfully! Order ID: ${newOrder.order_id}`;
        let exploitDetails = '';
        
        // Enhanced feedback for credit card theft
        if (creditCardIdForOrder !== creditCardId) {
            // We're using a stolen credit card
            successMessage = `BOLA Exploit: Order charged to ${exploitedUserName || "another user"}'s credit card!`;
            
            // Create more detailed exploit feedback
            exploitDetails = `
                <div class="exploit-success">
                    <div class="exploit-header">
                        <div class="exploit-icon">🔐</div>
                        <h3>Security Vulnerability Exploited!</h3>
                    </div>
                    
                    <div class="exploit-details">
                        <p>You've successfully demonstrated a <strong>Broken Object Level Authorization (BOLA)</strong> vulnerability by:</p>
                        <ul>
                            <li>Placing an order as yourself (${currentUser.username})</li>
                            <li>But charging it to <strong>${exploitedUserName || "another user"}</strong>'s credit card</li>
                        </ul>
                        
                        <div class="stolen-card-summary">
                            <h4>Stolen Payment Details:</h4>
                            <div class="card-theft-details">
                                ${exploitedCardDetails ? `
                                    <p><strong>Cardholder:</strong> ${exploitedCardDetails.cardholder_name}</p>
                                    <p><strong>Card:</strong> •••• •••• •••• ${exploitedCardDetails.card_last_four}</p>
                                    <p><strong>Expires:</strong> ${exploitedCardDetails.expiry_month}/${exploitedCardDetails.expiry_year.substring(2)}</p>
                                ` : `
                                    <p><strong>Card ID:</strong> ${creditCardIdForOrder.substring(0,8)}...</p>
                                `}
                            </div>
                        </div>
                        
                        <div class="security-impact-large">
                            <span>Security Impact:</span>
                            <div class="impact-meter high">
                                <span>CRITICAL</span>
                            </div>
                        </div>
                        
                        <p>In a real application, this vulnerability would allow attackers to make unauthorized charges to any user's payment method.</p>
                        
                        <div class="action-buttons">
                            <button id="view-victim-orders" class="btn btn-warning">
                                View ${exploitedUserName || "Victim"}'s Orders
                            </button>
                            <button id="view-own-orders" class="btn btn-primary">
                                View Your Orders
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            // Replace form with exploit details
            const checkoutForm = document.getElementById('checkout-form');
            if (checkoutForm) {
                checkoutForm.innerHTML = '';
                
                const exploitSuccessElement = document.createElement('div');
                exploitSuccessElement.className = 'vulnerability-exploit-success';
                exploitSuccessElement.innerHTML = exploitDetails;
                
                checkoutForm.appendChild(exploitSuccessElement);
                
                // Add event listeners to the buttons
                document.getElementById('view-victim-orders').addEventListener('click', () => {
                    // Store the target user ID in session to view their orders
                    sessionStorage.setItem('view_orders_for_user_id', userIdForOrder);
                    sessionStorage.setItem('view_orders_for_username', exploitedUserName || "Target User");
                    window.location.href = '/orders';
                });
                
                document.getElementById('view-own-orders').addEventListener('click', () => {
                    window.location.href = '/orders';
                });
                
                displayGlobalMessage('BOLA Vulnerability Exploited: Order charged to another user\'s credit card!', 'warning');
                // Re-enable the button and reset text to avoid stuck state
                if (submitButton) {
                    submitButton.innerHTML = originalButtonText;
                    submitButton.disabled = false;
                }
                return;
            }
        } else if (userIdForOrder !== currentUser.user_id) {
            // We're placing an order as another user
            successMessage = `BOLA Vulnerability: Order placed as user ${exploitedUserName || userIdForOrder}!`;
            displayGlobalMessage('BOLA Vulnerability Exploited: Order placed as another user!', 'warning');
        }
        
        displaySuccess(successMessage);
        
        // Replace button with success indicator
        submitButton.className = 'btn btn-success';
        submitButton.innerHTML = '<i class="fas fa-check"></i> Order Placed!';
        
        // Redirect to orders page after a delay
        setTimeout(() => {
            window.location.href = '/orders';
        }, 3000);
        
    } catch (error) {
        displayError(`Failed to place order: ${error.message}`);
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