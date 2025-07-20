"""
This module provides utility functions for screen-related operations,
such as detecting multiple monitors.
"""

import screeninfo
from utils import debug_console

def get_monitors():
    """Returns a list of all connected monitors."""
    try:
        return screeninfo.get_monitors()
    except screeninfo.common.ScreenInfoError as e:
        debug_console.log(f"Could not get screen info: {e}", level='WARNING')
        return []

def has_multiple_monitors() -> bool:
    """
    Checks if more than one monitor is connected to the system.
    """
    monitors = get_monitors()
    debug_console.log(f"Detected monitors: {len(monitors)}", level='INFO')
    return len(monitors) > 1

def get_secondary_monitor_index() -> int | None:
    """
    Returns the 1-based index of a secondary monitor, if one exists.
    
    Returns:
        The index (1, 2, ...) of a non-primary monitor, or None if only one
        monitor is found or an error occurs.
    """
    monitors = get_monitors()
    if len(monitors) < 2:
        return None
    
    for i, monitor in enumerate(monitors):
        if not monitor.is_primary:
            # SumatraPDF monitor indices are 1-based.
            debug_console.log(f"Found secondary monitor at index {i+1}", level='INFO')
            return i + 1
            
    # Fallback: if no monitor is explicitly primary, return the second one.
    debug_console.log("No primary monitor designated. Falling back to monitor 2.", level='INFO')
    return 2

