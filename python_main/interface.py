import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.font import Font
import os
import subprocess
import platform
import datetime # NEW: Import datetime for timestamps
import sv_ttk # Import sv_ttk

# Import functions from other modules
import editor_logic
import latex_compiler
import llm_service # MODIFIED: Import new llm_service
import latex_translator # NEW: Import latex_translator
from editor_tab import EditorTab # NEW: Import the EditorTab class

# Global variables for main widgets and state
# These are initialized in setup_gui and accessed by other modules
root = None
notebook = None # NEW: Replaces the single editor
tabs = {} # NEW: Dictionary to hold EditorTab instances, mapping tab_id to tab_object
outline_tree = None
llm_progress_bar = None
status_bar = None
main_pane = None
_theme_settings = {} # Store current theme colors and properties
current_theme = "light" # Initial theme state, ensure it matches main.py if it sets it first

# Zoom settings
zoom_factor = 1.1
min_font_size = 8
max_font_size = 36

# --- Configuration for Heavy Updates ---
# Threshold for considering a file "large" (in number of lines)
LARGE_FILE_LINE_THRESHOLD = 1000
HEAVY_UPDATE_DELAY_NORMAL = 200  # milliseconds
HEAVY_UPDATE_DELAY_LARGE_FILE = 2000  # milliseconds for large files
heavy_update_timer_id = None

# Status bar temporary message state
_temporary_status_active = False
_temporary_status_timer_id = None

def perform_heavy_updates():
    """Performs updates that might be computationally heavy."""
    global heavy_update_timer_id
    heavy_update_timer_id = None  # Reset timer ID
    
    current_tab = get_current_tab()
    
    # If there is no active tab, clear the outline and stop.
    if not current_tab:
        if outline_tree:
            outline_tree.delete(*outline_tree.get_children())
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Heavy updates skipped (no active tab).")
        return

    # Perform all updates for the current tab
    editor_logic.apply_syntax_highlighting(current_tab.editor)
    editor_logic.update_outline_tree(current_tab.editor)
    if current_tab.line_numbers:
        current_tab.line_numbers.redraw()
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Performed heavy updates (syntax highlighting, outline, line numbers) for '{os.path.basename(current_tab.file_path) if current_tab.file_path else 'Untitled'}'.")
def schedule_heavy_updates(_=None):
    """Schedules heavy updates after a short delay."""
    global heavy_update_timer_id
    if root and heavy_update_timer_id is not None:
        root.after_cancel(heavy_update_timer_id)
    current_tab = get_current_tab()
    if root and current_tab: # Ensure root and a tab are available
        current_delay = HEAVY_UPDATE_DELAY_NORMAL
        try:
            # Get total lines to determine if the file is large
            last_line_index_str = current_tab.editor.index("end-1c")
            # Correctly get total_lines, handling empty editor
            total_lines = 0
            if last_line_index_str: # Ensure index is not None or empty
                total_lines = int(last_line_index_str.split(".")[0])
                if total_lines == 1 and not current_tab.editor.get("1.0", "1.end").strip(): # Check if line 1 is empty
                    total_lines = 0
            
            if total_lines > LARGE_FILE_LINE_THRESHOLD:
                current_delay = HEAVY_UPDATE_DELAY_LARGE_FILE
        except tk.TclError: # Handle cases where editor might not be ready
            pass # Use normal delay
        heavy_update_timer_id = root.after(current_delay, perform_heavy_updates)

def get_theme_setting(key, default=None):
    """Gets a value from the current theme settings."""
    return _theme_settings.get(key, default)

def get_current_tab():
    """Returns the currently active EditorTab object, or None."""
    global notebook, tabs
    if not notebook or not tabs:
        return None
    try:
        selected_tab_id = notebook.select()
        return tabs.get(selected_tab_id)
    except tk.TclError: # Happens if no tabs are present
        return None

## -- Zoom Functionality -- ##

def zoom_in(_=None): # Accept optional event argument
    """Increases the editor font size."""
    current_tab = get_current_tab()
    if not current_tab:
        return

    current_size = current_tab.editor_font.cget("size")
    new_size = int(current_size * zoom_factor)
    new_size = min(new_size, max_font_size)

    if new_size != current_size:
        current_tab.editor_font = Font(family=current_tab.editor_font.cget("family"), size=new_size, weight=current_tab.editor_font.cget("weight"), slant=current_tab.editor_font.cget("slant"))
        current_tab.editor.config(font=current_tab.editor_font)
        if current_tab.line_numbers:
            current_tab.line_numbers.font = current_tab.editor_font # Update the font reference
            current_tab.line_numbers.redraw()
        perform_heavy_updates() # Reapply syntax highlighting and outline

