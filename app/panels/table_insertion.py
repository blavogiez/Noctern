"""
Interactive table insertion panel with visual grid selector.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import debug_console


class InteractiveGridSelector(tk.Frame):
    """Interactive grid selector for table dimensions."""
    
    def __init__(self, parent, on_selection_change: Callable[[int, int], None]):
        super().__init__(parent)
        self.on_selection_change = on_selection_change
        
        # Grid settings - Larger grid for better user experience
        self.max_rows = 12
        self.max_cols = 10
        self.cell_size = 26  # Increased from 24 for even better visibility
        self.cell_gap = 3    # Increased gap for cleaner separation
        self.selected_rows = 2
        self.selected_cols = 3
        
        # Create canvas for grid - flexible size to use available space
        self.canvas = tk.Canvas(
            self,
            highlightthickness=2,
            highlightbackground="#0078d4",
            highlightcolor="#0078d4",
            bg="#f8f9fa",
            relief="solid",
            borderwidth=1
        )
        self.canvas.pack(fill="both", expand=True, pady=15, padx=10)
        
        # Bind resize event to adjust grid when canvas size changes
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        
        # Status label
        self.status_label = ttk.Label(
            self,
            text=f"{self.selected_rows} × {self.selected_cols} table",
            font=StandardComponents.BODY_FONT
        )
        self.status_label.pack(pady=(0, 5))
        
        # Bind events
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Leave>", self._on_mouse_leave)
        
        # Draw initial grid (will be drawn after first Configure event)
        self.after(100, self._draw_grid)  # Delay to ensure canvas is sized
    
    def _draw_grid(self):
        """Draw the interactive grid adapted to canvas size."""
        self.canvas.delete("all")
        
        # Get current canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return  # Canvas not ready yet
        
        # Calculate optimal cell size based on available space
        margin = 20
        available_width = canvas_width - 2 * margin
        available_height = canvas_height - 2 * margin - 40  # Space for status label
        
        # Calculate cell size that fits the available space
        cell_width = (available_width - (self.max_cols + 1) * self.cell_gap) // self.max_cols
        cell_height = (available_height - (self.max_rows + 1) * self.cell_gap) // self.max_rows
        
        # Use the smaller dimension to keep cells square, with minimum size
        cell_size = max(min(cell_width, cell_height), 16)
        
        # Calculate grid position to center it
        grid_width = self.max_cols * cell_size + (self.max_cols + 1) * self.cell_gap
        grid_height = self.max_rows * cell_size + (self.max_rows + 1) * self.cell_gap
        start_x = (canvas_width - grid_width) // 2
        start_y = (canvas_height - grid_height) // 2
        
        for row in range(self.max_rows):
            for col in range(self.max_cols):
                x1 = start_x + col * (cell_size + self.cell_gap) + self.cell_gap
                y1 = start_y + row * (cell_size + self.cell_gap) + self.cell_gap
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                # Determine cell color - More professional colors
                if row < self.selected_rows and col < self.selected_cols:
                    color = "#0078d4"    # Professional blue for selected
                    outline = "#005a9e"  # Darker blue outline
                else:
                    color = "#ffffff"    # Clean white for unselected
                    outline = "#e1e5e9"  # Light gray outline
                
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=outline,
                    width=2 if row < self.selected_rows and col < self.selected_cols else 1
                )
        
        # Store calculated values for mouse interaction
        self._grid_start_x = start_x
        self._grid_start_y = start_y
        self._grid_cell_size = cell_size
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize by redrawing the grid."""
        self.after(50, self._draw_grid)  # Small delay to avoid too many redraws
    
    def _on_mouse_move(self, event):
        """Handle mouse movement over grid with enhanced feedback."""
        # Only proceed if grid is ready
        if not hasattr(self, '_grid_start_x'):
            return
            
        # Calculate which cell we're over using dynamic coordinates
        relative_x = event.x - self._grid_start_x - self.cell_gap
        relative_y = event.y - self._grid_start_y - self.cell_gap
        
        if relative_x < 0 or relative_y < 0:
            return
            
        col = min(self.max_cols, max(1, relative_x // (self._grid_cell_size + self.cell_gap) + 1))
        row = min(self.max_rows, max(1, relative_y // (self._grid_cell_size + self.cell_gap) + 1))
        
        # Update selection with smooth feedback
        if row != self.selected_rows or col != self.selected_cols:
            self.selected_rows = row
            self.selected_cols = col
            self._draw_grid()
            # Enhanced status message
            table_type = "Small" if (row * col <= 6) else "Medium" if (row * col <= 20) else "Large"
            self.status_label.config(text=f"{self.selected_rows} × {self.selected_cols} table ({table_type})")
    
    def _on_click(self, event):
        """Handle grid click."""
        if self.on_selection_change:
            self.on_selection_change(self.selected_rows, self.selected_cols)
    
    def _on_mouse_leave(self, event):
        """Handle mouse leaving the grid area."""
        # Keep current selection
        pass
    
    def get_selection(self):
        """Get current grid selection."""
        return self.selected_rows, self.selected_cols


class TableGenerator:
    """Enhanced LaTeX table code generator."""
    
    @staticmethod
    def generate(rows, cols, has_header=True, alignment='c', caption='', label=''):
        """Generate LaTeX table with enhanced formatting."""
        debug_console.log(f"Generating {rows}×{cols} table", level='INFO')
        
        # Build column spec
        col_spec = '|' + alignment + '|' * cols
        lines = []
        
        # Table environment if caption or label
        if caption or label:
            lines.append("\\begin{table}[htbp]")
            lines.append("    \\centering")
        
        # Tabular environment
        lines.append(f"    \\begin{{tabular}}{{{col_spec}}}")
        lines.append("        \\hline")
        
        # Generate rows with smart placeholders
        for row in range(rows):
            if row == 0 and has_header:
                cells = [f"Header {i+1}" for i in range(cols)]
                row_text = " & ".join([f"\\textbf{{{cell}}}" for cell in cells]) + " \\\\"
            else:
                data_row = row if not has_header else row
                cells = [f"Data {data_row+1}.{i+1}" for i in range(cols)]
                row_text = " & ".join(cells) + " \\\\"
            
            lines.append(f"        {row_text}")
            
            # Add hlines strategically
            if (row == 0 and has_header) or row == rows - 1:
                lines.append("        \\hline")
        
        lines.append("    \\end{tabular}")
        
        # Caption and label
        if caption:
            lines.append(f"    \\caption{{{caption}}}")
        if label:
            lines.append(f"    \\label{{tab:{label}}}")
        
        if caption or label:
            lines.append("\\end{table}")
        
        return "\n".join(lines)


class TableInsertionPanel(BasePanel):
    """
    Beautiful table insertion panel with interactive grid selector.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter,
                 insert_callback: Callable,
                 on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.insert_callback = insert_callback
        
        # UI components
        self.grid_selector: Optional[InteractiveGridSelector] = None
        self.header_var: Optional[tk.BooleanVar] = None
        self.align_var: Optional[tk.StringVar] = None
        self.caption_var: Optional[tk.StringVar] = None
        self.label_var: Optional[tk.StringVar] = None
        self.preview_text: Optional[tk.Text] = None
        
        # Current dimensions
        self.current_rows = 2
        self.current_cols = 3
        
    def get_panel_title(self) -> str:
        return "Insert Table"
    
    def get_layout_style(self) -> PanelStyle:
        """Use split layout like generation panel for better space usage."""
        return PanelStyle.SPLIT
    
    def create_content(self):
        """Create the table insertion panel using split layout like generation panel."""
        # main_container is a PanedWindow for split layout
        paned_window = self.main_container
        
        # Grid selector section (top - takes more space)
        self._create_grid_selector_section(paned_window)
        
        # Options and preview section (bottom)
        self._create_bottom_section(paned_window)
        
        # Generate initial preview
        self._update_preview()
    
    def _create_grid_selector_section(self, parent):
        """Create the grid selector section (top pane)."""
        grid_frame = ttk.Frame(parent)
        parent.add(grid_frame, weight=2)  # Give more space to grid like generation panel
        
        # Main content with padding like generation panel
        main_frame = ttk.Frame(grid_frame, padding=StandardComponents.PADDING)
        main_frame.pack(fill="both", expand=True)
        
        # Grid section using standardized components
        grid_section = StandardComponents.create_section(main_frame, "Select Table Size")
        grid_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        # Instructions
        instructions = StandardComponents.create_info_label(
            grid_section,
            "Hover over the grid to select table dimensions, then click to confirm:",
            "body"
        )
        instructions.pack(anchor="w", pady=(0, StandardComponents.PADDING//2))
        
        # Interactive grid selector - Uses remaining space
        self.grid_selector = InteractiveGridSelector(
            grid_section,
            self._on_grid_selection_changed
        )
        self.grid_selector.pack(fill="both", expand=True, pady=10)
        
        # Set as main widget for focus
        self.main_widget = self.grid_selector
    
    def _create_bottom_section(self, parent):
        """Create the bottom section with options and preview (bottom pane)."""
        bottom_frame = ttk.Frame(parent)
        parent.add(bottom_frame, weight=1)  # Less space for options like generation panel
        
        # Main content with padding like generation panel
        main_frame = ttk.Frame(bottom_frame, padding=StandardComponents.PADDING)
        main_frame.pack(fill="both", expand=True)
        
        # Table options section
        self._create_options_section(main_frame)
        
        # Preview section
        self._create_preview_section(main_frame)
        
        # Action buttons section
        self._create_action_section(main_frame)
    
    def _create_options_section(self, parent):
        """Create table formatting options."""
        options_section = StandardComponents.create_section(parent, "Table Options")
        options_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Options grid
        options_grid = StandardComponents.create_grid_frame(options_section, columns=2, padding=StandardComponents.ELEMENT_SPACING)
        
        row = 0
        
        # Header row option
        ttk.Label(options_grid, text="Include header row:", font=StandardComponents.BODY_FONT).grid(
            row=row, column=0, sticky="w", pady=2
        )
        self.header_var = tk.BooleanVar(value=True)
        header_check = ttk.Checkbutton(options_grid, variable=self.header_var, command=self._update_preview)
        header_check.grid(row=row, column=1, sticky="w", pady=2)
        row += 1
        
        # Column alignment
        ttk.Label(options_grid, text="Column alignment:", font=StandardComponents.BODY_FONT).grid(
            row=row, column=0, sticky="w", pady=2
        )
        self.align_var = tk.StringVar(value="c")
        align_frame = ttk.Frame(options_grid)
        align_frame.grid(row=row, column=1, sticky="w", pady=2)
        
        alignments = [("Left", "l"), ("Center", "c"), ("Right", "r")]
        for i, (text, value) in enumerate(alignments):
            ttk.Radiobutton(
                align_frame,
                text=text,
                variable=self.align_var,
                value=value,
                command=self._update_preview
            ).pack(side="left", padx=(0, 10))
        row += 1
        
        # Caption
        ttk.Label(options_grid, text="Caption (optional):", font=StandardComponents.BODY_FONT).grid(
            row=row, column=0, sticky="w", pady=2
        )
        self.caption_var = tk.StringVar()
        caption_entry = StandardComponents.create_entry_input(options_grid, width=20)
        caption_entry.configure(textvariable=self.caption_var)
        caption_entry.grid(row=row, column=1, sticky="ew", pady=2)
        caption_entry.bind("<KeyRelease>", lambda e: self._update_preview())
        row += 1
        
        # Label
        ttk.Label(options_grid, text="Label (optional):", font=StandardComponents.BODY_FONT).grid(
            row=row, column=0, sticky="w", pady=2
        )
        self.label_var = tk.StringVar()
        label_entry = StandardComponents.create_entry_input(options_grid, width=20)
        label_entry.configure(textvariable=self.label_var)
        label_entry.grid(row=row, column=1, sticky="ew", pady=2)
        label_entry.bind("<KeyRelease>", lambda e: self._update_preview())
    
    def _create_preview_section(self, parent):
        """Create live preview section."""
        preview_section = StandardComponents.create_section(parent, "Live Preview")
        preview_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        # Preview text widget
        self.preview_text = StandardComponents.create_text_input(
            preview_section,
            "LaTeX code will appear here...",
            height=12
        )
        self.preview_text.pack(fill="both", expand=True)
        self.preview_text.config(state="disabled", font=StandardComponents.CODE_FONT)
    
    def _create_action_section(self, parent):
        """Create action buttons."""
        # Action buttons
        action_buttons = [
            ("Insert Table", self._handle_insert, "primary"),
            ("Cancel", self._handle_close, "secondary")
        ]
        action_row = StandardComponents.create_button_row(parent, action_buttons)
        action_row.pack(fill="x", pady=(StandardComponents.SECTION_SPACING, 0))
    
    def _on_grid_selection_changed(self, rows, cols):
        """Handle grid selection change."""
        self.current_rows = rows
        self.current_cols = cols
        debug_console.log(f"Table dimensions changed to {rows}×{cols}", level='DEBUG')
        self._update_preview()
    
    def _update_preview(self):
        """Update the live preview."""
        if not self.preview_text:
            return
        
        try:
            # Generate table code
            table_code = TableGenerator.generate(
                rows=self.current_rows,
                cols=self.current_cols,
                has_header=self.header_var.get() if self.header_var else True,
                alignment=self.align_var.get() if self.align_var else 'c',
                caption=self.caption_var.get() if self.caption_var else '',
                label=self.label_var.get() if self.label_var else ''
            )
            
            # Update preview
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", table_code)
            self.preview_text.config(state="disabled")
            
        except Exception as e:
            debug_console.log(f"Error updating preview: {e}", level='ERROR')
    
    def _handle_insert(self):
        """Handle table insertion."""
        if not self.preview_text:
            return
        
        # Get the generated table code
        table_code = self.preview_text.get("1.0", "end-1c")
        
        debug_console.log(f"Inserting {self.current_rows}×{self.current_cols} table", level='ACTION')
        
        # Call insert callback
        if self.insert_callback:
            self.insert_callback(table_code)
        
        # Close panel
        self._handle_close()
    
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.grid_selector:
            self.grid_selector.focus_set()