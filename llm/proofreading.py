"""Proofreading entry point."""
from tkinter import messagebox
from llm import state
from llm.dialogs.proofreading import ProofreadingDialog


def open_proofreading_dialog():
    """Open proofreading dialog for active document."""
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
    
    # Launch dialog
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