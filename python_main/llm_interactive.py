import llm_state
import tkinter as tk
from tkinter import messagebox
import datetime
import interface
import llm_utils
# NOTE: Pas d'import global de llm_rephrase ici pour éviter une dépendance circulaire
# au chargement du module. L'import sera fait localement dans la fonction.

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
        # --- ROBUST BINDING: Bind shortcuts when the session is created ---
        self._bind_keyboard_shortcuts()


    def _create_ui_elements(self):
        """Crée la frame des boutons avec un style compact et fonctionnel."""
        NAVY_BLUE = "#0078D4"
        MODERN_BLACK = "#2D2D2D"
        HOVER_BLACK = "#404040"
        TEXT_COLOR = "#F0F0F0"

        frame_style = {"bg": MODERN_BLACK, "bd": 0}
        btn_style = {"relief": tk.FLAT, "bd": 0, "fg": TEXT_COLOR, "font": ("Segoe UI", 9),
                     "cursor": "hand2", "padx": 8, "pady": 2, "activeforeground": "#FFFFFF"}
        
        frame = tk.Frame(self.editor, **frame_style)
        
        accept_btn = tk.Button(frame, text="Accept (Tab)", bg=NAVY_BLUE, activebackground="#005A9E", **btn_style, command=self.accept)
        rephrase_btn = tk.Button(frame, text="Rephrase (Ctrl+R)", bg=MODERN_BLACK, activebackground=HOVER_BLACK, **btn_style, command=self.rephrase)
        discard_btn = tk.Button(frame, text="Discard (Esc)", bg=MODERN_BLACK, activebackground=HOVER_BLACK, **btn_style, command=self.discard)
        
        accept_btn.pack(side=tk.LEFT)
        rephrase_btn.pack(side=tk.LEFT)
        discard_btn.pack(side=tk.LEFT)
        
        return frame

    # --- START: ROBUST SHORTCUT HANDLING ---
    def _bind_keyboard_shortcuts(self):
        """Binds keys specifically for this session's lifetime."""
        self.editor.bind("<Tab>", self._handle_accept_key)
        self.editor.bind("<Escape>", self._handle_discard_key)
        self.editor.bind("<Control-r>", self._handle_rephrase_key)
        self.editor.bind("<Control-R>", self._handle_rephrase_key) # For consistency

    def _unbind_keyboard_shortcuts(self):
        """Unbinds all session-specific keys to restore normal editor behavior."""
        self.editor.unbind("<Tab>")
        self.editor.unbind("<Escape>")
        self.editor.unbind("<Control-r>")
        self.editor.unbind("<Control-R>")
        
    def _handle_accept_key(self, event=None):
        """Handles the Tab key to accept the suggestion."""
        if not llm_state._is_generating:
            self.accept()
        return "break"  # This is CRITICAL: it prevents the default Tab behavior.

    def _handle_discard_key(self, event=None):
        """Handles the Escape key to discard the suggestion."""
        self.discard()
        return "break"  # Prevents any other Escape behavior.
        
    def _handle_rephrase_key(self, event=None):
        """Handles Ctrl+R to rephrase the suggestion."""
        if not llm_state._is_generating:
            self.rephrase()
        return "break"  # Prevents any other default behavior.
    # --- END: ROBUST SHORTCUT HANDLING ---

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
        self.editor.focus_set() # Ensure focus is on the editor for shortcuts to work
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} INFO: LLM stream finished.")

    def handle_error(self, error_msg):
        messagebox.showerror("LLM Error", error_msg)
        self.destroy(delete_text=True)

    # --- Actions utilisateur ---
    def accept(self):
        if llm_state._is_generating: return
        self.editor.tag_remove("llm_generated_text", self.buttons_end_index, self.text_end_index)
        self.destroy(delete_text=False)
        self.editor.focus_set()

    def discard(self):
        self.destroy(delete_text=True)
        self.editor.focus_set()

    def rephrase(self):
        """
        Action de reformulation non-destructive : demande une instruction, et ne
        remplace cette session que si l'utilisateur valide la nouvelle requête.
        """
        if llm_state._is_generating: return

        import llm_rephrase

        text_to_rephrase = self.full_response_text
        start_pos = self.block_start_index
        
        if not text_to_rephrase.strip():
            messagebox.showinfo("Rephrase", "Nothing to rephrase yet. Please wait for text to be generated.")
            return

        # Le callback `on_validate` ne sera appelé que si l'utilisateur
        # confirme la reformulation dans la boîte de dialogue.
        def on_validate_rephrase_request():
            # C'est seulement maintenant qu'on détruit l'ancienne session.
            self.destroy(delete_text=True)

        # On appelle la nouvelle fonction logique en lui passant un callback
        # qui s'occupera de détruire l'ancienne session au bon moment.
        self.editor.after(10, lambda: llm_rephrase.request_rephrase_for_text(
            self.editor, 
            text_to_rephrase, 
            start_pos, 
            self.text_end_index, # On passe end_index pour la cohérence
            on_validate_callback=on_validate_rephrase_request
        ))
        
    def _post_process_completion(self):
        cleaned_text = llm_utils.remove_prefix_overlap_from_completion(self.completion_phrase, self.full_response_text)
        text_start = self.buttons_end_index
        self.editor.delete(text_start, self.text_end_index)
        self.editor.insert(text_start, cleaned_text, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{text_start} + {len(cleaned_text)} chars")

    def destroy(self, delete_text):
        global _current_session
        self._stop_generating_animation()
        
        # --- ROBUST CLEANUP: Always unbind the keys ---
        self._unbind_keyboard_shortcuts()

        try:
            if delete_text: self.editor.delete(self.block_start_index, self.text_end_index)
            else: self.editor.delete(self.block_start_index, self.buttons_end_index)
            if self.buttons_frame: self.buttons_frame.destroy()
        except tk.TclError: 
            # This can happen if the parent widget is already destroyed. Safe to ignore.
            pass
        _current_session = None
        llm_state._is_generating = False

def start_new_interactive_session(editor, is_completion=False, completion_phrase=""):
    """
    Démarre une nouvelle session et retourne un dictionnaire de callbacks.
    Modifié pour ne plus prendre start_index, car il est calculé à l'intérieur.
    """
    global _current_session
    if _current_session: _current_session.discard()
    llm_state._is_generating = True
    # Le start_index est toujours la position actuelle du curseur
    start_index = editor.index(tk.INSERT)
    _current_session = InteractiveSession(editor, start_index, is_completion, completion_phrase)
    return {'on_chunk': _current_session.handle_chunk, 'on_success': _current_session.handle_success, 'on_error': _current_session.handle_error}

# --- The old, fragile global key handler has been REMOVED ---
# --- All logic is now self-contained in the InteractiveSession class ---
# --- No need for bind_keyboard_shortcuts() or any global handlers anymore. ---