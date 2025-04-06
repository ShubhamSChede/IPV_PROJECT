from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np
from PIL import Image
import io
import os
import uuid
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes to allow requests from Next.js frontend

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
TEMP_FOLDER = 'temp'  # For storing intermediate results
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Constants to prevent memory issues
MAX_ELEMENT_SIZE = 32  # Maximum size of element image (width/height)
MAX_TARGET_SIZE = 128  # Maximum size of target image (width/height)
MAX_MOSAIC_PIXELS = 16777216  # ~16 million pixels (4096x4096)

# Dictionary to store job states
job_states = {}

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

def create_mosaic(element_img, big_img, job_id):
    """
    Generate a mosaic image that looks like big_img but is made of element_img blocks
    
    Args:
        element_img: 2D grayscale image (numpy array) - the building block
        big_img: 2D grayscale image (numpy array) - the target image
        job_id: unique identifier for the job
    
    Returns:
        tuple: (mosaic, simple_mosaic)
            - mosaic: the final mosaic with adjusted element images
            - simple_mosaic: mosaic without dynamic adjustment
    """
    N, M = element_img.shape
    H, W = big_img.shape
    
    # Update job state
    job_states[job_id]['status'] = 'creating_simple_mosaic'
    job_states[job_id]['progress'] = 10
    
    # Generate a simple mosaic
    simple_mosaic = create_image_matrix(element_img, (H, W))
    
    # Save intermediate result
    simple_mosaic_norm = (normalize_image(simple_mosaic) * 255).astype(np.uint8)
    simple_mosaic_path = os.path.join(app.config['TEMP_FOLDER'], f"{job_id}_simple_mosaic.png")
    Image.fromarray(simple_mosaic_norm).save(simple_mosaic_path)
    
    # Update job state
    job_states[job_id]['status'] = 'adjusting_elements'
    job_states[job_id]['progress'] = 30
    job_states[job_id]['intermediate_outputs']['simple_mosaic'] = f"/api/temp/{job_id}_simple_mosaic.png"
    
    # Start with the simple mosaic
    mosaic = simple_mosaic.copy()
    
    # Save a partial result halfway through
    if H > 2 and W > 2:
        half_point = H // 2
        partial_mosaic = mosaic.copy()
        
        # Adjust first half of the image
        for i in range(half_point):
            for j in range(W):
                element = adjust_element_mean(element_img, big_img[i, j])
                partial_mosaic[i*N:(i+1)*N, j*M:(j+1)*M] = element
        
        # Save this partial result
        partial_mosaic_norm = (normalize_image(partial_mosaic) * 255).astype(np.uint8)
        partial_path = os.path.join(app.config['TEMP_FOLDER'], f"{job_id}_partial_mosaic.png")
        Image.fromarray(partial_mosaic_norm).save(partial_path)
        
        # Update job state
        job_states[job_id]['status'] = 'halfway_complete'
        job_states[job_id]['progress'] = 50
        job_states[job_id]['intermediate_outputs']['partial_mosaic'] = f"/api/temp/{job_id}_partial_mosaic.png"
    
    # Adjust each element block to match the target image's intensity
    for i in range(H):
        # Update progress every few rows
        if i % max(1, H // 10) == 0:
            progress = 50 + (i / H) * 40
            job_states[job_id]['status'] = 'adjusting_elements'
            job_states[job_id]['progress'] = progress
        
        for j in range(W):
            # Adjust the mean of the element_img to match the target pixel
            element = adjust_element_mean(element_img, big_img[i, j])
            mosaic[i*N:(i+1)*N, j*M:(j+1)*M] = element
    
    # Update job state
    job_states[job_id]['status'] = 'finalizing'
    job_states[job_id]['progress'] = 90
    
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

def save_as_image(array, path):
    """Save numpy array as image file"""
    array_norm = (normalize_image(array) * 255).astype(np.uint8)
    Image.fromarray(array_norm).save(path)
    return path

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Step 1: Upload files and initialize job"""
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
        # Generate unique ID for the job
        job_id = str(uuid.uuid4())
        
        # Save files with secure names
        element_filename = f"{job_id}_element{os.path.splitext(element_file.filename)[1]}"
        big_filename = f"{job_id}_big{os.path.splitext(big_file.filename)[1]}"
        
        element_path = os.path.join(app.config['UPLOAD_FOLDER'], element_filename)
        big_path = os.path.join(app.config['UPLOAD_FOLDER'], big_filename)
        
        element_file.save(element_path)
        big_file.save(big_path)
        
        # Initialize job state
        job_states[job_id] = {
            'status': 'uploaded',
            'progress': 5,
            'element_path': element_path,
            'big_path': big_path,
            'intermediate_outputs': {},
            'final_outputs': {}
        }
        
        return jsonify({
            'job_id': job_id,
            'status': 'uploaded',
            'element_url': f"/api/images/uploads/{element_filename}",
            'big_url': f"/api/images/uploads/{big_filename}",
            'next_step': f"/api/preprocess/{job_id}"
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/preprocess/<job_id>', methods=['GET'])
def preprocess_images(job_id):
    """Step 2: Preprocess images (resize and convert to grayscale)"""
    if job_id not in job_states:
        return jsonify({'error': 'Job not found'}), 404
    
    try:
        # Update job state
        job_states[job_id]['status'] = 'preprocessing'
        job_states[job_id]['progress'] = 10
        
        # Get paths
        element_path = job_states[job_id]['element_path']
        big_path = job_states[job_id]['big_path']
        
        # Open images with PIL
        element_pil = Image.open(element_path).convert('L')
        big_pil = Image.open(big_path).convert('L')
        
        # Save grayscale versions
        gray_element_filename = f"{job_id}_element_gray.png"
        gray_big_filename = f"{job_id}_big_gray.png"
        
        gray_element_path = os.path.join(app.config['TEMP_FOLDER'], gray_element_filename)
        gray_big_path = os.path.join(app.config['TEMP_FOLDER'], gray_big_filename)
        
        element_pil.save(gray_element_path)
        big_pil.save(gray_big_path)
        
        # Update job state
        job_states[job_id]['intermediate_outputs']['gray_element'] = f"/api/temp/{gray_element_filename}"
        job_states[job_id]['intermediate_outputs']['gray_big'] = f"/api/temp/{gray_big_filename}"
        
        # Resize images if needed
        element_pil = resize_image_if_needed(element_pil, MAX_ELEMENT_SIZE)
        big_pil = resize_image_if_needed(big_pil, MAX_TARGET_SIZE)
        
        # Save resized versions
        resized_element_filename = f"{job_id}_element_resized.png"
        resized_big_filename = f"{job_id}_big_resized.png"
        
        resized_element_path = os.path.join(app.config['TEMP_FOLDER'], resized_element_filename)
        resized_big_path = os.path.join(app.config['TEMP_FOLDER'], resized_big_filename)
        
        element_pil.save(resized_element_path)
        big_pil.save(resized_big_path)
        
        # Convert to numpy arrays
        element_img = np.array(element_pil)
        big_img = np.array(big_pil)
        
        # Check for mosaic size adjustment
        original_shape = big_img.shape
        adjusted_shape = check_mosaic_size(element_img.shape, big_img.shape)
        
        job_states[job_id]['element_shape'] = element_img.shape
        job_states[job_id]['original_target_shape'] = original_shape
        job_states[job_id]['adjusted_target_shape'] = adjusted_shape
        
        # Update job state
        job_states[job_id]['status'] = 'preprocessed'
        job_states[job_id]['progress'] = 25
        job_states[job_id]['intermediate_outputs']['resized_element'] = f"/api/temp/{resized_element_filename}"
        job_states[job_id]['intermediate_outputs']['resized_big'] = f"/api/temp/{resized_big_filename}"
        
        # Save paths for later use
        job_states[job_id]['resized_element_path'] = resized_element_path
        job_states[job_id]['resized_big_path'] = resized_big_path
        
        if original_shape != adjusted_shape:
            big_pil = big_pil.resize((adjusted_shape[1], adjusted_shape[0]), Image.LANCZOS)
            big_img = np.array(big_pil)
            
            adjusted_big_filename = f"{job_id}_big_adjusted.png"
            adjusted_big_path = os.path.join(app.config['TEMP_FOLDER'], adjusted_big_filename)
            big_pil.save(adjusted_big_path)
            
            job_states[job_id]['intermediate_outputs']['adjusted_big'] = f"/api/temp/{adjusted_big_filename}"
            job_states[job_id]['adjusted_big_path'] = adjusted_big_path
        
        return jsonify({
            'job_id': job_id,
            'status': 'preprocessed',
            'progress': 25,
            'element_shape': element_img.shape,
            'original_target_shape': original_shape,
            'adjusted_target_shape': adjusted_shape,
            'intermediate_outputs': job_states[job_id]['intermediate_outputs'],
            'next_step': f"/api/generate_mosaic/{job_id}"
        }), 200
    
    except Exception as e:
        job_states[job_id]['status'] = 'error'
        job_states[job_id]['error'] = str(e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_mosaic/<job_id>', methods=['GET'])
def generate_mosaic_step(job_id):
    """Step 3: Generate mosaic images"""
    if job_id not in job_states:
        return jsonify({'error': 'Job not found'}), 404
    
    try:
        # Load preprocessed images
        element_path = job_states[job_id].get('resized_element_path')
        big_path = job_states[job_id].get('adjusted_big_path') or job_states[job_id].get('resized_big_path')
        
        if not element_path or not big_path:
            return jsonify({'error': 'Preprocessing step not completed'}), 400
        
        element_pil = Image.open(element_path)
        big_pil = Image.open(big_path)
        
        element_img = np.array(element_pil)
        big_img = np.array(big_pil)
        
        # Generate mosaic (this will update job state internally)
        mosaic, simple_mosaic = create_mosaic(element_img, big_img, job_id)
        
        # Save final output images
        mosaic_filename = f"{job_id}_mosaic.png"
        simple_mosaic_filename = f"{job_id}_simple_mosaic.png"
        
        mosaic_path = os.path.join(app.config['OUTPUT_FOLDER'], mosaic_filename)
        simple_mosaic_path = os.path.join(app.config['OUTPUT_FOLDER'], simple_mosaic_filename)
        
        # Normalize and save
        mosaic_norm = (normalize_image(mosaic) * 255).astype(np.uint8)
        simple_mosaic_norm = (normalize_image(simple_mosaic) * 255).astype(np.uint8)
        
        Image.fromarray(mosaic_norm).save(mosaic_path)
        Image.fromarray(simple_mosaic_norm).save(simple_mosaic_path)
        
        # Update job state
        job_states[job_id]['status'] = 'completed'
        job_states[job_id]['progress'] = 100
        job_states[job_id]['final_outputs']['mosaic'] = f"/api/images/outputs/{mosaic_filename}"
        job_states[job_id]['final_outputs']['simple_mosaic'] = f"/api/images/outputs/{simple_mosaic_filename}"
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'progress': 100,
            'intermediate_outputs': job_states[job_id]['intermediate_outputs'],
            'final_outputs': job_states[job_id]['final_outputs'],
            'next_step': f"/api/job/{job_id}"
        }), 200
    
    except Exception as e:
        job_states[job_id]['status'] = 'error'
        job_states[job_id]['error'] = str(e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the current status and outputs of a job"""
    if job_id not in job_states:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job_states[job_id]), 200

