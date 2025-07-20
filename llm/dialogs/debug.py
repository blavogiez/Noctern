"""
This module contains the dialog for displaying LaTeX debugging information.
"""

import tkinter as tk
from tkinter import ttk

def show_debug_dialog(root_window, theme_getter, diff_content, log_content, ai_analysis):
    """
    Displays a dialog with the code diff, AI analysis, and raw error log.
    """
    dialog = tk.Toplevel(root_window)
    dialog.title("LaTeX Compilation Error Analysis")
    dialog.geometry("1000x700")
    dialog.transient(root_window)
    dialog.grab_set()

    # --- Theme ---
    bg_color = theme_getter("root_bg", "#f0f0f0")
    text_bg_color = theme_getter("editor_bg", "#ffffff")
    text_fg_color = theme_getter("editor_fg", "#000000")
    dialog.configure(bg=bg_color)

    # --- Paned Window ---
    main_pane = tk.PanedWindow(dialog, orient=tk.VERTICAL, sashrelief=tk.FLAT, bg=bg_color)
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)

    # --- Top Pane: Diff and AI Analysis ---
    top_pane = tk.PanedWindow(main_pane, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, bg=bg_color)
    main_pane.add(top_pane, stretch="always")

    # Diff View
    diff_frame = ttk.LabelFrame(top_pane, text="Code Changes (Diff)", padding=5)
    diff_text = tk.Text(diff_frame, wrap="word", bg=text_bg_color, fg=text_fg_color, font=("Consolas", 9))
    diff_text.insert("1.0", diff_content)
    diff_text.config(state="disabled")
    diff_text.pack(fill="both", expand=True)
    top_pane.add(diff_frame, stretch="always")

    # AI Analysis View
    ai_frame = ttk.LabelFrame(top_pane, text="AI Analysis", padding=5)
    ai_text = tk.Text(ai_frame, wrap="word", bg=text_bg_color, fg=text_fg_color, font=("Segoe UI", 10))
    ai_text.insert("1.0", ai_analysis)
    ai_text.config(state="disabled")
    ai_text.pack(fill="both", expand=True)
    top_pane.add(ai_frame, stretch="always")

    # --- Bottom Pane: Raw Log ---
    log_frame = ttk.LabelFrame(main_pane, text="Raw Error Log", padding=5)
    log_text = tk.Text(log_frame, wrap="word", bg=text_bg_color, fg=text_fg_color, font=("Consolas", 9))
    log_text.insert("1.0", log_content)
    log_text.config(state="disabled")
    log_text.pack(fill="both", expand=True)
    main_pane.add(log_frame, stretch="always")

    dialog.wait_window()
