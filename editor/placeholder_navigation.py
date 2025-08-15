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
        """Find and navigate to the next ⟨placeholder⟩ after current position."""
        # Search for next placeholder pattern from current position
        text_from_current = self.text_widget.get(self.current_search_pos, tk.END)
        
        match = re.search(self.PLACEHOLDER_PATTERN, text_from_current)
        if not match:
            # Not found, restart from beginning
            self.current_search_pos = "1.0"
            text_from_start = self.text_widget.get("1.0", tk.END)
            match = re.search(self.PLACEHOLDER_PATTERN, text_from_start)
            
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
        
        debug_console.log(f"Navigated to placeholder: {match.group()}", level='INFO')
        return True
    
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