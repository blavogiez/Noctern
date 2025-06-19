import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.font import Font
import os
import subprocess
import platform

# Import functions from other modules
import editor_logic
import latex_compiler
import llm_logic

# Global variables for main widgets and state
# These are initialized in setup_gui and accessed by other modules
root = None
editor = None
outline_tree = None
llm_progress_bar = None
line_numbers_canvas = None
editor_font = None # Store the font globally for theme updates
current_file_path = None # To track the currently open file

# Timer for heavy updates (syntax, outline, line numbers)
heavy_update_timer_id = None

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
    if root:
        # Schedule the update to happen after 200ms of inactivity
        heavy_update_timer_id = root.after(200, perform_heavy_updates)

## -- File Operations -- ##

def open_file():
    """Opens a file and loads its content into the editor."""
    global current_file_path
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
                current_file_path = filepath # Update the global file path
                # Update other modules that need the file path
                editor_logic.current_file_path = current_file_path
                latex_compiler.current_file_path = current_file_path

                # Perform initial updates
                perform_heavy_updates()

        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

def save_file():
    """Saves the current editor content to the current file or a new file."""
    global current_file_path
    if not editor:
        return

    content = editor.get("1.0", tk.END)

    if current_file_path:
        # Save to the existing file
        try:
            with open(current_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            # messagebox.showinfo("Success", f"File saved:\n{current_file_path}") # Optional confirmation
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
    """Sets up the main application window and widgets."""
    global root, editor, outline_tree, llm_progress_bar, line_numbers_canvas, editor_font, current_file_path

    root = tk.Tk()
    root.title("AutomaTeX v1.0")
    root.geometry("1200x800") # Adjusted default size
    root.configure(bg="#f5f5f5") # Default light theme background
    # root.iconbitmap("res/automatex.ico") # Ensure icon file exists

    style = ttk.Style()
    style.theme_use("clam") # Use clam theme as a base

    editor_font = Font(family="Consolas", size=12) # Store font globally

    # --- Top Buttons Frame ---
    top_frame = ttk.Frame(root, padding=5)
    top_frame.pack(fill="x")

    # File buttons
    ttk.Button(top_frame, text="📂 Open", command=open_file).pack(side="left", padx=5)
    ttk.Button(top_frame, text="💾 Save", command=save_file).pack(side="left", padx=5)

    # LaTeX buttons
    ttk.Button(top_frame, text="🛠 Compile (Ctrl+S)", command=latex_compiler.compile_latex).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🔍 Check Syntax (Ctrl+Shift+D)", command=latex_compiler.run_chktex_check).pack(side="left", padx=5)

    # LLM buttons
    ttk.Button(top_frame, text="✨ Complete (Ctrl+Shift+C)", command=llm_logic.complete_with_llm).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🎯 Generate Text (Ctrl+Shift+G)", command=llm_logic.generate_text_from_prompt).pack(side="left", padx=5)

    # Theme button
    # Use a lambda to toggle between themes
    ttk.Button(top_frame, text="🌓 Theme", command=lambda: apply_theme("dark" if current_theme == "light" else "light")).pack(side="right", padx=5)

    # --- Main Paned Window (Outline Tree + Editor) ---
    # PanedWindow allows resizing the panes by dragging the sash
    main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief="raised", bg="#e0e0e0")
    main_pane.pack(fill="both", expand=True)

    # --- Left Outline Tree Frame ---
    outline_frame = ttk.Frame(main_pane)
    # Treeview to display document outline
    outline_tree = ttk.Treeview(outline_frame, show="tree")
    outline_tree.pack(fill="both", expand=True)
    # Bind selection event to go_to_section function
    outline_tree.bind("<<TreeviewSelect>>", editor_logic.go_to_section)
    # Add the outline frame to the main pane
    main_pane.add(outline_frame, width=250) # Set initial width

    # --- Editor Container Frame (Line Numbers + Text Editor + Scrollbar) ---
    # Use a ttk.Frame for consistency and theme support
    editor_container = ttk.Frame(main_pane)

    # Text Editor widget
    editor = tk.Text(editor_container, wrap="word", font=editor_font, undo=True,
                     bg="#ffffff", fg="#333333", highlightthickness=0, bd=0)

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
    main_pane.add(editor_container, stretch="always") # Editor pane stretches to fill space

    # --- Configure Syntax Highlighting Tags ---
    # These tags are configured here but applied in editor_logic.apply_syntax_highlighting
    # Default light theme colors
    editor.tag_configure("latex_command", foreground="#005cc5", font=editor_font)
    editor.tag_configure("latex_brace", foreground="#d73a49", font=editor_font)
    editor.tag_configure("latex_comment", foreground="#6a737d", font=editor_font.copy().configure(slant="italic"))

    # --- LLM Progress Bar ---
    llm_progress_bar = ttk.Progressbar(root, mode="indeterminate", length=200)
    llm_progress_bar.pack(pady=2)
    llm_progress_bar.pack_forget() # Hide by default

    # --- Status Bar (for GPU info) ---
    status_bar = ttk.Label(root, text="⏳ Initializing...", anchor="w", relief="sunken", padding=4)
    status_bar.pack(side="bottom", fill="x")

    # Function to update GPU status (runs in a loop)
    def update_gpu_status():
        try:
            # Command to get GPU info (works on systems with nvidia-smi)
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
                encoding="utf-8"
            ).strip()

            name, temp, usage = output.split(", ")
            status_text = f"🎮 GPU: {name}   🌡 {temp}°C   📊 {usage}% used"
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Handle cases where nvidia-smi is not found or fails
            status_text = "⚠️ GPU status not available (nvidia-smi not found or failed)"
        except Exception as e:
            # Handle any other unexpected errors
            status_text = f"⚠️ Error getting GPU status: {str(e)}"

        status_bar.config(text=status_text)
        # Schedule the next update
        root.after(3000, update_gpu_status) # Update every 3 seconds

    # Start the GPU status update loop
    update_gpu_status()

    # --- Bind Keyboard Shortcuts ---
    # Bindings are on the root window to work application-wide
    root.bind_all("<Control-Shift-G>", lambda event: llm_logic.generate_text_from_prompt())
    root.bind_all("<Control-Shift-C>", lambda event: llm_logic.complete_with_llm())
    root.bind_all("<Control-Shift-D>", lambda event: latex_compiler.run_chktex_check())
    root.bind_all("<Control-Shift-V>", lambda event: editor_logic.paste_image())
    root.bind_all("<Control-o>", lambda event: open_file())
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
    llm_logic.set_llm_globals(editor, root, llm_progress_bar)

    return root # Return the root window

