import tkinter as tk
from tkinter import ttk
import datetime

class DebugConsole:
    def __init__(self):
        self.console_window = None
        self.text_widget = None
        self.levels = {
            'DEBUG': '#9E9E9E',   # Grey
            'INFO': '#FFFFFF',    # White
            'ACTION': '#81D4FA',  # Light Blue
            'SUCCESS': '#A5D6A7', # Green
            'WARNING': '#FFD54F', # Amber
            'ERROR': '#EF9A9A',   # Red
            'CONFIG': '#CE93D8',  # Purple
        }

    def initialize(self, root):
        self.root = root

    def show_console(self):
        if self.console_window and self.console_window.winfo_exists():
            self.console_window.lift()
            return

        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("Debug Console")
        self.console_window.geometry("900x400")
        self.console_window.configure(bg="#1e1e1e")

        self.text_widget = tk.Text(self.console_window, wrap="word", bg="#1e1e1e", fg="#d4d4d4",
                                   font=("Consolas", 10), relief=tk.FLAT, borderwidth=0)
        self.text_widget.pack(expand=True, fill="both", padx=5, pady=5)

        for level, color in self.levels.items():
            self.text_widget.tag_configure(level, foreground=color)

        self.console_window.protocol("WM_DELETE_WINDOW", self.hide_console)

    def hide_console(self):
        if self.console_window:
            self.console_window.destroy()
            self.console_window = None

    def log(self, message, level='INFO'):
        if not self.console_window or not self.text_widget or not self.console_window.winfo_exists():
            print(f"[{level}] {message}") # Fallback to stdout
            return

        # Timestamp generation is now centralized here
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Format the final log line
        log_line = f"{ts} [{level.upper()}] {message}\n"

        self.text_widget.config(state="normal")
        self.text_widget.insert(tk.END, log_line, level)
        self.text_widget.config(state="disabled")
        self.text_widget.see(tk.END)

# Create a single global instance
_console_instance = DebugConsole()

# Expose the public methods
initialize = _console_instance.initialize
show_console = _console_instance.show_console
hide_console = _console_instance.hide_console
log = _console_instance.log