import tkinter as tk
from tkinter.font import Font
from datetime import datetime

# References to main GUI components and callbacks
_root = None
_get_current_tab_callback = None
_outline_tree = None
_editor_logic = None

# Zoom settings
_zoom_factor = 1.1
_min_font_size = 8
_max_font_size = 36

# Heavy update settings
_LARGE_FILE_LINE_THRESHOLD = 1000
_HEAVY_UPDATE_DELAY_NORMAL = 150
_HEAVY_UPDATE_DELAY_LARGE_FILE = 750
_heavy_update_timer_id = None
_heavy_updates_paused = False

# Performance optimization: Cache for line count calculations
_last_line_count_cache = {}
_last_file_size_check = {}

def initialize(root_ref, get_current_tab_cb, outline_tree_ref, editor_logic_module):
    """Initializes the editor view manager."""
    global _root, _get_current_tab_callback, _outline_tree, _editor_logic
    _root = root_ref
    _get_current_tab_callback = get_current_tab_cb
    _outline_tree = outline_tree_ref
    _editor_logic = editor_logic_module

def pause_heavy_updates():
    """Pauses the scheduling of heavy updates and cancels any pending one."""
    global _heavy_updates_paused, _heavy_update_timer_id
    _heavy_updates_paused = True
    if _root and _heavy_update_timer_id is not None:
        _root.after_cancel(_heavy_update_timer_id)
        _heavy_update_timer_id = None

def resume_heavy_updates():
    """Resumes heavy updates and schedules one immediately."""
    global _heavy_updates_paused
    _heavy_updates_paused = False
    schedule_heavy_updates()

def _get_file_size_category(editor):
    """Efficiently determine if file is large, with caching."""
    editor_id = id(editor)
    
    try:
        # Use a more efficient way to get line count
        content = editor.get("1.0", "end-1c")
        if not content:
            return "small"
        
        # Quick line count using string count (much faster than tkinter operations)
        line_count = content.count('\n') + 1
        
        # Cache the result to avoid repeated calculations
        _last_line_count_cache[editor_id] = line_count
        
        return "large" if line_count > _LARGE_FILE_LINE_THRESHOLD else "small"
    except Exception:
        # If we can't access the editor, assume small file
        return "small"

def perform_heavy_updates():
    """Performs updates that might be computationally heavy."""
    global _heavy_update_timer_id
    _heavy_update_timer_id = None
    
    if _heavy_updates_paused:
        return
    
    current_tab = _get_current_tab_callback()
    
    # If there is no active tab, clear the outline and stop
    if not current_tab:
        if _outline_tree:
            # Use delete() more efficiently
            children = _outline_tree.get_children()
            if children:  # Only delete if there are children
                _outline_tree.delete(*children)
        return

    try:
        # Batch all updates together to minimize redraws
        _editor_logic.update_outline_tree(current_tab.editor)
    except Exception as e:
        # Handle cases where tab might be closing or not fully initialized
        print(f"Skipping heavy updates due to: {e}")

def schedule_heavy_updates(_=None):
    """Schedules heavy updates after a short delay."""
    global _heavy_update_timer_id
    
    # Early exit if updates are paused
    if _heavy_updates_paused:
        return

    # Cancel existing timer more efficiently
    if _heavy_update_timer_id is not None:
        _root.after_cancel(_heavy_update_timer_id)
        _heavy_update_timer_id = None

    current_tab = _get_current_tab_callback()
    if not (_root and current_tab):
        return

    # Determine delay based on file size (with caching)
    file_category = _get_file_size_category(current_tab.editor)
    current_delay = _HEAVY_UPDATE_DELAY_LARGE_FILE if file_category == "large" else _HEAVY_UPDATE_DELAY_NORMAL
    
    _heavy_update_timer_id = _root.after(current_delay, perform_heavy_updates)

def _update_font_efficiently(current_tab, new_size):
    """Helper function to update fonts more efficiently."""
    if not current_tab or not hasattr(current_tab, 'editor_font'):
        return False
    
    current_size = current_tab.editor_font.cget("size")
    if new_size == current_size:
        return False  # No change needed
    
    # Reuse existing font object when possible
    current_tab.editor_font.configure(size=new_size)
    current_tab.editor.config(font=current_tab.editor_font)
    
    return True

def zoom_in(_=None):
    """Increases the editor font size."""
    current_tab = _get_current_tab_callback()
    if not current_tab:
        return

    current_size = current_tab.editor_font.cget("size")
    new_size = min(int(current_size * _zoom_factor), _max_font_size)

    if _update_font_efficiently(current_tab, new_size):
        # Schedule heavy updates instead of doing them immediately
        schedule_heavy_updates()

def zoom_out(_=None):
    """Decreases the editor font size."""
    current_tab = _get_current_tab_callback()
    if not current_tab:
        return

    current_size = current_tab.editor_font.cget("size")
    new_size = max(int(current_size / _zoom_factor), _min_font_size)

    if _update_font_efficiently(current_tab, new_size):
        # Schedule heavy updates instead of doing them immediately
        schedule_heavy_updates()

def full_editor_refresh():
    """
    Performs a full refresh of the editor: clears undo stack,
    re-applies full syntax highlighting, and triggers heavy updates.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [Perf] full_editor_refresh: Starting full refresh.")
    
    current_tab = _get_current_tab_callback()
    if not current_tab or not current_tab.editor:
        resume_heavy_updates()
        return

    try:
        # Clear undo stack
        current_tab.editor.edit_reset()
        
        # Resume heavy updates
        global _heavy_updates_paused
        _heavy_updates_paused = False
        
        # Use after_idle to prevent blocking the UI thread
        _root.after_idle(perform_heavy_updates)
        
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [Perf] full_editor_refresh: Completed.")
        
    except Exception as e:
        print(f"Error during full refresh: {e}")
        resume_heavy_updates()

def clear_caches():
    """Clear performance caches when tabs are closed."""
    global _last_line_count_cache, _last_file_size_check
    _last_line_count_cache.clear()
    _last_file_size_check.clear()