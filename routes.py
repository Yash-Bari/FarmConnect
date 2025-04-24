from flask import render_template, request, redirect, url_for, flash, jsonify, abort, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import User, FarmerProfile, CustomerProfile, Crop, Order, OrderItem, Payment, Notification
from forms import (LoginForm, RegisterForm, FarmerProfileForm, CustomerProfileForm, 
                  CropForm, OrderStatusForm, PaymentForm)
from helpers import save_file, allowed_file, generate_unique_filename
import os
import json
from datetime import datetime, timedelta
import uuid

# Main routes
@app.route('/')
def index():
    featured_crops = Crop.query.filter_by(is_available=True).order_by(Crop.created_at.desc()).limit(6).all()
    return render_template('index.html', featured_crops=featured_crops)

# Farmer routes
@app.route('/farmer/dashboard')
@login_required
def farmer_dashboard():
    user = current_user
    
    if not user or user.user_type != 'farmer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    if not user.farmer_profile:
        flash('Please complete your farmer profile.', 'warning')
        return redirect(url_for('farmer_profile'))
    
    # Get statistics
    crops_count = Crop.query.filter_by(farmer_id=user.farmer_profile.id).count()
    orders = Order.query.filter_by(farmer_id=user.farmer_profile.id).all()
    pending_orders = [order for order in orders if order.status == 'pending']
    recent_orders = Order.query.filter_by(farmer_id=user.farmer_profile.id).order_by(Order.order_date.desc()).limit(5).all()
    
    # Calculate total revenue
    total_revenue = sum([order.total_amount for order in orders if order.status in ['delivered', 'shipped']])
    
    # Get recent notifications
    notifications = Notification.query.filter_by(user_id=user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('farmer/dashboard.html', 
                          user=user,
                          crops_count=crops_count,
                          orders_count=len(orders),
                          pending_orders=len(pending_orders),
                          total_revenue=total_revenue,
                          recent_orders=recent_orders,
                          notifications=notifications)

@app.route('/farmer/crops')
@jwt_required()
def farmer_crops():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'farmer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    crops = Crop.query.filter_by(farmer_id=user.farmer_profile.id).order_by(Crop.created_at.desc()).all()
    return render_template('farmer/crops.html', crops=crops, user=user)

@app.route('/farmer/crops/new', methods=['GET', 'POST'])
@jwt_required()
def new_crop():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'farmer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    form = CropForm()
    
    if form.validate_on_submit():
        # Handle image upload
        image_paths = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = save_file(file, app.config['UPLOAD_FOLDER'])
                    image_paths.append(filename)
        
        # Create new crop
        crop = Crop(
            farmer_id=user.farmer_profile.id,
            name=form.name.data,
            category=form.category.data,
            price=form.price.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            description=form.description.data,
            harvest_date=form.harvest_date.data,
            is_available=form.is_available.data,
            images=','.join(image_paths) if image_paths else None
        )
        
        db.session.add(crop)
        db.session.commit()
        
        flash('New crop added successfully!', 'success')
        return redirect(url_for('farmer_crops'))
    
    return render_template('farmer/crop_form.html', form=form, user=user, title='Add New Crop')

@app.route('/farmer/crops/edit/<int:crop_id>', methods=['GET', 'POST'])
@jwt_required()
def edit_crop(crop_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'farmer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    crop = Crop.query.get_or_404(crop_id)
    
    # Check if the crop belongs to the farmer
    if crop.farmer_id != user.farmer_profile.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('farmer_crops'))
    
    form = CropForm(obj=crop)
    
    if form.validate_on_submit():
        # Update crop details
        crop.name = form.name.data
        crop.category = form.category.data
        crop.price = form.price.data
        crop.quantity = form.quantity.data
        crop.unit = form.unit.data
        crop.description = form.description.data
        crop.harvest_date = form.harvest_date.data
        crop.is_available = form.is_available.data
        
        # Handle image upload
        if 'images' in request.files and request.files['images'].filename:
            files = request.files.getlist('images')
            image_paths = []
            for file in files:
                if file and allowed_file(file.filename):
                    filename = save_file(file, app.config['UPLOAD_FOLDER'])
                    image_paths.append(filename)
            
            if image_paths:
                crop.images = ','.join(image_paths)
        
        db.session.commit()
        flash('Crop updated successfully!', 'success')
        return redirect(url_for('farmer_crops'))
    
    return render_template('farmer/crop_form.html', form=form, user=user, crop=crop, title='Edit Crop')

@app.route('/farmer/crops/delete/<int:crop_id>', methods=['POST'])
@jwt_required()
def delete_crop(crop_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'farmer':
        return jsonify({'success': False, 'message': 'Unauthorized access.'})
    
    crop = Crop.query.get_or_404(crop_id)
    
    # Check if the crop belongs to the farmer
    if crop.farmer_id != user.farmer_profile.id:
        return jsonify({'success': False, 'message': 'Unauthorized access.'})
    
    db.session.delete(crop)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Crop deleted successfully!'})

@app.route('/farmer/orders')
@jwt_required()
def farmer_orders():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'farmer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(farmer_id=user.farmer_profile.id).order_by(Order.order_date.desc()).all()
    return render_template('farmer/orders.html', orders=orders, user=user)

@app.route('/farmer/orders/update/<int:order_id>', methods=['POST'])
@jwt_required()
def update_order_status(order_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'farmer':
        return jsonify({'success': False, 'message': 'Unauthorized access.'})
    
    order = Order.query.get_or_404(order_id)
    
    # Check if the order belongs to the farmer
    if order.farmer_id != user.farmer_profile.id:
        return jsonify({'success': False, 'message': 'Unauthorized access.'})
    
    status = request.form.get('status')
    if not status:
        return jsonify({'success': False, 'message': 'Status is required.'})
    
    order.status = status
    
    # If status is accepted, set estimated delivery
    if status == 'accepted':
        order.estimated_delivery = datetime.utcnow() + timedelta(days=3)
    
    db.session.commit()
    
    # Create notification for customer
    notification = Notification(
        user_id=order.customer.user_id,
        message=f'Your order #{order.id} status has been updated to: {status.capitalize()}',
        related_type='order',
        related_id=order.id
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Order status updated successfully!'})

# Customer routes
@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    user = current_user
    
    if not user or user.user_type != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    if not user.customer_profile:
        flash('Please complete your customer profile.', 'warning')
        return redirect(url_for('customer_profile'))
    
    # Get recent orders
    recent_orders = Order.query.filter_by(customer_id=user.customer_profile.id).order_by(Order.order_date.desc()).limit(5).all()
    
    # Get recent notifications
    notifications = Notification.query.filter_by(user_id=user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('customer/dashboard.html', 
                          user=user,
                          recent_orders=recent_orders,
                          notifications=notifications)

@app.route('/marketplace')
def marketplace():
    # Get filter parameters
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort_by', 'created_at')
    search = request.args.get('search', '')
    
    # Base query
    query = Crop.query.filter_by(is_available=True)
    
    # Apply category filter
    if category != 'all':
        query = query.filter_by(category=category)
    
    # Apply search
    if search:
        query = query.filter(Crop.name.ilike(f'%{search}%') | Crop.description.ilike(f'%{search}%'))
    
    # Apply sorting
    if sort_by == 'price_low':
        query = query.order_by(Crop.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Crop.price.desc())
    else:  # Default: created_at
        query = query.order_by(Crop.created_at.desc())
    
    crops = query.all()
    
    # Get all categories for filter dropdown
    categories = [c[0] for c in db.session.query(Crop.category).distinct()]
    
    # Check if user is logged in
    user_id = get_jwt_identity() if request.headers.get('Authorization') else None
    user = User.query.get(user_id) if user_id else None
    
    return render_template('customer/marketplace.html', 
                          crops=crops, 
                          categories=categories,
                          category=category,
                          sort_by=sort_by,
                          search=search,
                          user=user)

@app.route('/crop/<int:crop_id>')
def crop_detail(crop_id):
    crop = Crop.query.get_or_404(crop_id)
    farmer = FarmerProfile.query.get(crop.farmer_id)
    
    # Check if user is logged in
    user_id = get_jwt_identity() if request.headers.get('Authorization') else None
    user = User.query.get(user_id) if user_id else None
    
    return render_template('customer/crop_detail.html', crop=crop, farmer=farmer, user=user)

@app.route('/customer/cart')
@jwt_required()
def cart():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    # Get cart from session
    cart_items = session.get('cart', [])
    
    # Fetch crop details for each item in cart
    cart_data = []
    for item in cart_items:
        crop = Crop.query.get(item['crop_id'])
        if crop and crop.is_available:
            farmer = FarmerProfile.query.get(crop.farmer_id)
            cart_data.append({
                'crop_id': crop.id,
                'name': crop.name,
                'farmer_name': farmer.farm_name,
                'price': crop.price,
                'quantity': item['quantity'],
                'unit': crop.unit,
                'subtotal': crop.price * item['quantity'],
                'farmer_id': farmer.id
            })
    
    # Group by farmer
    farmers = {}
    for item in cart_data:
        if item['farmer_id'] not in farmers:
            farmers[item['farmer_id']] = {
                'farmer_id': item['farmer_id'],
                'farmer_name': item['farmer_name'],
                'items': [],
                'total': 0
            }
        farmers[item['farmer_id']]['items'].append(item)
        farmers[item['farmer_id']]['total'] += item['subtotal']
    
    return render_template('customer/cart.html', farmers=farmers.values(), user=user)

@app.route('/api/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'customer':
        return jsonify({'success': False, 'message': 'Unauthorized access.'})
    
    data = request.json
    crop_id = data.get('crop_id')
    quantity = float(data.get('quantity', 1))
    
    if not crop_id or not quantity:
        return jsonify({'success': False, 'message': 'Invalid request data.'})
    
    # Validate crop exists and is available
    crop = Crop.query.get(crop_id)
    if not crop or not crop.is_available:
        return jsonify({'success': False, 'message': 'Crop not available.'})
    
    # Check quantity
    if quantity > crop.quantity:
        return jsonify({'success': False, 'message': 'Requested quantity exceeds available stock.'})
    
    # Initialize cart if not exists
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if item already in cart
    cart = session['cart']
    item_found = False
    
    for item in cart:
        if item['crop_id'] == crop_id:
            item['quantity'] = quantity
            item_found = True
            break
    
    if not item_found:
        cart.append({'crop_id': crop_id, 'quantity': quantity})
    
    session['cart'] = cart
    
    return jsonify({'success': True, 'message': 'Item added to cart.', 'cart_count': len(cart)})

@app.route('/api/cart/remove', methods=['POST'])
@jwt_required()
def remove_from_cart():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'customer':
        return jsonify({'success': False, 'message': 'Unauthorized access.'})
    
    data = request.json
    crop_id = data.get('crop_id')
    
    if not crop_id:
        return jsonify({'success': False, 'message': 'Invalid request data.'})
    
    # Remove item from cart
    if 'cart' in session:
        cart = session['cart']
        session['cart'] = [item for item in cart if item['crop_id'] != crop_id]
    
    return jsonify({'success': True, 'message': 'Item removed from cart.', 'cart_count': len(session.get('cart', []))})

@app.route('/api/cart/update', methods=['POST'])
@jwt_required()
def update_cart():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'customer':
        return jsonify({'success': False, 'message': 'Unauthorized access.'})
    
    data = request.json
    crop_id = data.get('crop_id')
    quantity = float(data.get('quantity', 1))
    
    if not crop_id or not quantity:
        return jsonify({'success': False, 'message': 'Invalid request data.'})
    
    # Validate crop exists and is available
    crop = Crop.query.get(crop_id)
    if not crop or not crop.is_available:
        return jsonify({'success': False, 'message': 'Crop not available.'})
    
    # Check quantity
    if quantity > crop.quantity:
        return jsonify({'success': False, 'message': 'Requested quantity exceeds available stock.'})
    
    # Update quantity in cart
    if 'cart' in session:
        cart = session['cart']
        for item in cart:
            if item['crop_id'] == crop_id:
                item['quantity'] = quantity
                break
        session['cart'] = cart
    
    return jsonify({'success': True, 'message': 'Cart updated.', 'cart_count': len(session.get('cart', []))})

@app.route('/customer/checkout', methods=['GET', 'POST'])
@jwt_required()
def checkout():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    if not user.customer_profile:
        flash('Please complete your profile before checkout.', 'warning')
        return redirect(url_for('customer_profile'))
    
    # Get cart from session
    cart_items = session.get('cart', [])
    
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('marketplace'))
    
    # Group items by farmer
    farmer_orders = {}
    
    for item in cart_items:
        crop = Crop.query.get(item['crop_id'])
        if crop and crop.is_available:
            farmer_id = crop.farmer_id
            
            if farmer_id not in farmer_orders:
                farmer = FarmerProfile.query.get(farmer_id)
                farmer_orders[farmer_id] = {
                    'farmer': farmer,
                    'items': [],
                    'total': 0
                }
            
            item_total = crop.price * item['quantity']
            farmer_orders[farmer_id]['items'].append({
                'crop': crop,
                'quantity': item['quantity'],
                'price': crop.price,
                'subtotal': item_total
            })
            farmer_orders[farmer_id]['total'] += item_total
    
    if request.method == 'POST':
        # Process the order
        for farmer_id, order_data in farmer_orders.items():
            # Create order
            order = Order(
                customer_id=user.customer_profile.id,
                farmer_id=farmer_id,
                status='pending',
                total_amount=order_data['total'],
                delivery_address=user.customer_profile.delivery_address
            )
            db.session.add(order)
            db.session.flush()  # Get the order ID
            
            # Create order items
            for item in order_data['items']:
                order_item = OrderItem(
                    order_id=order.id,
                    crop_id=item['crop'].id,
                    quantity=item['quantity'],
                    price_per_unit=item['price'],
                    subtotal=item['subtotal']
                )
                db.session.add(order_item)
                
                # Reduce crop quantity
                crop = item['crop']
                crop.quantity -= item['quantity']
                if crop.quantity <= 0:
                    crop.is_available = False
            
            # Create payment record
            payment = Payment(
                order_id=order.id,
                amount=order_data['total'],
                payment_method=user.customer_profile.preferred_payment,
                status='pending'
            )
            db.session.add(payment)
            
            # Create notification for farmer
            notification = Notification(
                user_id=order_data['farmer'].user_id,
                message=f'New order received from {user.full_name}.',
                related_type='order',
                related_id=order.id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        # Clear cart
        session.pop('cart', None)
        
        flash('Your order has been placed successfully!', 'success')
        return redirect(url_for('customer_orders'))
    
    return render_template('customer/checkout.html', 
                          farmer_orders=farmer_orders,
                          user=user,
                          customer_profile=user.customer_profile)

@app.route('/customer/orders')
@jwt_required()
def customer_orders():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(customer_id=user.customer_profile.id).order_by(Order.order_date.desc()).all()
    return render_template('customer/orders.html', orders=orders, user=user)

@app.route('/customer/orders/<int:order_id>/payment', methods=['GET', 'POST'])
@jwt_required()
def order_payment(order_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    order = Order.query.get_or_404(order_id)
    
    # Check if order belongs to user
    if order.customer_id != user.customer_profile.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('customer_orders'))
    
    payment = Payment.query.filter_by(order_id=order.id).first()
    form = PaymentForm()
    
    if form.validate_on_submit():
        # Handle screenshot upload
        if 'payment_screenshot' in request.files:
            file = request.files['payment_screenshot']
            if file and allowed_file(file.filename):
                filename = save_file(file, app.config['UPLOAD_FOLDER'])
                payment.screenshot = filename
                payment.status = 'pending'
                db.session.commit()
                
                # Create notification for farmer
                notification = Notification(
                    user_id=order.farmer.user_id,
                    message=f'Payment screenshot uploaded for order #{order.id}.',
                    related_type='payment',
                    related_id=payment.id
                )
                db.session.add(notification)
                db.session.commit()
                
                flash('Payment screenshot uploaded successfully!', 'success')
                return redirect(url_for('customer_orders'))
        else:
            flash('Payment screenshot is required.', 'danger')
    
    # Get farmer payment details
    farmer = FarmerProfile.query.get(order.farmer_id)
    
    return render_template('customer/payment.html', 
                          order=order, 
                          payment=payment, 
                          farmer=farmer,
                          form=form,
                          user=user)

# Notification routes
@app.route('/api/notifications/read/<int:notification_id>', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    user_id = get_jwt_identity()
    
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if notification belongs to user
    if notification.user_id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized access.'})
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Notification marked as read.'})

@app.route('/api/notifications/read/all', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    user_id = get_jwt_identity()
    
    notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
    for notification in notifications:
        notification.is_read = True
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'All notifications marked as read.'})
