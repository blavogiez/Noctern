"""
Demo script for the search functionality in AutomaTeX.
This script demonstrates how to use the search feature programmatically.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the parent directory to the path so we can import modules from the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from editor.search import SearchBar, SearchEngine


def demo_search():
    """Demonstrate the search functionality."""
    # Create a root window
    root = tk.Tk()
    root.title("Search Feature Demo")
    root.geometry("600x400")
    
    # Create a text widget with sample content
    text_widget = tk.Text(root, wrap="word", font=("Consolas", 12))
    text_widget.insert("1.0", """\
This is a demonstration of the search functionality in AutomaTeX.
The search feature allows you to quickly find text in your document.

Features include:
- Real-time search as you type
- Highlighting of all matches
- Navigation between matches
- Case-sensitive and case-insensitive search
- Keyboard shortcuts for quick access

To use the search feature:
1. Press Ctrl+F to open the search bar
2. Type the text you want to find
3. Use the navigation buttons to move between matches
4. Press Esc to close the search bar

The search functionality is designed to be fast and efficient,
even with large documents. It uses optimized algorithms to
ensure smooth performance.
""")
    
    # Add scrollbars
    scrollbar_y = ttk.Scrollbar(root, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar_y.set)
    
    # Pack widgets
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar_y.pack(side="right", fill="y")
    
    # Create search bar
    search_bar = SearchBar(root)
    
    # Add a button to show the search bar
    show_button = ttk.Button(
        root, 
        text="Show Search Bar (Ctrl+F)", 
        command=search_bar.show
    )
    show_button.pack(side="bottom", pady=10)
    
    # Bind Ctrl+F to show search bar
    root.bind("<Control-f>", lambda e: search_bar.show())
    
    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    demo_search()