document.addEventListener('DOMContentLoaded', function() {
    // Parameter pollution checkboxes
    const adminEscalationCheckbox = document.getElementById('admin-escalation');
    const revealInternalCheckbox = document.getElementById('reveal-internal');

    const isRealAdmin = currentUser && currentUser.is_admin;

    // Banner element for BFLA demo
    const vulnerabilityBanner = document.getElementById('vulnerability-banner-admin');

    // Adjust headings and button styles based on admin status
    const addHeader = document.getElementById('add-product-header');
    const addHelper = document.getElementById('add-product-helper');
    const addSubmit = document.getElementById('add-product-submit');
    if (isRealAdmin) {
        if (addHeader) addHeader.textContent = 'Add New Product';
        if (addHelper) addHelper.textContent = 'Add a new product to the catalog.';
        if (addSubmit) {
            addSubmit.classList.remove('btn-warning', 'btn-exploit');
            addSubmit.classList.add('btn-primary');
            addSubmit.textContent = 'Add Product';
        }
    }

    const updateHeader = document.getElementById('update-stock-header');
    const updateHelper = document.getElementById('update-stock-helper');
    const updateSubmit = document.getElementById('update-stock-submit');
    if (isRealAdmin) {
        if (updateHeader) updateHeader.textContent = 'Update Product Stock';
        if (updateHelper) updateHelper.textContent = 'Update stock quantity for a product.';
        if (updateSubmit) {
            updateSubmit.classList.remove('btn-warning', 'btn-exploit');
            updateSubmit.classList.add('btn-primary');
            updateSubmit.textContent = 'Update Stock';
        }
    }

    // Function to update the displayed constructed URL
    function updateConstructedUrlDisplay() {
        const urlDisplaySpan = document.getElementById('constructed-url-display');
        const copyBtn = document.getElementById('copy-constructed-url');
        if (!urlDisplaySpan || !copyBtn || !adminEscalationCheckbox || !revealInternalCheckbox) return;

        let queryParams = '?role=user'; // Base query
        if (adminEscalationCheckbox.checked) {
            queryParams += '&role=admin';
        }
        if (revealInternalCheckbox.checked) {
            queryParams += '&status=internal';
        }
        
        const demoUrl = `/api/products${queryParams}`;
        urlDisplaySpan.textContent = demoUrl;

        copyBtn.onclick = function() {
            // Assuming API_BASE_URL is available globally from main.js, or construct full path differently
            const fullPathToCopy = `${window.location.origin}${demoUrl}`;
            navigator.clipboard.writeText(fullPathToCopy)
                .then(() => displayGlobalMessage('Demo URL copied to clipboard!', 'success'))
                .catch(err => displayGlobalMessage('Failed to copy URL: ' + err.message, 'error'));
        };
    }
    
    // Update banner based on checkbox states
    function updateVulnerabilityBanner() {
        if (!adminEscalationCheckbox || !revealInternalCheckbox || !vulnerabilityBanner) {
            fetchAdminProducts();
            updateConstructedUrlDisplay();
            return;
        }

        const adminChecked = adminEscalationCheckbox.checked;
        const internalChecked = revealInternalCheckbox.checked;

        vulnerabilityBanner.style.display = (adminChecked || internalChecked) ? 'block' : 'none';

        // Fetch products with the current checkbox states
        fetchAdminProducts();
        updateConstructedUrlDisplay();
    }
    
    // Add event listeners to checkboxes
    if (adminEscalationCheckbox) {
        adminEscalationCheckbox.addEventListener('change', updateVulnerabilityBanner);
    }
    if (revealInternalCheckbox) {
        revealInternalCheckbox.addEventListener('change', updateVulnerabilityBanner);
    }
    

    
    // Add product form submission
    const addProductForm = document.getElementById('add-product-form');
    if (addProductForm) {
        addProductForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const name = document.getElementById('new-product-name').value;
            const price = document.getElementById('new-product-price').value;
            const description = document.getElementById('new-product-description').value;
            const category = document.getElementById('new-product-category').value;
            
            // Construct endpoint using URLSearchParams for robustness
            const params = new URLSearchParams();
            params.append('name', name);
            params.append('price', price);
            if (description) params.append('description', description);
            if (category) params.append('category', category);

            // Parameter pollution for internal_status
            const internalStatusValue = document.getElementById('new-product-internal-status').value;
            if (internalStatusValue) {
                params.append('internal_status', internalStatusValue);
                if (typeof displaySuccess === 'function') {
                    displaySuccess("Parameter Pollution Demo: Adding internal_status parameter to the request!");
                }
            }
            
            const endpoint = `/api/products?${params.toString()}`;
            
            try {
                // apiCall is a global function from main.js
                if(typeof apiCall === 'function') {
                    await apiCall(endpoint, 'POST');
                    if (typeof displaySuccess === 'function') {
                        const msg = isRealAdmin ? 'Product added successfully!' : 'Product added (BFLA demo).';
                        displaySuccess(msg);
                    }
                    addProductForm.reset();
                    fetchAdminProducts(); // Refresh the products table
                } else {
                    console.error('apiCall function is not defined.');
                    if(typeof displayError === 'function') displayError('Core function missing, cannot add product.');
                }
            } catch (error) {
                if(typeof displayError === 'function') displayError(`Failed to add product: ${error.message}`);
            }
        });
    }

    const updateStockForm = document.getElementById('update-stock-form');
    if (updateStockForm) {
        updateStockForm.addEventListener('submit', handleUpdateStockSubmit);
    }

    const deleteUserForm = document.getElementById('delete-user-form');
    if (deleteUserForm) {
        deleteUserForm.addEventListener('submit', handleDeleteUserSubmit);
    }
    
    // Initial fetch and UI setup
    updateVulnerabilityBanner(); // This will also call fetchAdminProducts and updateConstructedUrlDisplay
});

