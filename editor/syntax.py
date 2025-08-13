import tkinter as tk
import re
import hashlib
import time
import weakref
from collections import defaultdict
from editor.tab import EditorTab
from utils import debug_console

# Performance thresholds
LARGE_FILE_THRESHOLD = 5000  # Lines
VIEWPORT_BUFFER_LINES = 100  # Extra lines around viewport
MAX_CACHE_SIZE = 20          # Max cached documents
DEBOUNCE_DELAY = 150         # ms

# Simplified color scheme
COLORS = {
    'command': '#2E86AB',
    'section': '#1565C0', 
    'math': '#C73E1D',
    'comment': '#7D8491',
    'number': '#E74C3C',
    'bracket': '#E67E22'
}

# Optimized regex patterns with compiled flags
PATTERNS = {
    'comment': re.compile(r'%[^\n]*', re.MULTILINE),
    'command': re.compile(r'\\[a-zA-Z@]+(?![a-zA-Z@])', re.MULTILINE),
    'section': re.compile(r'\\(?:sub)*section\*?(?![a-zA-Z])', re.MULTILINE),
    'math_env': re.compile(r'\\begin\{(?:equation|align|gather|split)\*?\}.*?\\end\{(?:equation|align|gather|split)\*?\}', re.DOTALL | re.MULTILINE),
    'number': re.compile(r'(?<!\w)\d+(?:\.\d+)?(?!\w)', re.MULTILINE),
    'brackets': re.compile(r'[{}\[\]()]', re.MULTILINE)
}

class SyntaxCache:
    """Cache for syntax highlighting results with content-based invalidation."""
    
    def __init__(self, max_size=MAX_CACHE_SIZE):
        self.max_size = max_size
        self.cache = {}  # content_hash -> {highlights, timestamp}
        self.access_times = {}  # content_hash -> last_access_time
        
    def get_hash(self, content):
        """Generate content hash for caching."""
        return hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()
    
    def get(self, content_hash):
        """Get cached highlights if available."""
        if content_hash in self.cache:
            self.access_times[content_hash] = time.time()
            return self.cache[content_hash]['highlights']
        return None
    
    def set(self, content_hash, highlights):
        """Cache highlights with LRU eviction."""
        if len(self.cache) >= self.max_size:
            # Remove least recently used
            lru_hash = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[lru_hash]
            del self.access_times[lru_hash]
        
        current_time = time.time()
        self.cache[content_hash] = {
            'highlights': highlights,
            'timestamp': current_time
        }
        self.access_times[content_hash] = current_time
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        self.access_times.clear()

class ViewportTracker:
    """Track visible viewport for large files."""
    
    def __init__(self, editor):
        self.editor_ref = weakref.ref(editor)
        self._visible_start = "1.0"
        self._visible_end = "1.0"
        self._last_update = 0
        
    def get_viewport(self):
        """Get current viewport boundaries."""
        editor = self.editor_ref()
        if not editor:
            return "1.0", "1.0"
            
        try:
            # Get visible area
            top_fraction = editor.yview()[0]
            bottom_fraction = editor.yview()[1]
            
            # Convert to line numbers
            total_lines = int(editor.index("end-1c").split('.')[0])
            start_line = max(1, int(top_fraction * total_lines) - VIEWPORT_BUFFER_LINES)
            end_line = min(total_lines, int(bottom_fraction * total_lines) + VIEWPORT_BUFFER_LINES)
            
            self._visible_start = f"{start_line}.0"
            self._visible_end = f"{end_line}.0"
            
        except (tk.TclError, ValueError, AttributeError):
            pass
            
        return self._visible_start, self._visible_end

# Global instances
_syntax_cache = SyntaxCache()
_viewport_trackers = weakref.WeakKeyDictionary()
_pending_updates = weakref.WeakKeyDictionary()

def apply_syntax_highlighting(editor):
    """High-performance syntax highlighting with caching and viewport optimization."""
    if not editor:
        return
        
    current_tab = editor.master
    if not isinstance(current_tab, EditorTab):
        return

    try:
        # Get font configuration
        base_font = current_tab.editor_font
        try:
            font_family = base_font.cget("family")
            font_size = base_font.cget("size")
            normal_font = (font_family, font_size)
            bold_font = (font_family, font_size, "bold")
        except tk.TclError:
            normal_font = ("Consolas", 12)
            bold_font = ("Consolas", 12, "bold")

        # Configure tags once
        _setup_tags(editor, normal_font, bold_font)
        
        # Get content and check for large files
        content = editor.get("1.0", tk.END)
        line_count = int(editor.index("end-1c").split('.')[0])
        
        if line_count > LARGE_FILE_THRESHOLD:
            _highlight_large_file(editor, content)
        else:
            _highlight_with_cache(editor, content)
            
    except tk.TclError:
        pass

def apply_syntax_highlighting_incremental(editor, start_line=None, end_line=None):
    """Apply highlighting to specific range for incremental updates."""
    if not editor:
        return
        
    try:
        if start_line and end_line:
            # Expand range slightly for context
            start_line = max(1, start_line - 2)
            total_lines = int(editor.index("end-1c").split('.')[0])
            end_line = min(total_lines, end_line + 2)
            
            start_idx = f"{start_line}.0"
            end_idx = f"{end_line}.end"
            content = editor.get(start_idx, end_idx)
            
            # Clear tags in range
            _clear_tags_in_range(editor, start_idx, end_idx)
            
            # Apply highlighting to this range
            _highlight_content_range(editor, content, start_idx, start_line - 1)
        else:
            apply_syntax_highlighting(editor)
            
    except tk.TclError:
        pass

