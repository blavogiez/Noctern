# interface_statusbar.py

# Global state to manage temporary messages
_temporary_status_active = False
_temporary_status_timer_id = None

def show_temporary_status_message(message, duration_ms, status_label, root, clear_func):
    """
    Displays a temporary message in the main status label.
    
    Args:
        message (str): The message to display.
        duration_ms (int): How long to display the message in milliseconds.
        status_label (tk.Label): The widget to update.
        root (tk.Tk): The main application window for scheduling.
        clear_func (function): The function to call when the timer expires.
    """
    global _temporary_status_timer_id
    if not status_label or not root:
        return
    
    # Cancel any previous temporary message timer
    if _temporary_status_timer_id:
        root.after_cancel(_temporary_status_timer_id)
        
    status_label.config(text=message)
    _temporary_status_timer_id = root.after(duration_ms, clear_func)

def clear_temporary_status_message():
    """
    Resets the state of the temporary message system.
    The actual restoration of the status bar text (e.g., word count)
    is now handled by the caller of this function.
    """
    global _temporary_status_timer_id
    _temporary_status_timer_id = None
    # The global flag `_temporary_status_active` is reset in interface.py
    # to ensure correct state management.