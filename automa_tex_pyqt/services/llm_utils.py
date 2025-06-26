# File: llm_utils.py
# automa_tex_pyqt/services/llm_utils.py
"""
Utility functions for LLM (Large Language Model) operations.

This module includes functions for extracting text context from the editor
and for processing text completions from the LLM.
"""
from PyQt6 import QtGui

def extract_editor_context(editor_widget, lines_before_cursor=5, lines_after_cursor=5):
    """
    Extracts text context from the editor widget around the current cursor position.

    Args:
        editor_widget (QTextEdit): The PyQt QTextEdit widget (the editor).
        lines_before_cursor (int): Number of lines to extract before the cursor line.
        lines_after_cursor (int): Number of lines to extract after the cursor line.

    Returns:
        str: A string containing the extracted context, with lines separated by newlines.
             Returns an empty string if the editor widget is not available or on error.
    """
    if not editor_widget:
        return ""

    try:
        cursor = editor_widget.textCursor()
        current_block = cursor.blockNumber()
        document = editor_widget.document()
        total_blocks = document.blockCount()

        start_block_num = max(0, current_block - lines_before_cursor)
        end_block_num = min(total_blocks - 1, current_block + lines_after_cursor)

        context_lines = []
        for i in range(start_block_num, end_block_num + 1):
            block = document.findBlockByNumber(i)
            context_lines.append(block.text())

        return "\n".join(context_lines)
    except Exception as e:
        print(f"Error getting context: {e}")
        return ""

def remove_prefix_overlap_from_completion(text_before_completion, llm_generated_completion):
    """
    Removes redundant overlap if the LLM completion starts by repeating the input text.
    This comparison is case-insensitive and word-based.
    """
    start_words = text_before_completion.strip().split()
    completion_words = llm_generated_completion.strip().split()

    if not start_words or not completion_words:
        return llm_generated_completion

    overlap_word_count = 0
    for i in range(min(len(start_words), len(completion_words)), 0, -1):
        if [w.lower() for w in start_words[-i:]] == [w.lower() for w in completion_words[:i]]:
            overlap_word_count = i
            break

    return " ".join(completion_words[overlap_word_count:]).strip()
