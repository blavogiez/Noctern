"""
Diff Viewer Window for displaying version comparisons.
Simple and effective diff display following SOLID principles.
"""

import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional
from utils import debug_console


class IDiffViewer:
    """Interface for diff viewing components."""
    
    def show_diff(self, diff_content: str, title: str = "Version Comparison"):
        """Display diff content."""
        raise NotImplementedError


class SimpleDiffViewer(IDiffViewer):
    """Simple diff viewer window."""
    
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        self.diff_window: Optional[tk.Toplevel] = None
        debug_console.log("Simple diff viewer initialized", level='DEBUG')
    
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
        if self.parent_window:
            self.diff_window = tk.Toplevel(self.parent_window)
        else:
            self.diff_window = tk.Tk()
        
        self.diff_window.title(title)
        self.diff_window.geometry("800x600")
        
        # Configure window
        self.diff_window.transient(self.parent_window) if self.parent_window else None
        self.diff_window.grab_set() if self.parent_window else None
        
        # Create UI elements
        self._create_diff_ui()
        
        debug_console.log("Diff window created", level='DEBUG')
    
    def _create_diff_ui(self):
        """Create the diff UI elements."""
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


class DiffViewerFactory:
    """Factory for creating diff viewer instances."""
    
    @staticmethod
    def create_simple_viewer(parent_window=None) -> SimpleDiffViewer:
        """Create a simple diff viewer."""
        return SimpleDiffViewer(parent_window)
    
    @staticmethod
    def create_viewer_for_panel(parent_window=None) -> IDiffViewer:
        """Create appropriate diff viewer for panel use."""
        return SimpleDiffViewer(parent_window)