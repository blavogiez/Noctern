import tkinter as tk
from tkinter import messagebox, simpledialog, ttk # Added ttk
import requests
import threading

# Access global variables defined in main.py or interface.py
editor = None
root = None
llm_progress_bar = None
llm_keywords = [] # To store user-defined LLM keywords
get_theme_setting_func = None # To get theme colors for dialogs
prompt_history = [] # To store user prompt history for generation
MAX_PROMPT_HISTORY = 20 # Maximum number of prompts to store in history

def update_prompt_history_response(user_prompt_key, new_response_text):
    """Updates the response for a given user_prompt_key in the global prompt_history."""
    global prompt_history
    for i, (p_user, p_resp) in enumerate(prompt_history):
        # Match the specific prompt that was being processed
        if p_user == user_prompt_key and p_resp == "⏳ Generating...":
            prompt_history[i] = (p_user, new_response_text)
            break

def set_llm_globals(editor_widget, root_widget, progress_bar_widget, get_theme_setting_callback):
    """Sets the global references to the main widgets."""
    global editor, root, llm_progress_bar, get_theme_setting_func
    editor = editor_widget
    root = root_widget
    llm_progress_bar = progress_bar_widget
    get_theme_setting_func = get_theme_setting_callback

def get_context(nb_lines_backwards=5, nb_lines_forwards=5):
    """Extracts text context around the cursor."""
    if not editor:
        return ""

    try:
        cursor_index = editor.index(tk.INSERT)
        line_index = int(cursor_index.split(".")[0])
        # Get total lines, handling empty editor case
        last_line_index_str = editor.index("end-1c")
        total_lines = int(last_line_index_str.split(".")[0]) if last_line_index_str != "1.0" or editor.get("1.0", "1.end") else 0

        start_line = max(1, line_index - nb_lines_backwards)
        end_line = min(total_lines, line_index + nb_lines_forwards)

        context_lines = []
        # Iterate from start_line to end_line (inclusive)
        for i in range(start_line, end_line + 1):
            line_text = editor.get(f"{i}.0", f"{i}.end")
            context_lines.append(line_text)

        return "\n".join(context_lines)
    except Exception as e:
        print(f"Error getting context: {e}")
        return ""

def remove_overlap(start_text: str, completion_text: str) -> str:
    """Removes redundant overlap between the start text and the completion."""
    start_words = start_text.split()
    completion_words = completion_text.split()

    # Find the longest suffix of start_words that is a prefix of completion_words
    overlap_length = 0
    for i in range(1, min(len(start_words), len(completion_words)) + 1):
        if start_words[-i:] == completion_words[:i]:
            overlap_length = i

    # Return the part of completion_words after the overlap
    return " ".join(completion_words[overlap_length:]).strip()

def complete_with_llm():
    """Requests sentence completion from the LLM based on preceding text."""
    if not editor or not root or not llm_progress_bar:
        return

    def run_completion():
        try:
            # Get context: 30 lines backwards, 0 forwards
            context = get_context(nb_lines_backwards=30, nb_lines_forwards=0)

            # Find the last sentence ending to isolate the current sentence fragment
            last_dot_index = max(context.rfind("."), context.rfind("!"), context.rfind("?"))

            if last_dot_index == -1:
                # No sentence end found in the context, use the whole context as the current phrase
                current_phrase_start = context.strip()
                previous_context = ""
            else:
                # Split context into previous context and current phrase start
                current_phrase_start = context[last_dot_index + 1:].strip()
                previous_context = context[:last_dot_index + 1].strip()

            # Construct the prompt for the LLM
            prompt = f"""
                "Complete only the current sentence fragment, without rephrasing the context or including tags/code. "
                "Maintain the same language. The beginning of the completion must strictly follow the beginning of the current phrase. "
                "Respond only with natural, fluid, and coherent text. "
                "Do not start a new idea or paragraph; stay in the logical continuation of the text.\n\n"
                f"Context (up to 30 preceding lines):\n\"{previous_context}\"\n\n"
                f"Beginning of the phrase to complete:\n\"{current_phrase_start}\"\n\n"
                "Expected completion (short and natural, no final punctuation if it's already started):"

                Keywords:
                "{', '.join(llm_keywords)}"
            """

            # Send request to the LLM API
            response = requests.post("http://localhost:11434/api/generate", json={
                "model": "mistral", # Or another configured model
                "prompt": prompt,
                "stream": False
            })

            # Process the response
            if response.status_code == 200:
                completion_raw = response.json().get("response", "").strip().strip('"')
                # Remove potential overlap if the LLM repeats the start of the phrase
                cleaned_completion = remove_overlap(current_phrase_start, completion_raw)
                # Insert the completion into the editor on the main thread
                editor.after(0, lambda: editor.insert(tk.INSERT, cleaned_completion))
            else:
                # Show error message on the main thread
                editor.after(0, lambda: messagebox.showerror("LLM Error", f"Status: {response.status_code}\nResponse: {response.text[:200]}..."))

        except requests.exceptions.ConnectionError:
             editor.after(0, lambda: messagebox.showerror("Connection Error", "Could not connect to LLM API. Is the backend running?"))
        except Exception as e:
            # Show any other errors on the main thread
            editor.after(0, lambda: messagebox.showerror("LLM Completion Error", str(e)))
        finally:
            # Hide progress bar on the main thread
            editor.after(0, lambda: llm_progress_bar.pack_forget())
            editor.after(0, lambda: llm_progress_bar.stop())

    # Show progress bar and start animation on the main thread
    llm_progress_bar.pack(pady=2)
    llm_progress_bar.start(10) # Start indeterminate animation

    # Run the LLM request in a separate thread to keep the GUI responsive
    threading.Thread(target=run_completion, daemon=True).start()

