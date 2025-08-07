import tkinter as tk
from tkinter import ttk

class ErrorPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.title = ttk.Label(self, text="Pre-compilation Errors")
        self.title.pack(side="top", fill="x", padx=5, pady=5)
        self.listbox = tk.Listbox(self)
        self.listbox.pack(side="top", fill="both", expand=True)

    def update_errors(self, errors):
        self.listbox.delete(0, tk.END)
        for error in errors:
            self.listbox.insert(tk.END, error)
