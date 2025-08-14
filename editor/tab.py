"""
This module defines the `LineNumbers` and `EditorTab` classes, which are core components
of the text editor interface.
"""
import re
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
import os
from tkinter import messagebox
from utils import debug_console
from editor.image_preview import ImagePreview
from editor.shortcuts import setup_editor_shortcuts # Correct import

class LineNumbers(tk.Canvas):
    """Optimized line numbers canvas with caching and viewport-based rendering."""
    def __init__(self, master, editor_widget, font, **kwargs):
        super().__init__(master, **kwargs)
        self.editor = editor_widget
        self.font = font
        self.text_color = "#6a737d"
        self.bg_color = "#f0f0f0"
        self.config(width=40, bg=self.bg_color, highlightthickness=0, bd=0)
        
        # Performance optimization caches
        self._last_viewport = (0, 0)
        self._last_total_lines = 0
        self._last_width = 40
        self._rendered_numbers = {}  # y_position -> line_number for incremental updates
        self._last_content_hash = ""

    def update_theme(self, text_color, bg_color):
        self.text_color = text_color
        self.bg_color = bg_color
        self.config(bg=self.bg_color)
        self.redraw()

    def redraw(self, *args):
        """Optimized redraw with viewport detection and incremental updates."""
        try:
            if not self.editor or not self.winfo_exists():
                return
            
            # Get current viewport and document stats
            first_visible_line = self.editor.index("@0,0")
            last_char = self.editor.index("end-1c")
            last_line_num = int(last_char.split('.')[0]) if last_char != "1.0" or self.editor.get("1.0", "1.end") else 0
            
            if last_line_num == 0:
                self.delete("all")
                return
            
            # Parse current viewport
            first_line_num = int(first_visible_line.split('.')[0])
            current_viewport = (first_line_num, last_line_num)
            
            # Check if we can skip expensive operations
            if self._should_skip_redraw(current_viewport, last_line_num):
                return
            
            # Calculate required width
            max_digits = len(str(last_line_num))
            required_width = self.font.measure("0" * max_digits) + 10
            
            # Only resize if significantly different
            if abs(self.winfo_width() - required_width) > 5:
                self.config(width=required_width)
                self._last_width = required_width
            else:
                required_width = self._last_width
            
            # For large files (>2000 lines), use optimized rendering
            if last_line_num > 2000:
                self._redraw_viewport_optimized(first_visible_line, required_width)
            else:
                self._redraw_standard(first_visible_line, last_line_num, required_width)
            
            # Update cache
            self._last_viewport = current_viewport
            self._last_total_lines = last_line_num
            
        except tk.TclError:
            # Editor might be destroyed
            pass
    
    def force_update(self):
        """Force an immediate update of the line numbers."""
        # Reset the cache to ensure a full redraw
        self._last_viewport = (0, 0)
        self._last_total_lines = 0
        self.redraw()
    
    def _should_skip_redraw(self, current_viewport, total_lines):
        """Determine if redraw can be skipped based on viewport changes."""
        old_start, old_total = self._last_viewport[0], self._last_total_lines
        new_start, _ = current_viewport
        
        # Always redraw if line count changed
        if total_lines != old_total:
            return False
            
        # For scrolling, we need to be more sensitive
        # Even small viewport changes should trigger a redraw
        return new_start == old_start
    
    def _redraw_viewport_optimized(self, first_visible_line, required_width):
        """Optimized redraw for large files - only visible area."""
        self.delete("all")
        self._rendered_numbers.clear()
        
        # Get visible area bounds
        try:
            canvas_height = self.winfo_height()
            line_height = self.font.metrics("linespace")
            max_visible_lines = min(100, canvas_height // line_height + 5)  # Safety limit
            
            current_line = first_visible_line
            lines_drawn = 0
            
            while lines_drawn < max_visible_lines:
                try:
                    dline = self.editor.dlineinfo(current_line)
                    if not dline:
                        break
                        
                    y = dline[1]
                    if y > canvas_height + 50:  # Off-screen buffer
                        break
                        
                    line_num_str = current_line.split(".")[0]
                    self.create_text(required_width - 5, y, anchor="ne", 
                                   text=line_num_str, font=self.font, fill=self.text_color)
                    
                    self._rendered_numbers[y] = line_num_str
                    current_line = self.editor.index(f"{current_line}+1line")
                    lines_drawn += 1
                    
                except tk.TclError:
                    break
                    
        except tk.TclError:
            pass
    
    def _redraw_standard(self, first_visible_line, last_line_num, required_width):
        """Standard redraw for smaller files."""
        self.delete("all")
        self._rendered_numbers.clear()
        
        current_line = first_visible_line
        while True:
            try:
                dline = self.editor.dlineinfo(current_line)
                if not dline:
                    break
                    
                y = dline[1]
                line_num_str = current_line.split(".")[0]
                self.create_text(required_width - 5, y, anchor="ne", 
                               text=line_num_str, font=self.font, fill=self.text_color)
                
                self._rendered_numbers[y] = line_num_str
                current_line = self.editor.index(f"{current_line}+1line")
                
                if int(current_line.split('.')[0]) > last_line_num + 1:
                    break
                    
            except tk.TclError:
                break
    
    def force_redraw(self):
        """Force complete redraw, ignoring cache."""
        self._last_viewport = (0, 0)
        self._last_total_lines = 0
        self._rendered_numbers.clear()
        self.redraw()

class EditorTab(ttk.Frame):
    """Represents a single editable tab."""
    def __init__(self, parent_notebook, file_path=None, schedule_heavy_updates_callback=None):
        super().__init__(parent_notebook)
        self.notebook = parent_notebook
        self.file_path = file_path
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback
        self.last_saved_content = ""
        self.editor_font = Font(family="Consolas", size=12)

        self.editor = tk.Text(self, wrap="word", font=self.editor_font, undo=True, relief=tk.FLAT, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.editor.yview)
        self.line_numbers = LineNumbers(self, editor_widget=self.editor, font=self.editor_font)
        
        self.line_numbers.pack(side="left", fill="y")
        self.scrollbar.pack(side="right", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)

        def sync_scroll_and_redraw(*args):
            self.scrollbar.set(*args)
            self.line_numbers.yview_moveto(self.editor.yview()[0])
            # Force update of line numbers when scrolling for perfect accuracy
            self.line_numbers.force_update()

        self.editor.config(yscrollcommand=sync_scroll_and_redraw)
        
        # Bind to scrollbar events for immediate updates
        self.scrollbar.bind("<ButtonRelease-1>", lambda e: self.line_numbers.force_update())
        self.scrollbar.bind("<B1-Motion>", lambda e: self.line_numbers.force_update())
        
        # Bind to mousewheel events for immediate updates
        self.editor.bind("<MouseWheel>", lambda e: self.line_numbers.force_update())
        
        self.editor.bind("<KeyRelease>", self.on_key_release)
        self.editor.bind("<Configure>", self.schedule_heavy_updates)
        # Marquer le widget comme modifié lors des changements
        self.editor.bind("<Key>", self._on_key_press)

        # Setup image preview functionality
        self.image_preview = ImagePreview(self, lambda: self.file_path)
        self.image_preview.attach_to_editor(self.editor)

        # Setup all editor shortcuts from the dedicated module
        setup_editor_shortcuts(self.editor)
        
        # Initialize Monaco-style optimization immediately
        try:
            from editor.monaco_optimizer import initialize_monaco_optimization
            initialize_monaco_optimization(self.editor)
        except ImportError:
            pass

    def on_key_release(self, event=None):
        self.update_tab_title()
        self._schedule_smart_updates(event, 'keyrelease')
        # Ensure line numbers are updated instantly
        self.line_numbers.redraw()
        # Note: syntax highlighting is already handled in _schedule_smart_updates

    def schedule_heavy_updates(self, event=None):
        """Legacy method - redirects to smart updates."""
        self._schedule_smart_updates(event, 'configure')
    
    def _schedule_smart_updates(self, event=None, event_type='general'):
        """ULTRA-FAST differential syntax highlighting - maximum performance."""
        try:
            from editor import syntax as editor_syntax
            
            if event_type == 'keyrelease':
                # DIFFERENTIAL HIGHLIGHTING: Only recolor changed lines
                editor_syntax.apply_differential_syntax_highlighting(self.editor)
                # Always update line numbers on key release for instant feedback
                self.line_numbers.redraw()
                
            elif event_type == 'configure':
                # For viewport changes, just redraw line numbers
                self.line_numbers.redraw()
                
            # Skip heavy outline updates unless truly needed
            
        except ImportError:
            # Fallback without syntax highlighting
            pass

    def _on_key_press(self, event=None):
        """Marque le widget comme modifié lors des changements."""
        self.editor.edit_modified(True)

    def _schedule_syntax_update(self):
        """Schedule syntax highlighting update with smart debouncing."""
        try:
            from editor import syntax as editor_syntax
            editor_syntax.schedule_syntax_update(self.editor, debounce=True, smart=True)
        except ImportError:
            # Fallback if syntax module is not available
            pass

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
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
        else:
            self.last_saved_content = "\n"
        
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", content)
        self.last_saved_content = self.get_content()
        self.update_tab_title()
        self.editor.edit_reset()
        
        # Initialize syntax highlighting for the loaded file
        try:
            from editor import syntax as editor_syntax
            editor_syntax.initialize_syntax_highlighting(self.editor)
        except ImportError:
            pass

    def save_file(self, new_path=None):
        if new_path: self.file_path = new_path
        if not self.file_path: return False
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(self.get_content())
            self.last_saved_content = self.get_content()
            self.update_tab_title()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{e}")
            return False
