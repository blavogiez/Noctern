import tkinter as tk
from tkinter import messagebox
from llm import state as llm_state
from llm import utils as llm_utils
from utils import debug_console
import uuid # Import uuid for unique session IDs

# NOTE: llm_rephrase is imported locally within functions to avoid circular dependencies
# during module loading.

# This global variable will hold the single active interactive session.
_current_session = None

class InteractiveSession:
    """
    Manages an interactive LLM generation session within the editor.
    """

    def __init__(self, editor, start_index, is_completion=False, is_rephrase=False, completion_phrase="", on_discard_callback=None):
        self.session_id = uuid.uuid4()
        debug_console.log(f"Creating new interactive LLM session: {self.session_id}", level='INFO')
        self.editor = editor
        self.is_completion = is_completion
        self.is_rephrase = is_rephrase
        self.completion_phrase = completion_phrase
        self.full_response_text = ""
        self.is_animating = False
        self.animation_dot_count = 0
        self.on_discard_callback = on_discard_callback
        self.is_discarded = False # Flag to poison this instance if discarded

        self.block_start_index = editor.index(start_index)
        self.buttons_frame = self._create_ui_elements()
        self.editor.window_create(self.block_start_index, window=self.buttons_frame, padx=5, align="center")
        
        self.text_start_index = self.editor.index(f"{self.block_start_index} + 1 char")
        self.text_end_index = self.text_start_index
        
        self._start_generating_animation()
        self._bind_keyboard_shortcuts()

    def _create_ui_elements(self):
        frame = tk.Frame(self.editor, bg="#2D2D2D", bd=0)
        btn_style = {"relief": tk.FLAT, "bd": 0, "fg": "#F0F0F0", "font": ("Segoe UI", 9),
                     "cursor": "hand2", "padx": 8, "pady": 2, "activeforeground": "#FFFFFF"}
        
        accept_btn = tk.Button(frame, text="Accept (Tab)", bg="#0078D4", activebackground="#005A9E", **btn_style, command=self.accept)
        rephrase_btn = tk.Button(frame, text="Rephrase (Ctrl+R)", bg="#2D2D2D", activebackground="#404040", **btn_style, command=self.rephrase)
        discard_btn = tk.Button(frame, text="Discard (Esc)", bg="#2D2D2D", activebackground="#404040", **btn_style, command=self.discard)
        
        self.animation_label = tk.Label(frame, text="", bg="#2D2D2D", fg="#aaa", font=("Segoe UI", 9, "italic"), padx=5)

        accept_btn.pack(side=tk.LEFT)
        rephrase_btn.pack(side=tk.LEFT)
        discard_btn.pack(side=tk.LEFT)
        self.animation_label.pack(side=tk.LEFT)
        return frame

    def _bind_keyboard_shortcuts(self):
        self.editor.bind("<Tab>", self._handle_accept_key)
        self.editor.bind("<Escape>", self._handle_discard_key)
        self.editor.bind("<Control-r>", self._handle_rephrase_key)
        self.editor.bind("<Control-R>", self._handle_rephrase_key)

    def _unbind_keyboard_shortcuts(self):
        self.editor.unbind("<Tab>")
        self.editor.unbind("<Escape>")
        self.editor.unbind("<Control-r>")
        self.editor.unbind("<Control-R>")
        
    def _handle_accept_key(self, event=None):
        if not llm_state._is_generating: self.accept()
        return "break"

    def _handle_discard_key(self, event=None):
        self.discard()
        return "break"
        
    def _handle_rephrase_key(self, event=None):
        if not llm_state._is_generating: self.rephrase()
        return "break"

    def _start_generating_animation(self):
        self.is_animating = True
        self._animate_dots()

    def _animate_dots(self):
        if not self.is_animating: return
        dots = '.' * (self.animation_dot_count % 3 + 1)
        self.animation_label.config(text=f" Generating{dots}")
        self.animation_dot_count += 1
        self.editor.after(400, self._animate_dots)

    def _stop_generating_animation(self):
        if self.is_animating:
            self.is_animating = False
            self.animation_label.config(text="")

    def handle_chunk(self, chunk):
        if self.is_discarded: return
        if self.is_animating: self._stop_generating_animation()
        self.editor.insert(self.text_end_index, chunk, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{self.text_end_index} + {len(chunk)} chars")
        self.full_response_text += chunk

    def handle_success(self, final_cleaned_text):
        if self.is_discarded: return
        self._stop_generating_animation()

        self.editor.delete(self.text_start_index, self.text_end_index)
        self.editor.insert(self.text_start_index, final_cleaned_text, "llm_generated_text")
        
        self.text_end_index = self.editor.index(f"{self.text_start_index} + {len(final_cleaned_text)} chars")
        self.full_response_text = final_cleaned_text

        if self.is_completion: self._post_process_completion()

        if self.is_rephrase:
            self.editor.tag_add(tk.SEL, self.text_start_index, self.text_end_index)

        llm_state._is_generating = False
        self.editor.focus_set()

        if not self.is_rephrase and not self.is_completion:
            self.editor.after(50, self.rephrase)

    def handle_error(self, error_msg):
        if self.is_discarded: return
        debug_console.log(f"LLM interactive session error: {error_msg}", level='ERROR')
        messagebox.showerror("LLM Error", error_msg)
        self.destroy(delete_text=True)

    def accept(self):
        if self.is_discarded or llm_state._is_generating: return
        debug_console.log(f"User ACCEPTED LLM suggestion for session {self.session_id}.", level='ACTION')
        self.editor.tag_remove("llm_generated_text", self.text_start_index, self.text_end_index)
        self.destroy(delete_text=False)
        self.editor.focus_set()

    def discard(self):
        if self.is_discarded: return
        debug_console.log(f"User DISCARDED LLM suggestion for session {self.session_id}.", level='ACTION')
        self.is_discarded = True # Poison this instance.

        # This is a global flag to signal cancellation to the running thread.
        llm_state._is_generation_cancelled = True
        debug_console.log("Cancellation flag set for ongoing generation.", level='INFO')

        # Immediately stop and hide the progress bar from the main thread
        if llm_state._llm_progress_bar_widget and llm_state._llm_progress_bar_widget.winfo_exists():
            llm_state._llm_progress_bar_widget.stop()
            llm_state._llm_progress_bar_widget.pack_forget()
        
        self.destroy(delete_text=True)
        
        if self.on_discard_callback:
            self.on_discard_callback()
            
        self.editor.focus_set()

    def rephrase(self):
        if llm_state._is_generating: return
        
        from . import rephrase as llm_rephrase
        from llm.dialogs.rephrase import show_rephrase_dialog
        from app import main_window

        text_to_rephrase = self.full_response_text
        if not text_to_rephrase.strip():
            messagebox.showinfo("Rephrase", "Nothing to rephrase yet.")
            return

        root_window = self.editor.winfo_toplevel()

        # This callback will be executed if the user provides an instruction and clicks "Rephrase"
        def on_rephrase_confirmed(instruction):
            # The `request_rephrase_for_text` function will start a new interactive session.
            # The `start_new_interactive_session` function will automatically discard the current session.
            llm_rephrase.request_rephrase_for_text(
                self.editor,
                text_to_rephrase,
                self.block_start_index, # The start of the area to be replaced by the new session
                self.text_end_index,   # The end of the area to be replaced
                instruction,
                self.on_discard_callback # Preserve the original discard behavior
            )

        # Show the dialog to get the instruction from the user.
        # If the user cancels, do nothing and leave the current interactive session as is.
        show_rephrase_dialog(
            root_window=root_window,
            theme_setting_getter_func=main_window.get_theme_setting,
            original_text=text_to_rephrase,
            on_rephrase_callback=on_rephrase_confirmed,
            on_cancel_callback=lambda: debug_console.log("Rephrase dialog cancelled.", level='INFO')
        )

    def _post_process_completion(self):
        cleaned_text = llm_utils.remove_prefix_overlap_from_completion(self.completion_phrase, self.full_response_text)
        self.editor.delete(self.text_start_index, self.text_end_index)
        self.editor.insert(self.text_start_index, cleaned_text, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{self.text_start_index} + {len(cleaned_text)} chars")

    def destroy(self, delete_text):
        global _current_session
        self._stop_generating_animation()
        self._unbind_keyboard_shortcuts()
        try:
            # If we need to delete the generated text, we delete from the start of the text to the end.
            if delete_text and self.editor.winfo_exists():
                start_text = self.editor.index(self.text_start_index)
                end_text = self.editor.index(self.text_end_index)
                if self.editor.compare(start_text, "<", end_text):
                    self.editor.delete(start_text, end_text)

            # Always delete the UI frame (which is 1 character wide in the text widget)
            if self.editor.winfo_exists():
                self.editor.delete(self.block_start_index)
            
            if self.buttons_frame and self.buttons_frame.winfo_exists():
                self.buttons_frame.destroy()
        except tk.TclError as e:
            debug_console.log(f"Error destroying interactive session UI: {e}", level='ERROR')
        
        _current_session = None
        llm_state._is_generating = False

def start_new_interactive_session(editor, is_completion=False, is_rephrase=False, completion_phrase="", on_discard_callback=None):
    global _current_session
    if _current_session:
        _current_session.discard()
    
    llm_state._is_generating = True
    llm_state._is_generation_cancelled = False
    start_index = editor.index(tk.INSERT)
    
    # Add a separator to group the entire generation as a single undo action.
    editor.edit_separator()
    
    _current_session = InteractiveSession(
        editor, start_index, 
        is_completion=is_completion, 
        is_rephrase=is_rephrase,
        completion_phrase=completion_phrase, 
        on_discard_callback=on_discard_callback
    )
    
    return {
        'on_chunk': _current_session.handle_chunk,
        'on_success': _current_session.handle_success,
        'on_error': _current_session.handle_error
    }