"""
This module handles SVG icons for the AutomaTeX application.
It provides utilities to load and display SVG icons in the UI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
import os
from utils import debug_console


def get_icon_path(icon_name: str) -> Optional[str]:
    """
    Get the full path to an icon file.
    
    Args:
        icon_name: Name of the icon file (with or without extension)
        
    Returns:
        Full path to the icon file or None if not found
    """
    # Check if the icon name already has an extension
    if not icon_name.endswith(('.svg', '.png')):
        # Try SVG first, then PNG
        for ext in ['.svg', '.png']:
            # Check in search subdirectory first
            full_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'resources', 
                'icons',
                'search',
                icon_name + ext
            )
            if os.path.exists(full_path):
                return full_path
                
            # Check in main icons directory
            full_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'resources', 
                'icons', 
                icon_name + ext
            )
            if os.path.exists(full_path):
                return full_path
    else:
        # Check in search subdirectory first
        full_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'resources', 
            'icons',
            'search',
            icon_name
        )
        if os.path.exists(full_path):
            return full_path
            
        # Check in main icons directory
        full_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'resources', 
            'icons', 
            icon_name
        )
        if os.path.exists(full_path):
            return full_path
            
    debug_console.log(f"Icon not found: {icon_name}", level='WARNING')
    return None


class IconButton(ttk.Button):
    """
    A button that displays an icon instead of text.
    """
    
    def __init__(self, parent, icon_name: str, **kwargs):
        """
        Initialize the icon button.
        
        Args:
            parent: Parent widget
            icon_name: Name of the icon file (without path)
            **kwargs: Additional arguments for ttk.Button
        """
        super().__init__(parent, **kwargs)
        self.icon_name = icon_name
        self.icon_photo = None
        self._load_icon()
        
    def _load_icon(self):
        """Load the icon and set it as the button image."""
        icon_path = get_icon_path(self.icon_name)
        if icon_path and icon_path.endswith('.png'):
            try:
                from PIL import Image, ImageTk
                img = Image.open(icon_path)
                # Resize to a standard size
                img = img.resize((16, 16), Image.Resampling.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(img)
                self.config(image=self.icon_photo)
            except Exception as e:
                debug_console.log(f"Error loading icon {self.icon_name}: {e}", level='ERROR')
                # Fallback to text
                self.config(text=self.icon_name[:1].upper())
        elif icon_path and icon_path.endswith('.svg'):
            # For SVG files, we'll use text as fallback for now
            # In a full implementation, we would use a library like cairosvg
            # to convert SVG to PNG first
            icon_map = {
                'search': '🔍',
                'next': '▶',
                'previous': '◀',
                'close': '✕'
            }
            text = icon_map.get(self.icon_name, self.icon_name[:1].upper())
            self.config(text=text)
        elif icon_path:
            # For other formats, just show the first letter as fallback
            self.config(text=self.icon_name[:1].upper())