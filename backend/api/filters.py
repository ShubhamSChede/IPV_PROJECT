"""
Filter application endpoints.
"""
from flask import request, jsonify
import numpy as np
from PIL import Image
import os
from utils.validation import validate_job_id, validate_filter
from utils.file_utils import get_file_path, get_file_url
from utils.image_utils import load_and_preprocess_image, save_image
from core.filters import apply_filter, apply_multiple_filters

def register_filter_routes(app, job_states):
    """
    Register filter-related routes.
    
    Args:
        app: Flask application
        job_states: Dictionary to store job states
    """
    
    @app.route('/api/apply_filter/<job_id>', methods=['POST'])
    def apply_single_filter(job_id):
        """Apply a filter to a mosaic image"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        # Check if job has completed mosaic generation
        if job_states[job_id].get('status') != 'completed' or 'final_outputs' not in job_states[job_id]:
            return jsonify({'error': 'Mosaic generation not completed for this job'}), 400
        
        # Get filter from request
        filter_name = request.json.get('filter')
        if not filter_name:
            return jsonify({'error': 'Missing filter parameter'}), 400
        
        # Validate filter
        is_valid, result = validate_filter(filter_name)
        if not is_valid:
            return jsonify({'error': result}), 400
        
        try:
            # Get path to mosaic image
            mosaic_url = job_states[job_id]['final_outputs'].get('mosaic')
            if not mosaic_url:
                return jsonify({'error': 'Mosaic image not found'}), 404
            
            mosaic_filename = os.path.basename(mosaic_url.split('/')[-1])
            mosaic_path = get_file_path(mosaic_filename, 'output')
            
            # Load mosaic image
            mosaic_pil = Image.open(mosaic_path)
            
            # Apply filter
            filtered_mosaic = apply_filter(mosaic_pil, filter_name)
            
            # Save filtered image
            filtered_filename = f"{job_id}_mosaic_{filter_name}.png"
            filtered_path = get_file_path(filtered_filename, 'output')
            filtered_mosaic.save(filtered_path)
            
            # Update job state
            if 'filtered_outputs' not in job_states[job_id]:
                job_states[job_id]['filtered_outputs'] = {}
            
            job_states[job_id]['filtered_outputs'][filter_name] = get_file_url(filtered_filename, 'output')
            
            return jsonify({
                'job_id': job_id,
                'filter': filter_name,
                'filtered_url': get_file_url(filtered_filename, 'output'),
                'message': f'Filter {filter_name} applied successfully'
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/available_filters', methods=['GET'])
    def get_available_filters():
        """Get list of available filters"""
        from config import AVAILABLE_FILTERS
        return jsonify({
            'filters': AVAILABLE_FILTERS
        }), 200
    
    @app.route('/api/filter_preview/<job_id>', methods=['GET'])
    def filter_preview(job_id):
        """Generate previews with different filters"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        # Check if job has completed mosaic generation
        if job_states[job_id].get('status') != 'completed' or 'final_outputs' not in job_states[job_id]:
            return jsonify({'error': 'Mosaic generation not completed for this job'}), 400
        
        try:
            # Get path to mosaic image
            mosaic_url = job_states[job_id]['final_outputs'].get('mosaic')
            if not mosaic_url:
                return jsonify({'error': 'Mosaic image not found'}), 404
            
            mosaic_filename = os.path.basename(mosaic_url.split('/')[-1])
            mosaic_path = get_file_path(mosaic_filename, 'output')
            
            # Load mosaic image
            mosaic_pil = Image.open(mosaic_path)
            
            # Create a smaller preview for faster processing
            preview_size = (300, 300)
            aspect_ratio = mosaic_pil.width / mosaic_pil.height
            if aspect_ratio > 1:
                preview_width = preview_size[0]
                preview_height = int(preview_width / aspect_ratio)
            else:
                preview_height = preview_size[1]
                preview_width = int(preview_height * aspect_ratio)
            
            preview_mosaic = mosaic_pil.resize((preview_width, preview_height), Image.LANCZOS)
            
            # Get filters to preview
            from config import AVAILABLE_FILTERS
            
            # Generate filter previews
            preview_outputs = {}
            for filter_name in AVAILABLE_FILTERS:
                # Apply filter
                filtered_preview = apply_filter(preview_mosaic, filter_name)
                
                # Save filtered preview
                preview_filename = f"{job_id}_preview_{filter_name}.png"
                preview_path = get_file_path(preview_filename, 'temp')
                filtered_preview.save(preview_path)
                
                # Add to outputs
                preview_outputs[filter_name] = get_file_url(preview_filename, 'temp')
            
            # Update job state
            job_states[job_id]['filter_previews'] = preview_outputs
            
            return jsonify({
                'job_id': job_id,
                'filter_previews': preview_outputs,
                'message': 'Filter previews generated successfully'
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/compare_filters/<job_id>', methods=['POST'])
    def compare_filters(job_id):
        """Generate side-by-side comparison of multiple filters"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        # Check if job has completed mosaic generation
        if job_states[job_id].get('status') != 'completed' or 'final_outputs' not in job_states[job_id]:
            return jsonify({'error': 'Mosaic generation not completed for this job'}), 400
        
        # Get filters from request
        filters = request.json.get('filters', [])
        if not filters:
            return jsonify({'error': 'Missing filters parameter'}), 400
        
        # Validate filters
        valid_filters = []
        for filter_name in filters:
            is_valid, result = validate_filter(filter_name)
            if is_valid:
                valid_filters.append(result)
        
        if not valid_filters:
            return jsonify({'error': 'No valid filters provided'}), 400
        
        try:
            # Get path to mosaic image
            mosaic_url = job_states[job_id]['final_outputs'].get('mosaic')
            if not mosaic_url:
                return jsonify({'error': 'Mosaic image not found'}), 404
            
            mosaic_filename = os.path.basename(mosaic_url.split('/')[-1])
            mosaic_path = get_file_path(mosaic_filename, 'output')
            
            # Load mosaic image
            mosaic_pil = Image.open(mosaic_path)
            
            # Calculate the size of the comparison image
            max_filters = 4  # Max number of filters to show side by side
            n_rows = (len(valid_filters) + 1 + max_filters - 1) // max_filters  # +1 for original
            n_cols = min(len(valid_filters) + 1, max_filters)  # +1 for original
            
            # Create comparison image
            thumb_width = 300
            thumb_height = int(thumb_width * mosaic_pil.height / mosaic_pil.width)
            
            comparison_width = thumb_width * n_cols
            comparison_height = thumb_height * n_rows
            
            comparison_img = Image.new('RGB', (comparison_width, comparison_height), (255, 255, 255))
            
            # Add original image
            original_thumb = mosaic_pil.resize((thumb_width, thumb_height), Image.LANCZOS)
            comparison_img.paste(original_thumb, (0, 0))
            
            # Add filtered images
            for i, filter_name in enumerate(valid_filters):
                # Apply filter
                filtered_mosaic = apply_filter(mosaic_pil, filter_name)
                
                # Resize to thumbnail
                filtered_thumb = filtered_mosaic.resize((thumb_width, thumb_height), Image.LANCZOS)
                
                # Calculate position
                pos_i = (i + 1) // n_cols
                pos_j = (i + 1) % n_cols
                
                # Paste into comparison image
                comparison_img.paste(filtered_thumb, (pos_j * thumb_width, pos_i * thumb_height))
            
            # Save comparison image
            comparison_filename = f"{job_id}_filter_comparison.png"
            comparison_path = get_file_path(comparison_filename, 'output')
            comparison_img.save(comparison_path)
            
            # Update job state
            job_states[job_id]['filter_comparison'] = get_file_url(comparison_filename, 'output')
            
            return jsonify({
                'job_id': job_id,
                'filters': valid_filters,
                'comparison_url': get_file_url(comparison_filename, 'output'),
                'message': 'Filter comparison generated successfully'
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500