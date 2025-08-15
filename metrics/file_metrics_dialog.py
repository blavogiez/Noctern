"""Visualize file-specific productivity metrics and session data."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import os
from .session_tracker import SessionTracker

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class FileMetricsDialog:
    """Display file-specific productivity metrics in dialog."""
    
    def __init__(self, parent, file_path=None):
        self.parent = parent
        self.file_path = file_path
        self.dialog = None
        self.tracker = None
        
        if file_path:
            self.tracker = SessionTracker(file_path)
    
    def show_dialog(self):
        """Show metrics dialog."""
        if not self.file_path:
            tk.messagebox.showwarning(
                "No File Selected", 
                "Please open a file to view its metrics."
            )
            return
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Metrics - {os.path.basename(self.file_path)}")
        self.dialog.geometry("900x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._load_and_display_data()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Overview tab
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="Overview")
        self._create_overview_tab(overview_frame)
        
        # Sessions tab
        sessions_frame = ttk.Frame(notebook)
        notebook.add(sessions_frame, text="Sessions")
        self._create_sessions_tab(sessions_frame)
        
        # Charts tab if matplotlib available
        if MATPLOTLIB_AVAILABLE:
            charts_frame = ttk.Frame(notebook)
            notebook.add(charts_frame, text="Charts")
            self._create_charts_tab(charts_frame)
        
        # Close button
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=5)
        
        ttk.Button(
            button_frame, 
            text="Close", 
            command=self.dialog.destroy
        ).pack(side="right")
        
        ttk.Button(
            button_frame, 
            text="Refresh", 
            command=self._refresh_data
        ).pack(side="right", padx=(0, 5))
    
    def _create_overview_tab(self, parent):
        """Create overview tab with summary statistics."""
        # Summary frame
        summary_frame = ttk.LabelFrame(parent, text="File Summary", padding=10)
        summary_frame.pack(fill="x", padx=5, pady=5)
        
        # Create summary labels
        self.summary_labels = {}
        summary_items = [
            ("File", "file_name"),
            ("Total Sessions", "session_count"),
            ("Total Time", "total_time"),
            ("Total Words Typed", "total_words"),
            ("Average Productivity", "avg_productivity"),
            ("Best Session", "best_session"),
            ("Last Session", "last_session")
        ]
        
        for i, (label, key) in enumerate(summary_items):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(summary_frame, text=f"{label}:", font=("Segoe UI", 9)).grid(
                row=row, column=col, sticky="w", padx=(0, 5), pady=2
            )
            
            self.summary_labels[key] = ttk.Label(summary_frame, text="Loading...")
            self.summary_labels[key].grid(
                row=row, column=col+1, sticky="w", padx=(0, 20), pady=2
            )
        
        # Recent activity frame
        activity_frame = ttk.LabelFrame(parent, text="Recent Activity (Last 7 Days)", padding=10)
        activity_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Activity treeview
        columns = ("Date", "Sessions", "Time", "Words", "Productivity")
        self.activity_tree = ttk.Treeview(activity_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.activity_tree.heading(col, text=col)
            self.activity_tree.column(col, width=120, anchor="center")
        
        scrollbar = ttk.Scrollbar(activity_frame, orient="vertical", command=self.activity_tree.yview)
        self.activity_tree.configure(yscrollcommand=scrollbar.set)
        
        self.activity_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_sessions_tab(self, parent):
        """Create sessions tab with detailed session list."""
        # Sessions treeview
        columns = ("Start Time", "Duration", "Words Typed", "Productivity", "Date")
        self.sessions_tree = ttk.Treeview(parent, columns=columns, show="headings")
        
        # Configure columns
        self.sessions_tree.heading("Start Time", text="Start Time")
        self.sessions_tree.heading("Duration", text="Duration")
        self.sessions_tree.heading("Words Typed", text="Words Typed")
        self.sessions_tree.heading("Productivity", text="WPM")
        self.sessions_tree.heading("Date", text="Date")
        
        self.sessions_tree.column("Start Time", width=150)
        self.sessions_tree.column("Duration", width=100)
        self.sessions_tree.column("Words Typed", width=100)
        self.sessions_tree.column("Productivity", width=80)
        self.sessions_tree.column("Date", width=100)
        
        # Scrollbar for sessions
        sessions_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.sessions_tree.yview)
        self.sessions_tree.configure(yscrollcommand=sessions_scrollbar.set)
        
        self.sessions_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        sessions_scrollbar.pack(side="right", fill="y", pady=5)
    
    def _create_charts_tab(self, parent):
        """Create charts tab with productivity visualizations."""
        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text="Matplotlib not available. Install matplotlib to view charts.").pack(expand=True)
            return
            
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
    
    def _load_and_display_data(self):
        """Load metrics data and update all displays."""
        if not self.tracker:
            return
        
        metrics = self.tracker.get_historical_metrics()
        sessions = metrics.get("sessions", [])
        
        self._update_overview(sessions)
        self._update_sessions_list(sessions)
        if MATPLOTLIB_AVAILABLE:
            self._update_charts(sessions)
    
    def _update_overview(self, sessions):
        """Update overview tab with summary data."""
        if not sessions:
            for label in self.summary_labels.values():
                label.config(text="No data")
            return
        
        # Calculate summary statistics
        total_time = sum(s.get("duration_seconds", 0) for s in sessions)
        total_words = sum(s.get("words_typed", 0) for s in sessions)
        avg_productivity = sum(s.get("productivity_score", 0) for s in sessions) / len(sessions)
        
        # Find best session
        best_session = max(sessions, key=lambda s: s.get("productivity_score", 0))
        last_session = max(sessions, key=lambda s: s.get("start_time", 0))
        
        # Update labels
        self.summary_labels["file_name"].config(text=os.path.basename(self.file_path))
        self.summary_labels["session_count"].config(text=str(len(sessions)))
        self.summary_labels["total_time"].config(text=self._format_duration(total_time))
        self.summary_labels["total_words"].config(text=str(total_words))
        self.summary_labels["avg_productivity"].config(text=f"{avg_productivity:.1f} WPM")
        self.summary_labels["best_session"].config(
            text=f"{best_session.get('productivity_score', 0):.1f} WPM"
        )
        self.summary_labels["last_session"].config(
            text=datetime.fromtimestamp(last_session.get("start_time", 0)).strftime("%Y-%m-%d %H:%M")
        )
        
        # Update recent activity
        self._update_recent_activity(sessions)
    
    def _update_recent_activity(self, sessions):
        """Update recent activity table."""
        # Clear existing items
        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
        
        # Get last 7 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        daily_data = {}
        for session in sessions:
            session_date = datetime.fromtimestamp(session.get("start_time", 0)).date()
            if start_date.date() <= session_date <= end_date.date():
                date_str = session_date.strftime("%Y-%m-%d")
                if date_str not in daily_data:
                    daily_data[date_str] = {
                        "sessions": 0,
                        "time": 0,
                        "words": 0,
                        "productivity": []
                    }
                
                daily_data[date_str]["sessions"] += 1
                daily_data[date_str]["time"] += session.get("duration_seconds", 0)
                daily_data[date_str]["words"] += session.get("words_typed", 0)
                daily_data[date_str]["productivity"].append(session.get("productivity_score", 0))
        
        # Insert data into treeview
        for date_str in sorted(daily_data.keys(), reverse=True):
            data = daily_data[date_str]
            avg_productivity = sum(data["productivity"]) / len(data["productivity"]) if data["productivity"] else 0
            
            self.activity_tree.insert("", "end", values=(
                date_str,
                data["sessions"],
                self._format_duration(data["time"]),
                data["words"],
                f"{avg_productivity:.1f}"
            ))
    
    def _update_sessions_list(self, sessions):
        """Update sessions list."""
        # Clear existing items
        for item in self.sessions_tree.get_children():
            self.sessions_tree.delete(item)
        
        # Sort sessions by start time (newest first)
        sorted_sessions = sorted(sessions, key=lambda s: s.get("start_time", 0), reverse=True)
        
        for session in sorted_sessions:
            start_time = datetime.fromtimestamp(session.get("start_time", 0))
            
            self.sessions_tree.insert("", "end", values=(
                start_time.strftime("%Y-%m-%d %H:%M:%S"),
                self._format_duration(session.get("duration_seconds", 0)),
                session.get("words_typed", 0),
                f"{session.get('productivity_score', 0):.1f}",
                start_time.strftime("%Y-%m-%d")
            ))
    
    def _update_charts(self, sessions):
        """Update productivity charts."""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.fig.clear()
        
        if not sessions:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "No data to display", ha="center", va="center", transform=ax.transAxes)
            self.canvas.draw()
            return
        
        # Create subplots
        gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 1. Productivity over time
        ax1 = self.fig.add_subplot(gs[0, :])
        dates = [datetime.fromtimestamp(s.get("start_time", 0)) for s in sessions]
        productivity = [s.get("productivity_score", 0) for s in sessions]
        
        ax1.plot(dates, productivity, marker='o', linewidth=2, markersize=4)
        ax1.set_title("Productivity Over Time (Words per Minute)")
        ax1.set_ylabel("WPM")
        ax1.grid(True, alpha=0.3)
        
        # 2. Session duration distribution
        ax2 = self.fig.add_subplot(gs[1, 0])
        durations = [s.get("duration_seconds", 0) / 60 for s in sessions]  # Convert to minutes
        ax2.hist(durations, bins=min(10, len(sessions)), alpha=0.7, color='skyblue')
        ax2.set_title("Session Duration Distribution")
        ax2.set_xlabel("Duration (minutes)")
        ax2.set_ylabel("Frequency")
        
        # 3. Words typed per session
        ax3 = self.fig.add_subplot(gs[1, 1])
        words_typed = [s.get("words_typed", 0) for s in sessions]
        ax3.hist(words_typed, bins=min(10, len(sessions)), alpha=0.7, color='lightgreen')
        ax3.set_title("Words Typed per Session")
        ax3.set_xlabel("Words Typed")
        ax3.set_ylabel("Frequency")
        
        self.canvas.draw()
    
    def _format_duration(self, seconds):
        """Format duration in human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _refresh_data(self):
        """Refresh displayed data."""
        if self.tracker:
            self._load_and_display_data()


def show_file_metrics_dialog(parent, file_path=None):
    """Show file metrics dialog."""
    dialog = FileMetricsDialog(parent, file_path)
    dialog.show_dialog()