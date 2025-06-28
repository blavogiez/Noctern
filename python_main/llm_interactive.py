import llm_state
import tkinter as tk

def clear_generated_text_state():
    active_editor = llm_state._active_editor_getter_func() if llm_state._active_editor_getter_func else None
    if active_editor and llm_state._generated_text_range:
        active_editor.tag_remove("llm_generated_text", llm_state._generated_text_range[0], llm_state._generated_text_range[1])
    llm_state._generated_text_range = None
    llm_state._is_generating = False

def accept_generated_text(event=None):
    if llm_state._is_generating:
        return "break"
    if llm_state._generated_text_range:
        clear_generated_text_state()
        return "break"
    return None

def discard_generated_text(event=None):
    if llm_state._is_generating:
        return "break"
    if llm_state._generated_text_range:
        active_editor = llm_state._active_editor_getter_func() if llm_state._active_editor_getter_func else None
        if active_editor:
            active_editor.delete(llm_state._generated_text_range[0], llm_state._generated_text_range[1])
        clear_generated_text_state()
        return "break"
    return None

def rephrase_generated_text(event=None):
    if llm_state._is_generating:
        return "break"
    if llm_state._generated_text_range:
        discard_generated_text()
        # Appeler la fonction de rephrase selon le type d'action précédente
        # (à compléter selon votre logique)
        return "break"
    return None
