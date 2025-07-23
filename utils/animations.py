"""
This module provides functions for creating simple, time-based animations
on Tkinter widgets.
"""

def move_widget(widget, end_y, duration=120):
    """
    Smoothly animates a widget's vertical position.

    Args:
        widget (tk.Widget): The widget to animate.
        end_y (int): The target final y-coordinate.
        duration (int): The total duration of the animation in milliseconds.
    """
    start_y = widget.winfo_y()
    delta_y = end_y - start_y
    
    # Use a smaller interval for smoother animation
    interval = 10 
    steps = duration // interval

    if steps == 0:
        widget.place(y=end_y)
        return

    def _step(step):
        if step > steps:
            # Ensure the final position is exact
            widget.place(y=end_y)
            return
        
        # Easing function (ease-out)
        progress = step / steps
        ease_progress = 1 - (1 - progress) ** 3
        
        new_y = start_y + (delta_y * ease_progress)
        widget.place(y=int(new_y))
        
        widget.after(interval, lambda: _step(step + 1))

    _step(0)
