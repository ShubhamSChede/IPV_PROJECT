"""
Quality assessment metrics for mosaic images.
"""
import numpy as np
import cv2
from PIL import Image
from skimage.metrics import structural_similarity as ssim

def calculate_mse(img1, img2):
    """
    Calculate Mean Squared Error between two images.
    
    Args:
        img1: first image (numpy array)
        img2: second image (numpy array)
        
    Returns:
        float: MSE value (lower is better)
    """
    # Ensure images have same dimensions
    if img1.shape != img2.shape:
        # Resize second image to match first
        if isinstance(img2, np.ndarray):
            if len(img2.shape) == 3:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            else:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    # Calculate MSE
    mse = np.mean((img1 - img2) ** 2)
    return mse

def calculate_ssim(img1, img2, multichannel=True):
    """
    Calculate Structural Similarity Index between two images.
    
    Args:
        img1: first image (numpy array)
        img2: second image (numpy array)
        multichannel: whether to calculate SSIM for each channel separately
        
    Returns:
        float: SSIM value (higher is better, max=1)
    """
    # Ensure images have same dimensions
    if img1.shape != img2.shape:
        # Resize second image to match first
        if isinstance(img2, np.ndarray):
            if len(img2.shape) > 2:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            else:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    # Get the minimum dimension of the image
    min_dim = min(img1.shape[0], img1.shape[1])
    
    # Determine appropriate window size (must be odd and <= min_dim)
    if min_dim < 7:
        # Use the largest odd number that fits
        win_size = min_dim if min_dim % 2 == 1 else min_dim - 1
    else:
        win_size = 7  # Default window size
    
    # Ensure we have a valid window size (must be at least 3)
    win_size = max(3, win_size)
    
    # Calculate SSIM
    if multichannel and len(img1.shape) > 2:
        # For color images
        return ssim(img1, img2, win_size=win_size, channel_axis=-1)
    else:
        # For grayscale images
        return ssim(img1, img2, win_size=win_size, channel_axis=None)

def calculate_psnr(img1, img2):
    """
    Calculate Peak Signal-to-Noise Ratio between two images.
    
    Args:
        img1: first image (numpy array)
        img2: second image (numpy array)
        
    Returns:
        float: PSNR value in dB (higher is better)
    """
    # Ensure images have same dimensions
    if img1.shape != img2.shape:
        # Resize second image to match first
        if isinstance(img2, np.ndarray):
            if len(img2.shape) == 3:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            else:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    # Calculate MSE
    mse = calculate_mse(img1, img2)
    if mse == 0:
        return float('inf')  # Perfect match
    
    # Calculate PSNR
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return psnr

def evaluate_mosaic_quality(original_img, mosaic_img):
    """
    Evaluate the quality of a mosaic image compared to the original.
    
    Args:
        original_img: original target image (numpy array)
        mosaic_img: generated mosaic image (numpy array)
        
    Returns:
        dict: Dictionary of quality metrics
    """
    # Ensure images have same dimensions
    if original_img.shape != mosaic_img.shape:
        # Resize mosaic to match original
        if len(original_img.shape) == 3:
            mosaic_img = cv2.resize(mosaic_img, (original_img.shape[1], original_img.shape[0]))
        else:
            mosaic_img = cv2.resize(mosaic_img, (original_img.shape[1], original_img.shape[0]))
    
    # Convert to 8-bit if needed
    if original_img.dtype != np.uint8:
        original_img = (original_img * 255).astype(np.uint8) if original_img.max() <= 1.0 else original_img.astype(np.uint8)
    if mosaic_img.dtype != np.uint8:
        mosaic_img = (mosaic_img * 255).astype(np.uint8) if mosaic_img.max() <= 1.0 else mosaic_img.astype(np.uint8)
    
    # Calculate metrics
    mse = calculate_mse(original_img, mosaic_img)
    ssim_value = calculate_ssim(original_img, mosaic_img)
    psnr = calculate_psnr(original_img, mosaic_img)
    
    return {
        'mse': float(mse),
        'ssim': float(ssim_value),
        'psnr': float(psnr)
    }