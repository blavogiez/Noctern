import tkinter as tk
from tkinter import ttk

class ErrorPanel(ttk.Frame):
    def __init__(self, parent, on_goto_line=None):
        super().__init__(parent)
        self.on_goto_line = on_goto_line
        self.errors = []

        # Create a frame for the title with tab-like styling
        title_frame = ttk.Frame(self)
        title_frame.pack(side="top", fill="x", padx=2, pady=(2, 2))
        
        self.title = ttk.Label(
            title_frame, 
            text="Pre-compilation Errors",
            style="Title.TLabel",
            anchor="w"  # Align left
        )
        self.title.pack(side="top", fill="x", ipady=3, padx=(6, 6))  # Adjusted padding to match tabs
        
        # Create a frame for the listbox to ensure proper layout
        listbox_frame = ttk.Frame(self)
        listbox_frame.pack(side="top", fill="both", expand=True, padx=2, pady=2)
        
        self.listbox = tk.Listbox(listbox_frame)
        self.listbox.pack(side="top", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_error_select)

    def update_errors(self, errors):
        self.errors = errors
        self.listbox.delete(0, tk.END)
        for error in self.errors:
            self.listbox.insert(tk.END, f"L{error['line']}: {error['error']}")
        # Force the update of the listbox
        self.listbox.update_idletasks()

    def on_error_select(self, event):
        if not self.on_goto_line:
            return
            
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        selected_index = selected_indices[0]
        if 0 <= selected_index < len(self.errors):
            error = self.errors[selected_index]
            self.on_goto_line(error['line'])