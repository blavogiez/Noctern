"""
File-based productivity metrics system for AutomaTeX.
Tracks session time, word count, and productivity per file.
"""

from .session_tracker import SessionTracker
from .status_display import MetricsStatusDisplay
from .file_metrics_dialog import show_file_metrics_dialog

__all__ = ['SessionTracker', 'MetricsStatusDisplay', 'show_file_metrics_dialog']