import tkinter as tk
import subprocess
import platform

# References to main GUI components
_root = None
_status_bar = None
_temporary_status_active = False
_temporary_status_timer_id = None

def initialize(root_ref, status_bar_ref):
    """Initializes the status bar manager."""
    global _root, _status_bar
    _root = root_ref
    _status_bar = status_bar_ref

def show_temporary_status_message(message, duration_ms=2500):
    """Displays a temporary message on the status bar."""
    global _temporary_status_active, _temporary_status_timer_id

    if not _status_bar or not _root:
        return

    # Cancel any existing temporary message timer
    if _temporary_status_timer_id:
        _root.after_cancel(_temporary_status_timer_id)

    _temporary_status_active = True  # Set flag to indicate temporary message is active
    _status_bar.config(text=message)  # Display the temporary message

    # Schedule the message to be cleared
    _temporary_status_timer_id = _root.after(duration_ms, clear_temporary_status_message)

def clear_temporary_status_message():
    """Clears the temporary message and restores the normal status bar content."""
    global _temporary_status_active, _temporary_status_timer_id
    _temporary_status_active = False # Clear the flag
    _temporary_status_timer_id = None # Reset timer ID
    if _status_bar:
        update_gpu_status() # Immediately refresh with GPU status or default

def update_gpu_status():
    """Updates the GPU status on the status bar."""
    if not _root or not _status_bar:
        return

    try:
        # If a temporary message is active, don't overwrite it with GPU status
        if _temporary_status_active:
            _root.after(300, update_gpu_status) # Reschedule and check again
            return
        # Command to get GPU info (works on systems with nvidia-smi)
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
            encoding="utf-8"
        ).strip()

        name, temp, usage = output.split(", ")
        status_text = f"🎮 GPU: {name}   🌡 {temp}°C   📊 {usage}% used"
    except Exception as e:
        # If GPU status fails or temporary message was just cleared,
        # ensure status_bar is not None before configuring.
        if _status_bar:
            if isinstance(e, (FileNotFoundError, subprocess.CalledProcessError)):
                _status_bar.config(text="⚠️ GPU status not available (nvidia-smi error)")
            else:
                _status_bar.config(text=f"⚠️ Error getting GPU status")
        # Still schedule next update even if this one failed
        _root.after(300, update_gpu_status)
        return
    if _status_bar and not _temporary_status_active: # Check again before setting
        _status_bar.config(text=status_text)
    # Schedule the next update
    _root.after(300, update_gpu_status) # Update every 0.3 seconds