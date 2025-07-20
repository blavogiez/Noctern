
"""
This module serves as the main interface for the AutomaTeX application, orchestrating
the graphical user interface (GUI) and integrating various functionalities such as
editing, LLM services, LaTeX compilation, and file operations.
It manages the main window, tabbed editor, outline tree, status bar, and handles
user interactions and global application state.
"""

import tkinter as tk
import os
import json
import sys
from tkinter import ttk, messagebox
from app import zoom as interface_zoom
from app import statusbar as interface_statusbar
from app import file_operations as interface_fileops
from app import tab_operations as interface_tabops
from app import theme as interface_theme
from app import config as app_config
from app.topbar import create_top_buttons_frame
from app.panes import create_main_paned_window, create_outline_tree, create_notebook, create_console_pane
from app.status import create_status_bar, start_gpu_status_loop
from app.shortcuts import bind_shortcuts
from editor.tab import EditorTab
from llm import service as llm_service
from editor import logic as editor_logic
from latex import compiler as latex_compiler
from latex import translator as latex_translator
from editor import wordcount as editor_wordcount
from utils import debug_console
from utils import screen as screen_utils
from utils import screen as screen_utils

# --- Global UI Component References ---
# These global variables hold references to key Tkinter widgets and application state,
# allowing different modules to interact with the main GUI components.
root = None  # The main Tkinter application window.
notebook = None  # The ttk.Notebook widget managing editor tabs.
tabs = {}  # A dictionary mapping notebook tab IDs to EditorTab instances.
outline_tree = None  # The ttk.Treeview widget displaying the document outline.
llm_progress_bar = None  # Progress bar for LLM operations.
status_bar_frame = None  # The frame containing status bar elements.
status_label = None  # Label for general application status messages.
gpu_status_label = None  # Label for displaying GPU status.
main_pane = None  # The main paned window separating editor and outline.
vertical_pane = None # The main vertical paned window
console_pane = None # The console pane at the bottom
console_output = None # The text widget for the console output

# --- Theme and Configuration Variables ---
_theme_settings = {}  # Dictionary holding current theme-specific settings.
current_theme = "light"  # Name of the currently active theme.
settings_menu = None  # Reference to the settings menu.
_app_config = {} # Holds user-specific settings from config.json
_auto_open_pdf_var = None # tk.BooleanVar for the auto-open PDF setting

# --- Editor and Performance Constants ---
zoom_factor = 1.1  # Factor by which font size changes during zoom operations.
min_font_size = 8  # Minimum allowed font size in the editor.
max_font_size = 36  # Maximum allowed font size in the editor.
LARGE_FILE_LINE_THRESHOLD = 1000  # Number of lines to consider a file "large".
HEAVY_UPDATE_DELAY_NORMAL = 200  # Delay (ms) for debounced updates in normal files.
HEAVY_UPDATE_DELAY_LARGE_FILE = 2000  # Delay (ms) for debounced updates in large files.
heavy_update_timer_id = None  # ID for the scheduled heavy update callback.

# --- Status Bar and Tab Management Variables ---
_temporary_status_active = False  # Flag indicating if a temporary status message is active.
_temporary_status_timer_id = None  # ID for the temporary status message timer.
_closed_tabs_stack = []  # Stack to store file paths of recently closed tabs for restoration.
_close_button_pressed_on_tab = None  # Tracks which tab's close button was pressed.
SESSION_STATE_FILE = ".session_state.json" # File to store session state

def perform_heavy_updates():
    """
    Executes computationally intensive updates for the active editor tab.

    This function is debounced, meaning it's called after a short delay following
    user input, preventing excessive updates during rapid typing. It updates
    syntax highlighting, the document outline, and word count.
    """
    global heavy_update_timer_id
    heavy_update_timer_id = None  # Reset the timer ID as the update is now running.
    
    current_tab = get_current_tab()
    
    if not current_tab:
        # If no tab is active, clear the outline tree and log the event.
        if outline_tree:
            outline_tree.delete(*outline_tree.get_children())
        debug_console.log("Heavy update skipped: No active editor tab.", level='DEBUG')
        return

    # Log the update for the current tab.
    tab_name = os.path.basename(current_tab.file_path) if current_tab.file_path else "Untitled"
    debug_console.log(f"Initiating heavy updates for tab: '{tab_name}'.", level='INFO')
    
    # Apply syntax highlighting to the editor's content.
    editor_logic.apply_syntax_highlighting(current_tab.editor)
    # Update the document outline tree based on the editor's content.
    editor_logic.update_outline_tree(current_tab.editor)

    # Update word count only if no temporary status message is active.
    if not _temporary_status_active:
        editor_wordcount.update_word_count(current_tab.editor, status_label)

    # Redraw line numbers to ensure they are synchronized with the editor's view.
    if current_tab.line_numbers:
        current_tab.line_numbers.redraw()

