"""Provide utility functions for screen-related operations."""

import screeninfo
from utils import logs_console

def get_monitors():
    """Return list of all connected monitors."""
    try:
        return screeninfo.get_monitors()
    except screeninfo.common.ScreenInfoError as e:
        logs_console.log(f"Could not get screen info: {e}", level='WARNING')
        return []

def has_multiple_monitors() -> bool:
    """Check if more than one monitor is connected to system."""
    monitors = get_monitors()
    logs_console.log(f"Detected monitors: {len(monitors)}", level='INFO')
    return len(monitors) > 1

def get_secondary_monitor_index() -> int | None:
    """Return 1-based index of secondary monitor if one exists."""
    monitors = get_monitors()
    if len(monitors) < 2:
        return None
    
    for i, monitor in enumerate(monitors):
        if not monitor.is_primary:
            # sumatrapdf monitor indices are 1-based
            logs_console.log(f"Found secondary monitor at index {i+1}", level='INFO')
            return i + 1
            
    # fallback: if no monitor is explicitly primary, return second one
    logs_console.log("No primary monitor designated. Falling back to monitor 2.", level='INFO')
    return 2

import tkinter as tk

def show_screen_numbers(root):
    """Display large number on each monitor for identification."""
    monitors = get_monitors()
    if not monitors:
        logs_console.log("No monitors found to display numbers on.", level='WARNING')
        return

    for i, monitor in enumerate(monitors):
        screen_num = i + 1
        
        # create transparent, borderless window
        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        
        # center id window on monitor
        win_width = 200
        win_height = 150
        pos_x = monitor.x + (monitor.width // 2) - (win_width // 2)
        pos_y = monitor.y + (monitor.height // 2) - (win_height // 2)
        win.geometry(f"{win_width}x{win_height}+{pos_x}+{pos_y}")

        # make window bg transparent
        win.config(bg='black')
        win.attributes('-transparentcolor', 'black')

        # add screen number label
        label = tk.Label(
            win, 
            text=str(screen_num), 
            font=('Arial', 80, 'bold'), 
            fg='white', 
            bg='black'
        )
        label.pack(pady=20, expand=True, fill='both')

        # schedule window to close after 2 secs
        win.after(2000, win.destroy)

