"""Provide differential LaTeX syntax highlighting with maximum performance."""
import tkinter as tk
import weakref
from editor.tab import EditorTab
from .syntax_highlighter import apply_differential_highlighting
from .syntax_tracker import get_line_tracker, clear_line_tracker
from .syntax_patterns import PATTERNS, COLORS

# Performance threshold constants
LARGE_FILE_THRESHOLD = 2000
DEBOUNCE_DELAY = 500
QUICK_DEBOUNCE_DELAY = 150

# Global update tracking state
_pending_updates = weakref.WeakKeyDictionary()

def highlight_changes(editor):
    """Apply differential syntax highlighting to changed lines only."""
    apply_differential_highlighting(editor)

def highlight_full_document(editor):
    """Apply full document highlighting with cache clearing."""
    if not editor:
        return
        
    try:
        # Clear line tracker cache for fresh start
        tracker = get_line_tracker(editor)
        tracker.invalidate_cache()
        
        # Get document info
        line_count = int(editor.index("end-1c").split('.')[0])
        
        # Skip highlighting for very large files
        if line_count > 10000:
            return
            
        # Setup fonts and tags
        current_tab = editor.master
        if isinstance(current_tab, EditorTab):
            base_font = current_tab.editor_font
            try:
                font_family = base_font.cget("family")
                font_size = base_font.cget("size")
                normal_font = (font_family, font_size)
                bold_font = (font_family, font_size)
            except tk.TclError:
                normal_font = ("Consolas", 12)
                bold_font = ("Consolas", 12)
        else:
            normal_font = ("Consolas", 12)
            bold_font = ("Consolas", 12, "bold")
        
        _setup_tags(editor, normal_font, bold_font)
        
        # Use optimized highlighting based on file size
        if line_count > LARGE_FILE_THRESHOLD:
            _highlight_large_file_optimized(editor, line_count)
        else:
            _highlight_small_file_fast(editor, line_count)
            
    except tk.TclError:
        pass

def schedule_highlight_update(editor, debounce=True, smart=True):
    """
    Schedule syntax highlighting update with intelligent debouncing.
    """
    if not editor:
        return
        
    # Cancel pending update
    if editor in _pending_updates:
        try:
            editor.after_cancel(_pending_updates[editor])
        except (tk.TclError, ValueError):
            pass
    
    if not debounce:
        highlight_changes(editor)
        return
    
    # Smart debouncing based on file size
    delay = DEBOUNCE_DELAY
    if smart:
        try:
            line_count = int(editor.index("end-1c").split('.')[0])
            if line_count < 100:
                delay = QUICK_DEBOUNCE_DELAY
            elif line_count > LARGE_FILE_THRESHOLD:
                delay = DEBOUNCE_DELAY * 2
        except tk.TclError:
            pass
    
    # Schedule update
    timer_id = editor.after(delay, lambda: highlight_changes(editor))
    _pending_updates[editor] = timer_id

def clear_highlighting(editor):
    """Remove all syntax highlighting from editor."""
    if not editor:
        return
        
    # Cancel pending updates
    if editor in _pending_updates:
        try:
            editor.after_cancel(_pending_updates[editor])
            del _pending_updates[editor]
        except (tk.TclError, ValueError, KeyError):
            pass
    
    # Clear line tracker
    clear_line_tracker(editor)
    
    # Clear all tags
    _clear_all_tags(editor)

def _highlight_small_file_fast(editor, line_count):
    """Fast highlighting for small files."""
    try:
        content = editor.get("1.0", tk.END)
        
        # Clear all tags first
        _clear_all_tags(editor)
        
        # Apply all patterns efficiently
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                start_idx = f"1.0 + {match.start()} chars"
                end_idx = f"1.0 + {match.end()} chars"
                editor.tag_add(name, start_idx, end_idx)
                
    except tk.TclError:
        pass

def _highlight_large_file_optimized(editor, line_count):
    """Optimized highlighting for large files - viewport only."""
    try:
        # Get visible area
        top_fraction = editor.yview()[0]
        bottom_fraction = editor.yview()[1]
        
        # Convert to line numbers with buffer
        start_line = max(1, int(top_fraction * line_count) - 50)
        end_line = min(line_count, int(bottom_fraction * line_count) + 50)
        
        # Highlight only visible area
        start_idx = f"{start_line}.0"
        end_idx = f"{end_line}.end"
        content = editor.get(start_idx, end_idx)
        
        # Clear tags in visible area
        _clear_tags_in_range(editor, start_idx, end_idx)
        
        # Apply patterns to visible content
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                abs_start = f"{start_line}.0 + {match.start()} chars"
                abs_end = f"{start_line}.0 + {match.end()} chars"
                editor.tag_add(name, abs_start, abs_end)
                
    except tk.TclError:
        pass

def _setup_tags(editor, normal_font, bold_font):
    """Configure highlighting tags."""
    tags_config = {
        "documentclass": (COLORS['documentclass'], bold_font),
        "package": (COLORS['package'], normal_font),
        "section": (COLORS['section'], bold_font),
        "subsection": (COLORS['subsection'], bold_font),
        "title_commands": (COLORS['title_commands'], bold_font),
        "environment": (COLORS['environment'], normal_font),
        "list_env": (COLORS['list_env'], normal_font),
        "math_env": (COLORS['math_env'], bold_font),
        "figure_env": (COLORS['figure_env'], normal_font),
        "command": (COLORS['command'], normal_font),
        "text_format": (COLORS['text_format'], normal_font),
        "font_size": (COLORS['font_size'], normal_font),
        "geometry": (COLORS['geometry'], normal_font),
        "ref_cite": (COLORS['ref_cite'], normal_font),
        "label": (COLORS['label'], normal_font),
        "hyperref": (COLORS['hyperref'], normal_font),
        "math": (COLORS['math'], normal_font),
        "math_symbols": (COLORS['math_symbols'], normal_font),
        "proper_names": (COLORS['proper_names'], bold_font),
        "braced_content": (COLORS['braced_content'], normal_font),
        "comment": (COLORS['comment'], normal_font),
        "number": (COLORS['number'], normal_font),
        "bracket": (COLORS['bracket'], normal_font),
        "string": (COLORS['string'], normal_font),
        "special_chars": (COLORS['special_chars'], normal_font),
        "units": (COLORS['units'], normal_font)
    }
    
    for tag_name, (color, font) in tags_config.items():
        try:
            editor.tag_configure(tag_name, foreground=color, font=font)
        except tk.TclError:
            pass

def _clear_all_tags(editor):
    """Clear all highlighting tags."""
    tags = list(COLORS.keys()) + ['brackets']
    for tag in tags:
        try:
            editor.tag_remove(tag, "1.0", tk.END)
        except tk.TclError:
            pass

def _clear_tags_in_range(editor, start_idx, end_idx):
    """Clear highlighting tags in specific range."""
    tags = list(COLORS.keys()) + ['brackets']
    for tag in tags:
        try:
            editor.tag_remove(tag, start_idx, end_idx)
        except tk.TclError:
            pass

# Compatibility aliases for existing code
apply_differential_syntax_highlighting = highlight_changes
apply_syntax_highlighting = highlight_full_document
schedule_syntax_update = schedule_highlight_update
clear_syntax_highlighting = clear_highlighting
initialize_syntax_highlighting = highlight_full_document
refresh_syntax_highlighting = lambda editor: schedule_highlight_update(editor, debounce=False)

def get_color_scheme():
    """Return current color scheme."""
    return COLORS.copy()

def clear_cache():
    """Clear syntax highlighting cache."""
    # Cache is now handled by line trackers
    pass