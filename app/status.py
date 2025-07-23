"""
This module is responsible for creating and managing the application's status bar.
It includes functionalities for displaying general status messages, word count,
and real-time GPU performance metrics (if an NVIDIA GPU is detected).
"""

from tkinter import ttk
import tkinter as tk
import subprocess
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

"""
This module is responsible for creating and managing the status bar
of the AutomaTeX application.
"""

import ttkbootstrap as ttk
import GPUtil
from app import main_window as mw

def create_status_bar(root):
    """
    Creates the status bar frame and its labels.

    Args:
        root (tk.Tk): The main application window.

    Returns:
        tuple: A tuple containing the status bar frame (ttk.Frame),
               the main status label (ttk.Label), and the GPU status label (ttk.Label).
    """
    status_bar_frame = ttk.Frame(root, style='primary.TFrame')
    status_bar_frame.pack(side="bottom", fill="x", padx=5, pady=(0, 5))

    status_label = ttk.Label(status_bar_frame, text="Ready", anchor="w", style='primary.inverse.TLabel')
    status_label.pack(side="left", padx=10)

    gpu_status_label = ttk.Label(status_bar_frame, text="", anchor="e", style='primary.inverse.TLabel')
    gpu_status_label.pack(side="right", padx=10)
    
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
    except Exception:
        gpu_label.config(text="GPU: Error")

def start_gpu_status_loop(gpu_label, root):
    """
    Starts the periodic update of the GPU status.

    Args:
        gpu_label (ttk.Label): The label to update.
        root (tk.Tk): The main application window.
    """
    update_gpu_status(gpu_label)
    root.after(5000, lambda: start_gpu_status_loop(gpu_label, root))

