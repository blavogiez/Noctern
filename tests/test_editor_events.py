"""
Tests for editor events and error refresh functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from editor.tab import EditorTab

def test_editor_tab_creation():
    """Test that an EditorTab is created correctly."""
    # Create a real Tkinter root for testing
    root = tk.Tk()
    
    # Test creating an EditorTab
    tab = EditorTab(root, file_path=None, schedule_heavy_updates_callback=None)
    
    # Check that the tab has the required attributes
    assert hasattr(tab, 'editor')
    assert hasattr(tab, 'line_numbers')
    assert hasattr(tab, 'scrollbar')
    assert hasattr(tab, 'file_path')
    
    # Destroy the root to clean up
    root.destroy()

def test_editor_tab_modified_flag():
    """Test that the modified flag is set correctly."""
    # Create a real Tkinter root for testing
    root = tk.Tk()
    
    # Create an EditorTab
    tab = EditorTab(root, file_path=None, schedule_heavy_updates_callback=None)
    
    # Check initial state
    assert tab.editor.edit_modified() == 0
    
    # Simulate a key press event
    event = MagicMock()
    tab._on_key_press(event)
    
    # Destroy the root to clean up
    root.destroy()