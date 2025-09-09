"""
This module contains all the logic and bindings for editor-specific shortcuts.
"""
import tkinter as tk
import re
from editor.placeholder_navigation import handle_placeholder_navigation

# --- Helper Function ---
def _get_line_range(editor):
    """Gets the line range for a selection or the current cursor line."""
    try:
        start, end = editor.tag_ranges("sel")
        start_line = int(editor.index(start).split('.')[0])
        end_line = int(editor.index(end).split('.')[0])
        if editor.index(end).split('.')[1] == '0': end_line -= 1
        return start_line, end_line
    except ValueError:
        current_line = int(editor.index("insert").split('.')[0])
        return current_line, current_line

# --- Action Implementations ---

def delete_word_left(event):
    event.widget.delete("insert-1c wordstart", "insert")
    return "break"

def delete_word_right(event):
    event.widget.delete("insert", "insert wordend")
    return "break"

def move_word_left(event):
    event.widget.mark_set("insert", "insert-1c wordstart")
    event.widget.tag_remove("sel", "1.0", "end")
    return "break"

def move_word_right(event):
    event.widget.mark_set("insert", "insert wordend")
    event.widget.tag_remove("sel", "1.0", "end")
    return "break"

def select_word_left(event):
    editor = event.widget
    # Remember current position if no selection exists
    if not editor.tag_ranges("sel"):
        editor.mark_set("anchor", "insert")
    
    # Move cursor to start of previous word
    current_pos = editor.index("insert")
    new_pos = editor.index("insert-1c wordstart")
    
    # Update cursor position
    editor.mark_set("insert", new_pos)
    
    # Add new selection
    editor.tag_remove("sel", "1.0", "end")
    editor.tag_add("sel", "insert", "anchor")
    
    # Ensure cursor is visible
    editor.see("insert")
    return "break"

def select_word_right(event):
    editor = event.widget
    # Remember current position if no selection exists
    if not editor.tag_ranges("sel"):
        editor.mark_set("anchor", "insert")
    
    # Move cursor to end of next word
    current_pos = editor.index("insert")
    new_pos = editor.index("insert wordend")
    
    # Update cursor position
    editor.mark_set("insert", new_pos)
    
    # Add new selection
    editor.tag_remove("sel", "1.0", "end")
    editor.tag_add("sel", "anchor", "insert")
    
    # Ensure cursor is visible
    editor.see("insert")
    return "break"

def move_line_up(event):
    editor = event.widget
    start_line, end_line = _get_line_range(editor)
    if start_line <= 1: return "break"
    block = editor.get(f"{start_line}.0", f"{end_line}.end")
    line_above = editor.get(f"{start_line-1}.0", f"{start_line-1}.end")
    editor.delete(f"{start_line-1}.0", f"{end_line}.end")
    editor.insert(f"{start_line-1}.0", block + "\n" + line_above)
    editor.tag_add("sel", f"{start_line-1}.0", f"{end_line-1}.end")
    return "break"

def move_line_down(event):
    editor = event.widget
    start_line, end_line = _get_line_range(editor)
    last_line = int(editor.index("end-1c").split('.')[0])
    if end_line >= last_line: return "break"
    block = editor.get(f"{start_line}.0", f"{end_line}.end")
    line_below = editor.get(f"{end_line+1}.0", f"{end_line+1}.end")
    editor.delete(f"{start_line}.0", f"{end_line+1}.end")
    editor.insert(f"{start_line}.0", line_below + "\n" + block)
    editor.tag_add("sel", f"{start_line+1}.0", f"{end_line+1}.end")
    return "break"

def handle_tab(event):
    """Handle normal tab indentation without placeholder navigation."""
    editor = event.widget
    start_line, end_line = _get_line_range(editor)
    if editor.tag_ranges("sel"):
        for i in range(start_line, end_line + 1):
            editor.insert(f"{i}.0", "    ")
        editor.tag_add("sel", f"{start_line}.0", f"{end_line}.end")
    else:
        editor.insert(tk.INSERT, "    ")
    return "break"

def handle_shift_tab(event):
    editor = event.widget
    start_line, end_line = _get_line_range(editor)
    for i in range(start_line, end_line + 1):
        line = editor.get(f"{i}.0", f"{i}.end")
        if line.startswith('\t'):
            editor.delete(f"{i}.0")
        elif line.startswith(' '):
            leading_spaces = len(line) - len(line.lstrip(' '))
            spaces_to_remove = min(leading_spaces, 4)
            editor.delete(f"{i}.0", f"{i}.{spaces_to_remove}")
    editor.tag_add("sel", f"{start_line}.0", f"{end_line}.end")
    return "break"

def on_double_click(event):
    """Selects the content within quotes or LaTeX command braces on double-click."""
    editor = event.widget
    index = editor.index(f"@{event.x},{event.y}")
    line, char = map(int, index.split('.'))
    line_content = editor.get(f"{line}.0", f"{line}.end")
    
    # First try to select content within quotes - single optimized regex
    for match in re.finditer(r'(["\'"«])([^"\'»]*)\1|«([^»]*)»', line_content):
        content_start = match.start(2) if match.group(2) is not None else match.start(3)
        content_end = match.end(2) if match.group(2) is not None else match.end(3)
        if content_start <= char < content_end:
            start_abs = f"{line}.{content_start}"
            end_abs = f"{line}.{content_end}"
            editor.tag_remove("sel", "1.0", "end")
            editor.tag_add("sel", start_abs, end_abs)
            editor.mark_set("insert", start_abs)
            return "break"
    
    # Fallback to LaTeX command braces
    for match in re.finditer(r"\\(?:[a-zA-Z]+|emph|textbf|textit)(?:\[[^\]]*\])?\{([^}]*)\}", line_content):
        if match.start(1) <= char < match.end(1):
            start_abs = f"{line}.{match.start(1)}"
            end_abs = f"{line}.{match.end(1)}"
            editor.tag_remove("sel", "1.0", "end")
            editor.tag_add("sel", start_abs, end_abs)
            editor.mark_set("insert", start_abs)
            return "break"
    return None

def handle_placeholder_next(event):
    """Handle F3 navigation to next placeholder."""
    result = handle_placeholder_navigation(event)
    return result

def handle_placeholder_prev(event):
    """Handle Shift+F3 navigation to previous placeholder."""
    if not isinstance(event.widget, tk.Text):
        return
        
    text_widget = event.widget
    
    # Create manager if it doesn't exist
    if not hasattr(text_widget, 'placeholder_manager'):
        text_widget.placeholder_manager = PlaceholderManager(text_widget)
        
    manager = text_widget.placeholder_manager
    
    # Only navigate if there are placeholders
    if manager.has_placeholders() and manager.navigate_previous():
        return "break"
        
    return None

# --- Setup Function ---

def setup_editor_shortcuts(editor):
    """Binds all editor-specific shortcuts to the editor widget."""
    shortcuts = {
        "<Control-BackSpace>": delete_word_left,
        "<Control-Delete>": delete_word_right,
        "<Control-Left>": move_word_left,
        "<Control-Right>": move_word_right,
        "<Control-Shift-Left>": select_word_left,
        "<Control-Shift-Right>": select_word_right,
        "<Alt-Up>": move_line_up,
        "<Alt-Down>": move_line_down,
        "<Tab>": handle_tab,
        "<Shift-Tab>": handle_shift_tab,
        "<F3>": handle_placeholder_next,
        "<Shift-F3>": handle_placeholder_prev,
        "<Double-Button-1>": on_double_click,
    }
    for key, func in shortcuts.items():
        editor.bind(key, func)