/**
 * Sets up Parameter Pollution demo functionality for product detail page
 * This includes copy to clipboard functionality and URL manipulation for the demo
 */
function setupParameterPollutionDemo() {
    // Copy URL button functionality
    const copyUrlBtn = document.getElementById('copy-url-btn');
    if (copyUrlBtn) {
        copyUrlBtn.addEventListener('click', function() {
            const urlElement = document.getElementById('demo-url');
            if (!urlElement) return;
            
            const url = urlElement.textContent;
            navigator.clipboard.writeText(url)
                .then(() => {
                    displayGlobalMessage('URL copied to clipboard! Try visiting it to see the Parameter Pollution demo.', 'success');
                })
                .catch(err => {
                    displayError('Failed to copy URL: ' + err);
                });
        });
    }
    
    // Setup the demo URL with the parameter pollution example
    const demoUrlEl = document.getElementById('demo-url');
    if (demoUrlEl) {
        // Create the URL without the parameter, then add it for the demo
        const baseUrl = window.location.href.split('?')[0];
        demoUrlEl.textContent = `${baseUrl}?internal_status=view`;
    }
    
    // If there's already an internal_status parameter in the URL, show the "exploit success" message
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('internal_status')) {
        const status = urlParams.get('internal_status');
        showVulnerabilityWarning(
            'Parameter Pollution', 
            `You have successfully demonstrated Parameter Pollution by adding the <code>internal_status=${status}</code> parameter to the URL. In a secure application, this internal field would only be accessible to admin users.`
        );
        
        // Add a visual element showing the internal status that was "exposed"
        const productDetailContainer = document.getElementById('product-detail-container');
        if (productDetailContainer) {
            const internalStatusEl = document.createElement('div');
            internalStatusEl.className = 'internal-status';
            internalStatusEl.innerHTML = `
                <strong>Internal Status (Exposed via Parameter Pollution):</strong> ${status}
                <p class="vulnerability-info">This internal field would normally only be visible to admins.</p>
            `;
            
            // Find where to insert this - after product details but before demo section
            const demoSection = document.querySelector('.vulnerability-demo-section');
            if (demoSection && demoSection.parentNode === productDetailContainer) {
                productDetailContainer.insertBefore(internalStatusEl, demoSection);
            } else {
                productDetailContainer.appendChild(internalStatusEl);
            }
        }
    }
}
