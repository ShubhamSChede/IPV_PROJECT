"""
Main application entry point for mosaic generator.
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys

# Get absolute path of the directory containing app.py
project_root = os.path.dirname(os.path.abspath(__file__))

# Add project root to the Python path
sys.path.insert(0, project_root)

# Now import your modules
from flask import Flask, request, jsonify, send_file

# Add project root to path so modules can be imported properly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import configuration
from config import UPLOAD_FOLDER, TEMP_FOLDER, OUTPUT_FOLDER, MAX_CONTENT_LENGTH

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set up configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Dictionary to store job states
job_states = {}

# Register API routes
from api.upload import register_upload_routes
from api.preprocess import register_preprocess_routes
from api.generation import register_generation_routes
from api.filters import register_filter_routes
from api.metrics import register_metrics_routes

# Register routes
register_upload_routes(app, job_states)
register_preprocess_routes(app, job_states)
register_generation_routes(app, job_states)
register_filter_routes(app, job_states)
register_metrics_routes(app, job_states)

# Image serving endpoints
@app.route('/api/images/uploads/<filename>', methods=['GET'])
def get_upload_image(filename):
    """Serve an image from the uploads folder"""
    try:
        return send_file(os.path.join(UPLOAD_FOLDER, filename))
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/api/temp/<filename>', methods=['GET'])
def get_temp_image(filename):
    """Serve an image from the temp folder"""
    try:
        return send_file(os.path.join(TEMP_FOLDER, filename))
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/api/images/outputs/<filename>', methods=['GET'])
def get_output_image(filename):
    """Serve an image from the output folder"""
    try:
        return send_file(os.path.join(OUTPUT_FOLDER, filename))
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404

# Job status endpoint
@app.route('/api/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the current status and outputs of a job"""
    if job_id not in job_states:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job_states[job_id]), 200

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

# API documentation endpoint
@app.route('/api/docs', methods=['GET'])
def get_api_docs():
    """Return API documentation"""
    docs = {
        "api_version": "2.0.0",
        "title": "Enhanced Mosaic Generator API",
        "description": "Create color mosaics with adjustable resolution, filters, and quality metrics",
        "new_features": [
            "Color mosaic support (RGB)",
            "Adjustable block size for controlling resolution",
            "Post-processing filters (sepia, vintage, etc.)",
            "Quality metrics (SSIM, MSE, PSNR)"
        ],
        "endpoints": {
            "upload": {
                "/api/upload": "Upload element and target images (POST)",
                "/api/upload_element": "Upload only element image (POST)",
                "/api/upload_target/{job_id}": "Upload target image for existing job (POST)"
            },
            "preprocess": {
                "/api/preprocess/{job_id}": "Preprocess images (GET)",
                "/api/set_block_size/{job_id}": "Set/update block size (POST)",
                "/api/multiresolution_preview/{job_id}": "Generate previews at different block sizes (GET)"
            },
            "generation": {
                "/api/generate_mosaic/{job_id}": "Generate mosaic (GET)",
                "/api/multiresolution/{job_id}": "Generate mosaics at multiple resolutions (GET)",
                "/api/generate_mosaic": "Legacy one-step generation (POST)"
            },
            "filters": {
                "/api/apply_filter/{job_id}": "Apply filter to mosaic (POST)",
                "/api/available_filters": "Get list of available filters (GET)",
                "/api/filter_preview/{job_id}": "Generate previews with different filters (GET)",
                "/api/compare_filters/{job_id}": "Generate side-by-side filter comparison (POST)"
            },
            "metrics": {
                "/api/metrics/{job_id}": "Get quality metrics for a mosaic (GET)",
                "/api/metrics/compare/{job_id}": "Compare metrics for different block sizes or filters (GET)",
                "/api/metrics/batch": "Calculate metrics for multiple jobs (POST)"
            },
            "utility": {
                "/api/job/{job_id}": "Get job status and outputs (GET)",
                "/api/health": "Health check (GET)",
                "/api/docs": "API documentation (GET)"
            }
        }
    }
    return jsonify(docs), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')