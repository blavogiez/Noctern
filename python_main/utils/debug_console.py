import tkinter as tk
from tkinter import ttk
import datetime

class DebugConsole:
    """
    Manages a dedicated debug console window for displaying application logs.

    This class provides a graphical user interface (GUI) console that can display
    log messages with different severity levels, each identified by a distinct color.
    It acts as a centralized logging utility for the application, offering a more
    structured and visually distinct output than standard console prints.
    """
    def __init__(self):
        """
        Initializes the DebugConsole instance.

        Sets up the console window and text widget to None, as they are created
        dynamically when the console is shown. Defines a dictionary of log levels
        mapped to their respective hexadecimal color codes for display.
        """
        self.console_window = None
        self.text_widget = None
        # Define color codes for different log levels to enhance readability.
        self.levels = {
            'DEBUG': '#9E9E9E',   # Grey for detailed debugging information.
            'INFO': '#FFFFFF',    # White for general informational messages.
            'ACTION': '#81D4FA',  # Light Blue for user or system actions.
            'SUCCESS': '#A5D6A7', # Green for successful operations.
            'WARNING': '#FFD54F', # Amber for potential issues that are not errors.
            'ERROR': '#EF9A9A',   # Red for critical errors.
            'CONFIG': '#CE93D8',  # Purple for configuration-related messages.
        }

    def initialize(self, root):
        """
        Initializes the console with the main application root window.

        This method is crucial for associating the debug console's top-level window
        with the main application window, ensuring proper window management.

        Args:
            root (tk.Tk or tk.Toplevel): The root Tkinter window of the application.
        """
        self.root = root

    def show_console(self):
        """
        Displays the debug console window.

        If the console window already exists and is open, it brings it to the
        foreground. Otherwise, it creates a new Toplevel window, configures its
        appearance, and sets up the text widget for displaying logs. It also
        configures text tags for colored output based on log levels.
        """
        # If the console window is already open, bring it to the front.
        if self.console_window and self.console_window.winfo_exists():
            self.console_window.lift()
            return

        # Create a new top-level window for the debug console.
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("Debug Console")
        self.console_window.geometry("900x400")
        self.console_window.configure(bg="#1e1e1e") # Set background color for the window.

        # Create a text widget to display log messages.
        self.text_widget = tk.Text(self.console_window, wrap="word", bg="#1e1e1e", fg="#d4d4d4",
                                   font=("Consolas", 10), relief=tk.FLAT, borderwidth=0)
        self.text_widget.pack(expand=True, fill="both", padx=5, pady=5)

        # Configure text tags for each log level to apply specific foreground colors.
        for level, color in self.levels.items():
            self.text_widget.tag_configure(level, foreground=color)

        # Set the protocol for closing the window to call hide_console.
        self.console_window.protocol("WM_DELETE_WINDOW", self.hide_console)

    def hide_console(self):
        """
        Hides and destroys the debug console window.

        This method is called when the user closes the console window, ensuring
        that the window resources are properly released.
        """
        if self.console_window:
            self.console_window.destroy()
            self.console_window = None # Reset the reference to indicate the window is closed.

    def log(self, message, level='INFO'):
        """
        Logs a message to the debug console with a specified level.

        If the console window is not active, the message is printed to the standard
        output (stdout) as a fallback. Otherwise, the message is formatted with a
        timestamp and the log level, inserted into the text widget, and scrolled
        to the end. The text widget is temporarily set to 'normal' state for insertion
        and then back to 'disabled' to prevent user editing.

        Args:
            message (str): The log message to display.
            level (str, optional): The severity level of the log message (e.g., 'INFO', 'ERROR').
                                   Defaults to 'INFO'.
        """
        # Fallback to stdout if the console window is not active or does not exist.
        if not self.console_window or not self.text_widget or not self.console_window.winfo_exists():
            print(f"[{level}] {message}")
            return

        # Generate a timestamp for the log entry.
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Format the complete log line.
        log_line = f"{timestamp} [{level.upper()}] {message}\n"

        # Temporarily enable the text widget to insert the new log line.
        self.text_widget.config(state="normal")
        self.text_widget.insert(tk.END, log_line, level)
        # Disable the text widget to prevent user interaction.
        self.text_widget.config(state="disabled")
        # Automatically scroll to the end of the text widget to show the latest log.
        self.text_widget.see(tk.END)

# --- Global Instance and Public API ---
# This section creates a single, globally accessible instance of the DebugConsole
# and exposes its core functionalities as direct imports. This design pattern
# ensures that all parts of the application can log messages to the same console
# without needing to pass the console instance around.

_console_instance = DebugConsole()

# Expose the public methods of the DebugConsole instance for easy access throughout the application.
initialize = _console_instance.initialize
show_console = _console_instance.show_console
hide_console = _console_instance.hide_console
log = _console_instance.log