def schedule_heavy_updates(_=None):
    """
    Schedules the `perform_heavy_updates` function to run after a delay.

    This function acts as a debouncer. If called multiple times rapidly (e.g., during typing),
    it cancels any previously scheduled updates and schedules a new one, ensuring that
    `perform_heavy_updates` is only called once after a pause in user activity.
    The delay adjusts based on file size.

    Args:
        _ (any, optional): Placeholder for event object, typically not used.
    """
    global heavy_update_timer_id
    # Cancel any pending heavy update tasks.
    if root and heavy_update_timer_id is not None:
        root.after_cancel(heavy_update_timer_id)
    
    current_tab = get_current_tab()
    if root and current_tab:
        current_delay = HEAVY_UPDATE_DELAY_NORMAL
        try:
            # Determine the total number of lines to adjust the update delay for large files.
            last_line_index_str = current_tab.editor.index("end-1c")
            total_lines = 0
            if last_line_index_str:
                total_lines = int(last_line_index_str.split(".")[0])
                # Special case for empty files that might still report 1 line.
                if total_lines == 1 and not current_tab.editor.get("1.0", "1.end").strip():
                    total_lines = 0
            
            # Increase delay for large files to improve responsiveness.
            if total_lines > LARGE_FILE_LINE_THRESHOLD:
                current_delay = HEAVY_UPDATE_DELAY_LARGE_FILE
        except tk.TclError:
            debug_console.log("Error determining total lines for heavy update delay.", level='WARNING')
            pass # Ignore TclError if editor state is inconsistent.
        
        # Schedule the heavy update with the determined delay.
        heavy_update_timer_id = root.after(current_delay, perform_heavy_updates)

def get_theme_setting(key, default=None):
    """
    Retrieves a specific theme setting value by its key.

    Args:
        key (str): The key for the desired theme setting (e.g., "root_bg").
        default (any, optional): The default value to return if the key is not found.

    Returns:
        any: The value associated with the key, or the default value if not found.
    """
    return _theme_settings.get(key, default)

def get_theme_settings():
    """
    Returns the entire dictionary of current theme settings.

    Returns:
        dict: A dictionary containing all theme-specific configuration values.
    """
    return _theme_settings

def get_current_tab():
    """
    Retrieves the currently selected `EditorTab` instance from the notebook.

    Returns:
        EditorTab or None: The active EditorTab instance, or None if no tab is selected or available.
    """
    global notebook, tabs
    if not notebook or not tabs: # Ensure notebook and tabs dictionary are initialized.
        return None
    try:
        selected_tab_id = notebook.select() # Get the ID of the currently selected tab.
        return tabs.get(selected_tab_id) # Return the EditorTab instance associated with the ID.
    except tk.TclError:
        debug_console.log("No tab currently selected in the notebook.", level='DEBUG')
        return None

def paste_image(event=None):
    """
    Triggers the image pasting functionality from the clipboard into the active editor.

    This function acts as a wrapper, calling the `paste_image_from_clipboard` function
    from the `editor_image_paste` module.

    Args:
        event (tk.Event, optional): The Tkinter event object. Defaults to None.
    """
    from editor import image_paste as editor_image_paste # Import locally to avoid circular dependencies if not already imported.
    editor_image_paste.paste_image_from_clipboard(root, get_current_tab, get_theme_setting)

def zoom_in(_=None):
    """
    Increases the font size of the active editor tab, effectively zooming in.

    Args:
        _ (any, optional): Placeholder for event object, typically not used.
    """
    debug_console.log("Zoom In action triggered.", level='ACTION')
    interface_zoom.zoom_in(get_current_tab, perform_heavy_updates, min_font_size, max_font_size, zoom_factor)

