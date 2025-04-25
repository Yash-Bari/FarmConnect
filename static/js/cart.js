// Shopping cart functionality

// Function to update cart count badge
function updateCartCount() {
    fetch('/api/cart/info')
        .then(response => response.json())
        .then(data => {
            const cartCount = data.cart_count || 0;
            const cartBadge = document.querySelector('#cart-count');
            if (cartBadge) {
                cartBadge.textContent = cartCount;
                cartBadge.style.display = cartCount > 0 ? 'inline' : 'none';
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
}

// Function to get CSRF token
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Function to remove item from cart
function removeFromCart(cropId) {
    if (!confirm('Are you sure you want to remove this item from your cart?')) {
        return;
    }
    
    fetch('/api/cart/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ crop_id: cropId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove item from UI
            const cartItem = document.getElementById(`cart-item-${cropId}`);
            if (cartItem) {
                cartItem.remove();
            }
            
            // Update cart count
            updateCartCount();
            
            // Update cart total
            const cartTotal = document.getElementById('cart-total');
            if (cartTotal && data.cart_total) {
                cartTotal.textContent = `₹${data.cart_total.toFixed(2)}`;
            }
            
            // Check if cart is empty
            const cartItems = document.querySelectorAll('.cart-item');
            if (cartItems.length === 0) {
                window.location.reload(); // Reload to show empty cart message
            }
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error removing item from cart');
    });
}

// Initialize cart functionality
document.addEventListener('DOMContentLoaded', function() {
    // Update initial cart count
    updateCartCount();
    
    // Handle remove item buttons
    document.querySelectorAll('.remove-cart-item').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const cropId = this.dataset.cropId;
            removeFromCart(cropId);
        });
    });
});
