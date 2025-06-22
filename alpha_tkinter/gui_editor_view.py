import tkinter as tk
from tkinter.font import Font

# References to main GUI components and callbacks
_root = None
_get_current_tab_callback = None
_outline_tree = None

# External modules that need to be called for heavy updates
_editor_logic = None # Will be set during initialization

# Zoom settings
_zoom_factor = 1.1
_min_font_size = 8
_max_font_size = 36

# Heavy update settings
_LARGE_FILE_LINE_THRESHOLD = 1000
_HEAVY_UPDATE_DELAY_NORMAL = 200
_HEAVY_UPDATE_DELAY_LARGE_FILE = 2000
_heavy_update_timer_id = None

def initialize(root_ref, get_current_tab_cb, outline_tree_ref, editor_logic_module):
    """Initializes the editor view manager."""
    global _root, _get_current_tab_callback, _outline_tree, _editor_logic
    _root = root_ref
    _get_current_tab_callback = get_current_tab_cb
    _outline_tree = outline_tree_ref
    _editor_logic = editor_logic_module

def perform_heavy_updates():
    """Performs updates that might be computationally heavy."""
    global _heavy_update_timer_id
    _heavy_update_timer_id = None
    
    current_tab = _get_current_tab_callback()
    
    # If there is no active tab, clear the outline and stop.
    if not current_tab:
        if _outline_tree:
            _outline_tree.delete(*_outline_tree.get_children())
        return

    # Perform all updates for the current tab
    _editor_logic.apply_syntax_highlighting(current_tab.editor)
    _editor_logic.update_outline_tree(current_tab.editor)
    if current_tab.line_numbers:
        current_tab.line_numbers.redraw()

def schedule_heavy_updates(_=None):
    """Schedules heavy updates after a short delay."""
    global _heavy_update_timer_id
    if _root and _heavy_update_timer_id is not None:
        _root.after_cancel(_heavy_update_timer_id)
    current_tab = _get_current_tab_callback()
    if _root and current_tab: # Ensure root and a tab are available
        current_delay = _HEAVY_UPDATE_DELAY_NORMAL
        try:
            # Get total lines to determine if the file is large
            last_line_index_str = current_tab.editor.index("end-1c")
            # Correctly get total_lines, handling empty editor
            total_lines = 0
            if last_line_index_str: # Ensure index is not None or empty
                total_lines = int(last_line_index_str.split(".")[0])
                if total_lines == 1 and not current_tab.editor.get("1.0", "1.end").strip(): # Check if line 1 is empty
                    total_lines = 0
            
            if total_lines > _LARGE_FILE_LINE_THRESHOLD:
                current_delay = _HEAVY_UPDATE_DELAY_LARGE_FILE
        except tk.TclError: # Handle cases where editor might not be ready
            pass # Use normal delay
        _heavy_update_timer_id = _root.after(current_delay, perform_heavy_updates)

def zoom_in(_=None): # Accept optional event argument
    """Increases the editor font size."""
    current_tab = _get_current_tab_callback()
    if not current_tab:
        return

    current_size = current_tab.editor_font.cget("size")
    new_size = int(current_size * _zoom_factor)
    new_size = min(new_size, _max_font_size)

    if new_size != current_size:
        current_tab.editor_font = Font(family=current_tab.editor_font.cget("family"), size=new_size, weight=current_tab.editor_font.cget("weight"), slant=current_tab.editor_font.cget("slant"))
        current_tab.editor.config(font=current_tab.editor_font)
        if current_tab.line_numbers:
            current_tab.line_numbers.font = current_tab.editor_font # Update the font reference
            current_tab.line_numbers.redraw()
        perform_heavy_updates() # Reapply syntax highlighting and outline

def zoom_out(_=None): # Accept optional event argument
    """Decreases the editor font size."""
    current_tab = _get_current_tab_callback()
    if not current_tab:
        return

    current_size = current_tab.editor_font.cget("size")
    new_size = int(current_size / _zoom_factor)
    new_size = max(new_size, _min_font_size)

    if new_size != current_size:
        current_tab.editor_font = Font(family=current_tab.editor_font.cget("family"), size=new_size, weight=current_tab.editor_font.cget("weight"), slant=current_tab.editor_font.cget("slant"))
        current_tab.editor.config(font=current_tab.editor_font)
        if current_tab.line_numbers:
            current_tab.line_numbers.font = current_tab.editor_font # Update the font reference
            current_tab.line_numbers.redraw()
        perform_heavy_updates() # Reapply syntax highlighting and outline