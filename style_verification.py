#!/usr/bin/env python3
"""
Visual style verification for AutomaTeX panels.
Creates a demo window showing all panels to verify unified styling.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import ttkbootstrap as ttk
from app.panels.generation import GenerationPanel
from app.panels.rephrase import RephrasePanel
from app.panels.keywords import KeywordsPanel

def dummy_theme_getter(key, default):
    """Dummy theme getter for testing."""
    colors = {
        "treeview_bg": "#ffffff",
        "editor_fg": "#000000",
        "sel_bg": "#0078d4",
        "sel_fg": "#ffffff",
        "primary": "#0066cc"
    }
    return colors.get(key, default)

def dummy_callback(*args, **kwargs):
    """Dummy callback."""
    pass

def main():
    """Create demo window to visually verify panel styles."""
    
    # Create root window with professional theme
    root = ttk.Window("AutomaTeX - Style Verification", themename="cosmo")
    root.geometry("1000x800")
    root.configure(bg="#f8f9fa")
    
    # Create main container
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = ttk.Label(
        main_frame, 
        text="AutomaTeX Panel Style Verification", 
        font=("Segoe UI", 16, "bold"),
        foreground="#2c3e50"
    )
    title_label.pack(pady=(0, 20))
    
    # Create notebook for panels
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True)
    
    # Panel 1: Generation Panel
    gen_container = ttk.Frame(notebook)
    notebook.add(gen_container, text="Text Generation")
    
    gen_panel = GenerationPanel(
        gen_container,
        dummy_theme_getter,
        [("Sample prompt", "Sample response")],
        dummy_callback,
        dummy_callback,
        initial_prompt="Write a professional introduction paragraph"
    )
    
    # Panel 2: Rephrase Panel  
    reph_container = ttk.Frame(notebook)
    notebook.add(reph_container, text="Rephrase")
    
    reph_panel = RephrasePanel(
        reph_container,
        dummy_theme_getter,
        "This is some sample text that needs to be rephrased with a more professional tone.",
        dummy_callback
    )
    
    # Panel 3: Keywords Panel
    kw_container = ttk.Frame(notebook)
    notebook.add(kw_container, text="Keywords")
    
    kw_panel = KeywordsPanel(
        kw_container,
        dummy_theme_getter,
        "sample_document.tex"
    )
    
    # Add info label
    info_label = ttk.Label(
        main_frame,
        text="Visual verification: Check that all panels have consistent fonts, spacing, and button styles",
        font=("Segoe UI", 9),
        foreground="#7f8c8d"
    )
    info_label.pack(pady=(10, 0))
    
    print("=== Style Verification Window Opened ===")
    print("Please visually inspect the panels for:")
    print("1. Consistent font usage (no bold text)")
    print("2. Uniform spacing and padding")  
    print("3. Professional button styling")
    print("4. Clean, cohesive appearance")
    print("5. Proper use of StandardComponents")
    print("\nClose window when inspection is complete.")
    
    root.mainloop()

if __name__ == "__main__":
    main()