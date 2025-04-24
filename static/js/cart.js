// Shopping cart functionality - Server-side session based implementation

document.addEventListener('DOMContentLoaded', function() {
    // Function to get CSRF token
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
    
    // Function to update cart count in navbar
    function updateCartCount(count) {
        const cartCountBadge = document.querySelector('.cart-count');
        if (cartCountBadge) {
            if (count !== undefined) {
                cartCountBadge.textContent = count;
                cartCountBadge.style.display = count > 0 ? 'inline-block' : 'none';
            } else {
                // Request current cart count from server
                fetch('/customer/cart', {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    // If we get a redirect, the user might not be logged in
                    if (response.redirected) {
                        console.log('Session expired or not logged in');
                        return;
                    }
                    return response.text();
                })
                .then(html => {
                    if (html) {
                        // Parse cart count from response - this is a simple approach
                        // A better approach would be to have a dedicated API endpoint
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = html;
                        
                        const farmers = tempDiv.querySelectorAll('.card-footer');
                        let totalItems = 0;
                        
                        farmers.forEach(footer => {
                            const text = footer.textContent;
                            const match = text.match(/Subtotal \((\d+) items\)/);
                            if (match && match[1]) {
                                totalItems += parseInt(match[1]);
                            }
                        });
                        
                        if (cartCountBadge) {
                            cartCountBadge.textContent = totalItems;
                            cartCountBadge.style.display = totalItems > 0 ? 'inline-block' : 'none';
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching cart count:', error);
                });
            }
        }
    }
    
    // Initialize cart count on page load
    updateCartCount();
    
    // Function to format currency
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount);
    }
    
    // Function to update cart total
    function updateCartTotal() {
        // Calculate totals from the page
        const subtotalElements = document.querySelectorAll('.cart-subtotal');
        const totalElement = document.getElementById('cart-total');
        
        if (totalElement && subtotalElements.length > 0) {
            let total = 0;
            subtotalElements.forEach(el => {
                const value = parseFloat(el.dataset.value || 0);
                total += value;
            });
            
            totalElement.textContent = formatCurrency(total);
        }
    }
    
    // Setup cart quantity change handlers
    const cartQuantityInputs = document.querySelectorAll('.cart-quantity-input');
    if (cartQuantityInputs.length > 0) {
        cartQuantityInputs.forEach(input => {
            input.addEventListener('change', function() {
                const cropId = this.dataset.cropId;
                const quantity = parseFloat(this.value);
                
                if (!quantity || quantity <= 0) {
                    showToast('Please enter a valid quantity', 'danger');
                    // Reset to previous value
                    this.value = this.defaultValue;
                    return;
                }
                
                // Show loading indicator
                const loaderContainer = document.querySelector('.loader-container');
                if (loaderContainer) loaderContainer.style.display = 'flex';
                
                // Send update to server
                fetch('/api/cart/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        crop_id: cropId,
                        quantity: quantity
                    })
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Cart update response:', data);
                    
                    if (data.success) {
                        // Reload page to show updated cart
                        window.location.reload();
                    } else {
                        showToast(data.message, 'danger');
                        // Reset value
                        this.value = this.defaultValue;
                        
                        // Hide loading indicator
                        if (loaderContainer) loaderContainer.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Error updating cart:', error);
                    showToast('An error occurred. Please try again.', 'danger');
                    
                    // Reset value
                    this.value = this.defaultValue;
                    
                    // Hide loading indicator
                    if (loaderContainer) loaderContainer.style.display = 'none';
                });
            });
        });
    }
    
    // Setup remove cart item handlers
    const removeCartItemBtns = document.querySelectorAll('.remove-cart-item');
    if (removeCartItemBtns.length > 0) {
        removeCartItemBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const cropId = this.dataset.cropId;
                
                // Show loading indicator
                const loaderContainer = document.querySelector('.loader-container');
                if (loaderContainer) loaderContainer.style.display = 'flex';
                
                // Send remove request to server
                fetch('/api/cart/remove', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        crop_id: cropId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Remove item response:', data);
                    
                    if (data.success) {
                        // Reload page to show updated cart
                        window.location.reload();
                    } else {
                        showToast(data.message, 'danger');
                        
                        // Hide loading indicator
                        if (loaderContainer) loaderContainer.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Error removing item:', error);
                    showToast('An error occurred. Please try again.', 'danger');
                    
                    // Hide loading indicator
                    if (loaderContainer) loaderContainer.style.display = 'none';
                });
            });
        });
    }
});
