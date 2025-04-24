// Farmer-specific JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Handle crop deletion
    const deleteCropBtns = document.querySelectorAll('.delete-crop-btn');
    deleteCropBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const cropId = this.dataset.cropId;
            const cropName = this.dataset.cropName;
            
            if (confirm(`Are you sure you want to delete ${cropName}? This action cannot be undone.`)) {
                fetch(`/farmer/crops/delete/${cropId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getToken()}`
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showToast(data.message, 'success');
                        // Remove the crop row from the table
                        const cropRow = document.getElementById(`crop-${cropId}`);
                        if (cropRow) {
                            cropRow.remove();
                        }
                    } else {
                        showToast(data.message, 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error deleting crop:', error);
                    showToast('An error occurred. Please try again.', 'danger');
                });
            }
        });
    });
    
    // Handle order status updates
    const orderStatusForms = document.querySelectorAll('.order-status-form');
    orderStatusForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const orderId = this.dataset.orderId;
            const statusSelect = this.querySelector('select[name="status"]');
            const status = statusSelect.value;
            
            fetch(`/farmer/orders/update/${orderId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': `Bearer ${getToken()}`
                },
                body: `status=${status}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    
                    // Update status badge
                    const statusBadge = document.querySelector(`#order-${orderId} .status-badge`);
                    if (statusBadge) {
                        statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                        
                        // Update badge color
                        statusBadge.className = 'badge status-badge';
                        switch (status) {
                            case 'pending':
                                statusBadge.classList.add('bg-warning');
                                break;
                            case 'accepted':
                                statusBadge.classList.add('bg-primary');
                                break;
                            case 'processing':
                                statusBadge.classList.add('bg-info');
                                break;
                            case 'shipped':
                                statusBadge.classList.add('bg-secondary');
                                break;
                            case 'delivered':
                                statusBadge.classList.add('bg-success');
                                break;
                            case 'rejected':
                                statusBadge.classList.add('bg-danger');
                                break;
                        }
                    }
                } else {
                    showToast(data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error updating order status:', error);
                showToast('An error occurred. Please try again.', 'danger');
            });
        });
    });
    
    // Multi-image upload preview for crop form
    const cropImagesInput = document.getElementById('images');
    if (cropImagesInput) {
        cropImagesInput.addEventListener('change', function() {
            const previewContainer = document.getElementById('image-previews');
            previewContainer.innerHTML = '';
            
            if (this.files.length > 0) {
                for (let i = 0; i < this.files.length; i++) {
                    const file = this.files[i];
                    if (!file.type.match('image.*')) {
                        continue;
                    }
                    
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const previewDiv = document.createElement('div');
                        previewDiv.className = 'col-md-4 mb-2';
                        previewDiv.innerHTML = `
                            <div class="preview-image-container">
                                <img src="${e.target.result}" class="img-fluid rounded" alt="Crop image preview">
                            </div>
                        `;
                        previewContainer.appendChild(previewDiv);
                    }
                    reader.readAsDataURL(file);
                }
            }
        });
    }
    
    // Crop form validation
    const cropForm = document.getElementById('crop-form');
    if (cropForm) {
        cropForm.addEventListener('submit', function(e) {
            const name = document.getElementById('name').value;
            const price = document.getElementById('price').value;
            const quantity = document.getElementById('quantity').value;
            const description = document.getElementById('description').value;
            
            if (!name || !price || !quantity || !description) {
                e.preventDefault();
                showToast('Please fill in all required fields.', 'danger');
                return;
            }
            
            if (parseFloat(price) <= 0) {
                e.preventDefault();
                showToast('Price must be greater than zero.', 'danger');
                return;
            }
            
            if (parseFloat(quantity) <= 0) {
                e.preventDefault();
                showToast('Quantity must be greater than zero.', 'danger');
                return;
            }
        });
    }
    
    // Dashboard charts initialization
    const revenueChart = document.getElementById('revenue-chart');
    if (revenueChart) {
        // Sample data - in a real app, this would come from the backend
        new Chart(revenueChart, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Revenue',
                    data: [1200, 1900, 1500, 2500, 2200, 3000],
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    tension: 0.3
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value;
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return '₹' + context.parsed.y;
                            }
                        }
                    }
                }
            }
        });
    }
    
    const ordersChart = document.getElementById('orders-chart');
    if (ordersChart) {
        // Sample data - in a real app, this would come from the backend
        new Chart(ordersChart, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Orders',
                    data: [5, 8, 6, 12, 9, 14],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    // Function to get JWT token
    function getToken() {
        return localStorage.getItem('token') || sessionStorage.getItem('token') || '';
    }
});
