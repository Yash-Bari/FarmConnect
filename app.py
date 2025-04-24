import os
import logging
import tempfile
from datetime import timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
# Removed JWT imports as we're using Flask-Login
from flask_cors import CORS
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect
from flask_session import Session  # Add Flask-Session
from werkzeug.utils import secure_filename
import uuid
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Set a consistent secret key for session encryption and signing
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-make-this-random-in-production")

# Configure session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_FILE_DIR"] = os.path.join(tempfile.gettempdir(), "flask_session")
app.config["SESSION_KEY_PREFIX"] = "farmconnect_"
app.config["SESSION_FILE_THRESHOLD"] = 100  # Maximum number of sessions in session directory
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_REFRESH_EACH_REQUEST"] = True  # Refresh session timeout on each request

# Initialize Session
Session(app)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///farmconnect.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Authentication is now handled by Flask-Login

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# CORS configuration
CORS(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Initialize the database
db.init_app(app)

# Import models and create tables
with app.app_context():
    from models import User, FarmerProfile, CustomerProfile, Crop, Order, OrderItem, Payment, Notification
    db.create_all()

# Import routes
from routes import *
from auth import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
