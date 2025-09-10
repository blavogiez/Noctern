"""
Advanced performance optimizer for the Noctern editor.
Manages intelligent refresh batching, deduplication, and adaptive updates for large files.
"""

import time
import hashlib
import weakref
import threading
import tkinter as tk
from collections import defaultdict, namedtuple
from tkinter import TclError
from utils import logs_console

# Performance thresholds and configuration
class PerfConfig:
    LARGE_FILE_THRESHOLD = 2000          # Lines for large file detection
    HUGE_FILE_THRESHOLD = 10000          # Lines for huge file detection  
    VIEWPORT_BUFFER_LINES = 50           # Buffer around visible area
    
    # Debounce delays (ms)
    SMALL_FILE_DELAY = 100               # < 2000 lines
    LARGE_FILE_DELAY = 300               # 2000-10000 lines
    HUGE_FILE_DELAY = 1000               # > 10000 lines
    
    # Update intervals for different components
    SYNTAX_UPDATE_INTERVAL = 200         # Syntax highlighting
    OUTLINE_UPDATE_INTERVAL = 500        # Document outline  
    STATUS_UPDATE_INTERVAL = 100         # Status bar
    LINE_NUMBERS_UPDATE_INTERVAL = 50    # Line numbers
    
    # Cache sizes
    MAX_CONTENT_CACHE_SIZE = 10          # Content hashes
    MAX_OUTLINE_CACHE_SIZE = 15          # Parsed outlines
    MAX_WORDCOUNT_CACHE_SIZE = 20        # Word counts

# Update types for selective processing
class UpdateType:
    SYNTAX = 'syntax'
    OUTLINE = 'outline' 
    STATUS = 'status'
    LINE_NUMBERS = 'line_numbers'
    ALL = 'all'

# Change context for intelligent updates
ChangeContext = namedtuple('ChangeContext', [
    'editor', 'change_type', 'start_line', 'end_line', 
    'content_hash', 'line_count', 'timestamp'
])

class ContentCache:
    """Intelligent caching system for editor content and derived data."""
    
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.content_hashes = {}        # editor -> content_hash
        self.outline_cache = {}         # content_hash -> parsed_outline
        self.wordcount_cache = {}       # content_hash -> word_count
        self.line_count_cache = {}      # content_hash -> line_count
        self.access_times = defaultdict(float)
        
    def get_content_hash(self, content):
        """Generate fast hash for content."""
        return hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()[:16]
    
    def is_content_changed(self, editor, content):
        """Check if content has changed since last cache."""
        new_hash = self.get_content_hash(content)
        old_hash = self.content_hashes.get(editor)
        
        if old_hash != new_hash:
            self.content_hashes[editor] = new_hash
            self._evict_if_needed()
            return True, new_hash
        return False, new_hash
    
    def cache_outline(self, content_hash, outline_data):
        """Cache parsed outline data."""
        self.outline_cache[content_hash] = outline_data
        self.access_times[content_hash] = time.time()
        
    def get_cached_outline(self, content_hash):
        """Get cached outline if available."""
        if content_hash in self.outline_cache:
            self.access_times[content_hash] = time.time()
            return self.outline_cache[content_hash]
        return None
    
    def cache_wordcount(self, content_hash, word_count):
        """Cache word count."""
        self.wordcount_cache[content_hash] = word_count
        self.access_times[content_hash] = time.time()
        
    def get_cached_wordcount(self, content_hash):
        """Get cached word count if available."""
        if content_hash in self.wordcount_cache:
            self.access_times[content_hash] = time.time()
            return self.wordcount_cache[content_hash]
        return None
    
    def _evict_if_needed(self):
        """Evict least recently used items."""
        while len(self.content_hashes) > self.max_size:
            # Find LRU item
            lru_editor = min(self.content_hashes.keys(), 
                           key=lambda e: self.access_times.get(self.content_hashes[e], 0))
            old_hash = self.content_hashes[lru_editor]
            
            # Remove from all caches
            del self.content_hashes[lru_editor]
            self.outline_cache.pop(old_hash, None)
            self.wordcount_cache.pop(old_hash, None)
            self.access_times.pop(old_hash, None)

