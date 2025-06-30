import tkinter as tk
import debug_console

def extract_editor_context(editor_widget, lines_before_cursor=5, lines_after_cursor=5):
    """
    Extracts text context from the editor widget around the current cursor position.
    """
    if not editor_widget:
        return ""

    try:
        cursor_index = editor_widget.index(tk.INSERT)
        current_line_num = int(cursor_index.split(".")[0])

        last_line_index_str = editor_widget.index("end-1c")
        total_lines = int(last_line_index_str.split(".")[0]) if last_line_index_str != "1.0" or editor_widget.get("1.0", "1.end") else 0

        start_line = max(1, current_line_num - lines_before_cursor)
        end_line = min(total_lines, current_line_num + lines_after_cursor)

        context_lines = [editor_widget.get(f"{i}.0", f"{i}.end") for i in range(start_line, end_line + 1)]
        return "\n".join(context_lines)
    except Exception as e:
        debug_console.log(f"Error getting editor context: {e}", level='ERROR')
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