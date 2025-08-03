import tkinter as tk
from tkinter import messagebox
from llm import state as llm_state
from llm import utils as llm_utils
from utils import debug_console
from app import state as main_window
import uuid # Import uuid for unique session IDs

# This global variable will hold the single active interactive session.
_current_session = None

class InteractiveSession:
    """
    Manages the UI and interaction for an LLM generation session.
    This class should NOT manage the `_is_generating` state flag.
    """

    def __init__(self, editor, start_index, is_completion=False, is_rephrase=False, is_styling=False, completion_phrase="", on_discard_callback=None, selection_indices=None):
        self.session_id = uuid.uuid4()
        debug_console.log(f"Creating new interactive LLM session: {self.session_id}", level='INFO')
        self.editor = editor
        self.is_completion = is_completion
        self.is_rephrase = is_rephrase
        self.is_styling = is_styling
        self.completion_phrase = completion_phrase
        self.full_response_text = ""
        self.is_animating = False
        self.animation_dot_count = 0
        self.on_discard_callback = on_discard_callback
        self.is_discarded = False

        self.hidden_tag = None
        if is_styling and selection_indices:
            self.selection_start_index = selection_indices[0]
            self.selection_end_index = selection_indices[1]
            self.hidden_tag = f"styling_hidden_{self.session_id}"
            self.editor.tag_add(self.hidden_tag, self.selection_start_index, self.selection_end_index)
            self.editor.tag_config(self.hidden_tag, elide=True)
        else:
            self.selection_start_index = None
            self.selection_end_index = None

        self.block_start_index = editor.index(start_index)
        self.buttons_frame = self._create_ui_elements()
        self.editor.window_create(self.block_start_index, window=self.buttons_frame, padx=5, align="center")
        
        self.text_start_index = self.editor.index(f"{self.block_start_index} + 1 char")
        self.text_end_index = self.text_start_index
        
        self._start_generating_animation()
        self._bind_keyboard_shortcuts()

    def _create_ui_elements(self):
        bg_color = main_window.get_theme_setting("llm_generated_bg", "#2D2D2D")
        fg_color = main_window.get_theme_setting("llm_generated_fg", "#F0F0F0")
        button_bg = main_window.get_theme_setting("button_bg", "#0078D4")
        button_fg = main_window.get_theme_setting("button_fg", "#F0F0F0")
        button_active_bg = main_window.get_theme_setting("sel_bg", "#005A9E")
        
        frame = tk.Frame(self.editor, bg=bg_color, bd=0)
        btn_style = {"relief": tk.FLAT, "bd": 0, "fg": button_fg, "font": ("Segoe UI", 9),
                     "cursor": "hand2", "padx": 8, "pady": 2, "activeforeground": button_fg}
        
        accept_btn = tk.Button(frame, text="Accept (Tab)", bg=button_bg, activebackground=button_active_bg, **btn_style, command=self.accept)
        rephrase_btn = tk.Button(frame, text="Rephrase (Ctrl+R)", bg=bg_color, activebackground=button_active_bg, **btn_style, command=self.rephrase)
        discard_btn = tk.Button(frame, text="Discard (Esc)", bg=bg_color, activebackground=button_active_bg, **btn_style, command=self.discard)
        
        self.animation_label = tk.Label(frame, text="", bg=bg_color, fg=fg_color, font=("Segoe UI", 9, "italic"), padx=5)

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
        if self.is_rephrase: self.editor.tag_add(tk.SEL, self.text_start_index, self.text_end_index)

        self.editor.focus_set()

    def handle_error(self, error_msg):
        if self.is_discarded: return
        debug_console.log(f"LLM interactive session error: {error_msg}", level='ERROR')
        messagebox.showerror("LLM Error", error_msg)
        self.destroy(delete_text=True)

    def accept(self):
        if self.is_discarded or llm_state._is_generating: return
        debug_console.log(f"User ACCEPTED LLM suggestion for session {self.session_id}.", level='ACTION')
        
        if self.is_styling:
            final_text = self.full_response_text
            insert_pos = self.editor.index(f"{self.hidden_tag}.first")
            self.editor.delete(f"{self.hidden_tag}.first", f"{self.hidden_tag}.last")
            self.editor.tag_delete(self.hidden_tag)
            self.destroy(delete_text=True)
            self.editor.insert(insert_pos, final_text)
        else:
            self.editor.tag_remove("llm_generated_text", self.text_start_index, self.text_end_index)
            self.destroy(delete_text=False)
        self.editor.focus_set()

    def discard(self):
        if self.is_discarded: return
        debug_console.log(f"User DISCARDED LLM suggestion for session {self.session_id}.", level='ACTION')
        self.is_discarded = True
        llm_state._is_generation_cancelled = True
        debug_console.log("Cancellation flag set for ongoing generation.", level='INFO')
        if self.is_styling and self.hidden_tag: self.editor.tag_delete(self.hidden_tag)
        self.destroy(delete_text=True)
        if self.on_discard_callback: self.on_discard_callback()
        self.editor.focus_set()

    def rephrase(self):
        if llm_state._is_generating: return
        from . import rephrase as llm_rephrase
        text_to_rephrase = self.full_response_text
        if not text_to_rephrase.strip():
            messagebox.showinfo("Rephrase", "Nothing to rephrase yet.")
            return
        self.destroy(delete_text=False)
        new_start_index = self.block_start_index
        new_end_index = self.editor.index(f"{new_start_index} + {len(text_to_rephrase)} chars")
        self.editor.tag_add(tk.SEL, new_start_index, new_end_index)
        self.editor.focus_set()
        llm_rephrase.open_rephrase_dialog()

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
            if delete_text and self.editor.winfo_exists():
                start_text = self.editor.index(self.text_start_index)
                end_text = self.editor.index(self.text_end_index)
                if self.editor.compare(start_text, "<", end_text):
                    self.editor.delete(start_text, end_text)
            if self.editor.winfo_exists(): self.editor.delete(self.block_start_index)
            if self.buttons_frame and self.buttons_frame.winfo_exists(): self.buttons_frame.destroy()
        except tk.TclError as e:
            debug_console.log(f"Error destroying interactive session UI: {e}", level='ERROR')
        _current_session = None

def start_new_interactive_session(editor, is_completion=False, is_rephrase=False, is_styling=False, completion_phrase="", on_discard_callback=None, selection_indices=None):
    global _current_session
    if _current_session:
        _current_session.discard()
    
    llm_state._is_generation_cancelled = False
    
    if is_styling and selection_indices:
        start_index = editor.index(selection_indices[0])
    else:
        start_index = editor.index(tk.INSERT)
    
    editor.edit_separator()
    
    _current_session = InteractiveSession(
        editor, start_index, 
        is_completion=is_completion, 
        is_rephrase=is_rephrase,
        is_styling=is_styling,
        completion_phrase=completion_phrase, 
        on_discard_callback=on_discard_callback,
        selection_indices=selection_indices
    )
    
    return {
        'on_chunk': _current_session.handle_chunk,
        'on_success': _current_session.handle_success,
        'on_error': _current_session.handle_error
    }
