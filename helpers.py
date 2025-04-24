import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

# File upload helpers
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return f"{uuid.uuid4().hex}.{ext}"

def save_file(file, upload_folder):
    """Save a file to the upload folder with a unique name"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(filename)
        
        # Create year/month directory structure
        today = datetime.today()
        year_month = f"{today.year}/{today.month:02d}"
        upload_path = os.path.join(upload_folder, year_month)
        
        # Create directory if it doesn't exist
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        # Return relative path from upload folder
        return os.path.join(year_month, unique_filename)
    
    return None

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return ""
    return dt.strftime("%b %d, %Y %I:%M %p")

def format_date(dt):
    """Format date for display"""
    if not dt:
        return ""
    return dt.strftime("%b %d, %Y")

def format_currency(amount):
    """Format amount as currency"""
    return f"₹{amount:.2f}"

def get_image_url(image_path):
    """Get full URL for an image path"""
    if not image_path:
        return None
    
    return f"/static/uploads/{image_path}"
