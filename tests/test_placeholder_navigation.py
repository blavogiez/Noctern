"""
This module contains tests for the placeholder navigation functionality.
"""

import tkinter as tk
import pytest
from editor.placeholder_navigation import PlaceholderManager


class TestPlaceholderManager:
    """Tests for the PlaceholderManager class."""
    
    def test_find_placeholders(self):
        """Test finding placeholders in text."""
        # Create a root window for the text widget
        root = tk.Tk()
        
        # Create a text widget
        text_widget = tk.Text(root)
        text_widget.insert("1.0", "\\begin{itemize}\n    \\item $1$\n    \\item $2$\n    \\item $0$\n\\end{itemize}")
        
        # Create a placeholder manager
        manager = PlaceholderManager(text_widget)
        
        # Find placeholders
        manager.find_placeholders("1.0", "end")
        
        # Check that placeholders were found
        assert len(manager.placeholder_positions) == 3
        # Check that placeholders are sorted by their number (0, 1, 2)
        assert manager.placeholder_positions[0]['number'] == 0
        assert manager.placeholder_positions[1]['number'] == 1
        assert manager.placeholder_positions[2]['number'] == 2
        
        # Clean up
        root.destroy()
    
    def test_navigate_to_next_placeholder(self):
        """Test navigating to the next placeholder."""
        # Create a root window for the text widget
        root = tk.Tk()
        
        # Create a text widget
        text_widget = tk.Text(root)
        text_widget.insert("1.0", "\\begin{itemize}\n    \\item $1$\n    \\item $2$\n    \\item $0$\n\\end{itemize}")
        
        # Create a placeholder manager
        manager = PlaceholderManager(text_widget)
        
        # Find placeholders
        manager.find_placeholders("1.0", "end")
        
        # Navigate to the first placeholder
        result = manager.navigate_to_next_placeholder()
        assert result == True
        
        # Check that the cursor is at the first placeholder
        cursor_pos = text_widget.index(tk.INSERT)
        assert cursor_pos == manager.placeholder_positions[0]['start']
        
        # Navigate to the second placeholder
        result = manager.navigate_to_next_placeholder()
        assert result == True
        
        # Check that the cursor is at the second placeholder
        cursor_pos = text_widget.index(tk.INSERT)
        assert cursor_pos == manager.placeholder_positions[1]['start']
        
        # Navigate to the third placeholder
        result = manager.navigate_to_next_placeholder()
        assert result == True
        
        # Check that the cursor is at the third placeholder
        cursor_pos = text_widget.index(tk.INSERT)
        assert cursor_pos == manager.placeholder_positions[2]['start']
        
        # Try to navigate beyond the last placeholder
        result = manager.navigate_to_next_placeholder()
        assert result == False
        
        # Clean up
        root.destroy()
    
    def test_has_placeholders(self):
        """Test checking if there are placeholders."""
        # Create a root window for the text widget
        root = tk.Tk()
        
        # Create a text widget with placeholders
        text_widget = tk.Text(root)
        text_widget.insert("1.0", "\\begin{itemize}\n    \\item $1$\n\\end{itemize}")
        
        # Create a placeholder manager
        manager = PlaceholderManager(text_widget)
        
        # Find placeholders
        manager.find_placeholders("1.0", "end")
        
        # Check that there are placeholders
        assert manager.has_placeholders() == True
        
        # Create a text widget without placeholders
        text_widget2 = tk.Text(root)
        text_widget2.insert("1.0", "\\begin{itemize}\n    \\item \n\\end{itemize}")
        
        # Create a placeholder manager
        manager2 = PlaceholderManager(text_widget2)
        
        # Find placeholders
        manager2.find_placeholders("1.0", "end")
        
        # Check that there are no placeholders
        assert manager2.has_placeholders() == False
        
        # Clean up
        root.destroy()
    
    def test_clear_placeholders(self):
        """Test clearing placeholders."""
        # Create a root window for the text widget
        root = tk.Tk()
        
        # Create a text widget
        text_widget = tk.Text(root)
        text_widget.insert("1.0", "\\begin{itemize}\n    \\item $1$\n\\end{itemize}")
        
        # Create a placeholder manager
        manager = PlaceholderManager(text_widget)
        
        # Find placeholders
        manager.find_placeholders("1.0", "end")
        
        # Check that there are placeholders
        assert len(manager.placeholder_positions) == 1
        
        # Clear placeholders
        manager.clear_placeholders()
        
        # Check that there are no placeholders
        assert len(manager.placeholder_positions) == 0
        assert manager.current_placeholder_index == -1
        
        # Clean up
        root.destroy()


if __name__ == "__main__":
    pytest.main([__file__])