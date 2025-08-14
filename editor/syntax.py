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
DEBOUNCE_DELAY = 500          # Longer debounce for better performance
QUICK_DEBOUNCE_DELAY = 150    # Quick debounce for simple changes
VERY_LARGE_FILE_THRESHOLD = 10000  # Lines for extreme optimizations

# Enhanced color scheme with high visibility colors
COLORS = {
    # Document structure - More vibrant purples
    'documentclass': '#9C27B0',     # Bright purple for document class
    'package': '#673AB7',           # Deep violet for packages
    'section': '#0D47A1',           # Deep blue for sections
    'subsection': '#1565C0',        # Medium blue for subsections
    'title_commands': '#C2185B',    # Bright pink for title/author/date
    
    # Environments - More visible greens
    'environment': '#2E7D32',       # Forest green for begin/end environments
    'list_env': '#43A047',          # Bright green for itemize/enumerate
    'math_env': '#D32F2F',          # Bright red for math environments
    'figure_env': '#FF8F00',        # Bright amber for figure/table environments
    
    # Commands and text formatting - Enhanced visibility
    'command': '#1976D2',           # Bright blue for general commands
    'text_format': '#E65100',       # Bright orange for textbf, textit, etc.
    'font_size': '#7B1FA2',         # Bright purple for font size commands
    'geometry': '#5D4037',          # Dark brown for geometry and layout
    
    # References and citations - Enhanced teals
    'ref_cite': '#00838F',          # Bright teal for references and citations
    'label': '#006064',             # Dark cyan for labels
    'hyperref': '#0277BD',          # Light blue for hyperref commands
    
    # Math elements - Vibrant reds and pinks
    'math': '#D32F2F',              # Bright red for inline math
    'math_symbols': '#E91E63',      # Hot pink for special math symbols
    
    # Text content - New additions
    'proper_names': '#8E24AA',      # Purple for proper names (Jean Blanc, etc.)
    'braced_content': '#2E7D32',    # Forest green for content in braces {}
    
    # Basic elements - Enhanced visibility
    'comment': '#616161',           # Darker gray for better contrast
    'number': '#F44336',            # Bright red for numbers
    'bracket': '#FF9800',           # Bright orange for brackets
    'string': '#558B2F',            # Dark green for general strings
    
    # Special characters - High contrast
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
    
    # Text content patterns (before general patterns)
    'proper_names': re.compile(r'(?<!\w)[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?!\w)', re.MULTILINE),
    'braced_content': re.compile(r'\{[^{}]*\}', re.MULTILINE),
    
    # General patterns (lower priority)
    'environment': re.compile(r'\\(?:begin|end)\{[^}]+\}', re.MULTILINE),
    'number': re.compile(r'(?<!\w)\d+(?:\.\d+)?(?!\w)', re.MULTILINE),
    'brackets': re.compile(r'[{}\[\]()]', re.MULTILINE),
    
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
_line_trackers = weakref.WeakKeyDictionary()  # Track line changes for differential highlighting

class LineTracker:
    """Ultra-fast line change tracking for differential highlighting."""
    
    def __init__(self, editor):
        self.editor_ref = weakref.ref(editor)
        self.line_cache = {}  # line_num -> (content_hash, last_highlighted)
        self.last_cursor_line = 1
        self.last_total_lines = 0
        
    def get_changed_lines(self):
        """Get only the lines that actually changed - ultra efficient."""
        editor = self.editor_ref()
        if not editor:
            return set()
            
        try:
            # Get current cursor position for focused change detection
            cursor_pos = editor.index(tk.INSERT)
            current_cursor_line = int(cursor_pos.split('.')[0])
            
            # For single character changes, only check current line + context
            if abs(current_cursor_line - self.last_cursor_line) <= 1:
                changed_lines = self._check_focused_lines(editor, current_cursor_line)
            else:
                # Cursor moved significantly or larger change
                changed_lines = self._check_range_lines(editor, 
                    min(self.last_cursor_line, current_cursor_line) - 1,
                    max(self.last_cursor_line, current_cursor_line) + 1)
            
            self.last_cursor_line = current_cursor_line
            return changed_lines
            
        except tk.TclError:
            return set()
    
    def _check_focused_lines(self, editor, focus_line):
        """Check only the focused line and immediate context."""
        changed = set()
        
        # Check only current line and neighbors for maximum performance
        for line_num in range(max(1, focus_line - 1), focus_line + 2):
            try:
                line_content = editor.get(f"{line_num}.0", f"{line_num}.end")
                content_hash = hash(line_content)
                
                if line_num not in self.line_cache or self.line_cache[line_num][0] != content_hash:
                    changed.add(line_num)
                    self.line_cache[line_num] = (content_hash, True)
                    
            except tk.TclError:
                break
                
        return changed
    
    def _check_range_lines(self, editor, start_line, end_line):
        """Check a specific range of lines efficiently."""
        changed = set()
        
        try:
            total_lines = int(editor.index("end-1c").split('.')[0])
            start_line = max(1, start_line)
            end_line = min(total_lines, end_line)
            
            for line_num in range(start_line, end_line + 1):
                try:
                    line_content = editor.get(f"{line_num}.0", f"{line_num}.end")
                    content_hash = hash(line_content)
                    
                    if line_num not in self.line_cache or self.line_cache[line_num][0] != content_hash:
                        changed.add(line_num)
                        self.line_cache[line_num] = (content_hash, True)
                        
                except tk.TclError:
                    continue
                    
        except tk.TclError:
            pass
            
        return changed
    
    def invalidate_cache(self):
        """Clear the line cache for full refresh."""
        self.line_cache.clear()

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
            'documentclass': PATTERNS['documentclass'], # Document structure
            'proper_names': PATTERNS['proper_names'] # Proper names for readability
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
        
        # Text content
        "proper_names": (COLORS['proper_names'], bold_font),
        "braced_content": (COLORS['braced_content'], normal_font),
        
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
        'proper_names', 'braced_content',
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
        'proper_names', 'braced_content',
        'comment', 'number', 'bracket', 'string',
        'special_chars', 'units'
    ]
    for tag in tags:
        try:
            editor.tag_remove(tag, start_idx, end_idx)
        except tk.TclError:
            pass

