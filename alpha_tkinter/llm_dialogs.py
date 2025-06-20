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

def show_generate_text_dialog(root_window, theme_setting_getter_func,
                              current_prompt_history_list, # For display
                              on_generate_request_callback, # Called when user clicks "Generate"
                              on_history_entry_add_callback, # Called to add "Generating..." to history
                              initial_prompt_text=None):
    """
    Displays a dialog for users to input a custom prompt for LLM text generation.

    Args:
        root_window (tk.Tk): The main application window.
        theme_setting_getter_func (function): Function to get current theme settings.
        current_prompt_history_list (list): The current list of prompt-response tuples for display.
        on_generate_request_callback (function): Callback function to be invoked when the
                                                 user confirms the prompt.
                                                 Expected signature: func(user_prompt, lines_before, lines_after)
        on_history_entry_add_callback (function): Callback to add the new prompt (with a
                                                  placeholder response) to the main history list.
                                                  Expected signature: func(user_prompt)
        initial_prompt_text (str, optional): Text to pre-fill in the prompt input.
    """
    prompt_window = tk.Toplevel(root_window)
    prompt_window.title("Custom AI Generation")
    prompt_window.transient(root_window)
    prompt_window.grab_set()
    prompt_window.geometry("800x600")

    # --- Theming (simplified for brevity) ---
    dialog_bg = theme_setting_getter_func("root_bg", "#f0f0f0")
    dialog_fg = theme_setting_getter_func("fg_color", "#000000")
    dialog_input_bg = theme_setting_getter_func("input_bg", "#ffffff")
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
    history_listbox = tk.Listbox(history_listbox_frame, exportselection=False, font=("Consolas", 9))
    # ... (configure listbox colors, scrollbar)
    history_listbox.pack(side="left", fill="both", expand=True)
    # Populate history_listbox from current_prompt_history_list
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
    input_controls_frame.grid_rowconfigure(6, weight=0) # Response text (initially hidden)
    input_controls_frame.grid_columnconfigure(0, weight=1)

    ttk.Label(input_controls_frame, text="Your Prompt:").grid(row=0, column=0, columnspan=2, sticky="nw", padx=5, pady=(0,5))
    text_prompt = tk.Text(input_controls_frame, height=10, width=50, wrap="word", font=("Consolas", 10))
    # ... (configure text_prompt colors, scrollbar)
    text_prompt.grid(row=1, column=0, columnspan=2, padx=5, pady=(0,5), sticky="nsew")
    if initial_prompt_text:
        text_prompt.insert("1.0", initial_prompt_text)

    # --- LLM Response Display Area (shown on history selection) ---
    llm_response_label = ttk.Label(input_controls_frame, text="LLM Response:")
    text_response = tk.Text(input_controls_frame, height=10, width=50, wrap="word", state="disabled", font=("Consolas", 10))
    # ... (configure text_response colors, scrollbar)

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

                llm_response_label.grid(row=5, column=0, columnspan=2, sticky="nw", padx=5, pady=(10,5))
                text_response.grid(row=6, column=0, columnspan=2, padx=5, pady=(0,5), sticky="nsew")
                # response_scrollbar.grid(...)
                input_controls_frame.grid_rowconfigure(6, weight=1)

                text_response.config(state="normal")
                text_response.delete("1.0", tk.END)
                text_response.insert("1.0", selected_llm_response)
                text_response.config(state="disabled")
            else: # "No history yet." or invalid
                llm_response_label.grid_remove()
                text_response.grid_remove()
                # response_scrollbar.grid_remove()
                input_controls_frame.grid_rowconfigure(6, weight=0)
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

        # 1. Call back to add "Generating..." to history immediately
        if on_history_entry_add_callback:
            on_history_entry_add_callback(user_prompt)

        # 2. Call back to trigger the actual LLM generation process
        if on_generate_request_callback:
            on_generate_request_callback(user_prompt, num_back, num_forward)

        prompt_window.destroy()

    button_frame = ttk.Frame(input_controls_frame)
    button_frame.grid(row=4, column=0, columnspan=3, pady=(10,0), sticky="ew")
    ttk.Button(button_frame, text="Generate", command=handle_send_prompt_action).pack()

    main_pane.add(input_controls_frame, stretch="always")
    prompt_window.grid_rowconfigure(0, weight=1)
    prompt_window.grid_columnconfigure(0, weight=1)

    text_prompt.focus()
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
    text_bg = theme_setting_getter_func("editor_bg", "#ffffff")
    text_fg = theme_setting_getter_func("editor_fg", "#000000")
    # ...

    ttk.Label(keyword_window, text="Enter keywords (one per line or comma-separated):").pack(pady=(10,5))

    keyword_text_widget = tk.Text(keyword_window, height=10, width=45, font=("Consolas", 11))
    keyword_text_widget.configure(bg=text_bg, fg=text_fg, relief=tk.FLAT, borderwidth=0)
    # ... (configure insertbackground, selectbackground, etc.)
    keyword_text_widget.pack(pady=5, padx=10, fill="both", expand=True)

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

        keyword_window.destroy()

    ttk.Button(keyword_window, text="Save Keywords", command=save_keywords_action_internal).pack(pady=10)
    keyword_text_widget.focus()
    keyword_window.wait_window()