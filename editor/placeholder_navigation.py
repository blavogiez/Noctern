"""
Simplified module for $element$ placeholder navigation.
Simple Tab navigation to the next placeholder, regardless of location.
"""

import tkinter as tk
import re
from utils import debug_console


class PlaceholderManager:
    """Ultra-simple manager for navigating between $element$ placeholders."""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.current_search_pos = "1.0"
        
    def navigate_next(self):
        """Find and navigate to the next $element$ after current position."""
        # Search for next $...$ pattern from current position
        pattern = r'\$[^$]+\$'
        
        # Get all text from current position
        text_from_current = self.text_widget.get(self.current_search_pos, tk.END)
        
        match = re.search(pattern, text_from_current)
        if not match:
            # Not found, restart from beginning
            self.current_search_pos = "1.0"
            text_from_start = self.text_widget.get("1.0", tk.END)
            match = re.search(pattern, text_from_start)
            
            if not match:
                return False  # No placeholders in entire text
        
        # Calculate exact positions
        start_offset = match.start()
        end_offset = match.end()
        
        start_pos = f"{self.current_search_pos}+{start_offset}c"
        end_pos = f"{self.current_search_pos}+{end_offset}c"
        
        # Select the placeholder
        self.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
        self.text_widget.tag_add(tk.SEL, start_pos, end_pos)
        self.text_widget.mark_set(tk.INSERT, start_pos)
        self.text_widget.see(start_pos)
        
        # Update position for next search
        self.current_search_pos = end_pos
        
        debug_console.log(f"Navigué vers placeholder: {match.group()}", level='INFO')
        return True
    
    def reset(self):
        """Reset search to beginning."""
        self.current_search_pos = "1.0"


def handle_placeholder_navigation(event):
    """Handle Tab navigation to next $element$."""
    if not isinstance(event.widget, tk.Text):
        return
        
    text_widget = event.widget
    
    # Create manager if it doesn't exist
    if not hasattr(text_widget, 'placeholder_manager'):
        text_widget.placeholder_manager = PlaceholderManager(text_widget)
        
    manager = text_widget.placeholder_manager
    
    if manager.navigate_next():
        return "break"  # Stop Tab propagation
        
    return None