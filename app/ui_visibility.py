"""
This module contains functions to control the visibility of various UI elements
like the status bar and PDF preview pane.
"""

import ttkbootstrap as ttk
from app import state
from utils import logs_console


def toggle_status_bar():
    """
    Toggle the visibility of the status bar.
    """
    if not state.status_bar_frame:
        # If status bar frame doesn't exist, we need to create it
        from app.status import create_status_bar
        status_bar_frame, status_label, gpu_status_label, metrics_display = create_status_bar(state.root)
        state.status_bar_frame = status_bar_frame
        state.status_label = status_label
        state.gpu_status_label = gpu_status_label
        state.metrics_display = metrics_display
        
        # Update the status with current file info if there's an active tab
        from app import status_utils
        status_utils.update_status_bar_text()
        
        # Start GPU status loop
        from app.status import start_gpu_status_loop
        start_gpu_status_loop(state.gpu_status_label, state.root)
        logs_console.log("Status bar created and shown.", level='INFO')
        # Show temporary feedback to user
        from app import status_utils
        if state.status_label:
            from app.statusbar import show_temporary_status_message
            show_temporary_status_message(
                "Status bar enabled", 2000, 
                state.status_label, state.root, 
                status_utils.update_status_bar_text
            )
    else:
        # Check if the status bar is currently packed
        if state.status_bar_frame.winfo_viewable():
            state.status_bar_frame.pack_forget()
            logs_console.log("Status bar hidden.", level='INFO')
            # Show temporary feedback in debug console since status bar is hidden
            logs_console.log("Status bar disabled by user", level='INFO')
        else:
            state.status_bar_frame.pack(side="bottom", fill="x")
            logs_console.log("Status bar shown.", level='INFO')
            # Update status when showing
            from app import status_utils
            status_utils.update_status_bar_text()
            # Show temporary feedback to user
            if state.status_label:
                from app.statusbar import show_temporary_status_message
                show_temporary_status_message(
                    "Status bar enabled", 2000, 
                    state.status_label, state.root, 
                    status_utils.update_status_bar_text
                )


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
    # Check if PDF preview interface exists
    if not hasattr(state, 'pdf_preview_interface') or not state.pdf_preview_interface:
        # PDF preview is disabled, need to create it
        from app import config as app_config
        from pdf_preview.interface import PDFPreviewInterface
        from app.panes import create_pdf_preview_pane
        
        # Initialize PDF preview interface
        state.pdf_preview_interface = PDFPreviewInterface(state.root, state.get_current_tab)
        
        # Create PDF preview pane
        pdf_preview_content = create_pdf_preview_pane(state.main_pane)
        state.pdf_preview_interface.create_preview_panel(pdf_preview_content)
        
        # Store UI element references
        state.pdf_preview_pane = pdf_preview_content
        state.pdf_preview_parent = state.main_pane
        
        # Add to paned window
        state.main_pane.add(state.pdf_preview_pane.master, weight=2)
        
        # Update configuration
        state._app_config["show_pdf_preview"] = "True"
        app_config.save_config(state._app_config)
        
        logs_console.log("PDF preview created and shown.", level='INFO')
        
        # Load PDF for current tab
        current_tab = state.get_current_tab()
        if current_tab:
            state.pdf_preview_interface.load_existing_pdf_for_tab(current_tab)
        return
    
    if not state.pdf_preview_pane or not state.pdf_preview_parent:
        logs_console.log("PDF preview pane or parent not found.", level='WARNING')
        return
    
    # Check if the PDF preview is currently in the paned window
    try:
        # Get the master frame that contains the pdf_preview_pane
        pdf_preview_master_frame = state.pdf_preview_pane.master
        
        # Check if the master frame is currently added to the parent paned window
        if pdf_preview_master_frame in state.pdf_preview_parent.panes():
            state.pdf_preview_parent.remove(pdf_preview_master_frame)
            
            # Destroy the PDF preview components to save resources
            state.pdf_preview_interface = None
            state.pdf_preview_pane = None
            state.pdf_preview_parent = None
            
            # Update configuration
            from app import config as app_config
            state._app_config["show_pdf_preview"] = "False"
            app_config.save_config(state._app_config)
            
            logs_console.log("PDF preview hidden and destroyed.", level='INFO')
        else:
            # Add it back to the paned window with appropriate weight
            state.pdf_preview_parent.add(pdf_preview_master_frame, weight=2)
            logs_console.log("PDF preview shown.", level='INFO')
    except Exception as e:
        logs_console.log(f"Error toggling PDF preview: {e}", level='ERROR')


def is_pdf_preview_visible():
    """
    Check if the PDF preview is currently visible.
    
    Returns:
        bool: True if visible, False otherwise
    """
    # Check if PDF preview interface exists
    if not hasattr(state, 'pdf_preview_interface') or not state.pdf_preview_interface:
        return False
        
    if not state.pdf_preview_pane or not state.pdf_preview_parent:
        return False
    try:
        # Get the master frame that contains the pdf_preview_pane
        pdf_preview_master_frame = state.pdf_preview_pane.master
        return pdf_preview_master_frame in state.pdf_preview_parent.panes()
    except:
        return False