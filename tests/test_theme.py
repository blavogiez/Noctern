"""
Tests for the theme management module.
"""

import pytest
from unittest.mock import MagicMock
from app import theme
import ttkbootstrap as ttk

@pytest.fixture
def mock_style_light():
    """Provides a mock style object simulating a light theme environment."""
    style = MagicMock()
    style.colors = ttk.Style(theme="litera").colors
    # Simulate the check for a light theme
    style.lookup.return_value = style.colors.light
    return style

@pytest.fixture
def mock_style_dark():
    """Provides a mock style object simulating a dark theme environment."""
    style = MagicMock()
    style.colors = ttk.Style(theme="darkly").colors
    # Simulate the check for a dark theme
    style.lookup.return_value = style.colors.dark
    return style

def test_original_theme_selection_color(mock_style_light):
    """
    Tests that the 'original' theme returns the correct, softened green
    for the selection background color.
    """
    # Arrange
    theme_name = "original"
    
    # Act
    colors = theme.get_theme_colors(mock_style_light, theme_name)
    
    # Assert
    assert colors["sel_bg"] == "#A8DDA8"

def test_get_theme_colors_returns_dict_light(mock_style_light):
    """
    Tests that get_theme_colors returns a dictionary for a light theme.
    """
    # Arrange
    theme_name = "litera"
    
    # Act
    colors = theme.get_theme_colors(mock_style_light, theme_name)
    
    # Assert
    assert isinstance(colors, dict)
    assert "editor_bg" in colors
    assert colors["editor_bg"] == mock_style_light.colors.light

def test_get_theme_colors_returns_dict_dark(mock_style_dark):
    """
    Tests that get_theme_colors returns a dictionary for a dark theme.
    """
    # Arrange
    theme_name = "darkly"
    
    # Act
    colors = theme.get_theme_colors(mock_style_dark, theme_name)
    
    # Assert
    assert isinstance(colors, dict)
    assert "editor_bg" in colors
    assert colors["editor_bg"] == mock_style_dark.colors.dark