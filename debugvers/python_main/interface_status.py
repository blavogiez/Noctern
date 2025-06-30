from tkinter import ttk
import subprocess
import debug_console

def create_status_bar(root):
    status_bar = ttk.Label(root, text="⏳ Initializing...", anchor="w", relief="flat", padding=(5, 3))
    status_bar.pack(side="bottom", fill="x")
    return status_bar

def start_gpu_status_loop(status_bar, root):
    def update_gpu_status():
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
                encoding="utf-8"
            ).strip()
            name, temp, usage = output.split(", ")
            status_text = f"🎮 GPU: {name}   🌡 {temp}°C   📊 {usage}% used"
        except Exception:
            status_text = "⚠️ GPU status not available"
        if status_bar and 'winfo_exists' in dir(status_bar) and status_bar.winfo_exists():
            # Check if the message is a temporary one before overwriting
            if not getattr(interface_statusbar, '_temporary_status_active', False):
                 status_bar.config(text=status_text)
        if root and 'winfo_exists' in dir(root) and root.winfo_exists():
            root.after(2000, update_gpu_status) # Update every 2 seconds
    
    debug_console.log("Starting GPU status loop.", level='INFO')
    update_gpu_status()