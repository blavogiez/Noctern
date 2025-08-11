"""
This module contains functions to control the visibility of various UI elements
like the status bar and PDF preview pane.
"""

import ttkbootstrap as ttk
from app import state
from utils import debug_console


def toggle_status_bar():
    """
    Toggle the visibility of the status bar.
    """
    if not state.status_bar_frame:
        # If status bar frame doesn't exist, we need to create it
        from app.status import create_status_bar
        status_bar_frame, status_label, gpu_status_label = create_status_bar(state.root)
        state.status_bar_frame = status_bar_frame
        state.status_label = status_label
        state.gpu_status_label = gpu_status_label
        
        # Update the status with current file info if there's an active tab
        from app import status_utils
        status_utils.update_status_bar_text()
        
        # Start GPU status loop
        from app.status import start_gpu_status_loop
        start_gpu_status_loop(state.gpu_status_label, state.root)
        debug_console.log("Status bar created and shown.", level='INFO')
    else:
        # Check if the status bar is currently packed
        if state.status_bar_frame.winfo_viewable():
            state.status_bar_frame.pack_forget()
            debug_console.log("Status bar hidden.", level='INFO')
        else:
            state.status_bar_frame.pack(side="bottom", fill="x")
            debug_console.log("Status bar shown.", level='INFO')
            # Update status when showing
            from app import status_utils
            status_utils.update_status_bar_text()


def is_status_bar_visible():
    """
    Check if the status bar is currently visible.
    
    Returns:
        bool: True if visible, False otherwise
    """
    if not state.status_bar_frame:
        return False
    try:
        return state.status_bar_frame.winfo_viewable()
    except:
        return False


def toggle_pdf_preview():
    """
    Toggle the visibility of the PDF preview pane.
    """
    if not state.pdf_preview_pane or not state.pdf_preview_parent:
        debug_console.log("PDF preview pane or parent not found.", level='WARNING')
        return
    
    # Check if the PDF preview is currently in the paned window
    try:
        # Get the master frame that contains the pdf_preview_pane
        pdf_preview_master_frame = state.pdf_preview_pane.master
        
        if str(pdf_preview_master_frame.master) == str(state.pdf_preview_parent):
            state.pdf_preview_parent.remove(pdf_preview_master_frame)
            debug_console.log("PDF preview hidden.", level='INFO')
        else:
            # Add it back to the paned window with appropriate weight
            state.pdf_preview_parent.add(pdf_preview_master_frame, weight=2)
            debug_console.log("PDF preview shown.", level='INFO')
    except Exception as e:
        debug_console.log(f"Error toggling PDF preview: {e}", level='ERROR')


def is_pdf_preview_visible():
    """
    Check if the PDF preview is currently visible.
    
    Returns:
        bool: True if visible, False otherwise
    """
    if not state.pdf_preview_pane or not state.pdf_preview_parent:
        return False
    try:
        # Get the master frame that contains the pdf_preview_pane
        pdf_preview_master_frame = state.pdf_preview_pane.master
        return str(pdf_preview_master_frame.master) == str(state.pdf_preview_parent)
    except:
        return False