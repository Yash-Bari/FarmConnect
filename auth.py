from flask import render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db, mail
from models import User, FarmerProfile, CustomerProfile
from forms import LoginForm, RegisterForm, FarmerProfileForm, CustomerProfileForm, RequestPasswordResetForm, ResetPasswordForm
from helpers import save_file, allowed_file
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
import os

def get_reset_token_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def send_reset_email(user):
    s = get_reset_token_serializer()
    token = s.dumps(user.email, salt='password-reset-salt')
    reset_url = url_for('reset_password', token=token, _external=True)
    msg = Message('Password Reset Request',
                  sender='noreply@farmconnect.com',
                  recipients=[user.email])
    msg.body = f'''
To reset your password, visit the following link:
{reset_url}

If you did not make this request, simply ignore this email and no changes will be made.
'''
    mail.send(msg)

# Authentication routes
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Login with Flask-Login
            login_user(user)
            
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

def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
        
        # Login with Flask-Login
        login_user(user)
        
        flash('Registration successful! Please complete your profile.', 'success')
        
        # Redirect based on user type
        if user.user_type == 'farmer':
            return redirect(url_for('farmer_profile'))
        else:
            return redirect(url_for('customer_profile'))
    
    return render_template('auth/register.html', form=form)

def logout():
    # Logout with Flask-Login
    logout_user()
    # Clear session
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@login_required
def farmer_profile():
    user = current_user
    
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
        # Handle UPI QR code upload
        if 'upi_qr_code' in request.files and request.files['upi_qr_code'].filename:
            file = request.files['upi_qr_code']
            if file and allowed_file(file.filename):
                filename = save_file(file, app.config['UPLOAD_FOLDER'])
                if user.farmer_profile:
                    user.farmer_profile.upi_qr_code = filename

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
                bio=form.bio.data,
                upi_qr_code=filename if 'upi_qr_code' in request.files and request.files['upi_qr_code'].filename else None
            )
            db.session.add(farmer_profile)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('farmer_dashboard'))
    
    return render_template('auth/profile.html', form=form, user=user, user_type='farmer')

@login_required
def customer_profile():
    user = current_user
    
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

def get_token():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    
    # Use Flask-Login session instead of JWT
    login_user(user)
    return jsonify({'success': True, 'user_type': user.user_type})

def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                send_reset_email(user)
                flash('Check your email for instructions to reset your password.', 'info')
                return redirect(url_for('login'))
            except Exception as e:
                current_app.logger.error(f'Error sending reset email: {str(e)}')
                flash('Error sending reset email. Please try again later.', 'error')
        else:
            flash('Email address not found.', 'error')
    return render_template('auth/reset_password_request.html', form=form)

def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    try:
        s = get_reset_token_serializer()
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  # Token expires in 1 hour
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Invalid or expired reset link.', 'error')
            return redirect(url_for('login'))
    except Exception as e:
        current_app.logger.error(f'Error verifying reset token: {str(e)}')
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('login'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            user.set_password(form.password.data)
            db.session.commit()
            flash('Your password has been reset.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            current_app.logger.error(f'Error resetting password: {str(e)}')
            flash('Error resetting password. Please try again.', 'error')
            db.session.rollback()
    return render_template('auth/reset_password.html', form=form)