class ViewportTracker:
    """Track visible viewport and detect when updates are needed."""
    
    def __init__(self, editor):
        self.editor_ref = weakref.ref(editor)
        self.visible_start = 1
        self.visible_end = 1
        self.last_update = 0
        
    def get_viewport_bounds(self):
        """Get current visible line range with buffer."""
        editor = self.editor_ref()
        if not editor:
            return 1, 1
            
        try:
            # Get visible area
            top_fraction, bottom_fraction = editor.yview()
            total_lines = int(editor.index("end-1c").split('.')[0])
            
            # Calculate visible lines with buffer
            start_line = max(1, int(top_fraction * total_lines) - PerfConfig.VIEWPORT_BUFFER_LINES)
            end_line = min(total_lines, int(bottom_fraction * total_lines) + PerfConfig.VIEWPORT_BUFFER_LINES)
            
            return start_line, end_line
        except (TclError, ValueError, AttributeError):
            return self.visible_start, self.visible_end
    
    def has_viewport_changed(self):
        """Check if viewport has significantly changed."""
        new_start, new_end = self.get_viewport_bounds()
        
        # Significant change threshold (10% of viewport)
        threshold = max(10, (self.visible_end - self.visible_start) * 0.1)
        
        if (abs(new_start - self.visible_start) > threshold or 
            abs(new_end - self.visible_end) > threshold):
            self.visible_start, self.visible_end = new_start, new_end
            return True
        return False

