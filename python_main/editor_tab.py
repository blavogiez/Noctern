# editor_tab.py

import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
import os

# This class was moved from interface.py to avoid circular imports.
# It handles the visual display of line numbers for a given Text widget.
class LineNumbers(tk.Canvas):
    """A Canvas widget to display line numbers for a Text widget."""
    def __init__(self, master, editor_widget, font, **kwargs):
        super().__init__(master, **kwargs)
        self.editor = editor_widget
        self.font = font
        self.text_color = "#6a737d"
        self.bg_color = "#f0f0f0"
        self.config(width=40, bg=self.bg_color, highlightthickness=0, bd=0)

    def update_theme(self, text_color, bg_color):
        """Updates the colors of the line number bar."""
        self.text_color = text_color
        self.bg_color = bg_color
        self.config(bg=self.bg_color)
        self.redraw()

    def redraw(self, *args):
        """Redraws the line numbers, adjusting for the editor's view."""
        self.delete("all")
        if not self.editor or not self.winfo_exists():
            return
        
        # Get the index of the first visible line.
        first_visible_line_index = self.editor.index("@0,0")
        # Get the index of the last character in the document.
        last_doc_line_index = self.editor.index("end-1c")
        
        try:
            last_doc_line_num = int(last_doc_line_index.split('.')[0])
            # Handle empty document case.
            if last_doc_line_index == "1.0" and not self.editor.get("1.0", "1.end"):
                 last_doc_line_num = 0
        except (ValueError, tk.TclError):
            last_doc_line_num = 0

        # Adjust canvas width based on the number of digits in the last line number.
        max_digits = len(str(last_doc_line_num)) if last_doc_line_num > 0 else 1
        required_width = self.font.measure("0" * max_digits) + 10
        if abs(self.winfo_width() - required_width) > 2:
             self.config(width=required_width)

        # Iterate through visible lines and draw the numbers.
        current_line_index = first_visible_line_index
        while True:
            dline = self.editor.dlineinfo(current_line_index)
            if dline is None: break
            x, y, width, height, baseline = dline
            line_num_str = current_line_index.split(".")[0]
            self.create_text(required_width - 5, y, anchor="ne",
                             text=line_num_str, font=self.font, fill=self.text_color)
            
            next_line_index = self.editor.index(f"{current_line_index}+1line")
            if next_line_index == current_line_index: break # End of document
            current_line_index = next_line_index
            # Safety break for very large files.
            if int(current_line_index.split('.')[0]) > last_doc_line_num + 100: break

class EditorTab(ttk.Frame):
    """Represents a single tab in the editor notebook, containing a Text widget and its components."""
    def __init__(self, parent_notebook, file_path=None, schedule_heavy_updates_callback=None):
        super().__init__(parent_notebook)
        self.notebook = parent_notebook
        self.file_path = file_path
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback
        self.last_saved_content = "" if file_path else "\n"
        self.error_labels = [] # To hold widgets for missing image warnings.

        self.editor_font = Font(family="Consolas", size=12)

        # Main components of the tab
        self.editor = tk.Text(self, wrap="word", font=self.editor_font, undo=True,
                              relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.editor.yview)
        self.line_numbers = LineNumbers(self, editor_widget=self.editor, font=self.editor_font)
        
        self.line_numbers.pack(side="left", fill="y")
        self.scrollbar.pack(side="right", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)

        # Synchronize scrolling of editor and line numbers
        def sync_scroll_and_redraw(*args):
            self.scrollbar.set(*args)
            self.line_numbers.yview_moveto(self.editor.yview()[0])
            self.line_numbers.redraw()

        self.editor.config(yscrollcommand=sync_scroll_and_redraw)
        
        self.editor.bind("<KeyRelease>", self.on_key_release)
        self.editor.bind("<Configure>", self.schedule_heavy_updates)

    def on_key_release(self, event=None):
        """Called on any key release to update tab state and schedule updates."""
        self.update_tab_title()
        self.schedule_heavy_updates(event)

    def schedule_heavy_updates(self, event=None):
        """Calls the debounced update scheduler from the main interface."""
        if self._schedule_heavy_updates_callback:
            self._schedule_heavy_updates_callback(event)

    def get_content(self):
        """Returns the entire content of the editor."""
        return self.editor.get("1.0", tk.END)

    def is_dirty(self):
        """Checks if the editor content has changed since the last save."""
        return self.get_content() != self.last_saved_content

    def update_tab_title(self):
        """Updates the tab's text label, adding a '*' if the content is unsaved."""
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
                    self.editor.edit_reset() # Clear the undo/redo stack
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
        else:
            self.update_tab_title()

    def save_file(self, new_path=None):
        """Saves the editor content to a file."""
        if new_path:
            self.file_path = new_path
        
        if not self.file_path:
            return False

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