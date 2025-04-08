"""
Image preprocessing endpoints.
"""
from flask import request, jsonify
import numpy as np
from PIL import Image
import os
from utils.validation import validate_job_id, validate_block_size
from utils.file_utils import get_file_path, get_file_url
from utils.image_utils import resize_image_if_needed, check_mosaic_size, load_and_preprocess_image, save_image

def register_preprocess_routes(app, job_states):
    """
    Register preprocessing-related routes.
    
    Args:
        app: Flask application
        job_states: Dictionary to store job states
    """
    
    @app.route('/api/preprocess/<job_id>', methods=['GET'])
    def preprocess_images(job_id):
        """Step 2: Preprocess images (resize and prepare for mosaic creation)"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        try:
            # Update job state
            job_states[job_id]['status'] = 'preprocessing'
            job_states[job_id]['progress'] = 10
            
            # Check if required paths exist in job state
            if 'element_path' not in job_states[job_id]:
                return jsonify({'error': 'Element path not found in job state'}), 400
                
            if 'big_path' not in job_states[job_id]:
                return jsonify({'error': 'Target image path not found in job state'}), 400
            
            # Get paths safely
            element_path = job_states[job_id]['element_path']
            big_path = job_states[job_id]['big_path']   
            
            # Get block size from job state or use default
            from config import DEFAULT_BLOCK_SIZE
            block_size = job_states[job_id].get('block_size', DEFAULT_BLOCK_SIZE)
            
            # Get color mode from job state or use default
            color_mode = job_states[job_id].get('color_mode', 'rgb')
            
            # Open images
            color_mode_pil = 'RGB' if color_mode == 'rgb' else 'L'
            element_pil = load_and_preprocess_image(element_path, color_mode=color_mode)
            big_pil = load_and_preprocess_image(big_path, color_mode=color_mode)
            
            # Save original images in requested color mode
            color_element_filename = f"{job_id}_element_{color_mode}.png"
            color_big_filename = f"{job_id}_big_{color_mode}.png"
            
            color_element_path = get_file_path(color_element_filename, 'temp')
            color_big_path = get_file_path(color_big_filename, 'temp')
            
            element_pil.save(color_element_path)
            big_pil.save(color_big_path)
            
            # Update job state with color images
            job_states[job_id]['intermediate_outputs'][f'{color_mode}_element'] = get_file_url(color_element_filename, 'temp')
            job_states[job_id]['intermediate_outputs'][f'{color_mode}_big'] = get_file_url(color_big_filename, 'temp')
            
            # Resize element image if needed
            from config import MAX_ELEMENT_SIZE
            element_pil = resize_image_if_needed(element_pil, MAX_ELEMENT_SIZE)
            
            # Save resized element
            resized_element_filename = f"{job_id}_element_resized.png"
            resized_element_path = get_file_path(resized_element_filename, 'temp')
            element_pil.save(resized_element_path)
            
            # Update job state with resized element
            job_states[job_id]['intermediate_outputs']['resized_element'] = get_file_url(resized_element_filename, 'temp')
            job_states[job_id]['resized_element_path'] = resized_element_path
            
            # Convert to numpy arrays
            element_img = np.array(element_pil)
            big_img = np.array(big_pil)
            
            # Check if target needs to be adjusted to be a multiple of block_size
            h, w = big_img.shape[:2]
            adjusted_h = h - (h % block_size)
            adjusted_w = w - (w % block_size)
            
            # If dimensions need adjustment, crop the image
            if adjusted_h != h or adjusted_w != w:
                big_pil = big_pil.crop((0, 0, adjusted_w, adjusted_h))
                big_img = np.array(big_pil)
                
                # Save adjusted target
                adjusted_big_filename = f"{job_id}_big_adjusted.png"
                adjusted_big_path = get_file_path(adjusted_big_filename, 'temp')
                big_pil.save(adjusted_big_path)
                
                # Update job state with adjusted target
                job_states[job_id]['intermediate_outputs']['adjusted_big'] = get_file_url(adjusted_big_filename, 'temp')
                job_states[job_id]['adjusted_big_path'] = adjusted_big_path
            
            # Check for mosaic size limitation
            from config import MAX_TARGET_SIZE
            big_pil = resize_image_if_needed(big_pil, MAX_TARGET_SIZE)
            
            # Save resized target
            resized_big_filename = f"{job_id}_big_resized.png"
            resized_big_path = get_file_path(resized_big_filename, 'temp')
            big_pil.save(resized_big_path)
            
            # Update job state with resized target
            job_states[job_id]['intermediate_outputs']['resized_big'] = get_file_url(resized_big_filename, 'temp')
            job_states[job_id]['resized_big_path'] = resized_big_path
            
            # Update job state
            job_states[job_id]['status'] = 'preprocessed'
            job_states[job_id]['progress'] = 25
            job_states[job_id]['element_shape'] = element_img.shape
            job_states[job_id]['target_shape'] = big_img.shape
            job_states[job_id]['block_size'] = block_size
            
            return jsonify({
                'job_id': job_id,
                'status': 'preprocessed',
                'progress': 25,
                'element_shape': element_img.shape,
                'target_shape': big_img.shape,
                'block_size': block_size,
                'color_mode': color_mode,
                'intermediate_outputs': job_states[job_id]['intermediate_outputs'],
                'next_step': f"/api/generate_mosaic/{job_id}"
            }), 200
        
        except Exception as e:
            job_states[job_id]['status'] = 'error'
            job_states[job_id]['error'] = str(e)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/set_block_size/<job_id>', methods=['POST'])
    def set_block_size(job_id):
        """Set or update block size for an existing job"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        # Get block size from request
        block_size = request.json.get('block_size')
        if block_size is None:
            return jsonify({'error': 'Missing block_size parameter'}), 400
        
        # Validate block size
        is_valid, result = validate_block_size(block_size)
        if not is_valid:
            return jsonify({'error': result}), 400
        
        # Update job state
        job_states[job_id]['block_size'] = result
        
        return jsonify({
            'job_id': job_id,
            'block_size': result,
            'message': f'Block size updated to {result}'
        }), 200
    
    @app.route('/api/multiresolution_preview/<job_id>', methods=['GET'])
    def multiresolution_preview(job_id):
        """Generate previews at different block sizes"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        try:
            # Get paths
            element_path = job_states[job_id]['resized_element_path']
            big_path = job_states[job_id].get('adjusted_big_path') or job_states[job_id]['resized_big_path']
            
            # Get color mode
            color_mode = job_states[job_id].get('color_mode', 'rgb')
            
            # Load images
            element_pil = load_and_preprocess_image(element_path, color_mode=color_mode)
            big_pil = load_and_preprocess_image(big_path, color_mode=color_mode)
            
            # Get block sizes to preview (small, medium, large)
            from config import MIN_BLOCK_SIZE, MAX_BLOCK_SIZE
            block_sizes = [
                MIN_BLOCK_SIZE,
                (MIN_BLOCK_SIZE + MAX_BLOCK_SIZE) // 2,
                MAX_BLOCK_SIZE
            ]
            
            # Create small preview for each block size
            preview_outputs = {}
            for block_size in block_sizes:
                # Create a very small preview target (just for quick preview)
                preview_size = (200, 200)
                preview_target = big_pil.resize(preview_size, Image.LANCZOS)
                
                # Adjust to be multiple of block_size
                adjusted_w = (preview_size[0] // block_size) * block_size
                adjusted_h = (preview_size[1] // block_size) * block_size
                preview_target = preview_target.crop((0, 0, adjusted_w, adjusted_h))
                
                # Save preview target
                preview_target_filename = f"{job_id}_preview_target_{block_size}.png"
                preview_target_path = get_file_path(preview_target_filename, 'temp')
                preview_target.save(preview_target_path)
                
                # Convert to numpy array
                preview_target_np = np.array(preview_target)
                
                # Create a simple grid preview
                from core.mosaic import create_image_matrix
                element_np = np.array(element_pil)
                grid_size = (adjusted_h // block_size, adjusted_w // block_size)
                preview_mosaic = create_image_matrix(element_np, grid_size, block_size)
                
                # Save preview mosaic
                preview_mosaic_filename = f"{job_id}_preview_mosaic_{block_size}.png"
                preview_mosaic_path = get_file_path(preview_mosaic_filename, 'temp')
                save_image(preview_mosaic, preview_mosaic_path)
                
                # Add to outputs
                preview_outputs[str(block_size)] = {
                    'target': get_file_url(preview_target_filename, 'temp'),
                    'mosaic': get_file_url(preview_mosaic_filename, 'temp')
                }
            
            # Update job state
            job_states[job_id]['preview_outputs'] = preview_outputs
            
            return jsonify({
                'job_id': job_id,
                'preview_outputs': preview_outputs,
                'message': 'Preview images generated successfully'
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500