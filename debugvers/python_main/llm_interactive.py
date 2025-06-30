import llm_state
import tkinter as tk
from tkinter import messagebox
import interface
import llm_utils
import debug_console
# NOTE: Pas d'import global de llm_rephrase ici pour éviter une dépendance circulaire
# au chargement du module. L'import sera fait localement dans la fonction.

# Cette variable globale contiendra la seule session active.
_current_session = None

class InteractiveSession:
    """Une classe robuste pour gérer l'état et l'UI d'une interaction LLM."""

    def __init__(self, editor, start_index, is_completion=False, completion_phrase=""):
        debug_console.log(f"Creating new interactive session. Completion: {is_completion}", level='INFO')
        self.editor = editor
        self.is_completion = is_completion
        self.completion_phrase = completion_phrase
        self.full_response_text = ""
        self.is_animating = False
        self.animation_dot_count = 0

        self.block_start_index = editor.index(start_index)
        self.buttons_frame = self._create_ui_elements()
        self.editor.window_create(self.block_start_index, window=self.buttons_frame, padx=5, align="center")
        
        self.buttons_end_index = self.editor.index(f"{self.block_start_index} + 1 char")
        self.text_end_index = self.buttons_end_index
        
        self._start_generating_animation()
        self._bind_keyboard_shortcuts()


    def _create_ui_elements(self):
        """Crée la frame des boutons avec un style compact et fonctionnel."""
        frame = tk.Frame(self.editor, bg="#2D2D2D", bd=0)
        btn_style = {"relief": tk.FLAT, "bd": 0, "fg": "#F0F0F0", "font": ("Segoe UI", 9),
                     "cursor": "hand2", "padx": 8, "pady": 2, "activeforeground": "#FFFFFF"}
        
        accept_btn = tk.Button(frame, text="Accept (Tab)", bg="#0078D4", activebackground="#005A9E", **btn_style, command=self.accept)
        rephrase_btn = tk.Button(frame, text="Rephrase (Ctrl+R)", bg="#2D2D2D", activebackground="#404040", **btn_style, command=self.rephrase)
        discard_btn = tk.Button(frame, text="Discard (Esc)", bg="#2D2D2D", activebackground="#404040", **btn_style, command=self.discard)
        
        accept_btn.pack(side=tk.LEFT); rephrase_btn.pack(side=tk.LEFT); discard_btn.pack(side=tk.LEFT)
        return frame

    def _bind_keyboard_shortcuts(self):
        debug_console.log("Binding session-specific keyboard shortcuts (Tab, Esc, Ctrl+R).", level='DEBUG')
        self.editor.bind("<Tab>", self._handle_accept_key)
        self.editor.bind("<Escape>", self._handle_discard_key)
        self.editor.bind("<Control-r>", self._handle_rephrase_key)
        self.editor.bind("<Control-R>", self._handle_rephrase_key)

    def _unbind_keyboard_shortcuts(self):
        debug_console.log("Unbinding session-specific keyboard shortcuts.", level='DEBUG')
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
        self.editor.tag_config('llm_placeholder', foreground="#aaa", font=("Segoe UI", 9, "italic"))
        self._animate_dots()

    def _animate_dots(self):
        if not self.is_animating: return
        dots = '.' * (self.animation_dot_count % 3 + 1)
        text = f" Generating{dots}"
        self.editor.delete(self.buttons_end_index, self.text_end_index)
        self.editor.insert(self.buttons_end_index, text, "llm_placeholder")
        self.text_end_index = self.editor.index(f"{self.buttons_end_index} + {len(text)} chars")
        self.animation_dot_count += 1
        self.editor.after(400, self._animate_dots)

    def _stop_generating_animation(self):
        if self.is_animating:
            self.is_animating = False
            self.editor.delete(self.buttons_end_index, self.text_end_index)
            self.text_end_index = self.buttons_end_index

    def handle_chunk(self, chunk):
        if self.is_animating: self._stop_generating_animation()
        self.editor.insert(self.text_end_index, chunk, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{self.text_end_index} + {len(chunk)} chars")
        self.full_response_text += chunk

    def handle_success(self):
        self._stop_generating_animation()
        if self.is_completion: self._post_process_completion()
        llm_state._is_generating = False
        self.editor.focus_set()
        debug_console.log("LLM stream finished and handled by session.", level='INFO')

    def handle_error(self, error_msg):
        debug_console.log(f"LLM session error: {error_msg}", level='ERROR')
        messagebox.showerror("LLM Error", error_msg)
        self.destroy(delete_text=True)

    def accept(self):
        if llm_state._is_generating: return
        debug_console.log("User ACCEPTED suggestion.", level='ACTION')
        self.editor.tag_remove("llm_generated_text", self.buttons_end_index, self.text_end_index)
        self.destroy(delete_text=False)
        self.editor.focus_set()

    def discard(self):
        debug_console.log("User DISCARDED suggestion.", level='ACTION')
        self.destroy(delete_text=True)
        self.editor.focus_set()

    def rephrase(self):
        if llm_state._is_generating: return
        debug_console.log("User triggered REPHRASE on suggestion.", level='ACTION')
        import llm_rephrase
        text_to_rephrase = self.full_response_text
        if not text_to_rephrase.strip():
            messagebox.showinfo("Rephrase", "Nothing to rephrase yet. Wait for text to be generated.")
            return
        def on_validate_rephrase_request():
            self.destroy(delete_text=True)
        self.editor.after(10, lambda: llm_rephrase.request_rephrase_for_text(
            self.editor, text_to_rephrase, self.block_start_index, self.text_end_index,
            on_validate_callback=on_validate_rephrase_request
        ))
        
    def _post_process_completion(self):
        cleaned_text = llm_utils.remove_prefix_overlap_from_completion(self.completion_phrase, self.full_response_text)
        debug_console.log(f"Post-processing completion. Original length: {len(self.full_response_text)}, Cleaned length: {len(cleaned_text)}", level='DEBUG')
        text_start = self.buttons_end_index
        self.editor.delete(text_start, self.text_end_index)
        self.editor.insert(text_start, cleaned_text, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{text_start} + {len(cleaned_text)} chars")

    def destroy(self, delete_text):
        global _current_session
        debug_console.log(f"Destroying session. Deleting text: {delete_text}", level='INFO')
        self._stop_generating_animation()
        self._unbind_keyboard_shortcuts()
        try:
            if delete_text: self.editor.delete(self.block_start_index, self.text_end_index)
            else: self.editor.delete(self.block_start_index, self.buttons_end_index)
            if self.buttons_frame: self.buttons_frame.destroy()
        except tk.TclError: pass
        _current_session = None
        llm_state._is_generating = False

def start_new_interactive_session(editor, is_completion=False, completion_phrase=""):
    """Starts a new interactive session, replacing any existing one."""
    global _current_session
    if _current_session:
        debug_console.log("Discarding existing session to start a new one.", level='WARNING')
        _current_session.discard()
    llm_state._is_generating = True
    start_index = editor.index(tk.INSERT)
    _current_session = InteractiveSession(editor, start_index, is_completion, completion_phrase)
    return {'on_chunk': _current_session.handle_chunk, 'on_success': _current_session.handle_success, 'on_error': _current_session.handle_error}