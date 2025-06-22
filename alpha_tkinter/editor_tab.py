# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\editor_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
import os
import math # For ceil

# Refactor LineNumbers to use a Text widget for better performance
class LineNumbers(tk.Text):
    """A Text widget to display line numbers for a main Text editor widget."""
    def __init__(self, master, editor_widget, font, **kwargs):
        super().__init__(master, **kwargs)
        self.editor = editor_widget
        self.font = font
        self.text_color = "#6a737d"
        self.bg_color = "#f0f0f0"
        
        # Configure as read-only text widget for line numbers
        self.config(
            width=4, # Initial width, will adjust dynamically
            bg=self.bg_color, fg=self.text_color,
            font=self.font,
            relief=tk.FLAT, borderwidth=0, highlightthickness=0,
            state="disabled", # Make it read-only
            wrap="none", # No word wrap
            cursor="arrow" # Standard cursor
        )
        
        # Bind scroll events to synchronize with editor
        # These bindings are crucial for smooth scrolling of line numbers
        self.editor.bind("<MouseWheel>", self._on_mousewheel)
        self.editor.bind("<Button-4>", self._on_mousewheel) # Linux scroll up
        self.editor.bind("<Button-5>", self._on_mousewheel) # Linux scroll down
        self.editor.bind("<Configure>", self._on_configure) # For resizing the editor, which might affect line numbers

    def update_theme(self, text_color, bg_color):
        self.text_color = text_color
        self.bg_color = bg_color
        self.config(bg=self.bg_color)
        self.redraw() # Redraw content to apply new colors

    def redraw(self):
        """Updates the line numbers displayed in the widget."""
        self.config(state="normal") # Enable editing temporarily
        self.delete("1.0", tk.END) # Clear existing numbers

        if not self.editor or not self.winfo_exists():
            self.config(state="disabled")
            return
        
        # Get total lines in the document for width calculation
        last_doc_line_index = self.editor.index("end-1c") # Last character in the document
        # Handle empty editor case: "end-1c" on empty editor is "1.0", so check content
        if last_doc_line_index == "1.0" and not self.editor.get("1.0", "1.end").strip():
            total_lines_in_doc = 0
        else:
            total_lines_in_doc = int(last_doc_line_index.split('.')[0])

        # Calculate the number of lines to display based on the editor's height
        # We need to display enough lines to fill the visible area, plus a buffer
        # Estimate lines per page based on font height
        line_height = self.font.metrics("linespace")
        if line_height == 0: line_height = 1 # Avoid division by zero
        lines_per_page = math.ceil(self.editor.winfo_height() / line_height) if self.editor.winfo_height() > 0 else 50
        
        # Determine the maximum line number that might be displayed for width calculation
        # This should be the total lines in the document, or the number of lines that fit on screen, whichever is larger
        max_line_num_for_width = max(total_lines_in_doc, lines_per_page + 10) # Add a buffer for new lines
        max_digits = len(str(max_line_num_for_width)) if max_line_num_for_width > 0 else 1
        
        # Calculate required width in characters for the line numbers widget
        # Add 1 for padding/spacing
        required_width_chars = max_digits + 1 
        
        # Update width of the line numbers Text widget if it needs to change
        current_width_chars = self.cget("width")
        if current_width_chars != required_width_chars:
            self.config(width=required_width_chars)

        # Insert line numbers for the entire document (or a large buffer)
        # This is done once on content change, not on every scroll.
        # The yview_moveto will handle visible range.
        for i in range(1, total_lines_in_doc + lines_per_page + 1): # Add buffer for new lines
            self.insert(tk.END, f"{i}\n")
        
        # Synchronize scroll position with the main editor
        self.yview_moveto(self.editor.yview()[0])

        self.config(state="disabled") # Disable editing again

    def _on_mousewheel(self, event):
        """Propagates mouse wheel scroll from editor to line numbers."""
        # The 'units' argument scrolls by lines, 'pages' by page.
        # event.delta is typically 120 or -120 per scroll "tick"
        self.yview_scroll(-1 * int(event.delta/120), "units")
        # Return "break" to prevent the event from propagating further if desired,
        # but here we want the editor to also scroll.
        # If the editor's yscrollcommand is properly set, it will handle its own scroll.
        # We just need to ensure line numbers follow.

    def _on_configure(self, event):
        """Handles configure events (e.g., resize) to redraw line numbers."""
        self.redraw()

class EditorTab(ttk.Frame):
    """Represents a single tab in the editor notebook."""
    def __init__(self, parent_notebook, file_path=None, schedule_heavy_updates_callback=None):
        super().__init__(parent_notebook)
        self.notebook = parent_notebook
        self.file_path = file_path
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback # Store the callback
        self.last_saved_content = "" if file_path else "\n"

        # Each tab has its own font object to manage zoom level independently
        self.editor_font = Font(family="Consolas", size=12)

        # --- Editor Widgets for this tab ---
        self.editor = tk.Text(self, wrap="word", font=self.editor_font, undo=True,
                              relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.editor.yview) # Main editor scrollbar
        self.line_numbers = LineNumbers(self, editor_widget=self.editor, font=self.editor_font)
        
        self.line_numbers.pack(side="left", fill="y")
        self.scrollbar.pack(side="right", fill="y") # Pack main editor scrollbar
        self.editor.pack(side="left", fill="both", expand=True)

        # --- Configure scroll and events ---
        def sync_scroll_and_redraw(*args):
            self.scrollbar.set(*args)
            self.line_numbers.yview_moveto(self.editor.yview()[0]) # This part is fast and syncs the scroll position.
            self.schedule_heavy_updates() # Schedule heavy updates (syntax, outline)

        self.editor.config(yscrollcommand=sync_scroll_and_redraw)
        
        # Bind events to the editor instance of this tab
        self.editor.bind("<KeyRelease>", self.on_key_release)
        self.editor.bind("<Configure>", self.schedule_heavy_updates)

    def on_key_release(self, event=None):
        """Handle key release events to check for dirtiness and schedule updates."""
        self.update_tab_title()
        self.schedule_heavy_updates(event)

    def schedule_heavy_updates(self, event=None):
        """Schedules heavy updates for this specific tab by calling the main interface scheduler callback."""
        if self._schedule_heavy_updates_callback:
            self._schedule_heavy_updates_callback(event) # Call the passed callback

    def get_content(self):
        """Returns the full content of the editor widget."""
        return self.editor.get("1.0", tk.END)

    def is_dirty(self):
        """Checks if the editor content has changed since the last save."""
        return self.get_content() != self.last_saved_content

    def update_tab_title(self):
        """Updates the notebook tab text to show a '*' if the file is dirty."""
        base_name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        title = f"{base_name}{'*' if self.is_dirty() else ''}"
        self.notebook.tab(self, text=title)

    def load_file(self):
        """Loads content from self.file_path into the editor."""
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.editor.delete("1.0", tk.END)
                    self.editor.insert("1.0", content)
                    self.last_saved_content = self.get_content()
                    self.update_tab_title()
                    self.editor.edit_reset() # Clear undo stack
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
        else:
            # This is a new, unsaved file
            self.update_tab_title()

    def save_file(self, new_path=None):
        """
        Saves the editor content. If new_path is provided, it's a 'Save As' operation.
        Returns True on success, False on failure (e.g., user cancelled Save As).
        """
        if new_path:
            self.file_path = new_path
        
        if not self.file_path:
            return False # Should have been handled by a 'save as' dialog before calling this

        try:
            content = self.get_content()
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.last_saved_content = content
            self.update_tab_title()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{e}")
            return False