def zoom_out(_=None): # Accept optional event argument
    """Decreases the editor font size."""
    current_tab = get_current_tab()
    if not current_tab:
        return

    current_size = current_tab.editor_font.cget("size")
    new_size = int(current_size / zoom_factor)
    new_size = max(new_size, min_font_size)

    if new_size != current_size:
        current_tab.editor_font = Font(family=current_tab.editor_font.cget("family"), size=new_size, weight=current_tab.editor_font.cget("weight"), slant=current_tab.editor_font.cget("slant"))
        current_tab.editor.config(font=current_tab.editor_font)
        if current_tab.line_numbers:
            current_tab.line_numbers.font = current_tab.editor_font # Update the font reference
            current_tab.line_numbers.redraw()
        perform_heavy_updates() # Reapply syntax highlighting and outline

## -- Status Bar Feedback -- ##

def show_temporary_status_message(message, duration_ms=2500):
    """Displays a temporary message on the status bar."""
    global _temporary_status_active, _temporary_status_timer_id, status_bar, root

    if not status_bar or not root:
        return

    # Cancel any existing temporary message timer
    if _temporary_status_timer_id:
        root.after_cancel(_temporary_status_timer_id)

    _temporary_status_active = True  # Set flag to indicate temporary message is active
    status_bar.config(text=message)  # Display the temporary message

    # Schedule the message to be cleared
    _temporary_status_timer_id = root.after(duration_ms, clear_temporary_status_message)

def clear_temporary_status_message():
    """Clears the temporary message and restores the normal status bar content."""
    global _temporary_status_active, _temporary_status_timer_id, status_bar
    _temporary_status_active = False # Clear the flag
    _temporary_status_timer_id = None # Reset timer ID
    if status_bar:
        update_gpu_status() # Immediately refresh with GPU status or default
        # Also re-apply the current theme colors to ensure temporary colors are removed
        apply_theme(current_theme)

def on_close_request():
    """Handles closing the main window, checking for unsaved changes."""
    global root, tabs

    if not root:
        root.destroy()
        return

    dirty_tabs = [tab for tab in tabs.values() if tab.is_dirty()]

    if dirty_tabs:
        file_list = "\n - ".join([os.path.basename(tab.file_path) if tab.file_path else "Untitled" for tab in dirty_tabs])
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            f"You have unsaved changes in the following files:\n - {file_list}\n\nDo you want to save them before closing?",
            parent=root
        )
        if response is True:  # Yes, save and close
            all_saved = True
            for tab in dirty_tabs:
                # Switch to the tab to save it
                notebook.select(tab)
                if not save_file(): # save_file will handle the current tab
                    all_saved = False
                    break # User cancelled a "Save As" dialog
            if all_saved:
                root.destroy() # Close if all saves were successful
        elif response is False:  # No, just close
            root.destroy()
        # else: Cancel, do nothing and the window stays open.
    else:
        # No unsaved changes, just close.
        root.destroy()

def close_current_tab():
    """Closes the currently active tab."""
    current_tab = get_current_tab()
    if not current_tab:
        return

    if current_tab.is_dirty():
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            f"The file '{os.path.basename(current_tab.file_path) if current_tab.file_path else 'Untitled'}' has unsaved changes. Do you want to save before closing it?",
            parent=root
        )
        if response is True: # Yes
            if not save_file():
                return # User cancelled save, so don't close tab
        elif response is None: # Cancel
            return

    tab_id = notebook.select()
    notebook.forget(tab_id)
    del tabs[tab_id]

    if not tabs: # If no tabs are left, create a new empty one
        create_new_tab()

## -- File Operations -- ##

def create_new_tab(file_path=None):
    """Creates a new EditorTab, adds it to the notebook, and selects it."""
    global notebook, tabs
    
    # Check if file is already open
    if file_path:
        for tab in tabs.values():
            if tab.file_path == file_path:
                notebook.select(tab)
                return

    new_tab = EditorTab(notebook, file_path=file_path, schedule_heavy_updates_callback=schedule_heavy_updates)
    
    notebook.add(new_tab, text=os.path.basename(file_path) if file_path else "Untitled")
    notebook.select(new_tab) # Make the new tab active
    
    # Store the tab object using its widget ID as the key
    tabs[str(new_tab)] = new_tab
    
    # Apply the current theme to the new tab's widgets
    apply_theme(current_theme)
    
    # Trigger updates for the new tab
    on_tab_changed()

    # Now that the tab is added to the notebook, load its content
    new_tab.load_file()

