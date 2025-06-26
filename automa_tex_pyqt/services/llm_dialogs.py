# automa_tex_pyqt/services/llm_dialogs.py
"""
Manages dialog windows for LLM (Large Language Model) interactions.

This includes dialogs for generating text from a custom prompt and for
setting LLM keywords.
"""
from PyQt6 import QtWidgets, QtCore, QtGui
import os

# A list of common languages for the dropdown.
_LANGUAGES = [
    "English", "French", "Spanish", "German", "Italian", "Portuguese",
    "Dutch", "Russian", "Chinese (Simplified)", "Japanese", "Korean",
    "Arabic", "Hindi", "Bengali", "Turkish", "Polish", "Swedish",
    "Danish", "Norwegian", "Finnish", "Greek", "Hebrew", "Thai",
    "Vietnamese", "Indonesian", "Malay", "Czech", "Hungarian", "Romanian",
    "the same language as the prompt" # Special option
]

# To remember the last used language across dialog openings within a session.
_last_used_language = "English"

class GenerateTextDialog(QtWidgets.QDialog):
    def __init__(self, root_window, theme_setting_getter_func,
                 current_prompt_history_list, on_generate_request_callback,
                 on_history_entry_add_callback, initial_prompt_text=None,
                 is_latex_oriented_default=False):
        super().__init__(root_window)
        self.setWindowTitle("Custom AI Generation")
        self.setModal(True)
        self.resize(800, 600)

        self.theme_setting_getter_func = theme_setting_getter_func
        self.current_prompt_history_list = current_prompt_history_list
        self.on_generate_request_callback = on_generate_request_callback
        self.on_history_entry_add_callback = on_history_entry_add_callback

        # --- Theming ---
        self.setStyleSheet(self._get_dialog_stylesheet())

        # --- Main Splitter for History and Input ---
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(main_splitter)

        # --- Left Pane: History ListWidget ---
        history_frame = QtWidgets.QFrame()
        history_layout = QtWidgets.QVBoxLayout(history_frame)
        history_layout.setContentsMargins(0, 0, 5, 0)
        history_layout.addWidget(QtWidgets.QLabel("Prompt History:"))

        self.history_list_widget = QtWidgets.QListWidget()
        self.history_list_widget.setFont(QtGui.QFont("Segoe UI", 9))
        history_layout.addWidget(self.history_list_widget)

        self._populate_history_list()
        self.history_list_widget.itemSelectionChanged.connect(self._on_history_item_selected)

        main_splitter.addWidget(history_frame)
        main_splitter.setSizes([250, 550]) # Initial sizes

        # --- Right Pane: Prompt Input and Controls ---
        input_controls_frame = QtWidgets.QFrame()
        input_controls_layout = QtWidgets.QGridLayout(input_controls_frame)
        input_controls_layout.setContentsMargins(5, 0, 0, 0)

        input_controls_layout.addWidget(QtWidgets.QLabel("Your Prompt:"), 0, 0, 1, 2)
        self.text_prompt = QtWidgets.QTextEdit()
        self.text_prompt.setAcceptRichText(False)
        self.text_prompt.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.text_prompt.setFont(QtGui.QFont("Segoe UI", 10))
        if initial_prompt_text:
            self.text_prompt.setPlainText(initial_prompt_text)
        input_controls_layout.addWidget(self.text_prompt, 1, 0, 1, 2)

        # Context Line Inputs
        input_controls_layout.addWidget(QtWidgets.QLabel("Lines before cursor:"), 2, 0)
        self.entry_back = QtWidgets.QLineEdit("5")
        input_controls_layout.addWidget(self.entry_back, 2, 1)

        input_controls_layout.addWidget(QtWidgets.QLabel("Lines after cursor:"), 3, 0)
        self.entry_forward = QtWidgets.QLineEdit("0")
        input_controls_layout.addWidget(self.entry_forward, 3, 1)

        # Language Input with ComboBox
        input_controls_layout.addWidget(QtWidgets.QLabel("Response Language:"), 4, 0)
        self.lang_combobox = QtWidgets.QComboBox()
        self.lang_combobox.addItems(_LANGUAGES)
        global _last_used_language
        if _last_used_language in _LANGUAGES:
            self.lang_combobox.setCurrentText(_last_used_language)
        else:
            self.lang_combobox.setCurrentText("English")
        input_controls_layout.addWidget(self.lang_combobox, 4, 1)

        # LaTeX Oriented Checkbox
        self.is_latex_oriented_checkbox = QtWidgets.QCheckBox("LaTeX Oriented Generation")
        self.is_latex_oriented_checkbox.setChecked(is_latex_oriented_default)
        input_controls_layout.addWidget(self.is_latex_oriented_checkbox, 5, 0, 1, 2)

        # LLM Response Display Area (initially hidden)
        self.llm_response_label = QtWidgets.QLabel("LLM Response:")
        self.text_response = QtWidgets.QTextEdit()
        self.text_response.setReadOnly(True)
        self.text_response.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.text_response.setFont(QtGui.QFont("Segoe UI", 10))
        self.llm_response_label.hide()
        self.text_response.hide()
        input_controls_layout.addWidget(self.llm_response_label, 6, 0, 1, 2)
        input_controls_layout.addWidget(self.text_response, 7, 0, 1, 2)
        input_controls_layout.setRowStretch(7, 1) # Allow response text to expand

        # Generate Button
        self.generate_button = QtWidgets.QPushButton("Generate")
        self.generate_button.clicked.connect(self._handle_send_prompt_action)
        input_controls_layout.addWidget(self.generate_button, 8, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignCenter)

        main_splitter.addWidget(input_controls_frame)

        self.text_prompt.setFocus()

    def _get_dialog_stylesheet(self):
        # This should ideally be centralized in theme_manager
        dialog_bg = self.theme_setting_getter_func("root_bg", "#f0f0f0")
        text_bg = self.theme_setting_getter_func("editor_bg", "#ffffff")
        text_fg = self.theme_setting_getter_func("editor_fg", "#000000")
        sel_bg = self.theme_setting_getter_func("sel_bg", "#0078d4")
        sel_fg = self.theme_setting_getter_func("sel_fg", "#ffffff")
        insert_bg = self.theme_setting_getter_func("editor_insert_bg", "#000000")

        return f"""
            QDialog {{ background-color: {dialog_bg}; }}
            QLabel {{ color: {text_fg}; }}
            QTextEdit {{
                background-color: {text_bg};
                color: {text_fg};
                selection-background-color: {sel_bg};
                selection-color: {sel_fg};
                border: 1px solid #555; /* subtle border */
            }}
            QLineEdit {{
                background-color: {text_bg};
                color: {text_fg};
                selection-background-color: {sel_bg};
                selection-color: {sel_fg};
                border: 1px solid #555;
                padding: 2px;
            }}
            QListWidget {{
                background-color: {text_bg};
                color: {text_fg};
                selection-background-color: {sel_bg};
                selection-color: {sel_fg};
                border: 1px solid #555;
            }}
            QComboBox {{
                background-color: {text_bg};
                color: {text_fg};
                selection-background-color: {sel_bg};
                selection-color: {sel_fg};
                border: 1px solid #555;
                padding: 2px;
            }}
            QPushButton {{
                background-color: {self.theme_setting_getter_func("root_bg", "#f0f0f0")};
                color: {self.theme_setting_getter_func("fg_color", "#000000")};
                border: 1px solid {self.theme_setting_getter_func("panedwindow_sash", "#d0d0d0")};
                padding: 5px 10px;
            }}
            QSplitter::handle {{
                background-color: {self.theme_setting_getter_func("panedwindow_sash", "#d0d0d0")};
            }}
        """

    def _populate_history_list(self):
        self.history_list_widget.clear()
        if not self.current_prompt_history_list:
            self.history_list_widget.addItem("No history yet.")
            self.history_list_widget.setEnabled(False)
        else:
            self.history_list_widget.setEnabled(True)
            for item_user_prompt, _ in self.current_prompt_history_list:
                display_text = f"Q: {item_user_prompt[:100]}{'...' if len(item_user_prompt) > 100 else ''}"
                self.history_list_widget.addItem(display_text)

    def _on_history_item_selected(self):
        selected_items = self.history_list_widget.selectedItems()
        if selected_items:
            index = self.history_list_widget.row(selected_items[0])
            if 0 <= index < len(self.current_prompt_history_list):
                selected_user_prompt, selected_llm_response = self.current_prompt_history_list[index]
                self.text_prompt.setPlainText(selected_user_prompt)

                self.llm_response_label.show()
                self.text_response.show()
                self.text_response.setPlainText(selected_llm_response)
            else: # "No history yet." or invalid
                self.llm_response_label.hide()
                self.text_response.hide()
        else: # Deselection
            self.llm_response_label.hide()
            self.text_response.hide()

    def _handle_send_prompt_action(self):
        user_prompt = self.text_prompt.toPlainText().strip()
        try:
            num_back = int(self.entry_back.text())
            num_forward = int(self.entry_forward.text())
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Input Error", "Line counts must be integers.")
            return

        if not user_prompt:
            QtWidgets.QMessageBox.warning(self, "Warning", "The prompt is empty.")
            return

        global _last_used_language
        language = self.lang_combobox.currentText().strip()
        if not language:
            language = "the same language as the prompt"
        _last_used_language = language
        
        is_latex_oriented = self.is_latex_oriented_checkbox.isChecked()

        if self.on_history_entry_add_callback:
            self.on_history_entry_add_callback(user_prompt, is_latex_oriented)
        if self.on_generate_request_callback:
            self.on_generate_request_callback(user_prompt, num_back, num_forward, is_latex_oriented, language)

        self.accept() # Close the dialog

