// Authentication related JavaScript for FarmConnect

document.addEventListener('DOMContentLoaded', function() {
    // Handle login form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Basic validation
            if (!email || !password) {
                showToast('Please enter both email and password.', 'danger');
                return;
            }
            
            // Submit form normally (server-side handling)
            loginForm.submit();
        });
    }
    
    // Handle registration form submission
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const fullName = document.getElementById('full_name').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            // Basic validation
            if (!email || !fullName || !password || !confirmPassword) {
                showToast('Please fill in all required fields.', 'danger');
                return;
            }
            
            if (password !== confirmPassword) {
                showToast('Passwords do not match.', 'danger');
                return;
            }
            
            if (password.length < 6) {
                showToast('Password must be at least 6 characters long.', 'danger');
                return;
            }
            
            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                showToast('Please enter a valid email address.', 'danger');
                return;
            }
            
            // Submit form normally (server-side handling)
            registerForm.submit();
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
