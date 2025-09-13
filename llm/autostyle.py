"""
Smart Style feature for text styling and rephrasing.
Handle user interaction through callbacks and coordinate with streaming service for text enhancement.
UI integration through callbacks provided by app layer.
"""
import tkinter as tk
from tkinter import messagebox

from llm import state as llm_state
from llm.interactive import start_new_interactive_session
from llm.streaming_service import start_streaming_request
from utils import logs_console

def prepare_autostyle(panel_callback=None):
    """
    Prepare autostyle feature - pure business logic.
    
    Args:
        panel_callback: Callback to show the UI panel
        
    Main entry point for autostyle feature.
    Retrieve active editor, prompt for intensity, and initiate styling.
    """
    # Get active editor
    if not llm_state._active_editor_getter_func:
        messagebox.showerror("LLM Error", "LLM service not fully initialized.")
        return
    editor = llm_state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("LLM Error", "No active editor found.")
        return

    # Get selected text
    try:
        selection_indices = editor.tag_ranges("sel")
        if not selection_indices:
            messagebox.showinfo("Smart Style", "Please select some text to style.")
            return
        selected_text = editor.get(selection_indices[0], selection_indices[1])
        if not selected_text.strip():
            messagebox.showinfo("Smart Style", "The selected text is empty.")
            return
    except tk.TclError:
        messagebox.showinfo("Smart Style", "Please select some text to style.")
        return

    def on_intensity_confirm(intensity_value):
        """Handle intensity confirmation from panel."""
        # Continue with styling process
        _perform_styling(editor, selected_text, selection_indices, intensity_value)
    
    def on_intensity_cancel():
        """Handle intensity cancellation from panel."""
        logs_console.log("Smart Styling cancelled by user.", level='INFO')
    
    # Call UI callback if provided
    if panel_callback:
        panel_callback(
            last_intensity=getattr(llm_state, 'last_style_intensity', 5),
            on_confirm_callback=on_intensity_confirm,
            on_cancel_callback=on_intensity_cancel
        )


def _perform_styling(editor, selected_text, selection_indices, intensity):
    """Perform the actual styling operation."""
    # Save the intensity for next time
    llm_state.last_style_intensity = intensity
    
    # Check for ongoing generation and prepare prompt
    if llm_state.is_generating():
        messagebox.showinfo("LLM Busy", "LLM is currently generating. Please wait.")
        return

    prompt_template = llm_state.get_styling_prompt()
    if not prompt_template:
        messagebox.showerror("LLM Error", "Styling prompt template is not configured. Please check the global or document-specific prompt settings.")
        return
        
    full_prompt = prompt_template.format(text=selected_text, intensity=f"{intensity}/10")
    logs_console.log(f"LLM Styling Request - Intensity: {intensity}/10", level='INFO')

    # 5. Start interactive session and define callbacks
    session_callbacks = start_new_interactive_session(
        editor,
        is_styling=True,
        selection_indices=selection_indices
    )

    # Ensure consistent cleaning like generation flow
    from llm import utils as llm_utils
    accumulated_text = ""

    def on_chunk(chunk: str):
        nonlocal accumulated_text
        cleaned = llm_utils.normalize_text_content(chunk)
        accumulated_text += cleaned
        session_callbacks['on_chunk'](cleaned)

    def on_success(final_text: str):
        final_cleaned = llm_utils.prepare_final_response(accumulated_text, final_text)
        session_callbacks['on_success'](final_cleaned)

    # Call streaming service with rephrase settings for styling
    start_streaming_request(
        editor=editor,
        prompt=full_prompt,
        model_name=llm_state.model_style,
        on_chunk=on_chunk,
        on_success=on_success,
        on_error=session_callbacks['on_error'],
        task_type="rephrase"  # Use rephrase profile for styling (similar focused rewriting)
    )


# Backward compatibility wrapper
def autostyle_selection():
    """Legacy function name for backward compatibility."""
    prepare_autostyle()
