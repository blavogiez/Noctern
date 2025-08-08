"""
Tests for the error panel functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from pre_compiler.error_panel import ErrorPanel

class MockParent:
    """A mock parent widget for testing."""
    def __init__(self):
        pass

@pytest.fixture
def mock_parent():
    """Provides a mock parent widget."""
    return MockParent()

@pytest.fixture
def error_panel(mock_parent):
    """Provides an ErrorPanel instance for testing."""
    # Create a real Tkinter root for testing
    root = tk.Tk()
    
    # Create a mock on_goto_line callback
    mock_callback = MagicMock()
    
    # Create the ErrorPanel
    panel = ErrorPanel(root, on_goto_line=mock_callback)
    
    yield panel
    
    # Cleanup
    root.destroy()

def test_error_panel_initialization():
    """Test that the ErrorPanel initializes correctly."""
    root = tk.Tk()
    mock_callback = MagicMock()
    
    panel = ErrorPanel(root, on_goto_line=mock_callback)
    
    # Check that the panel has the required attributes
    assert hasattr(panel, 'listbox')
    assert hasattr(panel, 'title')
    assert panel.on_goto_line == mock_callback
    
    root.destroy()

def test_error_panel_update_errors():
    """Test that the ErrorPanel updates errors correctly."""
    root = tk.Tk()
    mock_callback = MagicMock()
    
    panel = ErrorPanel(root, on_goto_line=mock_callback)
    
    # Test with empty errors
    panel.update_errors([])
    assert panel.listbox.size() == 0
    assert panel.errors == []
    
    # Test with some errors
    errors = [
        {"line": 10, "error": "Mismatched braces"},
        {"line": 15, "error": "Missing file: test.tex"}
    ]
    
    panel.update_errors(errors)
    assert panel.listbox.size() == 2
    assert panel.errors == errors
    
    # Check that the listbox contains the correct items
    assert panel.listbox.get(0) == "L10: Mismatched braces"
    assert panel.listbox.get(1) == "L15: Missing file: test.tex"
    
    root.destroy()

def test_error_panel_on_error_select():
    """Test that the ErrorPanel handles error selection correctly."""
    root = tk.Tk()
    mock_callback = MagicMock()
    
    panel = ErrorPanel(root, on_goto_line=mock_callback)
    
    # Add some errors
    errors = [
        {"line": 10, "error": "Mismatched braces"},
        {"line": 15, "error": "Missing file: test.tex"}
    ]
    panel.update_errors(errors)
    
    # Simulate selecting the first error
    panel.listbox.selection_set(0)
    
    # Create a mock event
    event = MagicMock()
    
    # Call the on_error_select method
    panel.on_error_select(event)
    
    # Check that the callback was called with the correct line number
    mock_callback.assert_called_once_with(10)
    
    # Test with no selection
    panel.listbox.selection_clear(0)
    mock_callback.reset_mock()
    
    panel.on_error_select(event)
    mock_callback.assert_not_called()
    
    # Test with no callback
    panel_no_callback = ErrorPanel(root, on_goto_line=None)
    panel_no_callback.update_errors(errors)
    panel_no_callback.listbox.selection_set(0)
    panel_no_callback.on_error_select(event)  # Should not raise an error
    
    root.destroy()

def test_error_panel_with_invalid_errors():
    """Test that the ErrorPanel handles invalid errors gracefully."""
    root = tk.Tk()
    mock_callback = MagicMock()
    
    panel = ErrorPanel(root, on_goto_line=mock_callback)
    
    # Test with errors missing line numbers
    errors = [
        {"error": "Mismatched braces"},
        {"line": 15, "error": "Missing file: test.tex"}
    ]
    
    panel.update_errors(errors)
    assert panel.listbox.size() == 2
    assert panel.errors == errors
    
    root.destroy()