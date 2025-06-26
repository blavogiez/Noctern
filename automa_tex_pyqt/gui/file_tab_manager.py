import os
from PyQt6 import QtWidgets, QtCore, QtGui

# Import EditorTab class
from editor.editor_tab import EditorTab

# References to main GUI components and callbacks
_notebook = None
_welcome_screen = None
_root = None
_on_tab_changed_callback = None # Callback for when a tab changes (e.g., to load LLM history)
_schedule_heavy_updates_callback = None # Callback to schedule heavy updates
_apply_theme_callback = None # Callback to apply the current theme

# Dictionary to hold EditorTab instances, managed by this module
_tabs = {}

def initialize(notebook_ref, welcome_screen_ref, root_ref, on_tab_changed_cb, schedule_heavy_updates_cb, welcome_button_frame_ref, apply_theme_cb):
    """Initializes the file and tab manager with necessary GUI component references."""
    global _notebook, _welcome_screen, _root, _on_tab_changed_callback, _schedule_heavy_updates_callback, _apply_theme_callback
    _notebook = notebook_ref
    _welcome_screen = welcome_screen_ref
    _root = root_ref
    _on_tab_changed_callback = on_tab_changed_cb
    _schedule_heavy_updates_callback = schedule_heavy_updates_cb
    _apply_theme_callback = apply_theme_cb

    _notebook.currentChanged.connect(on_tab_changed) # Connect signal for tab changes
    _notebook.tabCloseRequested.connect(close_tab_by_index) # Connect signal for closing tabs

    # Add buttons to the welcome screen
    btn_new_file = QtWidgets.QPushButton("📄 New File (Ctrl+N)")
    btn_new_file.clicked.connect(lambda: create_new_tab(file_path=None))
    welcome_button_frame_ref.layout().addWidget(btn_new_file)

    btn_open_file = QtWidgets.QPushButton("📂 Open File (Ctrl+O)")
    btn_open_file.clicked.connect(lambda: open_file(_root.status_bar_label.setText)) # Pass status func
    welcome_button_frame_ref.layout().addWidget(btn_open_file)

    # Connect main window actions to file operations
    _root.action_new.triggered.connect(lambda: create_new_tab(file_path=None))
    _root.action_open.triggered.connect(lambda: open_file(_root.status_bar_label.setText))
    _root.action_save.triggered.connect(lambda: save_file(_root.status_bar_label.setText))
    _root.action_close_tab.triggered.connect(close_current_tab)

def get_current_tab():
    """Returns the currently active EditorTab object, or None."""
    if not _notebook:
        return None
    current_widget = _notebook.currentWidget()
    return current_widget if isinstance(current_widget, EditorTab) else None

def toggle_welcome_screen():
    """Shows or hides the welcome screen based on whether tabs are open."""
    if not _welcome_screen or not _notebook:
        return

    if _notebook.count() == 0: # No tabs are open
        _notebook.hide()
        _welcome_screen.show()
    else: # Tabs are open
        _welcome_screen.hide()
        _notebook.show()

def create_new_tab(file_path=None):
    """Creates a new EditorTab, adds it to the notebook, and selects it."""
    # Check if file is already open
    if file_path:
        for tab_widget in _tabs.values():
            if tab_widget.file_path == file_path:
                _notebook.setCurrentWidget(tab_widget)
                return

    is_first_tab = not _tabs

    new_tab = EditorTab(_notebook, file_path=file_path, schedule_heavy_updates_callback=_schedule_heavy_updates_callback)
    
    tab_title = os.path.basename(file_path) if file_path else "Untitled"
    _notebook.addTab(new_tab, tab_title)
    _notebook.setCurrentWidget(new_tab)
    
    _tabs[new_tab] = new_tab # Store reference to the widget itself
    
    if is_first_tab:
        toggle_welcome_screen()

    # Apply the current theme to ensure the new tab's widgets are styled correctly.
    if _apply_theme_callback:
        _apply_theme_callback()

    # Trigger updates for the new tab (e.g., LLM history, syntax highlighting)
    on_tab_changed()

    # Now that the tab is added to the notebook, load its content
    new_tab.load_file()

