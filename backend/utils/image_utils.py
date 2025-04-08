"""
Utility functions for image processing.
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import cv2
from config import MAX_ELEMENT_SIZE, MAX_TARGET_SIZE

def resize_image_if_needed(img, max_size, maintain_aspect_ratio=True):
    """Return to the original, reliable implementation"""
    width, height = img.size
    
    # Check if resizing is needed
    if width <= max_size and height <= max_size:
        return img
    
    if maintain_aspect_ratio:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
    else:
        new_width = new_height = max_size
        
    # Use LANCZOS for high-quality resizing
    return img.resize((new_width, new_height), Image.LANCZOS)

def normalize_image(img):
    """
    Normalize image values to [0, 1] range.
    
    Args:
        img: numpy array image
        
    Returns:
        normalized numpy array
    """
    img = img - np.min(img)
    if np.max(img) > 0:
        img = img / np.max(img)
    return img

# Improve the check_mosaic_size function to better handle different inputs
def check_mosaic_size(element_shape, target_shape, block_size=None):
    """
    Check if the resulting mosaic would be too large and adjust target size if needed.
    
    Args:
        element_shape: tuple (height, width) of element image
        target_shape: tuple (height, width) of target image
        block_size: optional block size for block-based mosaic
        
    Returns:
        tuple: adjusted target shape to keep mosaic size reasonable
    """
    element_h, element_w = element_shape
    target_h, target_w = target_shape
    
    # If using block size, adjust calculations
    if block_size is not None:
        # For the specified block size, calculate how many blocks will fit
        target_h_blocks = target_h // block_size
        target_w_blocks = target_w // block_size
        
        # Calculate resulting mosaic size
        mosaic_h = target_h_blocks * block_size
        mosaic_w = target_w_blocks * block_size
    else:
        # Direct element-by-element mosaic
        mosaic_h = element_h * target_h
        mosaic_w = element_w * target_w
        
    mosaic_pixels = mosaic_h * mosaic_w
    
    from config import MAX_MOSAIC_PIXELS
    
    # If mosaic would be too large, scale down target_shape
    if mosaic_pixels > MAX_MOSAIC_PIXELS:
        scale_factor = (MAX_MOSAIC_PIXELS / mosaic_pixels) ** 0.5
        
        if block_size is not None:
            # Scale the number of blocks
            new_target_h_blocks = max(1, int(target_h_blocks * scale_factor))
            new_target_w_blocks = max(1, int(target_w_blocks * scale_factor))
            new_target_h = new_target_h_blocks * block_size
            new_target_w = new_target_w_blocks * block_size
        else:
            # Scale target dimensions directly
            new_target_h = max(1, int(target_h * scale_factor))
            new_target_w = max(1, int(target_w * scale_factor))
            
        return (new_target_h, new_target_w)
    
    return target_shape

def get_average_color(img_block):
    """
    Calculate the average RGB color of an image block.
    
    Args:
        img_block: numpy array of RGB image block
        
    Returns:
        tuple: (R, G, B) average values
    """
    # Ensure the image is in RGB format
    if len(img_block.shape) == 2:  # Grayscale
        return (
            np.mean(img_block),
            np.mean(img_block),
            np.mean(img_block)
        )
    
    return (
        np.mean(img_block[:, :, 0]),
        np.mean(img_block[:, :, 1]),
        np.mean(img_block[:, :, 2])
    )

def get_color_histogram(img_block, bins=8):
    """
    Calculate the color histogram of an image block.
    
    Args:
        img_block: numpy array of RGB image block
        bins: number of bins for the histogram
        
    Returns:
        numpy array: flattened histogram
    """
    # Convert to proper format for cv2
    if len(img_block.shape) == 3 and img_block.shape[2] == 3:
        # Already RGB
        img_cv = cv2.cvtColor(img_block, cv2.COLOR_RGB2BGR)
    else:
        # Grayscale
        img_cv = img_block
    
    # Calculate histogram
    if len(img_block.shape) == 2 or img_block.shape[2] == 1:
        # Grayscale
        hist = cv2.calcHist([img_cv], [0], None, [bins], [0, 256])
    else:
        # RGB
        hist = cv2.calcHist([img_cv], [0, 1, 2], None, [bins, bins, bins], [0, 256, 0, 256, 0, 256])
    
    # Normalize and flatten
    cv2.normalize(hist, hist)
    return hist.flatten()

def color_distance(color1, color2):
    """
    Calculate Euclidean distance between two RGB colors.
    
    Args:
        color1: tuple (R, G, B)
        color2: tuple (R, G, B)
        
    Returns:
        float: distance between colors
    """
    return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)))

def histogram_comparison(hist1, hist2, method=cv2.HISTCMP_CORREL):
    """
    Compare two histograms using specified method.
    
    Args:
        hist1: first histogram
        hist2: second histogram
        method: comparison method from cv2
        
    Returns:
        float: similarity score
    """
    return cv2.compareHist(hist1, hist2, method)

def load_and_preprocess_image(image_path, target_size=None, color_mode='rgb'):
    """
    Load and preprocess an image from path.
    
    Args:
        image_path: path to the image file
        target_size: tuple (width, height) or None
        color_mode: 'rgb' or 'grayscale'
        
    Returns:
        PIL Image: preprocessed image
    """
    img = Image.open(image_path)
    
    # Convert to desired color mode
    if color_mode == 'rgb' and img.mode != 'RGB':
        img = img.convert('RGB')
    elif color_mode == 'grayscale' and img.mode != 'L':
        img = img.convert('L')
    
    # Resize if needed
    if target_size:
        img = img.resize(target_size, Image.LANCZOS)
    
    return img

def save_image(img, path):
    """
    Save image to file.
    
    Args:
        img: PIL Image or numpy array
        path: path to save the image
        
    Returns:
        str: path where the image was saved
    """
    if isinstance(img, np.ndarray):
        # Convert numpy array to PIL Image
        if img.dtype != np.uint8:
            if np.max(img) <= 1.0:
                img = (img * 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)
        
        if len(img.shape) == 2:
            # Grayscale
            pil_img = Image.fromarray(img, 'L')
        else:
            # RGB
            pil_img = Image.fromarray(img, 'RGB')
    else:
        # Already a PIL Image
        pil_img = img
    
    pil_img.save(path)
    return path