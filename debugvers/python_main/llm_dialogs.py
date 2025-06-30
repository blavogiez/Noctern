import tkinter as tk
from tkinter import ttk, messagebox
import debug_console

def show_generate_text_dialog(root_window, theme_setting_getter_func,
                              current_prompt_history_list, # For display
                              on_generate_request_callback, # Called when user clicks "Generate"
                              on_history_entry_add_callback, # Called to add "Generating..." to history
                              initial_prompt_text=None):
    """
    Displays a dialog for users to input a custom prompt for LLM text generation.
    """
    prompt_window = tk.Toplevel(root_window)
    prompt_window.title("Custom AI Generation")
    prompt_window.transient(root_window)
    prompt_window.grab_set()
    prompt_window.geometry("800x600")

    # Theming
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")
    prompt_window.configure(bg=dialog_bg)

    # Main Paned Window
    main_pane = tk.PanedWindow(prompt_window, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.configure(bg=theme_setting_getter_func("panedwindow_sash", "#d0d0d0"))
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)

    # Left Pane: History
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
    for item_user_prompt, _ in current_prompt_history_list:
        display_text = f"Q: {item_user_prompt[:100]}{'...' if len(item_user_prompt) > 100 else ''}"
        history_listbox.insert(tk.END, display_text)
    if not current_prompt_history_list:
        history_listbox.insert(tk.END, "No history yet.")
        history_listbox.config(state=tk.DISABLED)
    main_pane.add(history_frame, width=250, minsize=150)

    # Right Pane: Input and Controls
    input_controls_frame = ttk.Frame(main_pane, padding=(5,0,0,0))
    input_controls_frame.grid_rowconfigure(1, weight=1)
    input_controls_frame.grid_rowconfigure(6, weight=0)
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
    if initial_prompt_text: text_prompt.insert("1.0", initial_prompt_text)

    # LLM Response Display
    llm_response_label = ttk.Label(input_controls_frame, text="LLM Response:")
    response_text_frame = ttk.Frame(input_controls_frame)
    response_text_frame.grid_rowconfigure(0, weight=1)
    response_text_frame.grid_columnconfigure(0, weight=1)
    text_response = tk.Text(
        response_text_frame, height=10, width=50, wrap="word", state="disabled", font=("Segoe UI", 10),
        bg=text_bg, fg=text_fg, selectbackground=sel_bg, selectforeground=sel_fg, relief=tk.FLAT, borderwidth=0, highlightthickness=0
    )
    def on_history_item_selected(event):
        selection = event.widget.curselection()
        if not selection: return
        index = selection[0]
        if not (0 <= index < len(current_prompt_history_list)): return
        selected_user_prompt, selected_llm_response = current_prompt_history_list[index]
        text_prompt.delete("1.0", tk.END); text_prompt.insert("1.0", selected_user_prompt)
        llm_response_label.grid(row=5, column=0, columnspan=2, sticky="nw", padx=5, pady=(10,5))
        response_text_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=(0,5), sticky="nsew")
        input_controls_frame.grid_rowconfigure(6, weight=1)
        text_response.grid(row=0, column=0, sticky="nsew")
        response_scrollbar = ttk.Scrollbar(response_text_frame, orient="vertical", command=text_response.yview)
        response_scrollbar.grid(row=0, column=1, sticky="ns")
        text_response.config(yscrollcommand=response_scrollbar.set, state="normal")
        text_response.delete("1.0", tk.END); text_response.insert("1.0", selected_llm_response)
        text_response.config(state="disabled")
    history_listbox.bind("<<ListboxSelect>>", on_history_item_selected)

    # Context Line Inputs
    ttk.Label(input_controls_frame, text="Lines before cursor:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    entry_back = ttk.Entry(input_controls_frame, width=10); entry_back.insert(0, "5")
    entry_back.grid(row=2, column=1, sticky="w", padx=5, pady=5)
    ttk.Label(input_controls_frame, text="Lines after cursor:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    entry_forward = ttk.Entry(input_controls_frame, width=10); entry_forward.insert(0, "0")
    entry_forward.grid(row=3, column=1, sticky="w", padx=5, pady=5)

    # LaTeX Mode Checkbox
    is_latex_mode = tk.BooleanVar()
    options_frame = ttk.Frame(input_controls_frame)
    options_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 0))
    ttk.Checkbutton(options_frame, text="LaTeX oriented generation (uses code model)", variable=is_latex_mode).pack(side=tk.LEFT)

    # Generate Button
    def handle_send_prompt_action():
        user_prompt = text_prompt.get("1.0", tk.END).strip()
        try:
            num_back = int(entry_back.get()); num_forward = int(entry_forward.get())
        except ValueError:
            messagebox.showerror("Input Error", "Line counts must be integers.", parent=prompt_window); return
        if not user_prompt:
            messagebox.showwarning("Warning", "The prompt is empty.", parent=prompt_window); return
        
        latex_enabled = is_latex_mode.get()
        debug_console.log(f"Generate button clicked. Prompt: '{user_prompt[:50]}...', LaTeX mode: {latex_enabled}", level='ACTION')

        if on_history_entry_add_callback: on_history_entry_add_callback(user_prompt)
        if on_generate_request_callback: on_generate_request_callback(user_prompt, num_back, num_forward, latex_enabled)
        prompt_window.destroy()

    button_frame = ttk.Frame(input_controls_frame)
    button_frame.grid(row=7, column=0, columnspan=3, pady=(20,0), sticky="ew") 
    ttk.Button(button_frame, text="Generate", command=handle_send_prompt_action).pack()
    main_pane.add(input_controls_frame, stretch="always")
    
    text_prompt.focus()
    prompt_window.wait_window()


