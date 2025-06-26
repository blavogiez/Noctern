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
        self.rephrase_button = ttk.Button(self.frame, text="🔄 Rephrase (r)", command=self._on_rephrase)
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

        # Create an italic font for the generated text
        try:
            current_font = Font(font=self.editor.cget("font"))
            italic_font = current_font.copy()
            italic_font.configure(slant="italic")
        except tk.TclError:
            italic_font = ("Consolas", 12, "italic")

        # Determine background color for the generated text based on the current theme
        gen_bg = "#2a2d31" if self.theme_getter("root_bg", "").startswith("#2") else "#e8f0f8"
        self.editor.tag_configure(self.tag_name, background=gen_bg, font=italic_font)

        # Store original bindings to restore them properly
        self.original_bindings = {}
        self.bound_keys = []

    def _on_accept(self):
        """Handles the 'Accept' button click."""
        if self.accept_callback: 
            self.accept_callback()

    def _on_rephrase(self):
        """Handles the 'Rephrase' button click."""
        text_to_rephrase = self.get_text()
        if not text_to_rephrase.strip():
            messagebox.showwarning("Rephrase", "There is no generated text to rephrase.", parent=self.editor)
            return
        if self.rephrase_callback: 
            self.rephrase_callback(text_to_rephrase)

    def _on_cancel(self):
        """Handles the 'Cancel' or 'Discard' button click."""
        if self.cancel_callback: 
            self.cancel_callback()

    def _store_original_binding(self, key):
        """Store the original binding for a key before overriding it."""
        if key not in self.original_bindings:
            # Get all bindings for this key (there might be multiple)
            bindings = self.editor.bind(key)
            self.original_bindings[key] = bindings

    def _bind_key(self, key, callback):
        """Bind a key with proper storage of original binding."""
        if key not in self.bound_keys:
            self._store_original_binding(key)
            self.bound_keys.append(key)
        
        def handler(event):
            callback()
            return "break"
        
        self.editor.bind(key, handler)

    def _bind_keys_for_generating(self):
        """Binds keys for the 'generating' state."""
        self._unbind_keys()  # Clean up any existing bindings first
        
        # Bind keys for generating state
        self._bind_key('<Tab>', self._on_cancel)  # Tab cancels during generation
        self._bind_key('<c>', self._on_cancel)

    def _bind_keys_for_finished(self):
        """Binds keys for the 'finished' state."""
        self._unbind_keys()  # Clean up any existing bindings first
        
        # Bind keys for finished state
        self._bind_key('<Tab>', self._on_accept)
        self._bind_key('<Return>', self._on_accept)
        self._bind_key('<r>', self._on_rephrase)
        self._bind_key('<c>', self._on_cancel)

    def _unbind_keys(self):
        """Properly restore original key bindings."""
        for key in self.bound_keys:
            if key in self.original_bindings:
                original_binding = self.original_bindings[key]
                if original_binding:
                    # Restore the original binding
                    self.editor.bind(key, original_binding)
                else:
                    # If there was no original binding, unbind completely
                    self.editor.unbind(key)
            else:
                # Fallback: unbind the key
                self.editor.unbind(key)
        
        # Clear the tracking lists but keep original_bindings for potential reuse
        self.bound_keys.clear()

    def show_generating_state(self):
        """Displays the UI in its 'generating' state (only cancel button)."""
        if self.is_cleaned_up:
            return
            
        # Clear existing widgets efficiently
        for widget in self.frame.winfo_children(): 
            widget.pack_forget()
        
        self.cancel_button.pack(side="left")
        
        # Only create window if it doesn't exist
        try:
            self.editor.window_create(self.start_mark_name, window=self.frame, align="top")
        except tk.TclError:
            # Window might already exist or mark might be invalid
            pass
            
        self._bind_keys_for_generating()

    def show_finished_state(self):
        """Displays the UI in its 'finished' state (accept, rephrase, discard buttons)."""
        if self.is_cleaned_up:
            return
            
        # Clear existing widgets efficiently
        for widget in self.frame.winfo_children(): 
            widget.pack_forget()
        
        self.accept_button.pack(side="left", padx=2)
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
            print(f"Harmless TclError in insert_chunk (widget likely destroyed): {e}")
            self.is_cleaned_up = True

    def get_text(self):
        """Returns the text that has been generated so far."""
        if self.is_cleaned_up:
            return ""
        try:
            return self.editor.get(self.start_mark_name, self.end_mark_name)
        except tk.TclError:
            return ""

    def get_start_index(self):
        """Returns the start index of the generated text."""
        if self.is_cleaned_up:
            return "1.0"
        try:
            return self.editor.index(self.start_mark_name)
        except tk.TclError:
            return "1.0"

    def get_end_index(self):
        """Returns the end index of the generated text."""
        if self.is_cleaned_up:
            return "1.0"
        try:
            return self.editor.index(self.end_mark_name)
        except tk.TclError:
            return "1.0"

    def cleanup(self, is_accept=False):
        """Removes the UI and the generated text (if not accepted)."""
        if self.is_cleaned_up:
            return
        
        self.is_cleaned_up = True

        # Unbind keys immediately to prevent lag
        self._unbind_keys()

        try:
            # Handle text cleanup
            if not is_accept:
                self.editor.delete(self.start_mark_name, self.end_mark_name)
            else:
                # If accepted, remove styling from the generated text
                self.editor.tag_remove(self.tag_name, self.start_mark_name, self.end_mark_name)

            # Clean up tag definition to prevent memory leaks
            self.editor.tag_delete(self.tag_name)

            # Destroy the frame widget
            if self.frame.winfo_exists():
                self.frame.destroy()

            # Clean up marks
            self.editor.mark_unset(self.start_mark_name)
            self.editor.mark_unset(self.end_mark_name)
            
        except tk.TclError as e:
            print(f"Harmless TclError during cleanup (widget likely destroyed): {e}")
        
        # Final cleanup of stored data
        self.original_bindings.clear()
        self.bound_keys.clear()