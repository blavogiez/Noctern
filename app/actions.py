

"""
This module contains the core action and event-handling functions for the AutomaTeX application.
These functions are typically triggered by user interactions such as menu clicks,
keyboard shortcuts, or GUI events. They orchestrate the application's response
by interacting with the state, UI components, and various backend services.
"""

import os
import json
import sys
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
from editor import syntax as editor_syntax
from editor import image_manager as editor_image_manager
from latex import compiler as latex_compiler
from editor import wordcount as editor_wordcount
from utils import debug_console, animations

def style_selected_text(event=None):
    """
    Main function to apply automatic styling to the selected text.
    This is a wrapper that calls the LLM service, which handles all logic.
    """
    debug_console.log("Initiating Smart Styling action.", level='ACTION')
    llm_service.start_autostyle_process()

def perform_heavy_updates():
    """
    Executes computationally intensive updates for the active editor tab.
    This function is debounced.
    """
    state.heavy_update_timer_id = None
    
    current_tab = state.get_current_tab()
    
    if not current_tab:
        if state.outline:
            state.outline.update_outline(None)
        debug_console.log("Heavy update skipped: No active editor tab.", level='DEBUG')
        return


    tab_name = os.path.basename(current_tab.file_path) if current_tab.file_path else "Untitled"
    debug_console.log(f"Initiating heavy updates for tab: '{tab_name}'.", level='INFO')
    
    editor_syntax.apply_syntax_highlighting(current_tab.editor)
    if state.outline:
        state.outline.update_outline(current_tab.editor)

    if not state._temporary_status_active:
        from app import status_utils
        status_utils.update_status_bar_text()

    if current_tab.line_numbers:
        current_tab.line_numbers.redraw()

def schedule_heavy_updates(_=None):
    """
    Schedules the `perform_heavy_updates` function to run after a delay.
    This function acts as a debouncer.
    """
    if state.root and state.heavy_update_timer_id is not None:
        state.root.after_cancel(state.heavy_update_timer_id)
    
    current_tab = state.get_current_tab()
    if state.root and current_tab:
        current_delay = state.HEAVY_UPDATE_DELAY_NORMAL
        try:
            last_line_index_str = current_tab.editor.index("end-1c")
            total_lines = 0
            if last_line_index_str:
                total_lines = int(last_line_index_str.split(".")[0])
                if total_lines == 1 and not current_tab.editor.get("1.0", "1.end").strip():
                    total_lines = 0
            
            if total_lines > state.LARGE_FILE_LINE_THRESHOLD:
                current_delay = state.HEAVY_UPDATE_DELAY_LARGE_FILE
        except TclError:
            debug_console.log("Error determining total lines for heavy update delay.", level='WARNING')
            pass
        
        state.heavy_update_timer_id = state.root.after(current_delay, perform_heavy_updates)

def paste_image(event=None):
    """
    Triggers the image pasting functionality from the clipboard into the active editor.
    """
    from editor import image_paste as editor_image_paste
    editor_image_paste.paste_image_from_clipboard(state.root, state.get_current_tab, state.get_theme_setting)

def zoom_in(_=None):
    """
    Increases the font size of the active editor tab.
    """
    debug_console.log("Zoom In action triggered.", level='ACTION')
    state.zoom_manager.zoom_in()

def zoom_out(_=None):
    """
    Decreases the font size of the active editor tab.
    """
    debug_console.log("Zoom Out action triggered.", level='ACTION')
    state.zoom_manager.zoom_out()

def show_console(content):
    """
    Displays the console pane with the given content.
    """
    if state.console_pane and state.console_output:
        if str(state.console_pane) not in state.vertical_pane.panes():
            state.vertical_pane.add(state.console_pane, height=150)

        state.console_output.config(state="normal")
        state.console_output.delete("1.0", ttk.END)
        state.console_output.insert("1.0", content)
        state.console_output.config(state="disabled")

def hide_console():
    """
    Hides the console pane.
    """
    if state.console_pane:
        if str(state.console_pane) in state.vertical_pane.panes():
            state.vertical_pane.remove(state.console_pane)

def show_temporary_status_message(message, duration_ms=2500):
    """
    Displays a temporary message in the status bar with a subtle flash animation.
    """
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
        debug_console.log(f"Session state saved to {CONFIG_FILE}", level='INFO')
    except Exception as e:
        debug_console.log(f"Error saving session state: {e}", level='ERROR')

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
                            debug_console.log(f"File not found, not reopening: {file_path}", level='WARNING')
                else:
                    create_new_tab(None)
            else:
                create_new_tab(None)
        else:
            create_new_tab(None)
    except Exception as e:
        debug_console.log(f"Error loading session state: {e}", level='ERROR')
        create_new_tab(None)

