// Main JavaScript for FarmConnect

// Wait for DOM to be loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Handle file input preview for profile pictures and crop images
    const fileInputs = document.querySelectorAll('.custom-file-input');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0].name;
            const nextSibling = e.target.nextElementSibling;
            nextSibling.innerText = fileName;
            
            // Preview image if it's an image input
            if (this.dataset.preview) {
                const previewElement = document.getElementById(this.dataset.preview);
                if (previewElement) {
                    const file = this.files[0];
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        previewElement.src = e.target.result;
                    };
                    
                    reader.readAsDataURL(file);
                }
            }
        });
    });
    
    // Handle notification read status
    const notificationLinks = document.querySelectorAll('.notification-item');
    notificationLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const notificationId = this.dataset.id;
            if (notificationId) {
                fetch(`/api/notifications/read/${notificationId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getToken()}`
                    }
                }).then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.classList.remove('unread');
                    }
                }).catch(error => console.error('Error marking notification as read:', error));
            }
        });
    });
    
    // Handle "Mark all as read" for notifications
    const markAllReadBtn = document.getElementById('mark-all-read');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            fetch('/api/notifications/read/all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getToken()}`
                }
            }).then(response => response.json())
            .then(data => {
                if (data.success) {
                    const notifications = document.querySelectorAll('.notification-item.unread');
                    notifications.forEach(function(notification) {
                        notification.classList.remove('unread');
                    });
                    
                    // Update notification badge
                    const badge = document.querySelector('.notification-badge');
                    if (badge) {
                        badge.textContent = '0';
                        badge.style.display = 'none';
                    }
                }
            }).catch(error => console.error('Error marking all notifications as read:', error));
        });
    }
    
    // Function to get JWT token from localStorage
    function getToken() {
        return localStorage.getItem('token') || '';
    }
    
    // Setup AJAX for CSRF token
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
    
    // Add CSRF token to all AJAX requests
    if (document.querySelector('meta[name="csrf-token"]')) {
        const csrfToken = getCsrfToken();
        if (csrfToken) {
            document.querySelectorAll('form').forEach(form => {
                if (!form.querySelector('input[name="csrf_token"]')) {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'csrf_token';
                    input.value = csrfToken;
                    form.appendChild(input);
                }
            });
        }
    }
    
    // Handle quantity input restrictions
    const quantityInputs = document.querySelectorAll('input[type="number"].quantity-input');
    quantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const min = parseFloat(this.min) || 0;
            const max = parseFloat(this.max) || Infinity;
            let value = parseFloat(this.value) || 0;
            
            if (value < min) {
                value = min;
            } else if (value > max) {
                value = max;
            }
            
            this.value = value;
        });
    });
    
    // Handle search form in marketplace
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('search-input');
            if (!searchInput.value.trim()) {
                e.preventDefault();
            }
        });
    }
});

// Show toast notifications
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
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

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

// Format datetime
function formatDateTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}
