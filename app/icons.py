"""
This module handles the loading and management of icons for the application.
It provides a centralized way to access icons, supporting both SVG and PNG formats,
and allows for dynamic color changes to match the application's theme.
"""

from PIL import Image, ImageTk
import tksvg
import os
from utils import debug_console

# Cache for loaded icons to prevent redundant disk I/O and processing.
_icon_cache = {}

def get_icon(icon_name: str, size: int = 16, color: str = None):
    """
    Loads an icon from the resources directory. It can handle both SVG and PNG files.
    For SVG files, it can dynamically change the icon's color.
    
    Args:
        icon_name (str): The name of the icon file (e.g., "save.svg").
        size (int): The desired size (width and height) of the icon.
        color (str, optional): The color to apply to the SVG icon (e.g., "#FFFFFF"). 
                               Defaults to None.

    Returns:
        An image object (tksvg.SvgImage or ImageTk.PhotoImage) or None if not found.
    """
    # Create a unique cache key based on name, size, and color.
    cache_key = f"{icon_name}_{size}_{color}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    try:
        path = os.path.join("resources", "icons", icon_name)
        if not os.path.exists(path):
            debug_console.log(f"Icon not found at path: {path}", level='WARNING')
            return None

        image = None
        if icon_name.lower().endswith(".svg"):
            # Read the SVG content to modify its color.
            with open(path, 'r') as f:
                svg_data = f.read()
            
            # If a color is provided, replace the stroke color.
            # This assumes the SVG has a placeholder like 'currentColor'.
            if color:
                svg_data = svg_data.replace('stroke="currentColor"', f'stroke="{color}"')

            image = tksvg.SvgImage(data=svg_data, scaletowidth=size)
        else:
            # For PNG and other formats, use Pillow. Colorization is not supported for these.
            pil_image = Image.open(path).resize((size, size), Image.LANCZOS)
            image = ImageTk.PhotoImage(pil_image)
        
        if image:
            _icon_cache[cache_key] = image
        return image

    except Exception as e:
        debug_console.log(f"Error loading icon '{icon_name}': {e}", level='ERROR')
        return None
