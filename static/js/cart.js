// Shopping cart functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize cart if not exists
    if (!localStorage.getItem('cart')) {
        localStorage.setItem('cart', JSON.stringify([]));
    }
    
    // Update cart count in UI
    updateCartCount();
    
    // Add to cart button functionality
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    addToCartButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const cropId = this.dataset.cropId;
            const cropName = this.dataset.cropName;
            const cropPrice = parseFloat(this.dataset.cropPrice);
            const quantityInput = document.querySelector(`input[data-crop-id="${cropId}"]`);
            
            if (!quantityInput) {
                console.error('Quantity input not found');
                return;
            }
            
            const quantity = parseFloat(quantityInput.value);
            
            if (!quantity || quantity <= 0) {
                showToast('Please enter a valid quantity', 'danger');
                return;
            }
            
            // Get current cart
            const cart = JSON.parse(localStorage.getItem('cart')) || [];
            
            // Check if item already in cart
            const existingItemIndex = cart.findIndex(item => item.cropId === cropId);
            
            if (existingItemIndex !== -1) {
                // Update quantity if item exists
                cart[existingItemIndex].quantity = quantity;
            } else {
                // Add new item
                cart.push({
                    cropId: cropId,
                    name: cropName,
                    price: cropPrice,
                    quantity: quantity
                });
            }
            
            // Save cart back to localStorage
            localStorage.setItem('cart', JSON.stringify(cart));
            
            // Update UI
            updateCartCount();
            showToast(`Added ${cropName} to cart`, 'success');
        });
    });
    
    // Remove from cart button functionality
    const removeFromCartButtons = document.querySelectorAll('.remove-from-cart-btn');
    removeFromCartButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const cropId = this.dataset.cropId;
            
            // Get current cart
            let cart = JSON.parse(localStorage.getItem('cart')) || [];
            
            // Remove item
            cart = cart.filter(item => item.cropId !== cropId);
            
            // Save cart back to localStorage
            localStorage.setItem('cart', JSON.stringify(cart));
            
            // Update UI
            const cartItemRow = document.getElementById(`cart-item-${cropId}`);
            if (cartItemRow) {
                cartItemRow.remove();
            }
            
            updateCartCount();
            updateCartTotal();
            
            showToast('Item removed from cart', 'info');
            
            // If cart is empty, show empty state
            if (cart.length === 0) {
                const cartTable = document.querySelector('.cart-table');
                const emptyCartMessage = document.querySelector('.empty-cart-message');
                
                if (cartTable) cartTable.style.display = 'none';
                if (emptyCartMessage) emptyCartMessage.style.display = 'block';
            }
        });
    });
    
    // Cart quantity change functionality
    const cartQuantityInputs = document.querySelectorAll('.cart-quantity');
    cartQuantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const cropId = this.dataset.cropId;
            const quantity = parseFloat(this.value);
            
            if (!quantity || quantity <= 0) {
                showToast('Please enter a valid quantity', 'danger');
                // Reset to previous value
                const cart = JSON.parse(localStorage.getItem('cart')) || [];
                const item = cart.find(item => item.cropId === cropId);
                if (item) {
                    this.value = item.quantity;
                }
                return;
            }
            
            // Get current cart
            const cart = JSON.parse(localStorage.getItem('cart')) || [];
            
            // Update quantity
            const itemIndex = cart.findIndex(item => item.cropId === cropId);
            if (itemIndex !== -1) {
                cart[itemIndex].quantity = quantity;
                
                // Update subtotal in UI
                const price = cart[itemIndex].price;
                const subtotal = price * quantity;
                const subtotalElement = document.getElementById(`subtotal-${cropId}`);
                if (subtotalElement) {
                    subtotalElement.textContent = formatCurrency(subtotal);
                }
            }
            
            // Save cart back to localStorage
            localStorage.setItem('cart', JSON.stringify(cart));
            
            // Update total
            updateCartTotal();
        });
    });
    
    // Clear cart button functionality
    const clearCartButton = document.getElementById('clear-cart-btn');
    if (clearCartButton) {
        clearCartButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (confirm('Are you sure you want to clear your cart?')) {
                // Clear cart in localStorage
                localStorage.setItem('cart', JSON.stringify([]));
                
                // Update UI
                const cartTable = document.querySelector('.cart-table');
                const emptyCartMessage = document.querySelector('.empty-cart-message');
                
                if (cartTable) cartTable.style.display = 'none';
                if (emptyCartMessage) emptyCartMessage.style.display = 'block';
                
                updateCartCount();
                
                showToast('Cart cleared', 'info');
            }
        });
    }
    
    // Function to update cart count badge
    function updateCartCount() {
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        const cartCountElement = document.querySelector('.cart-count');
        
        if (cartCountElement) {
            const itemCount = cart.length;
            cartCountElement.textContent = itemCount;
            
            if (itemCount > 0) {
                cartCountElement.style.display = 'inline-block';
            } else {
                cartCountElement.style.display = 'none';
            }
        }
    }
    
    // Function to update cart total
    function updateCartTotal() {
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        const totalElement = document.getElementById('cart-total');
        
        if (totalElement) {
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            totalElement.textContent = formatCurrency(total);
        }
    }
    
    // Function to format currency
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount);
    }
});