def zoom_out(_=None):
    """
    Decreases the font size of the active editor tab, effectively zooming out.

    Args:
        _ (any, optional): Placeholder for event object, typically not used.
    """
    debug_console.log("Zoom Out action triggered.", level='ACTION')
    interface_zoom.zoom_out(get_current_tab, perform_heavy_updates, min_font_size, max_font_size, zoom_factor)

def show_console(content):
    """
    Displays the console pane with the given content.
    """
    global console_pane, console_output, vertical_pane
    if console_pane and console_output:
        # Add the pane back if it's not currently there.
        if str(console_pane) not in vertical_pane.panes():
            vertical_pane.add(console_pane, height=150)

        console_output.config(state="normal")
        console_output.delete("1.0", tk.END)
        console_output.insert("1.0", content)
        console_output.config(state="disabled")

def hide_console():
    """
    Hides the console pane.
    """
    global console_pane, vertical_pane
    if console_pane:
        # Remove the pane if it is currently visible.
        if str(console_pane) in vertical_pane.panes():
            vertical_pane.remove(console_pane)


def show_temporary_status_message(message, duration_ms=2500):
    """
    Displays a temporary message in the status bar for a specified duration.

    Args:
        message (str): The message string to display.
        duration_ms (int, optional): The duration in milliseconds for which the message will be displayed.
                                     Defaults to 2500ms (2.5 seconds).
    """
    global _temporary_status_active, _temporary_status_timer_id
    _temporary_status_active = True # Set flag to indicate temporary message is active.
    interface_statusbar.show_temporary_status_message(
        message, duration_ms, status_label, root, clear_temporary_status_message
    )

def clear_temporary_status_message():
    """
    Clears any active temporary status message and restores the default status (e.g., word count).
    """
    global _temporary_status_active
    _temporary_status_active = False # Reset flag.
    current_tab = get_current_tab()
    if current_tab:
        # Restore word count display if a tab is active.
        editor_wordcount.update_word_count(current_tab.editor, status_label)
    else:
        status_label.config(text="...") # Default status if no tab is active.
    interface_statusbar.clear_temporary_status_message()

def save_session():
    """
    Saves the current session state, specifically the paths of open files.
    """
    open_files = [tab.file_path for tab in tabs.values() if tab.file_path and os.path.exists(tab.file_path)]
    try:
        with open(SESSION_STATE_FILE, "w") as f:
            json.dump({"open_files": open_files}, f)
        debug_console.log(f"Session state saved to {SESSION_STATE_FILE}", level='INFO')
    except Exception as e:
        debug_console.log(f"Error saving session state: {e}", level='ERROR')

def load_session():
    """
    Loads the last session state, reopening previously opened files.
    """
    try:
        if os.path.exists(SESSION_STATE_FILE):
            with open(SESSION_STATE_FILE, "r") as f:
                state = json.load(f)
                open_files = state.get("open_files", [])
                if open_files:
                    for file_path in open_files:
                        if os.path.exists(file_path):
                            create_new_tab(file_path)
                        else:
                            debug_console.log(f"File not found, not reopening: {file_path}", level='WARNING')
                    if not notebook.tabs(): # If all files were not found
                        create_new_tab(None)
                else:
                    create_new_tab(None) # No files in session, open an empty tab
        else:
            create_new_tab(None) # No session file, open an empty tab
    except Exception as e:
        debug_console.log(f"Error loading session state: {e}", level='ERROR')
        create_new_tab(None) # Fallback to an empty tab on error

