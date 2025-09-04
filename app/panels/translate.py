"""
Integrated translate panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import logs_console


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
        lang_section = StandardComponents.create_section(parent, "Translation Language")
        lang_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Language selection label
        lang_label = StandardComponents.create_info_label(
            lang_section,
            "Select translation language pair:",
            "body"
        )
        lang_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        # Language combobox
        selected_pair_var = tk.StringVar()
        display_options = list(self.supported_translations.keys())
        
        self.lang_combobox = StandardComponents.create_combobox_input(
            lang_section,
            values=display_options,
            width=40,
            state="readonly"
        )
        self.lang_combobox.config(textvariable=selected_pair_var)
        self.lang_combobox.pack(fill="x")
        
        if display_options:
            self.lang_combobox.set(display_options[0])
            
        # Store the variable for later access
        self.selected_pair_var = selected_pair_var
        
        # Set as main widget for focus
        self.main_widget = self.lang_combobox
        
    def _create_options_section(self, parent):
        """Create the translation options section."""
        options_section = StandardComponents.create_section(parent, "Translation Options")
        options_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Skip preamble option
        self.skip_preamble_var = tk.BooleanVar(value=True)
        preamble_checkbox = ttk.Checkbutton(
            options_section,
            text="Skip preamble (don't translate before first \\section)",
            variable=self.skip_preamble_var
        )
        preamble_checkbox.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        # Help text with proper wrapping
        help_label = StandardComponents.create_info_label(
            options_section,
            "Recommended: Preserves document structure and LaTeX commands",
            "small"
        )
        help_label.pack(anchor="w")
        
    def _create_preview_section(self, parent):
        """Create the document preview section."""
        preview_section = StandardComponents.create_section(parent, "Document Preview")
        preview_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        # Document info
        char_count = len(self.source_text)
        word_count = len(self.source_text.split())
        info_label = StandardComponents.create_info_label(
            preview_section,
            f"Document: {char_count:,} characters, ~{word_count:,} words",
            "small"
        )
        info_label.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        # Preview text widget using StandardComponents
        preview_text = StandardComponents.create_text_input(
            preview_section,
            "Document preview will appear here...",
            height=8
        )
        preview_text.pack(fill="both", expand=True)
        
        # Show preview of source text (first 500 chars) and make readonly
        preview_text.config(state="normal")
        preview_content = self.source_text[:500] + ("..." if len(self.source_text) > 500 else "")
        preview_text.delete("1.0", "end")
        preview_text.insert("1.0", preview_content)
        preview_text.config(state="disabled")
        
    def _create_action_section(self, parent):
        """Create the action buttons section."""
        # Device info
        device_info = StandardComponents.create_info_label(
            parent,
            f"Translation will run on: {self.device} (translating last saved file content)",
            "small"
        )
        device_info.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        # Warning text
        warning_label = StandardComponents.create_info_label(
            parent,
            "Note: Translation may take several minutes depending on document size",
            "small"
        )
        warning_label.pack(anchor="w", pady=(0, StandardComponents.PADDING))
        
        # Translate button
        translate_buttons = [(
            f"Start Translation on {self.device}", 
            self._handle_translate, 
            "primary"
        )]
        translate_row = StandardComponents.create_button_row(parent, translate_buttons)
        translate_row.pack(fill="x")
        self.translate_button = translate_row.winfo_children()[0]  # Get button reference
        
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
        
        logs_console.log(f"Starting translation: {selection}, model: {model_name}", level='ACTION')
        
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