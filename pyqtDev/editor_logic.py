# File: latex_translator.py
import os
import threading
from PyQt6 import QtWidgets, QtCore, QtGui
import theme_manager

try:
    import argostranslate.package
    import argostranslate.translate
    _ARGOS_TRANSLATE_AVAILABLE = True
except ImportError:
    _ARGOS_TRANSLATE_AVAILABLE = False
    print("Warning: argostranslate module not found. Translation functionality will be disabled.")

# Global variables to store references from the main application
_root = None
_theme_setting_getter_func = None
_show_temporary_status_message_func = None
_active_editor_getter_func = None
_active_filepath_getter_func = None

def initialize_translator(root_ref, theme_getter, status_message_func, active_editor_getter, active_filepath_getter):
    """
    Initializes the LaTeX translator service with necessary references from the main application.
    """
    global _root, _theme_setting_getter_func, _show_temporary_status_message_func
    global _active_editor_getter_func, _active_filepath_getter_func
    _root = root_ref
    _theme_setting_getter_func = theme_getter
    _show_temporary_status_message_func = status_message_func
    _active_editor_getter_func = active_editor_getter
    _active_filepath_getter_func = active_filepath_getter

    # Connect button and action
    _root.btn_translate.clicked.connect(open_translate_dialog)
    _root.action_translate.triggered.connect(open_translate_dialog)

def _get_available_translation_pairs():
    """
    Gets available translation pairs (source -> target) from argostranslate.
    Returns a list of tuples: (from_lang_code, to_lang_code, display_name).
    """
    if not _ARGOS_TRANSLATE_AVAILABLE:
        return []
    try:
        available_packages = argostranslate.package.get_available_packages()
        translation_pairs = []
        for p in available_packages:
            if p.from_code and p.to_code:
                is_installed = any(
                    installed_p.from_code == p.from_code and installed_p.to_code == p.to_code
                    for installed_p in argostranslate.package.get_installed_packages()
                )
                status = " (Installed)" if is_installed else " (Not Installed)"
                translation_pairs.append((p.from_code, p.to_code, f"{p.from_name} -> {p.to_name}{status}"))
        return translation_pairs
    except Exception as e:
        print(f"Error getting Argos Translate packages: {e}")
        return []

