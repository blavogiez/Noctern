import tkinter as tk
import re
import hashlib
import time
import weakref
from collections import defaultdict
from editor.tab import EditorTab
from utils import debug_console

# Performance thresholds (Monaco-inspired)
LARGE_FILE_THRESHOLD = 2000   # Lines (reduced for earlier optimization)
VIEWPORT_BUFFER_LINES = 50    # Reduced buffer for better performance
MAX_CACHE_SIZE = 15           # Reduced cache size
DEBOUNCE_DELAY = 100          # Faster debounce for better responsiveness
VERY_LARGE_FILE_THRESHOLD = 10000  # Lines for extreme optimizations

# Enhanced color scheme for better LaTeX syntax highlighting
COLORS = {
    # Document structure
    'documentclass': '#8E24AA',     # Purple for document class
    'package': '#5E35B1',           # Deep purple for packages
    'section': '#1565C0',           # Blue for sections (keeping original)
    'subsection': '#1976D2',        # Lighter blue for subsections
    'title_commands': '#AD1457',    # Pink for title/author/date
    
    # Environments
    'environment': '#2E7D32',       # Green for begin/end environments
    'list_env': '#388E3C',          # Lighter green for itemize/enumerate
    'math_env': '#C73E1D',          # Red for math environments (keeping original)
    'figure_env': '#F57C00',        # Orange for figure/table environments
    
    # Commands and text formatting
    'command': '#2E86AB',           # Blue for general commands (keeping original)
    'text_format': '#D84315',       # Dark orange for textbf, textit, etc.
    'font_size': '#6A1B9A',         # Purple for font size commands
    'geometry': '#795548',          # Brown for geometry and layout
    
    # References and citations
    'ref_cite': '#00796B',          # Teal for references and citations
    'label': '#004D40',             # Dark teal for labels
    'hyperref': '#1565C0',          # Blue for hyperref commands
    
    # Math elements
    'math': '#C73E1D',              # Red for inline math (keeping original)
    'math_symbols': '#E91E63',      # Pink for special math symbols
    
    # Basic elements
    'comment': '#7D8491',           # Gray for comments (keeping original)
    'number': '#E74C3C',            # Red for numbers (keeping original)
    'bracket': '#E67E22',           # Orange for brackets (keeping original)
    'string': '#689F38',            # Green for strings in braces
    
    # Special characters
    'special_chars': '#FF5722',     # Red-orange for special characters
    'units': '#3F51B5'              # Indigo for units and measurements
}

