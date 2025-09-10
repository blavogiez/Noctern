"""
Logs console for Noctern - provides logging functionality.
This is the logging system used throughout the application.
"""

import sys
import datetime
from typing import Optional

# Global console state
_console_initialized = False
_min_level = 'INFO'
_root_window = None

# Log level hierarchy
_LOG_LEVELS = {
    'TRACE': 0,
    'DEBUG': 1, 
    'INFO': 2,
    'WARNING': 3,
    'ERROR': 4,
    'SUCCESS': 5,
    'ACTION': 6
}

def initialize(root_window):
    """Initialize the logs console with the root window."""
    global _console_initialized, _root_window
    _console_initialized = True
    _root_window = root_window
    log("Logs console initialized", 'INFO')

def set_min_level(level: str):
    """Set minimum log level to display."""
    global _min_level
    if level in _LOG_LEVELS:
        _min_level = level
        log(f"Logs console level set to {level}", 'INFO')

def log(message: str, level: str = 'INFO', source: Optional[str] = None):
    """
    Log a message to console with proper formatting.
    
    Args:
        message: Message to log
        level: Log level (TRACE, DEBUG, INFO, WARNING, ERROR, SUCCESS, ACTION)
        source: Optional source identifier
    """
    if not _should_log(level):
        return
        
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Color codes for different levels
    colors = {
        'TRACE': '\033[90m',     # Gray
        'DEBUG': '\033[94m',     # Blue  
        'INFO': '\033[96m',      # Cyan
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'SUCCESS': '\033[92m',   # Green
        'ACTION': '\033[95m',    # Magenta
    }
    
    reset_color = '\033[0m'
    color = colors.get(level, '\033[0m')
    
    source_str = f"[{source}] " if source else ""
    formatted_message = f"{color}[{timestamp}] {level} {source_str}{message}{reset_color}"
    
    # Print to stdout/stderr based on level
    if level in ['ERROR', 'WARNING']:
        print(formatted_message, file=sys.stderr)
    else:
        print(formatted_message)

def _should_log(level: str) -> bool:
    """Check if message should be logged based on minimum level."""
    if not _console_initialized:
        return True  # Always log if not initialized
        
    current_level = _LOG_LEVELS.get(level, 2)
    min_level = _LOG_LEVELS.get(_min_level, 2)
    
    return current_level >= min_level

# Convenience functions
def trace(message: str, source: Optional[str] = None):
    """Log trace message."""
    log(message, 'TRACE', source)

def debug(message: str, source: Optional[str] = None):
    """Log debug message."""
    log(message, 'DEBUG', source)

def info(message: str, source: Optional[str] = None):
    """Log info message."""
    log(message, 'INFO', source)

def warning(message: str, source: Optional[str] = None):
    """Log warning message."""
    log(message, 'WARNING', source)

def error(message: str, source: Optional[str] = None):
    """Log error message."""
    log(message, 'ERROR', source)

def success(message: str, source: Optional[str] = None):
    """Log success message."""
    log(message, 'SUCCESS', source)

def action(message: str, source: Optional[str] = None):
    """Log action message."""
    log(message, 'ACTION', source)