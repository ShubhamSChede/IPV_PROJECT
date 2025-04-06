from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np
from PIL import Image
import io
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes to allow requests from Next.js frontend

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Constants to prevent memory issues
MAX_ELEMENT_SIZE = 32  # Maximum size of element image (width/height)
MAX_TARGET_SIZE = 128  # Maximum size of target image (width/height)
MAX_MOSAIC_PIXELS = 16777216  # ~16 million pixels (4096x4096)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_image_matrix(element_img, matrix_size):
    """
    Generate a simple mosaic image using the element_img as a building block.
    
    Args:
        element_img: 2D grayscale image (numpy array)
        matrix_size: tuple (H, W) specifying height and width of the output in terms of element blocks
    
    Returns:
        mosaic: 2D numpy array representing the mosaic image
    """
    N, M = element_img.shape
    H, W = matrix_size
    
    # Create a row of element images
    row_tmp = np.zeros((N, M*W))
    for j in range(W):
        row_tmp[:, j*M:(j+1)*M] = element_img
    
    # Repeat the row to create the full mosaic
    mosaic = np.zeros((N*H, M*W))
    for i in range(H):
        mosaic[i*N:(i+1)*N, :] = row_tmp
        
    return mosaic

def adjust_element_mean(element_img, target_mean_value):
    """
    Adjust the mean of the element_img to match the target_mean_value
    while keeping pixel values in the valid range.
    
    Args:
        element_img: 2D grayscale image (numpy array)
        target_mean_value: desired mean value
    
    Returns:
        adjusted element_img
    """
    # Convert to float for calculations
    element = element_img.astype(float)
    current = np.mean(element)
    
    # Calculate the difference and adjust all pixels accordingly
    diff = target_mean_value - current
    element = element + diff
    
    # Ensure values are within valid range (0-255)
    element = np.clip(element, 0, 255)
    
    return element

def create_mosaic(element_img, big_img):
    """
    Generate a mosaic image that looks like big_img but is made of element_img blocks
    
    Args:
        element_img: 2D grayscale image (numpy array) - the building block
        big_img: 2D grayscale image (numpy array) - the target image
    
    Returns:
        tuple: (mosaic, simple_mosaic)
            - mosaic: the final mosaic with adjusted element images
            - simple_mosaic: mosaic without dynamic adjustment
    """
    N, M = element_img.shape
    H, W = big_img.shape
    
    # Generate a simple mosaic
    simple_mosaic = create_image_matrix(element_img, (H, W))
    mosaic = simple_mosaic.copy()
    
    # Adjust each element block to match the target image's intensity
    for i in range(H):
        for j in range(W):
            # Adjust the mean of the element_img to match the target pixel
            element = adjust_element_mean(element_img, big_img[i, j])
            mosaic[i*N:(i+1)*N, j*M:(j+1)*M] = element
    
    return mosaic, simple_mosaic

def normalize_image(img):
    """
    Normalize image values to [0, 1] range
    """
    img = img - np.min(img)
    if np.max(img) > 0:
        img = img / np.max(img)
    return img

def resize_image_if_needed(img, max_size, maintain_aspect_ratio=True):
    """
    Resize image if larger than max_size while maintaining aspect ratio if requested
    
    Args:
        img: PIL Image object
        max_size: maximum width or height
        maintain_aspect_ratio: if True, maintain aspect ratio
        
    Returns:
        Resized PIL Image
    """
    width, height = img.size
    
    # Check if resizing is needed
    if width <= max_size and height <= max_size:
        return img
    
    if maintain_aspect_ratio:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
    else:
        new_width = new_height = max_size
        
    return img.resize((new_width, new_height), Image.LANCZOS)

