/**
 * Sets up Parameter Pollution demo functionality for product detail page
 * This includes copy to clipboard functionality and URL manipulation for the demo
 */
function setupParameterPollutionDemo(productId) {
    console.log(`setupParameterPollutionDemo called for productId: ${productId}`);

    if (!productId) {
        console.error("setupParameterPollutionDemo: productId is undefined or null.");
        return;
    }

    const currentUrlEl = document.getElementById('current-product-url');
    const demoUrlEl = document.getElementById('demo-url-display');
    const pollutionForm = document.getElementById('parameter-pollution-form');
    const paramNameInput = document.getElementById('param-name');
    const paramValueInput = document.getElementById('param-value');

    // --- 1. Update URL Displays ---
    const basePageUrl = window.location.origin + window.location.pathname; // URL without query string

    if (currentUrlEl) {
        currentUrlEl.textContent = basePageUrl;
        console.log("Populated current-product-url:", currentUrlEl.textContent);
    } else {
        console.warn("Element with ID 'current-product-url' not found. URL display will be incomplete.");
    }

    if (demoUrlEl && paramNameInput && paramValueInput) {
        // Function to update the demo URL display based on form inputs
        const updateDemoUrlText = () => {
            const pName = paramNameInput.value.trim() || "internal_status"; // Default if empty
            const pValue = paramValueInput.value.trim() || "example_value"; // Default if empty
            demoUrlEl.textContent = `${basePageUrl}?${encodeURIComponent(pName)}=${encodeURIComponent(pValue)}`;
        };
        
        // Initial update and on input change
        updateDemoUrlText();
        paramNameInput.addEventListener('input', updateDemoUrlText);
        paramValueInput.addEventListener('input', updateDemoUrlText);
        console.log("Populated demo-url-display:", demoUrlEl.textContent);
    } else {
        console.warn("One or more elements for demo URL display (demo-url-display, param-name, param-value) not found. Demo URL display functionality limited.");
    }

    // --- 2. Handle "Detected in URL" on Page Load ---
    // This part displays a message if 'internal_status' (or any other param) is already in the browser's URL
    const urlParams = new URLSearchParams(window.location.search);
    const initialPollutedParamName = paramNameInput ? paramNameInput.value.trim() : "internal_status"; // Use default if input not found
    
    if (urlParams.has(initialPollutedParamName)) {
        const statusValueFromUrl = urlParams.get(initialPollutedParamName);
        
        const message = `The <code>${initialPollutedParamName}</code> parameter in the URL was detected with value: <strong>${statusValueFromUrl}</strong>. 
                         This demonstrates how hidden or unintended parameters might be manipulated by directly altering the URL. 
                         The product details below might reflect this if the backend processed this parameter on initial load.`;
        
        if (typeof showVulnerabilityWarning === 'function') {
            showVulnerabilityWarning('Parameter Pollution (URL Detected)', message);
        } else if (typeof displayGlobalMessage === 'function') {
            displayGlobalMessage(message, 'warning', 7000);
        } else {
            console.warn("Vulnerability warning/display function not available.");
        }

        // Note: The actual display of the "internal_status" from the product object
        // is handled by fetchAndDisplayProductDetail in main.js (the small badge).
        // This section is for the explicit "detected in URL" demo message.
    }

    // --- 3. Setup Parameter Pollution Form Submission ---
    if (pollutionForm && paramNameInput && paramValueInput) {
        pollutionForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            console.log("Parameter pollution form submitted.");

            const paramName = paramNameInput.value.trim();
            const paramValue = paramValueInput.value.trim();

            if (!paramName) {
                if (typeof displayGlobalMessage === 'function') displayGlobalMessage('Parameter Name cannot be empty for the demo.', 'error');
                else console.error('Parameter Name cannot be empty for the demo.');
                return;
            }

            // The backend PUT /api/products/{product_id} expects parameters in the query string
            const endpoint = `/api/products/${productId}?${encodeURIComponent(paramName)}=${encodeURIComponent(paramValue)}`;
            
            try {
                if (typeof showPageLoader === 'function') showPageLoader('Attempting to pollute product parameters...');
                
                // apiCall and displayGlobalMessage are assumed to be globally available from main.js
                if (typeof apiCall !== 'function') {
                    console.error("apiCall function is not defined!");
                    if (typeof displayGlobalMessage === 'function') displayGlobalMessage('Critical error: API call function missing.', 'error');
                    return;
                }

                await apiCall(endpoint, 'PUT'); // Body is null/empty as per backend router for this PUT

                if (typeof displayGlobalMessage === 'function') {
                    displayGlobalMessage(
                        `Pollution attempt sent for parameter "${paramName}" with value "${paramValue}". Reloading product details...`, 
                        'success'
                    );
                }
                
                // Re-fetch and display product details to see if the pollution had an effect
                // fetchAndDisplayProductDetail is assumed global from main.js
                if (typeof fetchAndDisplayProductDetail === 'function') {
                    await fetchAndDisplayProductDetail(productId);
                } else {
                    console.error("fetchAndDisplayProductDetail function is not defined! Cannot refresh product details.");
                    if (typeof displayGlobalMessage === 'function') displayGlobalMessage('Could not refresh product details automatically.', 'warning');
                }

            } catch (error) {
                console.error('Error during parameter pollution attempt:', error);
                if (typeof displayGlobalMessage === 'function') {
                    displayGlobalMessage(`Error attempting parameter pollution: ${error.message || 'Unknown error'}`, 'error');
                }
            } finally {
                if (typeof hidePageLoader === 'function') hidePageLoader();
            }
        });
        console.log("Parameter pollution form event listener attached.");
    } else {
        console.warn("Parameter pollution form or its input elements not found. Demo form will not be functional.");
    }
}
