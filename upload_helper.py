import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov', 'avi'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename, file_type='photo'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'photo':
        return ext in ALLOWED_PHOTO_EXTENSIONS
    elif file_type == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    else:
        return ext in ALLOWED_PHOTO_EXTENSIONS or ext in ALLOWED_VIDEO_EXTENSIONS


def get_media_type(filename):
    """Determine if file is photo or video"""
    if '.' not in filename:
        return 'photo'
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return 'video'
    return 'photo'


def save_uploaded_file(file):
    """
    Save uploaded file and return the URL and media type
    Returns: (file_url, media_type, file_size) or (None, None, None) on error
    """
    if not file or file.filename == '':
        return None, None, None
    
    # Validate file type
    if not allowed_file(file.filename, 'any'):
        return None, None, None
    
    # Get media type
    media_type = get_media_type(file.filename)
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join('static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Get file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    # Check file size
    if file_size > MAX_FILE_SIZE:
        return None, None, None
    
    # Save the file
    file.save(file_path)
    
    # Return relative URL
    file_url = f"/static/uploads/{unique_filename}"
    
    return file_url, media_type, file_size


def delete_uploaded_file(file_url):
    """Delete uploaded file from storage"""
    if not file_url or not file_url.startswith('/static/uploads/'):
        return False
    
    try:
        file_path = file_url.lstrip('/')
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    return False
