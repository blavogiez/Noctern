import tkinter as tk
from tkinter import messagebox
import debug_console

def find_insertion_point(content, start_pos):
    # Find the end of the current line
    line_end = content.find('\n', start_pos)
    if line_end == -1:
        line_end = len(content)
    
    # Look for a good place to insert: end of line seems a reasonable default
    return line_end

def check_and_fix_brackets(editor_widget):
    content = editor_widget.get("1.0", tk.END)
    stack = []
    issues = []
    i = 0
    while i < len(content):
        char = content[i]
        if char == '\\':
            # Skip escaped characters
            i += 2
            continue
        if char == '{':
            stack.append(('{', i))
        elif char == '}':
            if not stack or stack[-1][0] != '{':
                issues.append(('extra_closing', i))
            else:
                stack.pop()
        i += 1

    # Unclosed brackets are remaining items in the stack
    for item, pos in stack:
        issues.append(('unclosed_opening', pos))

    debug_console.log(f"Bracket issues detected: {issues}", level='DEBUG')

    if not issues:
        return True

    # Sort issues by position
    issues.sort(key=lambda x: x[1], reverse=True)
    
    fixed_content = list(content)
    
    for issue_type, pos in issues:
        if issue_type == 'unclosed_opening':
            # Find a place to insert the closing bracket
            insertion_point = find_insertion_point(content, pos)
            fixed_content.insert(insertion_point, '}')
        elif issue_type == 'extra_closing':
            # For extra closing brackets, we can just remove them
            fixed_content.pop(pos)

    fixed_content_str = "".join(fixed_content)

    # Display a dialog
    response = messagebox.askyesno(
        "Bracket Mismatch Detected",
        f"It seems you have bracket mismatches. A proposed fix is available.\n\n"
        f"Do you want to apply this fix?"
    )
    
    debug_console.log(f"User response to bracket fix prompt: {response}", level='DEBUG')

    if response:
        editor_widget.delete("1.0", tk.END)
        editor_widget.insert("1.0", fixed_content_str)
        return True
    else:
        return False
