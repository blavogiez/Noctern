import tkinter as tk
import re
from editor.tab import EditorTab
from utils import debug_console

# Simplified color scheme
COLORS = {
    'command': '#2E86AB',
    'section': '#1565C0', 
    'math': '#C73E1D',
    'comment': '#7D8491',
    'number': '#E74C3C',
    'bracket': '#E67E22'
}

# Pre-compiled regex patterns for better performance
PATTERNS = {
    'comment': re.compile(r'%[^\n]*'),
    'command': re.compile(r'\\[a-zA-Z@]+'),
    'section': re.compile(r'\\(?:sub)*section\*?'),
    'math_env': re.compile(r'\\begin\{(?:equation|align|gather|split)\*?\}.*?\\end\{(?:equation|align|gather|split)\*?\}', re.DOTALL),
    'number': re.compile(r'\b\d+(?:\.\d+)?\b'),
    'brackets': re.compile(r'[{}\[\]()]')
}

def apply_syntax_highlighting(editor):
    """Simplified and performant syntax highlighting for LaTeX."""
    if not editor:
        return
        
    current_tab = editor.master
    if not isinstance(current_tab, EditorTab):
        return

    # Get font configuration (zoom-compatible)
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
    
    # Clear existing highlighting
    _clear_tags(editor)

    try:
        content = editor.get("1.0", tk.END)
        _highlight_content(editor, content)
    except tk.TclError:
        pass

def _setup_tags(editor, normal_font, bold_font):
    """Configure highlighting tags with minimal overhead."""
    editor.tag_configure("command", foreground=COLORS['command'], font=normal_font)
    editor.tag_configure("section", foreground=COLORS['section'], font=bold_font)
    editor.tag_configure("math", foreground=COLORS['math'], font=normal_font)
    editor.tag_configure("comment", foreground=COLORS['comment'], font=normal_font)
    editor.tag_configure("number", foreground=COLORS['number'], font=normal_font)
    editor.tag_configure("bracket", foreground=COLORS['bracket'], font=normal_font)

def _clear_tags(editor):
    """Clear existing highlighting tags."""
    tags = ['command', 'section', 'math', 'comment', 'number', 'bracket']
    for tag in tags:
        try:
            editor.tag_remove(tag, "1.0", tk.END)
        except tk.TclError:
            pass

def _highlight_content(editor, content):
    """Apply syntax highlighting with single-pass approach."""
    # Apply patterns in priority order
    for name, pattern in PATTERNS.items():
        _apply_pattern(editor, content, pattern, name)

def _apply_pattern(editor, content, pattern, tag_name):
    """Apply a single pattern and add tags efficiently."""
    try:
        for match in pattern.finditer(content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            editor.tag_add(tag_name, start, end)
    except tk.TclError:
        pass

def clear_syntax_highlighting(editor):
    """Remove all syntax highlighting."""
    if editor:
        _clear_tags(editor)

def refresh_syntax_highlighting(editor):
    """Refresh syntax highlighting."""
    apply_syntax_highlighting(editor)

def get_color_scheme():
    """Return current color scheme."""
    return COLORS.copy()

def update_color_scheme(new_colors):
    """Update color scheme."""
    COLORS.update(new_colors)