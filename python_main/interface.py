# interface.py

import tkinter as tk
from tkinter import ttk, messagebox
import interface_zoom
import interface_statusbar
import interface_fileops
import interface_tabops
import interface_theme
from interface_topbar import create_top_buttons_frame
from interface_panes import create_main_paned_window, create_outline_tree, create_notebook
from interface_status import create_status_bar, start_gpu_status_loop
from interface_shortcuts import bind_shortcuts
from editor_tab import EditorTab
import llm_service
import editor_logic
import latex_compiler
import latex_translator
import editor_wordcount
import os
import sys
import debug_console

# ... (global variables remain unchanged) ...
root = None
notebook = None
tabs = {}
outline_tree = None
llm_progress_bar = None
status_bar_frame = None
status_label = None
gpu_status_label = None
main_pane = None
_theme_settings = {}
current_theme = "light"
settings_menu = None
_advanced_mode_enabled = None
zoom_factor = 1.1
min_font_size = 8
max_font_size = 36
LARGE_FILE_LINE_THRESHOLD = 1000
HEAVY_UPDATE_DELAY_NORMAL = 200
HEAVY_UPDATE_DELAY_LARGE_FILE = 2000
heavy_update_timer_id = None
_temporary_status_active = False
_temporary_status_timer_id = None
_closed_tabs_stack = []
_close_button_pressed_on_tab = None

def perform_heavy_updates():
    """
    Performs updates that might be computationally heavy. This function is debounced.
    """
    global heavy_update_timer_id
    heavy_update_timer_id = None
    
    current_tab = get_current_tab()
    
    if not current_tab:
        if outline_tree:
            outline_tree.delete(*outline_tree.get_children())
        debug_console.log("Heavy update aborted, no active tab.", level='DEBUG')
        return

    tab_name = os.path.basename(current_tab.file_path) if current_tab.file_path else "Untitled"
    debug_console.log(f"Performing heavy updates for tab '{tab_name}'.", level='INFO')
    
    editor_logic.apply_syntax_highlighting(current_tab.editor)
    editor_logic.update_outline_tree(current_tab.editor)

    if not _temporary_status_active:
        editor_wordcount.update_word_count(current_tab.editor, status_label)

    if current_tab.line_numbers:
        current_tab.line_numbers.redraw()

def schedule_heavy_updates(_=None):
    """
    Schedules heavy updates after a short delay. This acts as a debouncer.
    """
    global heavy_update_timer_id
    if root and heavy_update_timer_id is not None:
        root.after_cancel(heavy_update_timer_id)
    
    current_tab = get_current_tab()
    if root and current_tab:
        current_delay = HEAVY_UPDATE_DELAY_NORMAL
        try:
            last_line_index_str = current_tab.editor.index("end-1c")
            total_lines = 0
            if last_line_index_str:
                total_lines = int(last_line_index_str.split(".")[0])
                if total_lines == 1 and not current_tab.editor.get("1.0", "1.end").strip():
                    total_lines = 0
            
            if total_lines > LARGE_FILE_LINE_THRESHOLD:
                current_delay = HEAVY_UPDATE_DELAY_LARGE_FILE
        except tk.TclError:
            pass
        
        heavy_update_timer_id = root.after(current_delay, perform_heavy_updates)

def get_theme_setting(key, default=None):
    """Returns a single value for a given theme key."""
    return _theme_settings.get(key, default)

def get_theme_settings():
    """Returns the entire dictionary of current theme settings."""
    return _theme_settings

def get_current_tab():
    global notebook, tabs
    if not notebook or not tabs:
        return None
    try:
        selected_tab_id = notebook.select()
        return tabs.get(selected_tab_id)
    except tk.TclError:
        return None

def paste_image(event=None):
    import editor_image_paste
    editor_image_paste.paste_image_from_clipboard()

def zoom_in(_=None):
    debug_console.log("Zoom In triggered.", level='ACTION')
    return interface_zoom.zoom_in(get_current_tab, perform_heavy_updates, min_font_size, max_font_size, zoom_factor)

def zoom_out(_=None):
    debug_console.log("Zoom Out triggered.", level='ACTION')
    return interface_zoom.zoom_out(get_current_tab, perform_heavy_updates, min_font_size, max_font_size, zoom_factor)

def show_temporary_status_message(message, duration_ms=2500):
    global _temporary_status_active, _temporary_status_timer_id
    _temporary_status_active = True
    return interface_statusbar.show_temporary_status_message(
        message, duration_ms, status_label, root, clear_temporary_status_message
    )

