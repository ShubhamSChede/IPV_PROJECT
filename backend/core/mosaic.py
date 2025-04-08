"""
Core mosaic generation logic.
"""
import numpy as np
from PIL import Image
from utils.image_utils import get_average_color, normalize_image
from core.color_analysis import build_element_library, find_best_matching_block, adjust_block_colors

def create_image_matrix(element_img, matrix_size, block_size):
    """
    Generate a simple mosaic image using the element_img as a building block.
    
    Args:
        element_img: RGB or grayscale image (numpy array)
        matrix_size: tuple (H, W) specifying height and width of the output in terms of blocks
        block_size: size of each block in pixels
        
    Returns:
        mosaic: numpy array representing the mosaic image
    """
    # Create a single element block of the desired size
    if len(element_img.shape) == 3:  # RGB
        h, w, c = element_img.shape
        element_block = element_img[:block_size, :block_size, :] if (h >= block_size and w >= block_size) else np.resize(element_img, (block_size, block_size, c))
        # Initialize mosaic array
        H, W = matrix_size
        mosaic = np.zeros((H * block_size, W * block_size, c), dtype=element_img.dtype)
    else:  # Grayscale
        h, w = element_img.shape
        element_block = element_img[:block_size, :block_size] if (h >= block_size and w >= block_size) else np.resize(element_img, (block_size, block_size))
        # Initialize mosaic array
        H, W = matrix_size
        mosaic = np.zeros((H * block_size, W * block_size), dtype=element_img.dtype)
    
    # Create the mosaic by tiling the element block
    for i in range(H):
        for j in range(W):
            h_start = i * block_size
            h_end = (i + 1) * block_size
            w_start = j * block_size
            w_end = (j + 1) * block_size
            
            mosaic[h_start:h_end, w_start:w_end] = element_block
    
    return mosaic

def create_mosaic(element_img, target_img, block_size, color_method='average_rgb', adjust_colors=True, alpha=0.7, job_id=None, job_states=None):
    """Return to the original, reliable implementation"""
    # Get dimensions
    if len(target_img.shape) == 3:  # RGB
        target_h, target_w, _ = target_img.shape
    else:  # Grayscale
        target_h, target_w = target_img.shape
    
    # Calculate number of blocks
    n_blocks_h = target_h // block_size
    n_blocks_w = target_w // block_size
    
    # Build element library
    element_library = build_element_library(element_img, block_size, method=color_method)
    
    # Create a simple mosaic for comparison
    simple_mosaic = create_image_matrix(element_img, (n_blocks_h, n_blocks_w), block_size)
    
    # Initialize the final mosaic
    if len(target_img.shape) == 3:  # RGB
        mosaic = np.zeros((n_blocks_h * block_size, n_blocks_w * block_size, 3), dtype=np.uint8)
    else:  # Grayscale
        mosaic = np.zeros((n_blocks_h * block_size, n_blocks_w * block_size), dtype=np.uint8)
    
    # Build mosaic by finding best matching blocks
    for i in range(n_blocks_h):
        for j in range(n_blocks_w):
            # Update progress if tracking
            if job_id is not None and job_states is not None and (i * n_blocks_w + j) % max(1, (n_blocks_h * n_blocks_w // 20)) == 0:
                progress = 30 + ((i * n_blocks_w + j) / (n_blocks_h * n_blocks_w)) * 60
                job_states[job_id]['progress'] = progress
            
            # Extract target block
            h_start = i * block_size
            h_end = min((i + 1) * block_size, target_h)
            w_start = j * block_size
            w_end = min((j + 1) * block_size, target_w)
            
            target_block = target_img[h_start:h_end, w_start:w_end]
            
            # Calculate color feature
            if color_method == 'average_rgb':
                from utils.image_utils import get_average_color
                color_feature = get_average_color(target_block)
            else:
                from utils.image_utils import get_color_histogram
                color_feature = get_color_histogram(target_block)
            
            # Find best matching block
            best_match = find_best_matching_block(color_feature, element_library, method=color_method)
            
            # Get matched block
            matched_block = best_match['block'].copy()
            
            # Adjust colors if requested
            if adjust_colors:
                from core.color_analysis import adjust_block_colors
                matched_block = adjust_block_colors(matched_block, color_feature, alpha)
            
            # Place in mosaic
            mosaic[h_start:h_end, w_start:w_end] = matched_block[:h_end-h_start, :w_end-w_start]
    
    # Return both mosaics
    return mosaic, simple_mosaic

def create_multiresolution_mosaic(element_img, target_img, block_sizes, color_method='average_rgb', adjust_colors=True, job_id=None, job_states=None):
    """
    Generate multiple mosaics with different block sizes.
    
    Args:
        element_img: RGB or grayscale image (numpy array) - the building block
        target_img: RGB or grayscale image (numpy array) - the target image
        block_sizes: list of block sizes to use
        color_method: method for color matching ('average_rgb' or 'histogram')
        adjust_colors: whether to adjust block colors to better match target
        job_id: unique identifier for the job, for tracking progress
        job_states: dictionary to store job states, for tracking progress
        
    Returns:
        dict: Dictionary mapping block sizes to (mosaic, simple_mosaic) tuples
    """
    results = {}
    
    for i, block_size in enumerate(block_sizes):
        # Update job state if tracking
        if job_id is not None and job_states is not None:
            job_states[job_id]['status'] = f'creating_mosaic_size_{block_size}'
            job_states[job_id]['progress'] = (i / len(block_sizes)) * 100
            
        # Generate mosaic for this block size
        mosaic, simple_mosaic = create_mosaic(
            element_img, 
            target_img, 
            block_size, 
            color_method=color_method, 
            adjust_colors=adjust_colors
        )
        
        results[block_size] = (mosaic, simple_mosaic)
    
    # Update job state if tracking
    if job_id is not None and job_states is not None:
        job_states[job_id]['status'] = 'completed'
        job_states[job_id]['progress'] = 100
        
    return results