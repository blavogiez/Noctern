"""
Proofreading service using LLM to detect and suggest corrections for grammar and spelling errors.
Handle document proofreading requests with error navigation interface.
"""
import json
from tkinter import messagebox
from llm import state as llm_state
from llm.dialogs.proofreading import show_proofreading_dialog
from llm import utils as llm_utils
from llm.streaming_service import start_streaming_request
from utils import debug_console

def open_proofreading_dialog():
    """
    Open full-screen proofreading dialog that stays open during processing.
    """
    debug_console.log("Opening document proofreading dialog.", level='ACTION')
    
    if not callable(llm_state._active_editor_getter_func):
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return
        
    editor = llm_state._active_editor_getter_func()
    if not editor:
        messagebox.showerror("LLM Error", "No active editor found.")
        return
        
    # Get selected text or entire document content
    try:
        selected_text = editor.get(editor.index("sel.first"), editor.index("sel.last"))
    except:
        selected_text = ""
    
    if not selected_text:
        selected_text = editor.get("1.0", "end-1c")
    
    if not selected_text.strip():
        messagebox.showwarning("No Content", "No text found to proofread.")
        return

    # Open the main proofreading interface directly
    from llm.dialogs.proofreading import show_proofreading_interface
    show_proofreading_interface(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        editor=editor,
        text_to_check=selected_text
    )