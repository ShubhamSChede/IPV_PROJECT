"""
Mosaic generation endpoints.
"""
from flask import request, jsonify
import numpy as np
from PIL import Image
import os
from utils.validation import validate_job_id, validate_block_size
from utils.file_utils import get_file_path, get_file_url
from utils.image_utils import load_and_preprocess_image, save_image
from core.mosaic import create_mosaic, create_multiresolution_mosaic
from core.metrics import evaluate_mosaic_quality
from core.legacy_mosaic import create_mosaic as legacy_create_mosaic
from core.legacy_mosaic import normalize_image as legacy_normalize_image

def register_generation_routes(app, job_states):
    """
    Register mosaic generation-related routes.
    
    Args:
        app: Flask application
        job_states: Dictionary to store job states
    """
    
    @app.route('/api/generate_mosaic/<job_id>', methods=['GET'])
    def generate_mosaic_step(job_id):
        """Step 3: Generate mosaic images"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        try:
            # Get paths
            element_path = job_states[job_id]['resized_element_path']
            big_path = job_states[job_id].get('adjusted_big_path') or job_states[job_id]['resized_big_path']
            
            # Get parameters
            block_size = job_states[job_id]['block_size']
            color_mode = job_states[job_id].get('color_mode', 'rgb')
            color_method = job_states[job_id].get('color_method', 'average_rgb')
            
            # Load images
            element_pil = load_and_preprocess_image(element_path, color_mode=color_mode)
            big_pil = load_and_preprocess_image(big_path, color_mode=color_mode)
            
            # Convert to numpy arrays
            element_img = np.array(element_pil)
            big_img = np.array(big_pil)
            
            # Update job state
            job_states[job_id]['status'] = 'generating_mosaic'
            job_states[job_id]['progress'] = 30
            
            # Use legacy implementation for high quality results
            mosaic, simple_mosaic = legacy_create_mosaic(element_img, big_img)
            
            # Normalize and convert to uint8 for saving
            mosaic_norm = (legacy_normalize_image(mosaic) * 255).astype(np.uint8)
            simple_mosaic_norm = (legacy_normalize_image(simple_mosaic) * 255).astype(np.uint8)
            
            # Save output images
            mosaic_filename = f"{job_id}_mosaic.png"
            simple_mosaic_filename = f"{job_id}_simple_mosaic.png"
            
            mosaic_path = get_file_path(mosaic_filename, 'output')
            simple_mosaic_path = get_file_path(simple_mosaic_filename, 'output')
            
            # Save images
            save_image(mosaic_norm, mosaic_path)
            save_image(simple_mosaic_norm, simple_mosaic_path)
            
            # Calculate quality metrics
            metrics = evaluate_mosaic_quality(big_img, mosaic_norm)
            
            # Update job state
            job_states[job_id]['status'] = 'completed'
            job_states[job_id]['progress'] = 100
            job_states[job_id]['final_outputs'] = {
                'mosaic': get_file_url(mosaic_filename, 'output'),
                'simple_mosaic': get_file_url(simple_mosaic_filename, 'output')
            }
            job_states[job_id]['metrics'] = metrics
            
            return jsonify({
                'job_id': job_id,
                'status': 'completed',
                'progress': 100,
                'block_size': block_size,
                'color_mode': color_mode,
                'color_method': color_method,
                'intermediate_outputs': job_states[job_id]['intermediate_outputs'],
                'final_outputs': job_states[job_id]['final_outputs'],
                'metrics': metrics,
                'next_step': f"/api/apply_filter/{job_id}"
            }), 200
        
        except Exception as e:
            job_states[job_id]['status'] = 'error'
            job_states[job_id]['error'] = str(e)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/multiresolution/<job_id>', methods=['GET'])
    def generate_multiresolution(job_id):
        """Generate mosaics at multiple resolutions"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        try:
            # Get paths
            element_path = job_states[job_id]['resized_element_path']
            big_path = job_states[job_id].get('adjusted_big_path') or job_states[job_id]['resized_big_path']
            
            # Get parameters
            color_mode = job_states[job_id].get('color_mode', 'rgb')
            color_method = job_states[job_id].get('color_method', 'average_rgb')
            
            # Get block sizes (can be specified in query params)
            block_sizes = request.args.get('block_sizes')
            if block_sizes:
                try:
                    block_sizes = [int(size) for size in block_sizes.split(',')]
                except ValueError:
                    return jsonify({'error': 'Invalid block sizes format'}), 400
            else:
                # Default block sizes
                from config import MIN_BLOCK_SIZE, MAX_BLOCK_SIZE
                block_sizes = [MIN_BLOCK_SIZE, (MIN_BLOCK_SIZE + MAX_BLOCK_SIZE) // 2, MAX_BLOCK_SIZE]
            
            # Validate block sizes
            validated_sizes = []
            for size in block_sizes:
                is_valid, result = validate_block_size(size)
                if is_valid:
                    validated_sizes.append(result)
            
            if not validated_sizes:
                return jsonify({'error': 'No valid block sizes provided'}), 400
            
            # Load images
            element_pil = load_and_preprocess_image(element_path, color_mode=color_mode)
            big_pil = load_and_preprocess_image(big_path, color_mode=color_mode)
            
            # Convert to numpy arrays
            element_img = np.array(element_pil)
            big_img = np.array(big_pil)
            
            # Update job state
            job_states[job_id]['status'] = 'generating_multiresolution'
            job_states[job_id]['progress'] = 30
            
            # Generate mosaics at different resolutions
            results = {}
            multi_outputs = {}
            
            for block_size in validated_sizes:
                # Update job state
                job_states[job_id]['status'] = f'generating_mosaic_size_{block_size}'
                
                # Generate mosaic
                mosaic, simple_mosaic = create_mosaic(
                    element_img,
                    big_img,
                    block_size,
                    color_method=color_method,
                    adjust_colors=True
                )
                
                # Save output images
                mosaic_filename = f"{job_id}_mosaic_{block_size}.png"
                simple_mosaic_filename = f"{job_id}_simple_mosaic_{block_size}.png"
                
                mosaic_path = get_file_path(mosaic_filename, 'output')
                simple_mosaic_path = get_file_path(simple_mosaic_filename, 'output')
                
                # Save images
                save_image(mosaic, mosaic_path)
                save_image(simple_mosaic, simple_mosaic_path)
                
                # Calculate quality metrics
                metrics = evaluate_mosaic_quality(big_img, mosaic)
                
                # Add to results
                results[block_size] = {
                    'mosaic': mosaic,
                    'simple_mosaic': simple_mosaic,
                    'metrics': metrics
                }
                
                # Add to multi outputs
                multi_outputs[str(block_size)] = {
                    'mosaic': get_file_url(mosaic_filename, 'output'),
                    'simple_mosaic': get_file_url(simple_mosaic_filename, 'output'),
                    'metrics': metrics
                }
            
            # Update job state
            job_states[job_id]['status'] = 'completed'
            job_states[job_id]['progress'] = 100
            job_states[job_id]['multi_outputs'] = multi_outputs
            
            return jsonify({
                'job_id': job_id,
                'status': 'completed',
                'progress': 100,
                'block_sizes': validated_sizes,
                'color_mode': color_mode,
                'color_method': color_method,
                'multi_outputs': multi_outputs,
                'next_step': f"/api/job/{job_id}"
            }), 200
        
        except Exception as e:
            job_states[job_id]['status'] = 'error'
            job_states[job_id]['error'] = str(e)
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/generate_mosaic', methods=['POST'])
    def generate_mosaic_api():
        """Legacy API endpoint for generating mosaic images in one step"""
        # Validate request
        from utils.validation import validate_file_upload
        is_valid, error = validate_file_upload(request)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        try:
            # Get files
            element_file = request.files['element_img']
            big_file = request.files['big_img']
            
            # Get parameters
            block_size = request.form.get('block_size')
            if block_size:
                is_valid, result = validate_block_size(block_size)
                if not is_valid:
                    return jsonify({'error': result}), 400
                block_size = result
            else:
                from config import DEFAULT_BLOCK_SIZE
                block_size = DEFAULT_BLOCK_SIZE
            
            color_mode = request.form.get('color_mode', 'rgb')
            color_method = request.form.get('color_method', 'average_rgb')
            
            # Save files
            from utils.file_utils import save_uploaded_file
            job_id, element_filename, element_path = save_uploaded_file(element_file)
            _, big_filename, big_path = save_uploaded_file(big_file, f"{job_id}_big{os.path.splitext(big_file.filename)[1]}")
            
            # Initialize job state
            job_states[job_id] = {
                'status': 'processing',
                'progress': 0,
                'element_path': element_path,
                'big_path': big_path,
                'block_size': block_size,
                'color_mode': color_mode,
                'color_method': color_method,
                'intermediate_outputs': {},
                'final_outputs': {},
                'metrics': {}
            }
            
            # Load and preprocess images
            from utils.image_utils import load_and_preprocess_image
            element_pil = load_and_preprocess_image(element_path, color_mode=color_mode)
            big_pil = load_and_preprocess_image(big_path, color_mode=color_mode)
            
            # Resize images if needed
            from config import MAX_ELEMENT_SIZE, MAX_TARGET_SIZE
            from utils.image_utils import resize_image_if_needed
            element_pil = resize_image_if_needed(element_pil, MAX_ELEMENT_SIZE)
            big_pil = resize_image_if_needed(big_pil, MAX_TARGET_SIZE)
            
            # Convert to numpy arrays
            element_img = np.array(element_pil)
            big_img = np.array(big_pil)
            
            # Check mosaic size
            from utils.image_utils import check_mosaic_size
            if len(big_img.shape) == 3:
                target_h, target_w, _ = big_img.shape
            else:
                target_h, target_w = big_img.shape
                
            adjusted_dims = check_mosaic_size(element_img.shape[:2], (target_h, target_w), block_size)
            
            # Resize if needed to prevent memory issues
            if adjusted_dims != (target_h, target_w):
                from PIL import Image
            
            # Resize if needed to prevent memory issues
            if adjusted_dims != (target_h, target_w):
                from PIL import Image
                adjusted_h, adjusted_w = adjusted_dims
                big_pil = big_pil.resize((adjusted_w, adjusted_h), Image.LANCZOS)
                big_img = np.array(big_pil)

            # Generate mosaic using the legacy implementation
            job_states[job_id]['progress'] = 30
            mosaic, simple_mosaic = legacy_create_mosaic(element_img, big_img)
            
            # Normalize and convert to uint8 for saving
            mosaic_norm = (legacy_normalize_image(mosaic) * 255).astype(np.uint8)
            simple_mosaic_norm = (legacy_normalize_image(simple_mosaic) * 255).astype(np.uint8)
            
            # Save output images
            from utils.file_utils import get_file_path, get_file_url
            from utils.image_utils import save_image
            
            mosaic_filename = f"{job_id}_mosaic.png"
            simple_mosaic_filename = f"{job_id}_simple_mosaic.png"
            
            mosaic_path = get_file_path(mosaic_filename, 'output')
            simple_mosaic_path = get_file_path(simple_mosaic_filename, 'output')
            
            # Save images
            save_image(mosaic_norm, mosaic_path)
            save_image(simple_mosaic_norm, simple_mosaic_path)
            
            # Calculate quality metrics if needed
            from core.metrics import evaluate_mosaic_quality
            metrics = evaluate_mosaic_quality(big_img, mosaic_norm)
            
            # Update job state
            job_states[job_id]['status'] = 'completed'
            job_states[job_id]['progress'] = 100
            job_states[job_id]['final_outputs'] = {
                'mosaic': get_file_url(mosaic_filename, 'output'),
                'simple_mosaic': get_file_url(simple_mosaic_filename, 'output')
            }
            job_states[job_id]['metrics'] = metrics
            
            # Return response
            return jsonify({
                'job_id': job_id,
                'mosaic_url': get_file_url(mosaic_filename, 'output'),
                'simple_mosaic_url': get_file_url(simple_mosaic_filename, 'output')
            }), 200
        
        except Exception as e:
            if job_id in job_states:
                job_states[job_id]['status'] = 'error'
                job_states[job_id]['error'] = str(e)
            return jsonify({'error': str(e)}), 500