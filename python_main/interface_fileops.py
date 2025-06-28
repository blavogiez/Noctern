from tkinter import filedialog
import os

def open_file(create_new_tab, show_temporary_status_message):
    filepath = filedialog.askopenfilename(
        title="Open File",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filepath:
        create_new_tab(file_path=filepath)
        show_temporary_status_message(f"✅ Opened: {os.path.basename(filepath)}")

def save_file(get_current_tab, show_temporary_status_message, save_file_as):
    current_tab = get_current_tab()
    if not current_tab:
        return False
    if current_tab.file_path:
        if current_tab.save_file():
            show_temporary_status_message(f"✅ Saved: {os.path.basename(current_tab.file_path)}")
            return True
        return False
    else:
        return save_file_as()

def save_file_as(get_current_tab, show_temporary_status_message, on_tab_changed):
    current_tab = get_current_tab()
    if not current_tab:
        return False
    new_filepath = filedialog.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        title="Save File As"
    )
    if new_filepath:
        if current_tab.save_file(new_path=new_filepath):
            show_temporary_status_message(f"✅ Saved as: {os.path.basename(new_filepath)}")
            on_tab_changed()
            return True
    return False