def generate_text_from_prompt(initial_prompt_text=None):
    """Opens a dialog to get a custom prompt for LLM text generation."""
    if not editor or not root or not llm_progress_bar:
        return
    # Use simpledialog or create a custom Toplevel window
    # A custom Toplevel window is better for multiple inputs and history display

    prompt_window = tk.Toplevel(root)
    prompt_window.title("Custom AI Generation")
    prompt_window.transient(root) # Keep window on top of root
    prompt_window.grab_set() # Modal window
    prompt_window.geometry("800x600") # Increased size for history

    # Theme settings
    dialog_bg = "#f0f0f0"
    dialog_fg = "#000000"
    dialog_input_bg = "#ffffff"
    dialog_input_fg = "#000000"
    if get_theme_setting_func:
        prompt_window.configure(bg=get_theme_setting_func("root_bg", "#f0f0f0"))
        dialog_fg = get_theme_setting_func("fg_color", "#000000")
        dialog_input_bg = get_theme_setting_func("input_bg", "#ffffff")
        dialog_input_fg = get_theme_setting_func("input_fg", "#000000")
    else: # Fallback defaults
        dialog_fg = "#000000"
        dialog_bg = "#f0f0f0" # Ensure dialog_bg is set in fallback
        dialog_input_bg = "#ffffff"
        dialog_input_fg = "#000000"

    prompt_window.configure(bg=dialog_bg)

    # Main paned window for history and input areas
    main_pane = tk.PanedWindow(prompt_window, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
    if get_theme_setting_func:
        main_pane.configure(bg=get_theme_setting_func("panedwindow_sash", "#d0d0d0"))
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)

    # --- Left Pane: History Listbox ---
    history_frame = ttk.Frame(main_pane, padding=(0,0,5,0)) # Add some padding to the right of history
    ttk.Label(history_frame, text="Prompt History:").pack(pady=(0, 5), anchor="w")

    history_listbox_frame = ttk.Frame(history_frame)
    history_listbox_frame.pack(fill="both", expand=True)

    history_listbox_bg = get_theme_setting_func("editor_bg", dialog_input_bg)
    history_listbox_fg = get_theme_setting_func("editor_fg", dialog_input_fg)
    history_listbox_select_bg = get_theme_setting_func("sel_bg", "#cce5ff")
    history_listbox_select_fg = get_theme_setting_func("sel_fg", "#000000")

    history_listbox = tk.Listbox(history_listbox_frame,
                                 bg=history_listbox_bg, fg=history_listbox_fg,
                                 selectbackground=history_listbox_select_bg, selectforeground=history_listbox_select_fg,
                                 highlightthickness=0, borderwidth=1, relief=tk.SOLID,
                                 activestyle='dotbox', font=("Consolas", 9), exportselection=False)
    history_listbox.pack(side="left", fill="both", expand=True)

    history_scrollbar = ttk.Scrollbar(history_listbox_frame, orient="vertical", command=history_listbox.yview)
    history_scrollbar.pack(side="right", fill="y")
    history_listbox.config(yscrollcommand=history_scrollbar.set)

    for item in prompt_history:
        user_p, _ = item # We only display the user prompt in the listbox
        display_user = user_p[:100] + '...' if len(user_p) > 100 else user_p # Truncate prompt for listbox
        listbox_item_text = f"Q: {display_user}"
        history_listbox.insert(tk.END, listbox_item_text)

    if not prompt_history:
        history_listbox.insert(tk.END, "No history yet.")
        history_listbox.config(state=tk.DISABLED)
    else:
        history_listbox.config(state=tk.NORMAL)

    main_pane.add(history_frame, width=250, minsize=150) # Add history frame to pane
    # --- Right Pane: Prompt Input and Controls ---
    input_controls_frame = ttk.Frame(main_pane, padding=(5,0,0,0)) # Add some padding to the left of input

    # Configure resizing for the input_controls_frame
    input_controls_frame.grid_rowconfigure(1, weight=1) # Row for the text_prompt
    input_controls_frame.grid_rowconfigure(6, weight=0) # Row for the response text, initially no weight
    input_controls_frame.grid_columnconfigure(0, weight=1) # Column for the text widgets
    
    ttk.Label(input_controls_frame, text="Your Prompt:").grid(row=0, column=0, columnspan=2, sticky="nw", padx=5, pady=(0,5))
    
    text_prompt = tk.Text(input_controls_frame, height=10, width=50, wrap="word") # Initial width
    text_prompt.grid(row=1, column=0, columnspan=2, padx=5, pady=(0,5), sticky="nsew")
    
    text_prompt.configure(
        relief=tk.FLAT, borderwidth=0, font=("Consolas", 10),
        bg=dialog_input_bg, fg=dialog_input_fg,
        insertbackground=get_theme_setting_func("editor_insert_bg", dialog_fg),
        selectbackground=get_theme_setting_func("sel_bg", "#cce5ff"), 
        selectforeground=get_theme_setting_func("sel_fg", "#000000")
    )
    prompt_scrollbar = ttk.Scrollbar(input_controls_frame, orient="vertical", command=text_prompt.yview)
    prompt_scrollbar.grid(row=1, column=2, sticky="ns", pady=(0,5))
    text_prompt.config(yscrollcommand=prompt_scrollbar.set)

    if initial_prompt_text:
        text_prompt.insert("1.0", initial_prompt_text)

    # --- LLM Response Display Area ---
    llm_response_label = ttk.Label(input_controls_frame, text="LLM Response:")
    # llm_response_label.grid(row=5, column=0, columnspan=2, sticky="nw", padx=5, pady=(10,5)) # Gridded on selection

    text_response = tk.Text(input_controls_frame, height=10, width=50, wrap="word", state="disabled") # Read-only

    text_response.configure(
        relief=tk.FLAT, borderwidth=0, font=("Consolas", 10),
        bg=dialog_input_bg, fg=dialog_input_fg, # Use input colors
        insertbackground=get_theme_setting_func("editor_insert_bg", dialog_fg), # Cursor color (though disabled)
        selectbackground=get_theme_setting_func("sel_bg", "#cce5ff"),
        selectforeground=get_theme_setting_func("sel_fg", "#000000")
    )
    response_scrollbar = ttk.Scrollbar(input_controls_frame, orient="vertical", command=text_response.yview)
    text_response.config(yscrollcommand=response_scrollbar.set)
    # text_response and response_scrollbar are gridded on history selection


    # --- Define run_generation function (moved outside send_prompt) ---
    def run_generation(user_prompt, num_back, num_forward):
        try:
            # Get context based on user input
            context = get_context(num_back, num_forward)

            # Construct the prompt for the LLM
            prompt = f"""You are an intelligent writing assistant. A user has given you an instruction to generate text to insert into a document. The user has also provided keywords to guide the generation.

                Main constraint: Respond only with the requested generation, without preamble, signature, explanation, or rephrasing the instruction.

                Language: Strictly in French, formal but natural register. The tone must remain consistent with the provided context.

                User prompt:
                "{user_prompt}"

                Keywords:
                "{', '.join(llm_keywords)}"

                Context around the cursor:
                \"\"\"{context}\"\"\"

                Instructions:
                - Do not modify the context.
                - Generate only the text corresponding to the instruction.
                - Respect the logical and thematic continuity of the text.
                - Your response should integrate smoothly into the existing content.
                - Write your answer following the keywords mentionned.
                
                Text to insert:
                """

            # Send request to the LLM API
            response = requests.post("http://localhost:11434/api/generate", json={
                "model": "mistral", # Or another configured model
                "prompt": prompt,
                "stream": False
            })

            # Process the response
            if response.status_code == 200:
                result = response.json().get("response", "").strip()
                # Insert the generated text into the editor on the main thread
                editor.after(0, lambda: editor.insert(tk.INSERT, result))
                update_prompt_history_response(user_prompt, result)
            else:
                # Show error message on the main thread
                error_msg = f"Status: {response.status_code}\nResponse: {response.text[:200]}..."
                editor.after(0, lambda: messagebox.showerror("LLM Error", error_msg))
                update_prompt_history_response(user_prompt, f"❌ Error: {response.status_code}")

        except requests.exceptions.ConnectionError:
            error_msg = "Could not connect to LLM API. Is the backend running?"
            editor.after(0, lambda: messagebox.showerror("Connection Error", error_msg))
            update_prompt_history_response(user_prompt, "❌ Connection Error")
        except Exception as e:
            # Show any other errors on the main thread
            error_msg = str(e)
            editor.after(0, lambda: messagebox.showerror("LLM Generation Error", error_msg))
            update_prompt_history_response(user_prompt, f"❌ Exception: {error_msg[:50]}...")
        finally:
            # Hide progress bar on the main thread
            editor.after(0, lambda: llm_progress_bar.pack_forget())
            editor.after(0, lambda: llm_progress_bar.stop()) # Ensure stop is also on main thread

    def on_history_select(event):
        widget = event.widget
        selection = widget.curselection()
        if selection:
            index = selection[0]
            # Ensure the selected index is valid for prompt_history
            if 0 <= index < len(prompt_history):
                selected_user_prompt, selected_llm_response = prompt_history[index] # Get the original user prompt and response
                text_prompt.delete("1.0", tk.END)
                text_prompt.insert("1.0", selected_user_prompt)

                # Show and populate the response area
                llm_response_label.grid(row=5, column=0, columnspan=2, sticky="nw", padx=5, pady=(10,5))
                text_response.grid(row=6, column=0, columnspan=2, padx=5, pady=(0,5), sticky="nsew")
                response_scrollbar.grid(row=6, column=2, sticky="ns", pady=(0,5))
                input_controls_frame.grid_rowconfigure(6, weight=1) # Allow response area to expand

                # Display the response in the response text widget
                text_response.config(state="normal") # Enable temporarily to insert
                text_response.delete("1.0", tk.END)
                text_response.insert("1.0", selected_llm_response)
                text_response.config(state="disabled") # Disable again
            else: # "No history yet." or invalid selection
                # Hide the response area
                llm_response_label.grid_remove()
                text_response.grid_remove()
                response_scrollbar.grid_remove()
                input_controls_frame.grid_rowconfigure(6, weight=0) # Prevent empty row from expanding
                text_response.config(state="normal")
                text_response.delete("1.0", tk.END)
                text_response.config(state="disabled")
        else: # No selection in listbox
            llm_response_label.grid_remove()
            text_response.grid_remove()
            response_scrollbar.grid_remove()
            input_controls_frame.grid_rowconfigure(6, weight=0)
            text_response.config(state="normal")
            text_response.delete("1.0", tk.END)
            text_response.config(state="disabled")
    history_listbox.bind("<<ListboxSelect>>", on_history_select)
    ttk.Label(input_controls_frame, text="Lines before cursor:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    entry_back = ttk.Entry(input_controls_frame, width=10)
    entry_back.insert(0, "5")
    entry_back.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(input_controls_frame, text="Lines after cursor:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    entry_forward = ttk.Entry(input_controls_frame, width=10)
    entry_forward.insert(0, "0")
    entry_forward.grid(row=3, column=1, sticky="w", padx=5, pady=5)

    button_frame = ttk.Frame(input_controls_frame) # Frame for the generate button - Adjusted row
    button_frame.grid(row=4, column=0, columnspan=3, pady=(10,0), sticky="ew") # Span 3 for scrollbar
    ttk.Button(button_frame, text="Generate", command=lambda: send_prompt()).pack() # send_prompt needs to be defined or passed

    main_pane.add(input_controls_frame, stretch="always") # Add input frame to pane

    # Configure resizing for the Toplevel window itself
    prompt_window.grid_rowconfigure(0, weight=1)
    prompt_window.grid_columnconfigure(0, weight=1)

    def send_prompt():
        user_prompt = text_prompt.get("1.0", tk.END).strip() # Get text from the Text widget
        try:
            num_back = int(entry_back.get())
            num_forward = int(entry_forward.get())
        except ValueError:
            messagebox.showerror("Input Error", "Line counts must be integers.", parent=prompt_window)
            return

        if not user_prompt:
            messagebox.showwarning("Warning", "The prompt is empty.", parent=prompt_window)
            return

        # Add to history (most recent at the top)
        # Do this BEFORE closing the window
        # The history listbox update within this function is removed as the window is destroyed
        # The global prompt_history list is correctly updated here.
        if user_prompt: # Only add non-empty prompts
            global prompt_history
            # Remove any existing entry for this user_prompt to move it to the top
            # or to update its status if it was already there.
            new_history = []
            for p_hist_user, p_hist_resp in prompt_history:
                if p_hist_user != user_prompt:
                    new_history.append((p_hist_user, p_hist_resp))
            prompt_history = new_history

            # Add the new/updated prompt at the beginning with "Generating..." status
            prompt_history.insert(0, (user_prompt, "⏳ Generating..."))

            if len(prompt_history) > MAX_PROMPT_HISTORY:
                prompt_history = prompt_history[:MAX_PROMPT_HISTORY] # Keep the newest items
        # Close the prompt window immediately AFTER updating history
        prompt_window.destroy()

        # Show progress bar and start animation on the main thread
        llm_progress_bar.pack(pady=2)
        llm_progress_bar.start(10) # Start indeterminate animation

        # Run the LLM request in a separate thread
        threading.Thread(target=run_generation, args=(user_prompt, num_back, num_forward), daemon=True).start()
    text_prompt.focus() # Set focus to the prompt text field
    prompt_window.wait_window() # Wait until the prompt window is closed

def set_llm_keywords_dialog():
    """Opens a dialog for the user to set or update LLM keywords."""
    global llm_keywords
    if not root:
        messagebox.showerror("Error", "Root window not available. Cannot open keywords dialog.")
        return

    keyword_window = tk.Toplevel(root)
    keyword_window.title("Set LLM Keywords")
    keyword_window.transient(root) # Keep window on top of root
    keyword_window.grab_set()     # Modal window
    keyword_window.geometry("400x300") # Initial size
    if get_theme_setting_func:
        keyword_window.configure(bg=get_theme_setting_func("root_bg", "#f0f0f0"))
        text_bg = get_theme_setting_func("editor_bg", "#ffffff")
        text_fg = get_theme_setting_func("editor_fg", "#000000")
        text_insert_bg = get_theme_setting_func("editor_insert_bg", "#000000")
        text_sel_bg = get_theme_setting_func("sel_bg", "#cce5ff")
        text_sel_fg = get_theme_setting_func("sel_fg", "#000000")
    else: # Fallback defaults
        text_bg = "#ffffff"
        text_fg = "#000000"
        text_insert_bg = "#000000"
        text_sel_bg = "#cce5ff"
        text_sel_fg = "#000000"


    ttk.Label(keyword_window, text="Enter keywords (one per line or comma-separated):").pack(pady=(10,5))

    keyword_text_widget = tk.Text(keyword_window, height=10, width=45)
    keyword_text_widget.pack(pady=5, padx=10, fill="both", expand=True)
    keyword_text_widget.configure(
        relief=tk.FLAT, borderwidth=0, font=("Consolas", 11), # Consistent font
        bg=text_bg, fg=text_fg, insertbackground=text_insert_bg,
        selectbackground=text_sel_bg, selectforeground=text_sel_fg
    )
    
    # Pre-fill with existing keywords
    if llm_keywords:
        keyword_text_widget.insert(tk.END, "\n".join(llm_keywords))

    def save_keywords_action():
        global llm_keywords
        input_text = keyword_text_widget.get("1.0", tk.END).strip()
        
        if not input_text:
            llm_keywords = []
            messagebox.showinfo("Keywords Cleared", "LLM keywords list has been cleared.", parent=keyword_window)
        else:
            # Split by newline, then by comma, and filter out empty strings
            raw_keywords = []
            for line in input_text.split('\n'):
                raw_keywords.extend(kw.strip() for kw in line.split(','))
            
            llm_keywords = [kw for kw in raw_keywords if kw] # Filter out empty/whitespace-only strings

            if llm_keywords:
                messagebox.showinfo("Keywords Saved", f"LLM keywords registered:\n- {', '.join(llm_keywords)}", parent=keyword_window)
            else:
                messagebox.showinfo("Keywords Cleared", "No valid keywords entered. LLM keywords list is empty.", parent=keyword_window)
        keyword_window.destroy()

    ttk.Button(keyword_window, text="Save Keywords", command=save_keywords_action).pack(pady=10)
    keyword_text_widget.focus()
    keyword_window.wait_window()