def on_close_request():
    """
    Handles the application close request, prompting to save unsaved changes.
    """
    debug_console.log("Application close request received.", level='INFO')
    if not state.root:
        return

    app_config_data = state.get_app_config()
    if state.root.attributes('-fullscreen'):
        app_config_data['window_state'] = 'Fullscreen'
    elif state.root.state() == 'zoomed':
        app_config_data['window_state'] = 'Maximized'
    else:
        app_config_data['window_state'] = 'Normal'
    
    app_config_data['theme'] = state.current_theme
    app_config.save_config(app_config_data)
    
    dirty_tabs = [tab for tab in state.tabs.values() if tab.is_dirty()]
    if dirty_tabs:
        file_list = "\n - ".join([os.path.basename(tab.file_path) if tab.file_path else "Untitled" for tab in dirty_tabs])
        response = Messagebox.yesno("Unsaved Changes", f"You have unsaved changes in the following files:\n - {file_list}\n\nDo you want to save them before closing?", parent=state.root)
        
        if response == "Yes":
            all_saved = True
            # Create a copy of the tabs dictionary since we'll be modifying it during iteration
            tabs_copy = dict(state.tabs)
            for tab_id, tab in tabs_copy.items():
                if tab.is_dirty():
                    # Check if the tab still exists before trying to select it
                    if tab_id in state.notebook.tabs():
                        try:
                            state.notebook.select(tab_id)
                            if not save_file():
                                all_saved = False
                                break
                        except TclError:
                            # Tab might have been closed already, skip it
                            continue
            if all_saved:
                save_session()
                state.root.destroy()
        elif response == "No":
            save_session()
            state.root.destroy()
    else:
        save_session()
        state.root.destroy()

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

    if file_path and file_path.endswith(".tex"):
        auto_open_var = state.get_auto_open_pdf_var()
        if auto_open_var and auto_open_var.get():
            pdf_path = file_path.replace(".tex", ".pdf")
            if os.path.exists(pdf_path):
                debug_console.log(f"Auto-opening PDF: {pdf_path}", level='INFO')
                latex_compiler.view_pdf_external(pdf_path=pdf_path)
            else:
                debug_console.log(f"Auto-open PDF: Corresponding PDF not found at {pdf_path}", level='DEBUG')

def restore_last_closed_tab(event=None):
    """
    Reopens the most recently closed tab.
    """
    if state._closed_tabs_stack:
        file_path_to_restore = state._closed_tabs_stack.pop()
        debug_console.log(f"Attempting to restore closed tab: {file_path_to_restore or 'Untitled'}", level='ACTION')
        create_new_tab(file_path=file_path_to_restore)
    else:
        debug_console.log("No recently closed tabs available for restoration.", level='INFO')
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
    tab_name = os.path.basename(current_tab.file_path) if current_tab and current_tab.file_path else "Untitled"
    debug_console.log(f"Active tab changed to: '{tab_name}'.", level='ACTION')
    
    llm_service.load_prompt_history_for_current_file()
    llm_service.load_prompts_for_current_file()
    
    perform_heavy_updates()

def toggle_auto_open_pdf():
    """
    Callback to update and save the auto-open PDF setting.
    """
    app_config_data = state.get_app_config()
    auto_open_var = state.get_auto_open_pdf_var()
    if auto_open_var:
        new_value = auto_open_var.get()
        app_config_data['auto_open_pdf'] = str(new_value)
        app_config.save_config(app_config_data)
        debug_console.log(f"Set 'auto_open_pdf' to {new_value}", level='CONFIG')

def restart_application():
    """
    Restarts the entire application.
    """
    debug_console.log("Application restart requested.", level='ACTION')
    if Messagebox.yesno("Are you sure you want to restart?\nUnsaved changes will be lost.", "Restart Application") == "Yes":
        debug_console.log("User confirmed restart. Proceeding...", level='INFO')
        try:
            pass
        finally:
            python_executable = sys.executable
            os.execl(python_executable, python_executable, *sys.argv)
    else:
        debug_console.log("Application restart cancelled by user.", level='INFO')

def go_to_line_in_pdf(event=None):
    """
    Navigate to the selected text in the PDF preview with context matching.
    """
    current_tab = state.get_current_tab()
    if not current_tab or not current_tab.editor:
        debug_console.log("No active editor tab found.", level='WARNING')
        return
        
    # Get selected text
    try:
        selected_text = current_tab.editor.get("sel.first", "sel.last")
        if not selected_text.strip():
            debug_console.log("No text selected.", level='INFO')
            return
    except tk.TclError:
        debug_console.log("No text selected.", level='INFO')
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
        debug_console.log(f"Error getting context: {e}", level='WARNING')
        context_before = ""
        context_after = ""
        
    # Use the PDF preview interface to navigate to the text with context
    if hasattr(state, 'pdf_preview_interface') and state.pdf_preview_interface:
        state.pdf_preview_interface.go_to_text_in_pdf(selected_text, context_before, context_after)
    else:
        debug_console.log("PDF preview interface not available.", level='WARNING')

def apply_theme(theme_name=None, event=None):
    """
    Applies the specified theme to the entire application.
    """
    if theme_name is None:
        theme_name = state.current_theme

    debug_console.log(f"Attempting to apply theme: '{theme_name}'.", level='ACTION')
    
    new_theme, new_settings = interface_theme.apply_theme(
        theme_name, state.root, state.main_pane, state.tabs, perform_heavy_updates, state.console_output,
        state.status_bar_frame, state.status_label, state.gpu_status_label
    )
    state.current_theme = new_theme
    state._theme_settings = new_settings
    
    app_config_data = state.get_app_config()
    app_config_data['theme'] = state.current_theme
    app_config.save_config(app_config_data)