@app.route('/api/temp/<filename>', methods=['GET'])
def get_temp_image(filename):
    """Serve an image from the temp folder"""
    try:
        return send_file(os.path.join(app.config['TEMP_FOLDER'], filename))
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/api/images/uploads/<filename>', methods=['GET'])
def get_upload_image(filename):
    """Serve an image from the uploads folder"""
    try:
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/api/images/outputs/<filename>', methods=['GET'])
def get_output_image(filename):
    """Serve an image from the output folder"""
    try:
        return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename))
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404

# Legacy endpoint for backward compatibility
@app.route('/api/generate_mosaic', methods=['POST'])
def generate_mosaic_api():
    """Legacy API endpoint for generating mosaic images in one step"""
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
        # Generate unique ID for the job
        job_id = str(uuid.uuid4())
        
        # Initialize job state
        job_states[job_id] = {
            'status': 'processing',
            'progress': 0,
            'intermediate_outputs': {},
            'final_outputs': {}
        }
        
        # Save files with secure names
        element_filename = f"{job_id}_element{os.path.splitext(element_file.filename)[1]}"
        big_filename = f"{job_id}_big{os.path.splitext(big_file.filename)[1]}"
        
        element_path = os.path.join(app.config['UPLOAD_FOLDER'], element_filename)
        big_path = os.path.join(app.config['UPLOAD_FOLDER'], big_filename)
        
        element_file.save(element_path)
        big_file.save(big_path)
        
        job_states[job_id]['progress'] = 10
        
        # Open images with PIL
        element_pil = Image.open(element_path).convert('L')
        big_pil = Image.open(big_path).convert('L')
        
        # Resize if needed
        element_pil = resize_image_if_needed(element_pil, MAX_ELEMENT_SIZE)
        big_pil = resize_image_if_needed(big_pil, MAX_TARGET_SIZE)
        
        job_states[job_id]['progress'] = 20
        
        # Convert to numpy arrays
        element_img = np.array(element_pil)
        big_img = np.array(big_pil)
        
        # Check if the mosaic would be too large and adjust target size if needed
        target_h, target_w = check_mosaic_size(element_img.shape, big_img.shape)
        
        if target_h != big_img.shape[0] or target_w != big_img.shape[1]:
            # Resize target image if needed to prevent memory issues
            big_pil = big_pil.resize((target_w, target_h), Image.LANCZOS)
            big_img = np.array(big_pil)
        
        job_states[job_id]['progress'] = 30
        
        # Generate mosaic
        mosaic, simple_mosaic = create_mosaic(element_img, big_img, job_id)
        
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
        
        # Update job state
        job_states[job_id]['status'] = 'completed'
        job_states[job_id]['progress'] = 100
        job_states[job_id]['final_outputs']['mosaic'] = f"/api/images/outputs/{mosaic_filename}"
        job_states[job_id]['final_outputs']['simple_mosaic'] = f"/api/images/outputs/{simple_mosaic_filename}"
        
        # Return URLs to access the images
        return jsonify({
            'job_id': job_id,
            'mosaic_url': f"/api/images/outputs/{mosaic_filename}",
            'simple_mosaic_url': f"/api/images/outputs/{simple_mosaic_filename}",
            'status': 'completed',
            'job_details_url': f"/api/job/{job_id}"
        }), 200
    
    except Exception as e:
        if job_id in job_states:
            job_states[job_id]['status'] = 'error'
            job_states[job_id]['error'] = str(e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/docs', methods=['GET'])
def get_api_docs():
    """Return API documentation"""
    docs = {
        "api_version": "1.0.0",
        "title": "Mosaic Generator API",
        "description": "Create mosaic images step by step",
        "endpoints": [
            {
                "path": "/api/health",
                "method": "GET",
                "description": "Health check endpoint",
                "response": {"status": "ok"}
            },
            {
                "path": "/api/upload",
                "method": "POST",
                "description": "Step 1: Upload element and target images",
                "parameters": [
                    {"name": "element_img", "type": "file", "required": True},
                    {"name": "big_img", "type": "file", "required": True}
                ],
                "response": "Job ID and URLs to access uploaded images"
            },
            {
                "path": "/api/preprocess/{job_id}",
                "method": "GET",
                "description": "Step 2: Preprocess images (resize and convert to grayscale)",
                "parameters": [
                    {"name": "job_id", "type": "path", "required": True}
                ],
                "response": "Preprocessing results and image information"
            },
            {
                "path": "/api/generate_mosaic/{job_id}",
                "method": "GET",
                "description": "Step 3: Generate mosaic images",
                "parameters": [
                    {"name": "job_id", "type": "path", "required": True}
                ],
                "response": "URLs to access generated mosaic images"
            },
            {
                "path": "/api/job/{job_id}",
                "method": "GET",
                "description": "Get the current status and outputs of a job",
                "parameters": [
                    {"name": "job_id", "type": "path", "required": True}
                ],
                "response": "Complete job state including status, progress, and all outputs"
            },
            {
                "path": "/api/temp/{filename}",
                "method": "GET",
                "description": "Serve an image from the temp folder",
                "parameters": [
                    {"name": "filename", "type": "path", "required": True}
                ],
                "response": "Image file"
            },
            {
                "path": "/api/images/uploads/{filename}",
                "method": "GET",
                "description": "Serve an image from the uploads folder",
                "parameters": [
                    {"name": "filename", "type": "path", "required": True}
                ],
                "response": "Image file"
            },
            {
                "path": "/api/images/outputs/{filename}",
                "method": "GET",
                "description": "Serve an image from the output folder",
                "parameters": [
                    {"name": "filename", "type": "path", "required": True}
                ],
                "response": "Image file"
            },
            {
                "path": "/api/generate_mosaic",
                "method": "POST",
                "description": "Legacy API endpoint for generating mosaic images in one step",
                "parameters": [
                    {"name": "element_img", "type": "file", "required": True},
                    {"name": "big_img", "type": "file", "required": True}
                ],
                "response": "URLs to access generated mosaic images"
            },
            {
                "path": "/api/docs",
                "method": "GET",
                "description": "Return API documentation",
                "response": "This documentation"
            }
        ],
        "workflow": {
            "description": "Step-by-step process to create a mosaic image",
            "steps": [
                "1. Upload images: POST /api/upload",
                "2. Preprocess images: GET /api/preprocess/{job_id}",
                "3. Generate mosaic: GET /api/generate_mosaic/{job_id}",
                "4. View results: GET /api/job/{job_id}"
            ]
        }
    }
    return jsonify(docs), 200

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