def schedule_syntax_update(editor, debounce=True, smart=True):
    """Schedule syntax highlighting update with intelligent debouncing."""
    if not editor:
        return
        
    # Cancel pending update
    if editor in _pending_updates:
        try:
            editor.after_cancel(_pending_updates[editor])
        except (tk.TclError, ValueError):
            pass
    
    if not debounce:
        apply_syntax_highlighting(editor)
        return
    
    # Smart debouncing: choose delay based on file size and change context
    delay = DEBOUNCE_DELAY
    if smart:
        try:
            line_count = int(editor.index("end-1c").split('.')[0])
            if line_count < 100:
                delay = QUICK_DEBOUNCE_DELAY  # Quick refresh for small files
            elif line_count > LARGE_FILE_THRESHOLD:
                delay = DEBOUNCE_DELAY * 2    # Slower refresh for large files
        except tk.TclError:
            pass
    
    # Schedule debounced update
    timer_id = editor.after(delay, lambda: apply_syntax_highlighting(editor))
    _pending_updates[editor] = timer_id

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

def apply_differential_syntax_highlighting(editor):
    """ULTRA-PERFORMANT differential highlighting - only changed lines."""
    if not editor:
        return
        
    # Get or create line tracker for this editor
    if editor not in _line_trackers:
        _line_trackers[editor] = LineTracker(editor)
    
    tracker = _line_trackers[editor]
    changed_lines = tracker.get_changed_lines()
    
    if not changed_lines:
        return  # Nothing changed, no work needed!
    
    try:
        # Setup fonts once
        current_tab = editor.master
        if isinstance(current_tab, EditorTab):
            base_font = current_tab.editor_font
            try:
                font_family = base_font.cget("family")
                font_size = base_font.cget("size")
                normal_font = (font_family, font_size)
                bold_font = (font_family, font_size, "bold")
            except tk.TclError:
                normal_font = ("Consolas", 12)
                bold_font = ("Consolas", 12, "bold")
        else:
            normal_font = ("Consolas", 12)
            bold_font = ("Consolas", 12, "bold")
        
        # Configure tags only once if not already done
        _setup_tags(editor, normal_font, bold_font)
        
        # Highlight ONLY the changed lines - maximum efficiency
        for line_num in changed_lines:
            _highlight_single_line_ultra_fast(editor, line_num)
            
    except tk.TclError:
        pass