def clear_temporary_status_message():
    global _temporary_status_active
    _temporary_status_active = False
    current_tab = get_current_tab()
    if current_tab:
        editor_wordcount.update_word_count(current_tab.editor, status_label)
    else:
        status_label.config(text="...")
    return interface_statusbar.clear_temporary_status_message()


def on_close_request():
    global root, tabs
    debug_console.log("Application close request received.", level='INFO')
    if not root:
        return
    
    dirty_tabs = [tab for tab in tabs.values() if tab.is_dirty()]
    if dirty_tabs:
        file_list = "\n - ".join([os.path.basename(tab.file_path) if tab.file_path else "Untitled" for tab in dirty_tabs])
        response = messagebox.askyesnocancel("Unsaved Changes", f"You have unsaved changes in the following files:\n - {file_list}\n\nDo you want to save them before closing?", parent=root)
        
        if response is True:
            debug_console.log("User chose to SAVE files before closing.", level='ACTION')
            all_saved = True
            for tab in dirty_tabs:
                notebook.select(tab)
                if not save_file():
                    all_saved = False
                    break
            if all_saved:
                root.destroy()
        elif response is False:
            debug_console.log("User chose NOT to save files. Closing.", level='ACTION')
            root.destroy()
        else:
            debug_console.log("User CANCELLED the close request.", level='ACTION')
    else:
        debug_console.log("No dirty tabs. Closing application.", level='INFO')
        root.destroy()

def close_tab_by_id(tab_id):
    """Closes a specific tab by its ID, selecting it first."""
    if tab_id in notebook.tabs():
        notebook.select(tab_id)
        close_current_tab()

def close_current_tab(event=None):
    return interface_tabops.close_current_tab(get_current_tab, root, notebook, save_file, create_new_tab, tabs, _closed_tabs_stack)

def create_new_tab(file_path=None, event=None):
    interface_tabops.create_new_tab(
        file_path, notebook, tabs, apply_theme, current_theme, on_tab_changed, EditorTab, schedule_heavy_updates
    )

def restore_last_closed_tab(event=None):
    """Reopens the most recently closed tab."""
    if _closed_tabs_stack:
        file_path_to_restore = _closed_tabs_stack.pop()
        debug_console.log(f"Restoring closed tab: {file_path_to_restore or 'Untitled'}", level='ACTION')
        create_new_tab(file_path=file_path_to_restore)
    else:
        debug_console.log("No tabs in restore stack.", level='INFO')
        show_temporary_status_message("ℹ️ No recently closed tabs to restore.")

def open_file(event=None):
    return interface_fileops.open_file(create_new_tab, show_temporary_status_message)

def save_file(event=None):
    current_tab = get_current_tab()
    if current_tab:
        editor_logic.check_for_deleted_images(current_tab)
    return interface_fileops.save_file(get_current_tab, show_temporary_status_message, save_file_as)

def save_file_as(event=None):
    current_tab = get_current_tab()
    if current_tab:
        editor_logic.check_for_deleted_images(current_tab)
    return interface_fileops.save_file_as(get_current_tab, show_temporary_status_message, on_tab_changed)

def on_tab_changed(event=None):
    current_tab = get_current_tab()
    tab_name = os.path.basename(current_tab.file_path) if current_tab and current_tab.file_path else "Untitled"
    debug_console.log(f"Tab changed to '{tab_name}'.", level='ACTION')
    
    llm_service.load_prompt_history_for_current_file()
    llm_service.load_prompts_for_current_file()
    
    perform_heavy_updates()

def toggle_advanced_mode():
    global settings_menu
    if not settings_menu:
        return
    
    is_advanced = _advanced_mode_enabled.get()
    settings_menu.entryconfig("Show Debug Console", state="normal" if is_advanced else "disabled")
    settings_menu.entryconfig("Restart Application", state="normal" if is_advanced else "disabled")
    
    if is_advanced:
        debug_console.log("Advanced mode ENABLED.", level='CONFIG')
    else:
        debug_console.hide_console()
        debug_console.log("Advanced mode DISABLED.", level='CONFIG')

def restart_application():
    """Restarts the current program, losing all unsaved changes."""
    debug_console.log("Restart application triggered.", level='ACTION')
    if messagebox.askyesno("Restart Application", "Are you sure you want to restart?\nUnsaved changes will be lost.", icon='warning'):
        debug_console.log("User confirmed restart. Restarting...", level='INFO')
        try:
            # Clean up before restart if needed (e.g., closing files, sockets)
            pass
        finally:
            python = sys.executable
            os.execl(python, python, *sys.argv)
    else:
        debug_console.log("User cancelled restart.", level='ACTION')

