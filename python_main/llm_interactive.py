import llm_state
import tkinter as tk
from tkinter import messagebox
import datetime
import interface
import llm_utils

# Cette variable globale contiendra la seule session active.
_current_session = None

class InteractiveSession:
    """Une classe robuste pour gérer l'état et l'UI d'une interaction LLM."""

    def __init__(self, editor, start_index, is_completion=False, completion_phrase=""):
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

    def _create_ui_elements(self):
        """Crée la frame des boutons avec un style compact et fonctionnel."""
        NAVY_BLUE = "#0078D4"
        MODERN_BLACK = "#2D2D2D"
        HOVER_BLACK = "#404040"
        TEXT_COLOR = "#F0F0F0"

        frame_style = {"bg": MODERN_BLACK, "bd": 0}
        # --- STYLE CORRIGÉ : Taille de police et padding réduits ---
        btn_style = {"relief": tk.FLAT, "bd": 0, "fg": TEXT_COLOR, "font": ("Segoe UI", 9), # Police plus petite, non grasse
                     "cursor": "hand2", "padx": 8, "pady": 2, "activeforeground": "#FFFFFF"} # Padding réduit
        
        frame = tk.Frame(self.editor, **frame_style)
        
        accept_btn = tk.Button(frame, text="Accept", bg=NAVY_BLUE, activebackground="#005A9E", **btn_style)
        rephrase_btn = tk.Button(frame, text="Rephrase", bg=MODERN_BLACK, activebackground=HOVER_BLACK, **btn_style)
        discard_btn = tk.Button(frame, text="Discard", bg=MODERN_BLACK, activebackground=HOVER_BLACK, **btn_style)

        # --- FIX : On bind l'événement de clic explicitement pour forcer l'action ---
        accept_btn.bind("<Button-1>", lambda event: self.accept())
        rephrase_btn.bind("<Button-1>", lambda event: self.rephrase())
        discard_btn.bind("<Button-1>", lambda event: self.discard())
        
        accept_btn.pack(side=tk.LEFT)
        rephrase_btn.pack(side=tk.LEFT)
        discard_btn.pack(side=tk.LEFT)
        
        return frame

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

    # --- Callbacks pour les threads ---
    def handle_chunk(self, chunk):
        if self.is_animating: self._stop_generating_animation()
        self.editor.insert(self.text_end_index, chunk, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{self.text_end_index} + {len(chunk)} chars")
        self.full_response_text += chunk

    def handle_success(self):
        self._stop_generating_animation()
        if self.is_completion: self._post_process_completion()
        llm_state._is_generating = False
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM stream finished.")

    def handle_error(self, error_msg):
        messagebox.showerror("LLM Error", error_msg)
        self.destroy(delete_text=True)

    # --- Actions utilisateur ---
    def accept(self):
        self.editor.tag_remove("llm_generated_text", self.buttons_end_index, self.text_end_index)
        self.destroy(delete_text=False)
        self.editor.focus_set()

    def discard(self):
        self.destroy(delete_text=True)
        self.editor.focus_set()

    def rephrase(self):
        import llm_completion, llm_generation
        last_action, last_prompt, last_phrase = (llm_state._last_llm_action_type, llm_state._last_generation_user_prompt, llm_state._last_completion_phrase_start)
        self.destroy(delete_text=True)
        if last_action == "completion": llm_completion.request_llm_to_complete_text()
        elif last_action == "generation": llm_generation.open_generate_text_dialog(initial_prompt_text=last_prompt)

    def _post_process_completion(self):
        cleaned_text = llm_utils.remove_prefix_overlap_from_completion(self.completion_phrase, self.full_response_text)
        text_start = self.buttons_end_index
        self.editor.delete(text_start, self.text_end_index)
        self.editor.insert(text_start, cleaned_text, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{text_start} + {len(cleaned_text)} chars")

    def destroy(self, delete_text):
        global _current_session
        self._stop_generating_animation()
        try:
            if delete_text: self.editor.delete(self.block_start_index, self.text_end_index)
            else: self.editor.delete(self.block_start_index, self.buttons_end_index)
            if self.buttons_frame: self.buttons_frame.destroy()
        except tk.TclError: pass
        _current_session = None
        llm_state._is_generating = False

def start_new_interactive_session(editor, is_completion=False, completion_phrase=""):
    global _current_session
    if _current_session: _current_session.discard()
    llm_state._is_generating = True
    _current_session = InteractiveSession(editor, editor.index(tk.INSERT), is_completion, completion_phrase)
    return {'on_chunk': _current_session.handle_chunk, 'on_success': _current_session.handle_success, 'on_error': _current_session.handle_error}

# --- Gestionnaire de Raccourcis Centralisé et Robuste ---
def _handle_keypress(event):
    if not _current_session: return
    if llm_state._is_generating: return "break"
    key = event.keysym.lower()
    if key == 'tab': accept_generated_text()
    elif key == 'r': rephrase_generated_text()
    elif key == 'c': discard_generated_text()
    return "break"

def accept_generated_text():
    if _current_session and not llm_state._is_generating: _current_session.accept()
def discard_generated_text():
    if _current_session: _current_session.discard()
def rephrase_generated_text():
    if _current_session and not llm_state._is_generating: _current_session.rephrase()

def bind_keyboard_shortcuts(editor):
    editor.unbind("<Tab>")
    editor.unbind("<KeyPress-space>")
    editor.unbind("<KeyPress-r>")
    editor.unbind("<KeyPress-c>")
    editor.bind("<KeyPress>", _handle_keypress)