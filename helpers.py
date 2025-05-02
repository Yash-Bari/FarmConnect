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
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(file.filename)
            base, ext = os.path.splitext(filename)
            unique_filename = f"{base}_{timestamp}{ext}"
            
            # Ensure upload folder exists
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save file using absolute path
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            # Return just the filename for database storage
            return unique_filename
            
        except Exception as e:
            print(f'Error saving file: {str(e)}')
            return None
    
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
