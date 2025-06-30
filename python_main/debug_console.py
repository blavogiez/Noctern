import tkinter as tk
from tkinter.scrolledtext import ScrolledText

_console_window = None
_console_text = None

def show_console(root=None):
    pass  # No-op for log-to-stdout mode

def log(msg, level="info", root=None):
    # Print to standard output with level prefix
    print(f"[{level.upper()}] {msg}")

def clear():
    pass  # No-op for log-to-stdout mode
    _console_window.title("Debug Console")
    _console_window.geometry("700x300")
    _console_window.protocol("WM_DELETE_WINDOW", lambda: _console_window.withdraw())
    _console_text = ScrolledText(_console_window, state="disabled", font=("Consolas", 10))
    _console_text.pack(fill="both", expand=True)
    _console_window.lift()

def log(msg, level="info", root=None):
    global _console_window, _console_text
    if _console_window is None or not (_console_window.winfo_exists() if _console_window else False):
        show_console(root)
    _console_text.config(state="normal")
    tag = level.lower()
    if tag not in _console_text.tag_names():
        color = {"info": "#222", "debug": "#0078d4", "warn": "#e6a700", "error": "#d40000"}.get(tag, "#222")
        _console_text.tag_configure(tag, foreground=color)
    _console_text.insert("end", f"[{level.upper()}] {msg}\n", tag)
    _console_text.see("end")
    _console_text.config(state="disabled")

def clear():
    global _console_text
    if _console_text:
        _console_text.config(state="normal")
        _console_text.delete("1.0", "end")
        _console_text.config(state="disabled")
