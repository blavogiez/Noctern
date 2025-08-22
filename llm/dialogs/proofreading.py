"""
Dialogs for document proofreading functionality.
Includes setup dialog for configuring proofreading and navigation dialog for reviewing errors.
"""
import json
import tkinter as tk
from tkinter import ttk, messagebox
from utils import debug_console
from llm import state as llm_state
from llm import utils as llm_utils
from llm.streaming_service import start_streaming_request
from llm.schemas import get_proofreading_schema, validate_proofreading_response

def show_proofreading_setup_dialog(root_window, theme_setting_getter_func, text_to_check, on_proofread_callback):
    """
    Display setup dialog for configuring proofreading parameters.
    
    Args:
        root_window (tk.Tk): Main application window
        theme_setting_getter_func (callable): Function to get theme settings
        text_to_check (str): Text to be proofread
        on_proofread_callback (callable): Callback with (text, custom_instructions) when ready
    """
    debug_console.log("Opening proofreading setup dialog.", level='ACTION')
    dialog = tk.Toplevel(root_window)
    dialog.title("Document Proofreading")
    dialog.transient(root_window)
    dialog.grab_set()
    dialog.geometry("600x400")
    
    # Theme settings
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    dialog.configure(bg=dialog_bg)
    
    # Main frame
    main_frame = ttk.Frame(dialog, padding=10)
    main_frame.pack(fill="both", expand=True)
    main_frame.grid_rowconfigure(2, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    
    # Title
    title_label = ttk.Label(main_frame, text="Document Proofreading", font=("Segoe UI", 12, "bold"))
    title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
    
    # Instructions entry
    instructions_frame = ttk.LabelFrame(main_frame, text="Custom Instructions (optional)", padding=5)
    instructions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
    instructions_frame.grid_columnconfigure(0, weight=1)
    
    instructions_entry = ttk.Entry(instructions_frame, font=("Segoe UI", 9))
    instructions_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    instructions_entry.insert(0, "Focus on grammar and spelling")
    
    # Text preview
    preview_frame = ttk.LabelFrame(main_frame, text="Text to Proofread", padding=5)
    preview_frame.grid(row=2, column=0, sticky="nsew")
    preview_frame.grid_rowconfigure(0, weight=1)
    preview_frame.grid_columnconfigure(0, weight=1)
    
    preview_text = tk.Text(
        preview_frame, wrap="word", bg=text_bg, fg=text_fg, 
        font=("Segoe UI", 9), state="disabled", height=12
    )
    preview_text.grid(row=0, column=0, sticky="nsew")
    
    preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
    preview_scrollbar.grid(row=0, column=1, sticky="ns")
    preview_text.config(yscrollcommand=preview_scrollbar.set)
    
    # Show text preview
    preview_text.config(state="normal")
    preview_text.insert("1.0", text_to_check)
    preview_text.config(state="disabled")
    
    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=3, column=0, sticky="e", pady=(10, 0))
    
    def _on_start_proofreading():
        custom_instructions = instructions_entry.get().strip()
        dialog.destroy()
        on_proofread_callback(text_to_check, custom_instructions)
    
    def _on_cancel():
        dialog.destroy()
    
    start_button = ttk.Button(button_frame, text="Start Proofreading", command=_on_start_proofreading)
    start_button.pack(side="left", padx=5)
    
    cancel_button = ttk.Button(button_frame, text="Cancel", command=_on_cancel)
    cancel_button.pack(side="left")
    
    # Shortcuts
    dialog.bind("<Return>", lambda e: _on_start_proofreading())
    dialog.bind("<Escape>", lambda e: _on_cancel())
    dialog.protocol("WM_DELETE_WINDOW", _on_cancel)
    
    instructions_entry.focus_set()
    dialog.wait_window()

