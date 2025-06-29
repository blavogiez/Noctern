import llm_state
import tkinter as tk
import datetime
import interface
import llm_utils # Needed for completion post-processing

# This global variable will hold the single, currently active session.
_current_session = None

class InteractiveSession:
    """A robust class to manage the state and UI of a single LLM interaction."""

    def __init__(self, editor, start_index, is_completion=False, completion_phrase=""):
        self.editor = editor
        self.is_completion = is_completion
        self.completion_phrase = completion_phrase
        self.full_response_text = ""
        
        # --- Define the precise locations for UI and text ---
        self.block_start_index = editor.index(start_index)
        self.buttons_end_index = None
        self.text_end_index = None
        
        self.buttons_frame = self._create_ui_elements()
        self.editor.window_create(self.block_start_index, window=self.buttons_frame, padx=5, align="center")
        
        self.buttons_end_index = self.editor.index(f"{self.block_start_index} + 1 char")
        self.text_end_index = self.buttons_end_index

    def _create_ui_elements(self):
        """Creates the button frame. Called only by the constructor."""
        btn_style = {"relief": tk.FLAT, "bd": 0, "fg": "#FFFFFF", "font": ("Segoe UI", 9),
                     "cursor": "hand2", "padx": 10, "pady": 3, "activeforeground": "#FFFFFF"}
        frame = tk.Frame(self.editor, bg="#404040", bd=1, relief=tk.SOLID,
                         highlightbackground="#606060", highlightcolor="#007bff", highlightthickness=1)
        tk.Button(frame, text="Accept", command=self.accept, bg="#28a745", activebackground="#218838", **btn_style).pack(side=tk.LEFT, padx=(2, 1))
        tk.Button(frame, text="Rephrase", command=self.rephrase, bg="#17a2b8", activebackground="#138496", **btn_style).pack(side=tk.LEFT, padx=1)
        tk.Button(frame, text="Discard", command=self.discard, bg="#dc3545", activebackground="#c82333", **btn_style).pack(side=tk.LEFT, padx=(1, 2))
        return frame

    # --- Callbacks for the streaming threads in other files ---
    def handle_chunk(self, chunk):
        """Inserts a text chunk and updates the session's state."""
        self.editor.insert(self.text_end_index, chunk, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{self.text_end_index} + {len(chunk)} chars")
        self.full_response_text += chunk

    def handle_success(self):
        """Called when the stream finishes successfully."""
        if self.is_completion:
            self._post_process_completion()
        llm_state._is_generating = False
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM stream finished.")

    def handle_error(self, error_msg):
        """Cleans up the UI if the stream fails."""
        messagebox.showerror("LLM Error", error_msg)
        self.destroy(delete_text=True)

    # --- User Actions ---
    def accept(self):
        """Finalizes the text: removes styling and the buttons."""
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Accepted LLM generated text.")
        text_start_index = self.buttons_end_index
        self.editor.tag_remove("llm_generated_text", text_start_index, self.text_end_index)
        self.destroy(delete_text=False) # Keep text, just destroy UI
        self.editor.focus_set()

    def discard(self):
        """Discards the entire interaction: text and buttons."""
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Discarded LLM generated text.")
        self.destroy(delete_text=True) # Destroy UI and delete text
        self.editor.focus_set()

    def rephrase(self):
        """Triggers a rephrase action."""
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: Rephrasing LLM generated text.")
        import llm_completion, llm_generation
        last_action, last_prompt, last_phrase = (
            llm_state._last_llm_action_type,
            llm_state._last_generation_user_prompt,
            llm_state._last_completion_phrase_start,
        )
        self.destroy(delete_text=True) # Clean up current UI first
        if last_action == "completion": llm_completion.request_llm_to_complete_text()
        elif last_action == "generation": llm_generation.open_generate_text_dialog(initial_prompt_text=last_prompt)

    def _post_process_completion(self):
        """Special logic to clean up completion text after streaming is done."""
        cleaned_text = llm_utils.remove_prefix_overlap_from_completion(self.completion_phrase, self.full_response_text)
        text_start = self.buttons_end_index
        # Replace the streamed text with the cleaned version
        self.editor.delete(text_start, self.text_end_index)
        self.editor.insert(text_start, cleaned_text, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{text_start} + {len(cleaned_text)} chars")

    def destroy(self, delete_text):
        """Cleans up the session and its resources."""
        global _current_session
        if delete_text:
            self.editor.delete(self.block_start_index, self.text_end_index)
        else: # Just delete the buttons
            self.editor.delete(self.block_start_index, self.buttons_end_index)
        
        if self.buttons_frame:
            try: self.buttons_frame.destroy()
            except tk.TclError: pass
        
        _current_session = None
        llm_state._is_generating = False

def start_new_interactive_session(editor, is_completion=False, completion_phrase=""):
    """Main entry point. Creates a session and returns its callbacks to the caller."""
    global _current_session
    if _current_session: _current_session.discard()
    
    llm_state._is_generating = True
    _current_session = InteractiveSession(editor, editor.index(tk.INSERT), is_completion, completion_phrase)
    
    # Return a dictionary of safe, bound methods for the thread to call.
    return {
        'on_chunk': _current_session.handle_chunk,
        'on_success': _current_session.handle_success,
        'on_error': _current_session.handle_error,
    }

# --- Public functions called by bindings are simple, safe wrappers ---
def accept_generated_text(event=None):
    if _current_session and not llm_state._is_generating:
        _current_session.accept(); return "break"
def discard_generated_text(event=None):
    if _current_session:
        _current_session.discard(); return "break"
def rephrase_generated_text(event=None):
    if _current_session and not llm_state._is_generating:
        _current_session.rephrase(); return "break"

# --- Bindings are unchanged, as requested ---
def bind_keyboard_shortcuts(editor):
    editor.bind("<Tab>", accept_generated_text)
    editor.bind("<KeyPress-space>", lambda e: accept_generated_text() if _is_word_complete(e) else None)
    editor.bind("<KeyPress-r>", rephrase_generated_text)
    editor.bind("<KeyPress-c>", discard_generated_text)

def _is_word_complete(event):
    return event.char == ' ' and _current_session is not None