def _install_language_package_threaded(from_code, to_code, dialog_window, callback):
    """
    Installs a language package in a separate thread.
    """
    if not _ARGOS_TRANSLATE_AVAILABLE:
        QtWidgets.QMessageBox.critical(dialog_window, "Installation Error", "Argos Translate module is not available.")
        return

    def run_install():
        try:
            QtCore.QMetaObject.invokeMethod(dialog_window, lambda: _show_temporary_status_message_func(f"⏳ Installing {from_code} to {to_code} language package... This may take a while."), QtCore.Qt.ConnectionType.QueuedConnection)
            argostranslate.package.install_from_path(
                argostranslate.package.get_package_path(from_code, to_code)
            )
            QtCore.QMetaObject.invokeMethod(dialog_window, lambda: _show_temporary_status_message_func(f"✅ Language package {from_code} to {to_code} installed."), QtCore.Qt.ConnectionType.QueuedConnection)
            QtCore.QMetaObject.invokeMethod(dialog_window, callback, QtCore.Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(dialog_window, lambda: QtWidgets.QMessageBox.critical(dialog_window, "Installation Error", f"Failed to install language package: {e}"), QtCore.Qt.ConnectionType.QueuedConnection)
            QtCore.QMetaObject.invokeMethod(dialog_window, lambda: _show_temporary_status_message_func(f"❌ Installation failed for {from_code} to {to_code}."), QtCore.Qt.ConnectionType.QueuedConnection)

    threading.Thread(target=run_install, daemon=True).start()

def _perform_translation_threaded(source_text, from_code, to_code, original_filepath, dialog_window):
    """
    Performs the actual translation in a separate thread and saves the result.
    """
    if not _ARGOS_TRANSLATE_AVAILABLE:
        QtWidgets.QMessageBox.critical(dialog_window, "Translation Error", "Argos Translate module is not available.")
        dialog_window.accept() # Close dialog
        return

    def run_translation():
        try:
            QtCore.QMetaObject.invokeMethod(dialog_window, lambda: _show_temporary_status_message_func(f"⏳ Translating from {from_code} to {to_code}..."), QtCore.Qt.ConnectionType.QueuedConnection)
            translated_text = argostranslate.translate.translate(source_text, from_code, to_code)

            if original_filepath:
                base_name, ext = os.path.splitext(os.path.basename(original_filepath))
                translated_filename = f"{to_code}_{base_name}{ext}"
                translated_filepath = os.path.join(os.path.dirname(original_filepath), translated_filename)
            else:
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                translated_filename = f"{to_code}_temp_document.tex"
                translated_filepath = os.path.join(output_dir, translated_filename)

            with open(translated_filepath, "w", encoding="utf-8") as f:
                f.write(translated_text)

            QtCore.QMetaObject.invokeMethod(dialog_window, lambda: _show_temporary_status_message_func(f"✅ Document translated and saved to {os.path.basename(translated_filepath)}"), QtCore.Qt.ConnectionType.QueuedConnection)
            QtCore.QMetaObject.invokeMethod(dialog_window, lambda: QtWidgets.QMessageBox.information(dialog_window, "Translation Success", f"Document translated and saved to:\n{translated_filepath}"), QtCore.Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(dialog_window, lambda: QtWidgets.QMessageBox.critical(dialog_window, "Translation Error", f"An error occurred during translation: {e}"), QtCore.Qt.ConnectionType.QueuedConnection)
            QtCore.QMetaObject.invokeMethod(dialog_window, lambda: _show_temporary_status_message_func(f"❌ Translation failed: {e}"), QtCore.Qt.ConnectionType.QueuedConnection)
        finally:
            QtCore.QMetaObject.invokeMethod(dialog_window, dialog_window.accept, QtCore.Qt.ConnectionType.QueuedConnection) # Close dialog after translation attempt

    threading.Thread(target=run_translation, daemon=True).start()

class TranslateDialog(QtWidgets.QDialog):
    def __init__(self, parent, editor_content, active_filepath, theme_getter, status_message_func):
        super().__init__(parent)
        self.setWindowTitle("Translate Document")
        self.setModal(True)
        self.setGeometry(100, 100, 450, 300)

        self.editor_content = editor_content
        self.active_filepath = active_filepath
        self.theme_getter = theme_getter
        self.status_message_func = status_message_func

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        main_layout.addWidget(QtWidgets.QLabel("Select Translation Pair:"))

        self.lang_combobox = QtWidgets.QComboBox()
        self.translation_pairs_data = _get_available_translation_pairs()
        display_options = [item[2] for item in self.translation_pairs_data]
        
        if not display_options:
            QtWidgets.QMessageBox.critical(self, "Argos Translate Error", "No translation packages found. Please download language packages using 'argos-translate --gui' or ensure internet connection.")
            self.close()
            return

        self.lang_combobox.addItems(display_options)
        main_layout.addWidget(self.lang_combobox)

        self.translate_button = QtWidgets.QPushButton("Translate")
        self.translate_button.clicked.connect(self._on_translate_button_click)
        main_layout.addWidget(self.translate_button)

    def _on_translate_button_click(self):
        selected_display_text = self.lang_combobox.currentText()
        if not selected_display_text:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Please select a translation pair.")
            return

        selected_pair = next((item for item in self.translation_pairs_data if item[2] == selected_display_text), None)
        if not selected_pair:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid selection.")
            return

        from_code, to_code, _ = selected_pair

        is_installed = any(
            p.from_code == from_code and p.to_code == to_code
            for p in argostranslate.package.get_installed_packages()
        )

        if not is_installed:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Install Language Package",
                f"The language package for {from_code} to {to_code} is not installed. Do you want to install it now? This may take some time.",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                _install_language_package_threaded(from_code, to_code, self,
                                                   lambda: _perform_translation_threaded(
                                                       self.editor_content, from_code, to_code,
                                                       self.active_filepath, self
                                                   ))
            else:
                self.close()
            return

        _perform_translation_threaded(self.editor_content, from_code, to_code, self.active_filepath, self)

def open_translate_dialog():
    """
    Opens a dialog for the user to select source and target languages for translation.
    """
    editor = _active_editor_getter_func()
    if not editor or not _root or not _theme_setting_getter_func or not _show_temporary_status_message_func:
        QtWidgets.QMessageBox.critical(_root, "Translator Error", "Translator service not fully initialized.")
        return

    if not _ARGOS_TRANSLATE_AVAILABLE:
        QtWidgets.QMessageBox.critical(_root, "Argos Translate Error", "The 'argostranslate' Python module is not installed. Please install it using 'pip install argostranslate' to enable translation features.")
        return
    
    source_text = editor.toPlainText()
    if not source_text.strip():
        QtWidgets.QMessageBox.warning(_root, "Translation", "The editor is empty. Nothing to translate.")
        return

    dialog = TranslateDialog(
        _root,
        source_text,
        _active_filepath_getter_func(),
        _theme_setting_getter_func,
        _show_temporary_status_message_func
    )
    dialog.exec()