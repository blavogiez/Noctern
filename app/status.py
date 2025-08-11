"""
This module is responsible for creating and managing the application's status bar.
It includes functionalities for displaying general status messages, word count,
and real-time GPU performance metrics (if an NVIDIA GPU is detected).
"""

import ttkbootstrap as ttk
import GPUtil
from utils import debug_console

def create_status_bar(root):
    """
    Creates the main status bar frame and its constituent labels.

    The status bar is divided into two main sections: one for general status messages
    (like word count or temporary notifications) and another for displaying GPU status.

    Args:
        root (tk.Tk): The root Tkinter window to which the status bar will be attached.

    Returns:
        tuple: A tuple containing:
            - status_bar_frame (ttk.Frame): The main frame for the status bar.
            - status_label (ttk.Label): The label for general status messages and word count.
            - gpu_status_label (ttk.Label): The label for displaying GPU performance metrics.
    """
    # Create the main frame for the status bar, packed at the bottom of the root window.
    status_bar_frame = ttk.Frame(root, padding=(5, 3))
    status_bar_frame.pack(side="bottom", fill="x")

    # Label for general status messages and word count. It expands to fill available space.
    status_label = ttk.Label(status_bar_frame, text="...", anchor="w")
    status_label.pack(side="left", fill="x", expand=True)

    # A vertical separator to visually divide the general status from the GPU status.
    separator = ttk.Separator(status_bar_frame, orient='vertical')
    separator.pack(side="left", fill='y', padx=10)

    # Label specifically for GPU status, aligned to the right.
    gpu_status_label = ttk.Label(status_bar_frame, text="GPU: N/A", anchor="e")
    gpu_status_label.pack(side="right")
    
    return status_bar_frame, status_label, gpu_status_label

def update_gpu_status(gpu_label):
    """
    Updates the GPU status label with the current GPU usage and memory.

    Args:
        gpu_label (ttk.Label): The label widget to update.
    """
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            gpu_info = f"GPU: {gpu.load*100:.1f}% | Mem: {gpu.memoryUsed}/{gpu.memoryTotal} MB"
            gpu_label.config(text=gpu_info)
        else:
            gpu_label.config(text="GPU: N/A")
    except Exception as e:
        # Log the error but don't crash the status loop
        debug_console.log(f"Could not update GPU status: {e}", level='WARNING')
        gpu_label.config(text="GPU: Error")

def start_gpu_status_loop(gpu_label, root):
    """
    Starts the periodic update of the GPU status.

    Args:
        gpu_label (ttk.Label): The label to update.
        root (tk.Tk): The main application window.
    """
    # Check if the widget still exists before proceeding
    if gpu_label and gpu_label.winfo_exists():
        update_gpu_status(gpu_label)
        root.after(5000, lambda: start_gpu_status_loop(gpu_label, root))