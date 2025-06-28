from tkinter import messagebox
import os

def close_current_tab(get_current_tab, root, notebook, save_file, create_new_tab, tabs):
    current_tab = get_current_tab()
    if not current_tab:
        return
    if current_tab.is_dirty():
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            f"The file '{os.path.basename(current_tab.file_path) if current_tab.file_path else 'Untitled'}' has unsaved changes. Do you want to save before closing it?",
            parent=root
        )
        if response is True:
            if not save_file():
                return
        elif response is None:
            return
    tab_id = notebook.select()
    notebook.forget(tab_id)
    del tabs[tab_id]
    if not tabs:
        create_new_tab()

def create_new_tab(file_path, notebook, tabs, apply_theme, current_theme, on_tab_changed, EditorTab, schedule_heavy_updates):
    # Check if file is already open
    if file_path:
        for tab in tabs.values():
            if tab.file_path == file_path:
                notebook.select(tab)
                return
    new_tab = EditorTab(notebook, file_path=file_path, schedule_heavy_updates_callback=schedule_heavy_updates)
    notebook.add(new_tab, text=os.path.basename(file_path) if file_path else "Untitled")
    notebook.select(new_tab)
    tabs[str(new_tab)] = new_tab
    apply_theme(current_theme)
    on_tab_changed()
    new_tab.load_file()
