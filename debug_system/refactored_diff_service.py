"""
Diff generation service for comparing current and last successful compilation.
Provides diff viewing capabilities integrated with the existing cache system.
"""

import os
import difflib
from typing import Optional, Tuple
from utils import debug_console
from debug_system.core import DiffGenerator


class CachedDiffGenerator(DiffGenerator):
    """Generates diffs using the existing cache system from compilation."""
    
    def __init__(self):
        """Initialize the diff generator with cache integration."""
        self.output_directory = "output"
        debug_console.log("Cached diff generator initialized", level='DEBUG')
    
    def analyze_current_vs_last_successful(self, file_path: str, current_content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Analyze current content vs last successful version.
        
        Returns:
            tuple: (has_previous, diff_content, last_content)
        """
        debug_console.log(f"Analyzing diff for {file_path}", level='INFO')
        
        if not file_path:
            debug_console.log("No file path provided for diff analysis", level='WARNING')
            return False, None, None
        
        try:
            # Get cached file path
            file_name = os.path.basename(file_path)
            cached_file_path = os.path.join(self.output_directory, f"cached_{file_name}")
            
            if not os.path.exists(cached_file_path):
                debug_console.log(f"No cached version found at {cached_file_path}", level='INFO')
                return False, None, None
            
            # Load cached content
            with open(cached_file_path, 'r', encoding='utf-8') as f:
                last_content = f.read()
            
            debug_console.log(f"Loaded cached version from {cached_file_path} ({len(last_content)} chars)", level='DEBUG')
            
            # Generate diff
            diff_lines = list(difflib.unified_diff(
                last_content.splitlines(keepends=True),
                current_content.splitlines(keepends=True),
                fromfile="last_successful",
                tofile="current",
                lineterm=""
            ))
            
            if not diff_lines:
                debug_console.log("No differences found between versions", level='INFO')
                return True, "", last_content
            
            diff_content = ''.join(diff_lines)
            debug_console.log(f"Generated diff ({len(diff_content)} chars)", level='DEBUG')
            
            debug_console.log("Differences found - diff generated", level='INFO')
            return True, diff_content, last_content
            
        except Exception as e:
            debug_console.log(f"Error analyzing diff: {e}", level='ERROR')
            return False, None, None
    
    def display_diff(self, diff_content: str, parent_window=None):
        """Display diff content to user."""
        if not diff_content.strip():
            debug_console.log("No diff content to display", level='DEBUG')
            return
        
        try:
            from debug_system.refactored_diff_service import DiffViewer
            
            debug_console.log("Opening diff viewer window", level='INFO')
            debug_console.log(f"Diff summary: {len(diff_content.splitlines())} lines changed", level='INFO')
            
            # Create and show diff viewer
            diff_viewer = DiffViewer(parent_window)
            diff_viewer.show_diff(diff_content, "Compare with Last Successful Version")
            
        except Exception as e:
            debug_console.log(f"Error displaying diff: {e}", level='ERROR')


class DiffViewer:
    """Simple diff viewer window for displaying version comparisons."""
    
    def __init__(self, parent_window=None):
        """Initialize the diff viewer."""
        self.parent_window = parent_window
        self.diff_window = None
        debug_console.log("Diff viewer initialized", level='DEBUG')
    
    def show_diff(self, diff_content: str, title: str = "Version Comparison"):
        """Display diff content in a new window."""
        try:
            # Create or reuse diff window
            if self.diff_window is None or not self.diff_window.winfo_exists():
                self._create_diff_window(title)
            else:
                # Bring existing window to front
                self.diff_window.lift()
                self.diff_window.focus_force()
            
            # Clear and populate content
            self._populate_diff_content(diff_content)
            
            debug_console.log(f"Displayed diff with {len(diff_content)} characters", level='INFO')
            
        except Exception as e:
            debug_console.log(f"Error showing diff: {e}", level='ERROR')
    
    def _create_diff_window(self, title: str):
        """Create the diff window."""
        import tkinter as tk
        import ttkbootstrap as ttk
        
        if self.parent_window:
            self.diff_window = tk.Toplevel(self.parent_window)
        else:
            self.diff_window = tk.Tk()
        
        self.diff_window.title(title)
        self.diff_window.geometry("800x600")
        
        # Configure window
        if self.parent_window:
            self.diff_window.transient(self.parent_window)
            self.diff_window.grab_set()
        
        # Create UI elements
        self._create_diff_ui()
        
        debug_console.log("Diff window created", level='DEBUG')
    
    def _create_diff_ui(self):
        """Create the diff UI elements."""
        import tkinter as tk
        import ttkbootstrap as ttk
        
        # Header frame
        header_frame = ttk.Frame(self.diff_window)
        header_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = ttk.Label(
            header_frame, 
            text="Comparison with Last Successful Version",
            font=('Arial', 12, 'bold')
        )
        title_label.pack(side='left')
        
        close_btn = ttk.Button(
            header_frame,
            text="Close",
            command=self._close_window,
            style='Outline.TButton'
        )
        close_btn.pack(side='right')
        
        # Separator
        separator = ttk.Separator(self.diff_window, orient='horizontal')
        separator.pack(fill='x', padx=10, pady=5)
        
        # Main content frame
        content_frame = ttk.Frame(self.diff_window)
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill='both', expand=True)
        
        self.text_widget = tk.Text(
            text_frame,
            wrap='none',
            font=('Consolas', 10),
            bg='#f8f8f8',
            fg='#333333',
            relief='flat',
            borderwidth=1
        )
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.text_widget.yview)
        h_scrollbar = ttk.Scrollbar(text_frame, orient='horizontal', command=self.text_widget.xview)
        
        self.text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and text
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        self.text_widget.pack(side='left', fill='both', expand=True)
        
        # Configure text tags for diff syntax highlighting
        self.text_widget.tag_configure('added', foreground='#2e7d32', background='#e8f5e8')
        self.text_widget.tag_configure('removed', foreground='#d32f2f', background='#fdeaea')
        self.text_widget.tag_configure('context', foreground='#666666')
        self.text_widget.tag_configure('header', foreground='#1976d2', font=('Consolas', 10, 'bold'))
        
        # Info frame
        info_frame = ttk.Frame(self.diff_window)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        info_label = ttk.Label(
            info_frame,
            text="Green = Added lines, Red = Removed lines, Blue = File headers",
            font=('Arial', 9),
            foreground='#666'
        )
        info_label.pack()
        
        # Bind close events
        self.diff_window.protocol("WM_DELETE_WINDOW", self._close_window)
        self.diff_window.bind('<Escape>', lambda e: self._close_window())
    
    def _populate_diff_content(self, diff_content: str):
        """Populate the text widget with diff content and syntax highlighting."""
        self.text_widget.delete('1.0', 'end')
        
        if not diff_content.strip():
            self.text_widget.insert('1.0', "No differences found between versions.")
            return
        
        lines = diff_content.splitlines()
        
        for line in lines:
            start_index = self.text_widget.index('end-1c')
            self.text_widget.insert('end', line + '\n')
            end_index = self.text_widget.index('end-1c')
            
            # Apply syntax highlighting based on line prefix
            if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
                self.text_widget.tag_add('header', start_index, end_index)
            elif line.startswith('+'):
                self.text_widget.tag_add('added', start_index, end_index)
            elif line.startswith('-'):
                self.text_widget.tag_add('removed', start_index, end_index)
            else:
                self.text_widget.tag_add('context', start_index, end_index)
        
        # Make text read-only
        self.text_widget.configure(state='disabled')
    
    def _close_window(self):
        """Close the diff window."""
        if self.diff_window:
            self.diff_window.destroy()
            self.diff_window = None
        debug_console.log("Diff window closed", level='DEBUG')