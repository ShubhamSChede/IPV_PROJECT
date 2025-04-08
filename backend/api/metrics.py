"""
Quality metrics endpoints.
"""
from flask import request, jsonify
import numpy as np
from PIL import Image
import os
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from utils.validation import validate_job_id
from utils.file_utils import get_file_path, get_file_url
from utils.image_utils import load_and_preprocess_image
from core.metrics import evaluate_mosaic_quality, calculate_ssim, calculate_mse, calculate_psnr

def register_metrics_routes(app, job_states):
    """
    Register metrics-related routes.
    
    Args:
        app: Flask application
        job_states: Dictionary to store job states
    """
    
    @app.route('/api/metrics/<job_id>', methods=['GET'])
    def get_metrics(job_id):
        """Get quality metrics for a completed mosaic job"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        # Check if job has completed mosaic generation
        if job_states[job_id].get('status') != 'completed' or 'final_outputs' not in job_states[job_id]:
            return jsonify({'error': 'Mosaic generation not completed for this job'}), 400
        
        # Get metrics from job state
        metrics = job_states[job_id].get('metrics', {})
        
        # If metrics don't exist yet, calculate them
        if not metrics:
            try:
                # Get paths to images
                big_path = job_states[job_id].get('adjusted_big_path') or job_states[job_id]['resized_big_path']
                mosaic_url = job_states[job_id]['final_outputs'].get('mosaic')
                if not mosaic_url:
                    return jsonify({'error': 'Mosaic image not found'}), 404
                
                mosaic_filename = os.path.basename(mosaic_url.split('/')[-1])
                mosaic_path = get_file_path(mosaic_filename, 'output')
                
                # Load images
                color_mode = job_states[job_id].get('color_mode', 'rgb')
                big_pil = load_and_preprocess_image(big_path, color_mode=color_mode)
                mosaic_pil = Image.open(mosaic_path)
                
                # Convert to numpy arrays
                big_img = np.array(big_pil)
                mosaic_img = np.array(mosaic_pil)
                
                # Calculate metrics
                metrics = evaluate_mosaic_quality(big_img, mosaic_img)
                
                # Update job state
                job_states[job_id]['metrics'] = metrics
            
            except Exception as e:
                return jsonify({'error': f'Error calculating metrics: {str(e)}'}), 500
        
        return jsonify({
            'job_id': job_id,
            'metrics': metrics,
            'message': 'Quality metrics retrieved successfully'
        }), 200
    
    @app.route('/api/metrics/compare/<job_id>', methods=['GET'])
    def compare_metrics(job_id):
        """Compare metrics for different block sizes or filters"""
        # Validate job ID
        is_valid, error = validate_job_id(job_id, job_states)
        if not is_valid:
            return jsonify({'error': error}), 404
        
        # Check if job has multi-resolution or filter outputs
        has_multi = 'multi_outputs' in job_states[job_id]
        has_filters = 'filtered_outputs' in job_states[job_id]
        
        if not has_multi and not has_filters:
            return jsonify({'error': 'No multi-resolution or filter outputs found for this job'}), 400
        
        comparison_type = request.args.get('type', 'resolution' if has_multi else 'filter')
        
        if comparison_type == 'resolution' and not has_multi:
            return jsonify({'error': 'No multi-resolution outputs found for this job'}), 400
        
        if comparison_type == 'filter' and not has_filters:
            return jsonify({'error': 'No filter outputs found for this job'}), 400
        
        try:
            # Get target image
            big_path = job_states[job_id].get('adjusted_big_path') or job_states[job_id]['resized_big_path']
            color_mode = job_states[job_id].get('color_mode', 'rgb')
            big_pil = load_and_preprocess_image(big_path, color_mode=color_mode)
            big_img = np.array(big_pil)
            
            # Get comparison data
            comparison_data = {}
            
            if comparison_type == 'resolution':
                # Compare metrics for different block sizes
                multi_outputs = job_states[job_id]['multi_outputs']
                
                for block_size, output in multi_outputs.items():
                    comparison_data[block_size] = output.get('metrics', {})
            
            elif comparison_type == 'filter':
                # Compare metrics for different filters
                mosaic_url = job_states[job_id]['final_outputs'].get('mosaic')
                mosaic_filename = os.path.basename(mosaic_url.split('/')[-1])
                mosaic_path = get_file_path(mosaic_filename, 'output')
                
                filtered_outputs = job_states[job_id]['filtered_outputs']
                
                # Add metrics for original mosaic
                original_mosaic = Image.open(mosaic_path)
                original_img = np.array(original_mosaic)
                original_metrics = evaluate_mosaic_quality(big_img, original_img)
                comparison_data['original'] = original_metrics
                
                # Calculate metrics for each filter
                for filter_name, filter_url in filtered_outputs.items():
                    filter_filename = os.path.basename(filter_url.split('/')[-1])
                    filter_path = get_file_path(filter_filename, 'output')
                    
                    filtered_img = Image.open(filter_path)
                    filtered_np = np.array(filtered_img)
                    
                    filter_metrics = evaluate_mosaic_quality(big_img, filtered_np)
                    comparison_data[filter_name] = filter_metrics
            
            # Generate comparison plot
            plot_data = generate_metrics_plot(comparison_data, comparison_type)
            
            return jsonify({
                'job_id': job_id,
                'comparison_type': comparison_type,
                'comparison_data': comparison_data,
                'plot': plot_data,
                'message': 'Metrics comparison generated successfully'
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/metrics/batch', methods=['POST'])
    def batch_metrics():
        """Calculate metrics for a batch of jobs"""
        # Get job IDs from request
        job_ids = request.json.get('job_ids', [])
        if not job_ids:
            return jsonify({'error': 'No job IDs provided'}), 400
        
        batch_results = {}
        
        for job_id in job_ids:
            # Validate job ID
            is_valid, _ = validate_job_id(job_id, job_states)
            if not is_valid:
                batch_results[job_id] = {'error': 'Job not found'}
                continue
            
            # Check if job has completed mosaic generation
            if job_states[job_id].get('status') != 'completed' or 'final_outputs' not in job_states[job_id]:
                batch_results[job_id] = {'error': 'Mosaic generation not completed for this job'}
                continue
            
            # Get metrics from job state
            metrics = job_states[job_id].get('metrics', {})
            
            # If metrics don't exist yet, calculate them
            if not metrics:
                try:
                    # Get paths to images
                    big_path = job_states[job_id].get('adjusted_big_path') or job_states[job_id]['resized_big_path']
                    mosaic_url = job_states[job_id]['final_outputs'].get('mosaic')
                    if not mosaic_url:
                        batch_results[job_id] = {'error': 'Mosaic image not found'}
                        continue
                    
                    mosaic_filename = os.path.basename(mosaic_url.split('/')[-1])
                    mosaic_path = get_file_path(mosaic_filename, 'output')
                    
                    # Load images
                    color_mode = job_states[job_id].get('color_mode', 'rgb')
                    big_pil = load_and_preprocess_image(big_path, color_mode=color_mode)
                    mosaic_pil = Image.open(mosaic_path)
                    
                    # Convert to numpy arrays
                    big_img = np.array(big_pil)
                    mosaic_img = np.array(mosaic_pil)
                    
                    # Calculate metrics
                    metrics = evaluate_mosaic_quality(big_img, mosaic_img)
                    
                    # Update job state
                    job_states[job_id]['metrics'] = metrics
                
                except Exception as e:
                    batch_results[job_id] = {'error': f'Error calculating metrics: {str(e)}'}
                    continue
            
            batch_results[job_id] = {
                'metrics': metrics,
                'block_size': job_states[job_id].get('block_size'),
                'color_mode': job_states[job_id].get('color_mode'),
                'color_method': job_states[job_id].get('color_method')
            }
        
        return jsonify({
            'batch_results': batch_results,
            'message': 'Batch metrics calculation completed'
        }), 200

def generate_metrics_plot(data, plot_type='resolution'):
    """
    Generate a plot comparing different metrics.
    
    Args:
        data: Dictionary of metrics data
        plot_type: Type of plot ('resolution' or 'filter')
        
    Returns:
        str: Base64-encoded PNG image
    """
    plt.figure(figsize=(10, 6))
    
    # Extract metric names
    if data and isinstance(next(iter(data.values())), dict):
        metric_names = list(next(iter(data.values())).keys())
    else:
        metric_names = []
    
    if not metric_names:
        return None
    
    # Create subplots for each metric
    fig, axes = plt.subplots(1, len(metric_names), figsize=(5 * len(metric_names), 4))
    if len(metric_names) == 1:
        axes = [axes]
    
    # Plot data
    labels = list(data.keys())
    
    for i, metric in enumerate(metric_names):
        values = [data[label].get(metric, 0) for label in labels]
        
        if plot_type == 'resolution':
            # Convert block sizes to integers for x-axis
            x_values = [int(label) for label in labels]
            axes[i].plot(x_values, values, marker='o', linestyle='-')
            axes[i].set_xlabel('Block Size')
        else:
            # For filters, use bar chart
            axes[i].bar(labels, values)
            plt.setp(axes[i].get_xticklabels(), rotation=45, ha='right')
            axes[i].set_xlabel('Filter')
        
        axes[i].set_ylabel(metric.upper())
        axes[i].set_title(f'{metric.upper()} Comparison')
        axes[i].grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    # Convert plot to base64 image
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return plot_data