# File: theme_manager.py
from PyQt6 import QtWidgets, QtCore, QtGui

# References to main GUI components and callbacks
_root = None
_perform_heavy_updates_callback = None # Callback to trigger syntax highlighting, outline updates etc.
_theme_settings = {} # Store current theme colors and properties
_current_theme = "dark" # Initial theme state (changed to dark by default for modern feel)

def initialize(root_ref, perform_heavy_updates_cb):
    """Initializes the theme manager with necessary references."""
    global _root, _perform_heavy_updates_callback
    _root = root_ref
    _perform_heavy_updates_callback = perform_heavy_updates_cb

    # Connect theme button
    _root.btn_theme.clicked.connect(lambda: apply_theme("dark" if _current_theme == "light" else "light"))

def get_theme_setting(key, default=None):
    """Gets a value from the current theme settings."""
    return _theme_settings.get(key, default)

def apply_theme(theme_name):
    """Applies the specified theme (light or dark) to the GUI."""
    global _current_theme, _theme_settings

    if not _root:
        return

    _current_theme = theme_name

    # Define colors based on theme
    if theme_name == "light":
        _theme_settings = {
            "root_bg": "#fdfdfd",
            "fg_color": "#000000",
            "sel_bg": "#0078d4", "sel_fg": "#ffffff",
            "editor_bg": "#ffffff", "editor_fg": "#1e1e1e", "editor_insert_bg": "#333333",
            "comment_color": "#008000", "command_color": "#0000ff", "brace_color": "#ff007f",
            "ln_text_color": "#888888", "ln_bg_color": "#f7f7f7", "ln_current_text_color": "#000000",
            "current_line_bg": "#f8f8f8",
            "panedwindow_sash": "#e6e6e6",
        }
        stylesheet = """
            QMainWindow { background-color: #fdfdfd; }
            QFrame { background-color: #fdfdfd; }
            QPushButton { background-color: #e0e0e0; color: #333333; border: 1px solid #cccccc; padding: 5px; }
            QPushButton:hover { background-color: #d0d0d0; }
            QTabWidget::pane { border: 1px solid #c2c2c2; background-color: #ffffff; }
            QTabBar::tab { background: #e0e0e0; border: 1px solid #c2c2c2; border-bottom-color: #c2c2c2; border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 5px 10px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; }
            QTextEdit { background-color: #ffffff; color: #1e1e1e; selection-background-color: #0078d4; selection-color: #ffffff; }
            QProgressBar { text-align: center; background-color: #e0e0e0; border: 1px solid #cccccc; border-radius: 5px; }
            QProgressBar::chunk { background-color: #0078d4; border-radius: 5px; }
            QStatusBar { background-color: #e0e0e0; color: #333333; }
            QSplitter::handle { background-color: #e6e6e6; }
            QTreeWidget { background-color: #fdfdfd; color: #000000; alternate-background-color: #f0f0f0; }
            QListWidget { background-color: #ffffff; color: #1e1e1e; selection-background-color: #0078d4; selection-color: #ffffff; }
            QComboBox { background-color: #ffffff; color: #1e1e1e; }
            QDialog { background-color: #fdfdfd; }
            QLabel { color: #000000; }
        """
    elif theme_name == "dark":
        _theme_settings = {
            "root_bg": "#202020",
            "fg_color": "#ffffff",
            "sel_bg": "#0078d4", "sel_fg": "#ffffff",
            "editor_bg": "#1e1e1e", "editor_fg": "#d4d4d4", "editor_insert_bg": "#d4d4d4",
            "comment_color": "#608b4e", "command_color": "#569cd6", "brace_color": "#c586c0",
            "ln_text_color": "#6a6a6a", "ln_bg_color": "#252526", "ln_current_text_color": "#ffffff",
            "current_line_bg": "#222222",
            "panedwindow_sash": "#333333",
        }
        stylesheet = """
            QMainWindow { background-color: #202020; }
            QFrame { background-color: #202020; }
            QPushButton { background-color: #333333; color: #ffffff; border: 1px solid #555555; padding: 5px; }
            QPushButton:hover { background-color: #444444; }
            QTabWidget::pane { border: 1px solid #444444; background-color: #1e1e1e; }
            QTabBar::tab { background: #333333; border: 1px solid #444444; border-bottom-color: #444444; border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 5px 10px; }
            QTabBar::tab:selected { background: #1e1e1e; border-bottom-color: #1e1e1e; }
            QTextEdit { background-color: #1e1e1e; color: #d4d4d4; selection-background-color: #0078d4; selection-color: #ffffff; }
            QProgressBar { text-align: center; background-color: #333333; border: 1px solid #555555; border-radius: 5px; }
            QProgressBar::chunk { background-color: #0078d4; border-radius: 5px; }
            QStatusBar { background-color: #333333; color: #ffffff; }
            QSplitter::handle { background-color: #333333; }
            QTreeWidget { background-color: #202020; color: #ffffff; alternate-background-color: #252526; }
            QListWidget { background-color: #1e1e1e; color: #d4d4d4; selection-background-color: #0078d4; selection-color: #ffffff; }
            QComboBox { background-color: #1e1e1e; color: #d4d4d4; }
            QDialog { background-color: #202020; }
            QLabel { color: #ffffff; }
        """
    else:
        return

    QtWidgets.QApplication.instance().setStyleSheet(stylesheet)

    # Apply colors to all open editor tabs (QTextEdit widgets) and line numbers
    for i in range(_root.notebook.count()):
        tab_widget = _root.notebook.widget(i)
        if hasattr(tab_widget, 'editor') and tab_widget.editor:
            tab_widget.line_numbers.update_theme(
                text_color=_theme_settings["ln_text_color"], bg_color=_theme_settings["ln_bg_color"],
                current_line_text_color=_theme_settings["ln_current_text_color"]
            )

    # Trigger a heavy update to redraw syntax highlighting, outline, and line numbers
    _perform_heavy_updates_callback()
