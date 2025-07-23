"""
This module contains the dedicated dialog for displaying LaTeX debugging information,
providing AI analysis, a colorized diff, and an option to apply the suggested fix.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import re

class DebugDialog(tk.Toplevel):
    """
    A dedicated dialog window for LaTeX error analysis and debugging.
    """
    def __init__(self, root_window, theme_getter, diff_content, log_content, ai_analysis, active_editor_getter):
        super().__init__(root_window)
        self.transient(root_window)
        self.title("LaTeX Debugger")
        self.geometry("1200x750")
        self.minsize(800, 500)
        self.grab_set()

        self.theme_getter = theme_getter
        self.diff_content = diff_content
        self.log_content = log_content
        self.ai_analysis_str = ai_analysis
        self.active_editor_getter = active_editor_getter
        
        self.corrected_code = ""
        self.ai_explanation = "No explanation provided."

        self._parse_ai_analysis()
        self._setup_styles()
        self._create_widgets()
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)

    def _parse_ai_analysis(self):
        """
        Parses the AI analysis string to extract key information, handling
        potential JSON formatting issues and markdown code blocks.
        """
        try:
            # Find the JSON block. This is more robust against extra text from the AI.
            json_match = re.search(r'\{.*\}', self.ai_analysis_str, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in the AI response.")
            
            json_str = json_match.group(0)
            analysis_data = json.loads(json_str)
            
            self.ai_explanation = analysis_data.get("explanation", "The AI did not provide an explanation.")
            corrected_code_raw = analysis_data.get("corrected_code", "")

            # Extract the code from markdown blocks like ```latex ... ``` or ``` ... ```
            code_match = re.search(r'```(?:latex)?\s*\n?(.*?)\n?```', corrected_code_raw, re.DOTALL)
            if code_match:
                self.corrected_code = code_match.group(1).strip()
            else:
                self.corrected_code = corrected_code_raw.strip()

        except (json.JSONDecodeError, ValueError) as e:
            self.ai_explanation = f"Could not parse the AI's response. Displaying raw output.\nError: {e}"
            self.corrected_code = self.ai_analysis_str

    def _setup_styles(self):
        """Sets up custom ttk styles for the dialog."""
        self.bg_color = self.theme_getter("root_bg", "#f0f0f0")
        self.text_bg_color = self.theme_getter("editor_bg", "#ffffff")
        self.text_fg_color = self.theme_getter("editor_fg", "#000000")
        self.configure(bg=self.bg_color)

        style = ttk.Style(self)
        style.configure("Debug.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.configure("Debug.TNotebook.Tab", font=("Segoe UI", 10), padding=[10, 5])
        style.map("Debug.TNotebook.Tab",
                  background=[("selected", self.theme_getter("tab_selected_bg", "#d0d0d0"))],
                  foreground=[("selected", self.theme_getter("tab_selected_fg", "#000000"))])

    def _create_widgets(self):
        """Creates and lays out the widgets for the dialog."""
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- Left Pane: AI Assistant ---
        left_pane = self._create_ai_pane(main_pane)
        main_pane.add(left_pane, weight=40) # 40% of width

        # --- Right Pane: Context (Diff & Log) ---
        right_pane = self._create_context_pane(main_pane)
        main_pane.add(right_pane, weight=60) # 60% of width

    def _create_ai_pane(self, parent):
        """Creates the left pane containing the AI's analysis and actions."""
        ai_frame = ttk.Frame(parent, padding=10)

        # Explanation
        exp_frame = ttk.LabelFrame(ai_frame, text="AI Explanation", padding=10)
        exp_frame.pack(fill=tk.BOTH, expand=True)
        
        exp_text = tk.Text(exp_frame, wrap="word", bg=self.bg_color, fg=self.text_fg_color, font=("Segoe UI", 11), relief=tk.FLAT, height=8)
        exp_text.insert("1.0", self.ai_explanation)
        exp_text.config(state="disabled")
        exp_text.pack(fill=tk.BOTH, expand=True)

        # Suggested Fix
        code_frame = ttk.LabelFrame(ai_frame, text="Suggested Fix", padding=10)
        code_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.code_text = tk.Text(code_frame, wrap="none", bg="#2d2d2d", fg="#dcdcdc", font=("Consolas", 10), relief=tk.FLAT, insertbackground="#ffffff")
        self.code_text.insert("1.0", self.corrected_code)
        self.code_text.config(state="disabled")
        self.code_text.pack(fill=tk.BOTH, expand=True)

        # Action Buttons
        action_frame = ttk.Frame(ai_frame)
        action_frame.pack(fill=tk.X, pady=(5, 0))

        copy_button = ttk.Button(action_frame, text="Copy Code", command=self._copy_code, style="Debug.TButton")
        copy_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        apply_button = ttk.Button(action_frame, text="Apply Fix", command=self._apply_fix, style="Debug.TButton")
        apply_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        if not self.corrected_code or "explanation" not in self.ai_analysis_str:
            apply_button.config(state="disabled")

        return ai_frame

    def _create_context_pane(self, parent):
        """Creates the right pane containing the diff and error log tabs."""
        context_notebook = ttk.Notebook(parent, style="Debug.TNotebook")
        context_notebook.pack(fill=tk.BOTH, expand=True)

        # Diff Tab
        diff_frame = ttk.Frame(context_notebook, padding=5)
        diff_text = tk.Text(diff_frame, wrap="none", bg=self.text_bg_color, fg=self.text_fg_color, font=("Consolas", 10))
        diff_text.pack(fill=tk.BOTH, expand=True)
        self._colorize_diff(diff_text, self.diff_content)
        context_notebook.add(diff_frame, text="Code Changes (Diff)")

        # Log Tab
        log_frame = ttk.Frame(context_notebook, padding=5)
        log_text = tk.Text(log_frame, wrap="word", bg=self.text_bg_color, fg=self.text_fg_color, font=("Consolas", 9))
        log_text.insert("1.0", self.log_content)
        log_text.config(state="disabled")
        log_text.pack(fill=tk.BOTH, expand=True)
        context_notebook.add(log_frame, text="Raw Error Log")

        return context_notebook

    def _colorize_diff(self, text_widget, diff_content):
        """Applies color tags to the diff content."""
        text_widget.config(state="normal")
        text_widget.tag_configure("addition", foreground="#4CAF50", font=("Consolas", 10, "bold"))
        text_widget.tag_configure("deletion", foreground="#F44336", font=("Consolas", 10, "bold"))
        text_widget.tag_configure("header", foreground="#2196F3", font=("Consolas", 10, "italic"))

        for line in diff_content.splitlines(True):
            if line.startswith('+'):
                text_widget.insert(tk.END, line, "addition")
            elif line.startswith('-'):
                text_widget.insert(tk.END, line, "deletion")
            elif line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                text_widget.insert(tk.END, line, "header")
            else:
                text_widget.insert(tk.END, line)
        text_widget.config(state="disabled")

    def _copy_code(self):
        """Copies the corrected code to the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.corrected_code)
        messagebox.showinfo("Copied", "The suggested fix has been copied to the clipboard.", parent=self)

    def _apply_fix(self):
        """Applies the corrected code to the active editor."""
        editor = self.active_editor_getter()
        if editor:
            if messagebox.askyesno("Confirm Fix", "This will replace the entire content of the current editor with the suggested fix. Are you sure?", parent=self):
                editor.delete("1.0", tk.END)
                editor.insert("1.0", self.corrected_code)
                self.destroy()
        else:
            messagebox.showerror("Error", "Could not find an active editor to apply the fix to.", parent=self)

def show_debug_dialog(root_window, theme_getter, diff_content, log_content, ai_analysis, active_editor_getter):
    """
    Public function to create and show the debug dialog.
    """
    DebugDialog(root_window, theme_getter, diff_content, log_content, ai_analysis, active_editor_getter)
