"""
Original mosaic generation logic that produced high-quality results.
"""
import numpy as np

def create_image_matrix(element_img, matrix_size):
    """
    Generate a simple mosaic image using the element_img as a building block.
    
    Args:
        element_img: 2D grayscale image or RGB image (numpy array)
        matrix_size: tuple (H, W) specifying height and width of the output in terms of element blocks
    
    Returns:
        mosaic: numpy array representing the mosaic image
    """
    # Handle RGB vs grayscale images
    if len(element_img.shape) == 3:
        N, M, C = element_img.shape
        H, W = matrix_size
        
        # Create a row of element images
        row_tmp = np.zeros((N, M*W, C), dtype=element_img.dtype)
        for j in range(W):
            row_tmp[:, j*M:(j+1)*M, :] = element_img
        
        # Repeat the row to create the full mosaic
        mosaic = np.zeros((N*H, M*W, C), dtype=element_img.dtype)
        for i in range(H):
            mosaic[i*N:(i+1)*N, :, :] = row_tmp
    else:
        N, M = element_img.shape
        H, W = matrix_size
        
        # Create a row of element images
        row_tmp = np.zeros((N, M*W), dtype=element_img.dtype)
        for j in range(W):
            row_tmp[:, j*M:(j+1)*M] = element_img
        
        # Repeat the row to create the full mosaic
        mosaic = np.zeros((N*H, M*W), dtype=element_img.dtype)
        for i in range(H):
            mosaic[i*N:(i+1)*N, :] = row_tmp
        
    return mosaic

def adjust_element_mean(element_img, target_mean_value):
    """
    Adjust the mean of the element_img to match the target_mean_value
    while keeping pixel values in the valid range.
    
    Args:
        element_img: 2D grayscale image or RGB image channel (numpy array)
        target_mean_value: desired mean value
    
    Returns:
        adjusted element_img
    """
    # Convert to float for calculations
    element = element_img.astype(float)
    current = np.mean(element)
    
    # Calculate the difference and adjust all pixels accordingly
    diff = target_mean_value - current
    element = element + diff
    
    # Ensure values are within valid range (0-255)
    element = np.clip(element, 0, 255)
    
    return element

def create_mosaic(element_img, big_img):
    """
    Generate a mosaic image that looks like big_img but is made of element_img blocks
    
    Args:
        element_img: 2D grayscale image or RGB image (numpy array) - the building block
        big_img: 2D grayscale image or RGB image (numpy array) - the target image
    
    Returns:
        tuple: (mosaic, simple_mosaic)
            - mosaic: the final mosaic with adjusted element images
            - simple_mosaic: mosaic without dynamic adjustment
    """
    # Handle RGB vs grayscale
    if len(element_img.shape) == 3 and len(big_img.shape) == 3:
        # RGB image
        N, M, C = element_img.shape
        H, W, _ = big_img.shape
        
        # Generate a simple mosaic
        simple_mosaic = create_image_matrix(element_img, (H, W))
        mosaic = simple_mosaic.copy()
        
        # Adjust each element block to match the target image's colors
        for i in range(H):
            for j in range(W):
                # For each RGB channel
                for c in range(C):
                    # Adjust the mean of the element_img to match the target pixel
                    element = adjust_element_mean(element_img[:,:,c], big_img[i, j, c])
                    mosaic[i*N:(i+1)*N, j*M:(j+1)*M, c] = element
    else:
        # Grayscale image
        N, M = element_img.shape
        H, W = big_img.shape
        
        # Generate a simple mosaic
        simple_mosaic = create_image_matrix(element_img, (H, W))
        mosaic = simple_mosaic.copy()
        
        # Adjust each element block to match the target image's intensity
        for i in range(H):
            for j in range(W):
                # Adjust the mean of the element_img to match the target pixel
                element = adjust_element_mean(element_img, big_img[i, j])
                mosaic[i*N:(i+1)*N, j*M:(j+1)*M] = element
    
    return mosaic, simple_mosaic

def normalize_image(img):
    """
    Normalize image values to [0, 1] range
    """
    # Handle multi-channel images
    if len(img.shape) > 2:
        normalized = np.zeros_like(img, dtype=float)
        for c in range(img.shape[2]):
            channel = img[:,:,c]
            channel = channel - np.min(channel)
            if np.max(channel) > 0:
                channel = channel / np.max(channel)
            normalized[:,:,c] = channel
        return normalized
    else:
        # Single channel
        img = img - np.min(img)
        if np.max(img) > 0:
            img = img / np.max(img)
        return img