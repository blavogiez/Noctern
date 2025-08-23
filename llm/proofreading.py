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
    Extract text to proofread from editor, filtering out LaTeX comment lines.
    
    Priority:
    1. Selected text (if any)
    2. Entire document content
    
    Comment lines (starting with %) are filtered out to avoid proofreading 
    LaTeX comments which should not be modified.
    
    Returns:
        str: Text to proofread, or empty string if no content
    """
    try:
        # Try to get selected text first
        selected_text = editor.get(editor.index("sel.first"), editor.index("sel.last"))
        if selected_text.strip():
            filtered_text = _filter_comment_lines(selected_text)
            debug_console.log(f"Using selected text for proofreading: {len(filtered_text)} chars (filtered from {len(selected_text)})", level='INFO')
            return filtered_text
    except:
        # No selection, use entire document
        pass
    
    # Get entire document content
    full_text = editor.get("1.0", "end-1c")
    if full_text.strip():
        filtered_text = _filter_comment_lines(full_text)
        debug_console.log(f"Using entire document for proofreading: {len(filtered_text)} chars (filtered from {len(full_text)})", level='INFO')
        return filtered_text
    
    return ""


def _filter_comment_lines(text: str) -> str:
    """
    Filter out LaTeX comment lines from the text.
    
    Removes lines that start with % (LaTeX comments), while preserving
    the structure of the document by keeping empty lines.
    
    Args:
        text (str): Original text content
        
    Returns:
        str: Text with comment lines removed
    """
    if not text:
        return text
    
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Check if line starts with % (after removing leading whitespace)
        stripped_line = line.lstrip()
        if stripped_line.startswith('%'):
            # Replace comment line with empty line to preserve document structure
            filtered_lines.append('')
        else:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)