"""
Document proofreading entry point and integration with the application.
Provides simple interface to launch professional proofreading sessions.
"""
"""Proofreading module entry point."""
from tkinter import messagebox
from llm import state
from llm.proofreading_service import ProofreadingService
from llm.dialogs.proofreading import ProofreadingDialog


def open_proofreading_dialog():
    """Open proofreading dialog for active document."""
    if not callable(state._active_editor_getter_func):
        messagebox.showerror("Error", "AI service not initialized.")
        return
        
    editor = state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("Error", "No active document found.")
        return
    
    text_to_check = get_text_to_proofread(editor)
    if not text_to_check:
        messagebox.showwarning("No Content", "No text found to proofread.")
        return
    
    try:
        dialog = ProofreadingDialog(
            parent=state._root_window,
            theme_getter=state._theme_setting_getter_func,
            editor=editor,
            initial_text=text_to_check
        )
        dialog.show()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open proofreading interface: {str(e)}")


def get_text_to_proofread(editor):
    """Get selected text or full document content for proofreading."""
    try:
        selected_text = editor.get(editor.index("sel.first"), editor.index("sel.last"))
        if selected_text.strip():
            return filter_comment_lines(selected_text)
    except:
        pass
    
    full_text = editor.get("1.0", "end-1c")
    if full_text.strip():
        return filter_comment_lines(full_text)
    
    return ""


def filter_comment_lines(text):
    """Remove LaTeX comment lines starting with %."""
    if not text:
        return text
    
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        if line.lstrip().startswith('%'):
            filtered_lines.append('')
        else:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)