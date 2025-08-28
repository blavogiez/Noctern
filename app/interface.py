

"""Handle core user actions and event-driven application responses."""

import os
import json
import sys
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import TclError
from ttkbootstrap.dialogs import Messagebox
import configparser

from app import state
from app import statusbar as interface_statusbar
from app import file_operations as interface_fileops
from app import tab_operations as interface_tabops
from app.config import CONFIG_FILE, DEFAULT_SECTION
from app import theme as interface_theme
from app import config as app_config

from editor.tab import EditorTab
from llm import service as llm_service
from llm import autostyle as llm_autostyle
from llm import generation as llm_generation
from llm import proofreading as llm_proofreading
from llm import rephrase as llm_rephrase
from llm import keywords as llm_keywords
from llm import prompts as llm_prompts
from llm import latex_debug as llm_latex_debug
from app import panels
from editor import syntax as editor_syntax
from editor import image_manager as editor_image_manager
from latex import compiler as latex_compiler
from editor import wordcount as editor_wordcount
from editor import table_insertion as editor_table_insertion
from app.panels import show_table_insertion_panel
from utils import logs_console, animations
from utils.unsaved_changes_dialog import show_unsaved_changes_dialog_multiple_files

# =============================================================================
# LLM + UI ORCHESTRATION - Central hub for all AI interactions
# =============================================================================

def open_generate_text_panel(event=None, initial_prompt_text=None):
    """Open text generation panel with LLM integration."""
    def panel_callback(prompt_history, on_generate_callback, on_history_add_callback, initial_prompt):
        panels.show_generation_panel(prompt_history, on_generate_callback, on_history_add_callback, initial_prompt)
    
    llm_generation.prepare_text_generation(initial_prompt_text, panel_callback)

def open_proofreading_panel(event=None):
    """Open proofreading panel with LLM integration."""
    def panel_callback(editor, text_to_check):
        panels.show_proofreading_panel(editor, text_to_check)
    
    llm_proofreading.prepare_proofreading(panel_callback)

def open_rephrase_panel(event=None):
    """Open rephrase panel with LLM integration."""
    def panel_callback(original_text, on_rephrase_callback, on_cancel_callback):
        panels.show_rephrase_panel(original_text, on_rephrase_callback, on_cancel_callback)
    
    llm_rephrase.prepare_rephrase(panel_callback=panel_callback)

def open_set_keywords_panel(event=None):
    """Open keywords panel with LLM integration."""
    def panel_callback(active_file_path):
        panels.show_keywords_panel(active_file_path)
    
    llm_keywords.prepare_keywords_panel(panel_callback)

def open_edit_prompts_panel(event=None):
    """Open prompts editing panel with LLM integration."""
    def panel_callback(theme_getter, active_file_path, prompts, default_prompts, load_callback, save_callback):
        panels.show_prompts_panel(theme_getter, active_file_path, prompts, default_prompts, load_callback, save_callback)
    
    llm_prompts.prepare_edit_prompts_panel(panel_callback)

def open_global_prompts_editor(event=None):
    """Open global prompts editor panel with LLM integration."""
    def panel_callback():
        panels.show_global_prompts_panel()
    
    llm_prompts.prepare_global_prompts_editor(panel_callback)

def style_selected_text(event=None):
    """Apply automatic styling to selected text via LLM service."""
    logs_console.log("Initiating Smart Styling action.", level='ACTION')
    def panel_callback(last_intensity, on_confirm_callback, on_cancel_callback):
        panels.show_style_intensity_panel(last_intensity, on_confirm_callback, on_cancel_callback)
    
    llm_autostyle.prepare_autostyle(panel_callback)

def analyze_compilation_diff(event=None):
    """Analyze LaTeX compilation differences with LLM integration."""
    def debug_callback(diff_content, log_content, file_path, current_content):
        from app import state
        if state.debug_coordinator:
            state.debug_coordinator.handle_compilation_result(
                success=False,
                log_content=log_content,
                file_path=file_path,
                current_content=current_content
            )
    
    llm_latex_debug.prepare_compilation_analysis(debug_callback)

def perform_heavy_updates():
    """Execute heavy updates using optimized performance system."""
    state.heavy_update_timer_id = None
    
    current_tab = state.get_current_tab()
    
    if not current_tab:
        if state.outline:
            state.outline.update_outline(None)
        logs_console.log("Heavy update skipped: No active editor tab.", level='DEBUG')
        return

    # Update debug system with current document
    if hasattr(state, 'debug_coordinator') and state.debug_coordinator and current_tab.file_path:
        try:
            content = current_tab.editor.get("1.0", tk.END)
            state.debug_coordinator.set_current_document(current_tab.file_path, content)
        except Exception as e:
            logs_console.log(f"Error updating debug system: {e}", level='WARNING')
    
    # Use optimized performance system
    from app.performance_optimizer import schedule_optimized_update, UpdateType
    schedule_optimized_update(current_tab.editor, {UpdateType.ALL}, force=True)

