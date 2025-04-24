from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import app, db
from models import User, FarmerProfile, CustomerProfile
from forms import LoginForm, RegisterForm, FarmerProfileForm, CustomerProfileForm
from helpers import save_file, allowed_file
import os

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Create JWT token
            access_token = create_access_token(identity=user.id)
            
            # Set JWT token in session
            session['token'] = access_token
            
            # Redirect based on user type
            if user.user_type == 'farmer':
                flash('Login successful!', 'success')
                return redirect(url_for('farmer_dashboard'))
            else:
                flash('Login successful!', 'success')
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        email = form.email.data
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            email=form.email.data,
            full_name=form.full_name.data,
            user_type=form.user_type.data,
            phone=form.phone.data,
            is_verified=True  # For simplicity, skip email verification
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Create JWT token
        access_token = create_access_token(identity=user.id)
        
        # Set JWT token in session
        session['token'] = access_token
        
        flash('Registration successful! Please complete your profile.', 'success')
        
        # Redirect based on user type
        if user.user_type == 'farmer':
            return redirect(url_for('farmer_profile'))
        else:
            return redirect(url_for('customer_profile'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/farmer/profile', methods=['GET', 'POST'])
@jwt_required()
def farmer_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'farmer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    # Check if profile already exists
    if user.farmer_profile:
        form = FarmerProfileForm(obj=user.farmer_profile)
    else:
        form = FarmerProfileForm()
    
    if form.validate_on_submit():
        # Handle profile picture upload
        if 'profile_picture' in request.files and request.files['profile_picture'].filename:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = save_file(file, app.config['UPLOAD_FOLDER'])
                user.profile_picture = filename
        
        # Create or update farmer profile
        if user.farmer_profile:
            # Update existing profile
            user.farmer_profile.farm_name = form.farm_name.data
            user.farmer_profile.farm_location = form.farm_location.data
            user.farmer_profile.farm_size = form.farm_size.data
            user.farmer_profile.growing_practices = form.growing_practices.data
            user.farmer_profile.payment_info = form.payment_info.data
            user.farmer_profile.bio = form.bio.data
        else:
            # Create new profile
            farmer_profile = FarmerProfile(
                user_id=user.id,
                farm_name=form.farm_name.data,
                farm_location=form.farm_location.data,
                farm_size=form.farm_size.data,
                growing_practices=form.growing_practices.data,
                payment_info=form.payment_info.data,
                bio=form.bio.data
            )
            db.session.add(farmer_profile)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('farmer_dashboard'))
    
    return render_template('auth/profile.html', form=form, user=user, user_type='farmer')

@app.route('/customer/profile', methods=['GET', 'POST'])
@jwt_required()
def customer_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.user_type != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    # Check if profile already exists
    if user.customer_profile:
        form = CustomerProfileForm(obj=user.customer_profile)
    else:
        form = CustomerProfileForm()
    
    if form.validate_on_submit():
        # Handle profile picture upload
        if 'profile_picture' in request.files and request.files['profile_picture'].filename:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = save_file(file, app.config['UPLOAD_FOLDER'])
                user.profile_picture = filename
        
        # Create or update customer profile
        if user.customer_profile:
            # Update existing profile
            user.customer_profile.delivery_address = form.delivery_address.data
            user.customer_profile.preferred_payment = form.preferred_payment.data
        else:
            # Create new profile
            customer_profile = CustomerProfile(
                user_id=user.id,
                delivery_address=form.delivery_address.data,
                preferred_payment=form.preferred_payment.data
            )
            db.session.add(customer_profile)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    return render_template('auth/profile.html', form=form, user=user, user_type='customer')

@app.route('/api/auth/token', methods=['POST'])
def get_token():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({'success': True, 'token': access_token, 'user_type': user.user_type})
