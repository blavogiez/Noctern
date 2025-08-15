"""
This module contains the dialog for setting LLM keywords.
"""

import tkinter as tk
from tkinter import ttk
import os
from llm import keyword_history
from utils import debug_console

def show_set_llm_keywords_dialog(root_window, theme_setting_getter_func, file_path):
    """
    Displays a dialog for users to set or update keywords for a specific file.
    Args:
        root_window (tk.Tk): The main Tkinter root window.
        theme_setting_getter_func (callable): Function to get theme settings.
        file_path (str): The absolute path to the file being edited.
    """
    debug_console.log(f"Opening LLM keywords dialog for: {os.path.basename(file_path)}", level='ACTION')
    keyword_window = tk.Toplevel(root_window)
    keyword_window.title(f"Keywords for {os.path.basename(file_path)}")
    keyword_window.transient(root_window)
    keyword_window.grab_set()
    keyword_window.geometry("450x400") # Increased size for better visibility

    # Apply theme settings.
    keyword_window.configure(bg=theme_setting_getter_func("root_bg", "#f0f0f0"))
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")

    # Add a label to explicitly state which file is being edited
    file_label = ttk.Label(keyword_window, text=f"Editing keywords for: {os.path.basename(file_path)}", font=("Segoe UI", 9))
    file_label.pack(pady=(10, 0))

    ttk.Label(keyword_window, text="Enter keywords (one per line or comma-separated):").pack(pady=(10, 5))
    keyword_text_frame = ttk.Frame(keyword_window)
    keyword_text_frame.pack(pady=5, padx=10, fill="both", expand=True)
    keyword_text_frame.grid_rowconfigure(0, weight=1); keyword_text_frame.grid_columnconfigure(0, weight=1)
    
    keyword_text_widget = tk.Text(
        keyword_text_frame, height=10, width=45, font=("Segoe UI", 10),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg,
        insertbackground=insert_bg, relief=tk.FLAT, borderwidth=0, highlightthickness=0
    )
    keyword_text_widget.grid(row=0, column=0, sticky="nsew")
    keyword_scrollbar = ttk.Scrollbar(keyword_text_frame, orient="vertical", command=keyword_text_widget.yview)
    keyword_scrollbar.grid(row=0, column=1, sticky="ns")
    keyword_text_widget.config(yscrollcommand=keyword_scrollbar.set)
    
    # Pre-fill with current keywords for the given file.
    current_keywords = keyword_history.get_keywords_for_file(file_path)
    if current_keywords:
        keyword_text_widget.insert(tk.END, "\n".join(current_keywords))

    def save_keywords_action_internal(event=None):
        """
        Internal function to process and save the entered keywords for the file.
        Triggered by button click or Ctrl+Enter.
        """
        input_text = keyword_text_widget.get("1.0", tk.END).strip()
        # Split by newlines, then by commas, strip whitespace, and filter empty strings.
        new_keywords = []
        for line in input_text.split('\n'):
            for kw in line.split(','):
                stripped_kw = kw.strip()
                if stripped_kw:
                    new_keywords.append(stripped_kw)
        
        # Set the keywords for the specific file.
        keyword_history.set_keywords_for_file(file_path, new_keywords);
        
        debug_console.log(f"Saved keywords for {os.path.basename(file_path)}: {new_keywords}", level='SUCCESS')
        keyword_window.destroy() # Close the dialog.
        return "break" # Prevent default event handling

    ttk.Button(keyword_window, text="Save Keywords (Ctrl+Enter)", command=save_keywords_action_internal).pack(pady=10)
    
    # Bind Ctrl+Enter to the save action
    keyword_window.bind("<Control-Return>", save_keywords_action_internal)
    
    keyword_text_widget.focus_set() # Set initial focus.
    keyword_window.wait_window() # Block until dialog is closed.
