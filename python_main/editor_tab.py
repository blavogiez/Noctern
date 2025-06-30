# editor_tab.py

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
import os
# REMOVED: No longer need to import editor_enhancements here.

# This class was moved from interface.py to avoid circular imports
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
        self.text_color = text_color
        self.bg_color = bg_color
        self.config(bg=self.bg_color)
        self.redraw()

    def redraw(self, *args):
        self.delete("all")
        if not self.editor or not self.winfo_exists():
            return
        
        first_visible_line_index = self.editor.index("@0,0")
        last_doc_line_index = self.editor.index("end-1c")
        
        try:
            last_doc_line_num = int(last_doc_line_index.split('.')[0])
            if last_doc_line_index == "1.0" and not self.editor.get("1.0", "1.end"):
                 last_doc_line_num = 0
        except (ValueError, tk.TclError):
            last_doc_line_num = 0

        max_digits = len(str(last_doc_line_num)) if last_doc_line_num > 0 else 1
        required_width = self.font.measure("0" * max_digits) + 10
        if abs(self.winfo_width() - required_width) > 2:
             self.config(width=required_width)

        current_line_index = first_visible_line_index
        while True:
            dline = self.editor.dlineinfo(current_line_index)
            if dline is None: break
            x, y, width, height, baseline = dline
            line_num_str = current_line_index.split(".")[0]
            self.create_text(required_width - 5, y, anchor="ne",
                             text=line_num_str, font=self.font, fill=self.text_color)
            next_line_index = self.editor.index(f"{current_line_index}+1line")
            if next_line_index == current_line_index: break
            current_line_index = next_line_index
            if int(current_line_index.split('.')[0]) > last_doc_line_num + 100: break

class EditorTab(ttk.Frame):
    """Represents a single tab in the editor notebook."""
    def __init__(self, parent_notebook, file_path=None, schedule_heavy_updates_callback=None):
        super().__init__(parent_notebook)
        self.notebook = parent_notebook
        self.file_path = file_path
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback
        self.last_saved_content = "" if file_path else "\n"
        self.llm_buttons_frame = None
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
        
        self.editor.bind("<KeyRelease>", self.on_key_release)
        self.editor.bind("<Configure>", self.schedule_heavy_updates)
        
        # REMOVED: All previous Tab key bindings have been removed from this file.
        # The functionality is now handled globally and robustly in interface_shortcuts.py.

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
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.editor.delete("1.0", tk.END)
                    self.editor.insert("1.0", content)
                    self.last_saved_content = self.get_content()
                    self.update_tab_title()
                    self.editor.edit_reset()
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
        else:
            self.update_tab_title()

    def save_file(self, new_path=None):
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