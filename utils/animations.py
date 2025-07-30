"""
This module provides simple animation utilities for Tkinter widgets.
"""

def flash_widget(widget, flash_color, original_color, duration_ms=300, steps=6):
    """
    Briefly flashes a widget's background color for visual feedback.

    Args:
        widget: The Tkinter widget to animate.
        flash_color (str): The color to flash to.
        original_color (str): The widget's normal background color.
        duration_ms (int): Total duration of the flash animation.
        steps (int): Number of steps in the animation (must be even).
    """
    if not widget or not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
        return

    try:
        # Ensure steps is an even number for a symmetrical flash
        if steps % 2 != 0:
            steps += 1
        
        half_steps = steps // 2
        delay = duration_ms // steps

        # Flash to the target color
        for i in range(half_steps):
            widget.after(i * delay, lambda: widget.config(background=flash_color))
        
        # Return to the original color
        for i in range(half_steps, steps):
            widget.after(i * delay, lambda: widget.config(background=original_color))
            
    except Exception:
        # Failsafe: if anything goes wrong, ensure the widget has its original color
        if widget.winfo_exists():
            widget.config(background=original_color)

def move_widget(widget, y_pos, duration_ms=100, steps=10):
    """
    Animates the vertical movement of a widget.

    Args:
        widget: The Tkinter widget to move.
        y_pos (int): The target final y-position.
        duration_ms (int): Total duration of the movement animation.
        steps (int): Number of steps in the animation.
    """
    if not widget or not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
        return

    try:
        start_y = widget.place_info().get('y')
        if start_y is None:
            return # Cannot animate if not placed with .place()

        start_y = int(start_y)
        y_change = y_pos - start_y
        delay = duration_ms // steps

        for i in range(steps + 1):
            current_y = start_y + (y_change * i // steps)
            widget.after(i * delay, lambda y=current_y: widget.place(y=y))
            
    except Exception:
        # Failsafe: if anything goes wrong, move widget directly to the final position
        if widget.winfo_exists():
            widget.place(y=y_pos)
