"""
PDF Image Processing for Dark Mode Support.
Handle color inversion and image optimization for dark themes.
"""

from PIL import Image, ImageOps
import numpy as np
from utils import logs_console


def invert_pdf_colors(image):
    """
    Invert PDF colors for dark mode while preserving readability.
    
    Args:
        image (PIL.Image): Original PDF page image
        
    Returns:
        PIL.Image: Color-inverted image optimized for dark themes
    """
    if not image:
        return None
        
    try:
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Apply simple color inversion for PDF content
        # This works well for text-heavy documents with white backgrounds
        inverted_image = ImageOps.invert(image)
        
        return inverted_image
        
    except Exception as e:
        logs_console.log(f"Error inverting PDF colors: {e}", level='ERROR')
        return image  # Return original image on error


def is_dark_mode_inversion_needed():
    """
    Check if dark mode color inversion should be applied to PDFs.
    
    Returns:
        bool: True if current theme requires PDF color inversion
    """
    try:
        from app import state
        theme_settings = state.get_theme_settings()
        
        if not theme_settings:
            return False
            
        # Check if background is dark (indicating dark theme)
        editor_bg = theme_settings.get('editor_bg', '#FFFFFF')
        
        # Simple luminance check for dark background
        if editor_bg.startswith('#'):
            # Convert hex to RGB
            r, g, b = int(editor_bg[1:3], 16), int(editor_bg[3:5], 16), int(editor_bg[5:7], 16)
            # Calculate luminance (0.0 = black, 1.0 = white)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # If luminance is low (dark background), we need inversion
            return luminance < 0.5
            
    except Exception as e:
        logs_console.log(f"Error checking dark mode state: {e}", level='ERROR')
        
    return False


def apply_dark_mode_processing(image):
    """
    Apply dark mode processing to a PDF image if needed.
    
    Args:
        image (PIL.Image): Original PDF page image
        
    Returns:
        PIL.Image: Processed image (inverted if in dark mode, original otherwise)
    """
    if not image:
        return None
        
    if is_dark_mode_inversion_needed():
        return invert_pdf_colors(image)
    else:
        return image