def show_generate_text_dialog(root_window, theme_setting_getter_func,
                              current_prompt_history_list, on_generate_request_callback,
                              on_history_entry_add_callback, initial_prompt_text=None,
                              is_latex_oriented_default=False):
    dialog = GenerateTextDialog(root_window, theme_setting_getter_func,
                                current_prompt_history_list, on_generate_request_callback,
                                on_history_entry_add_callback, initial_prompt_text,
                                is_latex_oriented_default)
    dialog.exec()

class SetLLMKeywordsDialog(QtWidgets.QDialog):
    def __init__(self, root_window, theme_setting_getter_func,
                 current_llm_keywords_list, on_save_keywords_callback):
        super().__init__(root_window)
        self.setWindowTitle("Set LLM Keywords")
        self.setModal(True)
        self.resize(400, 300)

        self.theme_setting_getter_func = theme_setting_getter_func
        self.on_save_keywords_callback = on_save_keywords_callback

        self.setStyleSheet(self._get_dialog_stylesheet())

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(QtWidgets.QLabel("Enter keywords (one per line or comma-separated):"))

        self.keyword_text_widget = QtWidgets.QTextEdit()
        self.keyword_text_widget.setFont(QtGui.QFont("Segoe UI", 10))
        if current_llm_keywords_list:
            self.keyword_text_widget.setPlainText("\n".join(current_llm_keywords_list))
        main_layout.addWidget(self.keyword_text_widget)

        save_button = QtWidgets.QPushButton("Save Keywords")
        save_button.clicked.connect(self._save_keywords_action_internal)
        main_layout.addWidget(save_button)

        self.keyword_text_widget.setFocus()

    def _get_dialog_stylesheet(self):
        dialog_bg = self.theme_setting_getter_func("root_bg", "#f0f0f0")
        text_bg = self.theme_setting_getter_func("editor_bg", "#ffffff")
        text_fg = self.theme_setting_getter_func("editor_fg", "#000000")
        sel_bg = self.theme_setting_getter_func("sel_bg", "#0078d4")
        sel_fg = self.theme_setting_getter_func("sel_fg", "#ffffff")

        return f"""
            QDialog {{ background-color: {dialog_bg}; }}
            QLabel {{ color: {text_fg}; }}
            QTextEdit {{
                background-color: {text_bg};
                color: {text_fg};
                selection-background-color: {sel_bg};
                selection-color: {sel_fg};
                border: 1px solid #555;
            }}
            QPushButton {{
                background-color: {self.theme_setting_getter_func("root_bg", "#f0f0f0")};
                color: {self.theme_setting_getter_func("fg_color", "#000000")};
                border: 1px solid {self.theme_setting_getter_func("panedwindow_sash", "#d0d0d0")};
                padding: 5px 10px;
            }}
        """

    def _save_keywords_action_internal(self):
        input_text = self.keyword_text_widget.toPlainText().strip()
        new_keywords = []
        if input_text:
            raw_keywords = []
            for line in input_text.split('\n'):
                raw_keywords.extend(kw.strip() for kw in line.split(','))
            new_keywords = [kw for kw in raw_keywords if kw]

        if self.on_save_keywords_callback:
            self.on_save_keywords_callback(new_keywords)

        self.accept() # Close the dialog