def show_set_llm_keywords_dialog(root_window, theme_setting_getter_func,
                                 current_llm_keywords_list, on_save_keywords_callback):
    """Displays a dialog for users to set or update LLM keywords."""
    keyword_window = tk.Toplevel(root_window)
    keyword_window.title("Set LLM Keywords")
    keyword_window.transient(root_window)
    keyword_window.grab_set()
    keyword_window.geometry("400x300")

    # Theming
    keyword_window.configure(bg=theme_setting_getter_func("root_bg", "#f0f0f0"))
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")

    ttk.Label(keyword_window, text="Enter keywords (one per line or comma-separated):").pack(pady=(10,5))
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
    if current_llm_keywords_list: keyword_text_widget.insert(tk.END, "\n".join(current_llm_keywords_list))

    def save_keywords_action_internal():
        input_text = keyword_text_widget.get("1.0", tk.END).strip()
        new_keywords = [kw.strip() for line in input_text.split('\n') for kw in line.split(',') if kw.strip()]
        debug_console.log(f"Saving keywords: {new_keywords}", level='ACTION')
        if on_save_keywords_callback: on_save_keywords_callback(new_keywords)
        keyword_window.destroy()

    ttk.Button(keyword_window, text="Save Keywords", command=save_keywords_action_internal).pack(pady=10)
    keyword_text_widget.focus()
    keyword_window.wait_window()


