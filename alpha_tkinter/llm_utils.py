# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\llm_utils.py
"""
Utility functions for LLM (Large Language Model) operations.

This module includes functions for extracting text context from the editor
and for processing text completions from the LLM.
"""
import tkinter as tk

def extract_editor_context(editor_widget, lines_before_cursor=5, lines_after_cursor=5):
    """
    Extracts text context from the editor widget around the current cursor position.

    Args:
        editor_widget (tk.Text): The Tkinter Text widget (the editor).
        lines_before_cursor (int): Number of lines to extract before the cursor line.
        lines_after_cursor (int): Number of lines to extract after the cursor line.

    Returns:
        str: A string containing the extracted context, with lines separated by newlines.
             Returns an empty string if the editor widget is not available or on error.
    """
    if not editor_widget:
        return ""

    try:
        cursor_index = editor_widget.index(tk.INSERT)
        current_line_num = int(cursor_index.split(".")[0])

        # Get total lines, handling empty editor case
        last_line_index_str = editor_widget.index("end-1c")
        total_lines = int(last_line_index_str.split(".")[0]) if last_line_index_str != "1.0" or editor_widget.get("1.0", "1.end") else 0

        start_line = max(1, current_line_num - lines_before_cursor)
        end_line = min(total_lines, current_line_num + lines_after_cursor)

        context_lines = []
        # Iterate from start_line to end_line (inclusive)
        for i in range(start_line, end_line + 1):
            line_text = editor_widget.get(f"{i}.0", f"{i}.end")
            context_lines.append(line_text)

        return "\n".join(context_lines)
    except Exception as e:
        print(f"Error getting context: {e}")
        return ""

def remove_prefix_overlap_from_completion(text_before_completion, llm_generated_completion):
    """Removes redundant overlap if the LLM completion starts by repeating the input text."""
    start_words = text_before_completion.split()
    completion_words = llm_generated_completion.split()

    overlap_length = 0
    for i in range(1, min(len(start_words), len(completion_words)) + 1):
        if start_words[-i:] == completion_words[:i]:
            overlap_length = i
    return " ".join(completion_words[overlap_length:]).strip()