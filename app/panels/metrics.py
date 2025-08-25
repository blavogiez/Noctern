"""
Integrated metrics panel for the left sidebar.
Shows both token usage and productivity metrics in tabbed interface.
"""

import tkinter as tk
from tkinter import ttk
import os
from typing import Optional
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents, PanelLayoutManager
from utils import debug_console


class MetricsPanel(BasePanel):
    """
    Integrated metrics panel with token usage and productivity metrics.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter,
                 file_path: str = None, on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        self.file_path = file_path
        
        # Token usage components
        self.token_tree: Optional[ttk.Treeview] = None
        self.token_summary_inner: Optional[tk.Frame] = None
        
        # Productivity components
        self.productivity_tree: Optional[ttk.Treeview] = None
        self.productivity_summary_inner: Optional[tk.Frame] = None
        
    def get_panel_title(self) -> str:
        return "Usage Metrics"
    
    def get_layout_style(self) -> PanelStyle:
        """Use split layout for full page usage like generation panel."""
        return PanelStyle.SPLIT
    
    def create_content(self):
        """Create the metrics panel content using split layout for full page usage."""
        # Use split layout from main_container (PanedWindow)
        paned_window = self.main_container
        
        # Token Usage section (top)
        self._create_token_usage_section(paned_window)
        
        # File Productivity section (bottom)
        self._create_productivity_section(paned_window)
        
        # Load initial data
        self._refresh_all_metrics()
        
    def _create_token_usage_section(self, parent):
        """Create the token usage metrics section (top)."""
        token_frame = ttk.Frame(parent, padding=StandardComponents.PADDING)
        parent.add(token_frame, weight=1)
        
        # Use main frame that fills all available space
        scrollable_frame = token_frame
        
        # Header section with main title
        header_section = StandardComponents.create_section(scrollable_frame, "Token Usage Metrics")
        header_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        header_frame = ttk.Frame(header_section)
        header_frame.pack(fill="x")
        
        refresh_button = StandardComponents.create_button_input(
            header_frame,
            "Refresh",
            self._refresh_token_metrics,
            width=10
        )
        refresh_button.pack(side="right")
        
        # Token usage treeview section
        tree_section = StandardComponents.create_section(scrollable_frame, "Daily Usage")
        tree_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        tree_frame = ttk.Frame(tree_section)
        tree_frame.pack(fill="both", expand=True)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Token treeview with columns
        self.token_tree = ttk.Treeview(
            tree_frame,
            columns=("date", "input", "output", "total"),
            show="headings",
            height=8
        )
        
        # Configure columns
        self.token_tree.heading("date", text="Date")
        self.token_tree.heading("input", text="Input Tokens")
        self.token_tree.heading("output", text="Output Tokens")
        self.token_tree.heading("total", text="Total")
        
        # Configure columns to fill available width
        self.token_tree.column("date", anchor=tk.W, width=120, minwidth=100)
        self.token_tree.column("input", anchor=tk.E, width=100, minwidth=80) 
        self.token_tree.column("output", anchor=tk.E, width=100, minwidth=80)
        self.token_tree.column("total", anchor=tk.E, width=100, minwidth=80)
        
        self.token_tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for token tree
        token_tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.token_tree.yview)
        token_tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.token_tree.config(yscrollcommand=token_tree_scrollbar.set)
        
        # Configure total row style
        self.token_tree.tag_configure("total_row", background="#e6f3ff", font=StandardComponents.BODY_FONT + ("bold",))
        
        # Token summary section
        token_summary_section = StandardComponents.create_section(scrollable_frame, "Token Summary")
        token_summary_section.pack(fill="x")
        
        self.token_summary_inner = ttk.Frame(token_summary_section)
        self.token_summary_inner.pack(fill="x", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        self.token_summary_inner.grid_columnconfigure(1, weight=1)
        
    def _create_productivity_section(self, parent):
        """Create the productivity metrics section (bottom)."""
        productivity_frame = ttk.Frame(parent, padding=StandardComponents.PADDING)
        parent.add(productivity_frame, weight=1)
        
        # Use main frame that fills all available space
        scrollable_frame = productivity_frame
        
        # Header section with main title  
        header_section = StandardComponents.create_section(scrollable_frame, "File Productivity Metrics")
        header_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Show current file info
        if self.file_path:
            filename = os.path.basename(self.file_path)
            file_info = StandardComponents.create_info_label(
                header_section,
                f"Viewing metrics for: {filename}",
                "body"
            )
            file_info.pack(anchor="w")
        else:
            file_info = StandardComponents.create_info_label(
                header_section,
                "No file selected for productivity metrics",
                "body"
            )
            file_info.pack(anchor="w")
        
        header_frame = ttk.Frame(header_section)
        header_frame.pack(fill="x", pady=(StandardComponents.PADDING//2, 0))
        
        refresh_button = StandardComponents.create_button_input(
            header_frame,
            "Refresh",
            self._refresh_productivity_metrics,
            width=10
        )
        refresh_button.pack(side="right")
        
        # Productivity sessions treeview section
        sessions_section = StandardComponents.create_section(scrollable_frame, "Session History")
        sessions_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        sessions_frame = ttk.Frame(sessions_section)
        sessions_frame.pack(fill="both", expand=True)
        sessions_frame.grid_rowconfigure(0, weight=1)
        sessions_frame.grid_columnconfigure(0, weight=1)
        
        # Productivity treeview with columns
        self.productivity_tree = ttk.Treeview(
            sessions_frame,
            columns=("date", "duration", "words", "productivity"),
            show="headings",
            height=8
        )
        
        # Configure columns
        self.productivity_tree.heading("date", text="Date")
        self.productivity_tree.heading("duration", text="Duration")
        self.productivity_tree.heading("words", text="Words")
        self.productivity_tree.heading("productivity", text="Words/Hour")
        
        # Configure columns to fill available width
        self.productivity_tree.column("date", anchor=tk.W, width=120, minwidth=100)
        self.productivity_tree.column("duration", anchor=tk.E, width=90, minwidth=70)
        self.productivity_tree.column("words", anchor=tk.E, width=90, minwidth=60)
        self.productivity_tree.column("productivity", anchor=tk.E, width=120, minwidth=80)
        
        self.productivity_tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for productivity tree
        prod_tree_scrollbar = ttk.Scrollbar(sessions_frame, orient="vertical", command=self.productivity_tree.yview)
        prod_tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.productivity_tree.config(yscrollcommand=prod_tree_scrollbar.set)
        
        # Productivity summary section
        prod_summary_section = StandardComponents.create_section(scrollable_frame, "Productivity Summary")
        prod_summary_section.pack(fill="x")
        
        self.productivity_summary_inner = ttk.Frame(prod_summary_section)
        self.productivity_summary_inner.pack(fill="x", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        self.productivity_summary_inner.grid_columnconfigure(1, weight=1)
        
    def _refresh_all_metrics(self):
        """Refresh both token and productivity metrics."""
        self._refresh_token_metrics()
        self._refresh_productivity_metrics()
        
    def _refresh_token_metrics(self):
        """Refresh the token usage metrics display."""
        try:
            # Import here to avoid circular imports
            from metrics import manager
            
            # Clear existing data
            if self.token_tree:
                for item in self.token_tree.get_children():
                    self.token_tree.delete(item)
            
                # Load metrics data
                metrics = manager.load_metrics()
                total_input = 0
                total_output = 0
                
                # Sort dates
                sorted_dates = sorted(metrics.keys())
                
                # Add rows for each date
                for date_str in sorted_dates:
                    data = metrics[date_str]
                    input_tokens = data.get("input", 0)
                    output_tokens = data.get("output", 0)
                    total_tokens = input_tokens + output_tokens
                    
                    self.token_tree.insert(
                        "", tk.END,
                        values=(date_str, f"{input_tokens:,}", f"{output_tokens:,}", f"{total_tokens:,}")
                    )
                    
                    total_input += input_tokens
                    total_output += output_tokens
                
                # Add total row
                total_all = total_input + total_output
                if total_all > 0:
                    self.token_tree.insert(
                        "", tk.END,
                        values=("TOTAL", f"{total_input:,}", f"{total_output:,}", f"{total_all:,}"),
                        tags=("total_row",)
                    )
                
                # Update summary
                self._update_token_summary(total_input, total_output, len(sorted_dates))
                
                debug_console.log(f"Refreshed token metrics: {len(sorted_dates)} days, {total_all:,} total tokens", level='INFO')
                
        except Exception as e:
            debug_console.log(f"Error refreshing token metrics: {e}", level='ERROR')
            
            # Show error in treeview
            if self.token_tree:
                self.token_tree.insert(
                    "", tk.END,
                    values=("Error", "Failed to load", "token metrics", "")
                )
    
    def _refresh_productivity_metrics(self):
        """Refresh the productivity metrics display."""
        try:
            if not self.file_path or not self.productivity_tree:
                return
                
            # Import here to avoid circular imports
            from metrics.session_tracker import SessionTracker
            
            # Clear existing data
            for item in self.productivity_tree.get_children():
                self.productivity_tree.delete(item)
            
            # Load productivity data
            tracker = SessionTracker(self.file_path)
            metrics_data = tracker.get_historical_metrics()
            sessions = metrics_data.get("sessions", []) if isinstance(metrics_data, dict) else []
            
            total_duration = 0
            total_words = 0
            
            # Add rows for each session
            for session in sessions:
                duration_str = self._format_duration(session.get('duration', 0))
                words = session.get('words_written', 0)
                duration_hours = session.get('duration', 0) / 3600
                productivity = words / duration_hours if duration_hours > 0 else 0
                
                self.productivity_tree.insert(
                    "", tk.END,
                    values=(
                        session.get('date', 'Unknown'),
                        duration_str,
                        f"{words:,}",
                        f"{productivity:.1f}"
                    )
                )
                
                total_duration += session.get('duration', 0)
                total_words += words
            
            # Update productivity summary
            self._update_productivity_summary(total_duration, total_words, len(sessions))
            
            debug_console.log(f"Refreshed productivity metrics: {len(sessions)} sessions", level='INFO')
            
        except Exception as e:
            debug_console.log(f"Error refreshing productivity metrics: {e}", level='ERROR')
            
            # Show error in treeview
            if self.productivity_tree:
                self.productivity_tree.insert(
                    "", tk.END,
                    values=("Error", "Failed to load", "productivity", "metrics")
                )
    
    def _format_duration(self, seconds):
        """Format duration in seconds to readable string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _update_token_summary(self, total_input: int, total_output: int, num_days: int):
        """Update the token usage summary statistics."""
        if not self.token_summary_inner:
            return
            
        # Clear existing summary widgets
        for widget in self.token_summary_inner.winfo_children():
            widget.destroy()
        
        total_tokens = total_input + total_output
        avg_per_day = total_tokens / max(num_days, 1)
        
        # Create summary labels
        summary_data = [
            ("Days with activity:", f"{num_days}"),
            ("Total input tokens:", f"{total_input:,}"),
            ("Total output tokens:", f"{total_output:,}"),
            ("Total tokens:", f"{total_tokens:,}"),
            ("Average per day:", f"{avg_per_day:,.1f}")
        ]
        
        for i, (label, value) in enumerate(summary_data):
            ttk.Label(self.token_summary_inner, text=label).grid(
                row=i, column=0, sticky="w", pady=2
            )
            ttk.Label(
                self.token_summary_inner,
                text=value,
                font=StandardComponents.BODY_FONT + ("bold",)
            ).grid(row=i, column=1, sticky="e", pady=2)
        
        # Cost estimation (rough)
        if total_tokens > 0:
            estimated_cost = total_tokens * 0.00002  # Rough estimate
            ttk.Label(self.token_summary_inner, text="Estimated cost (USD):").grid(
                row=len(summary_data), column=0, sticky="w", pady=(10, 2)
            )
            ttk.Label(
                self.token_summary_inner,
                text=f"${estimated_cost:.4f}",
                font=StandardComponents.BODY_FONT + ("bold",),
                foreground=self.get_theme_color("success_text", "#006600")
            ).grid(row=len(summary_data), column=1, sticky="e", pady=(10, 2))
            
            # Disclaimer
            ttk.Label(
                self.token_summary_inner,
                text="*Cost estimate is approximate and may vary by provider",
                font=StandardComponents.SMALL_FONT,
                foreground=self.get_theme_color("muted_text", "#666666")
            ).grid(row=len(summary_data) + 1, column=0, columnspan=2, pady=(5, 0))
    
    def _update_productivity_summary(self, total_duration: int, total_words: int, num_sessions: int):
        """Update the productivity summary statistics."""
        if not self.productivity_summary_inner:
            return
            
        # Clear existing summary widgets
        for widget in self.productivity_summary_inner.winfo_children():
            widget.destroy()
        
        total_hours = total_duration / 3600
        avg_productivity = total_words / total_hours if total_hours > 0 else 0
        avg_session_duration = total_duration / max(num_sessions, 1)
        
        # Create summary labels
        summary_data = [
            ("Total sessions:", f"{num_sessions}"),
            ("Total time:", self._format_duration(total_duration)),
            ("Total words written:", f"{total_words:,}"),
            ("Average productivity:", f"{avg_productivity:.1f} words/hour"),
            ("Average session:", self._format_duration(avg_session_duration))
        ]
        
        for i, (label, value) in enumerate(summary_data):
            ttk.Label(self.productivity_summary_inner, text=label).grid(
                row=i, column=0, sticky="w", pady=2
            )
            ttk.Label(
                self.productivity_summary_inner,
                text=value,
                font=StandardComponents.BODY_FONT + ("bold",)
            ).grid(row=i, column=1, sticky="e", pady=2)
    
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.token_tree:
            self.token_tree.focus_set()