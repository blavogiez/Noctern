from tkinter import filedialog
import os
import debug_console

def open_file(create_new_tab, show_temporary_status_message):
    debug_console.log("Open file dialog initiated.", level='ACTION')
    filepath = filedialog.askopenfilename(
        title="Open File",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filepath:
        debug_console.log(f"File selected for opening: {filepath}", level='INFO')
        create_new_tab(file_path=filepath)
        show_temporary_status_message(f"✅ Opened: {os.path.basename(filepath)}")
    else:
        debug_console.log("Open file dialog cancelled.", level='INFO')

def save_file(get_current_tab, show_temporary_status_message, save_file_as):
    current_tab = get_current_tab()
    if not current_tab:
        debug_console.log("Save failed: No active tab.", level='WARNING')
        return False
    
    tab_name = current_tab.file_path or "Untitled"
    debug_console.log(f"Save initiated for tab: {tab_name}", level='ACTION')

    if current_tab.file_path:
        if current_tab.save_file():
            debug_console.log(f"File saved successfully: {current_tab.file_path}", level='SUCCESS')
            show_temporary_status_message(f"✅ Saved: {os.path.basename(current_tab.file_path)}")
            return True
        debug_console.log(f"File save failed for: {current_tab.file_path}", level='ERROR')
        return False
    else:
        debug_console.log("No file path, redirecting to 'Save As'.", level='INFO')
        return save_file_as()

def save_file_as(get_current_tab, show_temporary_status_message, on_tab_changed):
    current_tab = get_current_tab()
    if not current_tab:
        debug_console.log("Save As failed: No active tab.", level='WARNING')
        return False
        
    debug_console.log("Save As dialog initiated.", level='ACTION')
    new_filepath = filedialog.asksaveasfilename(
        defaultextension=".tex",
        filetypes=[("LaTeX Files", "*.tex"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        title="Save File As"
    )
    if new_filepath:
        debug_console.log(f"File path selected for Save As: {new_filepath}", level='INFO')
        if current_tab.save_file(new_path=new_filepath):
            debug_console.log(f"File saved successfully to new path: {new_filepath}", level='SUCCESS')
            show_temporary_status_message(f"✅ Saved as: {os.path.basename(new_filepath)}")
            on_tab_changed()
            return True
        debug_console.log(f"Save As operation failed for: {new_filepath}", level='ERROR')
    else:
        debug_console.log("Save As dialog cancelled.", level='INFO')
    return False