// Function to fetch products for admin dashboard (moved outside DOMContentLoaded for clarity, but called within)
// Ensure this function has access to apiCall, displayError, displaySuccess (assumed global from main.js)
async function fetchAdminProducts() {
    const productsContainer = document.getElementById('admin-products-container');
    const loadingIndicator = document.getElementById('products-loading');
    const isRealAdmin = currentUser && currentUser.is_admin;
    
    if (!productsContainer || !loadingIndicator) {
        console.error('Required DOM elements for admin products not found');
        return;
    }
    
    try {
        loadingIndicator.style.display = 'block';
        productsContainer.innerHTML = ''; // Clear previous products
        
        // Build query parameters based on checkbox states
        let queryParams = '?role=user'; // Default role
        const adminEscalationEl = document.getElementById('admin-escalation');
        const revealInternalEl = document.getElementById('reveal-internal');
        
        if (adminEscalationEl && adminEscalationEl.checked) {
            queryParams += '&role=admin'; // Parameter pollution for BFLA
        }
        
        if (revealInternalEl && revealInternalEl.checked) {
            queryParams += '&status=internal'; // Parameter pollution for viewing internal products
        }
        
        // Make the API call with constructed query parameters
        // apiCall is assumed global from main.js
        if(typeof apiCall !== 'function') {
            console.error('apiCall function is not defined.');
            if(typeof displayError === 'function') displayError('Core function missing, cannot fetch products.');
            loadingIndicator.style.display = 'none';
            return;
        }
        const products = await apiCall(`/api/products${queryParams}`, 'GET', null, true); // Requires auth
        
        if (!products || products.length === 0) {
            productsContainer.innerHTML = '<p>No products available or you may not have permission to view them.</p>';
            loadingIndicator.style.display = 'none';
            return;
        }
        
        // Build products table
        let tableHTML = `
            <table class="admin-products-table table"> <!-- Added 'table' class for global table styles -->
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Price</th>
                        <th>Category</th>
                        <th>Internal Status</th>
                        <th>Stock</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Fetch stock for all products in parallel for efficiency
        const stockPromises = products.map(product =>
            apiCall(`/api/products/${product.product_id}/stock`, 'GET', null, false)
                .catch(err => {
                    console.warn(`Failed to fetch stock for ${product.product_id}: ${err.message}`);
                    return { quantity: 'N/A' }; // Default stock if fetch fails
                })
        );
        const stocks = await Promise.all(stockPromises);

        products.forEach((product, index) => {
            const stockQuantity = stocks[index] ? stocks[index].quantity : 'N/A';
            tableHTML += `
                <tr>
                    <td>${product.product_id.substring(0, 8)}...</td>
                    <td>${product.name}</td>
                    <td>$${parseFloat(product.price).toFixed(2)}</td>
                    <td>${product.category || 'N/A'}</td>
                    <td>${product.internal_status || 'N/A'}</td>
                    <td class="text-center">${stockQuantity}</td>
                    <td>
                        <button class="btn btn-sm btn-primary edit-product-btn" data-product-id="${product.product_id}" disabled title="Edit (Not Implemented)">Edit</button>
                        <button class="btn btn-sm btn-danger ${isRealAdmin ? '' : 'btn-exploit '}delete-product-btn" data-product-id="${product.product_id}">${isRealAdmin ? 'Delete' : 'Delete (BFLA Exploit)'}</button>
                    </td>
                </tr>
            `;
        });
        
        tableHTML += `
                </tbody>
            </table>
        `;
        
        productsContainer.innerHTML = tableHTML;
        
        // Success messages for parameter pollution demo
        if (adminEscalationEl && adminEscalationEl.checked) {
            if(typeof displaySuccess === 'function') displaySuccess("BFLA Vulnerability Demonstrated! You've accessed admin-level product data by exploiting parameter pollution.");
        }
        
        if (revealInternalEl && revealInternalEl.checked) {
            if(typeof displaySuccess === 'function') displaySuccess("Parameter Pollution Vulnerability Demonstrated! You're viewing internal products.");
        }
        
        // Add event listeners to delete buttons (Edit is disabled for now)
        document.querySelectorAll('.delete-product-btn').forEach(btn => {
            btn.addEventListener('click', async function() {
                const productId = this.getAttribute('data-product-id');
                const confirmMsg = isRealAdmin ?
                    `Are you sure you want to delete product ${productId}?` :
                    `BFLA Demo: Delete product ${productId}?`;
                if (confirm(confirmMsg)) {
                    try {
                        await apiCall(`/api/products/${productId}`, 'DELETE', null, true);
                        if (typeof displaySuccess === 'function') {
                            const msg = isRealAdmin ?
                                `Product ${productId} deleted successfully.` :
                                `Product ${productId} deleted via BFLA.`;
                            displaySuccess(msg);
                        }
                        fetchAdminProducts();
                    } catch (error) {
                        if (typeof displayError === 'function') {
                            displayError(`Failed to delete product ${productId}: ${error.message}`);
                        }
                    }
                }
            });
        });
            
    } catch (error) {
        if(typeof displayError === 'function') displayError(`Failed to load admin products: ${error.message}`);
        productsContainer.innerHTML = '<p>Error loading products. Check console for details.</p>';
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

async function handleUpdateStockSubmit(e) {
    e.preventDefault();
    const productId = document.getElementById('stock-product-id')?.value.trim();
    const qty = document.getElementById('new-stock-qty')?.value.trim();
    if (!productId || qty === '') {
        displayGlobalMessage('Product ID and quantity required.', 'error');
        return;
    }
    const endpoint = `/api/products/${productId}/stock?quantity=${encodeURIComponent(qty)}`;
    try {
        await apiCall(endpoint, 'PUT');
        const msg = (currentUser && currentUser.is_admin) ?
            `Stock for ${productId} set to ${qty}.` :
            `Stock for ${productId} set to ${qty} (BFLA demo).`;
        displayGlobalMessage(msg, 'success');
        fetchAdminProducts();
    } catch (err) {
        displayGlobalMessage(`Failed to update stock: ${err.message}`, 'error');
    }
}

async function handleDeleteUserSubmit(e) {
    e.preventDefault();
    const userId = document.getElementById('delete-user-id')?.value.trim();
    if (!userId) {
        displayGlobalMessage('User ID required.', 'error');
        return;
    }
    const confirmMsg = (currentUser && currentUser.is_admin) ?
        `Delete user ${userId}?` :
        `BFLA Demo: Delete user ${userId}?`;
    if (!confirm(confirmMsg)) return;
    try {
        await apiCall(`/api/users/${userId}`, 'DELETE');
        const msg = (currentUser && currentUser.is_admin) ?
            `User ${userId} deleted.` :
            `User ${userId} deleted via BFLA demo.`;
        displayGlobalMessage(msg, 'success');
    } catch (err) {
        displayGlobalMessage(`Failed to delete user: ${err.message}`, 'error');
    }
}
