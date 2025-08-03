import tkinter as tk
from tkinter import messagebox
from llm import state as llm_state
from llm import utils as llm_utils
from utils import debug_console
from app import state as main_window
import uuid

_current_session = None

def get_current_session_id():
    """Returns the UUID of the currently active session, or None."""
    return _current_session.session_id if _current_session else None

class InteractiveSession:
    """Manages the UI and interaction for an LLM generation session."""
    def __init__(self, editor, start_index, **kwargs):
        self.session_id = uuid.uuid4()
        debug_console.log(f"Creating new interactive LLM session: {self.session_id}", level='INFO')
        self.editor = editor
        self.is_discarded = False
        self.full_response_text = ""
        
        self.is_completion = kwargs.get('is_completion', False)
        self.is_rephrase = kwargs.get('is_rephrase', False)
        self.is_styling = kwargs.get('is_styling', False)
        self.completion_phrase = kwargs.get('completion_phrase', "")
        self.on_discard_callback = kwargs.get('on_discard_callback')
        
        self.hidden_tag = None
        if self.is_styling:
            selection_indices = kwargs.get('selection_indices')
            self.hidden_tag = f"styling_hidden_{self.session_id}"
            self.editor.tag_add(self.hidden_tag, selection_indices[0], selection_indices[1])
            self.editor.tag_config(self.hidden_tag, elide=True)

        self.block_start_index = editor.index(start_index)
        self.buttons_frame = self._create_ui_elements()
        self.editor.window_create(self.block_start_index, window=self.buttons_frame, padx=5, align="center")
        
        self.text_start_index = self.editor.index(f"{self.block_start_index} + 1 char")
        self.text_end_index = self.text_start_index
        
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
        
        frame.pack(side=tk.LEFT)
        accept_btn.pack(side=tk.LEFT)
        rephrase_btn.pack(side=tk.LEFT)
        discard_btn.pack(side=tk.LEFT)
        return frame

    def _bind_keyboard_shortcuts(self):
        self.editor.bind("<Tab>", lambda e: self.accept() or "break")
        self.editor.bind("<Escape>", lambda e: self.discard() or "break")
        self.editor.bind("<Control-r>", lambda e: self.rephrase() or "break")
        self.editor.bind("<Control-R>", lambda e: self.rephrase() or "break")

    def _unbind_keyboard_shortcuts(self):
        self.editor.unbind("<Tab>")
        self.editor.unbind("<Escape>")
        self.editor.unbind("<Control-r>")
        self.editor.unbind("<Control-R>")

    def handle_chunk(self, chunk):
        if self.is_discarded: return
        self.editor.insert(self.text_end_index, chunk, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{self.text_end_index} + {len(chunk)} chars")
        self.full_response_text += chunk

    def handle_success(self, final_cleaned_text):
        if self.is_discarded: return
        self.editor.delete(self.text_start_index, self.text_end_index)
        self.editor.insert(self.text_start_index, final_cleaned_text, "llm_generated_text")
        self.text_end_index = self.editor.index(f"{self.text_start_index} + {len(final_cleaned_text)} chars")
        self.full_response_text = final_cleaned_text
        if self.is_completion: self._post_process_completion()
        if self.is_rephrase: self.editor.tag_add(tk.SEL, self.text_start_index, self.text_end_index)
        self.editor.focus_set()

    def handle_error(self, error_msg):
        if self.is_discarded: return
        messagebox.showerror("LLM Error", error_msg)
        self.destroy(delete_text=True)

    def accept(self):
        if self.is_discarded or llm_state._is_generating: return
        debug_console.log(f"User ACCEPTED LLM suggestion for session {self.session_id}.", level='ACTION')

        # --- FIX 1: Immediately stop progress bar ---
        progress_bar = llm_state._llm_progress_bar_widget
        if progress_bar and progress_bar.winfo_exists():
            progress_bar.stop()
            progress_bar.pack_forget()

        if self.is_styling:
            # --- FIX 2: Correct order of operations ---
            # 1. Get insertion position
            insert_pos = self.editor.index(f"{self.hidden_tag}.first")
            # 2. Delete original text
            self.editor.delete(f"{self.hidden_tag}.first", f"{self.hidden_tag}.last")
            self.editor.tag_delete(self.hidden_tag)
            # 3. Insert the final text at the correct position BEFORE destroying UI
            self.editor.insert(insert_pos, self.full_response_text)
            # 4. Now, destroy the temporary UI elements
            self.destroy(delete_text=True)
        else:
            # Default behavior for completion/generation
            self.editor.tag_remove("llm_generated_text", self.text_start_index, self.text_end_index)
            self.destroy(delete_text=False)
            
        self.editor.focus_set()

    def discard(self):
        if self.is_discarded: return
        debug_console.log(f"User DISCARDED LLM suggestion for session {self.session_id}. Forcing state reset.", level='ACTION')
        self.is_discarded = True
        llm_state._is_generation_cancelled = True
        llm_state._is_generating = False
        progress_bar = llm_state._llm_progress_bar_widget
        if progress_bar and progress_bar.winfo_exists():
            progress_bar.stop()
            progress_bar.pack_forget()
        if self.is_styling and self.hidden_tag: self.editor.tag_delete(self.hidden_tag)
        self.destroy(delete_text=True)
        if self.on_discard_callback: self.on_discard_callback()
        self.editor.focus_set()

    def rephrase(self):
        if llm_state._is_generating: return
        from . import rephrase as llm_rephrase
        if not self.full_response_text.strip(): return
        self.destroy(delete_text=False)
        new_start_index = self.block_start_index
        new_end_index = self.editor.index(f"{new_start_index} + {len(self.full_response_text)} chars")
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
        self._unbind_keyboard_shortcuts()
        try:
            if delete_text and self.editor.winfo_exists():
                self.editor.delete(self.text_start_index, self.text_end_index)
            if self.editor.winfo_exists(): self.editor.delete(self.block_start_index)
            if self.buttons_frame.winfo_exists(): self.buttons_frame.destroy()
        except tk.TclError: pass
        if _current_session and _current_session.session_id == self.session_id:
            _current_session = None

def start_new_interactive_session(editor, **kwargs):
    global _current_session
    if _current_session:
        _current_session.discard()
    
    llm_state._is_generation_cancelled = False
    
    start_index = editor.index(kwargs.get('selection_indices', [tk.INSERT])[0])
    editor.edit_separator()
    
    _current_session = InteractiveSession(editor, start_index, **kwargs)
    
    return {
        'on_chunk': _current_session.handle_chunk,
        'on_success': _current_session.handle_success,
        'on_error': _current_session.handle_error
    }