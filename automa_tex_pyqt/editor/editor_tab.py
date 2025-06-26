import os
import re
from PyQt6 import QtWidgets, QtCore, QtGui

# Import editor_logic for syntax highlighting and outline updates
from editor import editor_logic

INDENT_WIDTH = 4 # Define indentation width in spaces

class LineNumberArea(QtWidgets.QWidget):
    """A QWidget to display line numbers for a QTextEdit widget."""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.text_color = QtGui.QColor("#6a737d") # Default color, will be overridden by theme
        self.text_color_current = QtGui.QColor("#d4d4d4") # Default current line color, will be overridden by theme
        self.bg_color = QtGui.QColor("#f0f0f0")
        
        self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

    def sizeHint(self):
        return QtCore.QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(event.rect(), self.bg_color)

        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + int(self.editor.blockBoundingRect(block).height())

        current_line_number = self.editor.textCursor().blockNumber()
        
        # Check for any selection
        has_selection = self.editor.textCursor().hasSelection()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
                # Determine font and color for the line number
                if not has_selection and block_number == current_line_number:
                    painter.setPen(self.text_color_current)
                    font = self.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(self.text_color)
                    font = self.font()
                    font.setBold(False)
                    painter.setFont(font)

                painter.drawText(0, top, self.width() - 5, self.editor.fontMetrics().height(),
                                 QtCore.Qt.AlignmentFlag.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + int(self.editor.blockBoundingRect(block).height())
            block_number += 1

    def update_theme(self, text_color, bg_color, current_line_text_color):
        self.text_color = QtGui.QColor(text_color)
        self.bg_color = QtGui.QColor(bg_color)
        self.text_color_current = QtGui.QColor(current_line_text_color)
        self.update() # Request a repaint

class Editor(QtWidgets.QTextEdit):
    """Custom QTextEdit with line numbers and custom behavior."""
    def __init__(self, parent=None, schedule_heavy_updates_callback=None):
        super().__init__(parent)
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback

        self.line_number_area = LineNumberArea(self)
        
        self.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.setUndoRedoEnabled(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame) # No border
        self.setContentsMargins(0, 0, 0, 0)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Signals for updating line numbers and syntax highlighting
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self._on_editor_event)
        self.textChanged.connect(self._on_editor_event)

        self.update_line_number_area_width(0) # Initial width calculation

        # Set default font
        self.setFont(QtGui.QFont("Consolas", 12))

    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        
        # Use fontMetrics from the editor itself
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, new_block_count):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        # This ensures the width is updated if the number of lines changes significantly
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QtCore.QRect(cr.left(), cr.top(),
                                                 self.line_number_area_width(), cr.height()))

    def _on_editor_event(self):
        """
        Central handler for events that should trigger updates.
        This includes key presses, mouse clicks, and configuration changes.
        """
        # This signal is emitted when text changes or cursor position changes.
        # It's a good place to trigger debounced updates.
        if self._schedule_heavy_updates_callback:
            self._schedule_heavy_updates_callback()
        self._highlight_current_line()

    def _highlight_current_line(self):
        """Highlights the current line in the editor."""
        extra_selections = []
        if not self.textCursor().hasSelection(): # Only highlight if no selection
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection() # Ensure no text is selected
            selection.format.setBackground(QtGui.QColor("#f8f8f8")) # Default light theme
            selection.format.setProperty(QtGui.QTextFormat.Property.FullWidthSelection, True)
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)
        self.line_number_area.update() # Request repaint for line numbers

    def keyPressEvent(self, event):
        """Override keyPressEvent for custom Tab/Shift+Tab behavior."""
        if event.key() == QtCore.Qt.Key.Key_Tab:
            self._on_tab_key()
            return # Prevent default tab behavior
        elif event.key() == QtCore.Qt.Key.Key_Backtab: # Shift+Tab
            self._on_shift_tab_key()
            return # Prevent default shift+tab behavior
        elif event.key() == QtCore.Qt.Key.Key_Backspace and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
            self._on_ctrl_backspace_key()
            return # Prevent default Ctrl+Backspace behavior
        super().keyPressEvent(event)

    def _on_tab_key(self):
        """Handles the Tab key for indentation."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            # Multi-line selection: indent all selected lines
            start_block = cursor.selectionStart()
            end_block = cursor.selectionEnd()
            
            cursor.beginEditBlock()
            cursor.setPosition(start_block)
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
            
            while True:
                cursor.insertText(" " * INDENT_WIDTH)
                if cursor.position() >= end_block:
                    break
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.NextBlock)
            cursor.endEditBlock()
        else:
            # No selection: insert spaces at cursor
            cursor.insertText(" " * INDENT_WIDTH)

    def _on_shift_tab_key(self):
        """Handles Shift+Tab for unindentation."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        if cursor.hasSelection():
            start_block = cursor.selectionStart()
            end_block = cursor.selectionEnd()
            
            cursor.setPosition(start_block)
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
            
            while True:
                block = cursor.block()
                text = block.text()
                if text.startswith(" " * INDENT_WIDTH):
                    cursor.deleteChar() # Delete first char
                    for _ in range(INDENT_WIDTH - 1):
                        cursor.deleteChar()
                elif text.startswith("\t"):
                    cursor.deleteChar()
                
                if cursor.position() >= end_block:
                    break
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.NextBlock)
        else:
            # No selection: unindent current line
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
            block = cursor.block()
            text = block.text()
            if text.startswith(" " * INDENT_WIDTH):
                for _ in range(INDENT_WIDTH):
                    cursor.deleteChar()
            elif text.startswith("\t"):
                cursor.deleteChar()
            else:
                # If less than INDENT_WIDTH spaces, remove all leading spaces
                leading_spaces_match = re.match(r"^\s*", text)
                if leading_spaces_match:
                    num_leading_spaces = len(leading_spaces_match.group(0))
                    if num_leading_spaces > 0:
                        for _ in range(num_leading_spaces):
                            cursor.deleteChar()
        cursor.endEditBlock()

    def _on_ctrl_backspace_key(self):
        """Handles Ctrl+Backspace for deleting a word backwards."""
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.WordLeft, QtGui.QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

