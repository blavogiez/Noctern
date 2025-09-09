"""
Interactive table insertion panel with visual grid selector.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import logs_console
from editor.table_insertion import TableGenerator, TablePackage, PackageTableGenerator


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
        
        # Track confirmed selections for visual history
        self.confirmed_selections = set()
        
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
                
                # Determine cell color with visual history
                if row < self.selected_rows and col < self.selected_cols:
                    # Current selection - blue (highest priority)
                    color = "#0078d4"    # Professional blue for current selection
                    outline = "#005a9e"  # Darker blue outline
                elif (row + 1, col + 1) in self.confirmed_selections:
                    # Previously confirmed selection - green
                    color = "#28a745"    # Professional green for confirmed
                    outline = "#1e7e34"  # Darker green outline
                else:
                    # Default unselected state
                    color = "#ffffff"    # Clean white for unselected
                    outline = "#e1e5e9"  # Light gray outline
                
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=outline,
                    width=2 if (row < self.selected_rows and col < self.selected_cols) or (row + 1, col + 1) in self.confirmed_selections else 1
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
        # Store current selection in history
        self.confirmed_selections.add((self.selected_rows, self.selected_cols))
        
        if self.on_selection_change:
            self.on_selection_change(self.selected_rows, self.selected_cols)
    
    def _on_mouse_leave(self, event):
        """Handle mouse leaving the grid area."""
        # Keep current selection
        pass
    
    def get_selection(self):
        """Get current grid selection."""
        return self.selected_rows, self.selected_cols




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
        self.package_var: Optional[tk.StringVar] = None
        self.option_widgets: dict = {}  # Dynamic option widgets
        self.packages_info: Optional[ttk.Label] = None
        
        # Current state
        self.current_rows = 2
        self.current_cols = 3
        self.current_package = TablePackage.BASIC
        self.current_generator: Optional[PackageTableGenerator] = None
        
    def get_panel_title(self) -> str:
        return "Insert Table"
    
    def get_layout_style(self) -> PanelStyle:
        """Use split layout like generation panel for better space usage."""
        return PanelStyle.SPLIT
    
    def get_critical_action_buttons(self) -> list:
        """Get critical action buttons that must always be visible."""
        return [
            ("Insert Table", self._handle_insert, "primary"),
            ("Cancel", self._handle_close, "secondary")
        ]
    
    def create_content(self):
        """Create the table insertion panel using split layout like generation panel."""
        # main_container is a PanedWindow for split layout
        paned_window = self.main_container
        
        # Grid selector section (top - takes more space)
        self._create_grid_selector_section(paned_window)
        
        # Options and preview section (bottom)
        self._create_bottom_section(paned_window)
        
    
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
        
        # Package selection section
        self._create_package_section(main_frame)
        
        # Dynamic options section
        self._create_dynamic_options_section(main_frame)
        
        # Action buttons section
        self._create_action_section(main_frame)
    
    def _create_package_section(self, parent):
        """Create package selection section."""
        package_section = StandardComponents.create_section(parent, "LaTeX Package")
        package_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Package selection frame
        selection_frame = ttk.Frame(package_section)
        selection_frame.pack(fill="x", pady=StandardComponents.ELEMENT_SPACING)
        
        # Package dropdown
        ttk.Label(selection_frame, text="Package:", font=StandardComponents.BODY_FONT).pack(side="left")
        
        self.package_var = tk.StringVar(value=TablePackage.BASIC.value)
        package_combo = ttk.Combobox(
            selection_frame,
            textvariable=self.package_var,
            state="readonly",
            width=20
        )
        
        # Populate package options
        package_options = []
        for package in TablePackage:
            display_name, description, _ = TableGenerator.get_package_info(package)
            package_options.append(f"{display_name} - {description}")
        
        package_combo['values'] = package_options
        package_combo.current(0)
        package_combo.bind('<<ComboboxSelected>>', self._on_package_change)
        package_combo.pack(side="left", padx=(10, 0), fill="x", expand=True)
        
        # Required packages info
        self.packages_info = ttk.Label(
            package_section,
            text="Required packages will appear here",
            font=StandardComponents.CODE_FONT,
            foreground="#666666"
        )
        self.packages_info.pack(anchor="w", pady=(10, 0))
        
        # Initialize current generator
        self.current_generator = TableGenerator.get_generator(self.current_package)
        self._update_packages_info()
    
    def _create_dynamic_options_section(self, parent):
        """Create dynamic options section that adapts to selected package."""
        self.options_section = StandardComponents.create_section(parent, "Package Options")
        self.options_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Create scrollable frame for options - reduced height to ensure button visibility
        self.options_canvas = tk.Canvas(self.options_section, height=180)  # Reduced from 280 to 180
        self.options_scrollbar = ttk.Scrollbar(self.options_section, orient="vertical", command=self.options_canvas.yview)
        self.options_frame = ttk.Frame(self.options_canvas)
        
        self.options_frame.bind(
            "<Configure>",
            lambda e: self.options_canvas.configure(scrollregion=self.options_canvas.bbox("all"))
        )
        
        self.options_canvas.create_window((0, 0), window=self.options_frame, anchor="nw")
        self.options_canvas.configure(yscrollcommand=self.options_scrollbar.set)
        
        self.options_canvas.pack(side="left", fill="both", expand=True)
        self.options_scrollbar.pack(side="right", fill="y")
        
        # Create initial options
        self._rebuild_options_ui()
    
    
    def _create_action_section(self, parent):
        """Action buttons are now handled by BasePanel's critical actions system."""
        # Critical action buttons are automatically created and guaranteed to be visible
        pass
    
    def _on_grid_selection_changed(self, rows, cols):
        """Handle grid selection change."""
        self.current_rows = rows
        self.current_cols = cols
        logs_console.log(f"Table dimensions changed to {rows}×{cols}", level='DEBUG')
    
    def _on_package_change(self, event=None):
        """Handle package selection change."""
        selected_index = event.widget.current()
        packages = list(TablePackage)
        
        if 0 <= selected_index < len(packages):
            self.current_package = packages[selected_index]
            self.current_generator = TableGenerator.get_generator(self.current_package)
            
            logs_console.log(f"Changed to {self.current_package.value} package", level='DEBUG')
            
            # Update UI
            self._rebuild_options_ui()
            self._update_packages_info()
    
    def _rebuild_options_ui(self):
        """Rebuild the options UI based on current package."""
        # Clear existing options
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        self.option_widgets.clear()
        
        if not self.current_generator:
            return
        
        # Get options for current generator
        options = self.current_generator.get_available_options()
        
        # Create grid for options
        row = 0
        
        for option_key, option_config in options.items():
            option_type = option_config['type']
            label_text = option_config['label']
            default_value = option_config['default']
            
            # Label
            ttk.Label(
                self.options_frame,
                text=f"{label_text}:",
                font=StandardComponents.BODY_FONT
            ).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 10))
            
            # Widget based on type
            if option_type == 'boolean':
                var = tk.BooleanVar(value=default_value)
                widget = ttk.Checkbutton(
                    self.options_frame,
                    variable=var
                )
                self.option_widgets[option_key] = var
                
            elif option_type == 'choice':
                var = tk.StringVar(value=default_value)
                choices = option_config['choices']
                
                # Use Combobox for choices
                widget = ttk.Combobox(
                    self.options_frame,
                    textvariable=var,
                    state="readonly",
                    width=15
                )
                widget['values'] = [choice[0] for choice in choices]
                # Find default index
                for i, (_, value) in enumerate(choices):
                    if value == default_value:
                        widget.current(i)
                        break
                
                self.option_widgets[option_key] = var
                
            elif option_type == 'string':
                var = tk.StringVar(value=default_value)
                widget = StandardComponents.create_entry_input(self.options_frame, width=20)
                widget.configure(textvariable=var)
                self.option_widgets[option_key] = var
            
            widget.grid(row=row, column=1, sticky="ew", pady=2)
            row += 1
        
        # Configure grid weights
        self.options_frame.grid_columnconfigure(1, weight=1)
    
    def _update_packages_info(self):
        """Update the required packages information."""
        if not self.packages_info or not self.current_generator:
            return
        
        try:
            required_packages = self.current_generator.required_packages
            
            if not required_packages:
                info_text = "No additional packages required (built-in LaTeX)"
            else:
                packages_str = ", ".join(required_packages)
                info_text = f"Required: \\usepackage{{{packages_str}}}"
            
            self.packages_info.config(text=info_text)
            
        except Exception as e:
            logs_console.log(f"Error updating packages info: {e}", level='ERROR')
    
    def _get_current_options(self) -> dict:
        """Get current option values."""
        if not self.current_generator:
            return {}
        
        options = {}
        available_options = self.current_generator.get_available_options()
        
        for option_key, option_config in available_options.items():
            if option_key in self.option_widgets:
                var = self.option_widgets[option_key]
                
                if option_config['type'] == 'choice':
                    # Find the value for the selected choice
                    selected_text = var.get()
                    for choice_text, choice_value in option_config['choices']:
                        if choice_text == selected_text:
                            options[option_key] = choice_value
                            break
                    else:
                        options[option_key] = option_config['default']
                else:
                    options[option_key] = var.get()
            else:
                options[option_key] = option_config['default']
        
        return options
    
    
    def _handle_insert(self):
        """Handle table insertion."""
        if not self.current_generator:
            return
        
        # Generate the table code with current options
        options = self._get_current_options()
        table_code = self.current_generator.generate(
            rows=self.current_rows,
            cols=self.current_cols,
            options=options
        )
        
        logs_console.log(f"Inserting {self.current_rows}×{self.current_cols} table", level='ACTION')
        
        # Call insert callback
        if self.insert_callback:
            self.insert_callback(table_code)
        
        # Close panel
        self._handle_close()
    
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.grid_selector:
            self.grid_selector.focus_set()