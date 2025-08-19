"""
Centralized dialog utilities for handling unsaved changes across the application.
Provides consistent user experience with clear action options.
"""

from tkinter import messagebox


def show_unsaved_changes_dialog(message, parent, title="Unsaved Changes"):
    """
    Show a standard dialog for unsaved changes with three clear options.
    
    Args:
        message (str): Message to display in the dialog
        parent: Parent window for the dialog
        title (str): Dialog title (default: "Unsaved Changes")
        
    Returns:
        str: "save", "dont_save", or "cancel" (or None if dialog was closed)
    """
    # Use the standard messagebox with three buttons
    result = messagebox.askyesnocancel(title, message, parent=parent)
    
    if result is True:
        return "save"
    elif result is False:
        return "dont_save"
    else:  # result is None (Cancel or closed)
        return "cancel"


def show_unsaved_changes_dialog_multiple_files(file_list, parent):
    """
    Show dialog for multiple unsaved files with clearer wording.
    
    Args:
        file_list (list): List of file names with unsaved changes
        parent: Parent window for the dialog
        
    Returns:
        str: "save", "dont_save", or "cancel" (or None if dialog was closed)
    """
    if len(file_list) == 1:
        message = f"The file '{file_list[0]}' has unsaved changes.\n\nDo you want to save it before closing?"
    else:
        files_text = ", ".join(file_list)
        message = f"The files {files_text} have unsaved changes.\n\nDo you want to save them before closing?"
    
    # Use the standard messagebox with three buttons
    result = messagebox.askyesnocancel("Unsaved Changes", message, parent=parent)
    
    if result is True:
        return "save"
    elif result is False:
        return "dont_save"
    else:  # result is None (Cancel or closed)
        return "cancel"