def show_set_llm_keywords_dialog(root_window, theme_setting_getter_func,
                                 current_llm_keywords_list, on_save_keywords_callback):
    dialog = SetLLMKeywordsDialog(root_window, theme_setting_getter_func,
                                  current_llm_keywords_list, on_save_keywords_callback)
    dialog.exec()

class EditPromptsDialog(QtWidgets.QDialog):
    def __init__(self, root_window, theme_setting_getter_func,
                 current_prompts, default_prompts, on_save_callback):
        super().__init__(root_window)
        self.setWindowTitle("Edit LLM Prompt Templates")
        self.setModal(True)
        self.resize(1200, 700)

        self.theme_setting_getter_func = theme_setting_getter_func
        self.current_prompts = current_prompts
        self.default_prompts = default_prompts
        self.on_save_callback = on_save_callback

        self.setStyleSheet(self._get_dialog_stylesheet())

        main_layout = QtWidgets.QVBoxLayout(self)

        # Warning Message
        warning_label = QtWidgets.QLabel(
            "⚠️ Warning: Modifying these prompts can significantly affect AI behavior and performance. "
            "Changes are saved per-document.\n"
            "Available placeholders for Completion: {previous_context}, {current_phrase_start}, {keywords}\n"
            "Available placeholders for Generation: {user_prompt}, {keywords}, {context}, {language}"
        )
        warning_label.setWordWrap(True)
        main_layout.addWidget(warning_label)

        # Main Splitter (HORIZONTAL for side-by-side)
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        self.text_editors = {} # Store references to QTextEdit widgets
        self.labels = {} # Store references to QLabel for "Using Default" status

        prompt_types = [
            ("completion", "Completion Prompt ('✨ Complete')", "completion"),
            ("latex_code_generation", "LaTeX Code Generation Prompt ('💻 Code LaTeX')", "latex_code_generation"),
            ("generation", "Generation Prompt ('🎯 Generate')", "generation")
        ]

        for key, title, default_key in prompt_types:
            frame = QtWidgets.QFrame()
            frame_layout = QtWidgets.QVBoxLayout(frame)
            
            is_default = (self.current_prompts.get(key, "").strip() == self.default_prompts.get(default_key, "").strip())
            label_text = f"{title}{' (Using Default)' if is_default else ''}"
            self.labels[key] = QtWidgets.QLabel(label_text)
            frame_layout.addWidget(self.labels[key])

            text_edit = QtWidgets.QTextEdit()
            text_edit.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
            text_edit.setFont(QtGui.QFont("Consolas", 10))
            text_edit.setPlainText(self.current_prompts.get(key, self.default_prompts.get(default_key, "")))
            self.text_editors[key] = text_edit
            frame_layout.addWidget(text_edit)

            button_frame = QtWidgets.QFrame()
            button_layout = QtWidgets.QHBoxLayout(button_frame)
            apply_button = QtWidgets.QPushButton("Apply")
            apply_button.clicked.connect(self._apply_changes)
            button_layout.addWidget(apply_button)

            restore_button = QtWidgets.QPushButton("Restore Default")
            restore_button.clicked.connect(lambda checked, k=key, dk=default_key: self._restore_default(k, dk))
            button_layout.addWidget(restore_button)
            frame_layout.addWidget(button_frame)

            main_splitter.addWidget(frame)

        # Bottom Bar with Close Button
        bottom_bar = QtWidgets.QFrame()
        bottom_layout = QtWidgets.QHBoxLayout(bottom_bar)
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self._close_window)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(close_button)
        main_layout.addWidget(bottom_bar)

        # Bind Ctrl+S for saving without closing
        save_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self._apply_changes)

    def _get_dialog_stylesheet(self):
        dialog_bg = self.theme_setting_getter_func("root_bg", "#f0f0f0")
        text_bg = self.theme_setting_getter_func("editor_bg", "#ffffff")
        text_fg = self.theme_setting_getter_func("editor_fg", "#000000")
        sel_bg = self.theme_setting_getter_func("sel_bg", "#0078d4")
        sel_fg = self.theme_setting_getter_func("sel_fg", "#ffffff")

        return f"""
            QDialog {{ background-color: {dialog_bg}; }}
            QLabel {{ color: {text_fg}; }}
            QTextEdit {{
                background-color: {text_bg};
                color: {text_fg};
                selection-background-color: {sel_bg};
                selection-color: {sel_fg};
                border: 1px solid #555;
            }}
            QPushButton {{
                background-color: {self.theme_setting_getter_func("root_bg", "#f0f0f0")};
                color: {self.theme_setting_getter_func("fg_color", "#000000")};
                border: 1px solid {self.theme_setting_getter_func("panedwindow_sash", "#d0d0d0")};
                padding: 5px 10px;
            }}
            QSplitter::handle {{
                background-color: {self.theme_setting_getter_func("panedwindow_sash", "#d0d0d0")};
            }}
        """

    def _update_default_status_labels(self):
        for key, label in self.labels.items():
            current_text = self.text_editors[key].toPlainText().strip()
            default_text = self.default_prompts.get(key, "").strip()
            is_default_now = (current_text == default_text)
            
            # Reconstruct the label text based on original title and default status
            original_title = ""
            for _, title, _ in [
                ("completion", "Completion Prompt ('✨ Complete')", "completion"),
                ("latex_code_generation", "LaTeX Code Generation Prompt ('💻 Code LaTeX')", "latex_code_generation"),
                ("generation", "Generation Prompt ('🎯 Generate')", "generation")
            ]:
                if key in title.lower(): # Simple check to find original title
                    original_title = title
                    break
            
            label.setText(f"{original_title}{' (Using Default)' if is_default_now else ''}")

    def _apply_changes(self):
        new_completion = self.text_editors["completion"].toPlainText().strip()
        new_generation = self.text_editors["generation"].toPlainText().strip()
        new_latex_code_generation = self.text_editors["latex_code_generation"].toPlainText().strip()

        if self.on_save_callback:
            self.on_save_callback(new_completion, new_generation, new_latex_code_generation)

        self.current_prompts["completion"] = new_completion
        self.current_prompts["generation"] = new_generation
        self.current_prompts["latex_code_generation"] = new_latex_code_generation

        self._update_default_status_labels()

    def _restore_default(self, key, default_key):
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Restore",
            f"Are you sure you want to restore the default for the {key.replace('_', ' ').title()} prompt?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.text_editors[key].setPlainText(self.default_prompts.get(default_key, ""))
            self._update_default_status_labels()

    def _close_window(self):
        current_completion = self.text_editors["completion"].toPlainText().strip()
        current_latex_code_generation = self.text_editors["latex_code_generation"].toPlainText().strip()
        current_generation = self.text_editors["generation"].toPlainText().strip()

        has_changes = (current_completion != self.current_prompts.get("completion", "").strip() or
                       current_latex_code_generation != self.current_prompts.get("latex_code_generation", "").strip() or
                       current_generation != self.current_prompts.get("generation", "").strip())

        if has_changes:
            reply = QtWidgets.QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self._apply_changes()
                self.accept()
            elif reply == QtWidgets.QMessageBox.StandardButton.No:
                self.accept()
            # else: Cancel, do nothing
        else:
            self.accept()

def show_edit_prompts_dialog(root_window, theme_setting_getter_func,
                             current_prompts, default_prompts, on_save_callback):
    dialog = EditPromptsDialog(root_window, theme_setting_getter_func,
                               current_prompts, default_prompts, on_save_callback)
    dialog.exec()