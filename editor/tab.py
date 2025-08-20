"""Define LineNumbers and EditorTab classes for text editor interface."""
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
        """Production-ready redraw with comprehensive error handling and optimization"""
        try:
            # Safety checks
            if not self.editor or not self.winfo_exists():
                return
            
            # Get current document state with error handling
            try:
                first_visible_line = self.editor.index("@0,0")
                last_char = self.editor.index("end-1c")
                last_line_num = int(last_char.split('.')[0]) if last_char != "1.0" or self.editor.get("1.0", "1.end") else 0
            except (tk.TclError, ValueError, AttributeError):
                return
            
            # Handle empty document
            if last_line_num <= 0:
                self.delete("all")
                return
            
            # Calculate viewport with bounds checking
            try:
                first_line_num = max(1, int(first_visible_line.split('.')[0]))
                current_viewport = (first_line_num, last_line_num)
            except (ValueError, IndexError):
                current_viewport = (1, last_line_num)
            
            # Smart skip logic for performance
            if self._should_skip_redraw(current_viewport, last_line_num):
                return
            
            # Calculate optimal width with caching
            max_digits = len(str(last_line_num))
            required_width = max(40, self.font.measure("9" * max_digits) + 15)  # Buffer for padding
            
            # Efficient width updates
            current_width = self.winfo_width()
            if abs(current_width - required_width) > 3:  # Reduced threshold for smoother resizing
                self.config(width=required_width)
                self._last_width = required_width
            else:
                required_width = current_width
            
            # Adaptive rendering based on file size
            if last_line_num > 2000:
                self._render_large_file(first_visible_line, required_width)
            elif last_line_num > 100:
                self._render_medium_file(first_visible_line, last_line_num, required_width)
            else:
                self._render_small_file(first_visible_line, last_line_num, required_width)
            
            # Update state cache
            self._last_viewport = current_viewport
            self._last_total_lines = last_line_num
            
        except Exception as e:
            # Production error handling - log and continue
            try:
                from utils import debug_console
                debug_console.log(f"Line numbers redraw error: {e}", level='WARNING')
            except:
                pass
    
    def force_update(self):
        """Force an immediate update of the line numbers."""
        # Reset the cache to ensure a full redraw
        self._last_viewport = (0, 0)
        self._last_total_lines = 0
        self.redraw()
    
    def _should_skip_redraw(self, current_viewport, total_lines):
        """Smart redraw logic optimized for production performance"""
        old_start, old_total = self._last_viewport[0], self._last_total_lines
        new_start, _ = current_viewport
        
        # Always redraw if line count changed (new lines added/removed)
        if total_lines != old_total:
            return False
            
        # Skip redraw if viewport hasn't changed significantly (optimization)
        viewport_change_threshold = max(1, total_lines // 100)  # 1% threshold or min 1
        if abs(new_start - old_start) < viewport_change_threshold:
            return True
            
        return False
    
    def _render_large_file(self, first_visible_line, required_width):
        """Render line numbers for large files with viewport optimization"""
        self.delete("all")
        self._rendered_numbers.clear()
        
        try:
            canvas_height = self.winfo_height()
            line_height = self.font.metrics("linespace")
            max_visible_lines = min(150, canvas_height // line_height + 10)  # Extended buffer for large files
            
            current_line = first_visible_line
            lines_drawn = 0
            
            while lines_drawn < max_visible_lines:
                try:
                    dline = self.editor.dlineinfo(current_line)
                    if not dline:
                        break
                        
                    y = dline[1]
                    if y > canvas_height + 100:  # Extended off-screen buffer
                        break
                        
                    line_num_str = current_line.split(".")[0]
                    self.create_text(required_width - 8, y + dline[3] // 2, anchor="e", 
                                   text=line_num_str, font=self.font, fill=self.text_color)
                    
                    self._rendered_numbers[y] = line_num_str
                    current_line = self.editor.index(f"{current_line}+1line")
                    lines_drawn += 1
                    
                except tk.TclError:
                    break
                    
        except (tk.TclError, ZeroDivisionError):
            pass
    
    def _render_medium_file(self, first_visible_line, last_line_num, required_width):
        """Render line numbers for medium files with balanced performance"""
        self.delete("all")
        self._rendered_numbers.clear()
        
        try:
            # Calculate visible range with buffer for smooth scrolling
            canvas_height = self.winfo_height()
            buffer_lines = max(5, canvas_height // 20)  # Adaptive buffer based on canvas height
            
            start_line_num = max(1, int(first_visible_line.split('.')[0]) - buffer_lines)
            end_line_num = min(last_line_num, int(first_visible_line.split('.')[0]) + canvas_height // 16 + buffer_lines)
            
            for line_num in range(start_line_num, end_line_num + 1):
                try:
                    line_index = f"{line_num}.0"
                    dline = self.editor.dlineinfo(line_index)
                    if not dline:
                        continue
                        
                    y = dline[1] + dline[3] // 2  # Center vertically in line
                    if -50 <= y <= canvas_height + 50:  # Render buffer zone
                        self.create_text(required_width - 8, y, anchor="e", 
                                       text=str(line_num), font=self.font, fill=self.text_color)
                        self._rendered_numbers[y] = str(line_num)
                        
                except tk.TclError:
                    continue
                    
        except (tk.TclError, ValueError, ZeroDivisionError):
            pass
    
    def _render_small_file(self, first_visible_line, last_line_num, required_width):
        """Render line numbers for small files with full document rendering"""
        self.delete("all")
        self._rendered_numbers.clear()
        
        try:
            # Render all lines for small files - performance is not critical
            for line_num in range(1, last_line_num + 1):
                try:
                    line_index = f"{line_num}.0"
                    dline = self.editor.dlineinfo(line_index)
                    if not dline:
                        continue
                        
                    y = dline[1] + dline[3] // 2  # Center vertically in line
                    self.create_text(required_width - 8, y, anchor="e", 
                                   text=str(line_num), font=self.font, fill=self.text_color)
                    self._rendered_numbers[y] = str(line_num)
                    
                except tk.TclError:
                    continue
                    
        except (tk.TclError, ValueError):
            pass
    
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
        # Load font from configuration
        from app import config as app_config
        config_dict = app_config.load_config()
        font_settings = app_config.get_editor_font_settings(config_dict)
        
        self.editor_font = Font(family=font_settings["family"], size=font_settings["size"])

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
        # Tab title and line numbers are now handled in main_window.py on_text_modified
        # Only handle syntax highlighting here to avoid duplication
        self._schedule_smart_updates(event, 'keyrelease')

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
        # Use "end-1c" to exclude the automatic trailing newline that Tkinter adds
        return self.editor.get("1.0", "end-1c")

    def is_dirty(self):
        current_content = self.get_content()
        return current_content != self.last_saved_content

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
            self.last_saved_content = ""
        
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
