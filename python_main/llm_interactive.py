import llm_state
import tkinter as tk
from tkinter import messagebox
import interface
import llm_utils
import debug_console
# NOTE: llm_rephrase is imported locally within functions to avoid circular dependencies
# during module loading.

# This global variable will hold the single active interactive session.
_current_session = None

class InteractiveSession:
    """
    Manages an interactive LLM generation session within the editor.

    This class handles the display of streaming LLM output, provides UI controls
    (Accept, Rephrase, Discard), and manages session-specific keyboard shortcuts.
    It also includes an animation to indicate ongoing generation.
    """

    def __init__(self, editor, start_index, is_completion=False, completion_phrase=""):
        """
        Initializes a new interactive LLM session.

        Args:
            editor (tk.Text): The Tkinter Text widget where the LLM output will be displayed.
            start_index (str): The Tkinter index (e.g., "1.0", "insert") where the LLM output should begin.
            is_completion (bool, optional): True if this is a completion session, False for generation.
                                            Defaults to False.
            completion_phrase (str, optional): The phrase that was being completed, used for post-processing.
                                               Only relevant if `is_completion` is True. Defaults to "".
        """
        debug_console.log(f"Creating new interactive LLM session. Is completion: {is_completion}", level='INFO')
        self.editor = editor
        self.is_completion = is_completion
        self.completion_phrase = completion_phrase
        self.full_response_text = "" # Accumulates the full LLM-generated text.
        self.is_animating = False     # Flag to control the generation animation.
        self.animation_dot_count = 0  # Counter for the animation dots.

        # Store the starting index where the LLM output block begins.
        self.block_start_index = editor.index(start_index)
        
        # Create and embed the UI buttons (Accept, Rephrase, Discard).
        self.buttons_frame = self._create_ui_elements()
        self.editor.window_create(self.block_start_index, window=self.buttons_frame, padx=5, align="center")
        
        # Define the end index of the buttons frame and the initial end index of the text.
        # The text_end_index will move as chunks are inserted.
        self.buttons_end_index = self.editor.index(f"{self.block_start_index} + 1 char")
        self.text_end_index = self.buttons_end_index
        
        self._start_generating_animation() # Start the visual animation.
        self._bind_keyboard_shortcuts()    # Bind session-specific shortcuts.

    def _create_ui_elements(self):
        """
        Creates the Tkinter Frame containing the Accept, Rephrase, and Discard buttons.

        These buttons provide user control over the LLM-generated text.
        The buttons are styled for a compact and functional appearance.

        Returns:
            tk.Frame: The Tkinter Frame containing the interactive buttons.
        """
        frame = tk.Frame(self.editor, bg="#2D2D2D", bd=0) # Main frame for buttons.
        # Common style dictionary for buttons.
        btn_style = {"relief": tk.FLAT, "bd": 0, "fg": "#F0F0F0", "font": ("Segoe UI", 9),
                     "cursor": "hand2", "padx": 8, "pady": 2, "activeforeground": "#FFFFFF"}
        
        # Accept button: Confirms the LLM suggestion.
        accept_btn = tk.Button(frame, text="Accept (Tab)", bg="#0078D4", activebackground="#005A9E", **btn_style, command=self.accept)
        # Rephrase button: Initiates a rephrasing operation on the generated text.
        rephrase_btn = tk.Button(frame, text="Rephrase (Ctrl+R)", bg="#2D2D2D", activebackground="#404040", **btn_style, command=self.rephrase)
        # Discard button: Removes the LLM suggestion.
        discard_btn = tk.Button(frame, text="Discard (Esc)", bg="#2D2D2D", activebackground="#404040", **btn_style, command=self.discard)
        
        # Pack buttons side-by-side.
        accept_btn.pack(side=tk.LEFT)
        rephrase_btn.pack(side=tk.LEFT)
        discard_btn.pack(side=tk.LEFT)
        
        return frame

    def _bind_keyboard_shortcuts(self):
        """
        Binds session-specific keyboard shortcuts (Tab, Escape, Ctrl+R) to their handlers.

        These bindings are active only when an interactive session is ongoing.
        """
        debug_console.log("Binding session-specific keyboard shortcuts (Tab, Esc, Ctrl+R).", level='DEBUG')
        self.editor.bind("<Tab>", self._handle_accept_key)      # Tab key for accepting.
        self.editor.bind("<Escape>", self._handle_discard_key)  # Escape key for discarding.
        self.editor.bind("<Control-r>", self._handle_rephrase_key) # Ctrl+R for rephrasing.
        self.editor.bind("<Control-R>", self._handle_rephrase_key) # Ctrl+Shift+R (capital R) for rephrasing.

    def _unbind_keyboard_shortcuts(self):
        """
        Unbinds the session-specific keyboard shortcuts.

        This is crucial for cleaning up the session and restoring default editor behavior.
        """
        debug_console.log("Unbinding session-specific keyboard shortcuts.", level='DEBUG')
        self.editor.unbind("<Tab>")
        self.editor.unbind("<Escape>")
        self.editor.unbind("<Control-r>")
        self.editor.unbind("<Control-R>")
        
    def _handle_accept_key(self, event=None):
        """
        Handler for the Tab key press. Accepts the LLM suggestion if not currently generating.
        """
        if not llm_state._is_generating: 
            self.accept()
        return "break" # Prevent default Tab behavior (e.g., indentation).

    def _handle_discard_key(self, event=None):
        """
        Handler for the Escape key press. Discards the LLM suggestion.
        """
        self.discard()
        return "break" # Prevent default Escape behavior.
        
    def _handle_rephrase_key(self, event=None):
        """
        Handler for the Ctrl+R key press. Initiates rephrasing if not currently generating.
        """
        if not llm_state._is_generating: 
            self.rephrase()
        return "break" # Prevent default Ctrl+R behavior.

    def _start_generating_animation(self):
        """
        Starts the visual animation indicating that the LLM is generating text.

        This involves configuring a placeholder tag and initiating a periodic update
        to display animated dots.
        """
        self.is_animating = True
        # Configure a tag for the placeholder text (e.g., "Generating...").
        self.editor.tag_config('llm_placeholder', foreground="#aaa", font=("Segoe UI", 9, "italic"))
        self._animate_dots() # Start the animation loop.

    def _animate_dots(self):
        """
        Updates the animation dots for the generating text placeholder.

        This function is called repeatedly by `editor.after()` to create a simple
        text animation.
        """
        if not self.is_animating: 
            return
        
        dots = '.' * (self.animation_dot_count % 3 + 1) # Cycle through 1, 2, or 3 dots.
        text = f" Generating{dots}"
        
        # Delete the old placeholder text and insert the new one.
        self.editor.delete(self.buttons_end_index, self.text_end_index)
        self.editor.insert(self.buttons_end_index, text, "llm_placeholder")
        
        # Update the end index of the text block.
        self.text_end_index = self.editor.index(f"{self.buttons_end_index} + {len(text)} chars")
        self.animation_dot_count += 1
        
        # Schedule the next animation frame.
        self.editor.after(400, self._animate_dots)

    def _stop_generating_animation(self):
        """
        Stops the generating animation and removes the placeholder text.
        """
        if self.is_animating:
            self.is_animating = False
            # Delete the placeholder text.
            self.editor.delete(self.buttons_end_index, self.text_end_index)
            self.text_end_index = self.buttons_end_index # Reset text end index.

    def handle_chunk(self, chunk):
        """
        Handles a new chunk of text received from the LLM.

        This function inserts the chunk into the editor and accumulates it into
        the `full_response_text`.

        Args:
            chunk (str): A new piece of text generated by the LLM.
        """
        if self.is_animating: 
            self._stop_generating_animation() # Stop animation once real text starts arriving.
        
        self.editor.insert(self.text_end_index, chunk, "llm_generated_text") # Insert chunk with styling.
        self.text_end_index = self.editor.index(f"{self.text_end_index} + {len(chunk)} chars") # Update end index.
        self.full_response_text += chunk # Accumulate the full response.

    def handle_success(self):
        """
        Handles the successful completion of LLM text generation.

        Stops the animation, performs post-processing for completion sessions,
        resets the generation flag, and sets focus back to the editor.
        """
        self._stop_generating_animation()
        if self.is_completion: 
            self._post_process_completion() # Apply completion-specific post-processing.
        
        llm_state._is_generating = False # Reset global generation flag.
        self.editor.focus_set() # Return focus to the editor.
        debug_console.log("LLM stream finished and handled by interactive session.", level='INFO')

    def handle_error(self, error_msg):
        """
        Handles an error during LLM text generation.

        Displays an error message box and destroys the interactive session.

        Args:
            error_msg (str): The error message to display.
        """
        debug_console.log(f"LLM interactive session error: {error_msg}", level='ERROR')
        messagebox.showerror("LLM Error", error_msg)
        self.destroy(delete_text=True) # Destroy session and remove generated text.

    def accept(self):
        """
        Accepts the LLM-generated suggestion.

        This removes the special styling from the generated text, making it regular
        editor content, and then destroys the interactive session.
        """
        if llm_state._is_generating: 
            return # Do not accept if generation is still ongoing.
        
        debug_console.log("User ACCEPTED LLM suggestion.", level='ACTION')
        # Remove the special tag, making the text regular.
        self.editor.tag_remove("llm_generated_text", self.buttons_end_index, self.text_end_index)
        self.destroy(delete_text=False) # Destroy session, but keep the text.
        self.editor.focus_set() # Return focus to the editor.

    def discard(self):
        """
        Discards the LLM-generated suggestion.

        This removes all generated text and destroys the interactive session.
        """
        debug_console.log("User DISCARDED LLM suggestion.", level='ACTION')
        self.destroy(delete_text=True) # Destroy session and remove the text.
        self.editor.focus_set() # Return focus to the editor.

    def rephrase(self):
        """
        Initiates a rephrasing operation on the currently generated LLM text.

        This function imports `llm_rephrase` locally to avoid circular dependencies.
        It passes the generated text and its position to the rephrase module.
        """
        if llm_state._is_generating: 
            return # Do not rephrase if generation is still ongoing.
        
        debug_console.log("User triggered REPHRASE on LLM suggestion.", level='ACTION')
        import llm_rephrase # Local import to avoid circular dependency.
        
        text_to_rephrase = self.full_response_text
        if not text_to_rephrase.strip():
            messagebox.showinfo("Rephrase", "Nothing to rephrase yet. Please wait for text to be generated.")
            return
        
        def on_validate_rephrase_request():
            """
            Callback executed when the rephrase dialog is validated.
            Destroys the current session as rephrasing will create a new one.
            """
            self.destroy(delete_text=True) # Remove the original generated text.
        
        # Schedule the rephrase request to run after a short delay to ensure UI responsiveness.
        self.editor.after(10, lambda: llm_rephrase.request_rephrase_for_text(
            self.editor, text_to_rephrase, self.block_start_index, self.text_end_index,
            on_validate_callback=on_validate_rephrase_request
        ))
        
    def _post_process_completion(self):
        """
        Performs post-processing specific to completion sessions.

        This involves removing any overlapping prefix between the original completion
        phrase and the LLM's generated response to ensure a smooth continuation.
        """
        # Remove any overlapping prefix from the generated text to ensure a clean completion.
        cleaned_text = llm_utils.remove_prefix_overlap_from_completion(self.completion_phrase, self.full_response_text)
        debug_console.log(f"Post-processing completion. Original length: {len(self.full_response_text)}, Cleaned length: {len(cleaned_text)}", level='DEBUG')
        
        text_start_index = self.buttons_end_index
        self.editor.delete(text_start_index, self.text_end_index) # Delete the raw generated text.
        self.editor.insert(text_start_index, cleaned_text, "llm_generated_text") # Insert the cleaned text.
        self.text_end_index = self.editor.index(f"{text_start_index} + {len(cleaned_text)} chars") # Update end index.

    def destroy(self, delete_text):
        """
        Destroys the interactive session, cleaning up UI elements and unbinding shortcuts.

        Args:
            delete_text (bool): If True, the LLM-generated text is removed from the editor.
                                If False, the text remains, but its special styling is removed.
        """
        global _current_session
        debug_console.log(f"Destroying interactive session. Deleting generated text: {delete_text}", level='INFO')
        self._stop_generating_animation() # Stop any ongoing animation.
        self._unbind_keyboard_shortcuts() # Unbind session-specific shortcuts.
        try:
            # Delete the generated text if requested.
            if delete_text: 
                self.editor.delete(self.block_start_index, self.text_end_index)
            else: 
                # If not deleting text, just remove the buttons frame.
                self.editor.delete(self.block_start_index, self.buttons_end_index)
            
            # Destroy the buttons frame widget.
            if self.buttons_frame: 
                self.buttons_frame.destroy()
        except tk.TclError as e:
            debug_console.log(f"Error destroying interactive session UI elements: {e}", level='ERROR')
            pass # Ignore TclError if widgets are already destroyed.
        
        _current_session = None # Clear the global session reference.
        llm_state._is_generating = False # Reset the global generation flag.