def on_close_request():
    """
    Handles the application close request, prompting the user to save unsaved changes.

    If there are unsaved changes in any open tabs, a confirmation dialog is displayed.
    The user can choose to save all, discard all, or cancel the close operation.
    """
    global root, tabs
    debug_console.log("Application close request received.", level='INFO')
    if not root:
        return
    
    # Identify all tabs with unsaved changes.
    dirty_tabs = [tab for tab in tabs.values() if tab.is_dirty()]
    if dirty_tabs:
        # Prepare a list of unsaved files for the message box.
        file_list = "\n - ".join([os.path.basename(tab.file_path) if tab.file_path else "Untitled" for tab in dirty_tabs])
        response = messagebox.askyesnocancel("Unsaved Changes", f"You have unsaved changes in the following files:\n - {file_list}\n\nDo you want to save them before closing?", parent=root)
        
        if response is True:
            debug_console.log("User chose to save files before closing.", level='ACTION')
            all_saved = True
            # Iterate through dirty tabs and attempt to save each one.
            for tab in dirty_tabs:
                notebook.select(tab) # Select the tab to ensure it's active for saving.
                if not save_file(): # Call the save_file function.
                    all_saved = False
                    break # Stop if any save operation fails.
            if all_saved:
                save_session()
                root.destroy() # Close the application if all files were saved.
        elif response is False:
            debug_console.log("User chose NOT to save files. Closing application.", level='ACTION')
            save_session()
            root.destroy() # Close the application without saving.
        else:
            debug_console.log("User CANCELLED the close request.", level='ACTION')
            # Do nothing, application remains open.
    else:
        debug_console.log("No unsaved changes. Closing application.", level='INFO')
        save_session()
        root.destroy() # Close the application directly if no unsaved changes.

def close_tab_by_id(tab_id):
    """
    Closes a specific tab identified by its notebook ID.

    This function first selects the target tab and then calls `close_current_tab`
    to handle the actual closing logic, including dirty checks.

    Args:
        tab_id (str): The unique ID of the tab to close within the notebook.
    """
    if tab_id in notebook.tabs():
        notebook.select(tab_id) # Select the tab to make it current.
        close_current_tab() # Call the function to close the currently selected tab.

def close_current_tab(event=None):
    """
    Closes the currently active editor tab.

    This function delegates the actual closing logic to `interface_tabops.close_current_tab`,
    passing necessary callbacks for saving, creating new tabs, and managing the closed tabs stack.

    Args:
        event (tk.Event, optional): The Tkinter event object. Defaults to None.
    """
    return interface_tabops.close_current_tab(get_current_tab, root, notebook, save_file, create_new_tab, tabs, _closed_tabs_stack)

def create_new_tab(file_path=None, event=None):
    """
    Creates and opens a new editor tab in the notebook.

    This function delegates to `interface_tabops.create_new_tab`, providing all necessary
    parameters and callbacks for tab creation, theme application, and event handling.

    Args:
        file_path (str, optional): The path to the file to open in the new tab. Defaults to None for a new untitled tab.
        event (tk.Event, optional): The Tkinter event object. Defaults to None.
    """
    interface_tabops.create_new_tab(
        file_path, notebook, tabs, apply_theme, current_theme, on_tab_changed, EditorTab, schedule_heavy_updates
    )

    if file_path and file_path.endswith(".tex"):
        if _app_config.get('auto_open_pdf', False):
            pdf_path = file_path.replace(".tex", ".pdf")
            if os.path.exists(pdf_path):
                debug_console.log(f"Auto-opening PDF: {pdf_path}", level='INFO')
                latex_compiler.view_pdf_external(pdf_path=pdf_path)
            else:
                debug_console.log(f"Auto-open PDF: Corresponding PDF not found at {pdf_path}", level='DEBUG')

def restore_last_closed_tab(event=None):
    """
    Reopens the most recently closed tab from the `_closed_tabs_stack`.

    If the stack is not empty, it pops the last file path and creates a new tab with it.
    Otherwise, it displays a temporary status message indicating no tabs to restore.

    Args:
        event (tk.Event, optional): The Tkinter event object. Defaults to None.
    """
    if _closed_tabs_stack:
        file_path_to_restore = _closed_tabs_stack.pop() # Get the last closed file path.
        debug_console.log(f"Attempting to restore closed tab: {file_path_to_restore or 'Untitled'}", level='ACTION')
        create_new_tab(file_path=file_path_to_restore) # Create a new tab with the restored file.
    else:
        debug_console.log("No recently closed tabs available for restoration.", level='INFO')
        show_temporary_status_message("ℹ️ No recently closed tabs to restore.")

def open_file(event=None):
    """
    Opens a file dialog to select a file and then opens it in a new editor tab.

    This function delegates to `interface_fileops.open_file`, providing callbacks
    for creating new tabs and showing status messages.

    Args:
        event (tk.Event, optional): The Tkinter event object. Defaults to None.
    """
    return interface_fileops.open_file(create_new_tab, show_temporary_status_message)

