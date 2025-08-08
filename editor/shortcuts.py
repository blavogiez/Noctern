# editor/shortcuts.py
import tkinter as tk
import re
from llm import state as llm_state

# --- Word/Line Deletion and Movement ---

def delete_word_left(event):
    """Deletes the word to the left of the cursor."""
    editor = event.widget
    editor.delete("insert-1c wordstart", "insert")
    return "break"

def delete_word_right(event):
    """Deletes the word to the right of the cursor."""
    editor = event.widget
    editor.delete("insert", "insert wordend")
    return "break"

def move_word_left(event):
    """Moves the cursor to the beginning of the previous word."""
    editor = event.widget
    editor.mark_set("insert", "insert-1c wordstart")
    editor.tag_remove("sel", "1.0", "end")
    return "break"

def move_word_right(event):
    """Moves the cursor to the end of the next word."""
    editor = event.widget
    editor.mark_set("insert", "insert wordend")
    editor.tag_remove("sel", "1.0", "end")
    return "break"

def select_word_left(event):
    """Selects text from the cursor to the start of the previous word."""
    editor = event.widget
    # If there's no selection yet, set the anchor point
    if not editor.tag_ranges("sel"):
        editor.mark_set("anchor", "insert")
    # Move the insert mark and adjust the selection
    editor.mark_set("insert", "insert-1c wordstart")
    editor.tag_add("sel", "anchor", "insert")
    return "break"

def select_word_right(event):
    """Selects text from the cursor to the end of the next word."""
    editor = event.widget
    if not editor.tag_ranges("sel"):
        editor.mark_set("anchor", "insert")
    editor.mark_set("insert", "insert wordend")
    editor.tag_add("sel", "anchor", "insert")
    return "break"

def move_line_up(event):
    """Moves the current line or selected block of lines up."""
    editor = event.widget
    try:
        start, end = editor.tag_ranges("sel")
        start_line = int(editor.index(start).split('.')[0])
        end_line = int(editor.index(end).split('.')[0])
        if int(editor.index(end).split('.')[1]) == 0: end_line -= 1
    except ValueError:
        start_line = end_line = int(editor.index("insert").split('.')[0])

    if start_line <= 1: return "break"

    block = editor.get(f"{start_line}.0", f"{end_line}.end")
    line_above = editor.get(f"{start_line-1}.0", f"{start_line-1}.end")
    
    editor.delete(f"{start_line-1}.0", f"{end_line}.end")
    editor.insert(f"{start_line-1}.0", block + "\n" + line_above)
    editor.tag_add("sel", f"{start_line-1}.0", f"{end_line-1}.end")
    return "break"

def move_line_down(event):
    """Moves the current line or selected block of lines down."""
    editor = event.widget
    try:
        start, end = editor.tag_ranges("sel")
        start_line = int(editor.index(start).split('.')[0])
        end_line = int(editor.index(end).split('.')[0])
        if int(editor.index(end).split('.')[1]) == 0: end_line -= 1
    except ValueError:
        start_line = end_line = int(editor.index("insert").split('.')[0])

    last_line = int(editor.index("end-1c").split('.')[0])
    if end_line >= last_line: return "break"

    block = editor.get(f"{start_line}.0", f"{end_line}.end")
    line_below = editor.get(f"{end_line+1}.0", f"{end_line+1}.end")

    editor.delete(f"{start_line}.0", f"{end_line+1}.end")
    editor.insert(f"{start_line}.0", line_below + "\n" + block)
    editor.tag_add("sel", f"{start_line+1}.0", f"{end_line+1}.end")
    return "break"

# --- Indentation and Comments ---

def handle_tab(event):
    """Indents the current line or selection."""
    editor = event.widget
    if llm_state._is_generating: return

    if editor.tag_ranges("sel"):
        start, end = editor.index("sel.first"), editor.index("sel.last")
        start_line, end_line = int(start.split('.')[0]), int(end.split('.')[0])
        if end.split('.')[1] == '0': end_line -= 1
        
        for i in range(start_line, end_line + 1):
            editor.insert(f"{i}.0", "\t")
        
        editor.tag_add("sel", f"{start_line}.0", f"{end_line+1}.0")
    else:
        editor.insert(tk.INSERT, "\t")
    return "break"

