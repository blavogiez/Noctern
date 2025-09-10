"""
This module creates and manages the application's settings window, allowing users
to configure various aspects of the application's behavior, such as display
settings and default window states.
"""

import tkinter as tk
from tkinter import ttk
from utils import screen
from app import config as app_config
from utils import logs_console
from llm import api_client
from llm import prompts as llm_prompts
from app.panels import show_global_prompts_panel

def open_settings_window(root):
    """
    Opens the application settings window as a Toplevel window.

    Args:
        root (tk.Tk): The root Tkinter window of the application.
    """
    settings_win = tk.Toplevel(root)
    settings_win.title("Noctern Settings")
    settings_win.transient(root)
    settings_win.grab_set()
    settings_win.resizable(False, False)
    
    # Set minimum window size for better proportions
    settings_win.minsize(520, 600)

    main_frame = ttk.Frame(settings_win, padding=24)
    main_frame.pack(fill="both", expand=True)

    # --- Load Current Config ---
    current_config = app_config.load_config()

    # --- Display Settings ---
    display_frame = ttk.LabelFrame(main_frame, text="Display Settings", padding=16)
    display_frame.pack(fill="x", expand=True, pady=12)
    
    # Monitor Settings
    monitors = screen.get_monitors()
    monitor_names = [f"Monitor {i+1}: {m.width}x{m.height}" for i, m in enumerate(monitors)]
    
    ttk.Label(display_frame, text="Application Monitor:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    app_monitor_var = tk.StringVar(value=current_config.get("app_monitor", monitor_names[0] if monitor_names else "Default"))
    app_monitor_combo = ttk.Combobox(display_frame, textvariable=app_monitor_var, values=monitor_names, state="readonly")
    app_monitor_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

    ttk.Label(display_frame, text="PDF Viewer Monitor:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    pdf_monitor_var = tk.StringVar(value=current_config.get("pdf_monitor", monitor_names[0] if monitor_names else "Default"))
    pdf_monitor_combo = ttk.Combobox(display_frame, textvariable=pdf_monitor_var, values=monitor_names, state="readonly")
    pdf_monitor_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

    identify_button = ttk.Button(display_frame, text="Identify Screens", command=lambda: screen.show_screen_numbers(settings_win))
    identify_button.grid(row=2, column=0, columnspan=2, pady=10)
    
    # Window State Settings
    window_states = ["Normal", "Maximized", "Fullscreen"]
    window_state_var = tk.StringVar(value=current_config.get("window_state", "Normal"))
    
    ttk.Label(display_frame, text="Startup State:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    window_state_combo = ttk.Combobox(display_frame, textvariable=window_state_var, values=window_states, state="readonly")
    window_state_combo.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
    
    # Editor Font Settings
    ttk.Label(display_frame, text="Editor Font:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
    available_fonts = app_config.get_available_editor_fonts()
    current_font = current_config.get("editor_font_family", "Consolas")
    editor_font_var = tk.StringVar(value=current_font)
    editor_font_combo = ttk.Combobox(display_frame, textvariable=editor_font_var, values=available_fonts, state="readonly")
    editor_font_combo.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
    
    # UI Visibility Settings
    ttk.Label(display_frame, text="Show Status Bar:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
    show_status_bar_var = tk.BooleanVar(value=app_config.get_bool(current_config.get("show_status_bar", "True")))
    show_status_bar_check = ttk.Checkbutton(display_frame, variable=show_status_bar_var)
    show_status_bar_check.grid(row=5, column=1, sticky="w", padx=5, pady=5)
    
    ttk.Label(display_frame, text="Show PDF Preview:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
    show_pdf_preview_var = tk.BooleanVar(value=app_config.get_bool(current_config.get("show_pdf_preview", "True")))
    show_pdf_preview_check = ttk.Checkbutton(display_frame, variable=show_pdf_preview_var)
    show_pdf_preview_check.grid(row=6, column=1, sticky="w", padx=5, pady=5)

    display_frame.columnconfigure(1, weight=1)

    # --- LLM Configuration ---
    llm_frame = ttk.LabelFrame(main_frame, text="LLM Configuration", padding=16)
    llm_frame.pack(fill="x", expand=True, pady=12)

    available_models = api_client.get_available_models()
    if not available_models:
        # If we can't fetch models, we add the currently saved ones as options
        # Display currently configured models for user visibility
        available_models = list(set(current_config.get(key) for key in current_config if key.startswith("model_")))

    model_vars = {}
    model_comboboxes = {} # To store combobox widgets for later update
    model_labels = {
        "model_completion": "Completion:",
        "model_generation": "Generation:",
        "model_rephrase": "Rephrase:",
        "model_debug": "Debug:",
        "model_style": "Style:",
        "model_proofreading": "Proofreading:"
    }

    def set_all_models_to(model_name):
        """Helper function to set all model variables to a specific model."""
        for key in model_vars:
            model_vars[key].set(model_name)
        logs_console.log(f"All models set to '{model_name}' in the UI.", level='INFO')

    for i, (key, label) in enumerate(model_labels.items()):
        ttk.Label(llm_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=5)
        
        current_value = current_config.get(key, "default")
        model_vars[key] = tk.StringVar(value=current_value)
        
        combo = ttk.Combobox(llm_frame, textvariable=model_vars[key], values=available_models, state="readonly")
        combo.grid(row=i, column=1, sticky="ew", padx=5, pady=5)
        model_comboboxes[key] = combo # Store the widget
        
        # Ensure the current value is properly selected in the combobox
        if current_value in available_models:
            combo.set(current_value)
        else:
            logs_console.log(f"Model '{current_value}' for {key} not in available models list", level='WARNING')
        
        # Button to set all models to the value of this combobox
        set_all_button = ttk.Button(
            llm_frame, 
            text="Set for All", 
            command=lambda m=model_vars[key]: set_all_models_to(m.get())
        )
        set_all_button.grid(row=i, column=2, padx=5, pady=5)

    # Add a button to open the global prompts editor
    global_prompts_button = ttk.Button(
        llm_frame, 
        text="Manage Global Prompts...", 
        command=show_global_prompts_panel
    )
    global_prompts_button.grid(row=len(model_labels), column=0, columnspan=3, pady=10)

    llm_frame.columnconfigure(1, weight=1)

    # --- API Settings ---
    api_frame = ttk.LabelFrame(main_frame, text="API Settings", padding=16)
    api_frame.pack(fill="x", expand=True, pady=12)

    ttk.Label(api_frame, text="Google Gemini API Key:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    gemini_api_key_var = tk.StringVar(value=current_config.get("gemini_api_key", ""))
    gemini_api_key_entry = ttk.Entry(api_frame, textvariable=gemini_api_key_var)
    gemini_api_key_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    
    api_frame.columnconfigure(1, weight=1)

    def refresh_models_command():
        """Saves the API key and refreshes the model list in the UI."""
        # 1. Save the current API key to the config file so the client can see it
        # Use current_config as base to preserve any unsaved UI changes
        updates = {"gemini_api_key": gemini_api_key_var.get()}
        for key, var in model_vars.items():
            updates[key] = var.get()
        app_config.update_and_save_config(updates)
        logs_console.log("API key and current model selections saved before refresh", level='INFO')

        # 2. Fetch the new, updated list of models
        new_models = api_client.get_available_models()
        logs_console.log(f"Model list refreshed. Found: {new_models}", level='INFO')

        # 3. Update all model comboboxes with the new list
        for key, combo in model_comboboxes.items():
            current_selection = combo.get()
            combo['values'] = new_models
            if current_selection in new_models:
                combo.set(current_selection)
            else:
                # Keep current selection even if not in new list
                # User can manually change if needed
                logs_console.log(f"Model '{current_selection}' not found in new list, keeping current selection", level='WARNING')
        
        from tkinter import messagebox
        messagebox.showinfo("Models Refreshed", f"Found {len(new_models)} available models.", parent=settings_win)

    refresh_button = ttk.Button(api_frame, text="Verify and Refresh Models", command=refresh_models_command)
    refresh_button.grid(row=0, column=2, padx=5, pady=5)

    # --- Save and Cancel Buttons ---
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=(24, 0))
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)

    def save_and_close():
        # Use the current_config as base instead of reloading from file
        # This prevents losing UI changes made since dialog opened
        updates = {
            "app_monitor": app_monitor_var.get(),
            "pdf_monitor": pdf_monitor_var.get(),
            "window_state": window_state_var.get(),
            "editor_font_family": editor_font_var.get(),
            "gemini_api_key": gemini_api_key_var.get(),
            "show_status_bar": str(show_status_bar_var.get()),
            "show_pdf_preview": str(show_pdf_preview_var.get()),
        }
        for key, var in model_vars.items():
            updates[key] = var.get()
            logs_console.log(f"Saving model {key}: {var.get()}", level='DEBUG')

        app_config.update_and_save_config(updates)
        logs_console.log("Settings saved successfully:", level='SUCCESS')
        
        # Log what was actually saved for debugging
        logs_console.log("Saved models:", level='INFO')
        for key, var in model_vars.items():
            logs_console.log(f"  {key}: {var.get()}", level='INFO')
        
        # CRITICAL: Update llm_state with new model settings
        # This prevents restart from overwriting with old values
        from llm import state as llm_state
        if 'model_completion' in updated_config:
            llm_state.model_completion = updated_config['model_completion']
        if 'model_generation' in updated_config:
            llm_state.model_generation = updated_config['model_generation']
        if 'model_rephrase' in updated_config:
            llm_state.model_rephrase = updated_config['model_rephrase']
        if 'model_debug' in updated_config:
            llm_state.model_debug = updated_config['model_debug']
        if 'model_style' in updated_config:
            llm_state.model_style = updated_config['model_style']
        if 'model_proofreading' in updated_config:
            llm_state.model_proofreading = updated_config['model_proofreading']
        logs_console.log("LLM state updated with new model settings", level='INFO')
        
        # Apply font change immediately if changed
        old_font = current_config.get("editor_font_family", "Consolas")
        new_font = updated_config["editor_font_family"]
        if old_font != new_font:
            # Import state to access zoom manager
            from app import state
            if hasattr(state, 'zoom_manager') and state.zoom_manager:
                state.zoom_manager.update_font_family(new_font)
                logs_console.log(f"Editor font changed from {old_font} to {new_font}", level='INFO')
        
        settings_win.destroy()
        
        from tkinter import messagebox
        if old_font != new_font:
            messagebox.showinfo("Settings Saved", "Your settings have been saved and the editor font has been updated immediately.", parent=root)
        else:
            messagebox.showinfo("Settings Saved", "Your new settings have been saved. Some changes may require a restart to take effect.", parent=root)

    save_btn = ttk.Button(button_frame, text="Save Settings", command=save_and_close, bootstyle="success")
    save_btn.grid(row=0, column=0, padx=8, sticky="e")
    
    cancel_btn = ttk.Button(button_frame, text="Cancel", command=settings_win.destroy, bootstyle="secondary")
    cancel_btn.grid(row=0, column=1, padx=8, sticky="w")

    display_frame.columnconfigure(1, weight=1)
    llm_frame.columnconfigure(1, weight=1)
    api_frame.columnconfigure(1, weight=1)
    
    settings_win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (settings_win.winfo_width() // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (settings_win.winfo_height() // 2)
    settings_win.geometry(f"+{x}+{y}")
