"""
This module contains the dialog for editing the global default LLM prompt templates.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from utils import debug_console
from llm import init as llm_init
from llm import state as llm_state

# Define global prompts directory path
PROMPTS_DIR = "data/prompts"

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

        self.prompts_content = self._load_prompts()
        self.text_widgets = {}
        self.placeholders = {
            "completion": "Placeholders: {previous_context}, {current_phrase_start}",
            "generation": "Placeholders: {user_prompt}, {context}, {keywords}",
            "generation_latex": "Placeholders: {user_prompt}, {context}, {keywords}",
            "styling": "Placeholders: {text}, {intensity}",
            "rephrase": "Placeholders: {text}, {instruction}",
            "debug_latex_diff": "Placeholders: {added_lines}"
        }

        self._setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)

    def _load_prompts(self):
        """Loads prompts from the .txt files in the prompts directory."""
        loaded_prompts = {}
        if not os.path.isdir(PROMPTS_DIR):
            messagebox.showerror("Error", f"Prompts directory not found: {PROMPTS_DIR}", parent=self)
            return {}
        
        for filename in sorted(os.listdir(PROMPTS_DIR)):
            if filename.endswith(".txt"):
                prompt_name = os.path.splitext(filename)[0]
                file_path = os.path.join(PROMPTS_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        loaded_prompts[prompt_name] = f.read()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not read prompt file: {filename}\n{e}", parent=self)
        return loaded_prompts

    def _setup_ui(self):
        """Creates the UI components."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=5)

        for key, value in self.prompts_content.items():
            tab = ttk.Frame(notebook, padding=10)
            notebook.add(tab, text=key.replace("_", " ").title())

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
        """Saves the prompts to their respective .txt files and reloads them."""
        for key, widget in self.text_widgets.items():
            content = widget.get("1.0", "end-1c")
            file_path = os.path.join(PROMPTS_DIR, f"{key}.txt")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save prompt: {key}\n{e}", parent=self)
                debug_console.log(f"Failed to save prompt {key}: {e}", level='ERROR')
                return # Stop saving if one file fails

        # Reload the global prompts in the application state
        llm_init._load_global_default_prompts()
        
        messagebox.showinfo("Success", "Global prompts have been saved and applied.", parent=self)
        debug_console.log("Global prompts saved and reloaded.", level='SUCCESS')
        self.destroy()
