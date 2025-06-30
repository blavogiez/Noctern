# interface_status.py

from tkinter import ttk
import tkinter as tk
import subprocess
import debug_console
import interface_statusbar

def create_status_bar(root):
    """
    Creates the status bar frame with dedicated labels for word count/status and GPU.
    Returns the main frame and the two labels.
    """
    status_bar_frame = ttk.Frame(root, padding=(5, 3))
    status_bar_frame.pack(side="bottom", fill="x")

    # Label for general status messages and word count
    status_label = ttk.Label(status_bar_frame, text="...", anchor="w")
    status_label.pack(side="left", fill="x", expand=True)

    # Separator
    separator = ttk.Separator(status_bar_frame, orient='vertical')
    separator.pack(side="left", fill='y', padx=10)

    # Label specifically for GPU status
    gpu_status_label = ttk.Label(status_bar_frame, text="GPU: N/A", anchor="e")
    gpu_status_label.pack(side="right")
    
    return status_bar_frame, status_label, gpu_status_label

def start_gpu_status_loop(gpu_status_label, root):
    """
    Starts a loop to periodically update the GPU status in its dedicated label.
    """
    def update_gpu_status():
        if not root or not root.winfo_exists():
            return # Stop loop if root window is closed
            
        try:
            # Command to get GPU name, temperature, and utilization from nvidia-smi
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
                encoding="utf-8",
                stderr=subprocess.DEVNULL # Hide errors if command fails
            ).strip()
            name, temp, usage = output.split(", ")
            status_text = f"🎮 {name}   🌡 {temp}°C   📊 {usage}%"
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            status_text = "GPU: N/A"
        
        # Update the dedicated GPU label if it still exists
        if gpu_status_label and gpu_status_label.winfo_exists():
            gpu_status_label.config(text=status_text)
        
        # Schedule the next update
        root.after(2000, update_gpu_status) # Update every 2 seconds
    
    debug_console.log("Starting GPU status loop.", level='INFO')
    update_gpu_status() # Start the first update