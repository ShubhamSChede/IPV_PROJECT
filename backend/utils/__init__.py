# utils/__init__.py
"""
Utility functions package.
"""
from utils.file_utils import (
    allowed_file, 
    generate_unique_filename, 
    get_file_path, 
    get_file_url, 
    save_uploaded_file
)
from utils.image_utils import (
    resize_image_if_needed,
    normalize_image,
    check_mosaic_size,
    get_average_color,
    get_color_histogram,
    color_distance,
    histogram_comparison,
    load_and_preprocess_image,
    save_image
)
from utils.validation import (
    validate_file_upload,
    allowed_file,
    validate_block_size,
    validate_filter,
    validate_job_id
)

