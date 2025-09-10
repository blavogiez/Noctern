"""
Integrated metrics panel for the left sidebar.
Shows both token usage and productivity metrics in tabbed interface.
"""

import tkinter as tk
from tkinter import ttk
import os
from typing import Optional, Dict, List, Tuple, Any
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents, PanelLayoutManager
from utils import logs_console


class TreeviewConfig:
    """Configuration for treeview setup."""
    
    def __init__(self, columns: List[str], headings: List[str], 
                 column_widths: List[int], column_alignments: List[str],
                 min_widths: List[int] = None):
        self.columns = columns
        self.headings = headings  
        self.column_widths = column_widths
        self.column_alignments = column_alignments
        self.min_widths = min_widths or [80] * len(columns)


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
        
        # Define treeview configurations
        self._token_tree_config = TreeviewConfig(
            columns=["date", "input", "output", "total"],
            headings=["Date", "Input Tokens", "Output Tokens", "Total"],
            column_widths=[120, 100, 100, 100],
            column_alignments=[tk.W, tk.E, tk.E, tk.E],
            min_widths=[100, 80, 80, 80]
        )
        
        self._productivity_tree_config = TreeviewConfig(
            columns=["date", "duration", "words", "productivity"],
            headings=["Date", "Duration", "Words", "Words/Hour"],
            column_widths=[120, 90, 90, 120],
            column_alignments=[tk.W, tk.E, tk.E, tk.E],
            min_widths=[100, 70, 60, 80]
        )
        
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
        
        scrollable_frame = token_frame
        
        # Create header with refresh button
        self._create_section_header(
            scrollable_frame, 
            "Token Usage Metrics", 
            self._refresh_token_metrics
        )
        
        # Create treeview section
        tree_section = self._create_treeview_section(
            scrollable_frame,
            "Daily Usage",
            self._token_tree_config,
            "total_row"
        )
        self.token_tree = tree_section["tree"]
        
        # Create summary section
        self.token_summary_inner = self._create_summary_section(
            scrollable_frame, 
            "Token Summary"
        )
        
    def _create_productivity_section(self, parent):
        """Create the productivity metrics section (bottom)."""
        productivity_frame = ttk.Frame(parent, padding=StandardComponents.PADDING)
        parent.add(productivity_frame, weight=1)
        
        scrollable_frame = productivity_frame
        
        # Create header with file info and refresh button
        self._create_productivity_header(scrollable_frame)
        
        # Create treeview section
        tree_section = self._create_treeview_section(
            scrollable_frame,
            "Session History", 
            self._productivity_tree_config
        )
        self.productivity_tree = tree_section["tree"]
        
        # Create summary section
        self.productivity_summary_inner = self._create_summary_section(
            scrollable_frame,
            "Productivity Summary"
        )
        
    def _create_section_header(self, parent, title: str, refresh_callback):
        """Create a standardized section header with refresh button."""
        header_section = StandardComponents.create_section(parent, title)
        header_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        header_frame = ttk.Frame(header_section)
        header_frame.pack(fill="x")
        
        refresh_button = StandardComponents.create_button_input(
            header_frame,
            "Refresh",
            refresh_callback,
            width=10
        )
        refresh_button.pack(side="right")
        
        return header_section
    
    def _create_productivity_header(self, parent):
        """Create header section for productivity metrics with file info."""
        header_section = StandardComponents.create_section(parent, "File Productivity Metrics")
        header_section.pack(fill="x", pady=(0, StandardComponents.SECTION_SPACING))
        
        # Show current file info
        file_info_text = (f"Viewing metrics for: {os.path.basename(self.file_path)}" 
                         if self.file_path 
                         else "No file selected for productivity metrics")
        
        file_info = StandardComponents.create_info_label(
            header_section,
            file_info_text,
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
        
        return header_section
    
    def _create_treeview_section(self, parent, section_title: str, config: TreeviewConfig, 
                               total_row_tag: str = None) -> Dict[str, Any]:
        """Create a standardized treeview section with scrollbar."""
        tree_section = StandardComponents.create_section(parent, section_title)
        tree_section.pack(fill="both", expand=True, pady=(0, StandardComponents.SECTION_SPACING))
        
        tree_frame = ttk.Frame(tree_section)
        tree_frame.pack(fill="both", expand=True)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview
        tree = ttk.Treeview(
            tree_frame,
            columns=tuple(config.columns),
            show="headings",
            height=8
        )
        
        # Configure columns
        for i, (col, heading, width, anchor, minwidth) in enumerate(zip(
            config.columns, config.headings, config.column_widths,
            config.column_alignments, config.min_widths
        )):
            tree.heading(col, text=heading)
            tree.column(col, anchor=anchor, width=width, minwidth=minwidth)
        
        tree.grid(row=0, column=0, sticky="nsew")
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.config(yscrollcommand=scrollbar.set)
        
        # Configure special row style if specified
        if total_row_tag:
            tree.tag_configure(total_row_tag, 
                              background="#e6f3ff", 
                              font=StandardComponents.BODY_FONT + ("bold",))
        
        return {"tree": tree, "scrollbar": scrollbar, "section": tree_section}
    
    def _create_summary_section(self, parent, title: str) -> ttk.Frame:
        """Create a standardized summary section."""
        summary_section = StandardComponents.create_section(parent, title)
        summary_section.pack(fill="x")
        
        summary_inner = ttk.Frame(summary_section)
        summary_inner.pack(fill="x", padx=StandardComponents.PADDING, pady=StandardComponents.PADDING)
        summary_inner.grid_columnconfigure(1, weight=1)
        
        return summary_inner
    
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
            self._clear_tree(self.token_tree)
            
            # Load and process metrics data
            metrics = manager.load_metrics()
            token_data = self._process_token_metrics(metrics)
            
            # Populate tree with data
            self._populate_token_tree(token_data)
            
            # Update summary
            self._update_token_summary(
                token_data["total_input"], 
                token_data["total_output"], 
                token_data["num_days"]
            )
            
            logs_console.log(
                f"Refreshed token metrics: {token_data['num_days']} days, {token_data['total_all']:,} total tokens", 
                level='INFO'
            )
            
        except Exception as e:
            logs_console.log(f"Error refreshing token metrics: {e}", level='ERROR')
            self._show_tree_error(self.token_tree, ["Error", "Failed to load", "token metrics", ""])
    
    def _refresh_productivity_metrics(self):
        """Refresh the productivity metrics display."""
        try:
            if not self.file_path or not self.productivity_tree:
                return
                
            # Import here to avoid circular imports
            from metrics.session_tracker import SessionTracker
            
            # Clear existing data
            self._clear_tree(self.productivity_tree)
            
            # Load and process productivity data
            tracker = SessionTracker(self.file_path)
            metrics_data = tracker.get_historical_metrics()
            sessions = metrics_data.get("sessions", []) if isinstance(metrics_data, dict) else []
            
            productivity_data = self._process_productivity_metrics(sessions)
            
            # Populate tree with data
            self._populate_productivity_tree(sessions)
            
            # Update summary
            self._update_productivity_summary(
                productivity_data["total_duration"], 
                productivity_data["total_words"], 
                productivity_data["num_sessions"]
            )
            
            logs_console.log(f"Refreshed productivity metrics: {productivity_data['num_sessions']} sessions", level='INFO')
            
        except Exception as e:
            logs_console.log(f"Error refreshing productivity metrics: {e}", level='ERROR')
            self._show_tree_error(self.productivity_tree, ["Error", "Failed to load", "productivity", "metrics"])
    
    def _clear_tree(self, tree: ttk.Treeview):
        """Clear all items from a treeview."""
        if tree:
            for item in tree.get_children():
                tree.delete(item)
    
    def _show_tree_error(self, tree: ttk.Treeview, error_values: List[str]):
        """Show an error message in a treeview."""
        if tree:
            tree.insert("", tk.END, values=tuple(error_values))
    
    def _process_token_metrics(self, metrics: Dict) -> Dict[str, int]:
        """Process raw token metrics into aggregated data."""
        total_input = 0
        total_output = 0
        sorted_dates = sorted(metrics.keys())
        
        for date_str in sorted_dates:
            data = metrics[date_str]
            total_input += data.get("input", 0)
            total_output += data.get("output", 0)
        
        return {
            "total_input": total_input,
            "total_output": total_output,
            "total_all": total_input + total_output,
            "num_days": len(sorted_dates),
            "sorted_dates": sorted_dates,
            "raw_metrics": metrics
        }
    
    def _populate_token_tree(self, token_data: Dict):
        """Populate the token tree with processed data."""
        if not self.token_tree:
            return
            
        metrics = token_data["raw_metrics"]
        
        # Add rows for each date
        for date_str in token_data["sorted_dates"]:
            data = metrics[date_str]
            input_tokens = data.get("input", 0)
            output_tokens = data.get("output", 0)
            total_tokens = input_tokens + output_tokens
            
            self.token_tree.insert(
                "", tk.END,
                values=(date_str, f"{input_tokens:,}", f"{output_tokens:,}", f"{total_tokens:,}")
            )
        
        # Add total row
        if token_data["total_all"] > 0:
            self.token_tree.insert(
                "", tk.END,
                values=(
                    "TOTAL", 
                    f"{token_data['total_input']:,}", 
                    f"{token_data['total_output']:,}", 
                    f"{token_data['total_all']:,}"
                ),
                tags=("total_row",)
            )
    
    def _process_productivity_metrics(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Process raw productivity sessions into aggregated data."""
        total_duration = 0
        total_words = 0
        
        for session in sessions:
            total_duration += session.get('duration', 0)
            total_words += session.get('words_written', 0)
        
        return {
            "total_duration": total_duration,
            "total_words": total_words,
            "num_sessions": len(sessions)
        }
    
    def _populate_productivity_tree(self, sessions: List[Dict]):
        """Populate the productivity tree with session data."""
        if not self.productivity_tree:
            return
            
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
    
    def _format_duration(self, seconds):
        """Format duration in seconds to readable string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _create_summary_labels(self, parent: ttk.Frame, summary_data: List[Tuple[str, str]]):
        """Create standardized summary labels in a grid layout."""
        for i, (label, value) in enumerate(summary_data):
            ttk.Label(parent, text=label).grid(
                row=i, column=0, sticky="w", pady=2
            )
            ttk.Label(
                parent,
                text=value,
                font=StandardComponents.BODY_FONT + ("bold",)
            ).grid(row=i, column=1, sticky="e", pady=2)
        
        return len(summary_data)  # Return next available row
    
    def _add_cost_estimation(self, parent: ttk.Frame, total_tokens: int, start_row: int):
        """Add cost estimation section to token summary."""
        estimated_cost = total_tokens * 0.00002  # Rough estimate
        
        ttk.Label(parent, text="Estimated cost (USD):").grid(
            row=start_row, column=0, sticky="w", pady=(10, 2)
        )
        ttk.Label(
            parent,
            text=f"${estimated_cost:.4f}",
            font=StandardComponents.BODY_FONT + ("bold",),
            foreground=self.get_theme_color("success_text", "#006600")
        ).grid(row=start_row, column=1, sticky="e", pady=(10, 2))
        
        # Disclaimer
        ttk.Label(
            parent,
            text="*Cost estimate is approximate and may vary by provider",
            font=StandardComponents.SMALL_FONT,
            foreground=self.get_theme_color("muted_text", "#666666")
        ).grid(row=start_row + 1, column=0, columnspan=2, pady=(5, 0))
    
    def _update_token_summary(self, total_input: int, total_output: int, num_days: int):
        """Update the token usage summary statistics."""
        if not self.token_summary_inner:
            return
            
        # Clear existing summary widgets
        for widget in self.token_summary_inner.winfo_children():
            widget.destroy()
        
        total_tokens = total_input + total_output
        avg_per_day = total_tokens / max(num_days, 1)
        
        # Create basic summary data
        summary_data = [
            ("Days with activity:", f"{num_days}"),
            ("Total input tokens:", f"{total_input:,}"),
            ("Total output tokens:", f"{total_output:,}"),
            ("Total tokens:", f"{total_tokens:,}"),
            ("Average per day:", f"{avg_per_day:,.1f}")
        ]
        
        next_row = self._create_summary_labels(self.token_summary_inner, summary_data)
        
        # Add cost estimation if there are tokens
        if total_tokens > 0:
            self._add_cost_estimation(self.token_summary_inner, total_tokens, next_row)
    
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
        
        # Create summary data
        summary_data = [
            ("Total sessions:", f"{num_sessions}"),
            ("Total time:", self._format_duration(total_duration)),
            ("Total words written:", f"{total_words:,}"),
            ("Average productivity:", f"{avg_productivity:.1f} words/hour"),
            ("Average session:", self._format_duration(avg_session_duration))
        ]
        
        self._create_summary_labels(self.productivity_summary_inner, summary_data)
    
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.token_tree:
            self.token_tree.focus_set()