def show_proofreading_dialog(root_window, theme_setting_getter_func, editor, errors, original_text):
    """
    Display dialog for navigating and applying proofreading corrections.
    
    Args:
        root_window (tk.Tk): Main application window
        theme_setting_getter_func (callable): Function to get theme settings
        editor (tk.Text): Editor widget to apply corrections to
        errors (list): List of error dictionaries from LLM
        original_text (str): Original text that was proofread
    """
    debug_console.log(f"Opening proofreading results dialog with {len(errors)} errors.", level='INFO')
    dialog = tk.Toplevel(root_window)
    dialog.title(f"Proofreading Results - {len(errors)} errors found")
    dialog.transient(root_window)
    dialog.grab_set()
    dialog.geometry("800x600")
    
    # Theme settings
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    error_bg = theme_setting_getter_func("llm_generated_bg", "#ffe6e6")
    dialog.configure(bg=dialog_bg)
    
    # State variables
    current_error_index = tk.IntVar(value=0)
    applied_corrections = set()  # Track applied corrections
    
    # Main frame
    main_frame = ttk.Frame(dialog, padding=10)
    main_frame.pack(fill="both", expand=True)
    main_frame.grid_rowconfigure(2, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    
    # Header with navigation
    header_frame = ttk.Frame(main_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    header_frame.grid_columnconfigure(1, weight=1)
    
    # Navigation buttons
    nav_frame = ttk.Frame(header_frame)
    nav_frame.grid(row=0, column=0, sticky="w")
    
    def _update_navigation():
        current = current_error_index.get()
        prev_button.config(state="normal" if current > 0 else "disabled")
        next_button.config(state="normal" if current < len(errors) - 1 else "disabled")
        counter_label.config(text=f"{current + 1} of {len(errors)}")
        _show_current_error()
    
    def _go_previous():
        if current_error_index.get() > 0:
            current_error_index.set(current_error_index.get() - 1)
            _update_navigation()
    
    def _go_next():
        if current_error_index.get() < len(errors) - 1:
            current_error_index.set(current_error_index.get() + 1)
            _update_navigation()
    
    prev_button = ttk.Button(nav_frame, text="◄ Previous", command=_go_previous)
    prev_button.pack(side="left", padx=2)
    
    next_button = ttk.Button(nav_frame, text="Next ►", command=_go_next)
    next_button.pack(side="left", padx=2)
    
    counter_label = ttk.Label(nav_frame, text="1 of 1", font=("Segoe UI", 9))
    counter_label.pack(side="left", padx=10)
    
    # Error info frame
    info_frame = ttk.LabelFrame(main_frame, text="Error Details", padding=10)
    info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
    info_frame.grid_columnconfigure(1, weight=1)
    
    # Error type and position
    type_label = ttk.Label(info_frame, text="Type:", font=("Segoe UI", 9, "bold"))
    type_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
    
    type_value = ttk.Label(info_frame, text="", font=("Segoe UI", 9))
    type_value.grid(row=0, column=1, sticky="w")
    
    # Original and suggested text
    original_label = ttk.Label(info_frame, text="Original:", font=("Segoe UI", 9, "bold"))
    original_label.grid(row=1, column=0, sticky="nw", padx=(0, 5), pady=(5, 0))
    
    original_text_widget = tk.Text(
        info_frame, height=2, wrap="word", bg=error_bg, fg=text_fg,
        font=("Segoe UI", 9), state="disabled", relief=tk.FLAT
    )
    original_text_widget.grid(row=1, column=1, sticky="ew", pady=(5, 0))
    
    suggested_label = ttk.Label(info_frame, text="Suggested:", font=("Segoe UI", 9, "bold"))
    suggested_label.grid(row=2, column=0, sticky="nw", padx=(0, 5), pady=(5, 0))
    
    suggested_text_widget = tk.Text(
        info_frame, height=2, wrap="word", bg=text_bg, fg=text_fg,
        font=("Segoe UI", 9), state="disabled", relief=tk.FLAT
    )
    suggested_text_widget.grid(row=2, column=1, sticky="ew", pady=(5, 0))
    
    # Context display
    context_frame = ttk.LabelFrame(main_frame, text="Context", padding=5)
    context_frame.grid(row=2, column=0, sticky="nsew")
    context_frame.grid_rowconfigure(0, weight=1)
    context_frame.grid_columnconfigure(0, weight=1)
    
    context_text = tk.Text(
        context_frame, wrap="word", bg=text_bg, fg=text_fg,
        font=("Segoe UI", 9), state="disabled"
    )
    context_text.grid(row=0, column=0, sticky="nsew")
    
    context_scrollbar = ttk.Scrollbar(context_frame, orient="vertical", command=context_text.yview)
    context_scrollbar.grid(row=0, column=1, sticky="ns")
    context_text.config(yscrollcommand=context_scrollbar.set)
    
    # Action buttons
    action_frame = ttk.Frame(main_frame)
    action_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
    
    def _apply_correction():
        current = current_error_index.get()
        error = errors[current]
        
        if current in applied_corrections:
            messagebox.showinfo("Already Applied", "This correction has already been applied.")
            return
        
        try:
            # Find and replace the original text with suggestion
            original = error.get("original", "")
            suggestion = error.get("suggestion", "")
            
            if not original or not suggestion:
                messagebox.showerror("Error", "Invalid error data - missing original or suggestion text.")
                return
            
            # Get current editor content
            editor_content = editor.get("1.0", "end-1c")
            
            # Simple replacement - in production, you might want more sophisticated position tracking
            if original in editor_content:
                updated_content = editor_content.replace(original, suggestion, 1)
                editor.delete("1.0", "end")
                editor.insert("1.0", updated_content)
                
                applied_corrections.add(current)
                messagebox.showinfo("Applied", f"Correction applied successfully.")
                
                # Move to next error if available
                if current < len(errors) - 1:
                    _go_next()
            else:
                messagebox.showwarning("Not Found", "The original text was not found in the editor. The text may have been modified.")
                
        except Exception as e:
            debug_console.log(f"Error applying correction: {e}", level='ERROR')
            messagebox.showerror("Error", f"Failed to apply correction: {str(e)}")
    
    def _skip_error():
        if current_error_index.get() < len(errors) - 1:
            _go_next()
        else:
            messagebox.showinfo("Complete", "Reached the end of errors.")
    
    apply_button = ttk.Button(action_frame, text="Apply Correction", command=_apply_correction)
    apply_button.pack(side="left", padx=5)
    
    skip_button = ttk.Button(action_frame, text="Skip", command=_skip_error)
    skip_button.pack(side="left", padx=5)
    
    close_button = ttk.Button(action_frame, text="Close", command=dialog.destroy)
    close_button.pack(side="right", padx=5)
    
    def _show_current_error():
        """Update UI to show current error details."""
        current = current_error_index.get()
        error = errors[current]
        
        # Update error type
        error_type = error.get("type", "Unknown")
        type_value.config(text=error_type)
        
        # Update original text
        original = error.get("original", "")
        original_text_widget.config(state="normal")
        original_text_widget.delete("1.0", "end")
        original_text_widget.insert("1.0", original)
        original_text_widget.config(state="disabled")
        
        # Update suggested text
        suggestion = error.get("suggestion", "")
        suggested_text_widget.config(state="normal")
        suggested_text_widget.delete("1.0", "end")
        suggested_text_widget.insert("1.0", suggestion)
        suggested_text_widget.config(state="disabled")
        
        # Update context - show surrounding text
        context = error.get("context", "")
        if not context:
            # Generate context from original text if not provided
            start_pos = error.get("start", 0)
            end_pos = error.get("end", len(original))
            context_start = max(0, start_pos - 50)
            context_end = min(len(original_text), end_pos + 50)
            context = original_text[context_start:context_end]
        
        context_text.config(state="normal")
        context_text.delete("1.0", "end")
        context_text.insert("1.0", context)
        
        # Highlight the error in context if possible
        if original in context:
            start_idx = context.find(original)
            if start_idx != -1:
                start_pos = f"1.{start_idx}"
                end_pos = f"1.{start_idx + len(original)}"
                context_text.tag_add("error", start_pos, end_pos)
                context_text.tag_config("error", background=error_bg, font=("Segoe UI", 9, "bold"))
        
        context_text.config(state="disabled")
        
        # Update apply button state
        if current in applied_corrections:
            apply_button.config(text="Applied ✓", state="disabled")
        else:
            apply_button.config(text="Apply Correction", state="normal")
    
    # Keyboard shortcuts
    dialog.bind("<Left>", lambda e: _go_previous())
    dialog.bind("<Right>", lambda e: _go_next())
    dialog.bind("<Return>", lambda e: _apply_correction())
    dialog.bind("<Escape>", lambda e: dialog.destroy())
    
    # Initialize display
    _update_navigation()
    dialog.wait_window()

def show_proofreading_interface(root_window, theme_setting_getter_func, editor, text_to_check):
    """
    Display full-screen proofreading interface that stays open during processing.
    
    Args:
        root_window (tk.Tk): Main application window
        theme_setting_getter_func (callable): Function to get theme settings
        editor (tk.Text): Editor widget to apply corrections to
        text_to_check (str): Text to be proofread
    """
    debug_console.log("Opening full-screen proofreading interface.", level='INFO')
    dialog = tk.Toplevel(root_window)
    dialog.title("Document Proofreading")
    dialog.transient(root_window)
    dialog.grab_set()
    dialog.state('zoomed')  # Full screen on Windows
    
    # Theme settings
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    error_bg = theme_setting_getter_func("llm_generated_bg", "#ffe6e6")
    dialog.configure(bg=dialog_bg)
    
    # State variables
    current_error_index = tk.IntVar(value=0)
    applied_corrections = set()
    errors_list = []
    is_processing = tk.BooleanVar(value=False)
    accumulated_response = tk.StringVar(value="")
    
    # Main frame with padding
    main_frame = ttk.Frame(dialog, padding=20)
    main_frame.pack(fill="both", expand=True)
    main_frame.grid_rowconfigure(3, weight=1)  # Make content area expandable
    main_frame.grid_columnconfigure(0, weight=1)
    
    # Title and status
    title_frame = ttk.Frame(main_frame)
    title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
    title_frame.grid_columnconfigure(1, weight=1)
    
    title_label = ttk.Label(title_frame, text="Document Proofreading", font=("Segoe UI", 16, "bold"))
    title_label.grid(row=0, column=0, sticky="w")
    
    status_label = ttk.Label(title_frame, text="Ready", font=("Segoe UI", 10))
    status_label.grid(row=0, column=1, sticky="e")
    
    # Instructions and controls frame
    controls_frame = ttk.Frame(main_frame)
    controls_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
    controls_frame.grid_columnconfigure(1, weight=1)
    
    ttk.Label(controls_frame, text="Custom Instructions:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 10))
    
    instructions_entry = ttk.Entry(controls_frame, font=("Segoe UI", 10))
    instructions_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
    instructions_entry.insert(0, "Focus on grammar and spelling")
    
    start_button = ttk.Button(controls_frame, text="Start Proofreading", bootstyle="success")
    start_button.grid(row=0, column=2, sticky="e")
    
    close_button = ttk.Button(controls_frame, text="Close", command=dialog.destroy)
    close_button.grid(row=0, column=3, sticky="e", padx=(5, 0))
    
    # Progress bar
    progress_frame = ttk.Frame(main_frame)
    progress_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
    progress_frame.grid_columnconfigure(0, weight=1)
    
    progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate", bootstyle="success-striped")
    progress_bar.grid(row=0, column=0, sticky="ew")
    
    progress_label = ttk.Label(progress_frame, text="", font=("Segoe UI", 9))
    progress_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
    
    # Content area - tabbed interface
    content_notebook = ttk.Notebook(main_frame)
    content_notebook.grid(row=3, column=0, sticky="nsew")
    
    # Tab 1: Text preview and streaming output
    preview_frame = ttk.Frame(content_notebook, padding=10)
    content_notebook.add(preview_frame, text="Text & Analysis")
    preview_frame.grid_rowconfigure(0, weight=1)
    preview_frame.grid_rowconfigure(2, weight=1)
    preview_frame.grid_columnconfigure(0, weight=1)
    
    # Original text display
    ttk.Label(preview_frame, text="Original Text:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="nw", pady=(0, 5))
    
    original_text_frame = ttk.Frame(preview_frame)
    original_text_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
    original_text_frame.grid_rowconfigure(0, weight=1)
    original_text_frame.grid_columnconfigure(0, weight=1)
    
    original_text_widget = tk.Text(
        original_text_frame, wrap="word", bg=text_bg, fg=text_fg,
        font=("Segoe UI", 10), state="disabled", height=8
    )
    original_text_widget.grid(row=0, column=0, sticky="nsew")
    
    original_scrollbar = ttk.Scrollbar(original_text_frame, orient="vertical", command=original_text_widget.yview)
    original_scrollbar.grid(row=0, column=1, sticky="ns")
    original_text_widget.config(yscrollcommand=original_scrollbar.set)
    
    # Show original text
    original_text_widget.config(state="normal")
    original_text_widget.insert("1.0", text_to_check)
    original_text_widget.config(state="disabled")
    
    # LLM Response area
    ttk.Label(preview_frame, text="LLM Analysis:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="nw", pady=(10, 5))
    
    response_text_frame = ttk.Frame(preview_frame)
    response_text_frame.grid(row=3, column=0, sticky="nsew")
    response_text_frame.grid_rowconfigure(0, weight=1)
    response_text_frame.grid_columnconfigure(0, weight=1)
    
    response_text_widget = tk.Text(
        response_text_frame, wrap="word", bg=text_bg, fg=text_fg,
        font=("Consolas", 9), state="disabled", height=8
    )
    response_text_widget.grid(row=0, column=0, sticky="nsew")
    
    response_scrollbar = ttk.Scrollbar(response_text_frame, orient="vertical", command=response_text_widget.yview)
    response_scrollbar.grid(row=0, column=1, sticky="ns")
    response_text_widget.config(yscrollcommand=response_scrollbar.set)
    
    # Tab 2: Error navigation (initially hidden)
    errors_frame = ttk.Frame(content_notebook, padding=10)
    
    def _show_errors_tab():
        """Show the errors navigation tab."""
        content_notebook.add(errors_frame, text=f"Errors ({len(errors_list)})")
        content_notebook.select(errors_frame)
        _setup_errors_navigation()
    
    def _setup_errors_navigation():
        """Setup the error navigation interface."""
        if not errors_list:
            return
            
        errors_frame.grid_rowconfigure(2, weight=1)
        errors_frame.grid_columnconfigure(0, weight=1)
        
        # Navigation controls
        nav_frame = ttk.Frame(errors_frame)
        nav_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        nav_frame.grid_columnconfigure(1, weight=1)
        
        def _update_navigation():
            current = current_error_index.get()
            prev_btn.config(state="normal" if current > 0 else "disabled")
            next_btn.config(state="normal" if current < len(errors_list) - 1 else "disabled")
            counter_lbl.config(text=f"{current + 1} of {len(errors_list)}")
            _show_current_error()
        
        def _go_previous():
            if current_error_index.get() > 0:
                current_error_index.set(current_error_index.get() - 1)
                _update_navigation()
        
        def _go_next():
            if current_error_index.get() < len(errors_list) - 1:
                current_error_index.set(current_error_index.get() + 1)
                _update_navigation()
        
        prev_btn = ttk.Button(nav_frame, text="◄ Previous", command=_go_previous)
        prev_btn.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        next_btn = ttk.Button(nav_frame, text="Next ►", command=_go_next)
        next_btn.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        counter_lbl = ttk.Label(nav_frame, text="1 of 1", font=("Segoe UI", 10))
        counter_lbl.grid(row=0, column=2, sticky="w")
        
        # Error details
        error_detail_frame = ttk.LabelFrame(errors_frame, text="Error Details", padding=10)
        error_detail_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        error_detail_frame.grid_columnconfigure(1, weight=1)
        
        type_lbl = ttk.Label(error_detail_frame, text="Type:", font=("Segoe UI", 9, "bold"))
        type_lbl.grid(row=0, column=0, sticky="w", padx=(0, 5))
        type_value = ttk.Label(error_detail_frame, text="", font=("Segoe UI", 9))
        type_value.grid(row=0, column=1, sticky="w")
        
        original_lbl = ttk.Label(error_detail_frame, text="Original:", font=("Segoe UI", 9, "bold"))
        original_lbl.grid(row=1, column=0, sticky="nw", padx=(0, 5), pady=(5, 0))
        original_text = tk.Text(error_detail_frame, height=2, wrap="word", bg=error_bg, fg=text_fg, font=("Segoe UI", 9), state="disabled")
        original_text.grid(row=1, column=1, sticky="ew", pady=(5, 0))
        
        suggested_lbl = ttk.Label(error_detail_frame, text="Suggested:", font=("Segoe UI", 9, "bold"))
        suggested_lbl.grid(row=2, column=0, sticky="nw", padx=(0, 5), pady=(5, 0))
        suggested_text = tk.Text(error_detail_frame, height=2, wrap="word", bg=text_bg, fg=text_fg, font=("Segoe UI", 9), state="disabled")
        suggested_text.grid(row=2, column=1, sticky="ew", pady=(5, 0))
        
        # Context display
        context_frame = ttk.LabelFrame(errors_frame, text="Context", padding=5)
        context_frame.grid(row=2, column=0, sticky="nsew")
        context_frame.grid_rowconfigure(0, weight=1)
        context_frame.grid_columnconfigure(0, weight=1)
        
        context_text = tk.Text(context_frame, wrap="word", bg=text_bg, fg=text_fg, font=("Segoe UI", 9), state="disabled")
        context_text.grid(row=0, column=0, sticky="nsew")
        
        # Action buttons
        action_frame = ttk.Frame(errors_frame)
        action_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        
        def _apply_correction():
            current = current_error_index.get()
            error = errors_list[current]
            
            if current in applied_corrections:
                messagebox.showinfo("Already Applied", "This correction has already been applied.")
                return
            
            try:
                original = error.get("original", "")
                suggestion = error.get("suggestion", "")
                
                if not original or not suggestion:
                    messagebox.showerror("Error", "Invalid error data.")
                    return
                
                # Apply correction to editor
                editor_content = editor.get("1.0", "end-1c")
                if original in editor_content:
                    updated_content = editor_content.replace(original, suggestion, 1)
                    editor.delete("1.0", "end")
                    editor.insert("1.0", updated_content)
                    applied_corrections.add(current)
                    messagebox.showinfo("Applied", "Correction applied successfully.")
                    if current < len(errors_list) - 1:
                        _go_next()
                else:
                    messagebox.showwarning("Not Found", "Original text not found in editor.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply correction: {str(e)}")
        
        apply_btn = ttk.Button(action_frame, text="Apply Correction", command=_apply_correction)
        apply_btn.pack(side="left", padx=5)
        
        skip_btn = ttk.Button(action_frame, text="Skip", command=_go_next)
        skip_btn.pack(side="left", padx=5)
        
        def _show_current_error():
            """Update UI to show current error details."""
            current = current_error_index.get()
            if current >= len(errors_list):
                return
                
            error = errors_list[current]
            type_value.config(text=error.get("type", "Unknown"))
            
            # Update original text
            original_text.config(state="normal")
            original_text.delete("1.0", "end")
            original_text.insert("1.0", error.get("original", ""))
            original_text.config(state="disabled")
            
            # Update suggested text
            suggested_text.config(state="normal")
            suggested_text.delete("1.0", "end")
            suggested_text.insert("1.0", error.get("suggestion", ""))
            suggested_text.config(state="disabled")
            
            # Update context
            context = error.get("context", error.get("original", ""))
            context_text.config(state="normal")
            context_text.delete("1.0", "end")
            context_text.insert("1.0", context)
            context_text.config(state="disabled")
            
            # Update apply button state
            if current in applied_corrections:
                apply_btn.config(text="Applied ✓", state="disabled")
            else:
                apply_btn.config(text="Apply Correction", state="normal")
        
        # Store references for updates
        errors_frame._type_value = type_value
        errors_frame._original_text = original_text
        errors_frame._suggested_text = suggested_text
        errors_frame._context_text = context_text
        errors_frame._apply_btn = apply_btn
        errors_frame._show_current_error = _show_current_error
        errors_frame._update_navigation = _update_navigation
        
        # Initialize display
        _update_navigation()
    
    def _start_proofreading():
        """Start the proofreading process."""
        if is_processing.get():
            return
            
        is_processing.set(True)
        start_button.config(state="disabled", text="Processing...")
        status_label.config(text="Processing...")
        progress_bar.start(10)
        progress_label.config(text="Analyzing text with LLM...")
        
        # Clear previous response
        response_text_widget.config(state="normal")
        response_text_widget.delete("1.0", "end")
        response_text_widget.config(state="disabled")
        accumulated_response.set("")
        
        # Get custom instructions
        custom_instructions = instructions_entry.get().strip()
        instructions_part = f"Additional instructions: {custom_instructions}" if custom_instructions else ""
        
        # Get prompt template
        prompt_template = llm_state._global_default_prompts.get("proofreading")
        if not prompt_template:
            messagebox.showerror("Error", "Proofreading prompt template not found.")
            _reset_ui()
            return
            
        full_prompt = prompt_template.format(
            text_to_check=text_to_check,
            custom_instructions=instructions_part
        )
        
        # Start streaming request
        def on_chunk(chunk):
            current_response = accumulated_response.get() + chunk
            accumulated_response.set(current_response)
            
            # Update response display
            response_text_widget.config(state="normal")
            response_text_widget.delete("1.0", "end")
            response_text_widget.insert("1.0", current_response)
            response_text_widget.see("end")
            response_text_widget.config(state="disabled")
            
        def on_success(final_text):
            _reset_ui()
            try:
                cleaned_response = llm_utils.clean_full_llm_response(final_text)
                debug_console.log(f"Cleaned response (first 200 chars): {cleaned_response[:200]}", level='DEBUG')
                
                # Parse JSON response
                errors_data = json.loads(cleaned_response)
                debug_console.log(f"Parsed JSON successfully", level='INFO')
                
                # Use schema validation for robust error handling
                is_valid, normalized_errors = validate_proofreading_response(errors_data)
                
                if not is_valid:
                    debug_console.log(f"Invalid response structure detected", level='WARNING')
                    debug_console.log(f"Response keys: {list(errors_data.keys()) if isinstance(errors_data, dict) else 'Not a dict'}", level='DEBUG')
                    
                    # Try to handle malformed response gracefully
                    if isinstance(errors_data, list):
                        # Response is a direct array instead of {"errors": [...]}
                        debug_console.log("Response is array instead of object, attempting conversion", level='INFO')
                        is_valid, normalized_errors = validate_proofreading_response({"errors": errors_data})
                    
                    # If still invalid, show a helpful error message
                    if not is_valid:
                        # Check if response looks like metadata extraction instead of proofreading
                        forbidden_fields = ["title", "authors", "journal", "volume", "issue", "pages", "doi", "abstract", "date"]
                        if isinstance(errors_data, dict) and any(field in errors_data for field in forbidden_fields):
                            error_msg = "The LLM extracted document metadata instead of finding proofreading errors. This suggests the model misunderstood the task."
                        else:
                            error_msg = "The LLM response does not match the expected proofreading format."
                        
                        status_label.config(text="Wrong response format")
                        progress_label.config(text=error_msg)
                        messagebox.showerror("Format Error", 
                            f"{error_msg}\n\nPlease try again. If this persists, try a different model or adjust the custom instructions.")
                        return
                
                nonlocal errors_list
                errors_list = normalized_errors
                
                debug_console.log(f"Validated and normalized {len(errors_list)} errors", level='INFO')
                
                if not errors_list:
                    status_label.config(text="No errors found")
                    progress_label.config(text="Analysis complete - no errors detected")
                else:
                    status_label.config(text=f"Found {len(errors_list)} errors")
                    progress_label.config(text=f"Analysis complete - {len(errors_list)} errors found")
                    _show_errors_tab()
                    
            except json.JSONDecodeError as e:
                debug_console.log(f"JSON parsing error: {e}", level='ERROR')
                debug_console.log(f"Raw response: {cleaned_response}", level='ERROR')
                status_label.config(text="Invalid JSON response")
                progress_label.config(text="LLM did not return valid JSON")
                messagebox.showerror("JSON Error", f"The LLM response is not valid JSON. This should not happen with structured output. Raw response is shown in the 'Text & Analysis' tab.")
            except Exception as e:
                debug_console.log(f"Error processing response: {e}", level='ERROR')
                debug_console.log(f"Response data: {cleaned_response}", level='ERROR')
                status_label.config(text="Processing error")
                progress_label.config(text=f"Error: {str(e)}")
                messagebox.showerror("Processing Error", f"Failed to process response: {str(e)}")
        
        def on_error(error_msg):
            _reset_ui()
            status_label.config(text="Request failed")
            progress_label.config(text=f"Error: {error_msg}")
            messagebox.showerror("Request Error", f"Proofreading request failed: {error_msg}")
        
        def _reset_ui():
            is_processing.set(False)
            start_button.config(state="normal", text="Start Proofreading")
            progress_bar.stop()
        
        # Start streaming request with structured output
        json_schema = get_proofreading_schema()
        start_streaming_request(
            editor=editor,
            prompt=full_prompt,
            model_name=llm_state.model_rephrase,
            on_chunk=on_chunk,
            on_success=on_success,
            on_error=on_error,
            task_type="proofreading",
            json_schema=json_schema
        )
    
    # Bind start button
    start_button.config(command=_start_proofreading)
    
    # Keyboard shortcuts
    dialog.bind("<Escape>", lambda e: dialog.destroy())
    dialog.bind("<Return>", lambda e: _start_proofreading() if not is_processing.get() else None)
    
    # Set initial focus
    instructions_entry.focus_set()
    
    dialog.wait_window()