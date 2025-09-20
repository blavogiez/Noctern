

"""Handle core user actions and event-driven application responses."""

import os
import tkinter as tk
from tkinter import TclError

from app import state
from app import tab_actions
from app import session_manager

from app.ui_feedback import (
    hide_console,
    show_console,
    show_temporary_status_message,
)
from app import theme as interface_theme
from app import config as app_config

from editor.tab import EditorTab
from editor import syntax as editor_syntax
from latex import compiler as latex_compiler
from editor import wordcount as editor_wordcount
from editor import table_insertion as editor_table_insertion
from app.panels import show_table_insertion_panel
from utils import logs_console
from utils.unsaved_changes_dialog import show_unsaved_changes_dialog_multiple_files

# =============================================================================
# llm + ui orchestration - central hub for all ai interactions
# =============================================================================

from app.llm_actions import (
    analyze_compilation_diff,
    open_edit_prompts_panel,
    open_generate_text_panel,
    open_global_prompts_editor,
    open_proofreading_panel,
    open_rephrase_panel,
    open_set_keywords_panel,
    style_selected_text,
)

def perform_heavy_updates():
    """Execute heavy updates using optimized performance system."""
    state.heavy_update_timer_id = None
    
    current_tab = state.get_current_tab()
    
    if not current_tab:
        if state.outline:
            state.outline.update_outline(None)
        logs_console.log("Heavy update skipped: No active editor tab.", level='DEBUG')
        return

    # update debug sys with current doc
    if hasattr(state, 'debug_coordinator') and state.debug_coordinator and current_tab.file_path:
        try:
            content = current_tab.editor.get("1.0", tk.END)
            state.debug_coordinator.set_current_document(current_tab.file_path, content)
        except Exception as e:
            logs_console.log(f"Error updating debug system: {e}", level='WARNING')
    
    # use optimized perf system
    from app.performance_optimizer import schedule_optimized_update, UpdateType
    schedule_optimized_update(current_tab.editor, {UpdateType.ALL}, force=True)

def schedule_heavy_updates(_=None):
    """Schedule optimized heavy updates for current editor tab."""
    current_tab = state.get_current_tab()
    if not current_tab:
        return
        
    # use optimized scheduling sys
    from app.performance_optimizer import schedule_optimized_update, UpdateType
    schedule_optimized_update(current_tab.editor, {UpdateType.ALL})

def paste_image(event=None):
    """Paste image from clipboard into active editor."""
    from editor import image_paste as editor_image_paste
    editor_image_paste.paste_image_from_clipboard(state.root, state.get_current_tab, state.get_theme_setting)

def insert_table(event=None):
    """Open table insertion dialog and insert LaTeX table with snippet navigation."""
    logs_console.log("Table insertion action triggered.", level='ACTION')
    
    current_tab = state.get_current_tab()
    if not current_tab or not current_tab.editor:
        logs_console.log("No active editor tab found for table insertion.", level='WARNING')
        return
    
    def insert_callback(latex_code):
        """Insert LaTeX code and setup snippet navigation."""
        try:
            # get cursor pos
            cursor_pos = current_tab.editor.index(tk.INSERT)
            
            # insert latex code
            current_tab.editor.insert(cursor_pos, latex_code)
            
            # setup placeholder nav
            from editor.placeholder_navigation import PlaceholderManager
            if not hasattr(current_tab.editor, 'placeholder_manager'):
                current_tab.editor.placeholder_manager = PlaceholderManager(current_tab.editor)
            
            # set context for snippet nav
            manager = current_tab.editor.placeholder_manager
            manager.set_snippet_context(cursor_pos, latex_code)
            
            # focus the editor to ensure proper nav
            current_tab.editor.focus_set()
            
            # position cursor at insertion point and reset search pos
            current_tab.editor.mark_set(tk.INSERT, cursor_pos)
            manager.current_search_pos = cursor_pos
            
            # navigate to first placeholder of the inserted table
            if manager.navigate_next():
                logs_console.log("Navigating to first table placeholder", level='INFO')
            
            # update syntax highlighting
            schedule_heavy_updates()
            
            show_temporary_status_message("✅ Table inserted - use F3 to navigate placeholders")
            logs_console.log("Table with placeholders inserted successfully.", level='SUCCESS')
            
        except Exception as e:
            logs_console.log(f"Error inserting table: {e}", level='ERROR')
            show_temporary_status_message("❌ Failed to insert table")
    
    # Show integrated table panel
    show_table_insertion_panel(insert_callback)



def zoom_in(_=None):
    """Increase font size of active editor tab."""
    logs_console.log("Zoom In action triggered.", level='ACTION')
    state.zoom_manager.zoom_in()

def zoom_out(_=None):
    """Decrease font size of active editor tab."""
    logs_console.log("Zoom Out action triggered.", level='ACTION')
    state.zoom_manager.zoom_out()

def save_session():
    """Persist currently open files."""
    session_manager.save_session()

def load_session():
    """Restore previously open files if available."""
    session_manager.load_session(lambda path: create_new_tab(file_path=path))