def save_file(event=None):
    """
    Saves the content of the current active editor tab.

    Before saving, it checks for any deleted image references within the document
    and prompts the user for associated file deletion. It then delegates the save
    operation to `interface_fileops.save_file`.

    Args:
        event (tk.Event, optional): The Tkinter event object. Defaults to None.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    current_tab = get_current_tab()
    if current_tab:
        # Check for and handle deleted image references before saving.
        editor_logic.check_for_deleted_images(current_tab)
    return interface_fileops.save_file(get_current_tab, show_temporary_status_message, save_file_as)

def save_file_as(event=None):
    """
    Prompts the user to save the current editor content to a new file path.

    Similar to `save_file`, it checks for deleted image references. It then delegates
    the "save as" operation to `interface_fileops.save_file_as`.

    Args:
        event (tk.Event, optional): The Tkinter event object. Defaults to None.

    Returns:
        bool: True if the file was saved successfully, False otherwise.
    """
    current_tab = get_current_tab()
    if current_tab:
        # Check for and handle deleted image references before saving.
        editor_logic.check_for_deleted_images(current_tab)
    return interface_fileops.save_file_as(get_current_tab, show_temporary_status_message, on_tab_changed)

def on_tab_changed(event=None):
    """
    Callback function executed when the active tab in the notebook changes.

    This function ensures that the LLM prompt history and current prompts are loaded
    for the newly active file, and triggers a heavy update for the editor.

    Args:
        event (tk.Event, optional): The Tkinter event object. Defaults to None.
    """
    current_tab = get_current_tab()
    tab_name = os.path.basename(current_tab.file_path) if current_tab and current_tab.file_path else "Untitled"
    debug_console.log(f"Active tab changed to: '{tab_name}'.", level='ACTION')
    
    # Load LLM-related data specific to the newly active file.
    llm_service.load_prompt_history_for_current_file()
    llm_service.load_prompts_for_current_file()
    
    perform_heavy_updates() # Trigger an immediate heavy update for the new tab.



def toggle_auto_open_pdf():
    """
    Callback to update and save the auto-open PDF setting.
    """
    global _app_config
    new_value = _auto_open_pdf_var.get()
    _app_config['auto_open_pdf'] = str(new_value)
    app_config.save_config(_app_config)
    debug_console.log(f"Set 'auto_open_pdf' to {new_value}", level='CONFIG')


def restart_application():
    """
    Restarts the entire application.

    This function prompts the user for confirmation, as all unsaved changes will be lost.
    If confirmed, it re-executes the current Python script, effectively restarting the application.
    """
    debug_console.log("Application restart requested.", level='ACTION')
    if messagebox.askyesno("Restart Application", "Are you sure you want to restart?\nUnsaved changes will be lost.", icon='warning'):
        debug_console.log("User confirmed restart. Proceeding with application restart...", level='INFO')
        try:
            # Perform any necessary cleanup before restarting (e.g., closing files).
            pass
        finally:
            python_executable = sys.executable # Get the path to the Python interpreter.
            # Re-execute the current script using the same Python interpreter and arguments.
            os.execl(python_executable, python_executable, *sys.argv)
    else:
        debug_console.log("Application restart cancelled by user.", level='INFO')

def _configure_notebook_style_and_events():
    """
    Configures a custom `ttk.Notebook` style to include a close button on each tab.

    This involves creating a new style element for the close button and modifying
    the default tab layout to incorporate this element. It also binds mouse events
    to the notebook to detect clicks on these custom close buttons.
    """
    try:
        style = ttk.Style()
        
        # Define a new element 'TNotebook.close' as a label with a close character.
        # This ensures the element is created only once.
        if "TNotebook.close" not in style.element_names():
            style.element_create("TNotebook.close", "label", text=' ✕ ') # '✕' is a multiplication sign, used as a close icon.
            debug_console.log("Created custom TNotebook.close style element.", level='DEBUG')

        # Configure the appearance of the close button element.
        style.configure("TNotebook.close", padding=0, anchor='center')
        
        # Map mouse-over (active) and pressed states to colors for visual feedback.
        # These colors are dynamically set based on the current theme.
        style.map("TNotebook.close",
            foreground=[('active', '#e81123'), ('!active', 'grey')], # Red on hover, grey otherwise.
            background=[('active', get_theme_setting("llm_generated_bg"))]
        )
        
        # Modify the default layout of a notebook tab to include our new 'close' element.
        # This check prevents re-applying the layout if it's already been modified.
        current_layout = style.layout("TNotebook.Tab")
        if "TNotebook.close" not in str(current_layout):
            style.layout("TNotebook.Tab", [
                ('TNotebook.tab', {'sticky': 'nswe', 'children':
                    [('TNotebook.padding', {'side': 'top', 'sticky': 'nswe', 'children':
                        [('TNotebook.focus', {'side': 'top', 'sticky': 'nswe', 'children':
                            [('TNotebook.label', {'side': 'left', 'sticky': ''}),
                             ('TNotebook.close', {'side': 'left', 'sticky': ''})
                            ]
                        })
                        ]
                    })
                    ]
                })
            ])
            debug_console.log("Applied custom notebook tab layout with integrated close button.", level='DEBUG')
    except tk.TclError as e:
        debug_console.log(f"Failed to configure custom notebook style. Error: {e}", level='ERROR')
        return

    # Bind mouse events to the notebook to detect clicks on the custom close button.
    def on_close_button_press(event):
        """
        Handles mouse button press events on the notebook tabs.
        Identifies if the click was on a custom close button and records the tab index.
        """
        global _close_button_pressed_on_tab
        try:
            # Identify the element under the mouse click.
            element = notebook.identify(event.x, event.y)
        except tk.TclError:
            return # Notebook is likely empty or click was outside.
            
        if "close" in element: # Check if the identified element is our custom close button.
            index = notebook.index(f"@{event.x},{event.y}") # Get the index of the tab clicked.
            notebook.state(['pressed']) # Set the notebook state to 'pressed' for visual feedback.
            _close_button_pressed_on_tab = index # Store the index of the tab whose close button was pressed.
            return "break" # Prevent default event handling.

    def on_close_button_release(event):
        """
        Handles mouse button release events on the notebook tabs.
        If a close button was pressed and released over the same button, it closes the tab.
        """
        global _close_button_pressed_on_tab
        if _close_button_pressed_on_tab is None:
            return # No close button was pressed initially.

        try:
            # Re-identify the element and tab index at the release position.
            element = notebook.identify(event.x, event.y)
            index = notebook.index(f"@{event.x},{event.y}")
            # If the release is over the same close button that was pressed, close the tab.
            if "close" in element and _close_button_pressed_on_tab == index:
                tab_id_to_close = notebook.tabs()[index] # Get the actual tab ID.
                # Use a short delay to allow visual feedback before the tab disappears.
                notebook.after(50, lambda: close_tab_by_id(tab_id_to_close))
        except tk.TclError:
            pass # Click was released outside any valid tab area.
        finally:
            notebook.state(["!pressed"]) # Reset notebook state.
            _close_button_pressed_on_tab = None # Clear the stored tab index.

    # Bind the mouse events to the notebook.
    notebook.bind("<ButtonPress-1>", on_close_button_press, True) # True for early binding.
    notebook.bind("<ButtonRelease-1>", on_close_button_release)

def _apply_startup_window_settings(window, config):
    """Applies window geometry and state from config at startup."""
    monitors = screen_utils.get_monitors()
    if not monitors:
        debug_console.log("No monitors detected, using default geometry.", level='WARNING')
        window.geometry("1200x800")
        return

    monitor_name = config.get("app_monitor", "Default")
    selected_monitor = None

    if monitor_name == "Default":
        selected_monitor = next((m for m in monitors if m.is_primary), monitors[0])
    else:
        try:
            # "Monitor 1: 1920x1080" -> index 0
            monitor_index = int(monitor_name.split(':')[0].split(' ')[1]) - 1
            if 0 <= monitor_index < len(monitors):
                selected_monitor = monitors[monitor_index]
            else:
                selected_monitor = monitors[0]
        except (ValueError, IndexError):
            debug_console.log(f"Could not parse monitor name '{monitor_name}'. Falling back to primary.", level='WARNING')
            selected_monitor = next((m for m in monitors if m.is_primary), monitors[0])

    window_state = config.get("window_state", "Normal")

    if window_state == "Maximized":
        # For maximized, move to monitor first, then maximize
        x, y = selected_monitor.x, selected_monitor.y
        window.geometry(f"+{x}+{y}")
        window.state('zoomed')
    elif window_state == "Fullscreen":
        x, y = selected_monitor.x, selected_monitor.y
        window.geometry(f"+{x}+{y}")
        window.attributes("-fullscreen", True)
    else: # Normal
        # Center the window on the selected monitor
        width, height = 1200, 800
        x = selected_monitor.x + (selected_monitor.width - width) // 2
        y = selected_monitor.y + (selected_monitor.height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

def setup_gui():
    """
    Initializes and sets up the main graphical user interface (GUI) of the application.

    This function creates the main Tkinter window, sets up its title and geometry,
    initializes various UI components (top bar, paned window, outline tree, notebook,
    status bar), applies initial theme settings, and binds global shortcuts.

    Returns:
        tk.Tk: The root Tkinter window of the application.
    """
    global root, notebook, outline_tree, llm_progress_bar, _theme_settings, status_bar_frame
    global status_label, gpu_status_label, main_pane, settings_menu
    global vertical_pane, console_pane, console_output, _app_config, _auto_open_pdf_var

    _app_config = app_config.load_config()

    root = tk.Tk() # Create the main application window.
    root.title("AutomaTeX v1.0") # Set the window title.
    _apply_startup_window_settings(root, _app_config)
    debug_console.log("GUI initialization process started.", level='INFO')

    _auto_open_pdf_var = tk.BooleanVar(value=app_config.get_bool(_app_config.get('auto_open_pdf', 'False')))
    debug_console.initialize(root) # Initialize the debug console with the root window.

    # Create the top buttons frame and retrieve the settings menu.
    top_frame, settings_menu = create_top_buttons_frame(root)

    # Create the main vertical paned window
    vertical_pane = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.FLAT, sashwidth=6)
    vertical_pane.pack(fill="both", expand=True)

    # Create the main horizontal paned window for layout management.
    main_pane = create_main_paned_window(vertical_pane)
    
    # Create the outline tree widget and link it to the main pane.
    outline_tree = create_outline_tree(main_pane, get_current_tab)
    
    # Create the notebook (tabbed editor area) and link it to the main pane.
    notebook = create_notebook(main_pane)
    
    # Add main_pane to the vertical_pane
    vertical_pane.add(main_pane, stretch="always")

    # Create the console pane
    console_frame, console_output = create_console_pane(vertical_pane)
    console_pane = console_frame
    vertical_pane.add(console_pane)
    hide_console() # Initially hidden

    # Bind the tab change event to the on_tab_changed callback.
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    # Create the LLM progress bar (initially indeterminate).
    llm_progress_bar = ttk.Progressbar(root, mode="indeterminate", length=200)
    
    # Create the status bar and retrieve its labels.
    status_bar_frame, status_label, gpu_status_label = create_status_bar(root)
    # Start the loop for updating GPU status.
    start_gpu_status_loop(gpu_status_label, root)
    
    bind_shortcuts(root) # Bind global keyboard shortcuts.
    
    load_session() # Load the previous session or create a new tab.
    
    # Set the protocol for handling the window close button.
    root.protocol("WM_DELETE_WINDOW", on_close_request)
    
    debug_console.log("GUI setup completed successfully.", level='SUCCESS')
    
    return root

def apply_theme(theme_name, event=None):
    """
    Applies the specified theme to the entire application.

    This function updates the application's visual style, including colors and
    widget appearances, by delegating to `interface_theme.apply_theme` and then
    re-configuring the custom notebook tab style.

    Args:
        theme_name (str): The name of the theme to apply (e.g., "light", "dark").
        event (tk.Event, optional): The Tkinter event object. Defaults to None.
    """
    global current_theme, _theme_settings
    debug_console.log(f"Attempting to apply theme: '{theme_name}'.", level='ACTION')
    # Apply the base theme using the interface_theme module and get new settings.
    new_theme, new_settings = interface_theme.apply_theme(
        theme_name, root, main_pane, tabs, perform_heavy_updates
    )
    current_theme = new_theme # Update the global current theme.
    _theme_settings = new_settings # Update the global theme settings.
    
    # Re-apply our custom notebook style modifications to ensure they are consistent
    # with the newly applied theme.
    _configure_notebook_style_and_events()
