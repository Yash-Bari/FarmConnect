// Authentication related JavaScript for FarmConnect

// Function to show toast notifications
function showToast(message, type = 'success') {
    // Check if toast container exists, if not create it
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.id = toastId;
    
    // Create toast content
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Handle login form validation
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Basic validation
            if (!email || !password) {
                e.preventDefault();
                showToast('Please enter both email and password.', 'danger');
                return false;
            }
            
            // Form submission will proceed naturally if all validations pass
            return true;
        });
    }
    
    // Handle registration form validation
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        // Client-side validation handling - don't prevent default form submission
        registerForm.addEventListener('submit', function(e) {
            const email = document.getElementById('email').value;
            const fullName = document.getElementById('full_name').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            // Basic validation
            if (!email || !fullName || !password || !confirmPassword) {
                e.preventDefault();
                showToast('Please fill in all required fields.', 'danger');
                return false;
            }
            
            if (password !== confirmPassword) {
                e.preventDefault();
                showToast('Passwords do not match.', 'danger');
                return false;
            }
            
            if (password.length < 6) {
                e.preventDefault();
                showToast('Password must be at least 6 characters long.', 'danger');
                return false;
            }
            
            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                e.preventDefault();
                showToast('Please enter a valid email address.', 'danger');
                return false;
            }
            
            // Form submission will proceed naturally if all validations pass
            return true;
        });
    }
    
    // Handle profile form submission
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            // Form will be validated on the server-side
            // This is just for any client-side enhancements
            
            const userType = profileForm.dataset.userType;
            
            if (userType === 'farmer') {
                const farmName = document.getElementById('farm_name').value;
                const farmLocation = document.getElementById('farm_location').value;
                const paymentInfo = document.getElementById('payment_info').value;
                
                if (!farmName || !farmLocation || !paymentInfo) {
                    e.preventDefault();
                    showToast('Please fill in all required fields.', 'danger');
                    return;
                }
            } else if (userType === 'customer') {
                const deliveryAddress = document.getElementById('delivery_address').value;
                
                if (!deliveryAddress) {
                    e.preventDefault();
                    showToast('Please enter your delivery address.', 'danger');
                    return;
                }
            }
        });
    }
    
    // Handle password toggle visibility
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const passwordInput = document.getElementById(targetId);
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                this.innerHTML = '<i class="bi bi-eye-slash"></i>';
            } else {
                passwordInput.type = 'password';
                this.innerHTML = '<i class="bi bi-eye"></i>';
            }
        });
    });
    
    // Handle user type selection in registration
    const userTypeRadios = document.querySelectorAll('input[name="user_type"]');
    userTypeRadios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            const userTypeInfo = document.getElementById('user-type-info');
            if (userTypeInfo) {
                if (this.value === 'farmer') {
                    userTypeInfo.textContent = 'As a farmer, you can list your crops for sale and manage orders from customers.';
                } else {
                    userTypeInfo.textContent = 'As a customer, you can browse and purchase crops directly from farmers.';
                }
            }
        });
    });
    
    // Automatically set JWT token in auth header for API requests
    function getToken() {
        return localStorage.getItem('token') || sessionStorage.getItem('token') || '';
    }
    
    // Function to log out user
    function logoutUser() {
        localStorage.removeItem('token');
        sessionStorage.removeItem('token');
        window.location.href = '/logout';
    }
    
    // Add logout functionality to logout buttons
    const logoutBtns = document.querySelectorAll('.logout-btn');
    logoutBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            logoutUser();
        });
    });
});
