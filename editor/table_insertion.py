"""
Simple LaTeX table insertion with snippet navigation support.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils import debug_console


class TableGenerator:
    """Simple LaTeX table code generator with placeholder navigation."""
    
    @staticmethod
    def generate(rows, cols, has_header=True, alignment='c', caption='', label=''):
        """Generate LaTeX table with navigation placeholders."""
        debug_console.log(f"Generating {rows}x{cols} table", level='INFO')
        
        # Build column spec
        col_spec = alignment * cols
        lines = []
        
        # Table environment if needed
        if caption or label:
            lines.append("\\begin{table}[htbp]")
            lines.append("    \\centering")
        
        # Tabular environment
        lines.append(f"    \\begin{{tabular}}{{{col_spec}}}")
        lines.append("        \\hline")
        
        # Generate rows with placeholders
        for row in range(rows):
            if row == 0 and has_header:
                cells = [f"⟨header{i+1}⟩" for i in range(cols)]
            else:
                cells = [f"⟨cell{row+1}-{i+1}⟩" for i in range(cols)]
            
            row_text = " & ".join(cells) + " \\\\"
            lines.append(f"        {row_text}")
            
            # Add hline after header or at end
            if (row == 0 and has_header) or row == rows - 1:
                lines.append("        \\hline")
        
        lines.append("    \\end{tabular}")
        
        # Caption and label with placeholders
        if caption:
            lines.append(f"    \\caption{{⟨{caption or 'caption'}⟩}}")
        if label:
            lines.append(f"    \\label{{⟨{label or 'label'}⟩}}")
            
        if caption or label:
            lines.append("\\end{table}")
        
        return "\n".join(lines)


class SimpleTableDialog:
    """Simple dialog for table insertion."""
    
    def __init__(self, parent, insert_callback=None):
        self.parent = parent
        self.insert_callback = insert_callback
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Insert LaTeX Table")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        self._setup_ui()
        self._center_dialog()
        
        # Focus first input
        self.rows_entry.focus_set()
        self.rows_entry.select_range(0, tk.END)
        
        debug_console.log("Table dialog opened", level='INFO')
    
    def _setup_ui(self):
        """Setup simple UI."""
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill="both", expand=True)
        
        # Dimensions
        dims_frame = ttk.LabelFrame(frame, text="Table Size", padding=10)
        dims_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(dims_frame, text="Rows:").grid(row=0, column=0, padx=5, pady=5)
        self.rows_var = tk.StringVar(value="3")
        self.rows_entry = ttk.Entry(dims_frame, textvariable=self.rows_var, width=8)
        self.rows_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dims_frame, text="Columns:").grid(row=0, column=2, padx=5, pady=5)
        self.cols_var = tk.StringVar(value="3")
        self.cols_entry = ttk.Entry(dims_frame, textvariable=self.cols_var, width=8)
        self.cols_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Options
        opts_frame = ttk.LabelFrame(frame, text="Options", padding=10)
        opts_frame.pack(fill="x", pady=(0, 10))
        
        self.header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="Include header row", 
                       variable=self.header_var).grid(row=0, column=0, sticky="w", pady=2)
        
        # Alignment
        align_frame = ttk.Frame(opts_frame)
        align_frame.grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(align_frame, text="Alignment:").pack(side="left", padx=(0, 10))
        
        self.align_var = tk.StringVar(value="c")
        for i, (text, val) in enumerate([("Left", "l"), ("Center", "c"), ("Right", "r")]):
            ttk.Radiobutton(align_frame, text=text, variable=self.align_var, 
                          value=val).pack(side="left", padx=5)
        
        # Caption and label
        ttk.Label(opts_frame, text="Caption:").grid(row=2, column=0, sticky="w", pady=2)
        self.caption_var = tk.StringVar()
        caption_entry = ttk.Entry(opts_frame, textvariable=self.caption_var, width=40)
        caption_entry.grid(row=3, column=0, sticky="ew", pady=2)
        
        ttk.Label(opts_frame, text="Label:").grid(row=4, column=0, sticky="w", pady=2)
        self.label_var = tk.StringVar()
        label_entry = ttk.Entry(opts_frame, textvariable=self.label_var, width=40)
        label_entry.grid(row=5, column=0, sticky="ew", pady=2)
        
        opts_frame.columnconfigure(0, weight=1)
        
        # Preview
        preview_frame = ttk.LabelFrame(frame, text="Preview", padding=10)
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.preview_text = tk.Text(preview_frame, height=10, width=60, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(preview_frame, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        self.preview_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(btn_frame, text="Insert", command=self._insert, 
                  bootstyle="success").pack(side="right", padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self._cancel, 
                  bootstyle="secondary").pack(side="right")
        
        # Bind updates
        for var in [self.rows_var, self.cols_var, self.caption_var, self.label_var]:
            var.trace_add("write", lambda *args: self._update_preview())
        self.header_var.trace_add("write", lambda *args: self._update_preview())
        self.align_var.trace_add("write", lambda *args: self._update_preview())
        
        # Initial preview
        self._update_preview()
        
        # Bind Enter key to insert
        self.dialog.bind('<Return>', lambda e: self._insert())
        self.dialog.bind('<Escape>', lambda e: self._cancel())
    
    def _update_preview(self):
        """Update preview with current settings."""
        try:
            rows = int(self.rows_var.get() or 0)
            cols = int(self.cols_var.get() or 0)
            
            if rows <= 0 or cols <= 0:
                self.preview_text.delete("1.0", tk.END)
                return
            
            latex_code = TableGenerator.generate(
                rows=rows,
                cols=cols,
                has_header=self.header_var.get(),
                alignment=self.align_var.get(),
                caption=self.caption_var.get(),
                label=self.label_var.get()
            )
            
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", latex_code)
            
        except ValueError:
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", "Invalid input - please enter positive numbers")
    
    def _validate_inputs(self):
        """Validate user inputs."""
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
            
            if rows <= 0 or cols <= 0:
                raise ValueError("Must be positive")
            if rows > 20 or cols > 10:
                raise ValueError("Too large (max 20 rows, 10 cols)")
                
            return rows, cols
        except ValueError as e:
            messagebox.showerror("Invalid Input", 
                               f"Please enter valid numbers for rows and columns.\n{e}", 
                               parent=self.dialog)
            return None, None
    
    def _insert(self):
        """Insert table into editor."""
        rows, cols = self._validate_inputs()
        if rows is None:
            return
        
        latex_code = TableGenerator.generate(
            rows=rows,
            cols=cols,
            has_header=self.header_var.get(),
            alignment=self.align_var.get(),
            caption=self.caption_var.get(),
            label=self.label_var.get()
        )
        
        self.result = latex_code
        
        if self.insert_callback:
            self.insert_callback(latex_code)
        
        debug_console.log("Table inserted successfully", level='SUCCESS')
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel dialog."""
        self.result = None
        self.dialog.destroy()
    
    def _center_dialog(self):
        """Center dialog on parent."""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")


def show_table_dialog(parent, insert_callback=None):
    """Show table insertion dialog."""
    debug_console.log("Opening table insertion dialog", level='ACTION')
    
    dialog = SimpleTableDialog(parent=parent, insert_callback=insert_callback)
    parent.wait_window(dialog.dialog)
    return dialog.result