def open_file():
    """Opens a file and loads its content into the editor."""
    filepath = filedialog.askopenfilename(
        title="Open File",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filepath:
        create_new_tab(file_path=filepath)
        show_temporary_status_message(f"✅ Opened: {os.path.basename(filepath)}")

def save_file():
    """Saves the current editor content to the current file or a new file."""
    current_tab = get_current_tab()
    if not current_tab:
        return False

    if current_tab.file_path:
        if current_tab.save_file():
            show_temporary_status_message(f"✅ Saved: {os.path.basename(current_tab.file_path)}")
            return True
        return False
    else:
        return save_file_as()

def save_file_as():
    """Saves the current tab to a new file path."""
    current_tab = get_current_tab()
    if not current_tab:
        return False

    new_filepath = filedialog.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        title="Save File As"
    )
    if new_filepath:
        if current_tab.save_file(new_path=new_filepath):
            show_temporary_status_message(f"✅ Saved as: {os.path.basename(new_filepath)}")
            # Update services that depend on file path
            on_tab_changed()
            return True
    return False

def on_tab_changed(event=None):
    """Handles logic when the active tab changes."""
    # Load prompt history and custom prompts for the newly active file
    llm_service.load_prompt_history_for_current_file()
    llm_service.load_prompts_for_current_file()
    # Update outline, syntax highlighting, etc.
    perform_heavy_updates()

