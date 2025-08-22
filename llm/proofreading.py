"""
Document proofreading entry point and integration with the application.
Provides simple interface to launch professional proofreading sessions.
"""
from tkinter import messagebox
from llm import state as llm_state
from llm.proofreading_service import get_proofreading_service
from llm.dialogs.proofreading import ProofreadingDialog
from utils import debug_console


def open_proofreading_dialog():
    """
    Launch professional document proofreading interface.
    
    This is the main entry point for proofreading functionality.
    Creates a maximized, user-friendly interface for AI-powered text correction.
    """
    debug_console.log("Launching professional document proofreading", level='ACTION')
    
    # Validate LLM service is ready
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("Service Error", "AI service not initialized. Please restart the application.")
        return
        
    editor = llm_state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("Editor Error", "No active document found. Please open a document first.")
        return
    
    # Get text to proofread (selected text or entire document)
    text_to_check = _get_text_to_proofread(editor)
    if not text_to_check:
        messagebox.showwarning("No Content", 
            "No text found to proofread. Please write some content or select text to analyze.")
        return
    
    # Launch professional proofreading interface
    try:
        proofreading_dialog = ProofreadingDialog(
            parent=llm_state._root_window,
            theme_getter=llm_state._theme_setting_getter_func,
            editor=editor,
            initial_text=text_to_check
        )
        proofreading_dialog.show()
        
    except Exception as e:
        debug_console.log(f"Error launching proofreading interface: {e}", level='ERROR')
        messagebox.showerror("Interface Error", 
            f"Failed to open proofreading interface: {str(e)}")


def _get_text_to_proofread(editor) -> str:
    """
    Extract text to proofread from editor.
    
    Priority:
    1. Selected text (if any)
    2. Entire document content
    
    Returns:
        str: Text to proofread, or empty string if no content
    """
    try:
        # Try to get selected text first
        selected_text = editor.get(editor.index("sel.first"), editor.index("sel.last"))
        if selected_text.strip():
            debug_console.log(f"Using selected text for proofreading: {len(selected_text)} chars", level='INFO')
            return selected_text
    except:
        # No selection, use entire document
        pass
    
    # Get entire document content
    full_text = editor.get("1.0", "end-1c")
    if full_text.strip():
        debug_console.log(f"Using entire document for proofreading: {len(full_text)} chars", level='INFO')
        return full_text
    
    return ""