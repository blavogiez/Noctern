from tkinter import messagebox
import os
import debug_console

def close_current_tab(get_current_tab, root, notebook, save_file, create_new_tab, tabs, closed_tabs_stack):
    current_tab = get_current_tab()
    if not current_tab:
        return
        
    tab_name = os.path.basename(current_tab.file_path) if current_tab.file_path else "Untitled"
    debug_console.log(f"Close tab requested for: '{tab_name}'", level='ACTION')

    if current_tab.is_dirty():
        debug_console.log(f"Tab '{tab_name}' is dirty. Prompting user to save.", level='INFO')
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            f"The file '{tab_name}' has unsaved changes. Do you want to save before closing it?",
            parent=root
        )
        if response is True:
            debug_console.log("User chose to SAVE before closing tab.", level='ACTION')
            if not save_file():
                debug_console.log("Save was cancelled. Aborting tab close.", level='INFO')
                return # Abort close if save fails/is cancelled
        elif response is None:
            debug_console.log("User CANCELLED the tab close operation.", level='ACTION')
            return
        else: # False
            debug_console.log("User chose NOT to save before closing tab.", level='ACTION')

    # Add to restore stack before forgetting the tab
    if closed_tabs_stack is not None:
        closed_tabs_stack.append(current_tab.file_path)
        if len(closed_tabs_stack) > 10: # Keep stack size reasonable
            closed_tabs_stack.pop(0)
        debug_console.log(f"Added '{current_tab.file_path}' to closed tab stack.", level='DEBUG')

    tab_id = notebook.select()
    notebook.forget(tab_id)
    del tabs[tab_id]
    debug_console.log(f"Tab '{tab_name}' closed and removed.", level='INFO')
    
    if not tabs:
        debug_console.log("No tabs remaining, creating a new 'Untitled' tab.", level='INFO')
        create_new_tab()

def create_new_tab(file_path, notebook, tabs, apply_theme, current_theme, on_tab_changed, EditorTab, schedule_heavy_updates):
    # Check if file is already open
    if file_path:
        for tab in tabs.values():
            if tab.file_path == file_path:
                debug_console.log(f"File '{file_path}' is already open. Switching to its tab.", level='INFO')
                notebook.select(tab)
                return
    
    tab_name = os.path.basename(file_path) if file_path else "Untitled"
    debug_console.log(f"Creating new tab for: '{tab_name}'", level='INFO')
    new_tab = EditorTab(notebook, file_path=file_path, schedule_heavy_updates_callback=schedule_heavy_updates)
    
    # CORRECTED: Add the tab to the notebook first, so it is "managed".
    notebook.add(new_tab, text=tab_name)
    
    # Now, load the content. The call to update_tab_title() inside load_file() will work correctly.
    new_tab.load_file() 
    
    notebook.select(new_tab)
    tabs[str(new_tab)] = new_tab
    apply_theme(current_theme) # Apply theme to the new tab's widgets
    on_tab_changed()
    debug_console.log(f"Tab for '{tab_name}' created and loaded successfully.", level='SUCCESS')