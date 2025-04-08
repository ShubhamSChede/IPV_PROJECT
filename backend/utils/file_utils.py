"""
Utility functions for file handling.
"""
import os
import uuid
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, TEMP_FOLDER, OUTPUT_FOLDER

def allowed_file(filename):
    """
    Check if the file has an allowed extension.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        bool: True if file has an allowed extension, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename):
    """
    Generate a unique filename based on the original filename.
    
    Args:
        original_filename: Original name of the file
        
    Returns:
        tuple: (unique_id, secure_unique_filename)
    """
    unique_id = str(uuid.uuid4())
    extension = os.path.splitext(original_filename)[1]
    secure_name = secure_filename(f"{unique_id}{extension}")
    return unique_id, secure_name

def get_file_path(filename, folder_type='upload'):
    """
    Get the full path for a file based on the folder type.
    
    Args:
        filename: Name of the file
        folder_type: Type of folder ('upload', 'temp', or 'output')
        
    Returns:
        str: Full path to the file
    """
    if folder_type == 'upload':
        return os.path.join(UPLOAD_FOLDER, filename)
    elif folder_type == 'temp':
        return os.path.join(TEMP_FOLDER, filename)
    elif folder_type == 'output':
        return os.path.join(OUTPUT_FOLDER, filename)
    else:
        raise ValueError(f"Invalid folder type: {folder_type}")

def save_uploaded_file(file_obj, filename=None):
    """
    Save an uploaded file with a secure filename.
    
    Args:
        file_obj: File object from the request
        filename: Optional filename to use (if None, will generate one)
        
    Returns:
        tuple: (unique_id, filename, full_path)
    """
    if filename is None:
        unique_id, filename = generate_unique_filename(file_obj.filename)
    else:
        unique_id = filename.split('_')[0] if '_' in filename else None
    
    file_path = get_file_path(filename, 'upload')
    file_obj.save(file_path)
    
    return unique_id, filename, file_path

def get_file_url(filename, folder_type='upload'):
    """
    Get the URL for accessing a file.
    
    Args:
        filename: Name of the file
        folder_type: Type of folder ('upload', 'temp', or 'output')
        
    Returns:
        str: URL path to access the file
    """
    if folder_type == 'upload':
        return f"/api/images/uploads/{filename}"
    elif folder_type == 'temp':
        return f"/api/temp/{filename}"
    elif folder_type == 'output':
        return f"/api/images/outputs/{filename}"
    else:
        raise ValueError(f"Invalid folder type: {folder_type}")