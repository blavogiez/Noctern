# File: editor_view.py
from PyQt6 import QtWidgets, QtCore, QtGui
from datetime import datetime

# References to main GUI components and callbacks
_root = None
_get_current_tab_callback = None
_outline_tree = None
_editor_logic = None # Will be set during initialization

# Zoom settings
_zoom_factor = 1.1
_min_font_size = 8
_max_font_size = 36

# Heavy update settings
_LARGE_FILE_LINE_THRESHOLD = 1000
_HEAVY_UPDATE_DELAY_NORMAL = 150
_HEAVY_UPDATE_DELAY_LARGE_FILE = 750
_heavy_update_timer = None # QTimer instance
_heavy_updates_paused = False # Flag to control heavy updates

def initialize(root_ref, get_current_tab_cb, outline_tree_ref, editor_logic_module):
    """Initializes the editor view manager."""
    global _root, _get_current_tab_callback, _outline_tree, _editor_logic, _heavy_update_timer
    _root = root_ref
    _get_current_tab_callback = get_current_tab_cb
    _outline_tree = outline_tree_ref
    _editor_logic = editor_logic_module

    _heavy_update_timer = QtCore.QTimer()
    _heavy_update_timer.setSingleShot(True)
    _heavy_update_timer.timeout.connect(perform_heavy_updates)

    # Connect zoom actions
    _root.action_zoom_in.triggered.connect(zoom_in)
    _root.action_zoom_out.triggered.connect(zoom_out)

def pause_heavy_updates():
    """Pauses the scheduling of heavy updates and cancels any pending one."""
    global _heavy_updates_paused
    _heavy_updates_paused = True
    if _heavy_update_timer and _heavy_update_timer.isActive():
        _heavy_update_timer.stop()

def resume_heavy_updates():
    """Resumes heavy updates and schedules one immediately."""
    global _heavy_updates_paused
    _heavy_updates_paused = False
    
    # Immediately perform one heavy update to ensure the UI is refreshed
    perform_heavy_updates()
    schedule_heavy_updates() # Schedule a debounced update for subsequent changes

def perform_heavy_updates():
    """Performs updates that might be computationally heavy."""
    current_tab = _get_current_tab_callback()
    
    # If there is no active tab, clear the outline and stop.
    if not current_tab:
        if _outline_tree:
            _outline_tree.clear() # Clear all items in QTreeWidget
        return

    _editor_logic.apply_syntax_highlighting(current_tab.editor, full_document=False)
    _editor_logic.update_outline_tree(current_tab.editor)
    current_tab.line_numbers.update() # Request repaint for line numbers

def schedule_heavy_updates():
    """Schedules heavy updates after a short delay."""
    if _heavy_updates_paused:
        return

    current_tab = _get_current_tab_callback()
    if not current_tab or not _root:
        return

    current_delay = _HEAVY_UPDATE_DELAY_NORMAL
    try:
        total_lines = current_tab.editor.document().blockCount()
        if total_lines > _LARGE_FILE_LINE_THRESHOLD:
            current_delay = _HEAVY_UPDATE_DELAY_LARGE_FILE
    except Exception: # Catch any potential errors if editor is not ready
        pass

    _heavy_update_timer.start(current_delay)

def zoom_in():
    """Increases the editor font size."""
    current_tab = _get_current_tab_callback()
    if not current_tab:
        return

    font = current_tab.editor.font()
    current_size = font.pointSize()
    new_size = int(current_size * _zoom_factor)
    new_size = min(new_size, _max_font_size)

    if new_size != current_size:
        font.setPointSize(new_size)
        current_tab.editor.setFont(font)
        current_tab.line_numbers.setFont(font) # Update line numbers font
        perform_heavy_updates()

def zoom_out():
    """Decreases the editor font size."""
    current_tab = _get_current_tab_callback()
    if not current_tab:
        return

    font = current_tab.editor.font()
    current_size = font.pointSize()
    new_size = int(current_size / _zoom_factor)
    new_size = max(new_size, _min_font_size)

    if new_size != current_size:
        font.setPointSize(new_size)
        current_tab.editor.setFont(font)
        current_tab.line_numbers.setFont(font) # Update line numbers font
        perform_heavy_updates()

def full_editor_refresh():
    """
    Performs a full refresh of the editor: clears undo stack,
    re-applies full syntax highlighting, and triggers heavy updates
    (outline, line numbers). It also resumes normal updates if they were paused.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [Perf] full_editor_refresh: Clearing undo, full re-highlight, updating outline.")
    current_tab = _get_current_tab_callback()
    if not current_tab or not current_tab.editor:
        resume_heavy_updates()
        return

    current_tab.editor.document().clearUndoRedoStacks() # Clear undo stack
    _editor_logic.apply_syntax_highlighting(current_tab.editor, full_document=True)

    global _heavy_updates_paused
    _heavy_updates_paused = False

    perform_heavy_updates()