class PerformanceOptimizer:
    """Main performance optimizer for editor updates with adaptive thresholds."""
    
    def __init__(self):
        self.content_cache = ContentCache()
        self.viewport_trackers = weakref.WeakKeyDictionary()
        self.pending_updates = weakref.WeakKeyDictionary()  # editor -> {update_types, timer_id}
        self.last_update_times = defaultdict(lambda: defaultdict(float))  # editor -> component -> timestamp
        self.performance_metrics = defaultdict(list)
        
        # Adaptive performance tracking
        self.adaptive_thresholds = {
            'small': {'delay_multiplier': 1.0, 'skip_threshold': 0.1},
            'large': {'delay_multiplier': 1.5, 'skip_threshold': 0.2},
            'huge': {'delay_multiplier': 3.0, 'skip_threshold': 0.5}
        }
        self.performance_history = defaultdict(list)  # component -> [durations]
        self.slow_operation_count = defaultdict(int)
        
        # Performance monitoring thread
        self._monitoring_enabled = True
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background performance monitoring."""
        def monitor_performance():
            if not self._monitoring_enabled:
                return
                
            # Analyze recent performance and adjust thresholds
            self._analyze_and_adapt()
            
            # Schedule next monitoring cycle
            threading.Timer(30.0, monitor_performance).start()  # Every 30 seconds
        
        # Start monitoring in background thread
        threading.Timer(30.0, monitor_performance).start()
    
    def _analyze_and_adapt(self):
        """Analyze performance metrics and adapt thresholds."""
        try:
            for category in ['small', 'large', 'huge']:
                if category in self.performance_metrics:
                    recent_times = self.performance_metrics[category][-20:]  # Last 20 operations
                    if len(recent_times) >= 5:
                        avg_time = sum(recent_times) / len(recent_times)
                        
                        # Adjust thresholds based on performance
                        if avg_time > 0.5:  # Very slow operations
                            self.adaptive_thresholds[category]['delay_multiplier'] *= 1.2
                            self.adaptive_thresholds[category]['skip_threshold'] *= 1.1
                            logs_console.log(f"Increased thresholds for {category} files due to slow performance", level='DEBUG')
                        elif avg_time < 0.05:  # Very fast operations
                            self.adaptive_thresholds[category]['delay_multiplier'] = max(0.5, 
                                self.adaptive_thresholds[category]['delay_multiplier'] * 0.9)
                            logs_console.log(f"Decreased thresholds for {category} files due to fast performance", level='DEBUG')
        except Exception as e:
            logs_console.log(f"Error in performance adaptation: {e}", level='WARNING')
        
    def get_file_size_category(self, line_count):
        """Categorize file size for adaptive performance."""
        if line_count < PerfConfig.LARGE_FILE_THRESHOLD:
            return 'small'
        elif line_count < PerfConfig.HUGE_FILE_THRESHOLD:
            return 'large'
        else:
            return 'huge'
    
    def get_adaptive_delay(self, line_count, update_type):
        """Get adaptive delay based on file size, update type, and performance history."""
        category = self.get_file_size_category(line_count)
        
        base_delays = {
            'small': PerfConfig.SMALL_FILE_DELAY,
            'large': PerfConfig.LARGE_FILE_DELAY,  
            'huge': PerfConfig.HUGE_FILE_DELAY
        }
        
        # Component-specific multipliers
        multipliers = {
            UpdateType.SYNTAX: 1.0,
            UpdateType.OUTLINE: 2.0,      # Outline parsing is expensive
            UpdateType.STATUS: 0.5,       # Status updates are fast
            UpdateType.LINE_NUMBERS: 0.3  # Line numbers are very fast
        }
        
        # Apply adaptive threshold multiplier
        adaptive_multiplier = self.adaptive_thresholds[category]['delay_multiplier']
        
        base_delay = base_delays[category] * multipliers.get(update_type, 1.0)
        return int(base_delay * adaptive_multiplier)
    
    def should_skip_update(self, editor, update_type, force=False):
        """Decide if update should be skipped based on recent activity."""
        if force:
            return False
            
        now = time.time()
        last_update = self.last_update_times[editor][update_type]
        
        # Minimum intervals between updates (in seconds)
        min_intervals = {
            UpdateType.SYNTAX: PerfConfig.SYNTAX_UPDATE_INTERVAL / 1000,
            UpdateType.OUTLINE: PerfConfig.OUTLINE_UPDATE_INTERVAL / 1000,
            UpdateType.STATUS: PerfConfig.STATUS_UPDATE_INTERVAL / 1000,
            UpdateType.LINE_NUMBERS: PerfConfig.LINE_NUMBERS_UPDATE_INTERVAL / 1000
        }
        
        return (now - last_update) < min_intervals.get(update_type, 0.1)
    
    def create_change_context(self, editor):
        """Create change context for intelligent updates."""
        try:
            content = editor.get("1.0", "end")
            line_count = int(editor.index("end-1c").split('.')[0])
            content_changed, content_hash = self.content_cache.is_content_changed(editor, content)
            
            # Try to detect change location (simplified)
            cursor_pos = editor.index(tk.INSERT) if hasattr(editor, 'index') else "1.0"
            start_line = int(cursor_pos.split('.')[0])
            
            return ChangeContext(
                editor=editor,
                change_type='edit' if content_changed else 'scroll',
                start_line=max(1, start_line - 5),
                end_line=min(line_count, start_line + 5),
                content_hash=content_hash,
                line_count=line_count,
                timestamp=time.time()
            )
        except (TclError, AttributeError):
            return None
    
    def schedule_intelligent_update(self, editor, update_types=None, force=False):
        """Schedule intelligent updates with deduplication and batching."""
        if not editor or not update_types:
            return
            
        # Ensure update_types is a set
        if isinstance(update_types, str):
            update_types = {update_types}
        elif not isinstance(update_types, set):
            update_types = set(update_types) if update_types else {UpdateType.ALL}
            
        context = self.create_change_context(editor)
        if not context:
            return
            
        # Cancel existing pending updates
        if editor in self.pending_updates:
            try:
                editor.after_cancel(self.pending_updates[editor]['timer_id'])
            except (TclError, KeyError):
                pass
        
        # Merge with existing pending update types
        existing_types = self.pending_updates.get(editor, {}).get('update_types', set())
        merged_types = existing_types | update_types
        
        # Filter out updates that should be skipped
        if not force:
            merged_types = {ut for ut in merged_types if not self.should_skip_update(editor, ut)}
        
        if not merged_types:
            return
            
        # Calculate adaptive delay
        delay = max(self.get_adaptive_delay(context.line_count, ut) for ut in merged_types)
        
        # Schedule the update
        timer_id = editor.after(delay, lambda: self._execute_intelligent_update(editor, merged_types, context))
        
        self.pending_updates[editor] = {
            'update_types': merged_types,
            'timer_id': timer_id,
            'context': context
        }
        
        logs_console.log(f"Scheduled updates {merged_types} with delay {delay}ms for {context.line_count} lines", level='DEBUG')
    
    def _execute_intelligent_update(self, editor, update_types, context):
        """Execute the actual updates with performance monitoring."""
        if editor not in self.pending_updates:
            return
            
        start_time = time.perf_counter()
        
        try:
            # Remove from pending
            del self.pending_updates[editor]
            
            # Get viewport tracker
            if editor not in self.viewport_trackers:
                self.viewport_trackers[editor] = ViewportTracker(editor)
            viewport = self.viewport_trackers[editor]
            
            # Execute updates based on type and file size
            if UpdateType.ALL in update_types:
                update_types = {UpdateType.SYNTAX, UpdateType.OUTLINE, UpdateType.STATUS, UpdateType.LINE_NUMBERS}
                
            category = self.get_file_size_category(context.line_count)
            
            # Update syntax highlighting
            if UpdateType.SYNTAX in update_types:
                self._update_syntax_intelligent(editor, context, category)
                
            # Update outline
            if UpdateType.OUTLINE in update_types:
                self._update_outline_intelligent(editor, context, category)
                
            # Update status bar
            if UpdateType.STATUS in update_types:
                self._update_status_intelligent(editor, context, category)
                
            # Update line numbers
            if UpdateType.LINE_NUMBERS in update_types:
                self._update_line_numbers_intelligent(editor, context, category, viewport)
            
            # Record performance metrics
            duration = time.perf_counter() - start_time
            self.performance_metrics[category].append(duration)
            
            # Keep only recent metrics (last 100)
            if len(self.performance_metrics[category]) > 100:
                self.performance_metrics[category] = self.performance_metrics[category][-100:]
                
            logs_console.log(f"Completed intelligent update in {duration*1000:.2f}ms", level='DEBUG')
            
        except Exception as e:
            logs_console.log(f"Error in intelligent update: {e}", level='ERROR')
    
    def _update_syntax_intelligent(self, editor, context, category):
        """Intelligently update syntax highlighting."""
        from editor import syntax
        
        if category == 'huge':
            # For huge files, use viewport-based syntax highlighting
            syntax.on_viewport_changed(editor)
        elif category == 'large' and hasattr(syntax, 'apply_syntax_highlighting_incremental'):
            # For large files, try incremental if change is localized  
            syntax.apply_syntax_highlighting_incremental(
                editor, context.start_line, context.end_line
            )
        else:
            # Regular syntax highlighting
            syntax.apply_syntax_highlighting(editor)
            
        self.last_update_times[editor][UpdateType.SYNTAX] = time.time()
    
    def _update_outline_intelligent(self, editor, context, category):
        """Intelligently update document outline with caching.""" 
        try:
            from app import state
            
            if not hasattr(state, 'outline') or not state.outline:
                logs_console.log("Outline not available, skipping update", level='DEBUG')
                return
                
            # Check cache first
            cached_outline = self.content_cache.get_cached_outline(context.content_hash)
            if cached_outline is not None:
                # Apply cached outline (implementation depends on outline structure)
                logs_console.log("Using cached outline", level='DEBUG')
                return
                
            # For huge files, skip outline updates during rapid editing
            if category == 'huge' and time.time() - context.timestamp < 2.0:
                return
                
            # Update outline and cache result
            state.outline.update_outline(editor)
            # Note: Actual caching would require outline data structure access
            
        except (ImportError, AttributeError) as e:
            logs_console.log(f"Could not update outline: {e}", level='DEBUG')
        
        self.last_update_times[editor][UpdateType.OUTLINE] = time.time()
    
    def _update_status_intelligent(self, editor, context, category):
        """Intelligently update status bar with caching."""
        from app import status_utils
        
        # Check word count cache
        cached_count = self.content_cache.get_cached_wordcount(context.content_hash)
        if cached_count is not None:
            # Use cached word count (would need status_utils modification)
            logs_console.log(f"Using cached word count: {cached_count}", level='DEBUG')
        
        # Update normally (caching would be implemented in status_utils)
        status_utils.update_status_bar_text()
        
        self.last_update_times[editor][UpdateType.STATUS] = time.time()
    
    def _update_line_numbers_intelligent(self, editor, context, category, viewport):
        """Intelligently update line numbers."""
        current_tab = getattr(editor, 'master', None)
        if not current_tab or not hasattr(current_tab, 'line_numbers') or not current_tab.line_numbers:
            return
            
        # For large files, only redraw if viewport changed significantly
        if category in ['large', 'huge']:
            if not viewport.has_viewport_changed():
                return
                
        current_tab.line_numbers.redraw()
        self.last_update_times[editor][UpdateType.LINE_NUMBERS] = time.time()
    
    def get_performance_stats(self):
        """Get performance statistics."""
        stats = {}
        for category, times in self.performance_metrics.items():
            if times:
                stats[category] = {
                    'avg_time': sum(times) / len(times),
                    'max_time': max(times),
                    'min_time': min(times),
                    'update_count': len(times)
                }
        return stats
    
    def clear_cache(self):
        """Clear all caches."""
        self.content_cache = ContentCache()
        self.performance_metrics.clear()

# Global optimizer instance
_performance_optimizer = PerformanceOptimizer()

def schedule_optimized_update(editor, update_types=None, force=False):
    """Schedule optimized editor update."""
    _performance_optimizer.schedule_intelligent_update(editor, update_types, force)

def get_optimizer_stats():
    """Get performance optimizer statistics."""
    return _performance_optimizer.get_performance_stats()

def clear_optimizer_cache():
    """Clear optimizer cache."""
    _performance_optimizer.clear_cache()