class EditorTab(QtWidgets.QWidget):
    """Represents a single tab in the editor notebook."""
    def __init__(self, parent_notebook, file_path=None, schedule_heavy_updates_callback=None,
                 initial_content=None, initial_cursor_pos=None, initial_scroll_pos=None, is_dirty_override=None):
        super().__init__(parent_notebook)
        self.notebook = parent_notebook
        self.file_path = file_path
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback

        self._initial_content = initial_content
        self._initial_cursor_pos = initial_cursor_pos
        self._initial_scroll_pos = initial_scroll_pos
        self._is_dirty_override = is_dirty_override

        self.last_content_for_outline_parsing = ""
        self.last_parsed_outline_structure = []

        # --- Editor Widgets for this tab ---
        self.editor = Editor(self, schedule_heavy_updates_callback=self._schedule_heavy_updates_callback)
        self.line_numbers = self.editor.line_number_area # Reference to the line number area

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0) # No spacing between line numbers and editor
        main_layout.addWidget(self.line_numbers)
        main_layout.addWidget(self.editor)

        # Connect textChanged signal to update tab title
        self.editor.textChanged.connect(self.update_tab_title)
        self.editor.document().contentsChanged.connect(self.update_tab_title)

    def get_content(self):
        """Returns the full content of the editor widget."""
        return self.editor.toPlainText()

    def is_dirty(self):
        """Checks if the editor content has changed since the last save."""
        return self.editor.document().isModified()

    def update_tab_title(self):
        """Updates the notebook tab text to show a '*' if the file is dirty."""
        base_name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        title = f"{base_name}{'*' if self.is_dirty() else ''}"
        index = self.notebook.indexOf(self)
        if index != -1:
            self.notebook.setTabText(index, title)

    def load_file(self):
        """Loads content from self.file_path into the editor."""
        if self._initial_content is not None:
            self.editor.setPlainText(self._initial_content)
            if self._initial_cursor_pos:
                cursor = self.editor.textCursor()
                cursor.setPosition(self._initial_cursor_pos)
                self.editor.setTextCursor(cursor)
            if self._initial_scroll_pos:
                # PyQt's scroll position is different, this might need adjustment
                # For simplicity, we'll just ensure cursor is visible
                self.editor.ensureCursorVisible()

            editor_logic.apply_syntax_highlighting(self.editor, full_document=True)
            self.editor.document().setModified(self._is_dirty_override or False)
            self.update_tab_title()
            return

        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.editor.setPlainText(content)
                    self.update_tab_title()
                    
                    editor_logic.apply_syntax_highlighting(self.editor, full_document=True)
                    self.editor.document().setModified(False) # Set modified state to False after load
            except Exception as e:
                QtWidgets.QMessageBox.showerror(self, "Error", f"Could not open file:\n{e}")
        else:
            self.update_tab_title()
            editor_logic.apply_syntax_highlighting(self.editor, full_document=True)
            self.editor.document().setModified(False)

    def save_file(self, new_path=None):
        """
        Saves the editor content. If new_path is provided, it's a 'Save As' operation.
        Returns True on success, False on failure.
        """
        if new_path:
            self.file_path = new_path
        
        if not self.file_path:
            return False # Should have been handled by a 'save as' dialog before calling this

        try:
            content = self.get_content()
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.update_tab_title()
            self.editor.document().setModified(False) # Set modified state to False after save
            return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error saving file:\n{e}")
            return False