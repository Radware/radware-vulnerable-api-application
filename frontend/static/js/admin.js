document.addEventListener('DOMContentLoaded', function() {
    // Parameter pollution checkboxes
    const adminEscalationCheckbox = document.getElementById('admin-escalation');
    const revealInternalCheckbox = document.getElementById('reveal-internal');
    
    // Banner elements
    const vulnerabilityBanner = document.getElementById('vulnerability-banner');
    const vulnerabilityType = document.getElementById('vulnerability-type');
    const vulnerabilityDescription = document.getElementById('vulnerability-description');

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
        if (!adminEscalationCheckbox || !revealInternalCheckbox || !vulnerabilityBanner || !vulnerabilityType || !vulnerabilityDescription) {
            // If elements are missing, try to fetch products without banner update
            fetchAdminProducts();
            updateConstructedUrlDisplay(); // Also update URL display
            return;
        }

        const adminChecked = adminEscalationCheckbox.checked;
        const internalChecked = revealInternalCheckbox.checked;
        
        if (adminChecked || internalChecked) {
            vulnerabilityBanner.style.display = 'block';
            
            if (adminChecked && internalChecked) {
                vulnerabilityType.textContent = 'Multiple Parameter Pollution (BFLA)';
                vulnerabilityDescription.textContent = 
                    'You are exploiting parameter pollution to bypass role-based access control AND view internal products.';
            } else if (adminChecked) {
                vulnerabilityType.textContent = 'Parameter Pollution (BFLA)';
                vulnerabilityDescription.textContent = 
                    'You are exploiting parameter pollution to bypass role-based access control.';
            } else { // internalChecked must be true
                vulnerabilityType.textContent = 'Parameter Pollution';
                vulnerabilityDescription.textContent = 
                    'You are exploiting parameter pollution to view internal products.';
            }
        } else {
            vulnerabilityBanner.style.display = 'none';
        }
        
        // Fetch products with the current checkbox states
        fetchAdminProducts();
        updateConstructedUrlDisplay(); // Update URL display whenever banner/products are updated
    }
    
    // Add event listeners to checkboxes
    if (adminEscalationCheckbox) {
        adminEscalationCheckbox.addEventListener('change', updateVulnerabilityBanner);
    }
    if (revealInternalCheckbox) {
        revealInternalCheckbox.addEventListener('change', updateVulnerabilityBanner);
    }
    
    // Toggle internal status field for adding products
    const internalStatusCheckbox = document.getElementById('set-internal-status');
    const internalStatusField = document.getElementById('internal-status-field');
    
    if (internalStatusCheckbox && internalStatusField) {
        internalStatusCheckbox.addEventListener('change', function() {
            internalStatusField.style.display = this.checked ? 'block' : 'none';
        });
    }
    
    // Add product form submission
    const addProductForm = document.getElementById('add-product-form');
    if (addProductForm) {
        addProductForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const name = document.getElementById('name').value;
            const price = document.getElementById('price').value;
            const description = document.getElementById('description').value;
            const category = document.getElementById('category').value;
            
            // Construct endpoint using URLSearchParams for robustness
            const params = new URLSearchParams();
            params.append('name', name);
            params.append('price', price);
            if (description) params.append('description', description);
            if (category) params.append('category', category);

            // Parameter pollution for internal_status
            const setInternalStatusCheckbox = document.getElementById('set-internal-status');
            if (setInternalStatusCheckbox && setInternalStatusCheckbox.checked) {
                const internalStatusValue = document.getElementById('internal-status').value;
                if (internalStatusValue) {
                    params.append('internal_status', internalStatusValue);
                    // displaySuccess is a global function from main.js
                    if(typeof displaySuccess === 'function') displaySuccess("Parameter Pollution Demo: Adding internal_status parameter to the request!");
                }
            }
            
            const endpoint = `/api/products?${params.toString()}`;
            
            try {
                // apiCall is a global function from main.js
                if(typeof apiCall === 'function') {
                    await apiCall(endpoint, 'POST'); // Body is not needed as per current backend spec for POST /products
                    if(typeof displaySuccess === 'function') displaySuccess("Product added successfully!");
                    addProductForm.reset();
                    if (internalStatusField) internalStatusField.style.display = 'none'; // Hide field after reset
                    if (setInternalStatusCheckbox) setInternalStatusCheckbox.checked = false;
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
                        <button class="btn btn-sm btn-danger delete-product-btn" data-product-id="${product.product_id}">Delete</button>
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
                if (confirm(`Are you sure you want to delete product ${productId}? This action might be exploiting BFLA if you are not a true admin.`)) {
                    try {
                        await apiCall(`/api/products/${productId}`, 'DELETE', null, true); // Requires auth
                        if(typeof displaySuccess === 'function') displaySuccess(`Product ${productId} deleted successfully.`);
                        fetchAdminProducts(); // Refresh list
                    } catch (error) {
                        if(typeof displayError === 'function') displayError(`Failed to delete product ${productId}: ${error.message}`);
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
        displayGlobalMessage(`Stock for ${productId} set to ${qty}.`, 'success');
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
    if (!confirm(`Delete user ${userId}?`)) return;
    try {
        await apiCall(`/api/users/${userId}`, 'DELETE');
        displayGlobalMessage(`User ${userId} deleted.`, 'success');
    } catch (err) {
        displayGlobalMessage(`Failed to delete user: ${err.message}`, 'error');
    }
}
