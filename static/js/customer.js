// Customer-specific JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Function to get CSRF token
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
    
    // Handle add to cart functionality
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    addToCartForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const cropId = this.dataset.cropId;
            const quantityInput = this.querySelector('input[name="quantity"]');
            const quantity = parseFloat(quantityInput.value);
            
            if (!quantity || quantity <= 0) {
                showToast('Please enter a valid quantity.', 'danger');
                return;
            }
            
            // Using Flask-Login sessions now, no token needed
            fetch('/api/cart/add', {
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
                if (data.success) {
                    showToast(data.message, 'success');
                    
                    // Update cart count in navbar
                    const cartCountBadge = document.querySelector('.cart-count');
                    if (cartCountBadge) {
                        cartCountBadge.textContent = data.cart_count;
                        cartCountBadge.style.display = data.cart_count > 0 ? 'inline-block' : 'none';
                    }
                } else {
                    showToast(data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error adding to cart:', error);
                showToast('An error occurred. Please try again.', 'danger');
            });
        });
    });
    
    // Handle marketplace filters
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        const categorySelect = document.getElementById('category-filter');
        const sortSelect = document.getElementById('sort-filter');
        
        // Auto-submit form when filters change
        categorySelect.addEventListener('change', function() {
            filterForm.submit();
        });
        
        sortSelect.addEventListener('change', function() {
            filterForm.submit();
        });
    }
    
    // Handle payment screenshot preview
    const paymentScreenshotInput = document.getElementById('payment_screenshot');
    if (paymentScreenshotInput) {
        paymentScreenshotInput.addEventListener('change', function() {
            const previewElement = document.getElementById('payment-screenshot-preview');
            if (previewElement && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewElement.src = e.target.result;
                    previewElement.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
    
    // Handle cart item quantity updates
    const cartQuantityInputs = document.querySelectorAll('.cart-quantity-input');
    cartQuantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const cropId = this.dataset.cropId;
            const quantity = parseFloat(this.value);
            
            if (!quantity || quantity <= 0) {
                showToast('Please enter a valid quantity.', 'danger');
                this.value = this.defaultValue;
                return;
            }
            
            updateCartItem(cropId, quantity);
        });
    });
    
    // Handle cart item removal
    const removeCartItemBtns = document.querySelectorAll('.remove-cart-item');
    removeCartItemBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const cropId = this.dataset.cropId;
            removeCartItem(cropId);
        });
    });
    
    // Update cart item quantity
    function updateCartItem(cropId, quantity) {
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
            if (data.success) {
                // Reload the page to update totals
                window.location.reload();
            } else {
                showToast(data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error updating cart:', error);
            showToast('An error occurred. Please try again.', 'danger');
        });
    }
    
    // Remove item from cart
    function removeCartItem(cropId) {
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
            if (data.success) {
                // Reload the page to update cart
                window.location.reload();
            } else {
                showToast(data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error removing from cart:', error);
            showToast('An error occurred. Please try again.', 'danger');
        });
    }
    
    // Function to get JWT token
    function getToken() {
        return localStorage.getItem('token') || sessionStorage.getItem('token') || '';
    }
});
