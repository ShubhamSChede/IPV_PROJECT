"""
Configuration settings for the mosaic generator application.
"""
import os

# Directory settings
UPLOAD_FOLDER = 'static/uploads'
TEMP_FOLDER = 'static/temp'
OUTPUT_FOLDER = 'static/outputs'

# Ensure directories exist
for folder in [UPLOAD_FOLDER, TEMP_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# File settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Size limitations to prevent memory issues
MAX_ELEMENT_SIZE = 32  # Maximum size of element image (width/height)
MAX_TARGET_SIZE = 128  # Maximum size of target image (width/height)
MAX_MOSAIC_PIXELS = 16777216  # ~16 million pixels (4096x4096)

# Mosaic default settings
DEFAULT_BLOCK_SIZE = 32  # Default block size for mosaic
MIN_BLOCK_SIZE = 8      # Minimum allowed block size
MAX_BLOCK_SIZE = 64     # Maximum allowed block size

# Available filter effects
AVAILABLE_FILTERS = {
    'none': 'No Filter',
    'sepia': 'Sepia Tone',
    'grayscale': 'Black & White',
    'vintage': 'Vintage',
    'pop_art': 'Pop Art',
    'posterize': 'Posterize',
    'negative': 'Negative',
    'blur': 'Blur',
    'sharpen': 'Sharpen',
    'edge_enhance': 'Edge Enhancement'
}