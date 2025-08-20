"""Production-ready line numbers performance manager"""

import time
import weakref
from threading import Timer


class LineNumberUpdateManager:
    """Centralized manager for line number updates with performance optimizations
    
    Handles intelligent debouncing, prevents redundant updates, and manages
    update scheduling for optimal editor responsiveness without performance impact
    """
    
    def __init__(self):
        self._update_timers = weakref.WeakKeyDictionary()  # Active update timers per widget
        self._last_update_times = weakref.WeakKeyDictionary()  # Last update timestamps  
        self._debounce_delay = 16  # Milliseconds - targets 60fps for smooth experience
        
    def schedule_update(self, line_numbers_widget, force=False):
        """Schedule line numbers update with intelligent debouncing and throttling
        
        Args:
            line_numbers_widget: Target LineNumbers widget to update
            force: Skip throttling checks for immediate response scenarios
        """
        if not line_numbers_widget:
            return
            
        current_time = time.perf_counter()
        
        # Cancel existing timer to prevent redundant updates
        if line_numbers_widget in self._update_timers:
            try:
                self._update_timers[line_numbers_widget].cancel()
            except (AttributeError, KeyError):
                pass
        
        # Throttle rapid successive updates unless forced
        if not force:
            last_update = self._last_update_times.get(line_numbers_widget, 0)
            if current_time - last_update < 0.016:  # Maintain 60fps maximum rate
                return
        
        # Schedule delayed update for optimal performance
        def perform_update():
            try:
                if line_numbers_widget and hasattr(line_numbers_widget, 'redraw'):
                    line_numbers_widget.redraw()
                    self._last_update_times[line_numbers_widget] = time.perf_counter()
            except (AttributeError, RuntimeError):
                # Handle widget destruction gracefully
                pass
            finally:
                # Clean up timer reference
                self._update_timers.pop(line_numbers_widget, None)
        
        timer = Timer(self._debounce_delay / 1000, perform_update)
        timer.start()
        self._update_timers[line_numbers_widget] = timer
    
    def immediate_update(self, line_numbers_widget):
        """Force immediate update bypassing all throttling and debouncing
        
        Used for user-initiated actions requiring instant visual feedback
        such as zoom operations or manual refresh commands
        
        Args:
            line_numbers_widget: Target LineNumbers widget to update immediately
        """
        if line_numbers_widget and hasattr(line_numbers_widget, 'redraw'):
            line_numbers_widget.redraw()
            self._last_update_times[line_numbers_widget] = time.perf_counter()


# Global manager instance for application-wide line number coordination
_line_number_manager = LineNumberUpdateManager()

def schedule_line_number_update(line_numbers_widget, force=False):
    """Schedule optimized line number update with performance management
    
    Primary interface for routine line number updates during text editing
    
    Args:
        line_numbers_widget: Target widget to update
        force: Override throttling for time-sensitive updates
    """
    _line_number_manager.schedule_update(line_numbers_widget, force)

def force_line_number_update(line_numbers_widget):
    """Force immediate line number update for user-initiated actions
    
    Use for operations requiring instant visual feedback like zoom changes
    
    Args:
        line_numbers_widget: Target widget to update immediately
    """
    _line_number_manager.immediate_update(line_numbers_widget)