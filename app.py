import os
import logging
import tempfile
from datetime import timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session

from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import uuid
import json

# Import db instance
from extensions import db

# Import models after db is defined
from models import Order, Notification

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)

# Set a strong secret key for session encryption and signing FIRST before other configs
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://avnadmin:AVNS_v0xlfmLjNPCQRwjxJx9@mysql-8cf57f9-khodseganesh2003-1d58.l.aivencloud.com:25713/farmconnect"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configure CORS
CORS(app)

# Configure ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Configure file upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/farmer/payment/update/<int:order_id>', methods=['POST'])
@login_required
def update_payment_status(order_id):
    if not current_user.user_type == 'farmer':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    try:
        order = Order.query.get_or_404(order_id)
        payment = order.payment

        # Check if the order belongs to the current farmer
        if order.farmer_id != current_user.farmer_profile.id:
            return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

        if not payment:
            return jsonify({'success': False, 'message': 'No payment found for this order'}), 404

        status = request.form.get('status')
        if status not in ['pending', 'verified', 'rejected']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400

        payment.status = status
        db.session.commit()

        # Create a notification for the customer
        notification = Notification(
            user_id=order.customer.user.id,
            message=f'Payment status for order #{order.id} has been updated to {status}',
            related_type='payment',
            related_id=payment.id
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Payment status updated to {status}'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating payment status'
        }), 500

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.logger.info(f'Upload folder configured at: {UPLOAD_FOLDER}')

# Import models and create tables
with app.app_context():
    from models import User, FarmerProfile, CustomerProfile, Crop, Order, OrderItem, Payment, Notification
    db.create_all()

# Import routes
from routes import *
from auth import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
