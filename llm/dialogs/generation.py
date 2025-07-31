"""
This module contains the dialog for custom LLM text generation.
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
    llm_generated_bg = theme_setting_getter_func("llm_generated_bg", "#e0e0e0")
    llm_generated_fg = theme_setting_getter_func("llm_generated_fg", "#000000")
    history_bg = theme_setting_getter_func("treeview_bg", "#ffffff")
    prompt_window.configure(bg=dialog_bg);

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
        bg=history_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg,
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
        bg=llm_generated_bg, fg=llm_generated_fg, selectbackground=sel_bg, selectforeground=sel_fg, relief=tk.FLAT, borderwidth=0, highlightthickness=0
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