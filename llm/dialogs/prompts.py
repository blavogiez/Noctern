"""
This module contains the dialog for editing LLM prompt templates.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils import debug_console

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
                                    Signature: `(new_completion_prompt, new_generation_prompt, new_styling_prompt)`.
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
    prompts_window.configure(bg=dialog_bg);

    # Paned Window for side-by-side prompt editors.
    main_pane = tk.PanedWindow(prompts_window, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.configure(bg=theme_setting_getter_func("panedwindow_sash", "#d0d0d0"))
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)

    # Store initial state to check for unsaved changes.
    saved_state = {"completion": current_prompts.get("completion", "").strip(), "generation": current_prompts.get("generation", "").strip(), "styling": current_prompts.get("styling", "").strip()}

    placeholders = {
        "completion": "Placeholders: {previous_context}, {current_phrase_start}",
        "generation": "Placeholders: {user_prompt}, {context}, {keywords}",
        "styling": "Placeholders: {text}, {intensity}"
    }

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
        
        # Add placeholder info label
        placeholder_text = placeholders.get(prompt_key, "No specific placeholders.")
        placeholder_label = ttk.Label(labelframe, text=placeholder_text, font=("Segoe UI", 9), foreground="gray")
        placeholder_label.pack(fill="x", padx=5, pady=(0, 5), anchor="w")

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
    styling_pane, styling_labelframe, styling_text_widget = create_prompt_pane(main_pane, "styling", "Styling Prompt ('🎨 Style')")

    def update_default_status_labels():
        """
        Updates the labels of the prompt panes to indicate if they are using default prompts.
        """
        is_completion_default = (completion_text_widget.get("1.0", tk.END).strip() == default_prompts.get("completion", "").strip())
        is_generation_default = (generation_text_widget.get("1.0", tk.END).strip() == default_prompts.get("generation", "").strip())
        is_styling_default = (styling_text_widget.get("1.0", tk.END).strip() == default_prompts.get("styling", "").strip())
        
        completion_labelframe.config(text=f"Completion Prompt ('✨ Complete'){' (Using Default)' if is_completion_default else ''}")
        generation_labelframe.config(text=f"Generation Prompt ('🎯 Generate'){' (Using Default)' if is_generation_default else ''}")
        styling_labelframe.config(text=f"Styling Prompt ('🎨 Style'){' (Using Default)' if is_styling_default else ''}")

    def apply_changes():
        """
        Applies the changes made in the prompt text areas.
        Saves the new prompts and updates the saved state and status labels.
        """
        new_completion_prompt = completion_text_widget.get("1.0", tk.END).strip()
        new_generation_prompt = generation_text_widget.get("1.0", tk.END).strip()
        new_styling_prompt = styling_text_widget.get("1.0", tk.END).strip()
        debug_console.log("Applying prompt template changes.", level='ACTION')
        if on_save_callback: 
            on_save_callback(new_completion_prompt, new_generation_prompt, new_styling_prompt)
        
        saved_state["completion"] = new_completion_prompt
        saved_state["generation"] = new_generation_prompt
        saved_state["styling"] = new_styling_prompt
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
    create_buttons_for_pane(styling_pane, styling_text_widget, "styling")
    
    # Add panes to the main paned window.
    main_pane.add(completion_pane, minsize=400, stretch="always")
    main_pane.add(generation_pane, minsize=400, stretch="always")
    main_pane.add(styling_pane, minsize=400, stretch="always")

    def close_window_handler():
        """
        Handles the window closing event, prompting to save unsaved changes.
        """
        has_unsaved_changes = (
            completion_text_widget.get("1.0", tk.END).strip() != saved_state["completion"] or
            generation_text_widget.get("1.0", tk.END).strip() != saved_state["generation"] or
            styling_text_widget.get("1.0", tk.END).strip() != saved_state["styling"]
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