def _highlight_single_line_ultra_fast(editor, line_num):
    """Highlight a single line with optimized patterns - ultra fast."""
    try:
        line_start = f"{line_num}.0"
        line_end = f"{line_num}.end"
        line_content = editor.get(line_start, line_end)
        
        if not line_content.strip():
            return  # Empty line, nothing to do
        
        # Clear existing tags for this line only
        _clear_tags_single_line(editor, line_start, line_end)
        
        # Apply only relevant patterns based on line content - smart optimization
        _apply_smart_patterns_to_line(editor, line_content, line_start, line_num)
        
    except tk.TclError:
        pass

def _clear_tags_single_line(editor, line_start, line_end):
    """Clear tags for a single line only."""
    tags = ['documentclass', 'package', 'section', 'subsection', 'title_commands',
            'environment', 'list_env', 'math_env', 'figure_env',
            'command', 'text_format', 'font_size', 'geometry',
            'ref_cite', 'label', 'hyperref', 'math', 'math_symbols',
            'proper_names', 'braced_content', 'comment', 'number', 'bracket', 'string',
            'special_chars', 'units']
    
    for tag in tags:
        try:
            editor.tag_remove(tag, line_start, line_end)
        except tk.TclError:
            continue

def _apply_smart_patterns_to_line(editor, line_content, line_start, line_num):
    """Apply only relevant patterns to a line - context-aware optimization."""
    
    # Quick pre-filtering based on line content - avoid unnecessary regex
    has_backslash = '\\' in line_content
    has_percent = '%' in line_content
    has_math = '$' in line_content
    has_braces = '{' in line_content or '}' in line_content
    
    # Comments first (highest priority)
    if has_percent:
        _apply_pattern_to_line(editor, PATTERNS['comment'], 'comment', line_content, line_start, line_num)
    
    # Only check LaTeX patterns if backslash present
    if has_backslash:
        # Check specific patterns based on context
        if 'section' in line_content:
            _apply_pattern_to_line(editor, PATTERNS['section'], 'section', line_content, line_start, line_num)
            _apply_pattern_to_line(editor, PATTERNS['subsection'], 'subsection', line_content, line_start, line_num)
        
        if 'documentclass' in line_content:
            _apply_pattern_to_line(editor, PATTERNS['documentclass'], 'documentclass', line_content, line_start, line_num)
        
        if 'usepackage' in line_content:
            _apply_pattern_to_line(editor, PATTERNS['package'], 'package', line_content, line_start, line_num)
        
        if 'textbf' in line_content or 'textit' in line_content:
            _apply_pattern_to_line(editor, PATTERNS['text_format'], 'text_format', line_content, line_start, line_num)
        
        if 'begin' in line_content or 'end' in line_content:
            _apply_pattern_to_line(editor, PATTERNS['environment'], 'environment', line_content, line_start, line_num)
            _apply_pattern_to_line(editor, PATTERNS['list_env'], 'list_env', line_content, line_start, line_num)
            _apply_pattern_to_line(editor, PATTERNS['math_env'], 'math_env', line_content, line_start, line_num)
            _apply_pattern_to_line(editor, PATTERNS['figure_env'], 'figure_env', line_content, line_start, line_num)
        
        # General command pattern (only if not caught by specific patterns above)
        _apply_pattern_to_line(editor, PATTERNS['command'], 'command', line_content, line_start, line_num)
    
    # Math patterns
    if has_math:
        _apply_pattern_to_line(editor, PATTERNS['math'], 'math', line_content, line_start, line_num)
    
    # Proper names (only if has uppercase letters)
    if any(c.isupper() for c in line_content):
        _apply_pattern_to_line(editor, PATTERNS['proper_names'], 'proper_names', line_content, line_start, line_num)
    
    # Numbers (only if has digits)
    if any(c.isdigit() for c in line_content):
        _apply_pattern_to_line(editor, PATTERNS['number'], 'number', line_content, line_start, line_num)

def _apply_pattern_to_line(editor, pattern, tag_name, line_content, line_start, line_num):
    """Apply a specific pattern to a single line."""
    try:
        for match in pattern.finditer(line_content):
            start_idx = f"{line_num}.{match.start()}"
            end_idx = f"{line_num}.{match.end()}"
            editor.tag_add(tag_name, start_idx, end_idx)
    except tk.TclError:
        pass

def initialize_syntax_highlighting(editor):
    """Initialize syntax highlighting for a new file - clear cache and do full highlighting."""
    if editor in _line_trackers:
        _line_trackers[editor].invalidate_cache()
    apply_syntax_highlighting(editor)

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