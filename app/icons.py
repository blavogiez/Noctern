"""
This module handles the loading and management of icons for the application.
It provides a centralized way to access icons, supporting both SVG and PNG formats.
"""

from PIL import Image, ImageTk
import tksvg
import os
from utils import debug_console

# This dictionary will map icon names to their PhotoImage/SvgImage objects.
# Caching them is good practice to avoid reloading from disk.
_icon_cache = {}

def get_icon(icon_name: str, size: int = 16):
    """
    Loads an icon from the resources directory. It can handle both SVG and PNG files.
    
    Args:
        icon_name (str): The name of the icon file (e.g., "save.svg").
        size (int): The desired size (width and height) of the icon.

    Returns:
        An image object (tksvg.SvgImage or ImageTk.PhotoImage) or None if not found.
    """
    cache_key = f"{icon_name}_{size}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    try:
        path = os.path.join("resources", "icons", icon_name)
        if not os.path.exists(path):
            debug_console.log(f"Icon not found at path: {path}", level='WARNING')
            return None

        image = None
        if icon_name.lower().endswith(".svg"):
            # For SVG, tksvg handles scaling.
            image = tksvg.SvgImage(file=path, scaletowidth=size)
        else:
            # For PNG and other formats, use Pillow.
            pil_image = Image.open(path).resize((size, size), Image.LANCZOS)
            image = ImageTk.PhotoImage(pil_image)
        
        if image:
            _icon_cache[cache_key] = image
        return image

    except Exception as e:
        debug_console.log(f"Error loading icon '{icon_name}': {e}", level='ERROR')
        return None
