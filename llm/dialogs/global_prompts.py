"""
This module contains the dialog for editing the global default LLM prompt templates.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from utils import debug_console
from llm import init as llm_init

# The path to the global prompts file
DEFAULT_PROMPTS_FILE = "data/default_prompts.json"

def open_global_prompts_editor(root):
    """Opens the editor for global default prompts."""
    GlobalPromptsEditor(root)

class GlobalPromptsEditor(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Global Prompts Editor")
        self.geometry("900x700")
        self.transient(parent)
        self.grab_set()

        self.prompts = self._load_prompts()
        self.text_widgets = {}
        self.placeholders = {
            "completion": "Placeholders: {previous_context}, {current_phrase_start}",
            "generation": "Placeholders: {user_prompt}, {context}, {keywords}",
            "generation_latex": "Placeholders: {user_prompt}, {context}, {keywords}",
            "styling": "Placeholders: {text}, {intensity}",
            "rephrase": "Placeholders: {text}, {instruction}",
            "debug_latex_diff": "Placeholders: {log_content}, {added_lines}"
        }

        self._setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)

    def _load_prompts(self):
        """Loads prompts from the JSON file."""
        try:
            with open(DEFAULT_PROMPTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            debug_console.log(f"Error loading global prompts: {e}", level='ERROR')
            messagebox.showerror("Error", f"Could not load prompts file: {e}", parent=self)
            # Provide a fallback structure
            return {}

    def _setup_ui(self):
        """Creates the UI components."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=5)

        for key, value in self.prompts.items():
            tab = ttk.Frame(notebook, padding=10)
            notebook.add(tab, text=key.replace("_", " ").title())

            # Add placeholder info label
            placeholder_text = self.placeholders.get(key, "No specific placeholders for this prompt.")
            placeholder_label = ttk.Label(tab, text=placeholder_text, font=("Segoe UI", 9), foreground="gray")
            placeholder_label.pack(fill="x", pady=(0, 5), anchor="w")

            text_widget = tk.Text(tab, wrap="word", font=("Consolas", 10), undo=True)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", value)
            self.text_widgets[key] = text_widget

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        save_button = ttk.Button(button_frame, text="Save and Apply", command=self._save_prompts)
        save_button.pack(side="right", padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side="right")

    def _save_prompts(self):
        """Saves the prompts to the JSON file and reloads them."""
        new_prompts = {}
        for key, widget in self.text_widgets.items():
            new_prompts[key] = widget.get("1.0", "end-1c")

        try:
            with open(DEFAULT_PROMPTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_prompts, f, indent=4)
            
            # Reload the global prompts in the application state
            llm_init._load_global_default_prompts()
            
            messagebox.showinfo("Success", "Global prompts have been saved and applied.", parent=self)
            debug_console.log("Global prompts saved and reloaded.", level='SUCCESS')
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save prompts: {e}", parent=self)
            debug_console.log(f"Failed to save global prompts: {e}", level='ERROR')
