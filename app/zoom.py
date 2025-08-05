"""
This module provides a ZoomManager class to handle zooming in and out of the editor.
"""

from tkinter.font import Font

class ZoomManager:
    """
    Manages the zoom functionality for the editor pane.
    """
    def __init__(self, state):
        """
        Initializes the ZoomManager.

        Args:
            state: The application state object, which provides access to the
                   current tab and other global settings.
        """
        self.state = state

    def zoom_in(self, event=None):
        """
        Increases the font size of the text in the currently active editor tab.
        """
        current_tab = self.state.get_current_tab()
        if not current_tab:
            return

        current_size = current_tab.editor_font.cget("size")
        
        # Ensure the font size increases by at least 1, even for small sizes
        new_size = max(int(current_size * self.state.zoom_factor), current_size + 1)
        
        new_size = min(new_size, self.state.max_font_size)

        if new_size != current_size:
            self._update_font_size(current_tab, new_size)

    def zoom_out(self, event=None):
        """
        Decreases the font size of the text in the currently active editor tab.
        """
        current_tab = self.state.get_current_tab()
        if not current_tab:
            return

        current_size = current_tab.editor_font.cget("size")
        new_size = int(current_size / self.state.zoom_factor)
        new_size = max(new_size, self.state.min_font_size)

        if new_size != current_size:
            self._update_font_size(current_tab, new_size)

    def _update_font_size(self, tab, new_size):
        """
        Applies the new font size to the editor and its components.
        """
        tab.editor_font = Font(
            family=tab.editor_font.cget("family"),
            size=new_size,
            weight=tab.editor_font.cget("weight"),
            slant=tab.editor_font.cget("slant")
        )
        tab.editor.config(font=tab.editor_font)

        if tab.line_numbers:
            tab.line_numbers.font = tab.editor_font
            tab.line_numbers.redraw()

        # Assuming perform_heavy_updates is available in actions
        from app import actions
        actions.perform_heavy_updates()