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
from llm import api_client
from llm import prompts as llm_prompts

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

    # --- Model Settings ---
    model_frame = ttk.LabelFrame(main_frame, text="Model Configuration", padding=10)
    model_frame.pack(fill="x", expand=True, pady=10)

    available_models = api_client.get_available_models()
    if not available_models:
        # If we can't fetch models, we add the currently saved ones as options
        # so the user can at least see what's configured.
        available_models = list(set(current_config.get(key) for key in current_config if key.startswith("model_")))

    model_vars = {}
    model_comboboxes = {} # To store combobox widgets for later update
    model_labels = {
        "model_completion": "Completion:",
        "model_generation": "Generation:",
        "model_rephrase": "Rephrase:",
        "model_debug": "Debug:",
        "model_style": "Style:"
    }

    def set_all_models_to(model_name):
        """Helper function to set all model variables to a specific model."""
        for key in model_vars:
            model_vars[key].set(model_name)
        debug_console.log(f"All models set to '{model_name}' in the UI.", level='INFO')

    for i, (key, label) in enumerate(model_labels.items()):
        ttk.Label(model_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=5)
        
        current_value = current_config.get(key, "default")
        model_vars[key] = tk.StringVar(value=current_value)
        
        combo = ttk.Combobox(model_frame, textvariable=model_vars[key], values=available_models, state="readonly")
        combo.grid(row=i, column=1, sticky="ew", padx=5, pady=5)
        model_comboboxes[key] = combo # Store the widget
        
        # Button to set all models to the value of this combobox
        set_all_button = ttk.Button(
            model_frame, 
            text="Set for All", 
            command=lambda m=model_vars[key]: set_all_models_to(m.get())
        )
        set_all_button.grid(row=i, column=2, padx=5, pady=5)

    # Add a button to open the global prompts editor
    global_prompts_button = ttk.Button(
        model_frame, 
        text="Manage Global Prompts...", 
        command=llm_prompts.open_global_prompts_editor
    )
    global_prompts_button.grid(row=len(model_labels), column=0, columnspan=3, pady=10)

    model_frame.columnconfigure(1, weight=1)

    # --- API Keys ---
    api_frame = ttk.LabelFrame(main_frame, text="API Keys", padding=10)
    api_frame.pack(fill="x", expand=True, pady=10)

    ttk.Label(api_frame, text="Google Gemini API Key:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    gemini_api_key_var = tk.StringVar(value=current_config.get("gemini_api_key", ""))
    gemini_api_key_entry = ttk.Entry(api_frame, textvariable=gemini_api_key_var)
    gemini_api_key_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    
    api_frame.columnconfigure(1, weight=1)

    def refresh_models_command():
        """Saves the API key and refreshes the model list in the UI."""
        # 1. Save the current API key to the config file so the client can see it
        temp_config = app_config.load_config()
        temp_config["gemini_api_key"] = gemini_api_key_var.get()
        app_config.save_config(temp_config)

        # 2. Fetch the new, updated list of models
        new_models = api_client.get_available_models()
        debug_console.log(f"Model list refreshed. Found: {new_models}", level='INFO')

        # 3. Update all model comboboxes with the new list
        for key, combo in model_comboboxes.items():
            current_selection = combo.get()
            combo['values'] = new_models
            if current_selection in new_models:
                combo.set(current_selection)
            elif new_models:
                combo.set(new_models[0])
            else:
                combo.set('')
        
        from tkinter import messagebox
        messagebox.showinfo("Models Refreshed", f"Found {len(new_models)} available models.", parent=settings_win)

    refresh_button = ttk.Button(api_frame, text="Verify and Refresh Models", command=refresh_models_command)
    refresh_button.grid(row=0, column=2, padx=5, pady=5)

    # --- Monitor Settings ---
    monitor_frame = ttk.LabelFrame(main_frame, text="Display Settings", padding=10)
    monitor_frame.pack(fill="x", expand=True, pady=10)

    monitors = screen.get_monitors()
    monitor_names = [f"Monitor {i+1}: {m.width}x{m.height}" for i, m in enumerate(monitors)]
    
    ttk.Label(monitor_frame, text="Application Monitor:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    app_monitor_var = tk.StringVar(value=current_config.get("app_monitor", monitor_names[0] if monitor_names else "Default"))
    app_monitor_combo = ttk.Combobox(monitor_frame, textvariable=app_monitor_var, values=monitor_names, state="readonly")
    app_monitor_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

    ttk.Label(monitor_frame, text="PDF Viewer Monitor:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    pdf_monitor_var = tk.StringVar(value=current_config.get("pdf_monitor", monitor_names[0] if monitor_names else "Default"))
    pdf_monitor_combo = ttk.Combobox(monitor_frame, textvariable=pdf_monitor_var, values=monitor_names, state="readonly")
    pdf_monitor_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

    identify_button = ttk.Button(monitor_frame, text="Identify Screens", command=lambda: screen.show_screen_numbers(settings_win))
    identify_button.grid(row=2, column=0, columnspan=2, pady=10)

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
        updated_config = app_config.load_config()
        
        updated_config["app_monitor"] = app_monitor_var.get()
        updated_config["pdf_monitor"] = pdf_monitor_var.get()
        updated_config["window_state"] = window_state_var.get()
        updated_config["gemini_api_key"] = gemini_api_key_var.get()
        for key, var in model_vars.items():
            updated_config[key] = var.get()
        
        app_config.save_config(updated_config)
        debug_console.log("Settings saved.", level='SUCCESS')
        settings_win.destroy()
        
        from tkinter import messagebox
        messagebox.showinfo("Settings Saved", "Your new settings have been saved. Some changes may require a restart to take effect.", parent=root)

    ttk.Button(button_frame, text="Save", command=save_and_close).grid(row=0, column=0, padx=5, sticky="e")
    ttk.Button(button_frame, text="Cancel", command=settings_win.destroy).grid(row=0, column=1, padx=5, sticky="w")

    model_frame.columnconfigure(1, weight=1)
    monitor_frame.columnconfigure(1, weight=1)
    window_frame.columnconfigure(1, weight=1)
    
    settings_win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (settings_win.winfo_width() // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (settings_win.winfo_height() // 2)
    settings_win.geometry(f"+{x}+{y}")