def _highlight_large_file(editor, content):
    """Optimized highlighting for large files using viewport-based rendering."""
    if editor not in _viewport_trackers:
        _viewport_trackers[editor] = ViewportTracker(editor)
    
    tracker = _viewport_trackers[editor]
    visible_start, visible_end = tracker.get_viewport()
    
    try:
        # Clear only visible area tags
        _clear_tags_in_range(editor, visible_start, visible_end)
        
        # Get visible content
        visible_content = editor.get(visible_start, visible_end)
        start_line = int(visible_start.split('.')[0]) - 1
        
        # Apply highlighting to visible area only
        _highlight_content_range(editor, visible_content, visible_start, start_line)
        
    except tk.TclError:
        pass

def _highlight_with_cache(editor, content):
    """Highlight with caching for regular-sized files."""
    content_hash = _syntax_cache.get_hash(content)
    cached_highlights = _syntax_cache.get(content_hash)
    
    if cached_highlights:
        # Apply cached highlights
        _apply_cached_highlights(editor, cached_highlights)
    else:
        # Generate and cache new highlights
        _clear_tags(editor)
        highlights = _generate_highlights(content)
        _syntax_cache.set(content_hash, highlights)
        _apply_highlights(editor, highlights)

def _generate_highlights(content):
    """Generate highlights data structure for caching."""
    highlights = defaultdict(list)
    
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(content):
            highlights[name].append((match.start(), match.end()))
    
    return dict(highlights)

def _apply_highlights(editor, highlights):
    """Apply pre-computed highlights to editor."""
    try:
        for tag_name, matches in highlights.items():
            for start_pos, end_pos in matches:
                start_idx = f"1.0 + {start_pos} chars"
                end_idx = f"1.0 + {end_pos} chars"
                editor.tag_add(tag_name, start_idx, end_idx)
    except tk.TclError:
        pass

def _apply_cached_highlights(editor, cached_highlights):
    """Apply cached highlights to editor."""
    _clear_tags(editor)
    _apply_highlights(editor, cached_highlights)

def _highlight_content_range(editor, content, start_idx, line_offset):
    """Apply highlighting to a specific content range."""
    try:
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                start_pos = f"1.0 + {line_offset} lines + {match.start()} chars"
                end_pos = f"1.0 + {line_offset} lines + {match.end()} chars"
                editor.tag_add(name, start_pos, end_pos)
    except tk.TclError:
        pass

def _setup_tags(editor, normal_font, bold_font):
    """Configure highlighting tags with minimal overhead."""
    tags_config = {
        "command": (COLORS['command'], normal_font),
        "section": (COLORS['section'], bold_font),
        "math": (COLORS['math'], normal_font),
        "comment": (COLORS['comment'], normal_font),
        "number": (COLORS['number'], normal_font),
        "bracket": (COLORS['bracket'], normal_font)
    }
    
    for tag_name, (color, font) in tags_config.items():
        editor.tag_configure(tag_name, foreground=color, font=font)

def _clear_tags(editor):
    """Clear all highlighting tags."""
    tags = ['command', 'section', 'math', 'comment', 'number', 'bracket']
    for tag in tags:
        try:
            editor.tag_remove(tag, "1.0", tk.END)
        except tk.TclError:
            pass

def _clear_tags_in_range(editor, start_idx, end_idx):
    """Clear highlighting tags in specific range."""
    tags = ['command', 'section', 'math', 'comment', 'number', 'bracket']
    for tag in tags:
        try:
            editor.tag_remove(tag, start_idx, end_idx)
        except tk.TclError:
            pass

def schedule_syntax_update(editor, debounce=True):
    """Schedule syntax highlighting update with debouncing."""
    if not editor:
        return
        
    # Cancel pending update
    if editor in _pending_updates:
        try:
            editor.after_cancel(_pending_updates[editor])
        except (tk.TclError, ValueError):
            pass
    
    if debounce:
        # Schedule debounced update
        timer_id = editor.after(DEBOUNCE_DELAY, lambda: apply_syntax_highlighting(editor))
        _pending_updates[editor] = timer_id
    else:
        apply_syntax_highlighting(editor)

def on_viewport_changed(editor):
    """Handle viewport changes for large files."""
    try:
        line_count = int(editor.index("end-1c").split('.')[0])
        if line_count > LARGE_FILE_THRESHOLD:
            content = editor.get("1.0", tk.END)
            _highlight_large_file(editor, content)
    except tk.TclError:
        pass

def clear_syntax_highlighting(editor):
    """Remove all syntax highlighting."""
    if editor:
        _clear_tags(editor)
        # Clean up tracking data
        if editor in _pending_updates:
            try:
                editor.after_cancel(_pending_updates[editor])
                del _pending_updates[editor]
            except (tk.TclError, ValueError, KeyError):
                pass

def refresh_syntax_highlighting(editor):
    """Refresh syntax highlighting."""
    schedule_syntax_update(editor, debounce=False)

def clear_cache():
    """Clear syntax highlighting cache."""
    _syntax_cache.clear()

def get_cache_stats():
    """Get cache statistics."""
    return {
        'cache_size': len(_syntax_cache.cache),
        'max_size': _syntax_cache.max_size,
        'hit_ratio': len(_syntax_cache.access_times) / max(1, len(_syntax_cache.cache))
    }

def get_color_scheme():
    """Return current color scheme."""
    return COLORS.copy()

def update_color_scheme(new_colors):
    """Update color scheme and clear cache."""
    COLORS.update(new_colors)
    _syntax_cache.clear()  # Clear cache when colors change