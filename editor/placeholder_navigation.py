"""
Enhanced module for ⟨placeholder⟩ navigation in snippets.
Uses mathematical angle brackets to avoid conflicts with LaTeX $ symbols.
"""

import tkinter as tk
import re
from utils import debug_console


class PlaceholderManager:
    """Enhanced manager for navigating between ⟨placeholder⟩ elements from snippets."""
    
    # Placeholder pattern using mathematical angle brackets (U+27E8, U+27E9)
    PLACEHOLDER_PATTERN = r'⟨[^⟩]+⟩'
    PLACEHOLDER_START = '⟨'
    PLACEHOLDER_END = '⟩'
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.current_search_pos = "1.0"
        self.snippet_placeholders = []  # Track placeholders from recent snippet insertion
        self.snippet_insertion_point = None
        
    def set_snippet_context(self, insertion_point, snippet_text):
        """Set context for snippet-specific placeholder navigation."""
        self.snippet_insertion_point = insertion_point
        self.snippet_placeholders = []
        
        # Find all placeholders in the snippet text
        for match in re.finditer(self.PLACEHOLDER_PATTERN, snippet_text):
            self.snippet_placeholders.append({
                'text': match.group(),
                'start_offset': match.start(),
                'end_offset': match.end()
            })
        
        debug_console.log(f"Found {len(self.snippet_placeholders)} placeholders in snippet", level='DEBUG')
        
    def navigate_next(self):
        """Find and navigate to the closest ⟨placeholder⟩ from current cursor position."""
        return self.navigate_to_closest_placeholder()
    
    def navigate_to_closest_placeholder(self):
        """Navigate to the closest placeholder TO THE RIGHT (forward) of current cursor position."""
        # Get current cursor position
        try:
            current_pos = self.text_widget.index(tk.INSERT)
        except tk.TclError:
            current_pos = "1.0"
        
        # Find all placeholders in document
        full_text = self.text_widget.get("1.0", tk.END)
        all_matches = list(re.finditer(self.PLACEHOLDER_PATTERN, full_text))
        
        if not all_matches:
            debug_console.log("No placeholders found in document", level='DEBUG')
            return False
        
        # Convert current position to character index for distance calculation
        current_char_idx = self._pos_to_char_index(current_pos)
        
        # Find closest placeholder TO THE RIGHT (after current position)
        closest_match = None
        min_distance = float('inf')
        
        for match in all_matches:
            match_start_idx = match.start()
            
            # Skip if this is the currently selected placeholder
            if self._is_currently_selected(match_start_idx, match.end()):
                continue
            
            # Only consider placeholders AFTER current position (to the right)
            if match_start_idx <= current_char_idx:
                continue
            
            # Calculate forward distance
            distance = match_start_idx - current_char_idx
            
            if distance < min_distance:
                min_distance = distance
                closest_match = match
        
        # If no forward placeholder found, wrap to first placeholder
        if closest_match is None:
            # Find the first unselected placeholder from beginning
            for match in all_matches:
                if not self._is_currently_selected(match.start(), match.end()):
                    closest_match = match
                    break
            
            # If still nothing, just take the first one
            if closest_match is None:
                closest_match = all_matches[0]
        
        # Navigate to the closest forward placeholder
        return self._navigate_to_match(closest_match)
    
    def _pos_to_char_index(self, pos):
        """Convert Tkinter position (line.col) to character index."""
        try:
            return len(self.text_widget.get("1.0", pos))
        except tk.TclError:
            return 0
    
    def _is_currently_selected(self, start_char_idx, end_char_idx):
        """Check if the placeholder at given indices is currently selected."""
        try:
            # Check if there's a selection
            sel_start = self.text_widget.index(tk.SEL_FIRST)
            sel_end = self.text_widget.index(tk.SEL_LAST)
            
            # Convert selection positions to character indices
            sel_start_char = self._pos_to_char_index(sel_start)
            sel_end_char = self._pos_to_char_index(sel_end)
            
            # Check if selection matches this placeholder
            return (sel_start_char == start_char_idx and sel_end_char == end_char_idx)
            
        except tk.TclError:
            # No selection
            return False
    
    def _navigate_to_match(self, match):
        """Navigate to a specific regex match."""
        try:
            # Convert character indices back to Tkinter positions
            start_pos = f"1.0+{match.start()}c"
            end_pos = f"1.0+{match.end()}c"
            
            # Select the placeholder
            self.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
            self.text_widget.tag_add(tk.SEL, start_pos, end_pos)
            self.text_widget.mark_set(tk.INSERT, start_pos)
            self.text_widget.see(start_pos)
            
            # Update position for next search
            self.current_search_pos = end_pos
            
            debug_console.log(f"Navigated to closest placeholder: {match.group()}", level='INFO')
            return True
            
        except tk.TclError as e:
            debug_console.log(f"Error navigating to placeholder: {e}", level='WARNING')
            return False
    
    def navigate_to_next_placeholder(self):
        """Navigate to the next placeholder (for backward compatibility)."""
        return self.navigate_next()
        
    def has_placeholders(self):
        """Check if there are any placeholders in the document."""
        text_content = self.text_widget.get("1.0", tk.END)
        return bool(re.search(self.PLACEHOLDER_PATTERN, text_content))
        
    def find_placeholders(self, start_pos, end_pos):
        """Find placeholders in specified text range (for backward compatibility)."""
        text_range = self.text_widget.get(start_pos, end_pos)
        placeholders = list(re.finditer(self.PLACEHOLDER_PATTERN, text_range))
        debug_console.log(f"Found {len(placeholders)} placeholders in range {start_pos}-{end_pos}", level='DEBUG')
        return len(placeholders) > 0
    
    def reset(self):
        """Reset search to beginning."""
        self.current_search_pos = "1.0"
        self.snippet_placeholders = []
        self.snippet_insertion_point = None

    @classmethod
    def convert_legacy_placeholders(cls, text):
        """Convert legacy $placeholder$ format to new ⟨placeholder⟩ format."""
        # Convert $text$ to ⟨text⟩ but avoid LaTeX math expressions
        # Only convert isolated $word$ patterns that look like placeholders
        pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)\$'
        return re.sub(pattern, r'⟨\1⟩', text)
        
    @classmethod
    def create_placeholder(cls, content):
        """Create a new placeholder with the specified content."""
        return f"{cls.PLACEHOLDER_START}{content}{cls.PLACEHOLDER_END}"


def handle_placeholder_navigation(event):
    """Handle Tab navigation to next ⟨placeholder⟩ element."""
    if not isinstance(event.widget, tk.Text):
        return
        
    text_widget = event.widget
    
    # Create manager if it doesn't exist
    if not hasattr(text_widget, 'placeholder_manager'):
        text_widget.placeholder_manager = PlaceholderManager(text_widget)
        
    manager = text_widget.placeholder_manager
    
    # Only navigate if there are placeholders to avoid interfering with normal Tab behavior
    if manager.has_placeholders() and manager.navigate_next():
        return "break"  # Stop Tab propagation
        
    return None