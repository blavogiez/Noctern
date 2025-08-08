"""
This module defines the `LineNumbers` and `EditorTab` classes, which are core components
of the text editor interface. `LineNumbers` provides a visual display of line numbers
adjacent to a `tk.Text` widget, while `EditorTab` encapsulates a single editable
document tab within the application's notebook.
"""

import re
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
import os
from tkinter import messagebox
from utils import debug_console
from editor.image_preview import ImagePreview
from editor import shortcuts # Import the new shortcuts module

class LineNumbers(tk.Canvas):
    """
    A custom Tkinter Canvas widget responsible for displaying line numbers
    alongside a `tk.Text` widget.
    """
    def __init__(self, master, editor_widget, font, **kwargs):
        super().__init__(master, **kwargs)
        self.editor = editor_widget
        self.font = font
        self.text_color = "#6a737d"
        self.bg_color = "#f0f0f0"
        self.config(width=40, bg=self.bg_color, highlightthickness=0, bd=0)

    def update_theme(self, text_color, bg_color):
        self.text_color = text_color
        self.bg_color = bg_color
        self.config(bg=self.bg_color)
        self.redraw()

    def redraw(self, *args):
        self.delete("all")
        if not self.editor or not self.winfo_exists():
            return
        
        first_visible_line = self.editor.index("@0,0")
        last_char = self.editor.index("end-1c")
        
        try:
            last_line_num = int(last_char.split('.')[0])
            if last_char == "1.0" and not self.editor.get("1.0", "1.end"):
                 last_line_num = 0
        except (ValueError, tk.TclError):
            last_line_num = 0

        max_digits = len(str(last_line_num)) if last_line_num > 0 else 1
        required_width = self.font.measure("0" * max_digits) + 10
        
        if abs(self.winfo_width() - required_width) > 2:
             self.config(width=required_width)

        current_line = first_visible_line
        while True:
            dline = self.editor.dlineinfo(current_line)
            if dline is None: break
            
            y = dline[1]
            line_num_str = current_line.split(".")[0]
            
            self.create_text(required_width - 5, y, anchor="ne",
                             text=line_num_str, font=self.font, fill=self.text_color)
            
            next_line = self.editor.index(f"{current_line}+1line")
            if next_line == current_line: break
            current_line = next_line
            
            if int(current_line.split('.')[0]) > last_line_num + 100: break

class EditorTab(ttk.Frame):
    """
    Represents a single editable tab. It contains the text editor,
    line numbers, and scrollbar, and connects them to the application's logic.
    """
    def __init__(self, parent_notebook, file_path=None, schedule_heavy_updates_callback=None):
        super().__init__(parent_notebook)
        self.notebook = parent_notebook
        self.file_path = file_path
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback
        self.last_saved_content = ""
        self.error_labels = []

        self.editor_font = Font(family="Consolas", size=12)

        self.editor = tk.Text(self, wrap="word", font=self.editor_font, undo=True,
                              relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.editor.yview)
        self.line_numbers = LineNumbers(self, editor_widget=self.editor, font=self.editor_font)
        
        self.line_numbers.pack(side="left", fill="y")
        self.scrollbar.pack(side="right", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)

        def sync_scroll_and_redraw(*args):
            self.scrollbar.set(*args)
            self.line_numbers.yview_moveto(self.editor.yview()[0])
            self.line_numbers.redraw()

        self.editor.config(yscrollcommand=sync_scroll_and_redraw)
        
        # Bind events
        self.editor.bind("<KeyRelease>", self.on_key_release)
        self.editor.bind("<Configure>", self.schedule_heavy_updates)

        # Image preview on hover
        self.image_preview = ImagePreview(self)
        self._hover_timer_id = None
        self._hover_path = None
        self.editor.bind("<Motion>", self._on_mouse_motion)
        self.editor.bind("<Leave>", self._on_mouse_leave)

        # Setup all editor shortcuts from the dedicated module
        shortcuts.setup_shortcuts(self.editor)

    def _on_mouse_motion(self, event):
        if self._hover_timer_id:
            self.after_cancel(self._hover_timer_id)
        self.image_preview.hide()

        index = self.editor.index(f"@{event.x},{event.y}")
        line_content = self.editor.get(f"{index.split('.')[0]}.0", f"{index.split('.')[0]}.end")

        if r"\includegraphics" in line_content:
            match = re.search(r'\\includegraphics(?:\\[^]]*\])?\{(.*?)\}', line_content)
            if match and self.file_path:
                image_path = os.path.join(os.path.dirname(self.file_path), match.group(1))
                if os.path.exists(image_path):
                    self._hover_path = image_path
                    self._hover_timer_id = self.after(200, self._show_image_preview, event.x_root, event.y_root)

    def _on_mouse_leave(self, event):
        if self._hover_timer_id:
            self.after_cancel(self._hover_timer_id)
        self.image_preview.hide()

    def _show_image_preview(self, x_root, y_root):
        if self._hover_path:
            self.image_preview.show_image(self._hover_path, (x_root + 10, y_root + 10))
        self._hover_path = None

    def on_key_release(self, event=None):
        self.update_tab_title()
        self.schedule_heavy_updates(event)

    def schedule_heavy_updates(self, event=None):
        if self._schedule_heavy_updates_callback:
            self._schedule_heavy_updates_callback(event)

    def get_content(self):
        return self.editor.get("1.0", tk.END)

    def is_dirty(self):
        return self.get_content() != self.last_saved_content

    def update_tab_title(self):
        base_name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        title = f"{base_name}{'*' if self.is_dirty() else ''}"
        self.notebook.tab(self, text=title)

    def load_file(self):
        content = ""
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                debug_console.log(f"Successfully loaded file: {self.file_path}", level='INFO')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
                debug_console.log(f"Error loading file '{self.file_path}': {e}", level='ERROR')
        else:
            self.last_saved_content = "\n" # Mark as dirty from the start for new files
        
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", content)
        self.last_saved_content = self.get_content()
        self.update_tab_title()
        self.editor.edit_reset()

    def save_file(self, new_path=None):
        if new_path:
            self.file_path = new_path
        
        if not self.file_path:
            debug_console.log("Save aborted: No file path specified.", level='WARNING')
            return False

        try:
            content_to_save = self.get_content()
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content_to_save)
            self.last_saved_content = content_to_save
            self.update_tab_title()
            debug_console.log(f"Successfully saved file: {self.file_path}", level='INFO')
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{e}")
            debug_console.log(f"Failed to save file '{self.file_path}': {e}", level='ERROR')
            return False
