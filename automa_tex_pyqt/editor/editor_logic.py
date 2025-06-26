import re
import os
from datetime import datetime
from PyQt6 import QtWidgets, QtCore, QtGui

outline_tree = None
get_current_tab_func = None # Callback to get the current tab from the GUI manager

def initialize_editor_logic(tree_widget, get_current_tab_callback):
    """Sets the global reference to the outline tree."""
    global outline_tree
    global get_current_tab_func
    outline_tree = tree_widget
    get_current_tab_func = get_current_tab_callback

    # Connect outline tree selection to go_to_section
    outline_tree.itemClicked.connect(lambda item: go_to_section(get_current_tab_func().editor if get_current_tab_func() else None, item))

def update_outline_tree(editor):
    """
    Updates the QTreeWidget with LaTeX section structure.
    To improve performance, it uses a per-tab cache to avoid re-parsing the
    entire document unless the content has actually changed.
    """
    if not outline_tree or not editor:
        return

    current_tab = get_current_tab_func()
    if not current_tab or current_tab.editor != editor:
        return

    content = editor.toPlainText()
    if content == current_tab.last_content_for_outline_parsing:
        return

    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [Perf] update_outline_tree: Re-parsing document structure.")

    lines = content.split("\n")
    
    current_outline_structure = []

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        for level, cmd in enumerate(["section", "subsection", "subsubsection"], 1):
            match = re.match(rf"\\{cmd}\*?(?:\[[^\]]*\])?{{([^}}]*)}}", stripped_line)
            if match:
                title = match.group(1).strip()
                current_outline_structure.append((level, title, i + 1))
                break

    if current_outline_structure != current_tab.last_parsed_outline_structure:
        outline_tree.clear() # Clear existing tree

        parents_for_tree = {0: outline_tree.invisibleRootItem()} # Map level to parent QTreeWidgetItem
        for level, title, line_num in current_outline_structure:
            parent_item = parents_for_tree.get(level - 1)
            if parent_item:
                node_item = QtWidgets.QTreeWidgetItem(parent_item, [title])
                node_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, line_num) # Store line number
                parents_for_tree[level] = node_item
                for deeper in range(level + 1, 4):
                    if deeper in parents_for_tree:
                        del parents_for_tree[deeper]

        current_tab.last_parsed_outline_structure = current_outline_structure

    current_tab.last_content_for_outline_parsing = content

def go_to_section(editor, item):
    """Scrolls the editor to the selected section in the outline tree."""
    if not editor or not item:
        return

    line_num = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
    if line_num is not None:
        cursor = editor.textCursor()
        block = editor.document().findBlockByLineNumber(line_num - 1) # Line numbers are 0-indexed in QTextDocument
        if block.isValid():
            cursor.setPosition(block.position())
            editor.setTextCursor(cursor)
            editor.ensureCursorVisible()

def apply_syntax_highlighting(editor, full_document=False):
    """
    Applies syntax highlighting to the text widget.
    If full_document is True, applies to the entire document.
    Otherwise, applies only to the visible portion.
    """
    scope = "full document" if full_document else "visible area"
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [Perf] apply_syntax_highlighting: Highlighting {scope}.")

    cursor = QtGui.QTextCursor(editor.document())
    
    # Define formats (these should ideally come from theme_manager)
    comment_format = QtGui.QTextCharFormat()
    comment_format.setForeground(QtGui.QColor("#608b4e")) # Dark theme green
    comment_format.setFontItalic(True)

    command_format = QtGui.QTextCharFormat()
    command_format.setForeground(QtGui.QColor("#569cd6")) # Dark theme blue

    brace_format = QtGui.QTextCharFormat()
    brace_format.setForeground(QtGui.QColor("#c586c0")) # Dark theme purple

    # Clear existing formats in the target range
    if full_document:
        cursor.select(QtGui.QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QtGui.QTextCharFormat()) # Clear all formats
        start_pos = 0
        end_pos = editor.document().characterCount() - 1
    else:
        # Get visible area
        viewport_rect = editor.viewport().rect()
        top_left = editor.mapToGlobal(viewport_rect.topLeft())
        bottom_right = editor.mapToGlobal(viewport_rect.bottomRight())

        start_cursor = editor.cursorForPosition(editor.mapFromGlobal(top_left))
        end_cursor = editor.cursorForPosition(editor.mapFromGlobal(bottom_right))

        start_block = start_cursor.blockNumber()
        end_block = end_cursor.blockNumber()

        # Expand to full lines and add buffer
        start_pos = editor.document().findBlockByLineNumber(max(0, start_block - 2)).position()
        end_pos = editor.document().findBlockByLineNumber(min(editor.document().blockCount() - 1, end_block + 2)).position() + editor.document().findBlockByLineNumber(min(editor.document().blockCount() - 1, end_block + 2)).length()

        # Clear formats in the visible range
        temp_cursor = QtGui.QTextCursor(editor.document())
        temp_cursor.setPosition(start_pos)
        temp_cursor.setPosition(end_pos, QtGui.QTextCursor.MoveMode.KeepAnchor)
        temp_cursor.setCharFormat(QtGui.QTextCharFormat())

    # Get text content for the range
    text_in_range = editor.document().toPlainText()[start_pos:end_pos]

    # Apply highlighting for each pattern
    def apply_format(pattern, format_obj):
        for match in re.finditer(pattern, text_in_range):
            start = start_pos + match.start()
            end = start_pos + match.end()
            
            temp_cursor = QtGui.QTextCursor(editor.document())
            temp_cursor.setPosition(start)
            temp_cursor.setPosition(end, QtGui.QTextCursor.MoveMode.KeepAnchor)
            temp_cursor.mergeCharFormat(format_obj)

    apply_format(r"%[^\n]*", comment_format)
    apply_format(r"\\[a-zA-Z@]+", command_format)
    apply_format(r"[{}]", brace_format)

