"""
This module contains the dialog for rephrasing text.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils import debug_console

def show_rephrase_dialog(root_window, theme_setting_getter_func, original_text, on_rephrase_callback, on_cancel_callback):
    """
    Displays an improved dialog for rephrasing text.
    Args:
        root_window (tk.Tk): The main Tkinter root window.
        theme_setting_getter_func (callable): Function to get theme settings.
        original_text (str): The text to be rephrased.
        on_rephrase_callback (callable): Called with the user's instruction when "Rephrase" is clicked.
                                         Signature: `(instruction)`.
        on_cancel_callback (callable): Called when the dialog is closed or "Cancel" is clicked.
    """
    debug_console.log("Opening improved rephrase dialog.", level='ACTION')
    dialog = tk.Toplevel(root_window)
    dialog.title("Rephrase Text")
    dialog.transient(root_window)
    dialog.grab_set()
    dialog.geometry("800x400")

    # --- Theme and Styling ---
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    dialog.configure(bg=dialog_bg);

    # --- Main Frame ---
    main_frame = ttk.Frame(dialog, padding=10)
    main_frame.pack(fill="both", expand=True)
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    # --- Instruction Entry ---
    instruction_frame = ttk.Frame(main_frame)
    instruction_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    ttk.Label(instruction_frame, text="Instruction:").pack(side="left", padx=(0, 5))
    instruction_entry = ttk.Entry(instruction_frame)
    instruction_entry.pack(side="left", fill="x", expand=True)
    instruction_entry.focus_set()

    # --- Original Text Display ---
    original_text_frame = ttk.LabelFrame(main_frame, text="Original Text", padding=5)
    original_text_frame.grid(row=1, column=0, sticky="nsew")
    original_text_frame.grid_rowconfigure(0, weight=1)
    original_text_frame.grid_columnconfigure(0, weight=1)
    
    original_text_widget = tk.Text(original_text_frame, wrap="word", bg=text_bg, fg=text_fg, font=("Segoe UI", 10), state="disabled")
    original_text_widget.grid(row=0, column=0, sticky="nsew")
    original_scrollbar = ttk.Scrollbar(original_text_frame, orient="vertical", command=original_text_widget.yview)
    original_scrollbar.grid(row=0, column=1, sticky="ns")
    original_text_widget.config(yscrollcommand=original_scrollbar.set)
    
    original_text_widget.config(state="normal")
    original_text_widget.insert("1.0", original_text)
    original_text_widget.config(state="disabled")

    # --- Buttons ---
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=2, column=0, sticky="e", pady=(10, 0))

    def _on_rephrase():
        instruction = instruction_entry.get().strip()
        if not instruction:
            messagebox.showwarning("Missing Instruction", "Please enter an instruction for rephrasing.", parent=dialog)
            return
        dialog.destroy()
        on_rephrase_callback(instruction)

    def _on_cancel():
        dialog.destroy()
        if on_cancel_callback:
            on_cancel_callback()

    rephrase_button = ttk.Button(button_frame, text="Rephrase (Enter)", command=_on_rephrase)
    rephrase_button.pack(side="left", padx=5)
    cancel_button = ttk.Button(button_frame, text="Cancel (Esc)", command=_on_cancel)
    cancel_button.pack(side="left")

    dialog.bind("<Return>", lambda e: _on_rephrase())
    dialog.bind("<Escape>", lambda e: _on_cancel())
    dialog.protocol("WM_DELETE_WINDOW", _on_cancel)

    dialog.wait_window()