def start_new_interactive_session(editor, is_completion=False, completion_phrase=""):
    """
    Starts a new interactive LLM session, replacing any existing one.

    This function ensures that only one interactive session is active at a time.
    It sets the global `_is_generating` flag and returns a dictionary of callbacks
    for managing the session's lifecycle (on_chunk, on_success, on_error).

    Args:
        editor (tk.Text): The Tkinter Text widget where the LLM output will be displayed.
        is_completion (bool, optional): True if this is a completion session, False for generation.
                                        Defaults to False.
        completion_phrase (str, optional): The phrase being completed, relevant for completion sessions.
                                           Defaults to "".

    Returns:
        dict: A dictionary containing callback functions for the LLM generation process:
              - 'on_chunk': Called when a new text chunk is received.
              - 'on_success': Called when the LLM generation completes successfully.
              - 'on_error': Called if an error occurs during generation.
    """
    global _current_session
    if _current_session:
        debug_console.log("Discarding existing interactive session to start a new one.", level='WARNING')
        _current_session.discard() # Discard the old session before starting a new one.
    
    llm_state._is_generating = True # Set the global flag to indicate ongoing generation.
    start_index = editor.index(tk.INSERT) # Get the current cursor position as the start of the new block.
    
    # Create the new InteractiveSession instance.
    _current_session = InteractiveSession(editor, start_index, is_completion, completion_phrase)
    
    # Return a dictionary of callbacks that the LLM generation process can use to interact with the session.
    return {
        'on_chunk': _current_session.handle_chunk,
        'on_success': _current_session.handle_success,
        'on_error': _current_session.handle_error
    }
