import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.font import Font
import os
import subprocess
import platform
import sv_ttk # Import sv_ttk

# Import functions from other modules
import editor_logic
import latex_compiler
import llm_service # MODIFIED: Import new llm_service
import latex_translator # NEW: Import latex_translator

# Global variables for main widgets and state
# These are initialized in setup_gui and accessed by other modules
root = None
editor = None
outline_tree = None
llm_progress_bar = None
line_numbers_canvas = None
editor_font = None # Store the editor font globally
current_file_path = None # To track the currently open file
_last_saved_content = "\n" # Content of the editor at last save
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
    heavy_update_timer_id = None # Reset timer ID
    if editor:
        editor_logic.apply_syntax_highlighting()
    if outline_tree:
        editor_logic.update_outline_tree()
    if line_numbers_canvas:
        line_numbers_canvas.redraw()

def schedule_heavy_updates(_=None):
    """Schedules heavy updates after a short delay."""
    global heavy_update_timer_id
    if root and heavy_update_timer_id is not None:
        root.after_cancel(heavy_update_timer_id)
    if root and editor: # Ensure root and editor are available
        current_delay = HEAVY_UPDATE_DELAY_NORMAL
        try:
            # Get total lines to determine if the file is large
            last_line_index_str = editor.index("end-1c")
            # Correctly get total_lines, handling empty editor
            total_lines = 0
            if last_line_index_str: # Ensure index is not None or empty
                total_lines = int(last_line_index_str.split(".")[0])
                if total_lines == 1 and not editor.get("1.0", "1.end").strip(): # Check if line 1 is empty
                    total_lines = 0
            
            if total_lines > LARGE_FILE_LINE_THRESHOLD:
                current_delay = HEAVY_UPDATE_DELAY_LARGE_FILE
        except tk.TclError: # Handle cases where editor might not be ready
            pass # Use normal delay
        heavy_update_timer_id = root.after(current_delay, perform_heavy_updates)

def get_theme_setting(key, default=None):
    """Gets a value from the current theme settings."""
    return _theme_settings.get(key, default)

def get_current_file_path_for_llm():
    """Getter function for llm_logic to access the current_file_path."""
    global current_file_path
    return current_file_path

## -- Zoom Functionality -- ##

def zoom_in(_=None): # Accept optional event argument
    """Increases the editor font size."""
    global editor_font
    if not editor or not editor_font:
        return

    current_size = editor_font.cget("size")
    new_size = int(current_size * zoom_factor)
    new_size = min(new_size, max_font_size)

    if new_size != current_size:
        editor_font = Font(family=editor_font.cget("family"), size=new_size, weight=editor_font.cget("weight"), slant=editor_font.cget("slant"))
        editor.config(font=editor_font)
        if line_numbers_canvas:
            line_numbers_canvas.font = editor_font # Update the font reference
            line_numbers_canvas.redraw()
        perform_heavy_updates() # Reapply syntax highlighting and outline

def zoom_out(_=None): # Accept optional event argument
    """Decreases the editor font size."""
    global editor_font
    if not editor or not editor_font:
        return

    current_size = editor_font.cget("size")
    new_size = int(current_size / zoom_factor)
    new_size = max(new_size, min_font_size)

    if new_size != current_size:
        editor_font = Font(family=editor_font.cget("family"), size=new_size, weight=editor_font.cget("weight"), slant=editor_font.cget("slant"))
        editor.config(font=editor_font)
        if line_numbers_canvas:
            line_numbers_canvas.font = editor_font # Update the font reference
            line_numbers_canvas.redraw()
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
    global root, editor, _last_saved_content

    if not root or not editor:
        root.destroy()
        return

    current_content = editor.get("1.0", tk.END)

    if current_content != _last_saved_content:
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save before closing?",
            parent=root
        )
        if response is True:  # Yes, save and close
            save_file() # This will attempt to save
            # After save_file(), check if content is now saved.
            # It might not be if the user cancelled the "Save As" dialog.
            if editor.get("1.0", tk.END) == _last_saved_content:
                root.destroy()
            # If not equal, it means save was cancelled, so we do nothing and the window stays open.
        elif response is False:  # No, just close
            root.destroy()
        # else: Cancel, do nothing and the window stays open.
    else:
        # No unsaved changes, just close.
        root.destroy()

