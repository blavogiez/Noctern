"""
Test module for the search functionality.
This module contains tests to verify the search feature works correctly.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the parent directory to the path so we can import modules from the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from editor.search import SearchBar, SearchEngine


def test_search_engine():
    """Test the SearchEngine class."""
    print("Testing SearchEngine...")
    
    # Create a mock text widget
    root = tk.Tk()
    text_widget = tk.Text(root)
    text_widget.insert("1.0", "This is a test document.\\nIt contains multiple lines.\\nThis is the third line.\\n")
    
    # Create search engine
    search_engine = SearchEngine()
    
    # Test basic search
    matches = search_engine.search(text_widget, "test")
    assert len(matches) == 1, f"Expected 1 match, got {len(matches)}"
    assert matches[0] == ("1", 10, 14), f"Expected match at (1, 10, 14), got {matches[0]}"
    
    # Test case sensitive search (should not match)
    matches = search_engine.search(text_widget, "TEST", case_sensitive=True)
    assert len(matches) == 0, f"Expected 0 match for case sensitive search, got {len(matches)}"
    
    # Test case insensitive search (should match)
    matches = search_engine.search(text_widget, "TEST", case_sensitive=False)
    assert len(matches) == 1, f"Expected 1 match for case insensitive search, got {len(matches)}"
    
    # Test multiple matches - "is" appears in "This" (2 times) and "lines" (1 time) and "This" again (2 times) = 4 times
    matches = search_engine.search(text_widget, "is", case_sensitive=False)
    assert len(matches) == 4, f"Expected 4 matches, got {len(matches)}"
    
    # Test navigation
    assert search_engine.get_total_matches() == 4
    assert search_engine.get_current_match_number() == 0
    
    # Test next match
    match = search_engine.next_match()
    assert match is not None, "Expected a match"
    assert search_engine.get_current_match_number() == 1
    
    match = search_engine.next_match()
    assert match is not None, "Expected a match"
    assert search_engine.get_current_match_number() == 2
    
    # Test wraparound
    search_engine.current_match_index = 3  # Set to last match
    match = search_engine.next_match()
    assert match is not None, "Expected a match"
    assert search_engine.get_current_match_number() == 1  # Should wrap to first
    
    # Test previous match
    search_engine.current_match_index = 0  # Set to first match
    match = search_engine.previous_match()
    assert match is not None, "Expected a match"
    assert search_engine.get_current_match_number() == 4  # Should wrap to last
    
    print("SearchEngine tests passed!")


def test_search_bar():
    """Test the SearchBar class."""
    print("Testing SearchBar...")
    
    # Create a root window
    root = tk.Tk()
    root.style = ttk.Style()  # Mock the style attribute
    
    # Create search bar
    search_bar = SearchBar(root)
    
    # Check that the search bar is initially hidden
    assert not search_bar.is_visible, "Search bar should be initially hidden"
    
    # Test showing the search bar
    search_bar.show()
    assert search_bar.is_visible, "Search bar should be visible after show()"
    
    # Test hiding the search bar
    search_bar.hide()
    assert not search_bar.is_visible, "Search bar should be hidden after hide()"
    
    print("SearchBar tests passed!")


if __name__ == "__main__":
    test_search_engine()
    test_search_bar()
    print("All tests passed!")