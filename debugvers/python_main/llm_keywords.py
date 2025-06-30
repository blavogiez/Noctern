import llm_state
import llm_dialogs
from tkinter import messagebox
import debug_console

def open_set_keywords_dialog():
    """Opens the dialog to set global LLM keywords."""
    debug_console.log("Set LLM Keywords dialog opened.", level='ACTION')
    if not llm_state._root_window or not llm_state._theme_setting_getter_func:
        messagebox.showerror("LLM Service Error", "UI components not fully initialized for keywords dialog.")
        return

    def _handle_keywords_save_from_dialog(new_keywords_list):
        debug_console.log(f"Saving LLM keywords: {new_keywords_list}", level='CONFIG')
        llm_state._llm_keywords_list = new_keywords_list
        if not llm_state._llm_keywords_list:
            messagebox.showinfo("Keywords Cleared", "LLM keywords list has been cleared.", parent=llm_state._root_window)
        else:
            messagebox.showinfo("Keywords Saved", f"LLM keywords registered:\n- {', '.join(llm_state._llm_keywords_list)}", parent=llm_state._root_window)

    llm_dialogs.show_set_llm_keywords_dialog(
        root_window=llm_state._root_window,
        theme_setting_getter_func=llm_state._theme_setting_getter_func,
        current_llm_keywords_list=llm_state._llm_keywords_list,
        on_save_keywords_callback=_handle_keywords_save_from_dialog
    )