def open_file(show_temporary_status_message_func):
    """Opens a file and loads its content into the editor."""
    filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
        _root,
        "Open File",
        "",
        "LaTeX Files (*.tex);;Text Files (*.txt);;All Files (*.*)"
    )
    if filepath:
        create_new_tab(file_path=filepath)
        if show_temporary_status_message_func:
            show_temporary_status_message_func(f"✅ Opened: {os.path.basename(filepath)}")

def save_file(show_temporary_status_message_func, tab_to_save=None):
    """Saves the current editor content to the current file or a new file."""
    tab = tab_to_save or get_current_tab()
    if not tab:
        return False

    if tab.file_path:
        if tab.save_file():
            if show_temporary_status_message_func:
                show_temporary_status_message_func(f"✅ Saved: {os.path.basename(tab.file_path)}")
            return True
        return False
    else:
        return save_file_as(show_temporary_status_message_func, tab_to_save=tab)

def save_file_as(show_temporary_status_message_func, tab_to_save=None):
    """Saves the current tab to a new file path."""
    tab = tab_to_save or get_current_tab()
    if not tab:
        return False

    new_filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
        _root,
        "Save File As",
        tab.file_path if tab.file_path else "Untitled.tex",
        "LaTeX Files (*.tex);;Text Files (*.txt);;All Files (*.*)"
    )
    if new_filepath:
        if tab.save_file(new_path=new_filepath):
            if show_temporary_status_message_func:
                show_temporary_status_message_func(f"✅ Saved as: {os.path.basename(new_filepath)}")
            # Update services that depend on file path (e.g., LLM prompts/history)
            on_tab_changed()
            return True
    return False

def close_current_tab():
    """Closes the currently active tab."""
    current_tab = get_current_tab()
    if not current_tab:
        return
    
    # Find the index of the current tab
    index = _notebook.indexOf(current_tab)
    if index != -1:
        close_tab_by_index(index)

def close_tab_by_index(index):
    """Closes the tab at the given index."""
    tab_widget = _notebook.widget(index)
    if not tab_widget:
        return

    if tab_widget.is_dirty():
        response = QtWidgets.QMessageBox.question(
            _root,
            "Unsaved Changes",
            f"The file '{os.path.basename(tab_widget.file_path) if tab_widget.file_path else 'Untitled'}' has unsaved changes. Do you want to save before closing it?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        if response == QtWidgets.QMessageBox.StandardButton.Yes:
            if not save_file(lambda x: None, tab_to_save=tab_widget): # Pass a dummy status message func
                return # User cancelled save, so don't close tab
        elif response == QtWidgets.QMessageBox.StandardButton.Cancel:
            return

    _notebook.removeTab(index)
    if tab_widget in _tabs:
        del _tabs[tab_widget]
    tab_widget.deleteLater() # Ensure widget is properly deleted

    toggle_welcome_screen()

def on_tab_changed(index=None):
    """Handles logic when the active tab changes."""
    # This callback triggers updates in other modules (LLM service, editor view)
    if _on_tab_changed_callback:
        _on_tab_changed_callback()

# Override MainWindow's closeEvent to check for unsaved changes across all tabs
def setup_main_window_close_event(main_window_ref, save_file_func, show_status_message_func):
    """Sets up the main window's close event handler."""
    original_close_event = main_window_ref.closeEvent

    def custom_close_event(event):
        dirty_tabs = [tab for tab in _tabs.values() if tab.is_dirty()]

        if dirty_tabs:
            file_list = "\n - ".join([os.path.basename(tab.file_path) if tab.file_path else "Untitled" for tab in dirty_tabs])
            response = QtWidgets.QMessageBox.question(
                main_window_ref,
                "Unsaved Changes",
                f"You have unsaved changes in the following files:\n - {file_list}\n\nDo you want to save them before closing?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel
            )
            if response == QtWidgets.QMessageBox.StandardButton.Yes:
                all_saved = True
                for tab in dirty_tabs:
                    if not save_file_func(show_status_message_func, tab_to_save=tab):
                        all_saved = False
                        break # User cancelled a "Save As" dialog
                if all_saved:
                    event.accept() # Close if all saves were successful
                else:
                    event.ignore() # Don't close if any save was cancelled
            elif response == QtWidgets.QMessageBox.StandardButton.No:
                event.accept() # Just close
            else: # Cancel
                event.ignore()
        else:
            event.accept() # No unsaved changes, just close.

    main_window_ref.closeEvent = custom_close_event