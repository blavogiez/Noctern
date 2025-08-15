"""Provide simple animation utilities for Tkinter widgets."""

def flash_widget(widget, flash_color, original_color, duration_ms=300, steps=6):
    """Flash widget background color for visual feedback."""
    if not widget or not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
        return

    try:
        # Ensure steps is even number for symmetrical flash
        if steps % 2 != 0:
            steps += 1
        
        half_steps = steps // 2
        delay = duration_ms // steps

        # Handle ttk widgets differently from regular tk widgets
        if hasattr(widget, 'configure'):
            # For ttk widgets, use style configuration
            if hasattr(widget, 'cget') and hasattr(widget, 'winfo_class'):
                # Flash to target color
                for i in range(half_steps):
                    widget.after(i * delay, lambda w=widget, c=flash_color: _set_widget_color(w, c))
                
                # Return to original color
                for i in range(half_steps, steps):
                    widget.after(i * delay, lambda w=widget, c=original_color: _set_widget_color(w, c))
            else:
                # Flash to target color
                for i in range(half_steps):
                    widget.after(i * delay, lambda w=widget, c=flash_color: _set_widget_color(w, c))
                
                # Return to original color
                for i in range(half_steps, steps):
                    widget.after(i * delay, lambda w=widget, c=original_color: _set_widget_color(w, c))
                    
    except Exception:
        # Failsafe: ensure widget has original color if anything goes wrong
        if widget.winfo_exists():
            _set_widget_color(widget, original_color)

def _set_widget_color(widget, color):
    """Set widget color appropriately for ttk or tk widgets."""
    try:
        if hasattr(widget, 'winfo_class'):
            widget_class = widget.winfo_class()
            if widget_class in ['TFrame', 'TLabel', 'TButton', 'TEntry']:
                # For ttk widgets, we need to configure the style
                import ttkbootstrap as ttk
                style = ttk.Style()
                widget_style = widget.cget('style') if widget.cget('style') else widget_class
                # Create a temporary style with the flash color
                if widget_class == 'TFrame':
                    style.configure(f"Flash.{widget_style}", background=color)
                elif widget_class == 'TLabel':
                    style.configure(f"Flash.{widget_style}", background=color)
                elif widget_class == 'TButton':
                    style.configure(f"Flash.{widget_style}", background=color)
                elif widget_class == 'TEntry':
                    style.configure(f"Flash.{widget_style}", fieldbackground=color)
                widget.configure(style=f"Flash.{widget_style}")
            else:
                # For regular tk widgets
                widget.configure(background=color)
        else:
            # For regular tk widgets
            widget.configure(background=color)
    except Exception:
        # If we can't set the color, just continue
        pass

def move_widget(widget, y_pos, duration_ms=100, steps=10):
    """Animate vertical movement of widget."""
    if not widget or not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
        return

    try:
        start_y = widget.place_info().get('y')
        if start_y is None:
            return  # Cannot animate if not placed with .place()

        start_y = int(start_y)
        y_change = y_pos - start_y
        delay = duration_ms // steps

        for i in range(steps + 1):
            current_y = start_y + (y_change * i // steps)
            widget.after(i * delay, lambda y=current_y: widget.place(y=y))
            
    except Exception:
        # Failsafe: move widget directly to final position if anything goes wrong
        if widget.winfo_exists():
            widget.place(y=y_pos)
