"""
Clean, minimal exit handling with unsaved changes detection.
"""

from tkinter import TclError
from utils.unsaved_changes_dialog import show_unsaved_changes_dialog_multiple_files
from utils import logs_console
from app import state
import os


def handle_unsaved_changes():
    """
    Handle unsaved changes for application exit or restart.
    
    Returns:
        str: "save", "dont_save", or "cancel"
    """
    dirty_tabs = [tab for tab in state.tabs.values() if tab.is_dirty()]
    if not dirty_tabs:
        return "dont_save"  # No changes to save
    
    file_list = [os.path.basename(tab.file_path) if tab.file_path else "Untitled" for tab in dirty_tabs]
    return show_unsaved_changes_dialog_multiple_files(file_list, state.root)


def save_all_dirty_tabs():
    """
    Save all dirty tabs.
    
    Returns:
        bool: True if all saves succeeded, False otherwise
    """
    from app.interface import save_file
    
    tabs_copy = dict(state.tabs)
    for tab_id, tab in tabs_copy.items():
        if tab.is_dirty() and tab_id in state.notebook.tabs():
            try:
                state.notebook.select(tab_id)
                if not save_file():
                    return False
            except TclError:
                continue
    return True


def save_application_state():
    """Save application configuration and session."""
    from app import config as app_config
    from llm import state as llm_state
    from app.interface import save_session
    
    # Save window state and preferences without overwriting unrelated keys
    updates = {}
    if state.root.attributes('-fullscreen'):
        updates['window_state'] = 'Fullscreen'
    elif state.root.state() == 'zoomed':
        updates['window_state'] = 'Maximized'
    else:
        updates['window_state'] = 'Normal'

    updates['theme'] = state.current_theme

    # Preserve API keys from current config
    current_config = app_config.load_config()
    updates['gemini_api_key'] = current_config.get('gemini_api_key', '')

    # Save LLM model configuration
    updates['model_completion'] = llm_state.model_completion
    updates['model_generation'] = llm_state.model_generation
    updates['model_rephrase'] = llm_state.model_rephrase
    updates['model_debug'] = llm_state.model_debug
    updates['model_style'] = llm_state.model_style
    updates['model_proofreading'] = llm_state.model_proofreading

    app_config.update_and_save_config(updates)
    save_session()


def exit_application():
    """Clean application exit with proper state saving."""
    response = handle_unsaved_changes()
    
    if response == "cancel":
        return False  # Don't exit
    
    if response == "save":
        if not save_all_dirty_tabs():
            return False  # Save failed, don't exit
    
    save_application_state()
    
    # Save metrics if available
    if hasattr(state, 'metrics_display') and state.metrics_display:
        state.metrics_display.save_current_session()
    
    state.root.destroy()
    return True


def restart_application():
    """Clean application restart with proper state saving."""
    import sys
    import os
    
    response = handle_unsaved_changes()
    
    if response == "cancel":
        return False  # Don't restart
    
    if response == "save":
        if not save_all_dirty_tabs():
            return False  # Save failed, don't restart
    
    save_application_state()
    
    # Save metrics if available
    if hasattr(state, 'metrics_display') and state.metrics_display:
        state.metrics_display.save_current_session()
    
    python_executable = sys.executable
    os.execl(python_executable, python_executable, *sys.argv)
    return True
