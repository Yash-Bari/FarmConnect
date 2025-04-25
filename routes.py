from flask import render_template, request, redirect, url_for, flash, jsonify, abort, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db, csrf
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

@app.route('/api/cart/remove', methods=['POST'])
@csrf.exempt
def remove_from_cart():
    """Remove an item from the shopping cart"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login first'})
        
    if current_user.user_type != 'customer':
        return jsonify({'success': False, 'message': 'Only customers can modify cart'})
    
    try:
        data = request.get_json()
        if not data:
            raise ValueError('No data provided')
            
        crop_id = int(data.get('crop_id'))
        if not crop_id:
            raise ValueError('No crop ID provided')
            
        if 'cart' not in session:
            session['cart'] = []
            
        # Remove item from cart
        cart = session['cart']
        cart = [item for item in cart if item.get('crop_id') != crop_id]
        
        session['cart'] = cart
        session.modified = True
        
        # Get updated cart info
        cart_count = len(cart)
        cart_total = sum(item['quantity'] * Crop.query.get(item['crop_id']).price for item in cart)
        
        return jsonify({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': cart_count,
            'cart_total': cart_total
        })
        
    except Exception as e:
        app.logger.error(f'Error removing from cart: {e}')
        return jsonify({'success': False, 'message': str(e)})

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
@login_required
def farmer_crops():
    user = current_user
    
    if not user or user.user_type != 'farmer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    crops = Crop.query.filter_by(farmer_id=user.farmer_profile.id).order_by(Crop.created_at.desc()).all()
    return render_template('farmer/crops.html', crops=crops, user=user)

@app.route('/farmer/crops/new', methods=['GET', 'POST'])
@login_required
def new_crop():
    user = current_user
    
    if not user or user.user_type != 'farmer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    form = CropForm()
    
    if form.validate_on_submit():
        app.logger.info('Form validated successfully')
        # Handle image upload
        image_paths = []
        try:
            if form.images.data:
                app.logger.info('Image data found')
                files = request.files.getlist('images')
                app.logger.info(f'Found {len(files)} files')
                for file in files:
                    if file and allowed_file(file.filename):
                        app.logger.info(f'Processing file: {file.filename}')
                        filename = save_file(file, app.config['UPLOAD_FOLDER'])
                        app.logger.info(f'File saved as: {filename}')
                        if filename:
                            image_paths.append(filename)
            else:
                app.logger.warning('No image data found in form')
        except Exception as e:
            app.logger.error(f'Error processing images: {str(e)}')
            flash('Error processing images. Please try again.', 'danger')
            return render_template('farmer/crop_form.html', form=form, user=user, title='Add New Crop')
        
        try:
            # Create new crop
            app.logger.info('Creating new crop with data:')
            app.logger.info(f'Farmer ID: {user.farmer_profile.id}')
            app.logger.info(f'Name: {form.name.data}')
            app.logger.info(f'Category: {form.category.data}')
            app.logger.info(f'Images: {image_paths}')
            
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
            app.logger.info(f'Crop saved successfully with ID: {crop.id}')
        except Exception as e:
            app.logger.error(f'Error saving crop: {str(e)}')
            db.session.rollback()
            flash('Error saving crop. Please try again.', 'danger')
            return render_template('farmer/crop_form.html', form=form, user=user, title='Add New Crop')
        
        flash('New crop added successfully!', 'success')
        return redirect(url_for('farmer_crops'))
    
    return render_template('farmer/crop_form.html', form=form, user=user, title='Add New Crop')

@app.route('/farmer/crops/edit/<int:crop_id>', methods=['GET', 'POST'])
@login_required
def edit_crop(crop_id):
    user = current_user
    
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
@login_required
def delete_crop(crop_id):
    user = current_user
    
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
@login_required
def farmer_orders():
    user = current_user
    
    if not user or user.user_type != 'farmer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(farmer_id=user.farmer_profile.id).order_by(Order.order_date.desc()).all()
    return render_template('farmer/orders.html', orders=orders, user=user)

@app.route('/farmer/orders/update/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    user = current_user
    
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
    
    # Get featured crops for dashboard
    featured_crops = Crop.query.filter_by(is_available=True).order_by(Crop.created_at.desc()).limit(6).all()
    
    return render_template('customer/dashboard.html', 
                          user=user,
                          recent_orders=recent_orders,
                          notifications=notifications,
                          featured_crops=featured_crops)

@app.route('/marketplace')
def marketplace():
    # Get filter parameters
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort_by', 'created_at')
    search = request.args.get('search', '')
    farmer_id = request.args.get('farmer')
    
    # Base query
    query = Crop.query.filter_by(is_available=True)
    
    # Apply category filter
    if category != 'all':
        query = query.filter_by(category=category)
    
    # Apply farmer filter
    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)
        farmer = FarmerProfile.query.get_or_404(farmer_id)
    else:
        farmer = None
    
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
    
    # Get current user for template
    user = current_user if current_user.is_authenticated else None
    
    return render_template('customer/marketplace.html', 
                          crops=crops, 
                          categories=categories,
                          category=category,
                          sort_by=sort_by,
                          search=search,
                          user=user,
                          farmer=farmer)

@app.route('/crop/<int:crop_id>')
def crop_detail(crop_id):
    """Display details of a specific crop"""
    crop = Crop.query.get_or_404(crop_id)
    farmer = FarmerProfile.query.get(crop.farmer_id)
    user = current_user if current_user.is_authenticated else None
    
    # Get similar crops (same category)
    similar_crops = Crop.query.filter_by(category=crop.category, is_available=True).all()
    
    return render_template('customer/crop_detail.html', 
                         crop=crop, 
                         farmer=farmer, 
                         user=user,
                         similar_crops=similar_crops)

@app.route('/customer/cart')
@login_required
def cart():
    """View the shopping cart"""
    user = current_user
    
    if user.user_type != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    # Debug output to see if the session has a cart - use direct dict access to show all session data
    app.logger.info("----------- CART DEBUG START -----------")
    app.logger.info(f"Session dict: {dict(session)}")
    app.logger.info(f"Session cart: {session.get('cart')}")
    app.logger.info(f"Session keys: {list(session.keys())}")
    
    # Make sure cart is initialized
    if 'cart' not in session:
        session['cart'] = []
        session.modified = True
        app.logger.warning("Cart was missing in session. Initialized new cart.")
    
    # Get cart items from session
    cart_items = session.get('cart', [])
    
    # Check the cart type and force to list if needed
    if not isinstance(cart_items, list):
        app.logger.warning(f"Cart was not a list ({type(cart_items)}). Initializing empty cart.")
        cart_items = []
        session['cart'] = cart_items
        session.modified = True
    
    app.logger.info(f"Cart items count: {len(cart_items)}")
    app.logger.info(f"Cart items data: {cart_items}")
    
    # Fetch crop details for each item in cart
    cart_data = []
    for item in cart_items:
        # Skip invalid items
        if not isinstance(item, dict) or 'crop_id' not in item:
            app.logger.warning(f"Invalid cart item found: {item}")
            continue
            
        try:
            crop_id = int(item['crop_id'])
            crop = Crop.query.get(crop_id)
            if crop and crop.is_available:
                farmer = FarmerProfile.query.get(crop.farmer_id)
                if farmer:
                    cart_data.append({
                        'crop_id': crop.id,
                        'name': crop.name,
                        'farmer_name': farmer.farm_name,
                        'price': crop.price,
                        'quantity': float(item['quantity']),
                        'unit': crop.unit,
                        'subtotal': crop.price * float(item['quantity']),
                        'farmer_id': farmer.id
                    })
                else:
                    app.logger.warning(f"Farmer not found for crop {crop_id}")
            else:
                app.logger.warning(f"Crop not found or not available: {crop_id}")
        except Exception as e:
            app.logger.error(f"Error processing cart item {item}: {str(e)}")
    
    # Group by farmer
    farmers_dict = {}
    for item in cart_data:
        if item['farmer_id'] not in farmers_dict:
            farmers_dict[item['farmer_id']] = {
                'farmer_id': item['farmer_id'],
                'farmer_name': item['farmer_name'],
                'cart_items': [],  # Renamed from 'items' to avoid conflict with dict.items()
                'total': 0
            }
        farmers_dict[item['farmer_id']]['cart_items'].append(item)
        farmers_dict[item['farmer_id']]['total'] += item['subtotal']
    
    # Convert to list for template rendering
    farmers_list = list(farmers_dict.values())
    
    # Calculate total cart value
    cart_total = sum(farmer['total'] for farmer in farmers_list)
    
    # Additional debugging
    app.logger.info(f"Cart data processed: {len(cart_data)} valid items")
    app.logger.info(f"Farmers in cart: {list(farmers_dict.keys())}")
    app.logger.info(f"Farmers data structure: {farmers_list}")
    app.logger.info(f"Cart total: {cart_total}")
    app.logger.info("----------- CART DEBUG END -----------")
    
    return render_template(
        'customer/cart.html', 
        farmers=farmers_list, 
        user=user,
        cart_count=len(cart_items),
        cart_empty=len(farmers_list) == 0,
        cart_total=cart_total
    )

@app.route('/api/cart/info')
def get_cart_info():
    """Get cart information including count and total"""
    if not current_user.is_authenticated or current_user.user_type != 'customer':
        return jsonify({
            'cart_count': 0,
            'cart_total': 0
        })
    
    cart_items = session.get('cart', [])
    cart_total = 0
    
    # Calculate cart total
    for item in cart_items:
        if isinstance(item, dict):
            crop = Crop.query.get(item.get('crop_id'))
            if crop:
                cart_total += crop.price * item.get('quantity', 0)
    
    return jsonify({
        'cart_count': len(cart_items),
        'cart_total': cart_total
    })

@app.route('/api/cart/clear', methods=['POST'])
@csrf.exempt
def clear_cart():
    """Clear the shopping cart"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login as a customer.', 'redirect': url_for('login')})
    
    if current_user.user_type != 'customer':
        return jsonify({'success': False, 'message': 'Only customers can access the cart.', 'redirect': url_for('login')})
    
    session['cart'] = []
    session.modified = True
    
    return jsonify({
        'success': True,
        'message': 'Cart cleared successfully',
        'cart_count': 0,
        'cart_total': 0
    })