def show_edit_prompts_dialog(root_window, theme_setting_getter_func,
                             current_prompts, default_prompts, on_save_callback):
    """Displays a dialog for users to edit the LLM prompt templates."""
    prompts_window = tk.Toplevel(root_window)
    prompts_window.title("Edit LLM Prompt Templates")
    prompts_window.transient(root_window)
    prompts_window.grab_set()
    prompts_window.geometry("1200x700")

    # Theming
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    sel_bg = theme_setting_getter_func("sel_bg", "#0078d4")
    sel_fg = theme_setting_getter_func("sel_fg", "#ffffff")
    insert_bg = theme_setting_getter_func("editor_insert_bg", "#000000")
    prompts_window.configure(bg=dialog_bg)

    # Warning
    warning_frame = ttk.Frame(prompts_window, padding=10)
    warning_frame.pack(fill="x", pady=(5, 0))
    ttk.Label(warning_frame, text="⚠️ Warning: Changes are saved per-document. Placeholders: {previous_context}, {current_phrase_start}, {user_prompt}, {keywords}, {context}", wraplength=850, justify="left").pack(fill="x")

    # Paned Window
    main_pane = tk.PanedWindow(prompts_window, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    main_pane.configure(bg=theme_setting_getter_func("panedwindow_sash", "#d0d0d0"))
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)

    saved_state = {"completion": current_prompts.get("completion", "").strip(), "generation": current_prompts.get("generation", "").strip()}

    # Helper to create a prompt editor pane
    def create_prompt_pane(parent, prompt_key, title_text):
        is_default = (current_prompts.get(prompt_key, "").strip() == default_prompts.get(prompt_key, "").strip())
        label_text = f"{title_text}{' (Using Default)' if is_default else ''}"
        
        pane_frame = ttk.Frame(parent)
        labelframe = ttk.LabelFrame(pane_frame, text=label_text, padding=5)
        labelframe.pack(pady=5, padx=5, fill="both", expand=True)
        
        text_frame = ttk.Frame(labelframe); text_frame.pack(fill="both", expand=True)
        text_frame.grid_rowconfigure(0, weight=1); text_frame.grid_columnconfigure(0, weight=1)
        
        text_widget = tk.Text(
            text_frame, wrap="word", font=("Consolas", 10), bg=text_bg, fg=text_fg,
            selectbackground=sel_bg, selectforeground=sel_fg, insertbackground=insert_bg,
            relief=tk.FLAT, borderwidth=0, highlightthickness=0, undo=True
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text_widget.config(yscrollcommand=scrollbar.set)
        text_widget.insert("1.0", current_prompts.get(prompt_key, ""))
        
        return pane_frame, labelframe, text_widget

    completion_pane, completion_labelframe, completion_text = create_prompt_pane(main_pane, "completion", "Completion Prompt ('✨ Complete')")
    generation_pane, generation_labelframe, generation_text = create_prompt_pane(main_pane, "generation", "Generation Prompt ('🎯 Generate')")

    def update_default_status_labels():
        is_comp_def = (completion_text.get("1.0", tk.END).strip() == default_prompts.get("completion", "").strip())
        is_gen_def = (generation_text.get("1.0", tk.END).strip() == default_prompts.get("generation", "").strip())
        completion_labelframe.config(text=f"Completion Prompt ('✨ Complete'){' (Using Default)' if is_comp_def else ''}")
        generation_labelframe.config(text=f"Generation Prompt ('🎯 Generate'){' (Using Default)' if is_gen_def else ''}")

    def apply_changes():
        new_completion = completion_text.get("1.0", tk.END).strip()
        new_generation = generation_text.get("1.0", tk.END).strip()
        debug_console.log("Applying prompt changes.", level='ACTION')
        if on_save_callback: on_save_callback(new_completion, new_generation)
        saved_state["completion"] = new_completion; saved_state["generation"] = new_generation
        update_default_status_labels()
        return "break"

    def create_buttons(parent, text_widget, prompt_key):
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", side="bottom", padx=5, pady=(10, 0))
        def restore_default():
            if messagebox.askyesno("Confirm Restore", f"Are you sure you want to restore the default for the {prompt_key.upper()} prompt?", parent=prompts_window):
                debug_console.log(f"Restoring default for {prompt_key} prompt.", level='ACTION')
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", default_prompts.get(prompt_key, ""))
                update_default_status_labels()
        ttk.Button(button_frame, text="Appliquer", command=apply_changes).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="Restaurer par défaut", command=restore_default).pack(side="left")

    create_buttons(completion_pane, completion_text, "completion")
    create_buttons(generation_pane, generation_text, "generation")
    main_pane.add(completion_pane, minsize=400, stretch="always")
    main_pane.add(generation_pane, minsize=400, stretch="always")

    def close_window():
        has_changes = (completion_text.get("1.0", tk.END).strip() != saved_state["completion"] or
                       generation_text.get("1.0", tk.END).strip() != saved_state["generation"])
        if has_changes:
            response = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Do you want to save before closing?", parent=prompts_window)
            if response is True: apply_changes(); prompts_window.destroy()
            elif response is False: prompts_window.destroy()
        else:
            prompts_window.destroy()

    bottom_bar = ttk.Frame(prompts_window, padding=(10, 0, 10, 10))
    bottom_bar.pack(fill="x", side="bottom")
    ttk.Button(bottom_bar, text="Fermer", command=close_window).pack(side="right")

    prompts_window.bind("<Control-s>", lambda event: apply_changes())
    prompts_window.protocol("WM_DELETE_WINDOW", close_window)
    prompts_window.wait_window()