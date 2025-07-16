"""
This module provides functionalities for zooming in and out of the editor's text content.
It adjusts the font size of the active editor tab and ensures that line numbers
and other editor elements are updated accordingly.
"""

from tkinter.font import Font

def zoom_in(get_current_tab_callback, perform_heavy_updates_callback, min_font_size, max_font_size, zoom_factor):
    """
    Increases the font size of the text in the currently active editor tab.

    The font size is increased by a `zoom_factor` but will not exceed `max_font_size`.
    After adjusting the font, it triggers a heavy update to re-render the editor
    content, including syntax highlighting and line numbers.

    Args:
        get_current_tab_callback (callable): A function that returns the current active EditorTab instance.
        perform_heavy_updates_callback (callable): A function to schedule a heavy update for the editor.
        min_font_size (int): The minimum allowed font size.
        max_font_size (int): The maximum allowed font size.
        zoom_factor (float): The factor by which to multiply the current font size.
    """
    current_tab = get_current_tab_callback()
    if not current_tab: # Do nothing if no tab is active.
        return
    
    current_size = current_tab.editor_font.cget("size") # Get the current font size.
    new_size = int(current_size * zoom_factor) # Calculate the new font size.
    new_size = min(new_size, max_font_size) # Ensure the new size does not exceed the maximum.
    
    if new_size != current_size: # Only update if the size has actually changed.
        # Create a new Font object with the updated size, preserving other font properties.
        current_tab.editor_font = Font(
            family=current_tab.editor_font.cget("family"),
            size=new_size,
            weight=current_tab.editor_font.cget("weight"),
            slant=current_tab.editor_font.cget("slant")
        )
        # Apply the new font to the editor widget.
        current_tab.editor.config(font=current_tab.editor_font)
        
        # Update the font for the line numbers and redraw them.
        if current_tab.line_numbers:
            current_tab.line_numbers.font = current_tab.editor_font
            current_tab.line_numbers.redraw()
            
        perform_heavy_updates_callback() # Trigger a heavy update to re-render editor content.

def zoom_out(get_current_tab_callback, perform_heavy_updates_callback, min_font_size, max_font_size, zoom_factor):
    """
    Decreases the font size of the text in the currently active editor tab.

    The font size is decreased by dividing by a `zoom_factor` but will not go below `min_font_size`.
    After adjusting the font, it triggers a heavy update to re-render the editor
    content, including syntax highlighting and line numbers.

    Args:
        get_current_tab_callback (callable): A function that returns the current active EditorTab instance.
        perform_heavy_updates_callback (callable): A function to schedule a heavy update for the editor.
        min_font_size (int): The minimum allowed font size.
        max_font_size (int): The maximum allowed font size.
        zoom_factor (float): The factor by which to divide the current font size.
    """
    current_tab = get_current_tab_callback()
    if not current_tab: # Do nothing if no tab is active.
        return
    
    current_size = current_tab.editor_font.cget("size") # Get the current font size.
    new_size = int(current_size / zoom_factor) # Calculate the new font size.
    new_size = max(new_size, min_font_size) # Ensure the new size does not go below the minimum.
    
    if new_size != current_size: # Only update if the size has actually changed.
        # Create a new Font object with the updated size, preserving other font properties.
        current_tab.editor_font = Font(
            family=current_tab.editor_font.cget("family"),
            size=new_size,
            weight=current_tab.editor_font.cget("weight"),
            slant=current_tab.editor_font.cget("slant")
        )
        # Apply the new font to the editor widget.
        current_tab.editor.config(font=current_tab.editor_font)
        
        # Update the font for the line numbers and redraw them.
        if current_tab.line_numbers:
            current_tab.line_numbers.font = current_tab.editor_font
            current_tab.line_numbers.redraw()
            
        perform_heavy_updates_callback() # Trigger a heavy update to re-render editor content.