def schedule_heavy_updates(_=None):
    """Schedule optimized heavy updates for current editor tab."""
    current_tab = state.get_current_tab()
    if not current_tab:
        return
        
    # Use optimized scheduling system
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
            # Get cursor position
            cursor_pos = current_tab.editor.index(tk.INSERT)
            
            # Insert LaTeX code
            current_tab.editor.insert(cursor_pos, latex_code)
            
            # Setup placeholder navigation
            from editor.placeholder_navigation import PlaceholderManager
            if not hasattr(current_tab.editor, 'placeholder_manager'):
                current_tab.editor.placeholder_manager = PlaceholderManager(current_tab.editor)
            
            # Set context for snippet navigation
            manager = current_tab.editor.placeholder_manager
            manager.set_snippet_context(cursor_pos, latex_code)
            
            # Navigate to first placeholder
            if manager.navigate_next():
                logs_console.log("Navigating to first table placeholder", level='INFO')
            
            # Update syntax highlighting
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

def show_console(content):
    """Display console pane with specified content."""
    if state.console_pane and state.console_output:
        if str(state.console_pane) not in state.vertical_pane.panes():
            state.vertical_pane.add(state.console_pane, height=150)

        state.console_output.config(state="normal")
        state.console_output.delete("1.0", ttk.END)
        state.console_output.insert("1.0", content)
        state.console_output.config(state="disabled")

def hide_console():
    """Hide console pane from view."""
    if state.console_pane:
        if str(state.console_pane) in state.vertical_pane.panes():
            state.vertical_pane.remove(state.console_pane)

def show_temporary_status_message(message, duration_ms=2500):
    """Display temporary status message with flash animation."""
    state._temporary_status_active = True
    
    if state.status_label:
        original_color = state.get_theme_setting('statusbar_bg', '#f0f0f0')
        flash_color = state.get_theme_setting('success', '#77dd77')
        from utils import animations
        animations.flash_widget(state.status_label, flash_color, original_color)

    from app import statusbar as interface_statusbar
    interface_statusbar.show_temporary_status_message(
        message, duration_ms, state.status_label, state.root, clear_temporary_status_message
    )

def clear_temporary_status_message():
    """
    Clears any active temporary status message and restores the default status.
    """
    state._temporary_status_active = False
    from app import status_utils
    status_utils.update_status_bar_text()
    from app import statusbar as interface_statusbar
    interface_statusbar.clear_temporary_status_message()

def save_session():
    """
    Saves the current session state (open files) to settings.conf.
    """
    open_files = [tab.file_path for tab in state.tabs.values() if tab.file_path and os.path.exists(tab.file_path)]
    
    # Load existing config
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    
    # Ensure the main section exists
    if DEFAULT_SECTION not in config:
        config[DEFAULT_SECTION] = {}
        
    # Add or update session section
    SESSION_SECTION = "Session"
    if SESSION_SECTION not in config:
        config[SESSION_SECTION] = {}
        
    # Save open files as a JSON string
    config[SESSION_SECTION]["open_files"] = json.dumps(open_files)
    
    try:
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        logs_console.log(f"Session state saved to {CONFIG_FILE}", level='INFO')
    except Exception as e:
        logs_console.log(f"Error saving session state: {e}", level='ERROR')

def load_session():
    """
    Loads the last session state from settings.conf, reopening previously opened files.
    """
    try:
        if os.path.exists(CONFIG_FILE):
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            
            SESSION_SECTION = "Session"
            if SESSION_SECTION in config and "open_files" in config[SESSION_SECTION]:
                open_files_json = config[SESSION_SECTION]["open_files"]
                open_files = json.loads(open_files_json) if open_files_json else []
                
                if open_files:
                    for file_path in open_files:
                        if os.path.exists(file_path):
                            create_new_tab(file_path)
                        else:
                            logs_console.log(f"File not found, not reopening: {file_path}", level='WARNING')
                # Skip creating empty tab if no file is open
            # Skip creating empty tab if session section doesn't exist
        # Skip creating empty tab if config file doesn't exist
    except Exception as e:
        logs_console.log(f"Error loading session state: {e}", level='ERROR')
        # Skip creating empty tab on error

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
    """
    Closes the currently active editor tab.
    """
    return interface_tabops.close_current_tab(state.get_current_tab, state.root, state.notebook, save_file, create_new_tab, state.tabs, state._closed_tabs_stack)

