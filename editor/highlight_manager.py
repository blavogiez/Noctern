"""Navigation highlight manager for visual feedback during section navigation."""

import tkinter as tk
from typing import Optional, Tuple
from utils import logs_console


class NavigationHighlightManager:
    """Manages temporary line highlighting for navigation feedback."""
    
    TAG_NAME = "nav_highlight"
    DEFAULT_DURATION = 2500  # milliseconds
    
    # Theme-based highlight colors
    HIGHLIGHT_COLORS = {
        'dark': '#ffc107',   # Amber for dark themes
        'light': '#17a2b8'   # Teal for light themes
    }
    
    def __init__(self):
        self._active_highlight: Optional[Tuple[tk.Text, int]] = None
        self._cleanup_after_id: Optional[str] = None
        self._preserve_selection = False
        
    def show_line_highlight(self, editor: tk.Text, line_number: int, 
                           duration_ms: int = DEFAULT_DURATION) -> None:
        """Show temporary highlight on specified line.
        
        Args:
            editor: Text editor widget
            line_number: Line number to highlight (1-based)  
            duration_ms: Highlight duration in milliseconds
        """
        if not self._validate_editor(editor):
            return
            
        try:
            self.clear_highlight()
            
            # Configure and apply highlight tag
            self._configure_highlight_tag(editor)
            self._apply_line_highlight(editor, line_number)
            
            # Store state and schedule cleanup
            self._active_highlight = (editor, line_number)
            self._cleanup_after_id = editor.after(duration_ms, self.clear_highlight)
            
            logs_console.log(f"Navigation highlight applied to line {line_number}", level='DEBUG')
            
        except tk.TclError as e:
            logs_console.log(f"Error applying navigation highlight: {e}", level='WARNING')
    
    def clear_highlight(self) -> None:
        """Clear current navigation highlight."""
        if self._cleanup_after_id and self._active_highlight:
            try:
                editor, _ = self._active_highlight
                if editor.winfo_exists():
                    editor.after_cancel(self._cleanup_after_id)
            except (tk.TclError, AttributeError):
                pass
                
        if self._active_highlight:
            try:
                editor, _ = self._active_highlight
                if editor.winfo_exists():
                    editor.tag_remove(self.TAG_NAME, "1.0", "end")
                    if self._preserve_selection:
                        editor.tag_remove("sel", "1.0", "end")
            except (tk.TclError, AttributeError):
                pass
                
        self._reset_state()
    
    def _validate_editor(self, editor: tk.Text) -> bool:
        """Validate editor widget is available."""
        return (editor and 
                hasattr(editor, 'winfo_exists') and 
                editor.winfo_exists())
    
    def _configure_highlight_tag(self, editor: tk.Text) -> None:
        """Configure highlight tag with theme-appropriate styling."""
        highlight_color = self._get_theme_highlight_color()
        
        editor.tag_configure(self.TAG_NAME,
                           background=highlight_color,
                           relief="solid", 
                           borderwidth=1)
    
    def _apply_line_highlight(self, editor: tk.Text, line_number: int) -> None:
        """Apply highlight to specified line with selection fallback."""
        line_start = f"{line_number}.0"
        line_end = f"{line_number}.0 lineend+1c"
        
        # Primary: Tag-based highlighting with high priority
        editor.tag_add(self.TAG_NAME, line_start, line_end)
        editor.tag_raise(self.TAG_NAME)
        
        # Fallback: Use selection if no existing selection
        if not editor.tag_ranges("sel"):
            editor.tag_add("sel", line_start, line_end)
            self._preserve_selection = True
    
    def _get_theme_highlight_color(self) -> str:
        """Get highlight color based on current theme."""
        try:
            from app import state
            current_theme = getattr(state, 'current_theme', 'litera')
            
            # Determine if theme is dark or light
            dark_themes = {'darkly', 'superhero', 'solar', 'cyborg', 'vapor'}
            theme_type = 'dark' if current_theme in dark_themes else 'light'
            
            return self.HIGHLIGHT_COLORS[theme_type]
            
        except Exception:
            return self.HIGHLIGHT_COLORS['light']
    
    def _reset_state(self) -> None:
        """Reset manager state."""
        self._active_highlight = None
        self._cleanup_after_id = None
        self._preserve_selection = False


# Global instance for consistent highlighting across the application
_highlight_manager = NavigationHighlightManager()


def show_navigation_highlight(editor: tk.Text, line_number: int) -> None:
    """Show navigation highlight on specified line.
    
    Args:
        editor: Text editor widget
        line_number: Line number to highlight (1-based)
    """
    _highlight_manager.show_line_highlight(editor, line_number)


def clear_navigation_highlight() -> None:
    """Clear current navigation highlight."""
    _highlight_manager.clear_highlight()