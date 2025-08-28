"""Integrate session metrics display into status bar."""

import tkinter as tk
from tkinter import ttk
from .session_tracker import SessionTracker
# Import dynamically to avoid circular imports


class MetricsStatusDisplay:
    """Manage session metrics display in status bar."""
    
    def __init__(self, status_frame, root):
        self.status_frame = status_frame
        self.root = root
        self.tracker = None
        self.session_label = None
        self.update_timer_id = None
        
        self._create_widgets()
        self._start_update_loop()
    
    def _create_widgets(self):
        """Create status bar widgets for metrics."""
        # Create frame for metrics display
        metrics_frame = ttk.Frame(self.status_frame)
        metrics_frame.pack(side="left", padx=(10, 0))
        
        # Session time label
        self.session_label = ttk.Label(
            metrics_frame, 
            text="Session: 0s", 
            font=("Segoe UI", 9)
        )
        self.session_label.pack(side="left")
        
    
    
    def set_current_file(self, file_path):
        """Set current file being tracked."""
        if file_path:
            self.tracker = SessionTracker(file_path)
        else:
            self.tracker = None
        
        # Reset display
        self._update_display()
    
    def update_word_count(self, word_count):
        """Update word count for current session."""
        if self.tracker:
            self.tracker.update_word_count(word_count)
    
    def save_current_session(self):
        """Save current session data."""
        if self.tracker:
            self.tracker.save_session_metrics()
    
    def _update_display(self):
        """Update session time display."""
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
        """Start periodic update of session display."""
        self._update_display()
        # Update every 5 seconds
        self.update_timer_id = self.root.after(5000, self._start_update_loop)
    
    
    def destroy(self):
        """Clean up metrics display."""
        if self.update_timer_id:
            self.root.after_cancel(self.update_timer_id)
        
        # Save final session data
        self.save_current_session()