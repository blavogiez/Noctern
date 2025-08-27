"""Simple line numbers component based on working version"""

import tkinter as tk


class LineNumbers(tk.Canvas):
    """Simple line numbers canvas with optimized rendering"""

    def __init__(self, master, editor_widget, font, **kwargs):
        super().__init__(master, **kwargs)
        self.editor = editor_widget
        self.font = font
        self.text_color = "#505050"  # Darker default for better contrast
        self.bg_color = "#f8f8f8"   # Slightly lighter background
        self.config(width=40, bg=self.bg_color, highlightthickness=0, bd=0)
        
        # Performance optimization caches
        self._last_viewport = (0, 0)
        self._last_total_lines = 0
        self._last_width = 40
        self._rendered_numbers = {}
        self._last_content_hash = ""

    def update_theme(self, text_color, bg_color):
        self.text_color = text_color
        self.bg_color = bg_color
        self.config(bg=self.bg_color)
        self.redraw()

    def redraw(self, *args):
        """Draw line numbers with viewport detection"""
        print(f"[DEBUG] redraw() called")
        try:
            if not self.editor or not self.winfo_exists():
                print(f"[DEBUG] Editor not available or widget destroyed")
                return
            
            # Get current viewport and document stats
            first_visible_line = self.editor.index("@0,0")
            last_char = self.editor.index("end-1c")
            last_line_num = int(last_char.split('.')[0]) if last_char != "1.0" or self.editor.get("1.0", "1.end") else 0
            
            print(f"[DEBUG] Total lines: {last_line_num}")
            
            if last_line_num == 0:
                self.delete("all")
                return
            
            # Parse current viewport
            first_line_num = int(first_visible_line.split('.')[0])
            current_viewport = (first_line_num, last_line_num)
            
            print(f"[DEBUG] Current viewport: {current_viewport}, Last viewport: {self._last_viewport}")
            print(f"[DEBUG] Current total: {last_line_num}, Last total: {self._last_total_lines}")
            
            # Check if we can skip expensive operations
            should_skip = self._should_skip_redraw(current_viewport, last_line_num)
            print(f"[DEBUG] Should skip redraw: {should_skip}")
            if should_skip:
                return
            
            print(f"[DEBUG] Actually redrawing line numbers!")
            
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
            
            print(f"[DEBUG] Redraw completed successfully")
            
        except tk.TclError as e:
            print(f"[DEBUG] TclError in redraw: {e}")
        except Exception as e:
            print(f"[DEBUG] Error in redraw: {e}")
    
    def force_update(self):
        """Force an immediate update of the line numbers"""
        # Reset the cache to ensure a full redraw
        self._last_viewport = (0, 0)
        self._last_total_lines = 0
        self.redraw()
    
    def _should_skip_redraw(self, current_viewport, total_lines):
        """Skip redraw only if viewport and line count unchanged"""
        old_start, old_total = self._last_viewport[0], self._last_total_lines
        new_start, _ = current_viewport
        
        # Always redraw if line count changed
        if total_lines != old_total:
            return False
            
        # For scrolling, we need to be more sensitive
        return new_start == old_start
    
    def _redraw_viewport_optimized(self, first_visible_line, required_width):
        """Optimized redraw for large files - only visible area"""
        self.delete("all")
        self._rendered_numbers.clear()
        
        # Get visible area bounds
        try:
            canvas_height = self.winfo_height()
            line_height = self.font.metrics("linespace")
            max_visible_lines = min(100, canvas_height // line_height + 5)
            
            current_line = first_visible_line
            lines_drawn = 0
            
            while lines_drawn < max_visible_lines:
                try:
                    dline = self.editor.dlineinfo(current_line)
                    if not dline:
                        break
                        
                    y = dline[1]
                    if y > canvas_height + 50:
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
        """Standard redraw for smaller files"""
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
        """Force complete redraw, ignoring cache"""
        self._last_viewport = (0, 0)
        self._last_total_lines = 0
        self._rendered_numbers.clear()
        self.redraw()