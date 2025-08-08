
"""
This module contains the dedicated dialog for displaying LaTeX debugging information,
providing AI analysis, a colorized diff, and an option to apply the suggested fix.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import re
import threading
from llm import api_client, state as llm_state

class DebugDialog(tk.Toplevel):
    """
    A dedicated dialog window for LaTeX error analysis and debugging.
    The dialog now starts by showing the diff and offers AI analysis on demand.
    """
    def __init__(self, root_window, theme_getter, diff_content, log_content, active_editor_getter):
        super().__init__(root_window)
        self.transient(root_window)
        self.title("LaTeX Debugger")
        self.geometry("1200x750")
        self.state('zoomed') # Open maximized
        self.grab_set()

        self.theme_getter = theme_getter
        self.diff_content = diff_content
        self.log_content = log_content
        self.active_editor_getter = active_editor_getter
        
        self.corrected_code = ""
        self.ai_explanation = "No explanation provided."
        self.ai_analysis_str = ""

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
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', self.ai_analysis_str, re.DOTALL)
            if not json_match:
                json_match = re.search(r'{.*}', self.ai_analysis_str, re.DOTALL)

            if not json_match:
                raise ValueError("No JSON object found in the AI response.")
            
            json_str = json_match.group(1) if len(json_match.groups()) > 0 else json_match.group(0)
            
            try:
                analysis_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                if "Expecting property name enclosed in double quotes" in str(e):
                    repaired_json_str = json_str.replace("'", '"')
                    analysis_data = json.loads(repaired_json_str)
                else:
                    raise
            
            self.ai_explanation = analysis_data.get("explanation", "The AI did not provide an explanation.")
            corrected_code_raw = analysis_data.get("corrected_code", "")

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
        style.configure("Debug.TButton", font=("Segoe UI", 11, "bold"), padding=12)
        style.configure("Small.TButton", font=("Segoe UI", 9), padding=8) # New smaller style
        style.configure("Debug.TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 6])
        style.map("Debug.TNotebook.Tab",
                  background=[("selected", self.theme_getter("tab_selected_bg", "#d0d0d0"))],
                  foreground=[("selected", self.theme_getter("tab_selected_fg", "#000000"))])

    def _create_widgets(self):
        """Creates and lays out the widgets for the dialog."""
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.left_pane = self._create_initial_ai_pane(main_pane)
        main_pane.add(self.left_pane, weight=35)

        right_pane = self._create_context_pane(main_pane)
        main_pane.add(right_pane, weight=65)

    def _create_initial_ai_pane(self, parent):
        """Creates the initial left pane with a cleaner, more subtle layout."""
        self.ai_frame = ttk.Frame(parent, padding=20)
        
        container = ttk.Frame(self.ai_frame)
        container.pack(expand=True, anchor="center")

        title_label = ttk.Label(container, text="Ready to Fix?", font=("Segoe UI", 14, "bold"))
        title_label.pack(pady=(0, 5))

        info_label = ttk.Label(container, text="Click the button below to analyze the error in your added code.", wraplength=300, justify=tk.CENTER)
        info_label.pack(pady=(0, 20))
        
        self.analyze_button = ttk.Button(container, text="Analyze Error", command=self._run_ai_analysis, style="Debug.TButton")
        self.analyze_button.pack()
        
        return self.ai_frame

    def _run_ai_analysis(self):
        """Handles the AI analysis process when the button is clicked."""
        for widget in self.ai_frame.winfo_children():
            widget.destroy()
        
        progress_frame = ttk.Frame(self.ai_frame)
        progress_frame.pack(expand=True)
        
        progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        progress.pack(pady=20)
        progress.start()
        
        loading_label = ttk.Label(progress_frame, text="Contacting LLM...", font=("Segoe UI", 10, "italic"))
        loading_label.pack()

        threading.Thread(target=self._fetch_ai_analysis, daemon=True).start()

    def _fetch_ai_analysis(self):
        """Makes the API call to the LLM, sending only the added lines for analysis."""
        prompt_template = llm_state._global_default_prompts.get("debug_latex_diff")
        if not prompt_template:
            self.after(0, lambda: messagebox.showerror("LLM Error", "The 'debug_latex_diff' prompt template is missing."))
            return

        added_lines = self._extract_added_lines(self.diff_content)
        if not added_lines.strip():
            self.after(0, lambda: self._show_error_in_pane("No added lines (+) found in the diff to analyze."))
            return

        # Ne transmettre que le diff_content et les added_lines, pas le log_content
        full_prompt = prompt_template.format(diff_content=self.diff_content, added_lines=added_lines)
        
        try:
            response_generator = api_client.request_llm_generation(full_prompt, model_name=llm_state.model_debug, stream=False)
            response = next(response_generator)

            if response.get("success"):
                self.ai_analysis_str = response.get("data", "No analysis available.")
                self.after(0, self._update_ui_with_analysis)
            else:
                error_msg = response.get("error", "An unknown error occurred.")
                self.after(0, lambda: self._show_error_in_pane(error_msg))
        except Exception as e:
            self.after(0, lambda: self._show_error_in_pane(f"An unexpected error occurred: {e}"))

    def _show_error_in_pane(self, error_message):
        """Displays an error message in the AI pane."""
        for widget in self.ai_frame.winfo_children():
            widget.destroy()
        
        error_label = ttk.Label(self.ai_frame, text="Analysis Failed", font=("Segoe UI", 14, "bold"), foreground="red")
        error_label.pack(pady=(10, 5), anchor="w")
        
        error_text = ttk.Label(self.ai_frame, text=error_message, wraplength=350, justify=tk.LEFT)
        error_text.pack(pady=10, anchor="w")

        # Removed the retry button for a simpler, less frustrating UX.
        # The user can close the dialog and re-trigger the compilation if they wish to try again.
        info_label = ttk.Label(self.ai_frame, text="You can close this dialog and try compiling again.", font=("Segoe UI", 9, "italic"))
        info_label.pack(pady=(20, 0), anchor="w")

    def _update_ui_with_analysis(self):
        """Clears the loading state and populates the pane with AI analysis."""
        for widget in self.ai_frame.winfo_children():
            widget.destroy()

        self._parse_ai_analysis()

        exp_frame = ttk.LabelFrame(self.ai_frame, text="Explanation", padding=15)
        exp_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        exp_text = tk.Text(exp_frame, wrap="word", bg=self.bg_color, fg=self.text_fg_color, font=("Segoe UI", 11), relief=tk.FLAT, height=8)
        exp_text.insert("1.0", self.ai_explanation)
        exp_text.config(state="disabled")
        exp_text.pack(fill=tk.BOTH, expand=True)

        code_frame = ttk.LabelFrame(self.ai_frame, text="Suggested Fix", padding=15)
        code_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.code_text = tk.Text(
            code_frame, wrap="none", bg=self.text_bg_color, fg=self.text_fg_color, 
            font=("Consolas", 10), relief=tk.FLAT, insertbackground=self.text_fg_color
        )
        self.code_text.insert("1.0", self.corrected_code)
        self.code_text.config(state="disabled")
        self.code_text.pack(fill=tk.BOTH, expand=True)

        action_frame = ttk.Frame(self.ai_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        copy_button = ttk.Button(action_frame, text="Copy Code", command=lambda: self._copy_to_clipboard(self.corrected_code, "The suggested fix has been copied to the clipboard."), style="Small.TButton")
        copy_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        apply_button = ttk.Button(action_frame, text="Apply Fix", command=self._apply_fix, style="Small.TButton")
        apply_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        if not self.corrected_code or "Could not parse" in self.ai_explanation:
            apply_button.config(state="disabled")

    def _create_context_pane(self, parent):
        """Creates the right pane containing the diff and error log tabs."""
        context_notebook = ttk.Notebook(parent, style="Debug.TNotebook")
        context_notebook.pack(fill=tk.BOTH, expand=True)

        diff_frame = ttk.Frame(context_notebook, padding=5)
        
        # Create a container for the text and the button
        diff_container = ttk.Frame(diff_frame)
        diff_container.pack(fill=tk.BOTH, expand=True)

        diff_text = tk.Text(diff_container, wrap="word", bg=self.text_bg_color, fg=self.text_fg_color, font=("Consolas", 10))
        diff_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._colorize_diff(diff_text, self.diff_content)

        # Frame for the copy button, aligned to the right
        button_frame = ttk.Frame(diff_container)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        copy_added_button = ttk.Button(button_frame, text="Copy only +", command=lambda: self._copy_to_clipboard(self._extract_added_lines(self.diff_content), "The added lines have been copied to the clipboard."))
        copy_added_button.pack(side=tk.RIGHT, padx=(5, 0))

        copy_diff_button = ttk.Button(button_frame, text="Copy Diff", command=lambda: self._copy_to_clipboard(self.diff_content, "The diff content has been copied to the clipboard."))
        copy_diff_button.pack(side=tk.RIGHT)

        context_notebook.add(diff_frame, text="Code Changes (Diff)")

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

    def _copy_to_clipboard(self, content_to_copy, confirmation_message):
        """Copies the given content to the clipboard and shows a confirmation."""
        self.clipboard_clear()
        self.clipboard_append(content_to_copy)
        messagebox.showinfo("Copied", confirmation_message, parent=self)

    def _extract_added_lines(self, diff_content):
        """Extracts only the added lines (starting with '+') from a diff string."""
        added_lines = [line[1:] for line in diff_content.splitlines() if line.startswith('+')]
        return "\n".join(added_lines)

    

    def _apply_fix(self):
        """
        Applies the corrected code to the active editor by replacing only the
        lines that were originally added.
        """
        editor = self.active_editor_getter()
        if not editor:
            messagebox.showerror("Error", "Could not find an active editor to apply the fix to.", parent=self)
            return

        block_to_replace = self._extract_added_lines(self.diff_content)
        if not block_to_replace.strip():
            messagebox.showerror("Apply Fix Failed", "There were no added lines (+) in the original change to replace.", parent=self)
            return

        try:
            current_editor_content = editor.get("1.0", tk.END)
            
            if block_to_replace in current_editor_content:
                start_index = current_editor_content.find(block_to_replace)
                end_index = start_index + len(block_to_replace)
                
                tk_start = editor.index(f"1.0 + {start_index} chars")
                tk_end = editor.index(f"1.0 + {end_index} chars")

                if messagebox.askyesno("Confirm Smart Replace", "This will replace the added lines in your editor with the AI's suggested fix.\n\nAre you sure you want to proceed?", parent=self):
                    editor.delete(tk_start, tk_end)
                    editor.insert(tk_start, self.corrected_code)
                    self.destroy()
            else:
                raise ValueError("Could not find the code block to replace in the editor. The content may have changed.")

        except Exception as e:
            messagebox.showerror("Apply Fix Failed", f"Could not apply the fix automatically: {e}\n\nPlease use 'Copy Code' and apply the fix manually.", parent=self)

def show_debug_dialog(root_window, theme_getter, diff_content, log_content, active_editor_getter):
    """
    Public function to create and show the debug dialog.
    """
    DebugDialog(root_window, theme_getter, diff_content, log_content, active_editor_getter)
