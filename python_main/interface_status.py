"""
This module is responsible for creating and managing the application's status bar.
It includes functionalities for displaying general status messages, word count,
and real-time GPU performance metrics (if an NVIDIA GPU is detected).
"""

from tkinter import ttk
import tkinter as tk
import subprocess
import debug_console
import interface_statusbar

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

def start_gpu_status_loop(gpu_status_label, root):
    """
    Initiates a periodic loop to fetch and update GPU performance information.

    This function attempts to query NVIDIA GPU metrics using `nvidia-smi`.
    If successful, it updates the `gpu_status_label` with the GPU name, temperature,
    and utilization. If `nvidia-smi` is not found or an error occurs, it displays
    "GPU: N/A". The update occurs every 2 seconds.

    Args:
        gpu_status_label (ttk.Label): The label widget where GPU status will be displayed.
        root (tk.Tk): The root Tkinter window, used for scheduling the update loop.
    """
    def update_gpu_status():
        """
        Internal function to fetch and update the GPU status.
        This function is called repeatedly by `root.after`.
        """
        # Stop the loop if the root window has been closed.
        if not root or not root.winfo_exists():
            debug_console.log("GPU status loop stopping: Root window no longer exists.", level='DEBUG')
            return 
            
        status_text = "GPU: N/A" # Default status text.
        try:
            # Execute nvidia-smi command to get GPU name, temperature, and utilization.
            # Output format: CSV, no header, no units.
            command_output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
                encoding="utf-8",
                stderr=subprocess.DEVNULL # Suppress error messages from nvidia-smi if it fails.
            ).strip()
            
            # Parse the comma-separated output.
            gpu_name, temperature, utilization = command_output.split(", ")
            status_text = f"🎮 {gpu_name}   🌡 {temperature}°C   📊 {utilization}%"
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
            # Log errors if nvidia-smi fails or output parsing fails.
            debug_console.log(f"Failed to get GPU status (nvidia-smi not found or error): {e}", level='DEBUG')
            status_text = "GPU: N/A"
        
        # Update the dedicated GPU label if it still exists and is visible.
        if gpu_status_label and gpu_status_label.winfo_exists():
            gpu_status_label.config(text=status_text)
        
        # Schedule the next update after 2 seconds.
        root.after(2000, update_gpu_status)
    
    debug_console.log("Starting periodic GPU status update loop.", level='INFO')
    update_gpu_status() # Call the function once to start the loop immediately.