def create_new_tab(file_path=None, event=None):
    """
    Creates and opens a new editor tab.
    """
    interface_tabops.create_new_tab(
        file_path, state.notebook, state.tabs, apply_theme, on_tab_changed, EditorTab, schedule_heavy_updates
    )

def restore_last_closed_tab(event=None):
    """
    Reopens the most recently closed tab.
    """
    if state._closed_tabs_stack:
        file_path_to_restore = state._closed_tabs_stack.pop()
        logs_console.log(f"Attempting to restore closed tab: {file_path_to_restore or 'Untitled'}", level='ACTION')
        create_new_tab(file_path=file_path_to_restore)
    else:
        logs_console.log("No recently closed tabs available for restoration.", level='INFO')
        show_temporary_status_message("ℹ️ No recently closed tabs to restore.")

def open_file(event=None):
    """
    Opens a file dialog to select and open a file.
    """
    return interface_fileops.open_file(create_new_tab, show_temporary_status_message)

def save_file(event=None):
    """
    Saves the content of the current active editor tab.
    """
    current_tab = state.get_current_tab()
    if current_tab:
        editor_image_manager.check_for_deleted_images(current_tab)
    return interface_fileops.save_file(state.get_current_tab, show_temporary_status_message, save_file_as)

def save_file_as(event=None):
    """
    Prompts the user to save the current content to a new file path.
    """
    current_tab = state.get_current_tab()
    if current_tab:
        editor_image_manager.check_for_deleted_images(current_tab)
    return interface_fileops.save_file_as(state.get_current_tab, show_temporary_status_message, on_tab_changed)

def on_tab_changed(event=None):
    """
    Callback executed when the active tab changes.
    """
    current_tab = state.get_current_tab()
    if current_tab is None:
        # No active tab, nothing to do
        # Update metrics display for no file
        if hasattr(state, 'metrics_display') and state.metrics_display:
            state.metrics_display.set_current_file(None)
        return
        
    tab_name = os.path.basename(current_tab.file_path) if current_tab and current_tab.file_path else "Untitled"
    logs_console.log(f"Active tab changed to: '{tab_name}'.", level='ACTION')
    
    # Update metrics tracking for the new file
    if hasattr(state, 'metrics_display') and state.metrics_display:
        state.metrics_display.save_current_session()  # Save previous session
        state.metrics_display.set_current_file(current_tab.file_path)
    
    # Load LLM history and prompts for the current file
    llm_service.load_prompt_history_for_current_file()
    llm_service.load_prompts_for_current_file()
    
    perform_heavy_updates()



def restart_application():
    """Restart the entire application with unsaved changes check."""
    logs_console.log("Application restart requested.", level='ACTION')
    
    from app.exit_handler import restart_application as clean_restart
    if not clean_restart():
        logs_console.log("Application restart cancelled by user.", level='INFO')

def go_to_line_in_pdf(event=None):
    """
    Navigate to the selected text in the PDF preview with context matching.
    """
    current_tab = state.get_current_tab()
    if not current_tab or not current_tab.editor:
        logs_console.log("No active editor tab found.", level='WARNING')
        return
        
    # Get selected text
    try:
        selected_text = current_tab.editor.get("sel.first", "sel.last")
        if not selected_text.strip():
            logs_console.log("No text selected.", level='INFO')
            return
    except tk.TclError:
        logs_console.log("No text selected.", level='INFO')
        return
        
    # Get context around selected text
    try:
        # Get start and end positions of selection
        sel_start = current_tab.editor.index("sel.first")
        sel_end = current_tab.editor.index("sel.last")
        
        # Get a few lines before and after the selection
        start_line = int(sel_start.split('.')[0])
        end_line = int(sel_end.split('.')[0])
        
        # Get context before (2 lines before selection)
        context_start_line = max(1, start_line - 2)
        context_before = ""
        if context_start_line < start_line:
            context_before = current_tab.editor.get(f"{context_start_line}.0", f"{start_line}.0")
            
        # Get context after (2 lines after selection)
        # First, get the total number of lines
        last_line_index = current_tab.editor.index("end-1c")
        total_lines = int(last_line_index.split('.')[0])
        context_end_line = min(total_lines, end_line + 2)
        context_after = ""
        if context_end_line > end_line:
            context_after = current_tab.editor.get(f"{end_line}.end", f"{context_end_line}.end")
            
    except Exception as e:
        logs_console.log(f"Error getting context: {e}", level='WARNING')
        context_before = ""
        context_after = ""
        
    # Use the PDF preview interface to navigate to the text with context
    if hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
        state.pdf_preview_interface.go_to_text_in_pdf(selected_text, context_before, context_after)
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
    
    app_config_data = state.get_app_config()
    app_config_data['theme'] = state.current_theme
    app_config.save_config(app_config_data)

