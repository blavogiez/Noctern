"""
Proofreading module - Production-ready text analysis.
"""

from .service import ProofreadingService, ProofreadingSession
from .core import ProofreadingError

# Public API
_service = None

def get_proofreading_service():
    """Get singleton proofreading service."""
    global _service
    if _service is None:
        _service = ProofreadingService()
    return _service

def analyze_text(text: str, instructions: str = ""):
    """Simple API for text analysis."""
    service = get_proofreading_service()
    session = service.start_session(text, instructions)
    service.analyze_text(session)
    return session.errors

# Backward compatibility functions
def prepare_proofreading(panel_callback=None):
    """Prepare proofreading - backward compatibility."""
    from tkinter import messagebox
    from llm import state
    
    # Check services ready
    if not callable(state._active_editor_getter_func):
        messagebox.showerror("Error", "AI service not initialized.")
        return
        
    editor = state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("Error", "No active document found.")
        return
    
    # Get text to analyze
    text_to_check = get_text_for_analysis(editor)
    if not text_to_check:
        messagebox.showwarning("No Content", "No text found to proofread.")
        return
    
    # Call UI callback if provided
    if panel_callback:
        try:
            panel_callback(editor, text_to_check)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open proofreading interface: {str(e)}")

def get_text_for_analysis(editor):
    """Get text from editor (selected or full document)."""
    try:
        # Try selected text first
        selected_text = editor.get(editor.index("sel.first"), editor.index("sel.last"))
        if selected_text.strip():
            return filter_latex_comments(selected_text)
    except:
        pass
    
    # Fall back to full document
    full_text = editor.get("1.0", "end-1c")
    if full_text.strip():
        return filter_latex_comments(full_text)
    
    return ""

def filter_latex_comments(text):
    """Remove LaTeX comment lines (starting with %)."""
    if not text:
        return text
    
    lines = []
    for line in text.split('\n'):
        if line.lstrip().startswith('%'):
            lines.append('')  # Keep structure, remove content
        else:
            lines.append(line)
    
    return '\n'.join(lines)