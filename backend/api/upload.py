"""
File upload endpoints.
"""
from flask import request, jsonify
from utils.validation import validate_file_upload
from utils.file_utils import save_uploaded_file, get_file_url
import os

def register_upload_routes(app, job_states):
    """
    Register upload-related routes.
    
    Args:
        app: Flask application
        job_states: Dictionary to store job states
    """
    
    @app.route('/api/upload', methods=['POST'])
    def upload_files():
        """Step 1: Upload files and initialize job"""
        # Validate request
        is_valid, error = validate_file_upload(request)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        try:
            # Get files
            element_file = request.files['element_img']
            big_file = request.files['big_img']
            
            # Save files
            job_id, element_filename, element_path = save_uploaded_file(element_file)
            _, big_filename, big_path = save_uploaded_file(big_file, f"{job_id}_big{os.path.splitext(big_file.filename)[1]}")
            
            # Get block size parameter (optional)
            from config import DEFAULT_BLOCK_SIZE
            block_size = request.form.get('block_size', DEFAULT_BLOCK_SIZE)
            try:
                block_size = int(block_size)
            except (ValueError, TypeError):
                block_size = DEFAULT_BLOCK_SIZE
            
            # Get color mode parameter (optional)
            color_mode = request.form.get('color_mode', 'rgb')
            
            # Get color matching method parameter (optional)
            color_method = request.form.get('color_method', 'average_rgb')
            
            # Initialize job state
            job_states[job_id] = {
                'status': 'uploaded',
                'progress': 5,
                'element_path': element_path,
                'big_path': big_path,
                'block_size': block_size,
                'color_mode': color_mode,
                'color_method': color_method,
                'intermediate_outputs': {},
                'final_outputs': {},
                'metrics': {}
            }
            
            # Generate URLs
            element_url = get_file_url(element_filename, 'upload')
            big_url = get_file_url(big_filename, 'upload')
            
            return jsonify({
                'job_id': job_id,
                'status': 'uploaded',
                'progress': 5,
                'element_url': element_url,
                'big_url': big_url,
                'block_size': block_size,
                'color_mode': color_mode,
                'color_method': color_method,
                'next_step': f"/api/preprocess/{job_id}"
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/upload_element', methods=['POST'])
    def upload_element():
        """Upload only the element image"""
        # Check if file is in the request
        if 'element_img' not in request.files:
            return jsonify({'error': 'Missing element image'}), 400
        
        element_file = request.files['element_img']
        
        # Check if filename is valid
        if element_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Check file extension
        from utils.file_utils import allowed_file
        if not allowed_file(element_file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        try:
            # Save file
            job_id, element_filename, element_path = save_uploaded_file(element_file)
            
            # Initialize job state
            job_states[job_id] = {
                'status': 'element_uploaded',
                'progress': 2,
                'element_path': element_path,
                'intermediate_outputs': {},
                'final_outputs': {}
            }
            
            # Generate URL
            element_url = get_file_url(element_filename, 'upload')
            
            return jsonify({
                'job_id': job_id,
                'status': 'element_uploaded',
                'progress': 2,
                'element_url': element_url,
                'next_step': f"/api/upload_target/{job_id}"
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/upload_target/<job_id>', methods=['POST'])
    def upload_target(job_id):
        """Upload only the target image for an existing job"""
        # Check if job exists
        from utils.validation import validate_job_id
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        # Check if file is in the request
        if 'big_img' not in request.files:
            return jsonify({'error': 'Missing target image'}), 400
        
        big_file = request.files['big_img']
        
        # Check if filename is valid
        if big_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Check file extension
        from utils.file_utils import allowed_file
        if not allowed_file(big_file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        try:
            # Save file
            _, big_filename, big_path = save_uploaded_file(big_file, f"{job_id}_big{os.path.splitext(big_file.filename)[1]}")
            
            # Update job state
            job_states[job_id]['big_path'] = big_path
            job_states[job_id]['status'] = 'uploaded'
            job_states[job_id]['progress'] = 5
            
            # Generate URL
            big_url = get_file_url(big_filename, 'upload')
            
            # Add to job state
            job_states[job_id]['big_url'] = big_url
            
            return jsonify({
                'job_id': job_id,
                'status': 'uploaded',
                'progress': 5,
                'element_url': get_file_url(os.path.basename(job_states[job_id]['element_path']), 'upload'),
                'big_url': big_url,
                'next_step': f"/api/preprocess/{job_id}"
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500