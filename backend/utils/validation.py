"""
Input validation functions.
"""
from config import ALLOWED_EXTENSIONS, MIN_BLOCK_SIZE, MAX_BLOCK_SIZE

def validate_file_upload(request):
    """
    Validate file upload request.
    
    Args:
        request: Flask request object
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check if files are in the request
    if 'element_img' not in request.files or 'big_img' not in request.files:
        return False, 'Missing files'
    
    element_file = request.files['element_img']
    big_file = request.files['big_img']
    
    # Check if filenames are valid
    if element_file.filename == '' or big_file.filename == '':
        return False, 'No selected files'
    
    # Check file extensions
    if not allowed_file(element_file.filename):
        return False, f'Invalid element image file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
    
    if not allowed_file(big_file.filename):
        return False, f'Invalid target image file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
    
    return True, None

def allowed_file(filename):
    """
    Check if file has an allowed extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        bool: True if allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_block_size(block_size):
    """
    Validate block size parameter.
    
    Args:
        block_size: Block size value
        
    Returns:
        tuple: (is_valid, error_message or valid_block_size)
    """
    try:
        block_size = int(block_size)
        
        if block_size < MIN_BLOCK_SIZE:
            return False, f'Block size too small. Minimum allowed: {MIN_BLOCK_SIZE}'
        
        if block_size > MAX_BLOCK_SIZE:
            return False, f'Block size too large. Maximum allowed: {MAX_BLOCK_SIZE}'
        
        return True, block_size
    except (ValueError, TypeError):
        return False, 'Invalid block size. Must be an integer.'

def validate_filter(filter_name):
    """
    Validate filter name.
    
    Args:
        filter_name: Name of the filter
        
    Returns:
        tuple: (is_valid, error_message or filter_name)
    """
    from config import AVAILABLE_FILTERS
    
    if filter_name not in AVAILABLE_FILTERS:
        return False, f'Invalid filter. Available filters: {", ".join(AVAILABLE_FILTERS.keys())}'
    
    return True, filter_name

def validate_job_id(job_id, job_states):
    """
    Validate job ID.
    
    Args:
        job_id: Job ID to validate
        job_states: Dictionary of job states
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if job_id not in job_states:
        return False, 'Job not found'
    
    return True, None