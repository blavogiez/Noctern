# gui_generation_controller.py
"""
Manages the interactive UI for LLM generation within the editor.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font

class GenerationUIController:
    """Manages the small UI widget that appears in the editor during LLM generation."""
    def __init__(self, editor, theme_getter):
        self.editor = editor
        self.theme_getter = theme_getter
        self.frame = ttk.Frame(self.editor)
        self.is_cleaned_up = False

        # Callbacks to be set by the service
        self.accept_callback = None
        self.rephrase_callback = None
        self.cancel_callback = None

        # Buttons
        self.accept_button = ttk.Button(self.frame, text="✅ Accept (Tab/Enter)", command=self._on_accept, style="Accent.TButton")
        self.rephrase_button = ttk.Button(self.frame, text="🔄 Rephrase (r)", command=self._on_rephrase) # Kept as 'r' for consistency with existing code
        self.cancel_button = ttk.Button(self.frame, text="❌ Cancel (c)", command=self._on_cancel)

        # Marks and tags for the generated text
        self.start_mark_name = f"gen_start_{id(self)}"
        self.end_mark_name = f"gen_end_{id(self)}"
        self.tag_name = f"live_gen_{id(self)}"

        # Set the marks at the current cursor position and define their gravity
        self.editor.mark_set(self.start_mark_name, "insert")
        self.editor.mark_set(self.end_mark_name, "insert")
        self.editor.mark_gravity(self.start_mark_name, "left")
        self.editor.mark_gravity(self.end_mark_name, "right")

        # Create an italic font for the generated text, and initialize storage for original Tab binding
        try:
            # Create a new Font object based on the editor's current font configuration
            current_font = Font(font=self.editor.cget("font"))
            italic_font = current_font.copy()
            italic_font.configure(slant="italic")
        except tk.TclError:
            # Fallback if font introspection fails
            italic_font = ("Consolas", 12, "italic")

        # Determine background color for the generated text based on the current theme
        gen_bg = "#2a2d31" if self.theme_getter("root_bg", "").startswith("#2") else "#e8f0f8"
        self.editor.tag_configure(self.tag_name, background=gen_bg, font=italic_font)

        self.original_tab_binding_func = None # To store the original Tab binding function

    def _on_accept(self): # Renamed from _on_accept to _on_accept
        """Handles the 'Accept' button click."""
        if self.accept_callback: self.accept_callback()

    def _on_rephrase(self):
        """Handles the 'Rephrase' button click."""
        text_to_rephrase = self.get_text()
        if not text_to_rephrase.strip():
            messagebox.showwarning("Rephrase", "There is no generated text to rephrase.", parent=self.editor)
            return
        if self.rephrase_callback: self.rephrase_callback(text_to_rephrase)

    def _on_cancel(self):
        """Handles the 'Cancel' or 'Discard' button click."""
        if self.cancel_callback: self.cancel_callback()

    def _bind_keys_for_generating(self):
        """Binds keys for the 'generating' state, taking precedence over editor's default Tab."""
        self._unbind_keys()
        # Store the original <Tab> binding function and replace it with our handler
        self.original_tab_binding_func = self.editor.bind('<Tab>', lambda event: (self._on_cancel(), "break")[1]) # Tab also cancels during generation
        # Bind 'c' for cancel. Returning "break" prevents the character from being inserted.
        self.editor.bind('<c>', lambda event: (self._on_cancel(), "break")[1])

    def _bind_keys_for_finished(self):
        """Binds keys for the 'finished' state, taking precedence over editor's default Tab."""
        self._unbind_keys()
        # Store the original <Tab> binding function and replace it with our accept handler
        self.original_tab_binding_func = self.editor.bind('<Tab>', lambda event: (self._on_accept(), "break")[1])
        # Also bind <Return> (Enter key) for acceptance. Returning "break" prevents a newline.
        self.editor.bind('<Return>', lambda event: (self._on_accept(), "break")[1])
        
        # Bind 'r' and 'c'. Returning "break" prevents the characters from being inserted.
        self.editor.bind('<r>', lambda event: (self._on_rephrase(), "break")[1])
        self.editor.bind('<c>', lambda event: (self._on_cancel(), "break")[1])

    def _unbind_keys(self):
        """Unbinds all keys managed by this controller and restores original bindings."""
        # Restore original Tab binding if it was stored
        if self.original_tab_binding_func:
            self.editor.bind('<Tab>', self.original_tab_binding_func)
            self.original_tab_binding_func = None # Clear it after restoring

        # Explicitly unbind the keys we set. This restores their default class behavior (e.g., inserting the character).
        self.editor.bind('<Return>', '') # Remove all <Return> bindings added by this controller
        self.editor.bind('<r>', '') # Remove all 'r' bindings added by this controller
        self.editor.bind('<c>', '') # Remove all 'c' bindings added by this controller

    def show_generating_state(self):
        """Displays the UI in its 'generating' state (only cancel button)."""
        for widget in self.frame.winfo_children(): widget.pack_forget()
        self.cancel_button.pack(side="left")
        self.editor.window_create(self.start_mark_name, window=self.frame, align="top")
        self._bind_keys_for_generating()

    def show_finished_state(self):
        """Displays the UI in its 'finished' state (accept, rephrase, discard buttons)."""
        if self.is_cleaned_up:
            return
        for widget in self.frame.winfo_children(): widget.pack_forget()
        self.accept_button.pack(side="left", padx=2) # Renamed from accept_button to accept_button
        self.rephrase_button.pack(side="left", padx=2)
        self.cancel_button.config(text="❌ Discard (c)")
        self.cancel_button.pack(side="left", padx=2)
        self._bind_keys_for_finished()

    def insert_chunk(self, chunk):
        """Inserts a chunk of generated text into the editor."""
        if self.is_cleaned_up:
            return

        try:
            self.editor.insert(self.end_mark_name, chunk, (self.tag_name,))
        except tk.TclError as e:
            # This can happen if the editor/tab is closed while generating.
            print(f"Harmless TclError in insert_chunk (widget likely destroyed): {e}")
            self.is_cleaned_up = True # Prevent further attempts

    def get_text(self):
        """Returns the text that has been generated so far."""
        return self.editor.get(self.start_mark_name, self.end_mark_name)

    def get_start_index(self):
        """Returns the start index of the generated text."""
        return self.editor.index(self.start_mark_name)

    def get_end_index(self):
        """Returns the end index of the generated text."""
        return self.editor.index(self.end_mark_name)

    def cleanup(self, is_accept=False):
        """Removes the UI and the generated text (if not accepted)."""
        if self.is_cleaned_up:
            return
        self.is_cleaned_up = True

        self._unbind_keys() # Unbind keys as soon as interaction is over

        try:
            if not is_accept:
                self.editor.delete(self.start_mark_name, self.end_mark_name)
            else:
                # If accepted, remove all styling from the generated text.
                self.editor.tag_remove(self.tag_name, self.start_mark_name, self.end_mark_name)

            if self.frame.winfo_exists():
                self.frame.destroy()

            # Clean up the marks to prevent them from lingering
            self.editor.mark_unset(self.start_mark_name)
            self.editor.mark_unset(self.end_mark_name)
        except tk.TclError as e:
            # This can happen if the editor/tab is closed before cleanup completes.
            print(f"Harmless TclError during cleanup (widget likely destroyed): {e}")