def extract_section_structure(content, position_index):
    """
    Extracts the current section, subsection, subsubsection titles
    based on the cursor position.
    """
    lines = content[:position_index].split("\n")

    section = "default"
    subsection = "default"
    subsubsection = "default"

    for line in lines:
        if r"\section{" in line:
            match = re.search(r"\\section\{(.+?)\}", line)
            if match:
                section = match.group(1).strip().replace(" ", "_").replace("{", "").replace("}", "")
                subsection = "default"
                subsubsection = "default"
        elif r"\subsection{" in line:
            match = re.search(r"\\subsection\{(.+?)\}", line)
            if match:
                subsection = match.group(1).strip().replace(" ", "_").replace("{", "").replace("}", "")
                subsubsection = "default"
        elif r"\subsubsection{" in line:
            match = re.search(r"\\subsubsection\{(.+?)\}", line)
            if match:
                subsubsection = match.group(1).strip().replace(" ", "_").replace("{", "").replace("}", "")

    section = re.sub(r'[^\w\-_\.]', '', section)
    subsection = re.sub(r'[^\w\-_\.]', '', subsection)
    subsubsection = re.sub(r'[^\w\-_\.]', '', subsubsection)

    return section, subsection, subsubsection

def paste_image():
    """Pastes an image from the clipboard into the editor as a LaTeX figure."""
    current_tab = get_current_tab_func()
    if not current_tab: return
    editor = current_tab.editor
    if not editor:
        return

    clipboard = QtWidgets.QApplication.clipboard()
    image = clipboard.image()

    if image.isNull():
        QtWidgets.QMessageBox.warning(None, "Warning", "No image found in clipboard.")
        return

    try:
        base_dir = os.path.dirname(current_tab.file_path) if current_tab.file_path else "."

        content = editor.toPlainText()
        cursor_pos = editor.textCursor().position()
        section, subsection, subsubsection = extract_section_structure(content, cursor_pos)

        fig_dir_path = os.path.join(base_dir, "figures", section, subsection, subsubsection)
        os.makedirs(fig_dir_path, exist_ok=True)

        index = 1
        while True:
            file_name = f"fig{index}.png"
            full_file_path = os.path.join(fig_dir_path, file_name)
            if not os.path.exists(full_file_path):
                break
            index += 1

        image.save(full_file_path, "PNG")

        latex_path = os.path.relpath(full_file_path, base_dir).replace("\\", "/")

        latex_code = (
            "\n\\begin{figure}[h!]\n"
            "    \\centering\n"
            f"    \\includegraphics[width=0.8\\textwidth]{{{latex_path}}}\n"
            f"    \\caption{{Caption here}}\n"
            f"    \\label{{fig:{section}_{subsection}_{index}}}\n"
            "\\end{figure}\n"
        )

        editor.textCursor().insertText(latex_code)

    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Error", f"Error pasting image:\n{str(e)}")