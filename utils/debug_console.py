"""Manage dedicated debug console window for displaying application logs."""

import tkinter as tk
from tkinter import ttk
import datetime

class DebugConsole:
    def __init__(self):
        """Initialize DebugConsole instance."""
        self.console_window = None
        self.text_widget = None
        # Define color codes for different log levels
        self.levels = {
            'DEBUG': '#9E9E9E',   # Grey for debugging information
            'TRACE': '#616161',   # Darker grey for detailed tracing
            'INFO': '#FFFFFF',    # White for informational messages
            'ACTION': '#81D4FA',  # Light blue for user or system actions
            'SUCCESS': '#A5D6A7', # Green for successful operations
            'WARNING': '#FFD54F', # Amber for potential issues
            'ERROR': '#EF9A9A',   # Red for critical errors
            'CONFIG': '#CE93D8',  # Purple for configuration messages
        }
        # Define level order for filtering
        self.level_order = ['TRACE', 'DEBUG', 'INFO', 'ACTION', 'SUCCESS', 'WARNING', 'ERROR', 'CONFIG']
        # Set default minimum level
        self.min_level = 'DEBUG'  # Show DEBUG and above by default

    def initialize(self, root):
        """Initialize console with main application root window."""
        self.root = root

    def set_min_level(self, level):
        """Set minimum log level to display in console."""
        if level in self.levels:
            self.min_level = level

    def _should_show_level(self, level):
        """Determine if log level should be shown based on minimum level setting."""
        try:
            level_idx = self.level_order.index(level.upper())
            min_idx = self.level_order.index(self.min_level.upper())
            return level_idx >= min_idx
        except ValueError:
            # If level not in known levels, show by default
            return True

    def show_console(self):
        """Display debug console window."""
        # If console window is already open, bring to front
        if self.console_window and self.console_window.winfo_exists():
            self.console_window.lift()
            return

        # Create new top-level window for debug console
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("Debug Console")
        self.console_window.geometry("900x400")
        self.console_window.configure(bg="#1e1e1e")  # Set background color for window

        # Create text widget to display log messages
        self.text_widget = tk.Text(self.console_window, wrap="word", bg="#1e1e1e", fg="#d4d4d4",
                                   font=("Consolas", 10), relief=tk.FLAT, borderwidth=0)
        self.text_widget.pack(expand=True, fill="both", padx=5, pady=5)

        # Configure text tags for each log level with specific colors
        for level, color in self.levels.items():
            self.text_widget.tag_configure(level, foreground=color)

        # Set protocol for closing window to call hide_console
        self.console_window.protocol("WM_DELETE_WINDOW", self.hide_console)

    def hide_console(self):
        """Hide and destroy debug console window."""
        if self.console_window:
            self.console_window.destroy()
            self.console_window = None  # Reset reference to indicate window is closed

    def log(self, message, level='INFO'):
        """Log message to debug console with specified level."""
        # Check if level should be shown
        if not self._should_show_level(level):
            return
            
        # Fallback to stdout if console window not active or does not exist
        if not self.console_window or not self.text_widget or not self.console_window.winfo_exists():
            print(f"[{level}] {message}")
            return

        # Generate timestamp for log entry
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Format complete log line
        log_line = f"{timestamp} [{level.upper()}] {message}\n"

        # Temporarily enable text widget to insert new log line
        self.text_widget.config(state="normal")
        self.text_widget.insert(tk.END, log_line, level)
        # Disable text widget to prevent user interaction
        self.text_widget.config(state="disabled")
        # Automatically scroll to end to show latest log
        self.text_widget.see(tk.END)

# Global instance and public API
# Create single globally accessible instance for application logging

_console_instance = DebugConsole()

# Expose public methods for easy access throughout application
initialize = _console_instance.initialize
show_console = _console_instance.show_console
hide_console = _console_instance.hide_console
log = _console_instance.log
set_min_level = _console_instance.set_min_level