def setup_gui():
    """Sets up the main application window and widgets."""
    global root, notebook, outline_tree, llm_progress_bar, _theme_settings, status_bar, main_pane

    root = tk.Tk()
    root.title("AutomaTeX v1.0")
    root.geometry("1200x800") # Adjusted default size
    # Initial background will be set by apply_theme
    # root.iconbitmap("res/automatex.ico") # Ensure icon file exists
    
    # sv_ttk.set_theme("light") # Or "dark", will be set by apply_theme
    # No need for manual ttk.Style() or theme_use("clam") initially, sv_ttk handles it.

    # --- Top Buttons Frame ---
    top_frame = ttk.Frame(root, padding=10) # Increased padding
    top_frame.pack(fill="x", pady=(0, 5)) # Add some pady below top_frame

    # File buttons
    ttk.Button(top_frame, text="📂 Open", command=open_file).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="💾 Save", command=save_file).pack(side="left", padx=3, pady=3) # Shorter text
    ttk.Button(top_frame, text="💾 Save As", command=save_file_as).pack(side="left", padx=3, pady=3) # Shorter text

    # LaTeX buttons
    ttk.Button(top_frame, text="🛠 Compile", command=latex_compiler.compile_latex).pack(side="left", padx=3, pady=3) # Shorter text
    ttk.Button(top_frame, text="🔍 Check", command=latex_compiler.run_chktex_check).pack(side="left", padx=3, pady=3) # Shorter text

    # LLM buttons - MODIFIED to call llm_service functions
    ttk.Button(top_frame, text="✨ Complete", command=llm_service.request_llm_to_complete_text).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🎯 Generate", command=llm_service.open_generate_text_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🔑 Keywords", command=llm_service.open_set_keywords_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="📝 Prompts", command=llm_service.open_edit_prompts_dialog).pack(side="left", padx=3, pady=3) # Shorter text
    ttk.Button(top_frame, text="🌐 Translate", command=latex_translator.open_translate_dialog).pack(side="left", padx=3, pady=3) # NEW: Translate button

    # Theme button
    # Use a lambda to toggle between themes
    ttk.Button(top_frame, text="🌓 Theme", command=lambda: apply_theme("dark" if current_theme == "light" else "light")).pack(side="right", padx=3, pady=3)

    # --- Main Paned Window (Outline Tree + Editor) ---
    # PanedWindow allows resizing the panes by dragging the sash
    main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6) # Modern sash
    main_pane.pack(fill="both", expand=True)

    # --- Left Outline Tree Frame ---
    outline_frame = ttk.Frame(main_pane) # No specific padding here, let Treeview fill
    # Treeview to display document outline
    outline_tree = ttk.Treeview(outline_frame, show="tree")
    outline_tree.pack(fill="both", expand=True)
    # Bind selection event to go_to_section function
    outline_tree.bind("<<TreeviewSelect>>", lambda event: editor_logic.go_to_section(get_current_tab().editor if get_current_tab() else None, event))
    # Add the outline frame to the main pane
    main_pane.add(outline_frame, width=250, minsize=150) # Added minsize

    # --- Editor Notebook ---
    notebook_frame = ttk.Frame(main_pane) # A frame to hold the notebook
    notebook = ttk.Notebook(notebook_frame)
    notebook.pack(fill="both", expand=True)
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    # Add the notebook frame to the main pane
    main_pane.add(notebook_frame, stretch="always", minsize=400)

    # --- LLM Progress Bar ---
    llm_progress_bar = ttk.Progressbar(root, mode="indeterminate", length=200)
    # Packing is handled by llm_logic functions when it's shown/hidden

    # --- Status Bar (for GPU info) ---
    status_bar = ttk.Label(root, text="⏳ Initializing...", anchor="w", relief=tk.FLAT, padding=(5, 3)) # Modern flat look
    status_bar.pack(side="bottom", fill="x")

    # Function to update GPU status (runs in a loop)
    def update_gpu_status():
        try:
            # If a temporary message is active, don't overwrite it with GPU status
            if _temporary_status_active:
                root.after(300, update_gpu_status) # Reschedule and check again
                return
            # Command to get GPU info (works on systems with nvidia-smi)
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
                encoding="utf-8"
            ).strip()

            name, temp, usage = output.split(", ")
            status_text = f"🎮 GPU: {name}   🌡 {temp}°C   📊 {usage}% used"
        except Exception as e:
            # If GPU status fails or temporary message was just cleared,
            # ensure status_bar is not None before configuring.
            if status_bar:
                if isinstance(e, (FileNotFoundError, subprocess.CalledProcessError)):
                    status_bar.config(text="⚠️ GPU status not available (nvidia-smi error)")
                else:
                    status_bar.config(text=f"⚠️ Error getting GPU status")
            # Still schedule next update even if this one failed
            root.after(300, update_gpu_status)
            return
        if status_bar and not _temporary_status_active: # Check again before setting
            status_bar.config(text=status_text)
        # Schedule the next update
        root.after(300, update_gpu_status) # Update every 0.3 seconds

    # Start the GPU status update loop
    update_gpu_status()

    # --- Bind Keyboard Shortcuts ---
    # Bindings are on the root window to work application-wide
    root.bind_all("<Control-Shift-G>", lambda event: llm_service.open_generate_text_dialog()) # MODIFIED
    root.bind_all("<Control-Shift-C>", lambda event: llm_service.request_llm_to_complete_text()) # MODIFIED
    root.bind_all("<Control-Shift-D>", lambda event: latex_compiler.run_chktex_check())
    root.bind_all("<Control-Shift-V>", lambda event: editor_logic.paste_image())
    root.bind_all("<Control-Shift-K>", lambda event: llm_service.open_set_keywords_dialog()) # MODIFIED: Shortcut for keywords
    root.bind_all("<Control-Shift-P>", lambda event: llm_service.open_edit_prompts_dialog()) # Shortcut for editing prompts
    root.bind_all("<Control-o>", lambda event: open_file())
    root.bind_all("<Control-s>", lambda event: save_file())
    root.bind_all("<Control-w>", lambda event: close_current_tab()) # Shortcut to close tab

    root.bind_all("<Control-t>", lambda event: latex_translator.open_translate_dialog()) # NEW: Shortcut for translate

    # Bind Zoom shortcuts
    root.bind_all("<Control-equal>", zoom_in) # Ctrl+= is common for zoom in
    root.bind_all("<Control-minus>", zoom_out)

    # Create the first empty tab to start with
    create_new_tab()

    # --- Initialize Global References in Other Modules ---
    # NOTE: Service initializations (LLM, Translator) are now handled in main.py after the GUI is fully set up.

    # Intercept the window close ('X') button to check for unsaved changes
    root.protocol("WM_DELETE_WINDOW", on_close_request)
    return root