# Enhanced regex patterns for comprehensive LaTeX highlighting
# Ordered from most specific to most general to avoid conflicts
PATTERNS = {
    # Comments (highest priority - can appear anywhere)
    'comment': re.compile(r'%[^\n]*', re.MULTILINE),
    
    # Document structure (very specific)
    'documentclass': re.compile(r'\\documentclass(?:\[[^\]]*\])?\{[^}]*\}', re.MULTILINE),
    'package': re.compile(r'\\usepackage(?:\[[^\]]*\])?\{[^}]*\}', re.MULTILINE),
    
    # Specific environments (before general environment pattern)
    'list_env': re.compile(r'\\(?:begin|end)\{(?:itemize|enumerate|description)\}', re.MULTILINE),
    'math_env': re.compile(r'\\(?:begin|end)\{(?:equation|align|gather|split|math|displaymath|eqnarray)\*?\}', re.MULTILINE),
    'figure_env': re.compile(r'\\(?:begin|end)\{(?:figure|table|tabular|array)\*?\}', re.MULTILINE),
    
    # Math content (before math commands)
    'math': re.compile(r'\$[^$\n]*\$|\\\([^)]*\\\)', re.MULTILINE),
    'math_symbols': re.compile(r'\\(?:alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|phi|psi|omega|sum|int|prod|sqrt|frac|partial|infty|nabla|times|cdot|ldots|pm|mp|leq|geq|neq|approx|equiv|subset|supset|in|cup|cap|forall|exists)(?![a-zA-Z])', re.MULTILINE),
    
    # Specific command types (before general commands)
    'section': re.compile(r'\\section\*?(?![a-zA-Z])', re.MULTILINE),
    'subsection': re.compile(r'\\(?:sub)+section\*?(?![a-zA-Z])', re.MULTILINE),
    'title_commands': re.compile(r'\\(?:title|author|date)(?![a-zA-Z])', re.MULTILINE),
    'text_format': re.compile(r'\\(?:textbf|textit|texttt|textsc|emph|underline|textcolor)(?![a-zA-Z])', re.MULTILINE),
    'font_size': re.compile(r'\\(?:tiny|scriptsize|footnotesize|small|normalsize|large|Large|LARGE|huge|Huge)(?![a-zA-Z])', re.MULTILINE),
    'geometry': re.compile(r'\\(?:geometry|newpage|clearpage|pagebreak|noindent|indent|hspace|vspace)(?![a-zA-Z])', re.MULTILINE),
    'ref_cite': re.compile(r'\\(?:ref|cite|citet|citep|autoref|nameref|pageref|eqref)(?![a-zA-Z])', re.MULTILINE),
    'hyperref': re.compile(r'\\(?:href|url|hyperref)(?![a-zA-Z])', re.MULTILINE),
    'special_chars': re.compile(r'\\(?:&|%|\$|#|_|\^|~|\\|textbackslash)(?![a-zA-Z])', re.MULTILINE),
    
    # Specific patterns with braces
    'label': re.compile(r'\\label\{[^}]*\}', re.MULTILINE),
    'units': re.compile(r'\\(?:si|SI|unit|num|ang|celsius|degree)\{[^}]*\}', re.MULTILINE),
    
    # General patterns (lower priority)
    'environment': re.compile(r'\\(?:begin|end)\{[^}]+\}', re.MULTILINE),
    'number': re.compile(r'(?<!\w)\d+(?:\.\d+)?(?!\w)', re.MULTILINE),
    'brackets': re.compile(r'[{}\[\]()]', re.MULTILINE),
    'string': re.compile(r'\{[^{}]*\}', re.MULTILINE),
    
    # General commands (lowest priority - catch-all)
    'command': re.compile(r'\\[a-zA-Z@]+(?![a-zA-Z@])', re.MULTILINE)
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
    """Monaco-inspired high-performance syntax highlighting with intelligent optimization."""
    if not editor:
        return
        
    current_tab = editor.master
    if not isinstance(current_tab, EditorTab):
        return

    try:
        # Get content info efficiently
        line_count = int(editor.index("end-1c").split('.')[0])
        
        # Skip highlighting for very large files to maintain responsiveness
        if line_count > VERY_LARGE_FILE_THRESHOLD:
            _setup_minimal_tags(editor)
            return
            
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
        
        # Use viewport-only highlighting for large files
        if line_count > LARGE_FILE_THRESHOLD:
            _highlight_large_file_viewport_only(editor)
        else:
            # Use caching for smaller files
            content = editor.get("1.0", tk.END)
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

def _setup_minimal_tags(editor):
    """Setup minimal tags for very large files with no highlighting."""
    try:
        # Just set up basic font for very large files
        current_tab = editor.master
        if isinstance(current_tab, EditorTab):
            base_font = current_tab.editor_font
            try:
                font_family = base_font.cget("family")
                font_size = base_font.cget("size")
                editor.config(font=(font_family, font_size))
            except tk.TclError:
                pass
    except tk.TclError:
        pass

def _highlight_large_file_viewport_only(editor):
    """Ultra-optimized highlighting for large files - viewport only."""
    if editor not in _viewport_trackers:
        _viewport_trackers[editor] = ViewportTracker(editor)
    
    tracker = _viewport_trackers[editor]
    visible_start, visible_end = tracker.get_viewport()
    
    try:
        # Clear only visible area tags  
        _clear_tags_in_range(editor, visible_start, visible_end)
        
        # Get visible content only
        visible_content = editor.get(visible_start, visible_end)
        if not visible_content.strip():
            return
            
        # Calculate line offset for positioning
        start_line_num = int(visible_start.split('.')[0])
        
        # Apply minimal highlighting patterns for performance
        _highlight_content_range_minimal(editor, visible_content, visible_start, start_line_num - 1)
        
    except tk.TclError:
        pass

def _highlight_content_range_minimal(editor, content, start_idx, line_offset):
    """Minimal highlighting for large files - only essential patterns."""
    try:
        # Only highlight the most important elements for large files
        minimal_patterns = {
            'section': PATTERNS['section'],      # Sections are important for navigation
            'subsection': PATTERNS['subsection'], # Subsections too
            'comment': PATTERNS['comment'],      # Comments are visually important
            'math': PATTERNS['math'],            # Math expressions stand out
            'documentclass': PATTERNS['documentclass'] # Document structure
        }
        
        for name, pattern in minimal_patterns.items():
            for match in pattern.finditer(content):
                start_char = match.start()
                end_char = match.end()
                
                # Convert content positions to editor positions
                content_before_match = content[:start_char]
                newlines_before = content_before_match.count('\n')
                last_newline_pos = content_before_match.rfind('\n')
                char_in_line = start_char - last_newline_pos - 1 if last_newline_pos >= 0 else start_char
                
                match_start_line = line_offset + newlines_before + 1
                start_pos = f"{match_start_line}.{char_in_line}"
                
                content_match = content[start_char:end_char]
                match_newlines = content_match.count('\n')
                if match_newlines == 0:
                    end_pos = f"{match_start_line}.{char_in_line + len(content_match)}"
                else:
                    last_line_content = content_match.split('\n')[-1]
                    end_pos = f"{match_start_line + match_newlines}.{len(last_line_content)}"
                
                editor.tag_add(name, start_pos, end_pos)
                
    except (tk.TclError, ValueError, IndexError):
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
    """Configure highlighting tags with comprehensive LaTeX support."""
    tags_config = {
        # Document structure (bold for emphasis)
        "documentclass": (COLORS['documentclass'], bold_font),
        "package": (COLORS['package'], normal_font),
        "section": (COLORS['section'], bold_font),
        "subsection": (COLORS['subsection'], bold_font),
        "title_commands": (COLORS['title_commands'], bold_font),
        
        # Environments
        "environment": (COLORS['environment'], normal_font),
        "list_env": (COLORS['list_env'], normal_font),
        "math_env": (COLORS['math_env'], bold_font),
        "figure_env": (COLORS['figure_env'], normal_font),
        
        # Commands and formatting
        "command": (COLORS['command'], normal_font),
        "text_format": (COLORS['text_format'], normal_font),
        "font_size": (COLORS['font_size'], normal_font),
        "geometry": (COLORS['geometry'], normal_font),
        
        # References and citations
        "ref_cite": (COLORS['ref_cite'], normal_font),
        "label": (COLORS['label'], normal_font),
        "hyperref": (COLORS['hyperref'], normal_font),
        
        # Math elements
        "math": (COLORS['math'], normal_font),
        "math_symbols": (COLORS['math_symbols'], normal_font),
        
        # Basic elements
        "comment": (COLORS['comment'], normal_font),
        "number": (COLORS['number'], normal_font),
        "bracket": (COLORS['bracket'], normal_font),
        "string": (COLORS['string'], normal_font),
        
        # Special elements
        "special_chars": (COLORS['special_chars'], normal_font),
        "units": (COLORS['units'], normal_font)
    }
    
    for tag_name, (color, font) in tags_config.items():
        editor.tag_configure(tag_name, foreground=color, font=font)

def _clear_tags(editor):
    """Clear all highlighting tags."""
    tags = [
        'documentclass', 'package', 'section', 'subsection', 'title_commands',
        'environment', 'list_env', 'math_env', 'figure_env',
        'command', 'text_format', 'font_size', 'geometry',
        'ref_cite', 'label', 'hyperref',
        'math', 'math_symbols',
        'comment', 'number', 'bracket', 'string',
        'special_chars', 'units'
    ]
    for tag in tags:
        try:
            editor.tag_remove(tag, "1.0", tk.END)
        except tk.TclError:
            pass

def _clear_tags_in_range(editor, start_idx, end_idx):
    """Clear highlighting tags in specific range."""
    tags = [
        'documentclass', 'package', 'section', 'subsection', 'title_commands',
        'environment', 'list_env', 'math_env', 'figure_env',
        'command', 'text_format', 'font_size', 'geometry',
        'ref_cite', 'label', 'hyperref',
        'math', 'math_symbols',
        'comment', 'number', 'bracket', 'string',
        'special_chars', 'units'
    ]
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