"""
Integrated translate panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import debug_console


class TranslatePanel(BasePanel):
    """
    Integrated translate panel that replaces the dialog window.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter,
                 source_text: str,
                 supported_translations: Dict[str, str],
                 on_translate_callback: Callable,
                 device: str = "CPU",
                 on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.source_text = source_text
        self.supported_translations = supported_translations
        self.on_translate_callback = on_translate_callback
        self.device = device
        
        # UI components
        self.lang_combobox: Optional[ttk.Combobox] = None
        self.skip_preamble_var: Optional[tk.BooleanVar] = None
        self.translate_button: Optional[tk.Button] = None
        
    def get_panel_title(self) -> str:
        return "Translate Document"
    
    def get_layout_style(self) -> PanelStyle:
        """Use simple layout for translate panel."""
        return PanelStyle.SIMPLE
        
    def create_content(self):
        """Create the translate panel content using standardized components."""
        # main_container is provided by PanelFactory
        main_frame = self.main_container
        
        # Language selection section
        self._create_language_section(main_frame)
        
        # Translation options section
        self._create_options_section(main_frame)
        
        # Preview section
        self._create_preview_section(main_frame)
        
        # Action button section
        self._create_action_section(main_frame)
        
    def _create_language_section(self, parent):
        """Create the language selection section."""
        lang_frame = ttk.LabelFrame(parent, text=" Translation Language ", padding="10")
        lang_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        lang_frame.grid_columnconfigure(0, weight=1)
        
        # Language selection label
        ttk.Label(lang_frame, text="Select translation language pair:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Language combobox
        selected_pair_var = tk.StringVar()
        display_options = list(self.supported_translations.keys())
        
        self.lang_combobox = ttk.Combobox(
            lang_frame,
            textvariable=selected_pair_var,
            values=display_options,
            state="readonly",
            width=40
        )
        self.lang_combobox.grid(row=1, column=0, sticky="ew")
        
        if display_options:
            self.lang_combobox.set(display_options[0])
            
        # Store the variable for later access
        self.selected_pair_var = selected_pair_var
        
    def _create_options_section(self, parent):
        """Create the translation options section."""
        options_frame = ttk.LabelFrame(parent, text=" Translation Options ", padding="10")
        options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Skip preamble option
        self.skip_preamble_var = tk.BooleanVar(value=True)
        preamble_checkbox = ttk.Checkbutton(
            options_frame,
            text="Skip preamble (don't translate before first \\section)",
            variable=self.skip_preamble_var
        )
        preamble_checkbox.pack(anchor="w")
        
        # Help text with proper wrapping
        help_label = ttk.Label(
            options_frame,
            text="Recommended: Preserves document structure and LaTeX commands",
            font=StandardComponents.SMALL_FONT,
            foreground=self.get_theme_color("muted_text", "#666666"),
            wraplength=350  # Wrap text for better fit
        )
        help_label.pack(anchor="w", pady=(2, 0))
        
    def _create_preview_section(self, parent):
        """Create the document preview section."""
        preview_frame = ttk.LabelFrame(parent, text=" Document Preview ", padding="10")
        preview_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # Configure parent to expand this section
        parent.grid_rowconfigure(2, weight=1)
        
        # Text widget with scrollbar
        text_container = ttk.Frame(preview_frame)
        text_container.grid(row=0, column=0, sticky="nsew")
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        preview_text = tk.Text(
            text_container,
            height=8,
            wrap="word",
            bg=self.get_theme_color("editor_bg", "#ffffff"),
            fg=self.get_theme_color("editor_fg", "#000000"),
            font=("Courier New", 9),
            state="disabled",
            relief="solid",
            borderwidth=1
        )
        preview_text.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=preview_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        preview_text.config(yscrollcommand=scrollbar.set)
        
        # Show preview of source text (first 500 chars)
        preview_text.config(state="normal")
        preview_content = self.source_text[:500] + ("..." if len(self.source_text) > 500 else "")
        preview_text.insert("1.0", preview_content)
        preview_text.config(state="disabled")
        
        # Document info
        char_count = len(self.source_text)
        word_count = len(self.source_text.split())
        info_label = ttk.Label(
            preview_frame,
            text=f"Document: {char_count:,} characters, ~{word_count:,} words",
            font=("Segoe UI", 8),
            foreground=self.get_theme_color("muted_text", "#666666")
        )
        info_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
    def _create_action_section(self, parent):
        """Create the action buttons section."""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        action_frame.grid_columnconfigure(0, weight=1)
        
        # Device info and translate button
        device_info = ttk.Label(
            action_frame,
            text=f"Translation will run on: {self.device}",
            font=("Segoe UI", 9),
            foreground=self.get_theme_color("muted_text", "#666666")
        )
        device_info.grid(row=0, column=0, pady=(0, 10))
        
        # Translate button
        self.translate_button = ttk.Button(
            action_frame,
            text=f"Start Translation on {self.device}",
            command=self._handle_translate
        )
        self.translate_button.grid(row=1, column=0)
        
        # Warning text
        warning_label = ttk.Label(
            action_frame,
            text="Note: Translation may take several minutes depending on document size",
            font=("Segoe UI", 8),
            foreground=self.get_theme_color("warning_text", "#ff6600")
        )
        warning_label.grid(row=2, column=0, pady=(10, 0))
        
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.lang_combobox:
            self.lang_combobox.focus_set()
    
    def _handle_translate(self):
        """Handle translate button click."""
        selection = self.selected_pair_var.get()
        
        if not selection:
            messagebox.showwarning(
                "Selection Error", 
                "Please select a translation language pair.",
                parent=self.panel_frame
            )
            return
        
        model_name = self.supported_translations[selection]
        skip_preamble = self.skip_preamble_var.get()
        
        debug_console.log(f"Starting translation: {selection}, model: {model_name}", level='ACTION')
        
        # Disable translate button during translation
        self.translate_button.config(state="disabled", text="Translating...")
        
        # Call the callback
        if self.on_translate_callback:
            # Get the selected translation pair key instead of model name
            selected_pair = model_name  # This should actually be the translation pair key
            for pair, model in self.supported_translations.items():
                if model == model_name:
                    selected_pair = pair
                    break
            self.on_translate_callback(selected_pair, skip_preamble)
        
        # Note: Panel will be closed by the translation callback when complete