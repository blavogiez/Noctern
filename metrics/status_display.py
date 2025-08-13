"""
Status bar integration for session metrics.
Displays session time and provides access to metrics visualization.
"""

import tkinter as tk
from tkinter import ttk
from .session_tracker import SessionTracker
from .file_metrics_dialog import show_file_metrics_dialog


class MetricsStatusDisplay:
    """Manages the display of session metrics in the status bar."""
    
    def __init__(self, status_frame, root):
        self.status_frame = status_frame
        self.root = root
        self.tracker = None
        self.session_label = None
        self.metrics_button = None
        self.update_timer_id = None
        
        self._create_widgets()
        self._start_update_loop()
    
    def _create_widgets(self):
        """Create the status bar widgets for metrics."""
        # Create a frame for metrics display
        metrics_frame = ttk.Frame(self.status_frame)
        metrics_frame.pack(side="left", padx=(10, 0))
        
        # Session time label
        self.session_label = ttk.Label(
            metrics_frame, 
            text="Session: 0s", 
            font=("", 8)
        )
        self.session_label.pack(side="left")
        
        # Metrics button (small)
        self.metrics_button = ttk.Button(
            metrics_frame,
            text="📊",
            width=3,
            command=self._show_metrics_dialog
        )
        self.metrics_button.pack(side="left", padx=(5, 0))
        
        # Add tooltip to button
        self._create_tooltip(self.metrics_button, "View file productivity metrics")
    
    def _create_tooltip(self, widget, text):
        """Create a simple tooltip for a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = ttk.Label(tooltip, text=text, background="lightyellow", font=("", 8))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def set_current_file(self, file_path):
        """Set the current file being tracked."""
        if file_path:
            self.tracker = SessionTracker(file_path)
            self.metrics_button.config(state="normal")
        else:
            self.tracker = None
            self.metrics_button.config(state="disabled")
        
        # Reset display
        self._update_display()
    
    def update_word_count(self, word_count):
        """Update the word count for the current session."""
        if self.tracker:
            self.tracker.update_word_count(word_count)
    
    def save_current_session(self):
        """Save the current session data."""
        if self.tracker:
            self.tracker.save_session_metrics()
    
    def _update_display(self):
        """Update the session time display."""
        if self.tracker:
            summary = self.tracker.get_session_summary()
            duration_text = summary["duration_formatted"]
            words_typed = summary["words_typed"]
            
            if words_typed > 0:
                self.session_label.config(text=f"Session: {duration_text} | {words_typed} words")
            else:
                self.session_label.config(text=f"Session: {duration_text}")
        else:
            self.session_label.config(text="Session: --")
    
    def _start_update_loop(self):
        """Start the periodic update of the session display."""
        self._update_display()
        # Update every 5 seconds
        self.update_timer_id = self.root.after(5000, self._start_update_loop)
    
    def _show_metrics_dialog(self):
        """Show the metrics visualization dialog."""
        if self.tracker and self.tracker.file_path:
            # Save current session before showing dialog
            self.save_current_session()
            show_file_metrics_dialog(self.root, self.tracker.file_path)
    
    def destroy(self):
        """Clean up the metrics display."""
        if self.update_timer_id:
            self.root.after_cancel(self.update_timer_id)
        
        # Save final session data
        self.save_current_session()