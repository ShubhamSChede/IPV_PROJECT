"""
Post-processing filter effects for mosaic images.
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps

def apply_filter(img, filter_name):
    """
    Apply a filter effect to an image.
    
    Args:
        img: PIL Image object
        filter_name: name of the filter to apply
        
    Returns:
        PIL Image: filtered image
    """
    if filter_name == 'none':
        return img
    
    # Convert numpy array to PIL Image if needed
    if isinstance(img, np.ndarray):
        if len(img.shape) == 2:
            pil_img = Image.fromarray(img, 'L')
        else:
            pil_img = Image.fromarray(img, 'RGB')
    else:
        pil_img = img
    
    # Apply the appropriate filter
    if filter_name == 'sepia':
        return apply_sepia(pil_img)
    elif filter_name == 'grayscale':
        return pil_img.convert('L').convert('RGB')
    elif filter_name == 'vintage':
        return apply_vintage(pil_img)
    elif filter_name == 'pop_art':
        return apply_pop_art(pil_img)
    elif filter_name == 'posterize':
        return ImageOps.posterize(pil_img, 3)
    elif filter_name == 'negative':
        return ImageOps.invert(pil_img)
    elif filter_name == 'blur':
        return pil_img.filter(ImageFilter.GaussianBlur(2))
    elif filter_name == 'sharpen':
        return pil_img.filter(ImageFilter.SHARPEN)
    elif filter_name == 'edge_enhance':
        return pil_img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    else:
        raise ValueError(f"Unknown filter: {filter_name}")

def apply_sepia(img):
    """
    Apply a sepia tone filter.
    
    Args:
        img: PIL Image object
        
    Returns:
        PIL Image: sepia-toned image
    """
    # Convert to RGB if not already
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Create sepia matrix (needs to be 12 values for color matrix transform)
    sepia_matrix = (
        0.393, 0.769, 0.189, 0,
        0.349, 0.686, 0.168, 0,
        0.272, 0.534, 0.131, 0
    )
    
    # Apply color matrix
    return img.convert('RGB', sepia_matrix)

def apply_vintage(img):
    """
    Apply a vintage effect filter.
    
    Args:
        img: PIL Image object
        
    Returns:
        PIL Image: vintage-effect image
    """
    # Convert to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Adjust colors
    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(0.85)
    
    color = ImageEnhance.Color(img)
    img = color.enhance(0.7)
    
    brightness = ImageEnhance.Brightness(img)
    img = brightness.enhance(1.1)
    
    # Add slight vignette
    width, height = img.size
    mask = Image.new('L', (width, height), 255)
    
    # Draw a radial gradient for the vignette
    from PIL import ImageDraw
    draw = ImageDraw.Draw(mask)
    for i in range(20):
        bound = (i, i, width - i, height - i)
        draw.ellipse(bound, fill=255 - i * 6)
    
    # Apply vignette
    img = Image.composite(img, Image.new('RGB', (width, height), (30, 20, 10)), mask)
    
    return img

def apply_pop_art(img):
    """
    Apply a pop art style filter.
    
    Args:
        img: PIL Image object
        
    Returns:
        PIL Image: pop art styled image
    """
    # Convert to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Increase contrast and saturation
    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(1.5)
    
    color = ImageEnhance.Color(img)
    img = color.enhance(1.8)
    
    # Posterize to reduce colors
    img = ImageOps.posterize(img, 3)
    
    return img

def apply_multiple_filters(img, filters):
    """
    Apply multiple filters in sequence.
    
    Args:
        img: PIL Image object
        filters: list of filter names to apply
        
    Returns:
        PIL Image: image with all filters applied
    """
    result = img
    for filter_name in filters:
        result = apply_filter(result, filter_name)
    return result