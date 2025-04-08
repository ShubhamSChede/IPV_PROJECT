# core/__init__.py
"""
Core functionality package.
"""
from core.color_analysis import (
    build_element_library,
    find_best_matching_block,
    adjust_block_colors,
    create_color_palette
)
from core.mosaic import (
    create_image_matrix,
    create_mosaic,
    create_multiresolution_mosaic
)
from core.filters import (
    apply_filter,
    apply_multiple_filters
)
from core.metrics import (
    calculate_mse,
    calculate_ssim,
    calculate_psnr,
    evaluate_mosaic_quality
)

