import tkinter as tk
import subprocess
import platform

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

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
        gpu_status = f"🎮 GPU: {name}   🌡 {temp}°C   📊 {usage}% used"
    except Exception as e:
        if _status_bar:
            if isinstance(e, (FileNotFoundError, subprocess.CalledProcessError)):
                gpu_status = "⚠️ GPU status not available (nvidia-smi error)"
            else:
                gpu_status = f"⚠️ Error getting GPU status"
        else:
            gpu_status = ""
    # --- Memory and CPU usage ---
    mem_cpu_status = ""
    if _PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            mem_mb = process.memory_info().rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=0.1)
            mem_cpu_status = f"   🧠 RAM: {mem_mb:.1f} MB   🖥 CPU: {cpu_percent:.1f}%"
        except Exception:
            mem_cpu_status = "   🧠 RAM: N/A   🖥 CPU: N/A"
    else:
        mem_cpu_status = "   🧠 RAM: N/A   🖥 CPU: N/A"

    status_text = gpu_status + mem_cpu_status
    if _status_bar and not _temporary_status_active:
        _status_bar.config(text=status_text)
    # Schedule the next update
    _root.after(300, update_gpu_status) # Update every 0.3 seconds