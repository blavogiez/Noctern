
"""
This module contains functions for displaying various dialogs related to Large Language Model (LLM)
interactions, including text generation, keyword management, and prompt template editing.
These dialogs provide user interfaces for configuring and initiating LLM-related tasks.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils import debug_console

def show_generate_text_dialog(root_window, theme_setting_getter_func,
                              current_prompt_history_list, 
                              on_generate_request_callback, 
                              on_history_entry_add_callback,
                              initial_prompt_text=None):
    """
    Displays a dialog for users to input a custom prompt for LLM text generation.

    This dialog allows users to specify a prompt, context lines from the editor,
    and whether the generation should be LaTeX-oriented. It also displays a history
    of previous prompts and responses.

    Args:
        root_window (tk.Tk): The main Tkinter root window.
        theme_setting_getter_func (callable): Function to get theme settings.
        current_prompt_history_list (list): A list of (user_prompt, llm_response) tuples for history display.
        on_generate_request_callback (callable): Callback function triggered when the user clicks "Generate".
                                                Signature: `(user_prompt, lines_before, lines_after, is_latex_mode)`.
        on_history_entry_add_callback (callable): Callback to add a new entry to the history (e.g., "Generating...").
                                                  Signature: `(user_prompt)`.
        initial_prompt_text (str, optional): Initial text to pre-fill the prompt input area. Defaults to None.
    """
    debug_console.log("Opening LLM text generation dialog.", level='ACTION')
    prompt_window = tk.Toplevel(root_window)
    prompt_window.title("Custom AI Generation")
    prompt_window.transient(root_window) # Make dialog transient to the root window.
    prompt_window.grab_set() # Grab all input until the dialog is closed.
    prompt_window.geometry("800x600")

    # Apply theme settings to the dialog and its widgets.
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")
    prompt_window.configure(bg=dialog_bg)

    # Main Paned Window to divide history and input/controls.
    main_pane = tk.PanedWindow(prompt_window, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.configure(bg=theme_setting_getter_func("panedwindow_sash", "#d0d0d0"))
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)

    # --- Left Pane: Prompt History ---
    history_frame = ttk.Frame(main_pane, padding=(0,0,5,0))
    ttk.Label(history_frame, text="Prompt History:").pack(pady=(0, 5), anchor="w")
    history_listbox_frame = ttk.Frame(history_frame)
    history_listbox_frame.pack(fill="both", expand=True)
    history_listbox = tk.Listbox(
        history_listbox_frame, exportselection=False, font=("Segoe UI", 9),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg,
        highlightthickness=0, borderwidth=0, relief=tk.FLAT
    )
    history_listbox.pack(side="left", fill="both", expand=True)
    history_scrollbar = ttk.Scrollbar(history_listbox_frame, orient="vertical", command=history_listbox.yview)
    history_scrollbar.pack(side="right", fill="y")
    history_listbox.config(yscrollcommand=history_scrollbar.set)
    
    # Populate history listbox.
    if current_prompt_history_list:
        for user_prompt_entry, _ in current_prompt_history_list:
            display_text = f"Q: {user_prompt_entry[:100]}{'...' if len(user_prompt_entry) > 100 else ''}"
            history_listbox.insert(tk.END, display_text)
    else:
        history_listbox.insert(tk.END, "No history yet.")
        history_listbox.config(state=tk.DISABLED) # Disable if no history.
    main_pane.add(history_frame, width=250, minsize=150)

    # --- Right Pane: Input and Controls ---
    input_controls_frame = ttk.Frame(main_pane, padding=(5,0,0,0))
    input_controls_frame.grid_rowconfigure(1, weight=1) # Prompt text area expands.
    input_controls_frame.grid_rowconfigure(6, weight=0) # LLM response area (initially not expanding).
    input_controls_frame.grid_columnconfigure(0, weight=1)
    
    ttk.Label(input_controls_frame, text="Your Prompt:").grid(row=0, column=0, columnspan=2, sticky="nw", padx=5, pady=(0,5))
    prompt_text_frame = ttk.Frame(input_controls_frame)
    prompt_text_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=(0,5), sticky="nsew")
    prompt_text_frame.grid_rowconfigure(0, weight=1)
    prompt_text_frame.grid_columnconfigure(0, weight=1)
    text_prompt = tk.Text(
        prompt_text_frame, height=10, width=50, wrap="word", font=("Segoe UI", 10),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg,
        insertbackground=insert_bg, relief=tk.FLAT, borderwidth=0, highlightthickness=0
    )
    text_prompt.grid(row=0, column=0, sticky="nsew")
    prompt_scrollbar = ttk.Scrollbar(prompt_text_frame, orient="vertical", command=text_prompt.yview)
    prompt_scrollbar.grid(row=0, column=1, sticky="ns")
    text_prompt.config(yscrollcommand=prompt_scrollbar.set)
    if initial_prompt_text: 
        text_prompt.insert("1.0", initial_prompt_text) # Pre-fill prompt if provided.

    # LLM Response Display Area (initially hidden)
    llm_response_label = ttk.Label(input_controls_frame, text="LLM Response:")
    response_text_frame = ttk.Frame(input_controls_frame)
    response_text_frame.grid_rowconfigure(0, weight=1)
    response_text_frame.grid_columnconfigure(0, weight=1)
    text_response = tk.Text(
        response_text_frame, height=10, width=50, wrap="word", state="disabled", font=("Segoe UI", 10),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg, relief=tk.FLAT, borderwidth=0, highlightthickness=0
    )
    
    def on_history_item_selected(event):
        """
        Callback function for when an item in the history listbox is selected.
        Populates the prompt and response text areas with the selected history entry.
        """
        selection_indices = event.widget.curselection()
        if not selection_indices: 
            return
        selected_index = selection_indices[0]
        
        # Ensure the index is valid for the history list.
        if not (0 <= selected_index < len(current_prompt_history_list)): 
            return
        
        selected_user_prompt, selected_llm_response = current_prompt_history_list[selected_index]
        
        # Populate the user prompt text area.
        text_prompt.delete("1.0", tk.END)
        text_prompt.insert("1.0", selected_user_prompt)
        
        # Show and populate the LLM response area.
        llm_response_label.grid(row=5, column=0, columnspan=2, sticky="nw", padx=5, pady=(10,5))
        response_text_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=(0,5), sticky="nsew")
        input_controls_frame.grid_rowconfigure(6, weight=1) # Make response area expandable.
        text_response.grid(row=0, column=0, sticky="nsew")
        response_scrollbar = ttk.Scrollbar(response_text_frame, orient="vertical", command=text_response.yview)
        response_scrollbar.grid(row=0, column=1, sticky="ns")
        text_response.config(yscrollcommand=response_scrollbar.set, state="normal") # Enable for insertion.
        text_response.delete("1.0", tk.END)
        text_response.insert("1.0", selected_llm_response)
        text_response.config(state="disabled") # Disable after insertion.
    
    history_listbox.bind("<<ListboxSelect>>", on_history_item_selected)

    # Context Line Inputs (lines before/after cursor)
    ttk.Label(input_controls_frame, text="Lines before cursor:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    entry_back = ttk.Entry(input_controls_frame, width=10)
    entry_back.insert(0, "5") # Default value.
    entry_back.grid(row=2, column=1, sticky="w", padx=5, pady=5)
    
    ttk.Label(input_controls_frame, text="Lines after cursor:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    entry_forward = ttk.Entry(input_controls_frame, width=10)
    entry_forward.insert(0, "0") # Default value.
    entry_forward.grid(row=3, column=1, sticky="w", padx=5, pady=5)

    # LaTeX Mode Checkbox
    is_latex_mode = tk.BooleanVar() # Variable to store checkbox state.
    options_frame = ttk.Frame(input_controls_frame)
    options_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 0))
    ttk.Checkbutton(options_frame, text="LaTeX oriented generation (uses code model)", variable=is_latex_mode).pack(side=tk.LEFT)

    # Generate Button and its handler.
    def handle_send_prompt_action(event=None):
        """
        Handles the action when the 'Generate' button is clicked or Ctrl+Enter is pressed.
        Validates input, logs the request, and calls the generation callback.
        """
        user_prompt_text = text_prompt.get("1.0", tk.END).strip()
        try:
            num_lines_before = int(entry_back.get())
            num_lines_after = int(entry_forward.get())
        except ValueError:
            messagebox.showerror("Input Error", "Line counts must be valid integers.", parent=prompt_window)
            return
        
        if not user_prompt_text:
            messagebox.showwarning("Warning", "The prompt text area is empty. Please enter a prompt.", parent=prompt_window)
            return
        
        latex_generation_enabled = is_latex_mode.get()
        debug_console.log(f"Generate button clicked. Prompt: '{user_prompt_text[:50]}...', LaTeX mode: {latex_generation_enabled}", level='ACTION')

        # Add a history entry indicating generation is in progress.
        if on_history_entry_add_callback: 
            on_history_entry_add_callback(user_prompt_text)
        
        # Call the main generation request callback.
        if on_generate_request_callback: 
            on_generate_request_callback(user_prompt_text, num_lines_before, num_lines_after, latex_generation_enabled)
        
        prompt_window.destroy() # Close the dialog after initiating generation.
        return "break" # Prevent default event handling

    button_frame = ttk.Frame(input_controls_frame)
    button_frame.grid(row=7, column=0, columnspan=3, pady=(20,0), sticky="ew") 
    ttk.Button(button_frame, text="Generate (Ctrl+Enter)", command=handle_send_prompt_action).pack()
    main_pane.add(input_controls_frame, stretch="always")
    
    # Bind Ctrl+Enter to the send action
    prompt_window.bind("<Control-Return>", handle_send_prompt_action)
    
    text_prompt.focus_set() # Set initial focus to the prompt input area.
    prompt_window.wait_window() # Block until the dialog is closed.


import os
from llm import keyword_history

def show_set_llm_keywords_dialog(root_window, theme_setting_getter_func, file_path):
    """
    Displays a dialog for users to set or update keywords for a specific file.
    Args:
        root_window (tk.Tk): The main Tkinter root window.
        theme_setting_getter_func (callable): Function to get theme settings.
        file_path (str): The absolute path to the file being edited.
    """
    debug_console.log(f"Opening LLM keywords dialog for: {os.path.basename(file_path)}", level='ACTION')
    keyword_window = tk.Toplevel(root_window)
    keyword_window.title(f"Keywords for {os.path.basename(file_path)}")
    keyword_window.transient(root_window)
    keyword_window.grab_set()
    keyword_window.geometry("450x400") # Increased size for better visibility

    # Apply theme settings.
    keyword_window.configure(bg=theme_setting_getter_func("root_bg", "#f0f0f0"))
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")

    # Add a label to explicitly state which file is being edited
    file_label = ttk.Label(keyword_window, text=f"Editing keywords for: {os.path.basename(file_path)}", font=("Segoe UI", 10, "bold"))
    file_label.pack(pady=(10, 0))

    ttk.Label(keyword_window, text="Enter keywords (one per line or comma-separated):").pack(pady=(10, 5))
    keyword_text_frame = ttk.Frame(keyword_window)
    keyword_text_frame.pack(pady=5, padx=10, fill="both", expand=True)
    keyword_text_frame.grid_rowconfigure(0, weight=1); keyword_text_frame.grid_columnconfigure(0, weight=1)
    
    keyword_text_widget = tk.Text(
        keyword_text_frame, height=10, width=45, font=("Segoe UI", 10),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg,
        insertbackground=insert_bg, relief=tk.FLAT, borderwidth=0, highlightthickness=0
    )
    keyword_text_widget.grid(row=0, column=0, sticky="nsew")
    keyword_scrollbar = ttk.Scrollbar(keyword_text_frame, orient="vertical", command=keyword_text_widget.yview)
    keyword_scrollbar.grid(row=0, column=1, sticky="ns")
    keyword_text_widget.config(yscrollcommand=keyword_scrollbar.set)
    
    # Pre-fill with current keywords for the given file.
    current_keywords = keyword_history.get_keywords_for_file(file_path)
    if current_keywords:
        keyword_text_widget.insert(tk.END, "\n".join(current_keywords))

    def save_keywords_action_internal(event=None):
        """
        Internal function to process and save the entered keywords for the file.
        Triggered by button click or Ctrl+Enter.
        """
        input_text = keyword_text_widget.get("1.0", tk.END).strip()
        # Split by newlines, then by commas, strip whitespace, and filter empty strings.
        new_keywords = [kw.strip() for line in input_text.split('\n') for kw in line.split(',') if kw.strip()]
        
        # Set the keywords for the specific file.
        keyword_history.set_keywords_for_file(file_path, new_keywords)
        
        debug_console.log(f"Saved keywords for {os.path.basename(file_path)}: {new_keywords}", level='SUCCESS')
        keyword_window.destroy() # Close the dialog.
        return "break" # Prevent default event handling

    ttk.Button(keyword_window, text="Save Keywords (Ctrl+Enter)", command=save_keywords_action_internal).pack(pady=10)
    
    # Bind Ctrl+Enter to the save action
    keyword_window.bind("<Control-Return>", save_keywords_action_internal)
    
    keyword_text_widget.focus_set() # Set initial focus.
    keyword_window.wait_window() # Block until dialog is closed.



def show_edit_prompts_dialog(root_window, theme_setting_getter_func,
                             current_prompts, default_prompts, on_save_callback):
    """
    Displays a dialog for users to view and edit LLM prompt templates.

    This dialog allows customization of both completion and generation prompts.
    It provides options to restore default prompts and handles unsaved changes.

    Args:
        root_window (tk.Tk): The main Tkinter root window.
        theme_setting_getter_func (callable): Function to get theme settings.
        current_prompts (dict): Dictionary of currently active prompt templates.
        default_prompts (dict): Dictionary of default prompt templates.
        on_save_callback (callable): Callback function triggered when changes are applied.
                                    Signature: `(new_completion_prompt, new_generation_prompt)`.
    """
    debug_console.log("Opening LLM prompt templates editing dialog.", level='ACTION')
    prompts_window = tk.Toplevel(root_window)
    prompts_window.title("Edit LLM Prompt Templates")
    prompts_window.transient(root_window)
    prompts_window.grab_set()
    prompts_window.geometry("1200x700")

    # Apply theme settings.
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")
    prompts_window.configure(bg=dialog_bg)

    # Warning and Placeholder Information.
    warning_frame = ttk.Frame(prompts_window, padding=10)
    warning_frame.pack(fill="x", pady=(5, 0))
    ttk.Label(warning_frame, text="⚠️ Warning: Changes are saved per-document. Available Placeholders: {previous_context}, {current_phrase_start}, {user_prompt}, {keywords}, {context}", wraplength=850, justify="left").pack(fill="x")

    # Paned Window for side-by-side prompt editors.
    main_pane = tk.PanedWindow(prompts_window, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.configure(bg=theme_setting_getter_func("panedwindow_sash", "#d0d0d0"))
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)

    # Store initial state to check for unsaved changes.
    saved_state = {"completion": current_prompts.get("completion", "").strip(), "generation": current_prompts.get("generation", "").strip()}

    def create_prompt_pane(parent_widget, prompt_key, title_text):
        """
        Helper function to create a single prompt editing pane.
        """
        # Determine if the current prompt is using the default template.
        is_using_default = (current_prompts.get(prompt_key, "").strip() == default_prompts.get(prompt_key, "").strip())
        label_display_text = f"{title_text}{' (Using Default)' if is_using_default else ''}"
        
        pane_frame = ttk.Frame(parent_widget)
        labelframe = ttk.LabelFrame(pane_frame, text=label_display_text, padding=5)
        labelframe.pack(pady=5, padx=5, fill="both", expand=True)
        
        text_frame = ttk.Frame(labelframe)
        text_frame.pack(fill="both", expand=True)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        text_widget = tk.Text(
            text_frame, wrap="word", font=("Consolas", 10), bg=text_bg, fg=text_fg,
            selectbackground=sel_bg, selectforeground=sel_fg, insertbackground=insert_bg,
            relief=tk.FLAT, borderwidth=0, highlightthickness=0, undo=True
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text_widget.config(yscrollcommand=scrollbar.set)
        text_widget.insert("1.0", current_prompts.get(prompt_key, "")) # Load current prompt.
        
        return pane_frame, labelframe, text_widget

    # Create panes for completion and generation prompts.
    completion_pane, completion_labelframe, completion_text_widget = create_prompt_pane(main_pane, "completion", "Completion Prompt ('✨ Complete')")
    generation_pane, generation_labelframe, generation_text_widget = create_prompt_pane(main_pane, "generation", "Generation Prompt ('🎯 Generate')")

    def update_default_status_labels():
        """
        Updates the labels of the prompt panes to indicate if they are using default prompts.
        """
        is_completion_default = (completion_text_widget.get("1.0", tk.END).strip() == default_prompts.get("completion", "").strip())
        is_generation_default = (generation_text_widget.get("1.0", tk.END).strip() == default_prompts.get("generation", "").strip())
        
        completion_labelframe.config(text=f"Completion Prompt ('✨ Complete'){' (Using Default)' if is_completion_default else ''}")
        generation_labelframe.config(text=f"Generation Prompt ('🎯 Generate'){' (Using Default)' if is_generation_default else ''}")

    def apply_changes():
        """
        Applies the changes made in the prompt text areas.
        Saves the new prompts and updates the saved state and status labels.
        """
        new_completion_prompt = completion_text_widget.get("1.0", tk.END).strip()
        new_generation_prompt = generation_text_widget.get("1.0", tk.END).strip()
        debug_console.log("Applying prompt template changes.", level='ACTION')
        if on_save_callback: 
            on_save_callback(new_completion_prompt, new_generation_prompt)
        
        saved_state["completion"] = new_completion_prompt
        saved_state["generation"] = new_generation_prompt
        update_default_status_labels() # Refresh labels to reflect default status.
        return "break" # Prevent default event handling.

    def create_buttons_for_pane(parent_frame, text_widget_for_pane, prompt_key_for_pane):
        """
        Helper function to create 'Apply' and 'Restore Default' buttons for a prompt pane.
        """
        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(fill="x", side="bottom", padx=5, pady=(10, 0))
        
        def restore_default_action():
            """
            Restores the prompt in the associated text widget to its default value.
            """
            if messagebox.askyesno("Confirm Restore", f"Are you sure you want to restore the default for the {prompt_key_for_pane.upper()} prompt? This action cannot be undone.", parent=prompts_window):
                debug_console.log(f"Restoring default for {prompt_key_for_pane} prompt.", level='ACTION')
                text_widget_for_pane.delete("1.0", tk.END)
                text_widget_for_pane.insert("1.0", default_prompts.get(prompt_key_for_pane, ""))
                update_default_status_labels() # Update label after restoring default.
        
        ttk.Button(button_frame, text="Apply Changes", command=apply_changes).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Restore Default", command=restore_default_action).pack(side="left")

    # Create buttons for each prompt pane.
    create_buttons_for_pane(completion_pane, completion_text_widget, "completion")
    create_buttons_for_pane(generation_pane, generation_text_widget, "generation")
    
    # Add panes to the main paned window.
    main_pane.add(completion_pane, minsize=400, stretch="always")
    main_pane.add(generation_pane, minsize=400, stretch="always")

    def close_window_handler():
        """
        Handles the window closing event, prompting to save unsaved changes.
        """
        has_unsaved_changes = (
            completion_text_widget.get("1.0", tk.END).strip() != saved_state["completion"] or
            generation_text_widget.get("1.0", tk.END).strip() != saved_state["generation"]
        )
        
        if has_unsaved_changes:
            response = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Do you want to save them before closing?", parent=prompts_window)
            if response is True: 
                apply_changes()
                prompts_window.destroy()
            elif response is False: 
                prompts_window.destroy()
            # If response is None (Cancel), do nothing.
        else:
            prompts_window.destroy() # Close directly if no changes.

    # Bottom bar for the close button.
    bottom_bar = ttk.Frame(prompts_window, padding=(10, 0, 10, 10))
    bottom_bar.pack(fill="x", side="bottom")
    ttk.Button(bottom_bar, text="Close", command=close_window_handler).pack(side="right")

    # Bind Ctrl+S to apply changes.
    prompts_window.bind("<Control-s>", lambda event: apply_changes())
    # Set protocol for window close button.
    prompts_window.protocol("WM_DELETE_WINDOW", close_window_handler)
    prompts_window.wait_window() # Block until the dialog is closed.
