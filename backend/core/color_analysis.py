"""
Functions for color analysis and matching.
"""
import numpy as np
import cv2
from PIL import Image
from utils.image_utils import get_average_color, get_color_histogram, color_distance, histogram_comparison

def build_element_library(element_img, block_size, method='average_rgb'):
    """
    Build a library of element blocks with their color information.
    
    Args:
        element_img: numpy array of the element image
        block_size: size of each block
        method: 'average_rgb' or 'histogram'
        
    Returns:
        dict: Library of element blocks with color information
    """
    # Get dimensions
    height, width = element_img.shape[:2]
    
    # Calculate how many blocks we can get
    n_blocks_h = height // block_size
    n_blocks_w = width // block_size
    
    # Initialize library
    library = []
    
    # Extract blocks and calculate color features
    for i in range(n_blocks_h):
        for j in range(n_blocks_w):
            # Extract block
            h_start = i * block_size
            h_end = (i + 1) * block_size
            w_start = j * block_size
            w_end = (j + 1) * block_size
            
            block = element_img[h_start:h_end, w_start:w_end]
            
            # Calculate color feature
            if method == 'average_rgb':
                color_feature = get_average_color(block)
            elif method == 'histogram':
                color_feature = get_color_histogram(block)
            else:
                raise ValueError(f"Unknown color analysis method: {method}")
            
            # Add to library
            library.append({
                'block': block,
                'color_feature': color_feature,
                'position': (i, j)
            })
    
    return library

def find_best_matching_block(target_color, element_library, method='average_rgb'):
    """
    Find the best matching block from the element library.
    
    Args:
        target_color: target color feature
        element_library: library of element blocks
        method: 'average_rgb' or 'histogram'
        
    Returns:
        dict: Best matching block entry from the library
    """
    best_match = None
    best_score = float('-inf') if method == 'histogram' else float('inf')
    
    for entry in element_library:
        if method == 'average_rgb':
            # For average RGB, lower distance is better
            score = color_distance(target_color, entry['color_feature'])
            if score < best_score:
                best_score = score
                best_match = entry
        elif method == 'histogram':
            # For histogram, higher correlation is better
            score = histogram_comparison(target_color, entry['color_feature'])
            if score > best_score:
                best_score = score
                best_match = entry
    
    return best_match

def adjust_block_colors(block, target_color, alpha=0.7):
    """
    Adjust the colors of a block to better match the target color.
    
    Args:
        block: numpy array of the block
        target_color: tuple (R, G, B) target color
        alpha: blending factor (0 = no change, 1 = full target color)
        
    Returns:
        numpy array: Color-adjusted block
    """
    # Convert to float for calculations
    block_float = block.astype(float)
    
    # Calculate current average color
    current_color = get_average_color(block)
    
    # Initialize adjusted block
    adjusted_block = np.zeros_like(block_float)
    
    # Adjust colors
    if len(block.shape) == 2:  # Grayscale
        # Calculate difference
        diff = target_color[0] - current_color[0]
        
        # Adjust
        adjusted_block = block_float + (diff * alpha)
    else:  # RGB
        for c in range(3):
            # Calculate difference
            diff = target_color[c] - current_color[c]
            
            # Adjust
            adjusted_block[:, :, c] = block_float[:, :, c] + (diff * alpha)
    
    # Ensure values are within range
    adjusted_block = np.clip(adjusted_block, 0, 255)
    
    return adjusted_block.astype(np.uint8)

def create_color_palette(image, n_colors=8):
    """
    Extract the dominant colors from an image to create a color palette.
    
    Args:
        image: numpy array of the image
        n_colors: number of colors to extract
        
    Returns:
        list: List of (R, G, B) tuples representing the dominant colors
    """
    # Reshape the image for k-means
    pixels = image.reshape(-1, 3) if len(image.shape) == 3 else image.reshape(-1, 1)
    pixels = pixels.astype(np.float32)
    
    # Define criteria and apply k-means
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, centers = cv2.kmeans(pixels, n_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Convert centers to integers
    centers = centers.astype(np.uint8)
    
    # Count occurrences of each label
    counts = np.bincount(labels.flatten())
    
    # Sort colors by frequency (most frequent first)
    sorted_indices = np.argsort(counts)[::-1]
    sorted_centers = centers[sorted_indices]
    
    # Convert to RGB tuples
    palette = []
    for center in sorted_centers:
        if len(center) == 1:  # Grayscale
            palette.append((center[0], center[0], center[0]))
        else:  # RGB
            palette.append(tuple(center))
    
    return palette