current_theme = "light" # Global variable to track the current theme

def apply_theme(theme):
    """Applies the specified theme (light or dark) to the GUI."""
    global current_theme, line_numbers_canvas, editor_font
    current_theme = theme # Update the global theme state

    style = ttk.Style()
    # Use clam theme as a base, then configure specific elements
    style.theme_use("clam")

    # Define colors based on theme
    if theme == "light":
        root_bg = "#f5f5f5"
        bg_color = "#ffffff" # Background for most widgets
        fg_color = "#000000" # Foreground for most widgets
        tree_bg = "#ffffff"
        tree_fg = "#000000"
        sel_bg = "#cce6ff" # Selection background
        sel_fg = "#000000" # Selection foreground
        editor_bg = "#ffffff"
        editor_fg = "#000000"
        comment_color = "#6a737d" # Color for LaTeX comments
        ln_text_color = "#6a737d" # Line number text color
        ln_bg_color = "#f0f0f0"   # Line number background color
    elif theme == "dark":
        root_bg = "#1e1e1e"
        bg_color = "#2e2e2e"
        fg_color = "#ffffff"
        tree_bg = "#2e2e2e"
        tree_fg = "#ffffff"
        sel_bg = "#44475a"
        sel_fg = "#ffffff"
        editor_bg = "#1e1e1e"
        editor_fg = "#f8f8f2"
        comment_color = "#6272a4"
        ln_text_color = "#6272a4" # Similar to comments
        ln_bg_color = "#282a36"   # Slightly different from editor background
    else:
        # If theme is neither 'light' nor 'dark', do nothing
        return

    # Apply colors to the root window
    root.configure(bg=root_bg)

    # Apply colors to the Text editor widget
    editor.configure(bg=editor_bg, fg=editor_fg, insertbackground=fg_color,
                     selectbackground=sel_bg, selectforeground=sel_fg)

    # Update syntax highlighting tag configurations
    # Use the global editor_font
    editor.tag_configure("latex_command", foreground="#8be9fd" if theme == "dark" else "#005cc5", font=editor_font)
    editor.tag_configure("latex_brace", foreground="#ff79c6" if theme == "dark" else "#d73a49", font=editor_font)
    # Create a new font object for italic comments if needed, or configure the existing one
    comment_font = editor_font.copy()
    comment_font.configure(slant="italic")
    editor.tag_configure("latex_comment", foreground=comment_color, font=comment_font)

    # Apply style to Treeview
    style.configure("Treeview",
                    background=tree_bg,
                    foreground=tree_fg,
                    fieldbackground=tree_bg,
                    bordercolor=bg_color) # Use background color for border
    style.map("Treeview",
              background=[('selected', sel_bg)],
              foreground=[('selected', sel_fg)])

    # Apply style to other ttk widgets (Frame, Label, Button, Progressbar)
    style.configure("TFrame", background=bg_color)
    style.configure("TLabel", background=bg_color, foreground=fg_color)
    style.configure("TButton", background=bg_color, foreground=fg_color)
    style.configure("Horizontal.TProgressbar", troughcolor=bg_color, background=sel_bg)
    style.configure("TPanedwindow", background=bg_color) # Apply to PanedWindow sash area

    # Manually update background/foreground for some widgets if needed
    # The status bar is a ttk.Label, should be covered by "TLabel" style, but explicit update is safer
    for widget in root.winfo_children():
        if isinstance(widget, ttk.Label):
            # Check if it's the status bar or another label
            if widget.cget("text").startswith("🎮 GPU:") or widget.cget("text").startswith("⚠️ GPU:"):
                 widget.configure(background=bg_color, foreground=fg_color)

    # Update the theme of the line numbers canvas
    if line_numbers_canvas:
        line_numbers_canvas.update_theme(text_color=ln_text_color, bg_color=ln_bg_color)

    # Trigger a heavy update to redraw syntax highlighting, outline, and line numbers
    # This ensures everything is displayed with the new theme colors
    perform_heavy_updates()