def handle_shift_tab(event):
    """Outdents the current line or selection."""
    editor = event.widget
    if llm_state._is_generating: return

    try:
        start, end = editor.tag_ranges("sel")
        start_line, end_line = int(editor.index(start).split('.')[0]), int(editor.index(end).split('.')[0])
        if editor.index(end).split('.')[1] == '0': end_line -= 1
    except ValueError:
        start_line = end_line = int(editor.index("insert").split('.')[0])

    for i in range(start_line, end_line + 1):
        line = editor.get(f"{i}.0", f"{i}.end")
        if line.startswith('\t'):
            editor.delete(f"{i}.0")
        elif line.startswith('    '):
            editor.delete(f"{i}.0", f"{i}.4")
            
    editor.tag_add("sel", f"{start_line}.0", f"{end_line}.end")
    return "break"

def toggle_comment(event):
    """Toggles comments for the selected lines or the current line."""
    editor = event.widget
    try:
        start, end = editor.tag_ranges("sel")
        start_line, end_line = int(editor.index(start).split('.')[0]), int(editor.index(end).split('.')[0])
        if editor.index(end).split('.')[1] == '0': end_line -= 1
    except ValueError:
        start_line = end_line = int(editor.index("insert").split('.')[0])

    all_commented = all(editor.get(f"{i}.0", f"{i}.end").lstrip().startswith('%') for i in range(start_line, end_line + 1))
    
    for i in range(start_line, end_line + 1):
        line = editor.get(f"{i}.0", f"{i}.end")
        if all_commented:
            if match := re.search(r"^\s*%", line):
                editor.delete(f"{i}.{match.start()}", f"{i}.{match.end()}")
        else:
            indent = len(line) - len(line.lstrip(' '))
            editor.insert(f"{i}.{indent}", "% ")

    editor.tag_add("sel", f"{start_line}.0", f"{end_line}.end")
    return "break"

# --- Mouse Actions ---

def on_double_click(event):
    """Selects the content within LaTeX command braces on double-click."""
    editor = event.widget
    index = editor.index(f"@{event.x},{event.y}")
    line, char = map(int, index.split('.'))
    line_content = editor.get(f"{line}.0", f"{line}.end")

    for match in re.finditer(r"\\(?:[a-zA-Z]+|emph|textbf|textit)(?:\\[^\\]*\])?\{([^}]*)", line_content):
        if match.start(1) <= char < match.end(1):
            start_abs = f"{line}.{match.start(1)}"
            end_abs = f"{line}.{match.end(1)}"
            editor.tag_remove("sel", "1.0", "end")
            editor.tag_add("sel", start_abs, end_abs)
            editor.mark_set("insert", start_abs)
            return "break"
    return None

# --- Setup ---

def setup_shortcuts(editor):
    """Binds all enhanced editing shortcuts to the editor widget."""
    editor.bind("<Control-w>", delete_word_left)
    editor.bind("<Control-BackSpace>", delete_word_left)
    editor.bind("<Control-Delete>", delete_word_right)
    
    editor.bind("<Control-Left>", move_word_left)
    editor.bind("<Control-Right>", move_word_right)
    editor.bind("<Control-Shift-Left>", select_word_left)
    editor.bind("<Control-Shift-Right>", select_word_right)
    
    editor.bind("<Alt-Up>", move_line_up)
    editor.bind("<Alt-Down>", move_line_down)
    
    editor.bind("<Control-slash>", toggle_comment)
    editor.bind("<Control-KP_Divide>", toggle_comment)
    
    editor.bind("<Tab>", handle_tab)
    editor.bind("<Shift-Tab>", handle_shift_tab)
    
    editor.bind("<Double-Button-1>", on_double_click)