## -- File Operations -- ##

def open_file():
    """Opens a file and loads its content into the editor."""
    global current_file_path, _last_saved_content
    if not editor or not outline_tree:
        return

    filepath = filedialog.askopenfilename(
        title="Open File",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filepath:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                editor.delete("1.0", tk.END)
                editor.insert("1.0", content)
                # IMPORTANT: Get content back from editor to ensure it matches what get() will return later
                _last_saved_content = editor.get("1.0", tk.END)
                current_file_path = filepath # Update the global file path
                # Update other modules that need the file path
                editor_logic.current_file_path = current_file_path
                latex_compiler.current_file_path = current_file_path
                
                # Load prompt history and custom prompts for the newly opened file
                llm_service.load_prompt_history_for_current_file()
                llm_service.load_prompts_for_current_file()

                # Perform initial updates
                perform_heavy_updates()
                # Show feedback message
                show_temporary_status_message(f"✅ Opened: {os.path.basename(current_file_path)}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

def save_file():
    """Saves the current editor content to the current file or a new file."""
    global current_file_path, _last_saved_content
    if not editor:
        return

    content = editor.get("1.0", tk.END)

    if current_file_path:
        # Save to the existing file
        try:
            with open(current_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            _last_saved_content = content # Update last saved state
            # Show feedback message
            show_temporary_status_message(f"✅ Saved: {os.path.basename(current_file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{e}")
    else:
        # Ask user for a new file path
        new_filepath = filedialog.asksaveasfilename(
            defaultextension=".tex",
            filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save File As"
        )
        if new_filepath:
            current_file_path = new_filepath # Update the global file path
            # Update other modules that need the file path
            editor_logic.current_file_path = current_file_path
            latex_compiler.current_file_path = current_file_path
            # Now save to the new file path
            save_file() # Recursive call to save to the newly set path

## -- Line Numbering Canvas -- ##

class LineNumbers(tk.Canvas):
    """A Canvas widget to display line numbers for a Text widget."""
    def __init__(self, master, editor_widget, font, **kwargs):
        super().__init__(master, **kwargs)
        self.editor = editor_widget
        self.font = font
        # Default colors (will be updated by apply_theme)
        self.text_color = "#6a737d"
        self.bg_color = "#f0f0f0"
        self.config(width=40, bg=self.bg_color, highlightthickness=0, bd=0)

    def update_theme(self, text_color, bg_color):
        """Updates the colors and redraws the line numbers."""
        self.text_color = text_color
        self.bg_color = bg_color
        self.config(bg=self.bg_color)
        self.redraw()

    def redraw(self, *args):
        """Redraws the line numbers based on the editor's visible content."""
        self.delete("all") # Clear previous numbers
        if not self.editor or not self.winfo_exists():
            return

        # Get the first visible line index in the editor
        first_visible_line_index = self.editor.index("@0,0")

        # Calculate the total number of lines in the document
        last_doc_line_index = self.editor.index("end-1c")
        # Handle empty editor case (index is "1.0" but no content)
        last_doc_line_num = int(last_doc_line_index.split('.')[0])
        if last_doc_line_index == "1.0" and not self.editor.get("1.0", "1.end"):
             last_doc_line_num = 0

        # Adjust the canvas width based on the number of digits in the last line number
        max_digits = len(str(last_doc_line_num)) if last_doc_line_num > 0 else 1
        # Calculate required width: width of max digits + padding
        required_width = self.font.measure("0" * max_digits) + 10 # 5px padding on each side
        # Update canvas width if it's significantly different
        if abs(self.winfo_width() - required_width) > 2: # Use a small tolerance
             self.config(width=required_width)

        # Iterate over visible lines and draw line numbers
        current_line_index = first_visible_line_index
        while True:
            # Get bounding box info for the current line
            dline = self.editor.dlineinfo(current_line_index)
            if dline is None:
                # No more visible lines
                break

            x, y, width, height, baseline = dline
            line_num_str = current_line_index.split(".")[0]

            # Draw the line number text
            self.create_text(required_width - 5, y, anchor="ne",
                             text=line_num_str, font=self.font, fill=self.text_color)

            # Move to the next line index
            next_line_index = self.editor.index(f"{current_line_index}+1line")
            if next_line_index == current_line_index:
                # Reached the end of the document
                break
            current_line_index = next_line_index

            # Safety break in case of infinite loop (shouldn't happen with +1line)
            if int(current_line_index.split('.')[0]) > last_doc_line_num + 100: # Check up to 100 lines past end
                 break

def setup_gui():
    """Sets up the main application window and widgets.""" # Corrected global list
    global root, editor, outline_tree, llm_progress_bar, line_numbers_canvas, editor_font, current_file_path, _theme_settings, status_bar, main_pane

    root = tk.Tk()
    root.title("AutomaTeX v1.0")
    root.geometry("1200x800") # Adjusted default size
    # Initial background will be set by apply_theme
    # root.iconbitmap("res/automatex.ico") # Ensure icon file exists
    
    # sv_ttk.set_theme("light") # Or "dark", will be set by apply_theme
    # No need for manual ttk.Style() or theme_use("clam") initially, sv_ttk handles it.

    editor_font = Font(family="Consolas", size=12) # Store font globally

    # --- Top Buttons Frame ---
    top_frame = ttk.Frame(root, padding=10) # Increased padding
    top_frame.pack(fill="x", pady=(0, 5)) # Add some pady below top_frame

    # File buttons
    ttk.Button(top_frame, text="📂 Open", command=open_file).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="💾 Save", command=save_file).pack(side="left", padx=3, pady=3)

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
    outline_tree.bind("<<TreeviewSelect>>", editor_logic.go_to_section)
    # Add the outline frame to the main pane
    main_pane.add(outline_frame, width=250, minsize=150) # Added minsize

    # --- Editor Container Frame (Line Numbers + Text Editor + Scrollbar) ---
    # Use a ttk.Frame for consistency and theme support
    editor_container = ttk.Frame(main_pane) # No specific padding here

    # Text Editor widget
    editor = tk.Text(editor_container, wrap="word", font=editor_font, undo=True,
                     relief=tk.FLAT, borderwidth=0, highlightthickness=0) # Modern flat look

    # Vertical Scrollbar for the editor
    # Must be created before configuring the editor's yscrollcommand
    editor_scrollbar = ttk.Scrollbar(editor_container, orient="vertical", command=editor.yview)

    # Line Numbers Canvas
    line_numbers_canvas = LineNumbers(editor_container, editor_widget=editor, font=editor_font)
    line_numbers_canvas.pack(side="left", fill="y") # Pack to the left of the editor

    # Pack the scrollbar and editor
    editor_scrollbar.pack(side="right", fill="y") # Pack scrollbar to the right
    editor.pack(side="left", fill="both", expand=True) # Editor fills the remaining space

    # Configure the editor's yscrollcommand to update both the scrollbar and line numbers
    def sync_scroll_and_redraw_linenums(*args):
        editor_scrollbar.set(*args) # Update the scrollbar position
        if line_numbers_canvas:
            # editor.yview() returns (top_fraction, bottom_fraction)
            # Move the line numbers canvas view to match the editor's top fraction
            current_y_view = editor.yview()
            line_numbers_canvas.yview_moveto(current_y_view[0])
            # Redraw line numbers (important for adding/removing lines)
            line_numbers_canvas.redraw()

    editor.config(yscrollcommand=sync_scroll_and_redraw_linenums)

    # Add the editor container to the main pane
    main_pane.add(editor_container, stretch="always", minsize=400) # Added minsize

    # --- Configure Syntax Highlighting Tags ---
    # These tags are configured here but applied in editor_logic.apply_syntax_highlighting
    # Default light theme colors
    editor.tag_configure("latex_command", font=editor_font) # Colors set in apply_theme
    editor.tag_configure("latex_brace", font=editor_font)   # Colors set in apply_theme
    comment_font_initial = editor_font.copy()
    comment_font_initial.configure(slant="italic")
    editor.tag_configure("latex_comment", font=comment_font_initial) # Colors set in apply_theme

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

    root.bind_all("<Control-t>", lambda event: latex_translator.open_translate_dialog()) # NEW: Shortcut for translate

    # Bind Zoom shortcuts
    root.bind_all("<Control-equal>", zoom_in) # Ctrl+= is common for zoom in
    root.bind_all("<Control-minus>", zoom_out)
    root.bind_all("<Control-s>", lambda event: save_file())

    # --- Bind Editor Events for Updates ---
    # Bind KeyRelease to schedule heavy updates (syntax, outline, line numbers)
    # This is triggered after text is entered or deleted
    def on_editor_key_release(event):
        # Trigger updates on keys that likely change structure or content significantly
        if event.keysym in ["Return", "BackSpace", "Delete", "Control_L", "Control_R", "Shift_L", "Shift_R"]:
            schedule_heavy_updates()
        # Also trigger on punctuation that might affect syntax or outline
        elif event.char in "{}[]();,.":
            schedule_heavy_updates()
        # Space and Tab can also affect outline structure
        elif event.keysym == "space" or event.keysym == "Tab":
             schedule_heavy_updates()
        # For other simple text entry, the scroll command binding handles line number positions.
        # A full redraw is less critical immediately.

    editor.bind("<KeyRelease>", on_editor_key_release)
    # Bind Configure event to redraw line numbers if editor size changes (e.g., window resize, wrap changes)
    editor.bind("<Configure>", schedule_heavy_updates)

    # --- Initialize Global References in Other Modules ---
    # Pass the created widgets and variables to the other modules
    editor_logic.set_editor_globals(editor, outline_tree, current_file_path)
    latex_compiler.set_compiler_globals(editor, root, current_file_path)
    # NOTE: Service initializations (LLM, Translator) are now handled in main.py after the GUI is fully set up.

    # Intercept the window close ('X') button to check for unsaved changes
    root.protocol("WM_DELETE_WINDOW", on_close_request)
    return root

def apply_theme(theme_name):
    """Applies the specified theme (light or dark) to the GUI."""
    global current_theme, line_numbers_canvas, editor_font, _theme_settings, root, editor, outline_tree, status_bar, main_pane

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
    if editor:
        editor.configure(
            background=_theme_settings["editor_bg"], foreground=_theme_settings["editor_fg"],
            selectbackground=_theme_settings["sel_bg"], selectforeground=_theme_settings["sel_fg"],
            insertbackground=_theme_settings["editor_insert_bg"],
            relief=tk.FLAT, borderwidth=0
        )
        editor.tag_configure("latex_command", foreground=_theme_settings["command_color"], font=editor_font)
        editor.tag_configure("latex_brace", foreground=_theme_settings["brace_color"], font=editor_font)
        comment_font = editor_font.copy()
        comment_font.configure(slant="italic")
        editor.tag_configure("latex_comment", foreground=_theme_settings["comment_color"], font=comment_font)

    # Handle temporary status bar message styling
    # If a temporary message is active, its specific styling (if any) should be applied
    # by show_temporary_status_message. When cleared, it reverts.
    # sv_ttk will handle the default appearance.
    if _temporary_status_active and status_bar:
        # Example: if temporary messages have a special background
        pass # status_bar.config(background="<temp_color_bg>", foreground="<temp_color_fg>")

    # Update the theme of the line numbers canvas
    if line_numbers_canvas:
        line_numbers_canvas.update_theme(text_color=_theme_settings["ln_text_color"], bg_color=_theme_settings["ln_bg_color"])

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