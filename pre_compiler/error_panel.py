"""
Simple error panel for displaying LaTeX compilation errors.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext


class ErrorPanel(ttk.Frame):
    """Simple error display panel."""
    
    def __init__(self, parent, on_goto_line=None):
        super().__init__(parent)
        self.on_goto_line = on_goto_line
        
        self.pack(fill="both", expand=True)
        
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="LaTeX Compilation Errors", 
                 font=("Segoe UI", 10)).pack(side="left")
        
        # Clear button
        ttk.Button(header_frame, text="Clear", 
                  command=self.clear_errors).pack(side="right")
        
        # Error display
        self.error_text = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=("Consolas", 9),
            height=10
        )
        self.error_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def clear_errors(self):
        """Clear the error display."""
        self.error_text.delete(1.0, tk.END)
        
    def display_errors(self, error_text):
        """Display error text."""
        self.error_text.delete(1.0, tk.END)
        self.error_text.insert(1.0, error_text)