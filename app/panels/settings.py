"""
Settings panel for integrated sidebar display.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import screen, logs_console
from app import config as app_config
from llm import api_client


class SettingsPanel(BasePanel):
    """
    Settings panel that replaces the settings window popup.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter, on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        # Store current config
        self.current_config = app_config.load_config()
        
        # UI variables
        self.app_monitor_var: Optional[tk.StringVar] = None
        self.pdf_monitor_var: Optional[tk.StringVar] = None
        self.window_state_var: Optional[tk.StringVar] = None
        self.editor_font_var: Optional[tk.StringVar] = None
        self.show_status_bar_var: Optional[tk.BooleanVar] = None
        self.show_pdf_preview_var: Optional[tk.BooleanVar] = None
        self.gemini_api_key_var: Optional[tk.StringVar] = None
        self.model_vars: Dict[str, tk.StringVar] = {}
        self.model_comboboxes: Dict[str, ttk.Combobox] = {}
        
    def get_panel_title(self) -> str:
        return "Settings"
    
    def get_layout_style(self) -> PanelStyle:
        return PanelStyle.SPLIT  # Use split layout like Text Generation panel
    
    def create_content(self):
        """Create the settings panel content using split layout like Text Generation."""
        # main_container is a PanedWindow for split layout
        paned_window = self.main_container
        
        # Display & Interface section (top)
        self._create_display_interface_section(paned_window)
        
        # LLM & API Configuration section (bottom)
        self._create_llm_api_section(paned_window)
        
    def _create_display_interface_section(self, parent):
        """Create the display and interface settings section (top)."""
        display_frame = ttk.Frame(parent)
        parent.add(display_frame, weight=2)  # More space for display settings
        
        # Main scrollable content
        main_frame = ttk.Frame(display_frame, padding=StandardComponents.PADDING)
        main_frame.pack(fill="both", expand=True)
        
        # Display Settings section
        display_section = StandardComponents.create_section(main_frame, "Display Settings")
        display_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Monitor settings in a grid
        monitor_frame = ttk.Frame(display_section)
        monitor_frame.pack(fill="x", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        monitor_frame.grid_columnconfigure(1, weight=1)
        
        # Monitor Settings
        monitors = screen.get_monitors()
        monitor_names = [f"Monitor {i+1}: {m.width}x{m.height}" for i, m in enumerate(monitors)]
        
        ttk.Label(monitor_frame, text="Application Monitor:", font=StandardComponents.BODY_FONT).grid(row=0, column=0, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=2)
        self.app_monitor_var = tk.StringVar(value=self.current_config.get("app_monitor", monitor_names[0] if monitor_names else "Default"))
        app_monitor_combo = StandardComponents.create_combobox_input(monitor_frame, monitor_names)
        app_monitor_combo.configure(textvariable=self.app_monitor_var)
        app_monitor_combo.grid(row=0, column=1, sticky="ew", padx=(StandardComponents.ELEMENT_SPACING, 0), pady=2)
        
        ttk.Label(monitor_frame, text="PDF Viewer Monitor:", font=StandardComponents.BODY_FONT).grid(row=1, column=0, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=2)
        self.pdf_monitor_var = tk.StringVar(value=self.current_config.get("pdf_monitor", monitor_names[0] if monitor_names else "Default"))
        pdf_monitor_combo = StandardComponents.create_combobox_input(monitor_frame, monitor_names)
        pdf_monitor_combo.configure(textvariable=self.pdf_monitor_var)
        pdf_monitor_combo.grid(row=1, column=1, sticky="ew", padx=(StandardComponents.ELEMENT_SPACING, 0), pady=2)
        
        # Identify screens button
        identify_button = StandardComponents.create_button_input(monitor_frame, "Identify Screens", self._identify_screens)
        identify_button.grid(row=2, column=0, columnspan=2, pady=8)
        
        # Interface Settings section
        interface_section = StandardComponents.create_section(main_frame, "Interface Settings")
        interface_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        interface_frame = ttk.Frame(interface_section)
        interface_frame.pack(fill="x", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        interface_frame.grid_columnconfigure(1, weight=1)
        
        # Window State
        window_states = ["Normal", "Maximized", "Fullscreen"]
        self.window_state_var = tk.StringVar(value=self.current_config.get("window_state", "Normal"))
        ttk.Label(interface_frame, text="Startup State:", font=StandardComponents.BODY_FONT).grid(row=0, column=0, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=2)
        window_state_combo = StandardComponents.create_combobox_input(interface_frame, window_states)
        window_state_combo.configure(textvariable=self.window_state_var)
        window_state_combo.grid(row=0, column=1, sticky="ew", padx=(StandardComponents.ELEMENT_SPACING, 0), pady=2)
        
        # Editor Font
        available_fonts = app_config.get_available_editor_fonts()
        current_font = self.current_config.get("editor_font_family", "Consolas")
        self.editor_font_var = tk.StringVar(value=current_font)
        ttk.Label(interface_frame, text="Editor Font:", font=StandardComponents.BODY_FONT).grid(row=1, column=0, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=2)
        editor_font_combo = StandardComponents.create_combobox_input(interface_frame, available_fonts)
        editor_font_combo.configure(textvariable=self.editor_font_var)
        editor_font_combo.grid(row=1, column=1, sticky="ew", padx=(StandardComponents.ELEMENT_SPACING, 0), pady=2)
        
        # UI Visibility checkboxes
        ttk.Label(interface_frame, text="Show Status Bar:", font=StandardComponents.BODY_FONT).grid(row=2, column=0, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=2)
        self.show_status_bar_var = tk.BooleanVar(value=app_config.get_bool(self.current_config.get("show_status_bar", "True")))
        show_status_bar_check = ttk.Checkbutton(interface_frame, variable=self.show_status_bar_var)
        show_status_bar_check.grid(row=2, column=1, sticky="w", padx=(StandardComponents.ELEMENT_SPACING, 0), pady=2)
        
        ttk.Label(interface_frame, text="Show PDF Preview:", font=StandardComponents.BODY_FONT).grid(row=3, column=0, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=2)
        self.show_pdf_preview_var = tk.BooleanVar(value=app_config.get_bool(self.current_config.get("show_pdf_preview", "True")))
        show_pdf_preview_check = ttk.Checkbutton(interface_frame, variable=self.show_pdf_preview_var)
        show_pdf_preview_check.grid(row=3, column=1, sticky="w", padx=(StandardComponents.ELEMENT_SPACING, 0), pady=2)
        
    def _create_llm_api_section(self, parent):
        """Create the LLM and API configuration section (bottom)."""
        llm_frame = ttk.Frame(parent)
        parent.add(llm_frame, weight=2)  # Give more space to this section
        
        # Main scrollable content
        main_frame = ttk.Frame(llm_frame, padding=StandardComponents.PADDING)
        main_frame.pack(fill="both", expand=True)
        
        # LLM Configuration section
        llm_section = StandardComponents.create_section(main_frame, "LLM Configuration")
        llm_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        llm_config_frame = ttk.Frame(llm_section)
        llm_config_frame.pack(fill="x", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        llm_config_frame.grid_columnconfigure(1, weight=1)
        
        available_models = api_client.get_available_models()
        if not available_models:
            available_models = list(set(self.current_config.get(key) for key in self.current_config if key.startswith("model_")))
        
        model_labels = {
            "model_completion": "Completion:",
            "model_generation": "Generation:",
            "model_rephrase": "Rephrase:",
            "model_debug": "Debug:",
            "model_style": "Style:",
            "model_proofreading": "Proofreading:"
        }
        
        def set_all_models_to(model_name):
            for key in self.model_vars:
                self.model_vars[key].set(model_name)
            logs_console.log(f"All models set to '{model_name}' in the UI.", level='INFO')
        
        for i, (key, label) in enumerate(model_labels.items()):
            ttk.Label(llm_config_frame, text=label, font=StandardComponents.BODY_FONT).grid(row=i, column=0, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=2)
            self.model_vars[key] = tk.StringVar(value=self.current_config.get(key, available_models[0] if available_models else ""))
            model_combobox = StandardComponents.create_combobox_input(llm_config_frame, available_models)
            model_combobox.configure(textvariable=self.model_vars[key])
            model_combobox.grid(row=i, column=1, sticky="ew", padx=(StandardComponents.ELEMENT_SPACING, 0), pady=2)
            self.model_comboboxes[key] = model_combobox
        
        # Model management buttons
        button_frame = ttk.Frame(llm_config_frame)
        button_frame.grid(row=len(model_labels), column=0, columnspan=2, pady=(10, 0), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        refresh_btn = StandardComponents.create_button_input(button_frame, "Refresh Models", self._refresh_models)
        refresh_btn.grid(row=0, column=0, padx=(0, 3), sticky="ew")
        
        clear_btn = StandardComponents.create_button_input(button_frame, "Clear All", lambda: set_all_models_to(""))
        clear_btn.grid(row=0, column=1, padx=(3, 3), sticky="ew")
        
        # Global prompts button
        def open_global_prompts():
            from app.panels import show_global_prompts_panel
            show_global_prompts_panel()
            
        global_prompts_btn = StandardComponents.create_button_input(button_frame, "Global Prompts", open_global_prompts)
        global_prompts_btn.grid(row=0, column=2, padx=(3, 0), sticky="ew")
        
        # API Settings section
        api_section = StandardComponents.create_section(main_frame, "API Settings")
        api_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        api_frame = ttk.Frame(api_section)
        api_frame.pack(fill="x", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        api_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(api_frame, text="Gemini API Key:", font=StandardComponents.BODY_FONT).grid(row=0, column=0, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=2)
        self.gemini_api_key_var = tk.StringVar(value=self.current_config.get("gemini_api_key", ""))
        gemini_api_entry = StandardComponents.create_entry_input(api_frame)
        gemini_api_entry.configure(textvariable=self.gemini_api_key_var, show="*")
        gemini_api_entry.grid(row=0, column=1, sticky="ew", padx=(StandardComponents.ELEMENT_SPACING, 0), pady=2)
        
        # Action buttons
        action_section = ttk.Frame(main_frame)
        action_section.pack(fill="x", pady=(StandardComponents.SECTION_SPACING, 0))
        
        action_buttons = [
            ("Save Settings", self._save_settings, "primary"),
            ("Reset to Defaults", self._reset_settings, "secondary")
        ]
        button_row = StandardComponents.create_button_row(action_section, action_buttons)
        button_row.pack()
    
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        # Focus is managed by the paned window layout
        pass
        
    def _identify_screens(self):
        """Display screen identification."""
        from app import state
        screen.show_screen_numbers(state.main_window)

    def _refresh_models(self):
        """Refresh the available models list."""
        try:
            # Temporarily disable widgets to show loading
            for combo in self.model_comboboxes.values():
                combo.configure(state="disabled")
            
            # Fetch fresh models
            available_models = api_client.get_available_models(force_refresh=True)
            if available_models:
                # Update all comboboxes with new models
                for combo in self.model_comboboxes.values():
                    combo.configure(values=available_models, state="readonly")
                
                logs_console.log(f"Refreshed {len(available_models)} available models", level='INFO')
                messagebox.showinfo(
                    "Success", 
                    f"Successfully refreshed {len(available_models)} models.",
                    parent=self.panel_frame
                )
            else:
                for combo in self.model_comboboxes.values():
                    combo.configure(state="readonly")
                logs_console.log("No models found during refresh", level='WARNING')
                messagebox.showwarning(
                    "No Models", 
                    "No models found. Please check your Ollama installation.",
                    parent=self.panel_frame
                )
                
        except Exception as e:
            for combo in self.model_comboboxes.values():
                combo.configure(state="readonly")
            logs_console.log(f"Error refreshing models: {e}", level='ERROR')
            messagebox.showerror(
                "Error", 
                f"Failed to refresh models:\n{str(e)}",
                parent=self.panel_frame
            )

    def _save_settings(self):
        """Save current settings to config."""
        try:
            # Collect values from all UI components
            updated_config = {
                "app_monitor": self.app_monitor_var.get(),
                "pdf_monitor": self.pdf_monitor_var.get(),
                "window_state": self.window_state_var.get(),
                "editor_font_family": self.editor_font_var.get(),
                "show_status_bar": str(self.show_status_bar_var.get()),
                "show_pdf_preview": str(self.show_pdf_preview_var.get()),
                "gemini_api_key": self.gemini_api_key_var.get(),
            }
            
            # Add model selections
            for key, var in self.model_vars.items():
                updated_config[key] = var.get()
            
            # Merge with existing config and save
            self.current_config.update(updated_config)
            app_config.save_config(self.current_config)
            
            logs_console.log("Settings saved successfully", level='INFO')
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.", parent=self.panel_frame)
            
        except Exception as e:
            logs_console.log(f"Error saving settings: {e}", level='ERROR')
            messagebox.showerror("Save Error", f"Failed to save settings:\n{str(e)}", parent=self.panel_frame)

    def _reset_settings(self):
        """Reset settings to defaults."""
        if messagebox.askyesno("Reset Settings", 
                              "Are you sure you want to reset all settings to defaults? This cannot be undone.", 
                              parent=self.panel_frame):
            try:
                # Reset config to defaults
                app_config.reset_config()
                self.current_config = app_config.load_config()
                
                # Update UI with default values
                self._update_ui_from_config()
                
                logs_console.log("Settings reset to defaults", level='INFO')
                messagebox.showinfo("Settings Reset", "All settings have been reset to defaults.", parent=self.panel_frame)
                
            except Exception as e:
                logs_console.log(f"Error resetting settings: {e}", level='ERROR')
                messagebox.showerror("Reset Error", f"Failed to reset settings:\n{str(e)}", parent=self.panel_frame)

    def _update_ui_from_config(self):
        """Update UI elements with values from current config."""
        if hasattr(self, 'app_monitor_var') and self.app_monitor_var:
            monitors = screen.get_monitors()
            monitor_names = [f"Monitor {i+1}: {m.width}x{m.height}" for i, m in enumerate(monitors)]
            self.app_monitor_var.set(self.current_config.get("app_monitor", monitor_names[0] if monitor_names else "Default"))
            self.pdf_monitor_var.set(self.current_config.get("pdf_monitor", monitor_names[0] if monitor_names else "Default"))
            self.window_state_var.set(self.current_config.get("window_state", "Normal"))
            self.editor_font_var.set(self.current_config.get("editor_font_family", "Consolas"))
            self.show_status_bar_var.set(app_config.get_bool(self.current_config.get("show_status_bar", "True")))
            self.show_pdf_preview_var.set(app_config.get_bool(self.current_config.get("show_pdf_preview", "True")))
            self.gemini_api_key_var.set(self.current_config.get("gemini_api_key", ""))
            
            # Update model variables
            for key, var in self.model_vars.items():
                var.set(self.current_config.get(key, ""))