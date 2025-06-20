import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
import threading

# Access global variables defined in main.py or interface.py
editor = None
root = None
llm_progress_bar = None
llm_keywords = [] # To store user-defined LLM keywords

def set_llm_globals(editor_widget, root_widget, progress_bar_widget):
    """Sets the global references to the main widgets."""
    global editor, root, llm_progress_bar
    editor = editor_widget
    root = root_widget
    llm_progress_bar = progress_bar_widget

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

def generate_text_from_prompt():
    """Opens a dialog to get a custom prompt for LLM text generation."""
    if not editor or not root or not llm_progress_bar:
        return

    # Use simpledialog or create a custom Toplevel window
    # A custom Toplevel window is better for multiple inputs (prompt, lines before/after)

    prompt_window = tk.Toplevel(root)
    prompt_window.title("Custom AI Generation")
    prompt_window.transient(root) # Keep window on top of root
    prompt_window.grab_set() # Modal window

    tk.Label(prompt_window, text="Prompt:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    entry_prompt = tk.Entry(prompt_window, width=60)
    entry_prompt.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(prompt_window, text="Lines before cursor:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    entry_back = tk.Entry(prompt_window, width=10)
    entry_back.insert(0, "5") # Default 5 lines before
    entry_back.grid(row=1, column=1, sticky="w", padx=5, pady=5)

    tk.Label(prompt_window, text="Lines after cursor:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    entry_forward = tk.Entry(prompt_window, width=10)
    entry_forward.insert(0, "0") # Default 0 lines after
    entry_forward.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    def send_prompt():
        user_prompt = entry_prompt.get().strip()
        try:
            num_back = int(entry_back.get())
            num_forward = int(entry_forward.get())
        except ValueError:
            messagebox.showerror("Input Error", "Line counts must be integers.", parent=prompt_window)
            return

        if not user_prompt:
            messagebox.showwarning("Warning", "The prompt is empty.", parent=prompt_window)
            return

        # Close the prompt window immediately
        prompt_window.destroy()

        def run_generation():
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
                else:
                    # Show error message on the main thread
                    editor.after(0, lambda: messagebox.showerror("LLM Error", f"Status: {response.status_code}\nResponse: {response.text[:200]}..."))

            except requests.exceptions.ConnectionError:
                 editor.after(0, lambda: messagebox.showerror("Connection Error", "Could not connect to LLM API. Is the backend running?"))
            except Exception as e:
                # Show any other errors on the main thread
                editor.after(0, lambda: messagebox.showerror("LLM Generation Error", str(e)))
            finally:
                # Hide progress bar on the main thread
                editor.after(0, lambda: llm_progress_bar.pack_forget())
                llm_progress_bar.stop()

        # Show progress bar and start animation on the main thread
        llm_progress_bar.pack(pady=2)
        llm_progress_bar.start(10) # Start indeterminate animation

        # Run the LLM request in a separate thread
        threading.Thread(target=run_generation, daemon=True).start()

    tk.Button(prompt_window, text="Generate", command=send_prompt).grid(row=3, column=0, columnspan=2, pady=10, padx=5)
    entry_prompt.focus() # Set focus to the prompt entry field
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

    tk.Label(keyword_window, text="Enter keywords (one per line or comma-separated):").pack(pady=(10,5))

    keyword_text_widget = tk.Text(keyword_window, height=10, width=45)
    keyword_text_widget.pack(pady=5, padx=10, fill="both", expand=True)

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

    tk.Button(keyword_window, text="Save Keywords", command=save_keywords_action).pack(pady=10)
    keyword_text_widget.focus()
    keyword_window.wait_window()