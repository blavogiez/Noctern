"""
Modern vertical sidebar for AutomaTeX with icon-based action buttons.

Provides a clean, space-efficient alternative to the traditional horizontal topbar
with collapsible groups and modern visual styling.
"""

import ttkbootstrap as ttk
from tkinter import Canvas
from latex import compiler as latex_compiler
from llm import service as llm_service
from latex import translator as latex_translator
from app import interface, state
from utils import logs_console
from app.panels import show_metrics_panel, show_settings_panel
from utils.animations import move_widget

def _log_action(action_name):
    """Helper function to log user actions triggered from the sidebar."""
    logs_console.log(f"Sidebar Action: User triggered '{action_name}'.", level='ACTION')

class VerticalSidebar:
    """Modern vertical sidebar with icon-based buttons and collapsible groups."""
    
    def __init__(self, parent):
        self.parent = parent
        self.is_collapsed = False
        self.button_size = 34
        self.expanded_width = 160
        self.collapsed_width = 44
        
        # Create main sidebar frame
        self.sidebar_frame = ttk.Frame(parent, width=self.expanded_width, padding=2)
        self.sidebar_frame.pack_propagate(False)
        
        # Header with collapse/expand button
        self._create_header()
        
        # Button groups
        self._create_button_groups()
        
        # Apply theme-aware styling
        self._apply_styling()
    
    def _create_header(self):
        """Create sidebar header with collapse toggle."""
        header_frame = ttk.Frame(self.sidebar_frame, height=40)
        header_frame.pack(fill="x", padx=4, pady=(4, 8))
        header_frame.pack_propagate(False)
        
        # Toggle button
        self.toggle_btn = ttk.Button(
            header_frame,
            text="≡",
            width=3,
            command=self._toggle_sidebar,
            bootstyle="secondary-outline"
        )
        self.toggle_btn.pack(side="right", pady=4)
        
        # Title (hidden when collapsed)
        self.title_label = ttk.Label(
            header_frame, 
            text="Actions", 
            font=("Segoe UI", 10, "bold")
        )
        self.title_label.pack(side="left", padx=8, pady=4)
    
    def _create_button_groups(self):
        """Create organized button groups with icons and labels."""
        
        # File Operations Group
        self._create_group("File Operations", [
            ("📁", "Open", lambda: [_log_action("Open File"), interface.open_file()]),
            ("💾", "Save", lambda: [_log_action("Save File"), interface.save_file()]),
            ("📄", "Save As", lambda: [_log_action("Save File As"), interface.save_file_as()])
        ], "primary")
        
        # LaTeX Processing Group  
        self._create_group("LaTeX", [
            ("⚙️", "Compile", lambda: [_log_action("Compile LaTeX"), latex_compiler.compile_latex()]),
            ("👁️", "View PDF", lambda: [_log_action("View PDF"), latex_compiler.view_pdf_external()]),
            ("🌐", "Translate", lambda: [_log_action("Translate Text"), latex_translator.open_translate_panel()]),
            ("📍", "Go to PDF Line", lambda: [_log_action("Go to line in PDF"), interface.go_to_line_in_pdf()])
        ], "info")
        
        # AI/LLM Group
        self._create_group("AI Assistant", [
            ("✨", "Complete", lambda: [_log_action("LLM Complete Text"), llm_service.request_llm_to_complete_text()]),
            ("🎯", "Generate", lambda: [_log_action("LLM Generate Text"), llm_service.open_generate_text_panel()]),
            ("📝", "Rephrase", lambda: [_log_action("Tools: Rephrase Text"), interface.open_rephrase_panel()]),
            ("✅", "Proofread", lambda: [_log_action("Tools: Proofread Document"), llm_service.open_proofreading_panel()])
        ], "success")
        
        # Tools Group
        self._create_group("Tools", [
            ("🎨", "Smart Style", lambda: [_log_action("Tools: Smart Style"), interface.style_selected_text()]),
            ("🖼️", "Paste Image", lambda: [_log_action("Tools: Paste Image"), interface.paste_image()]),
            ("📋", "Insert Table", lambda: [_log_action("Tools: Insert Table"), interface.insert_table()]),
            ("🧹", "Clean Project", lambda: [_log_action("Tools: Clean Project"), latex_compiler.clean_project_directory()])
        ], "warning")
        
        # Settings Group (at bottom)
        self._create_bottom_group([
            ("📊", "Metrics", lambda: [_log_action("Tools: Usage Metrics"), show_metrics_panel()]),
            ("⚙️", "Settings", lambda: [_log_action("Settings: Open Preferences"), show_settings_panel()])
        ], "secondary")
    
    def _create_group(self, title, buttons, color_theme):
        """Create a collapsible button group."""
        # Group frame
        group_frame = ttk.LabelFrame(
            self.sidebar_frame, 
            text=title, 
            padding=6
        )
        group_frame.pack(fill="x", padx=4, pady=4)
        
        # Store group for collapse/expand
        group_frame.title_text = title
        
        # Create buttons
        for icon, label, command in buttons:
            btn_frame = ttk.Frame(group_frame)
            btn_frame.pack(fill="x", pady=1)
            
            # Icon button
            icon_btn = ttk.Button(
                btn_frame,
                text=icon,
                width=3,
                command=command,
                bootstyle=f"{color_theme}-outline"
            )
            icon_btn.pack(side="left")
            
            # Label (hidden when collapsed)
            label_btn = ttk.Button(
                btn_frame,
                text=label,
                command=command,
                bootstyle=f"{color_theme}-outline"
            )
            label_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))
            
            # Store references for collapse/expand
            btn_frame.icon_btn = icon_btn
            btn_frame.label_btn = label_btn
            
            # Add hover effects
            self._add_hover_effects(icon_btn, f"{color_theme}-outline", color_theme)
            self._add_hover_effects(label_btn, f"{color_theme}-outline", color_theme)
    
    def _create_bottom_group(self, buttons, color_theme):
        """Create bottom-aligned settings group."""
        # Spacer to push settings to bottom
        spacer = ttk.Frame(self.sidebar_frame)
        spacer.pack(fill="both", expand=True)
        
        # Settings frame
        settings_frame = ttk.Frame(self.sidebar_frame)
        settings_frame.pack(fill="x", padx=4, pady=4, side="bottom")
        
        for icon, label, command in buttons:
            btn_frame = ttk.Frame(settings_frame)
            btn_frame.pack(fill="x", pady=1)
            
            # Icon button  
            icon_btn = ttk.Button(
                btn_frame,
                text=icon,
                width=3,
                command=command,
                bootstyle=f"{color_theme}-outline"
            )
            icon_btn.pack(side="left")
            
            # Label button
            label_btn = ttk.Button(
                btn_frame,
                text=label,
                command=command,
                bootstyle=f"{color_theme}-outline"  
            )
            label_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))
            
            # Store references
            btn_frame.icon_btn = icon_btn
            btn_frame.label_btn = label_btn
            
            # Add hover effects
            self._add_hover_effects(icon_btn, f"{color_theme}-outline", color_theme)
            self._add_hover_effects(label_btn, f"{color_theme}-outline", color_theme)
    
    def _add_hover_effects(self, button, original_style, hover_color):
        """Add modern hover effects to buttons."""
        hover_style = hover_color if "outline" in original_style else f"{hover_color}-outline"
        
        def on_enter(e):
            button.config(bootstyle=hover_style)
            
        def on_leave(e):
            button.config(bootstyle=original_style)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<FocusIn>", on_enter)
        button.bind("<FocusOut>", on_leave)
    
    def _toggle_sidebar(self):
        """Toggle between collapsed and expanded states."""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self._collapse_sidebar()
        else:
            self._expand_sidebar()
    
    def _collapse_sidebar(self):
        """Collapse sidebar to show only icons."""
        self.sidebar_frame.configure(width=self.collapsed_width)
        self.toggle_btn.config(text="☰")
        self.title_label.pack_forget()
        
        # Hide all label buttons and group titles
        for widget in self.sidebar_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                widget.configure(text="")
                self._hide_labels_in_frame(widget)
            elif isinstance(widget, ttk.Frame):
                self._hide_labels_in_frame(widget)
    
    def _expand_sidebar(self):
        """Expand sidebar to show icons and labels."""
        self.sidebar_frame.configure(width=self.expanded_width)
        self.toggle_btn.config(text="≡")
        self.title_label.pack(side="left", padx=8, pady=4)
        
        # Show all label buttons and restore group titles
        for widget in self.sidebar_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame) and hasattr(widget, 'title_text'):
                widget.configure(text=widget.title_text)
                self._show_labels_in_frame(widget)
            elif isinstance(widget, ttk.Frame):
                self._show_labels_in_frame(widget)
    
    def _hide_labels_in_frame(self, frame):
        """Hide label buttons in a frame."""
        for child in frame.winfo_children():
            if isinstance(child, ttk.Frame) and hasattr(child, 'label_btn'):
                child.label_btn.pack_forget()
            elif isinstance(child, ttk.Frame):
                self._hide_labels_in_frame(child)
    
    def _show_labels_in_frame(self, frame):
        """Show label buttons in a frame."""
        for child in frame.winfo_children():
            if isinstance(child, ttk.Frame) and hasattr(child, 'label_btn'):
                child.label_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))
            elif isinstance(child, ttk.Frame):
                self._show_labels_in_frame(child)
    
    def _apply_styling(self):
        """Apply theme-aware styling to sidebar."""
        try:
            # Get current theme colors
            theme_colors = state.get_theme_settings() if hasattr(state, 'get_theme_settings') else {}
            
            # Apply subtle background differentiation
            if theme_colors.get('bg'):
                # Slightly darker/lighter background for sidebar
                bg_color = theme_colors['bg']
                self.sidebar_frame.configure(style="Sidebar.TFrame")
                
        except Exception as e:
            logs_console.log(f"Could not apply sidebar styling: {e}", level='DEBUG')
    
    def get_widget(self):
        """Return the main sidebar widget for integration."""
        return self.sidebar_frame

def create_vertical_sidebar(parent):
    """
    Create and return a vertical sidebar instance.
    
    Args:
        parent: Parent widget to contain the sidebar
        
    Returns:
        VerticalSidebar: Configured sidebar instance
    """
    sidebar = VerticalSidebar(parent)
    logs_console.log("Vertical sidebar created successfully", level='SUCCESS')
    return sidebar