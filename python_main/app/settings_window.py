"""
This module creates and manages the application's settings window, allowing users
to configure various aspects of the application's behavior, such as display
settings and default window states.
"""

import tkinter as tk
from tkinter import ttk
from utils import screen
from app import config as app_config
from utils import debug_console

def open_settings_window(root):
    """
    Opens the application settings window as a Toplevel window.

    Args:
        root (tk.Tk): The root Tkinter window of the application.
    """
    settings_win = tk.Toplevel(root)
    settings_win.title("Settings")
    settings_win.transient(root)
    settings_win.grab_set()
    settings_win.resizable(False, False)

    main_frame = ttk.Frame(settings_win, padding=20)
    main_frame.pack(fill="both", expand=True)

    # --- Load Current Config ---
    current_config = app_config.load_config()

    # --- Monitor Settings ---
    monitor_frame = ttk.LabelFrame(main_frame, text="Display Settings", padding=10)
    monitor_frame.pack(fill="x", expand=True, pady=10)

    monitors = screen.get_monitors()
    monitor_names = [f"Monitor {i+1}: {m.width}x{m.height}" for i, m in enumerate(monitors)]
    
    # App Monitor Setting
    ttk.Label(monitor_frame, text="Application Monitor:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    app_monitor_var = tk.StringVar(value=current_config.get("app_monitor", monitor_names[0] if monitor_names else "Default"))
    app_monitor_combo = ttk.Combobox(monitor_frame, textvariable=app_monitor_var, values=monitor_names, state="readonly")
    app_monitor_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

    # PDF Viewer Monitor Setting
    ttk.Label(monitor_frame, text="PDF Viewer Monitor:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    pdf_monitor_var = tk.StringVar(value=current_config.get("pdf_monitor", monitor_names[0] if monitor_names else "Default"))
    pdf_monitor_combo = ttk.Combobox(monitor_frame, textvariable=pdf_monitor_var, values=monitor_names, state="readonly")
    pdf_monitor_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

    # --- Window State Settings ---
    window_frame = ttk.LabelFrame(main_frame, text="Window Startup State", padding=10)
    window_frame.pack(fill="x", expand=True, pady=10)

    window_states = ["Normal", "Maximized", "Fullscreen"]
    window_state_var = tk.StringVar(value=current_config.get("window_state", "Normal"))
    
    ttk.Label(window_frame, text="Startup State:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    window_state_combo = ttk.Combobox(window_frame, textvariable=window_state_var, values=window_states, state="readonly")
    window_state_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

    # --- Save and Cancel Buttons ---
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=(20, 0))
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)

    def save_and_close():
        """Saves the settings and closes the window."""
        # Load the most recent config to preserve other settings
        updated_config = app_config.load_config()
        
        # Update values from the dialog
        updated_config["app_monitor"] = app_monitor_var.get()
        updated_config["pdf_monitor"] = pdf_monitor_var.get()
        updated_config["window_state"] = window_state_var.get()
        
        app_config.save_config(updated_config)
        debug_console.log("Settings saved.", level='SUCCESS')
        settings_win.destroy()
        
        # Optionally, notify the user that a restart is needed
        from tkinter import messagebox
        messagebox.showinfo("Settings Saved", "Your new settings have been saved. Some changes may require a restart to take effect.", parent=root)


    ttk.Button(button_frame, text="Save", command=save_and_close).grid(row=0, column=0, padx=5, sticky="e")
    ttk.Button(button_frame, text="Cancel", command=settings_win.destroy).grid(row=0, column=1, padx=5, sticky="w")

    monitor_frame.columnconfigure(1, weight=1)
    window_frame.columnconfigure(1, weight=1)
    
    settings_win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (settings_win.winfo_width() // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (settings_win.winfo_height() // 2)
    settings_win.geometry(f"+{x}+{y}")
