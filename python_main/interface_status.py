from tkinter import ttk
import subprocess

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
        if status_bar:
            status_bar.config(text=status_text)
        root.after(300, update_gpu_status)
    update_gpu_status()
