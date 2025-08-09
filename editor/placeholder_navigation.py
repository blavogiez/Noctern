"""
This module provides functionalities for managing and navigating placeholders within expanded snippets.
It allows users to move between placeholders using the Tab key, enhancing the snippet expansion experience.
"""

import tkinter as tk
import re
from utils import debug_console


class PlaceholderManager:
    """
    A class to manage placeholder navigation within a Tkinter Text widget.
    
    This class handles the identification of placeholders in expanded snippets
    and provides navigation between them using the Tab key.
    """
    
    def __init__(self, text_widget):
        """
        Initialize the PlaceholderManager with a text widget.
        
        Args:
            text_widget (tk.Text): The text widget where placeholders will be managed.
        """
        self.text_widget = text_widget
        self.placeholder_positions = []
        self.current_placeholder_index = -1
        
    def find_placeholders(self, start_index, end_index):
        """
        Find all placeholders within a specified range of the text widget.
        
        Args:
            start_index (str): The starting index to search for placeholders.
            end_index (str): The ending index to search for placeholders.
        """
        # Get the text content between start and end indices
        content = self.text_widget.get(start_index, end_index)
        
        # Find all placeholders in the format $1$, $2$, etc.
        pattern = r'\$(\d+)\$'
        matches = re.finditer(pattern, content)
        
        # Convert relative positions to absolute positions in the text widget
        self.placeholder_positions = []
        
        # Get the line and column of the start index
        start_line, start_col = map(int, start_index.split('.'))
        
        for match in matches:
            # Calculate absolute positions
            # First, find the line and column of the match relative to the start
            match_start = match.start()
            match_end = match.end()
            
            # Count newlines to determine the line offset
            newlines_before_match = content[:match_start].count('\n')
            line_of_match = start_line + newlines_before_match
            
            # Calculate column position
            if newlines_before_match == 0:
                col_of_match = start_col + match_start
                col_of_end = start_col + match_end
            else:
                # Find the last newline before the match
                last_newline_pos = content.rfind('\n', 0, match_start)
                col_of_match = match_start - last_newline_pos - 1
                col_of_end = match_end - last_newline_pos - 1
            
            # Create absolute index strings
            abs_start = f"{line_of_match}.{col_of_match}"
            abs_end = f"{line_of_match}.{col_of_end}"
            
            # Store placeholder info
            placeholder_info = {
                'start': abs_start,
                'end': abs_end,
                'number': int(match.group(1))
            }
            
            self.placeholder_positions.append(placeholder_info)
        
        # Sort placeholders by their number
        self.placeholder_positions.sort(key=lambda x: x['number'])
        
        # Initialize current index
        self.current_placeholder_index = 0 if self.placeholder_positions else -1
        
        debug_console.log(f"Found {len(self.placeholder_positions)} placeholders", level='INFO')
    
    def navigate_to_next_placeholder(self):
        """
        Navigate to the next placeholder in the sequence.
        
        Returns:
            bool: True if navigation was successful, False if no more placeholders.
        """
        if not self.placeholder_positions or self.current_placeholder_index >= len(self.placeholder_positions):
            return False
            
        # Get current placeholder
        placeholder = self.placeholder_positions[self.current_placeholder_index]
        
        # Move cursor to the placeholder position
        self.text_widget.mark_set(tk.INSERT, placeholder['start'])
        self.text_widget.see(placeholder['start'])
        
        # Select the placeholder text (including $ signs)
        self.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
        self.text_widget.tag_add(tk.SEL, placeholder['start'], placeholder['end'])
        
        # Move to next placeholder for next navigation
        self.current_placeholder_index += 1
        
        return True
    
    def has_placeholders(self):
        """
        Check if there are placeholders to navigate.
        
        Returns:
            bool: True if placeholders exist, False otherwise.
        """
        return len(self.placeholder_positions) > 0
    
    def clear_placeholders(self):
        """
        Clear the current placeholder positions.
        """
        self.placeholder_positions = []
        self.current_placeholder_index = -1


def handle_placeholder_navigation(event):
    """
    Handle Tab key press for placeholder navigation.
    
    This function should be bound to the Tab key event in the text widget.
    
    Args:
        event (tk.Event): The Tkinter event object.
        
    Returns:
        str or None: Returns "break" to stop further event propagation
                     if a placeholder navigation occurred, otherwise None.
    """
    # Ensure the event originated from a Tkinter Text widget
    if not isinstance(event.widget, tk.Text):
        return
        
    text_widget = event.widget
    
    # Check if the widget has a placeholder manager
    if not hasattr(text_widget, 'placeholder_manager'):
        return
        
    placeholder_manager = text_widget.placeholder_manager
    
    # Try to navigate to the next placeholder
    if placeholder_manager.has_placeholders():
        if placeholder_manager.navigate_to_next_placeholder():
            return "break"
        else:
            # No more placeholders, clear the placeholder manager
            placeholder_manager.clear_placeholders()
            
    return