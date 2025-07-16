"""
This module manages the display of temporary status messages in the application's status bar.
It provides functions to show a message for a specified duration and to clear it,
ensuring that the status bar can revert to its default display (e.g., word count).
"""

# Global state variables to manage the lifecycle of temporary status messages.
_temporary_status_active = False  # Flag indicating if a temporary message is currently displayed.
_temporary_status_timer_id = None # Stores the ID of the `root.after` call for clearing the message.

def show_temporary_status_message(message, duration_ms, status_label, root, clear_function):
    """
    Displays a temporary message in the provided status label for a specified duration.

    If another temporary message is already active, its timer is cancelled before
    displaying the new message. After the `duration_ms`, the `clear_function` is called.

    Args:
        message (str): The text message to display in the status bar.
        duration_ms (int): The duration in milliseconds for which the message should be displayed.
        status_label (tk.Label): The Tkinter Label widget in the status bar to update.
        root (tk.Tk): The main Tkinter application window, used for scheduling the timer.
        clear_function (callable): A callback function to execute when the temporary message
                                   duration expires. This function is responsible for clearing
                                   the temporary message and restoring the default status.
    """
    global _temporary_status_timer_id
    # Basic validation to ensure necessary widgets are provided.
    if not status_label or not root:
        # In a real application, you might log this or raise an error.
        return
    
    # Cancel any previously scheduled timer for a temporary message.
    # This ensures that only the latest message is displayed and cleared correctly.
    if _temporary_status_timer_id:
        root.after_cancel(_temporary_status_timer_id)
        
    # Update the status label with the new temporary message.
    status_label.config(text=message)
    
    # Schedule the `clear_function` to be called after `duration_ms` milliseconds.
    _temporary_status_timer_id = root.after(duration_ms, clear_function)

def clear_temporary_status_message():
    """
    Resets the internal state related to temporary status messages.

    This function is typically called by the `clear_function` passed to
    `show_temporary_status_message` when the timer expires. It clears the
    timer ID, indicating that no temporary message is currently scheduled.
    The actual restoration of the status bar's default text (e.g., word count)
    is handled by the caller of this function (e.g., in `interface.py`).
    """
    global _temporary_status_timer_id
    _temporary_status_timer_id = None # Clear the timer ID.
    # The `_temporary_status_active` flag is managed externally (e.g., in `interface.py`)
    # to ensure proper synchronization with the overall application state.
