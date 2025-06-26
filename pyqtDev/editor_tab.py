# File: editor_tab.py
import os
import re
from PyQt6 import QtWidgets, QtCore, QtGui
import editor_logic
import theme_manager

INDENT_WIDTH = 4

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.text_color = QtGui.QColor("#6a737d")
        self.text_color_current = QtGui.QColor("#d4d4d4")
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
        has_selection = self.editor.textCursor().hasSelection()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
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
        self.update()

class Editor(QtWidgets.QPlainTextEdit):  # CHANGED: QTextEdit -> QPlainTextEdit
    def __init__(self, parent=None, schedule_heavy_updates_callback=None):
        super().__init__(parent)
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback
        self.line_number_area = LineNumberArea(self)
        self.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.setUndoRedoEnabled(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setContentsMargins(0, 0, 0, 0)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.document().blockCountChanged.connect(self.update_line_number_area_width)
        self.verticalScrollBar().valueChanged.connect(self.line_number_area.update)
        self.cursorPositionChanged.connect(self._on_editor_event)
        self.textChanged.connect(self._on_editor_event)
        self.update_line_number_area_width(0)
        self.setFont(QtGui.QFont("Consolas", 12))

    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, new_block_count):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QtCore.QRect(cr.left(), cr.top(),
                                                 self.line_number_area_width(), cr.height()))

    def _on_editor_event(self):
        if self._schedule_heavy_updates_callback:
            self._schedule_heavy_updates_callback()
        self._highlight_current_line()

    def _highlight_current_line(self):
        extra_selections = []
        if not self.textCursor().hasSelection():
            # Use QTextEdit.ExtraSelection for QPlainTextEdit as well
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selection.format.setBackground(QtGui.QColor(theme_manager.get_theme_setting("current_line_bg", "#f8f8f8")))
            selection.format.setProperty(QtGui.QTextFormat.Property.FullWidthSelection, True)
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)
        self.line_number_area.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Tab:
            self._on_tab_key()
            return
        elif event.key() == QtCore.Qt.Key.Key_Backtab:
            self._on_shift_tab_key()
            return
        elif event.key() == QtCore.Qt.Key.Key_Backspace and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
            self._on_ctrl_backspace_key()
            return
        super().keyPressEvent(event)

    def _on_tab_key(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
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
            cursor.insertText(" " * INDENT_WIDTH)

    def _on_shift_tab_key(self):
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
                    cursor.deleteChar()
                    for _ in range(INDENT_WIDTH - 1):
                        cursor.deleteChar()
                elif text.startswith("\t"):
                    cursor.deleteChar()
                if cursor.position() >= end_block:
                    break
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.NextBlock)
        else:
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
            block = cursor.block()
            text = block.text()
            if text.startswith(" " * INDENT_WIDTH):
                for _ in range(INDENT_WIDTH):
                    cursor.deleteChar()
            elif text.startswith("\t"):
                cursor.deleteChar()
            else:
                leading_spaces_match = re.match(r"^\s*", text)
                if leading_spaces_match:
                    num_leading_spaces = len(leading_spaces_match.group(0))
                    if num_leading_spaces > 0:
                        for _ in range(num_leading_spaces):
                            cursor.deleteChar()
        cursor.endEditBlock()

    def _on_ctrl_backspace_key(self):
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.WordLeft, QtGui.QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

class EditorTab(QtWidgets.QWidget):
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
        self.editor = Editor(self, schedule_heavy_updates_callback=self._schedule_heavy_updates_callback)
        self.line_numbers = self.editor.line_number_area
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.line_numbers)
        main_layout.addWidget(self.editor)
        self.editor.textChanged.connect(self.update_tab_title)
        self.editor.document().contentsChanged.connect(self.update_tab_title)

    def get_content(self):
        return self.editor.toPlainText()

    def is_dirty(self):
        return self.editor.document().isModified()

    def update_tab_title(self):
        base_name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        title = f"{base_name}{'*' if self.is_dirty() else ''}"
        index = self.notebook.indexOf(self)
        if index != -1:
            self.notebook.setTabText(index, title)

    def load_file(self):
        if self._initial_content is not None:
            self.editor.setPlainText(self._initial_content)
            if self._initial_cursor_pos:
                cursor = self.editor.textCursor()
                cursor.setPosition(self._initial_cursor_pos)
                self.editor.setTextCursor(cursor)
            if self._initial_scroll_pos:
                self.editor.ensureCursorVisible()
            self.editor.document().setModified(self._is_dirty_override or False)
            self.update_tab_title()
            return
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.editor.setPlainText(content)
                    self.update_tab_title()
                    self.editor.document().setModified(False)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")
        else:
            self.update_tab_title()
            self.editor.document().setModified(False)

    def save_file(self, new_path=None):
        if new_path:
            self.file_path = new_path
        if not self.file_path:
            return False
        try:
            content = self.get_content()
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.update_tab_title()
            self.editor.document().setModified(False)
            return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error saving file:\n{e}")
            return False
