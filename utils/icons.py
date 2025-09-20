"""
This module handles SVG icons for the Noctern application.
It provides utilities to load and display SVG icons in the UI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
import os
from utils import logs_console


def get_icon_path(icon_name: str) -> Optional[str]:
    """
    Get the full path to an icon file.
    
    Args:
        icon_name: Name of the icon file (with or without extension)
        
    Returns:
        Full path to the icon file or None if not found
    """
    # check if the icon name already has an extension
    if not icon_name.endswith(('.svg', '.png')):
        # try svg first, then png
        for ext in ['.svg', '.png']:
            # check in search subdir first
            full_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'resources', 
                'icons',
                'search',
                icon_name + ext
            )
            if os.path.exists(full_path):
                return full_path
                
            # check in main icons dir
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
            
    logs_console.log(f"Icon not found: {icon_name}", level='WARNING')
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
                # resize to a standard size
                img = img.resize((16, 16), Image.Resampling.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(img)
                self.config(image=self.icon_photo)
                return
            except Exception as e:
                logs_console.log(f"Error loading icon {self.icon_name}: {e}", level='ERROR')

        elif icon_path and icon_path.endswith('.svg'):
            try:
                import cairosvg
                from PIL import Image, ImageTk
                import io

                # convert svg to png in memory
                png_data = cairosvg.svg2png(url=icon_path, output_width=16, output_height=16)
                img = Image.open(io.BytesIO(png_data))
                self.icon_photo = ImageTk.PhotoImage(img)
                self.config(image=self.icon_photo)
                return
            except (ImportError, Exception) as exc:
                logs_console.log(f"Error loading SVG icon {self.icon_name}: {exc}", level='WARNING')

        self._set_fallback_text()

    def _set_fallback_text(self):
        """Fallback glyphs when icon assets are unavailable."""
        icon_map = {
            'search': '🔍',
            'chevron-up': '▲',
            'chevron-down': '▼',
            'up': '▲',
            'down': '▼',
            'next': '▶',
            'previous': '◀',
            'close': '✕',
            'replace': '⟲',
            'expand': '▾'
        }
        text = icon_map.get(self.icon_name, self.icon_name[:1].upper())
        self.config(text=text)