def check_mosaic_size(element_shape, target_shape):
    """
    Check if the resulting mosaic would be too large and adjust target size if needed.
    
    Args:
        element_shape: tuple (height, width) of element image
        target_shape: tuple (height, width) of target image
        
    Returns:
        tuple: adjusted target shape to keep mosaic size reasonable
    """
    element_h, element_w = element_shape
    target_h, target_w = target_shape
    
    # Calculate resulting mosaic size
    mosaic_h = element_h * target_h
    mosaic_w = element_w * target_w
    mosaic_pixels = mosaic_h * mosaic_w
    
    # If mosaic would be too large, scale down target_shape
    if mosaic_pixels > MAX_MOSAIC_PIXELS:
        scale_factor = (MAX_MOSAIC_PIXELS / mosaic_pixels) ** 0.5
        new_target_h = max(1, int(target_h * scale_factor))
        new_target_w = max(1, int(target_w * scale_factor))
        return (new_target_h, new_target_w)
    
    return target_shape

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

@app.route('/api/generate_mosaic', methods=['POST'])
def generate_mosaic_api():
    """API endpoint for generating mosaic images"""
    # Check if files are in the request
    if 'element_img' not in request.files or 'big_img' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
    
    element_file = request.files['element_img']
    big_file = request.files['big_img']
    
    # Check if filenames are valid
    if element_file.filename == '' or big_file.filename == '':
        return jsonify({'error': 'No selected files'}), 400
    
    if not (allowed_file(element_file.filename) and allowed_file(big_file.filename)):
        return jsonify({'error': 'Invalid file type. Please use PNG, JPG or JPEG files.'}), 400
    
    try:
        # Generate unique IDs for the files
        job_id = str(uuid.uuid4())
        
        # Save files with secure names
        element_filename = f"{job_id}_element{os.path.splitext(element_file.filename)[1]}"
        big_filename = f"{job_id}_big{os.path.splitext(big_file.filename)[1]}"
        
        element_path = os.path.join(app.config['UPLOAD_FOLDER'], element_filename)
        big_path = os.path.join(app.config['UPLOAD_FOLDER'], big_filename)
        
        element_file.save(element_path)
        big_file.save(big_path)
        
        # Open images with PIL first
        element_pil = Image.open(element_path).convert('L')
        big_pil = Image.open(big_path).convert('L')
        
        # Resize if needed to prevent memory issues
        element_pil = resize_image_if_needed(element_pil, MAX_ELEMENT_SIZE)
        big_pil = resize_image_if_needed(big_pil, MAX_TARGET_SIZE)
        
        # Convert to numpy arrays
        element_img = np.array(element_pil)
        big_img = np.array(big_pil)
        
        # Check if the mosaic would be too large and adjust target size if needed
        target_h, target_w = check_mosaic_size(element_img.shape, big_img.shape)
        
        if target_h != big_img.shape[0] or target_w != big_img.shape[1]:
            # Resize target image if needed to prevent memory issues
            big_pil = big_pil.resize((target_w, target_h), Image.LANCZOS)
            big_img = np.array(big_pil)
        
        # Generate mosaic
        mosaic, simple_mosaic = create_mosaic(element_img, big_img)
        
        # Normalize and convert to uint8 for saving
        mosaic_norm = (normalize_image(mosaic) * 255).astype(np.uint8)
        simple_mosaic_norm = (normalize_image(simple_mosaic) * 255).astype(np.uint8)
        
        # Save output images
        mosaic_filename = f"{job_id}_mosaic.png"
        simple_mosaic_filename = f"{job_id}_simple_mosaic.png"
        
        mosaic_path = os.path.join(app.config['OUTPUT_FOLDER'], mosaic_filename)
        simple_mosaic_path = os.path.join(app.config['OUTPUT_FOLDER'], simple_mosaic_filename)
        
        Image.fromarray(mosaic_norm).save(mosaic_path)
        Image.fromarray(simple_mosaic_norm).save(simple_mosaic_path)
        
        # Return URLs to access the images
        return jsonify({
            'job_id': job_id,
            'mosaic_url': f"/api/images/{mosaic_filename}",
            'simple_mosaic_url': f"/api/images/{simple_mosaic_filename}"
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/<filename>', methods=['GET'])
def get_image(filename):
    """Serve an image from the output folder"""
    try:
        return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename))
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)