def _configure_notebook_style_and_events():
    """Sets up a custom ttk style for notebook tabs to include a close button."""
    try:
        style = ttk.Style()
        
        # Define a new element 'TNotebook.close' as a label with a close character.
        # This only needs to be done once.
        if "TNotebook.close" not in style.element_names():
            style.element_create("TNotebook.close", "label", text=' ✕ ') # Padded for better clicking
            debug_console.log("Created TNotebook.close style element.", level='DEBUG')

        # Configure the element's appearance.
        style.configure("TNotebook.close", padding=0, anchor='center')
        
        # Map mouse-over (active) and pressed states to colors to simulate a button.
        # This is safe to call multiple times, so we do it in apply_theme.
        style.map("TNotebook.close",
            foreground=[('active', '#e81123'), ('!active', 'grey')],
            background=[('active', get_theme_setting("llm_generated_bg"))]
        )
        
        # Get the current layout of a tab and insert our new 'close' element.
        # This is the most fragile part, so we check if we've already done it.
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
            debug_console.log("Applied custom notebook tab layout with close button.", level='DEBUG')
    except tk.TclError as e:
        debug_console.log(f"Could not create custom notebook style. Error: {e}", level='WARNING')
        return

    # Bind mouse events to the notebook to detect clicks on our custom 'close' element.
    def on_close_press(event):
        global _close_button_pressed_on_tab
        try:
            element = notebook.identify(event.x, event.y)
        except tk.TclError:
            return # Notebook is likely empty
            
        if "close" in element:
            index = notebook.index(f"@{event.x},{event.y}")
            notebook.state(['pressed'])
            _close_button_pressed_on_tab = index
            return "break"

    def on_close_release(event):
        global _close_button_pressed_on_tab
        if _close_button_pressed_on_tab is None:
            return

        try:
            # Check if release is still over the close button of the same tab
            element = notebook.identify(event.x, event.y)
            index = notebook.index(f"@{event.x},{event.y}")
            if "close" in element and _close_button_pressed_on_tab == index:
                tab_id_to_close = notebook.tabs()[index]
                # Use a short delay to allow visual feedback to register before the tab disappears
                notebook.after(50, lambda: close_tab_by_id(tab_id_to_close))
        except tk.TclError:
            pass # Click was released outside any tab
        finally:
            notebook.state(["!pressed"])
            _close_button_pressed_on_tab = None

    notebook.bind("<ButtonPress-1>", on_close_press, True)
    notebook.bind("<ButtonRelease-1>", on_close_release)

def setup_gui():
    global root, notebook, outline_tree, llm_progress_bar, _theme_settings, status_bar_frame
    global status_label, gpu_status_label, main_pane, settings_menu, _advanced_mode_enabled

    root = tk.Tk()
    root.title("AutomaTeX v1.0")
    root.geometry("1200x800")
    debug_console.log("GUI setup started.", level='INFO')

    _advanced_mode_enabled = tk.BooleanVar(value=False)
    debug_console.initialize(root)

    top_frame, settings_menu = create_top_buttons_frame(root)

    main_pane = create_main_paned_window(root)
    outline_tree = create_outline_tree(main_pane, get_current_tab)
    notebook = create_notebook(main_pane)
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    llm_progress_bar = ttk.Progressbar(root, mode="indeterminate", length=200)
    
    status_bar_frame, status_label, gpu_status_label = create_status_bar(root)
    start_gpu_status_loop(gpu_status_label, root)
    
    bind_shortcuts(root)
    
    create_new_tab(None)
    
    root.protocol("WM_DELETE_WINDOW", on_close_request)
    
    toggle_advanced_mode()
    debug_console.log("GUI setup complete.", level='SUCCESS')
    
    return root

def apply_theme(theme_name, event=None):
    global current_theme, _theme_settings
    debug_console.log(f"Applying theme '{theme_name}'.", level='ACTION')
    # Apply the base theme from sv_ttk and our custom colors
    new_theme, new_settings = interface_theme.apply_theme(
        theme_name, root, main_pane, tabs, perform_heavy_updates
    )
    current_theme = new_theme
    _theme_settings = new_settings
    
    # Re-apply our custom notebook style modifications on top of the new theme
    _configure_notebook_style_and_events()