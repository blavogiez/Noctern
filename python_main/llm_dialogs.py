# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_dialogs.py
"""
Manages dialog windows for LLM (Large Language Model) interactions.

This includes dialogs for generating text from a custom prompt and for
setting LLM keywords.
"""
import tkinter as tk
from tkinter import ttk, messagebox

# Note: The full implementation of these dialogs is extensive and involves
# adapting the Toplevel window code from the original llm_logic.py.
# The following are structural placeholders and key interaction points.

# A list of common languages for the dropdown.
# Sourced from a common list, can be expanded.
_LANGUAGES = [
    "English", "French", "Spanish", "German", "Italian", "Portuguese",
    "Dutch", "Russian", "Chinese (Simplified)", "Japanese", "Korean",
    "Arabic", "Hindi", "Bengali", "Turkish", "Polish", "Swedish",
    "Danish", "Norwegian", "Finnish", "Greek", "Hebrew", "Thai",
    "Vietnamese", "Indonesian", "Malay", "Czech", "Hungarian", "Romanian",
    "the same language as the prompt" # Special option
]

# NEW: To remember the last used language across dialog openings within a session.
_last_used_language = "English"


def show_generate_text_dialog(root_window, theme_setting_getter_func,
                              current_prompt_history_list, # For display
                              on_generate_request_callback, # Called when user clicks "Generate"
                              on_history_entry_add_callback, # Called to add "Generating..." to history
                              initial_prompt_text=None,
                              is_latex_oriented_default=False): # NEW: Default state for LaTeX checkbox
    """
    Displays a dialog for users to input a custom prompt for LLM text generation.

    Args:
        root_window (tk.Tk): The main application window.
        theme_setting_getter_func (function): Function to get current theme settings.
        current_prompt_history_list (list): The current list of prompt-response tuples for display.
        on_generate_request_callback (function): Callback function to be invoked when the
                                                 user confirms the prompt.
                                                 Expected signature: func(user_prompt, lines_before, lines_after, is_latex_oriented, language)
        on_history_entry_add_callback (function): Callback to add the new prompt (with a
                                                  placeholder response) to the main history list.
                                                  Expected signature: func(user_prompt, is_latex_oriented)
        initial_prompt_text (str, optional): Text to pre-fill in the prompt input.
    """
    prompt_window = tk.Toplevel(root_window)
    prompt_window.title("Custom AI Generation")
    prompt_window.transient(root_window)
    prompt_window.grab_set()
    prompt_window.geometry("800x600")

    # Defensive check: Ensure the window is still valid before setting protocol
    if not prompt_window.winfo_exists():
        print("WARNING: Dialog window was destroyed immediately after creation. Aborting setup.")
        return # Exit the function if the window is already gone

    # --- Theming ---
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    dialog_fg = theme_setting_getter_func("fg_color", "#000000")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff") # Use editor_bg for Text widgets
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")
    # ... and so on for other theme elements
    prompt_window.configure(bg=dialog_bg)

    # --- Main Paned Window for History and Input ---
    main_pane = tk.PanedWindow(prompt_window, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.configure(bg=theme_setting_getter_func("panedwindow_sash", "#d0d0d0"))
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)

    # --- Left Pane: History Listbox ---
    history_frame = ttk.Frame(main_pane, padding=(0,0,5,0))
    ttk.Label(history_frame, text="Prompt History:").pack(pady=(0, 5), anchor="w")
    history_listbox_frame = ttk.Frame(history_frame)
    history_listbox_frame.pack(fill="both", expand=True)

    history_listbox = tk.Listbox(
        history_listbox_frame, exportselection=False, font=("Segoe UI", 9),
        bg=text_bg, fg=text_fg,
        selectbackground=sel_bg, selectforeground=sel_fg,
        highlightthickness=0, borderwidth=0, relief=tk.FLAT
    )
    history_listbox.pack(side="left", fill="both", expand=True)

    history_scrollbar = ttk.Scrollbar(history_listbox_frame, orient="vertical", command=history_listbox.yview)
    history_scrollbar.pack(side="right", fill="y")
    history_listbox.config(yscrollcommand=history_scrollbar.set)

    # Populate history_listbox
    for item_user_prompt, _ in current_prompt_history_list:
        display_text = f"Q: {item_user_prompt[:100]}{'...' if len(item_user_prompt) > 100 else ''}"
        history_listbox.insert(tk.END, display_text)
    if not current_prompt_history_list:
        history_listbox.insert(tk.END, "No history yet.")
        history_listbox.config(state=tk.DISABLED)

    main_pane.add(history_frame, width=250, minsize=150)

    # --- Right Pane: Prompt Input and Controls ---
    input_controls_frame = ttk.Frame(main_pane, padding=(5,0,0,0))
    input_controls_frame.grid_rowconfigure(1, weight=1) # Prompt text
    input_controls_frame.grid_rowconfigure(8, weight=0) # Response text (initially hidden)
    input_controls_frame.grid_columnconfigure(0, weight=1)

    ttk.Label(input_controls_frame, text="Your Prompt:").grid(row=0, column=0, columnspan=2, sticky="nw", padx=5, pady=(0,5))
    prompt_text_frame = ttk.Frame(input_controls_frame) # Frame for Text and Scrollbar
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
        text_prompt.insert("1.0", initial_prompt_text)

    # --- LLM Response Display Area (shown on history selection) ---
    llm_response_label = ttk.Label(input_controls_frame, text="LLM Response:")
    response_text_frame = ttk.Frame(input_controls_frame) # Frame for Text and Scrollbar
    response_text_frame.grid_rowconfigure(0, weight=1)
    response_text_frame.grid_columnconfigure(0, weight=1)
    text_response = tk.Text(
        response_text_frame, height=10, width=50, wrap="word", state="disabled", font=("Segoe UI", 10),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg, relief=tk.FLAT, borderwidth=0, highlightthickness=0
    )

    def on_history_item_selected(event):
        # When a history item is clicked, show its prompt in text_prompt
        # and its response in text_response.
        widget = event.widget
        selection = widget.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(current_prompt_history_list):
                selected_user_prompt, selected_llm_response = current_prompt_history_list[index]
                text_prompt.delete("1.0", tk.END)
                text_prompt.insert("1.0", selected_user_prompt)

                llm_response_label.grid(row=7, column=0, columnspan=2, sticky="nw", padx=5, pady=(10,5))
                response_text_frame.grid(row=8, column=0, columnspan=2, padx=5, pady=(0,5), sticky="nsew")
                input_controls_frame.grid_rowconfigure(8, weight=1)
                text_response.grid(row=0, column=0, sticky="nsew") # Inside response_text_frame
                response_scrollbar = ttk.Scrollbar(response_text_frame, orient="vertical", command=text_response.yview)
                response_scrollbar.grid(row=0, column=1, sticky="ns")
                text_response.config(yscrollcommand=response_scrollbar.set)

                text_response.config(state="normal")
                text_response.delete("1.0", tk.END)
                text_response.insert("1.0", selected_llm_response)
                text_response.config(state="disabled")
            else: # "No history yet." or invalid
                llm_response_label.grid_remove()
                response_text_frame.grid_remove()
                input_controls_frame.grid_rowconfigure(8, weight=0)
        # ... (handle deselection: clear response area)

    history_listbox.bind("<<ListboxSelect>>", on_history_item_selected)

    # --- Context Line Inputs ---
    ttk.Label(input_controls_frame, text="Lines before cursor:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    entry_back = ttk.Entry(input_controls_frame, width=10)
    entry_back.insert(0, "5")
    entry_back.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(input_controls_frame, text="Lines after cursor:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    entry_forward = ttk.Entry(input_controls_frame, width=10)
    entry_forward.insert(0, "0")
    entry_forward.grid(row=3, column=1, sticky="w", padx=5, pady=5)

    # NEW: Language Input with Combobox
    ttk.Label(input_controls_frame, text="Response Language:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
    language_var = tk.StringVar(prompt_window)
    lang_combobox = ttk.Combobox(input_controls_frame, textvariable=language_var, values=_LANGUAGES, width=25)
    # Set the default/last-used language
    if _last_used_language in _LANGUAGES:
        lang_combobox.set(_last_used_language)
    else:
        lang_combobox.set("English") # Fallback
    lang_combobox.grid(row=4, column=1, sticky="w", padx=5, pady=5)

    # NEW: LaTeX Oriented Checkbox
    is_latex_oriented_var = tk.BooleanVar(prompt_window, value=is_latex_oriented_default)
    ttk.Checkbutton(input_controls_frame, text="LaTeX Oriented Generation", variable=is_latex_oriented_var).grid(
        row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    # --- Unified Cleanup Logic ---
    def cleanup_and_close():
        text_prompt.delete("1.0", tk.END)
        text_response.config(state="normal") # Enable to clear
        text_response.delete("1.0", tk.END)
        text_response.config(state="disabled")
        prompt_window.destroy()

    # --- Generate Button ---
    def handle_send_prompt_action():
        user_prompt = text_prompt.get("1.0", tk.END).strip()
        try:
            num_back = int(entry_back.get())
            num_forward = int(entry_forward.get())
        except ValueError:
            messagebox.showerror("Input Error", "Line counts must be integers.", parent=prompt_window)
            return

        if not user_prompt:
            messagebox.showwarning("Warning", "The prompt is empty.", parent=prompt_window)
            return

        # NEW: Get language and remember it for next time
        global _last_used_language
        language = language_var.get().strip()
        if not language:
            language = "the same language as the prompt" # Fallback if field is cleared
        _last_used_language = language
        
        is_latex_oriented = is_latex_oriented_var.get() # Get the state of the checkbox
        # 1. Call back to add "Generating..." to history immediately
        if on_history_entry_add_callback:
            # Adjust placeholder message based on LaTeX orientation
            on_history_entry_add_callback(user_prompt, is_latex_oriented)
        # 2. Call back to trigger the actual LLM generation process
        if on_generate_request_callback:
            on_generate_request_callback(user_prompt, num_back, num_forward, is_latex_oriented, language)

        cleanup_and_close()

    button_frame = ttk.Frame(input_controls_frame)
    button_frame.grid(row=6, column=0, columnspan=3, pady=(10,0), sticky="ew") # Adjusted row
    ttk.Button(button_frame, text="Generate", command=handle_send_prompt_action).pack()

    main_pane.add(input_controls_frame, stretch="always")
    prompt_window.grid_rowconfigure(0, weight=1)
    prompt_window.grid_columnconfigure(0, weight=1)

    text_prompt.focus()
    prompt_window.protocol("WM_DELETE_WINDOW", cleanup_and_close)
    prompt_window.wait_window()


def show_set_llm_keywords_dialog(root_window, theme_setting_getter_func,
                                 current_llm_keywords_list, # For pre-filling
                                 on_save_keywords_callback): # Called when user clicks "Save"
    """
    Displays a dialog for users to set or update LLM keywords.

    Args:
        root_window (tk.Tk): The main application window.
        theme_setting_getter_func (function): Function to get current theme settings.
        current_llm_keywords_list (list): The current list of LLM keywords.
        on_save_keywords_callback (function): Callback function to be invoked when the
                                              user saves the keywords.
                                              Expected signature: func(new_keywords_list)
    """
    keyword_window = tk.Toplevel(root_window)
    keyword_window.title("Set LLM Keywords")
    keyword_window.transient(root_window)
    keyword_window.grab_set()
    keyword_window.geometry("400x300")

    # --- Theming (simplified) ---
    keyword_window.configure(bg=theme_setting_getter_func("root_bg", "#f0f0f0"))
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff") # Use editor_bg for Text widgets
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")

    ttk.Label(keyword_window, text="Enter keywords (one per line or comma-separated):").pack(pady=(10,5))

    keyword_text_frame = ttk.Frame(keyword_window) # Frame for Text and Scrollbar
    keyword_text_frame.pack(pady=5, padx=10, fill="both", expand=True)
    keyword_text_frame.grid_rowconfigure(0, weight=1)
    keyword_text_frame.grid_columnconfigure(0, weight=1)

    keyword_text_widget = tk.Text(
        keyword_text_frame, height=10, width=45, font=("Segoe UI", 10),
        bg=text_bg, fg=text_fg,
        selectbackground=sel_bg, selectforeground=sel_fg,
        insertbackground=insert_bg, relief=tk.FLAT, borderwidth=0, highlightthickness=0
    )
    keyword_text_widget.grid(row=0, column=0, sticky="nsew")
    keyword_scrollbar = ttk.Scrollbar(keyword_text_frame, orient="vertical", command=keyword_text_widget.yview)
    keyword_scrollbar.grid(row=0, column=1, sticky="ns")
    keyword_text_widget.config(yscrollcommand=keyword_scrollbar.set)

    if current_llm_keywords_list:
        keyword_text_widget.insert(tk.END, "\n".join(current_llm_keywords_list))

    def save_keywords_action_internal():
        input_text = keyword_text_widget.get("1.0", tk.END).strip()
        new_keywords = []
        if input_text:
            raw_keywords = []
            for line in input_text.split('\n'):
                raw_keywords.extend(kw.strip() for kw in line.split(','))
            new_keywords = [kw for kw in raw_keywords if kw] # Filter out empty

        if on_save_keywords_callback:
            on_save_keywords_callback(new_keywords) # Pass the processed list

        keyword_text_widget.delete("1.0", tk.END) # Explicitly clear content
        keyword_window.destroy()

    ttk.Button(keyword_window, text="Save Keywords", command=save_keywords_action_internal).pack(pady=10)
    keyword_text_widget.focus()

    def on_keywords_dialog_close():
        keyword_text_widget.delete("1.0", tk.END)
        keyword_window.destroy()
    keyword_window.protocol("WM_DELETE_WINDOW", on_keywords_dialog_close)
    keyword_window.wait_window()

def show_edit_prompts_dialog(root_window, theme_setting_getter_func,
                             current_prompts,
                             default_prompts,
                             on_save_callback):
    """
    Displays a dialog for users to edit the LLM prompt templates.
    """
    prompts_window = tk.Toplevel(root_window)
    prompts_window.title("Edit LLM Prompt Templates")
    prompts_window.transient(root_window)
    prompts_window.grab_set()
    prompts_window.geometry("1200x700") # Wider for side-by-side layout

    # --- Theming ---
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")
    prompts_window.configure(bg=dialog_bg)

    # --- Warning Message ---
    warning_frame = ttk.Frame(prompts_window, padding=10)
    warning_frame.pack(fill="x", pady=(5, 0))
    warning_label = ttk.Label(
        warning_frame,
        text="⚠️ Warning: Modifying these prompts can significantly affect AI behavior and performance. "
             "Changes are saved per-document.\n"
             "Available placeholders for Completion: {previous_context}, {current_phrase_start}, {keywords}\n"
             "Available placeholders for Generation: {user_prompt}, {keywords}, {context}, {language}",
        wraplength=850,
        justify="left"
    )
    warning_label.pack(fill="x")

    # --- Main Paned Window (HORIZONTAL for side-by-side) ---
    main_pane = tk.PanedWindow(prompts_window, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.configure(bg=theme_setting_getter_func("panedwindow_sash", "#d0d0d0"))
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)

    # --- State Tracking ---
    saved_state = {
        "completion": current_prompts.get("completion", "").strip(),
        "generation": current_prompts.get("generation", "").strip(),
        "latex_code_generation": current_prompts.get("latex_code_generation", "").strip() # NEW
    }

    # ===================================================================
    # --- Left Pane: Completion Prompt
    # ===================================================================
    # Renamed from completion_pane_frame to completion_pane_frame
    completion_pane_frame = ttk.Frame(main_pane)

    is_completion_default = (current_prompts.get("completion", "").strip() == default_prompts.get("completion", "").strip())
    completion_label_text = "Completion Prompt ('✨ Complete')"
    if is_completion_default:
        completion_label_text += " (Using Default)"
    completion_labelframe = ttk.LabelFrame(completion_pane_frame, text=completion_label_text, padding=5)
    completion_labelframe.pack(pady=5, padx=5, fill="both", expand=True)
    
    completion_text_frame = ttk.Frame(completion_labelframe)
    completion_text_frame.pack(fill="both", expand=True)
    completion_text_frame.grid_rowconfigure(0, weight=1)
    completion_text_frame.grid_columnconfigure(0, weight=1)

    completion_text = tk.Text(
        completion_text_frame, wrap="word", font=("Consolas", 10),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg,
        insertbackground=insert_bg, relief=tk.FLAT, borderwidth=0, highlightthickness=0, undo=True
    )
    completion_text.grid(row=0, column=0, sticky="nsew")
    completion_scrollbar = ttk.Scrollbar(completion_text_frame, orient="vertical", command=completion_text.yview)
    completion_scrollbar.grid(row=0, column=1, sticky="ns")
    completion_text.config(yscrollcommand=completion_scrollbar.set)
    completion_text.insert("1.0", current_prompts.get("completion", ""))

    # ===================================================================
    # --- Middle Pane: LaTeX Code Generation Prompt (NEW)
    # ===================================================================
    latex_code_pane_frame = ttk.Frame(main_pane)

    is_latex_code_default = (current_prompts.get("latex_code_generation", "").strip() == default_prompts.get("latex_code_generation", "").strip())
    latex_code_label_text = "LaTeX Code Generation Prompt ('💻 Code LaTeX')"
    if is_latex_code_default:
        latex_code_label_text += " (Using Default)"
    latex_code_labelframe = ttk.LabelFrame(latex_code_pane_frame, text=latex_code_label_text, padding=5)
    latex_code_labelframe.pack(pady=5, padx=5, fill="both", expand=True)
    
    latex_code_text_frame = ttk.Frame(latex_code_labelframe)
    latex_code_text_frame.pack(fill="both", expand=True)
    latex_code_text_frame.grid_rowconfigure(0, weight=1)
    latex_code_text_frame.grid_columnconfigure(0, weight=1)

    latex_code_text = tk.Text(
        latex_code_text_frame, wrap="word", font=("Consolas", 10),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg,
        insertbackground=insert_bg, relief=tk.FLAT, borderwidth=0, highlightthickness=0, undo=True
    )
    latex_code_text.grid(row=0, column=0, sticky="nsew")
    latex_code_scrollbar = ttk.Scrollbar(latex_code_text_frame, orient="vertical", command=latex_code_text.yview)
    latex_code_scrollbar.grid(row=0, column=1, sticky="ns")
    latex_code_text.config(yscrollcommand=latex_code_scrollbar.set)
    # If the current prompt is empty, pre-fill with the default LaTeX code generation prompt.
    # This ensures that if a document's prompt file was saved with an empty LaTeX prompt,
    # the user sees the full default prompt when editing.
    latex_code_text.insert("1.0", current_prompts.get("latex_code_generation", default_prompts.get("latex_code_generation", "")))

    # Add the new pane to the main PanedWindow
    main_pane.add(latex_code_pane_frame, minsize=400, stretch="always")

    # ===================================================================
    # --- Right Pane: Generation Prompt
    # ===================================================================
    generation_pane_frame = ttk.Frame(main_pane)

    is_generation_default = (current_prompts.get("generation", "").strip() == default_prompts.get("generation", "").strip())
    generation_label_text = "Generation Prompt ('🎯 Generate')"
    if is_generation_default:
        generation_label_text += " (Using Default)"
    generation_labelframe = ttk.LabelFrame(generation_pane_frame, text=generation_label_text, padding=5)
    generation_labelframe.pack(pady=5, padx=5, fill="both", expand=True)
    
    generation_text_frame = ttk.Frame(generation_labelframe)
    generation_text_frame.pack(fill="both", expand=True)
    generation_text_frame.grid_rowconfigure(0, weight=1)
    generation_text_frame.grid_columnconfigure(0, weight=1)

    generation_text = tk.Text(
        generation_text_frame, wrap="word", font=("Consolas", 10),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg,
        insertbackground=insert_bg, relief=tk.FLAT, borderwidth=0, highlightthickness=0, undo=True
    )
    generation_text.grid(row=0, column=0, sticky="nsew")
    generation_scrollbar = ttk.Scrollbar(generation_text_frame, orient="vertical", command=generation_text.yview)
    generation_scrollbar.grid(row=0, column=1, sticky="ns")
    generation_text.config(yscrollcommand=generation_scrollbar.set)
    generation_text.insert("1.0", current_prompts.get("generation", ""))

    # --- Helper function to update the "Using Default" labels ---
    def update_default_status_labels():
        is_completion_default_now = (completion_text.get("1.0", tk.END).strip() == default_prompts.get("completion", "").strip())
        is_latex_code_default_now = (latex_code_text.get("1.0", tk.END).strip() == default_prompts.get("latex_code_generation", "").strip()) # NEW
        is_generation_default_now = (generation_text.get("1.0", tk.END).strip() == default_prompts.get("generation", "").strip())

        completion_labelframe.config(text=f"Completion Prompt ('✨ Complete'){' (Using Default)' if is_completion_default_now else ''}")
        latex_code_labelframe.config(text=f"LaTeX Code Generation Prompt ('💻 Code LaTeX'){' (Using Default)' if is_latex_code_default_now else ''}") # NEW
        generation_labelframe.config(text=f"Generation Prompt ('🎯 Generate'){' (Using Default)' if is_generation_default_now else ''}")

    # --- Core Action: Apply Changes --- # Renamed from apply_changes to apply_changes
    def apply_changes():
        """Saves changes for BOTH prompts to the file but does not close the window."""
        new_completion = completion_text.get("1.0", tk.END).strip()
        new_generation = generation_text.get("1.0", tk.END).strip()
        new_latex_code_generation = latex_code_text.get("1.0", tk.END).strip() # NEW

        if on_save_callback: # Renamed from on_save_callback to on_save_callback
            on_save_callback(new_completion, new_generation, new_latex_code_generation) # Pass new LaTeX prompt

        saved_state["completion"] = new_completion
        saved_state["generation"] = new_generation
        saved_state["latex_code_generation"] = new_latex_code_generation # FIX: Update saved state for latex prompt

        update_default_status_labels()
        return "break"  # Prevents other bindings from firing

    # --- Buttons for Completion Pane ---
    completion_button_frame = ttk.Frame(completion_pane_frame)
    completion_button_frame.pack(fill="x", side="bottom", padx=5, pady=(10, 0))

    def restore_completion_default():
        if messagebox.askyesno("Confirm Restore",
                               "Are you sure you want to restore the default for the COMPLETION prompt?",
                               parent=prompts_window):
            completion_text.delete("1.0", tk.END)
            completion_text.insert("1.0", default_prompts.get("completion", ""))
            update_default_status_labels()

    ttk.Button(completion_button_frame, text="Apply", command=apply_changes).pack(side="left", padx=(0, 5))
    ttk.Button(completion_button_frame, text="Restore Default", command=restore_completion_default).pack(side="left")
    main_pane.add(completion_pane_frame, minsize=400, stretch="always")

    # --- Buttons for LaTeX Code Pane (NEW) ---
    latex_code_button_frame = ttk.Frame(latex_code_pane_frame)
    latex_code_button_frame.pack(fill="x", side="bottom", padx=5, pady=(10, 0))

    def restore_latex_code_default():
        if messagebox.askyesno("Confirm Restore",
                               "Are you sure you want to restore the default for the LaTeX CODE GENERATION prompt?",
                               parent=prompts_window):
            latex_code_text.delete("1.0", tk.END)
            latex_code_text.insert("1.0", default_prompts.get("latex_code_generation", ""))
            update_default_status_labels()

    ttk.Button(latex_code_button_frame, text="Apply", command=apply_changes).pack(side="left", padx=(0, 5))
    ttk.Button(latex_code_button_frame, text="Restore Default", command=restore_latex_code_default).pack(side="left")
    # --- Buttons for Generation Pane ---
    generation_button_frame = ttk.Frame(generation_pane_frame)
    generation_button_frame.pack(fill="x", side="bottom", padx=5, pady=(10, 0))

    def restore_generation_default():
        if messagebox.askyesno("Confirm Restore",
                               "Are you sure you want to restore the default for the GENERATION prompt?",
                               parent=prompts_window):
            generation_text.delete("1.0", tk.END)
            generation_text.insert("1.0", default_prompts.get("generation", ""))
            update_default_status_labels()

    ttk.Button(generation_button_frame, text="Apply", command=apply_changes).pack(side="left", padx=(0, 5))
    ttk.Button(generation_button_frame, text="Restore Default", command=restore_generation_default).pack(side="left")
    main_pane.add(generation_pane_frame, minsize=400, stretch="always")

    # --- Bottom Bar with Close Button ---
    bottom_bar = ttk.Frame(prompts_window, padding=(10, 0, 10, 10))
    bottom_bar.pack(fill="x", side="bottom")

    def close_window():
        current_completion = completion_text.get("1.0", tk.END).strip()
        current_latex_code_generation = latex_code_text.get("1.0", tk.END).strip() # NEW
        current_generation = generation_text.get("1.0", tk.END).strip()
        has_changes = (current_completion != saved_state["completion"] or
                       current_latex_code_generation != saved_state["latex_code_generation"] or # NEW
                       current_generation != saved_state["generation"])

        if has_changes:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                parent=prompts_window
            )
            if response is True:  # Yes
                apply_changes()
                prompts_window.destroy()
            elif response is False: # No
                prompts_window.destroy()
            # else: Cancel, do nothing, so don't destroy the window
        else:
            prompts_window.destroy()
        # Always clear content on close, regardless of save status
        completion_text.delete("1.0", tk.END)
        latex_code_text.delete("1.0", tk.END) # NEW
        generation_text.delete("1.0", tk.END)

    ttk.Button(bottom_bar, text="Close", command=close_window).pack(side="right")

    # Bind Ctrl+S for saving without closing
    prompts_window.bind("<Control-s>", lambda event: apply_changes())

    # Intercept the window close ('X') button
    prompts_window.protocol("WM_DELETE_WINDOW", close_window)
    prompts_window.wait_window()