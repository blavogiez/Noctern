"""
Ultra-fast differential syntax highlighter.
Only highlights changed lines - maximum performance.
"""
import tkinter as tk
from editor.tab import EditorTab
from .syntax_patterns import COLORS, get_relevant_patterns
from .syntax_tracker import get_line_tracker

def apply_differential_highlighting(editor):
    """ULTRA-PERFORMANT differential highlighting - only changed lines."""
    if not editor:
        return
        
    # Get line tracker and check for changes
    tracker = get_line_tracker(editor)
    changed_lines = tracker.get_changed_lines()
    
    if not changed_lines:
        return  # Nothing changed, no work needed!
    
    try:
        # Setup fonts once
        normal_font, bold_font = _get_fonts(editor)
        
        # Configure tags only once if not already done
        _setup_tags(editor, normal_font, bold_font)
        
        # Highlight ONLY the changed lines - maximum efficiency
        for line_num in changed_lines:
            _highlight_single_line(editor, line_num)
            
    except tk.TclError:
        pass

def _highlight_single_line(editor, line_num):
    """Highlight a single line with optimized patterns - ultra fast."""
    try:
        line_start = f"{line_num}.0"
        line_end = f"{line_num}.end"
        line_content = editor.get(line_start, line_end)
        
        if not line_content.strip():
            return  # Empty line, nothing to do
        
        # Clear existing tags for this line only
        _clear_tags_single_line(editor, line_start, line_end)
        
        # Get only relevant patterns for this line content
        relevant_patterns = get_relevant_patterns(line_content)
        
        # Apply only relevant patterns to this line
        for pattern_name, pattern in relevant_patterns.items():
            try:
                for match in pattern.finditer(line_content):
                    start_idx = f"{line_num}.{match.start()}"
                    end_idx = f"{line_num}.{match.end()}"
                    editor.tag_add(pattern_name, start_idx, end_idx)
            except tk.TclError:
                continue
        
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

def _get_fonts(editor):
    """Get fonts from editor tab."""
    try:
        current_tab = editor.master
        if isinstance(current_tab, EditorTab):
            base_font = current_tab.editor_font
            font_family = base_font.cget("family")
            font_size = base_font.cget("size")
            return (font_family, font_size), (font_family, font_size, "bold")
    except tk.TclError:
        pass
    return ("Consolas", 12), ("Consolas", 12, "bold")

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
        try:
            editor.tag_configure(tag_name, foreground=color, font=font)
        except tk.TclError:
            pass