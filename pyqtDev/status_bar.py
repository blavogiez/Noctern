# File: status_bar.py
import subprocess
import platform
from PyQt6 import QtWidgets, QtCore

# References to main GUI components
_root = None
_status_bar = None
_temporary_status_active = False
_temporary_status_timer = None # QTimer instance

def initialize(root_ref, status_bar_ref):
    """Initializes the status bar manager."""
    global _root, _status_bar, _temporary_status_timer
    _root = root_ref
    _status_bar = status_bar_ref

    _temporary_status_timer = QtCore.QTimer()
    _temporary_status_timer.setSingleShot(True)
    _temporary_status_timer.timeout.connect(clear_temporary_status_message)

def show_temporary_status_message(message, duration_ms=2500):
    """Displays a temporary message on the status bar."""
    global _temporary_status_active

    if not _status_bar:
        return

    # Cancel any existing temporary message timer
    if _temporary_status_timer.isActive():
        _temporary_status_timer.stop()

    _temporary_status_active = True
    _status_bar.setText(message)

    _temporary_status_timer.start(duration_ms)

def clear_temporary_status_message():
    """Clears the temporary message and restores the normal status bar content."""
    global _temporary_status_active
    _temporary_status_active = False
    update_gpu_status() # Immediately refresh with GPU status or default

def update_gpu_status():
    """Updates the GPU status on the status bar."""
    if not _status_bar:
        return

    if _temporary_status_active:
        QtCore.QTimer.singleShot(300, update_gpu_status) # Reschedule and check again
        return

    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
            encoding="utf-8"
        ).strip()
        name, temp, usage = output.split(", ")
        status_text = f"🎮 GPU: {name}   🌡 {temp}°C   📊 {usage}% used"
        _status_bar.setText(status_text)
    except Exception as e:
        _status_bar.setText(f"⚠️ GPU status not available ({type(e).__name__})")

    QtCore.QTimer.singleShot(300, update_gpu_status) # Update every 0.3 seconds