def apply_theme(theme_name):
    """Applies the specified theme (light or dark) to the GUI."""
    global current_theme, _theme_settings, root, outline_tree, status_bar, main_pane, tabs

    if not root: # Guard against calling too early
        return

    # Set the theme using sv_ttk
    sv_ttk.set_theme(theme_name)
    current_theme = theme_name

    # Font for non-ttk widgets (like tk.Text in dialogs if not using editor_font)
    # sv_ttk will handle fonts for ttk widgets.
    ui_font_family = "Segoe UI" if platform.system() == "Windows" else "Helvetica"
    ui_font_button = Font(family=ui_font_family, size=9, weight="normal")

    # Define colors based on theme
    if theme_name == "light":
        _theme_settings = {
            # sv_ttk typically uses a very light grey or white for root_bg in light mode
            "root_bg": "#fdfdfd", # Adjusted to match typical sv_ttk light theme
            "fg_color": "#000000", # General foreground for non-ttk elements
            "sel_bg": "#0078d4", "sel_fg": "#ffffff", # Selection colors for editor (inspired by Windows)
            "editor_bg": "#ffffff", "editor_fg": "#1e1e1e", "editor_insert_bg": "#333333",
            "comment_color": "#008000", "command_color": "#0000ff", "brace_color": "#ff007f",
            "ln_text_color": "#888888", "ln_bg_color": "#f7f7f7",
            "panedwindow_sash": "#e6e6e6", # Light sash for PanedWindow if sv_ttk doesn't fully style it
            # Status bar will now be styled by sv_ttk. If specific colors are needed, they should be harmonious.
            # "status_bar_bg": "#f0f0f0", "status_bar_fg": "#000000", # Example: neutral status bar
        }
    elif theme_name == "dark":
        _theme_settings = {
            # sv_ttk uses dark greys for root_bg in dark mode
            "root_bg": "#202020", # Adjusted to match typical sv_ttk dark theme
            "fg_color": "#ffffff", # General foreground for non-ttk elements
            "sel_bg": "#0078d4", "sel_fg": "#ffffff", # Selection colors for editor
            "editor_bg": "#1e1e1e", "editor_fg": "#d4d4d4", "editor_insert_bg": "#d4d4d4",
            "comment_color": "#608b4e", "command_color": "#569cd6", "brace_color": "#c586c0",
            "ln_text_color": "#6a6a6a", "ln_bg_color": "#252526",
            "panedwindow_sash": "#333333", # Dark sash for PanedWindow
            # "status_bar_bg": "#2b2b2b", "status_bar_fg": "#d0d0d0", # Example: neutral status bar
        }
    else:
        return

    # Apply colors to the root window
    root.configure(bg=_theme_settings["root_bg"])

    # --- ttk Widget Theming ---
    # All ttk widget styling (buttons, treeview, scrollbars, progressbar, status_bar, etc.)
    # is now primarily handled by sv_ttk.set_theme() called above.

    # The status_bar (ttk.Label) will be styled by sv_ttk.
    # If you need to override its font or specific aspects not covered by sv_ttk's theme:
    # if 'status_bar' in globals() and status_bar:
    #     status_bar.configure(font=Font(family=ui_font_family, size=9)) # Example: ensure font

    # PanedWindow sash color: sv_ttk usually styles sashes well.
    # or if you want a specific color. sv_ttk usually styles sashes.
    if 'main_pane' in globals() and main_pane:
         main_pane.configure(sashrelief=tk.FLAT, sashwidth=6, bg=_theme_settings["panedwindow_sash"])

    # --- tk Widget Theming (Manual - These are not ttk widgets) ---
    # These remain essential as sv_ttk only themes ttk widgets.
    # We now need to iterate through all open tabs and apply the theme to each one.
    for tab in tabs.values():
        if tab.editor:
            tab.editor.configure(
                background=_theme_settings["editor_bg"], foreground=_theme_settings["editor_fg"],
                selectbackground=_theme_settings["sel_bg"], selectforeground=_theme_settings["sel_fg"],
                insertbackground=_theme_settings["editor_insert_bg"],
                relief=tk.FLAT, borderwidth=0
            )
            # Configure tags for each editor instance
            tab.editor.tag_configure("latex_command", foreground=_theme_settings["command_color"], font=tab.editor_font)
            tab.editor.tag_configure("latex_brace", foreground=_theme_settings["brace_color"], font=tab.editor_font)
            comment_font = tab.editor_font.copy()
            comment_font.configure(slant="italic")
            tab.editor.tag_configure("latex_comment", foreground=_theme_settings["comment_color"], font=comment_font)
        
        # Update the theme of the line numbers canvas for each tab
        if tab.line_numbers:
            tab.line_numbers.update_theme(text_color=_theme_settings["ln_text_color"], bg_color=_theme_settings["ln_bg_color"])

    # Handle temporary status bar message styling
    # If a temporary message is active, its specific styling (if any) should be applied


    # Trigger a heavy update to redraw syntax highlighting, outline, and line numbers
    perform_heavy_updates()
    if root:
        # Ensure the status bar padding is set correctly after theme application
        if 'status_bar' in globals() and status_bar:
             # sv_ttk should handle padding for ttk.Label.
             pass
        # Update the background of the root window itself
        root.configure(bg=_theme_settings["root_bg"])

        # Force an update to apply all configuration changes immediately
        root.update_idletasks()