def on_close_request():
    """Handle application close request with unsaved changes check."""
    logs_console.log("Application close request received.", level='INFO')
    if not state.root:
        return
    
    from app.exit_handler import exit_application
    exit_application()

def close_tab_by_id(tab_id):
    """
    Closes a specific tab by its notebook ID.
    """
    if tab_id in state.notebook.tabs():
        state.notebook.select(tab_id)
        close_current_tab()

def close_current_tab(event=None):
    """Close the active tab."""
    return tab_actions.close_current_tab(save_file, create_new_tab)



def create_new_tab(file_path=None, event=None):
    """Create a new editor tab."""
    tab_actions.create_new_tab(
        file_path=file_path,
        apply_theme=apply_theme,
        on_tab_changed=on_tab_changed,
        schedule_heavy_updates=schedule_heavy_updates,
        editor_factory=EditorTab,
    )



def restore_last_closed_tab(event=None):
    """Bring back the most recently closed tab when available."""
    tab_actions.restore_last_closed_tab(create_new_tab, show_temporary_status_message)



def open_file(event=None):
    """Open a file from disk."""
    return tab_actions.open_file(create_new_tab, show_temporary_status_message)



def save_file(event=None):
    """Save the active document."""
    return tab_actions.save_file(show_temporary_status_message, save_file_as)



def save_file_as(event=None):
    """Save the active document to a new path."""
    return tab_actions.save_file_as(show_temporary_status_message, on_tab_changed)



def on_tab_changed(event=None):
    """React to tab selection changes."""
    tab_actions.on_tab_changed(perform_heavy_updates)




def restart_application():
    """Restart the entire application with unsaved changes check."""
    logs_console.log("Application restart requested.", level='ACTION')
    
    from app.exit_handler import restart_application as clean_restart
    if not clean_restart():
        logs_console.log("Application restart cancelled by user.", level='INFO')

def go_to_line_in_pdf(event=None):
    """
    Navigate to the selected text in PDF preview with precise line-based positioning.
    Uses the new PreciseNavigator system for enhanced accuracy.
    """
    current_tab = state.get_current_tab()
    if not current_tab or not current_tab.editor:
        logs_console.log("No active editor tab found.", level='WARNING')
        return
        
    # get current cursor pos for precise line nav
    try:
        cursor_pos = current_tab.editor.index(tk.INSERT)
        current_line = int(cursor_pos.split('.')[0])
        
        # get selected text if available
        selected_text = ""
        try:
            selected_text = current_tab.editor.get("sel.first", "sel.last")
        except tk.TclError:
            # No selection, use current line text
            selected_text = current_tab.editor.get(f"{current_line}.0", f"{current_line}.end")
        
        if not selected_text.strip():
            logs_console.log("No text found at current position.", level='INFO')
            return
            
    except Exception as e:
        logs_console.log(f"Error getting cursor position: {e}", level='WARNING')
        return
        
    # Get enhanced context around the target line
    try:
        # Get broader context for better disambiguation
        context_start_line = max(1, current_line - 3)
        context_end_line = min(
            int(current_tab.editor.index("end-1c").split('.')[0]),
            current_line + 3
        )
        
        # Extract context before target line
        context_before = ""
        if context_start_line < current_line:
            context_before = current_tab.editor.get(f"{context_start_line}.0", f"{current_line}.0")
            
        # Extract context after target line
        context_after = ""
        if context_end_line > current_line:
            context_after = current_tab.editor.get(f"{current_line}.end", f"{context_end_line}.end")
            
        # Get full source content for SyncTeX processing
        source_content = current_tab.editor.get("1.0", "end-1c")
            
    except Exception as e:
        logs_console.log(f"Error extracting context: {e}", level='WARNING')
        context_before = ""
        context_after = ""
        source_content = ""
    
    # Use enhanced PDF preview interface with precise navigation
    if hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
        success = state.pdf_preview_interface.navigate_to_exact_line(
            line_number=current_line,
            source_text=selected_text.strip(),
            context_before=context_before,
            context_after=context_after,
            source_content=source_content
        )
        
        if success:
            show_temporary_status_message(f"✅ Navigated to line {current_line} in PDF")
        else:
            # Fallback to text-based navigation
            state.pdf_preview_interface.go_to_text_in_pdf(selected_text, context_before, context_after)
            show_temporary_status_message(f"⚠️ Used text search for line {current_line}")
    else:
        logs_console.log("PDF preview interface not available.", level='WARNING')

def apply_theme(theme_name=None, event=None):
    """
    Applies the specified theme to the entire application.
    """
    if theme_name is None:
        theme_name = state.current_theme

    logs_console.log(f"Attempting to apply theme: '{theme_name}'.", level='ACTION')
    
    new_theme, new_settings = interface_theme.apply_theme(
        theme_name, state.root, state.main_pane, state.tabs, perform_heavy_updates, state.console_output,
        state.status_bar_frame, state.status_label, state.gpu_status_label, state._app_config
    )
    state.current_theme = new_theme
    state._theme_settings = new_settings
    
    # Persist only the theme to avoid clobbering other settings
    app_config.update_and_save_config({'theme': state.current_theme})