@app.route('/api/cart/update', methods=['POST'])
@csrf.exempt
def update_cart():
    """Update quantity of a crop in the shopping cart"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login as a customer.', 'redirect': url_for('login')})
    
    if current_user.user_type != 'customer':
        return jsonify({'success': False, 'message': 'Only customers can access the cart.', 'redirect': url_for('login')})
    
    data = request.json
    crop_id = data.get('crop_id')
    quantity = float(data.get('quantity', 0))
    
    if not crop_id or not quantity:
        return jsonify({'success': False, 'message': 'Invalid request data.'})
    
    # Validate crop exists and quantity is available
    crop = Crop.query.get(crop_id)
    if not crop or not crop.is_available:
        return jsonify({'success': False, 'message': 'Crop not available.'})
    
    if quantity > crop.quantity:
        return jsonify({'success': False, 'message': 'Requested quantity exceeds available stock.'})
    
    cart_items = session.get('cart', [])
    
    # Update quantity if item exists, otherwise add new item
    item_found = False
    for item in cart_items:
        if isinstance(item, dict) and item.get('crop_id') == crop_id:
            item['quantity'] = quantity
            item_found = True
            break
    
    if not item_found:
        # Add new item to cart
        cart_items.append({
            'crop_id': crop_id,
            'quantity': quantity
        })
    
    session['cart'] = cart_items
    session.modified = True
    
    # Calculate cart total
    cart_total = 0
    for item in cart_items:
        crop = Crop.query.get(item.get('crop_id'))
        if crop:
            cart_total += crop.price * item.get('quantity', 0)
    
    return jsonify({
        'success': True,
        'message': 'Cart updated successfully',
        'cart_count': len(cart_items),
        'cart_total': cart_total,
        'item_details': {
            'crop_id': crop_id,
            'name': crop.name,
            'price': crop.price,
            'unit': crop.unit,
            'quantity': quantity,
            'subtotal': crop.price * quantity
        }
    })

@app.route('/api/cart/add', methods=['GET', 'POST'])
def add_to_cart():
    """Add a crop to the shopping cart"""
    if not current_user.is_authenticated:
        flash('Please login as a customer to add items to cart.', 'warning')
        return redirect(url_for('login'))
    
    if current_user.user_type != 'customer':
        flash('Only customers can add items to cart.', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            crop_id = request.form.get('crop_id')
            if not crop_id:
                raise ValueError('No crop ID provided')
            
            crop_id = int(crop_id)
            quantity = float(request.form.get('quantity', 1))
            
            if quantity <= 0:
                raise ValueError('Please enter a valid quantity')
                
            # Validate crop exists and is available
            crop = Crop.query.get(crop_id)
            if not crop:
                raise ValueError('Crop not found')
                
            if not crop.is_available:
                raise ValueError('This crop is not available')
                
            if quantity > crop.quantity:
                raise ValueError(f'Only {crop.quantity} {crop.unit} available')
            
            # Initialize cart if needed
            if 'cart' not in session:
                session['cart'] = []
            
            # Update or add item to cart
            cart = session['cart']
            item_found = False
            
            for item in cart:
                if item.get('crop_id') == crop_id:
                    item['quantity'] = quantity
                    item_found = True
                    break
            
            if not item_found:
                cart.append({
                    'crop_id': crop_id,
                    'quantity': quantity
                })
            
            session['cart'] = cart
            session.modified = True
            
            flash(f'Added {quantity} {crop.unit} of {crop.name} to cart!', 'success')
            
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            app.logger.error(f'Error adding to cart: {e}')
            flash('Error adding item to cart', 'error')
            
        return redirect(url_for('crop_detail', crop_id=crop_id))
    
    return redirect(url_for('marketplace'))

@app.route('/customer/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    user = current_user
    
    if user.user_type != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    if not user.customer_profile:
        flash('Please complete your profile before checkout.', 'warning')
        return redirect(url_for('customer_profile'))
    
    # Debug output
    app.logger.info(f"Checkout - Session Keys: {list(session.keys())}")
    app.logger.info(f"Checkout - Session Cart: {session.get('cart')}")
    
    # Get cart from session
    cart_items = session.get('cart', [])
    
    # If cart wasn't a list, initialize it
    if not isinstance(cart_items, list):
        cart_items = []
        session['cart'] = cart_items
        session.modified = True
        app.logger.warning("Checkout - Cart was not a list. Initialized empty cart.")
    
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('marketplace'))
    
    # Group items by farmer
    farmer_orders = {}
    
    for item in cart_items:
        # Skip invalid items
        if not isinstance(item, dict) or 'crop_id' not in item:
            app.logger.warning(f"Checkout - Invalid cart item found: {item}")
            continue
            
        try:
            crop_id = int(item['crop_id'])
            crop = Crop.query.get(crop_id)
            if crop and crop.is_available:
                farmer_id = crop.farmer_id
                
                if farmer_id not in farmer_orders:
                    farmer = FarmerProfile.query.get(farmer_id)
                    if not farmer:
                        app.logger.warning(f"Checkout - Farmer not found for crop {crop_id}")
                        continue
                        
                    farmer_orders[farmer_id] = {
                        'farmer': farmer,
                        'items': [],  # Renamed from 'items' to avoid conflict with dict.items()
                        'total': 0
                    }
                
                quantity = float(item['quantity'])
                item_total = crop.price * quantity
                farmer_orders[farmer_id]['items'].append({
                    'crop': crop,
                    'quantity': quantity,
                    'price': crop.price,
                    'subtotal': item_total
                })
                farmer_orders[farmer_id]['total'] += item_total
            else:
                app.logger.warning(f"Checkout - Crop not found or not available: {crop_id}")
        except Exception as e:
            app.logger.error(f"Checkout - Error processing cart item {item}: {str(e)}")
    
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
@login_required
def customer_orders():
    user = current_user
    
    if user.user_type != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(customer_id=user.customer_profile.id).order_by(Order.order_date.desc()).all()
    return render_template('customer/orders.html', orders=orders, user=user)

@app.route('/customer/orders/<int:order_id>/payment', methods=['GET', 'POST'])
@login_required
def order_payment(order_id):
    user = current_user
    
    if user.user_type != 'customer':
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

# Session test route (for debugging only)
@app.route('/test/session')
@login_required
def test_session():
    """Test route to verify session functionality"""
    # Set a test value in session
    session['test_value'] = f"Test at {datetime.utcnow()}"
    session.modified = True
    
    # Create a test cart if none exists
    if 'cart' not in session:
        session['cart'] = []
        session.modified = True
    
    # Force cart to be a list
    if not isinstance(session['cart'], list):
        session['cart'] = []
        session.modified = True
    
    # Add test item to cart
    session['cart'].append({
        'crop_id': 1,
        'quantity': 2.5,
        'test_time': datetime.utcnow().strftime('%H:%M:%S')
    })
    
    # Ensure session is saved
    session.modified = True
    
    # Return session info
    return jsonify({
        'session_keys': list(session.keys()),
        'test_value': session.get('test_value'),
        'cart': session.get('cart'),
        'user_id': session.get('_user_id'),
        'message': 'Session test complete - check if data persists on refresh'
    })

@app.route('/test/cart')
@login_required
def test_cart():
    """Advanced test route to debug cart operations"""
    user = current_user
    
    # Capture session state before
    session_before = dict(session)
    cart_before = session.get('cart', None)
    
    # Initialize cart if not present
    if 'cart' not in session:
        session['cart'] = []
        session.modified = True
    
    # Add test item to cart
    test_item = {
        'crop_id': 1, 
        'quantity': 1.5,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }
    
    # Add to cart and mark session modified
    session['cart'].append(test_item)
    session.modified = True
    
    # Force permanent session
    session.permanent = True
    
    # Get latest session state
    cart_after = session.get('cart')
    
    app.logger.info(f"Cart before: {cart_before}")
    app.logger.info(f"Cart after: {cart_after}")
    
    # Return detailed debug info
    return jsonify({
        'message': 'Cart test complete',
        'session_keys_before': list(session_before.keys()) if session_before else [],
        'session_keys_after': list(session.keys()),
        'cart_before': cart_before,
        'cart_after': cart_after,
        'test_item_added': test_item,
        'user_id': user.id,
        'user_email': user.email
    })

# Notification routes
@app.route('/api/notifications/read/<int:notification_id>', methods=['POST'])
@login_required
@csrf.exempt
def mark_notification_read(notification_id):
    user = current_user
    
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if notification belongs to user
    if notification.user_id != user.id:
        return jsonify({'success': False, 'message': 'Unauthorized access.'})
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Notification marked as read.'})

@app.route('/api/notifications/read/all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    user = current_user
    
    notifications = Notification.query.filter_by(user_id=user.id, is_read=False).all()
    for notification in notifications:
        notification.is_read = True
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'All notifications marked as read.'})
