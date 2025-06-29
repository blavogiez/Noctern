import os
import json
import tkinter as tk
from tkinter import messagebox
import threading
import datetime

import interface
import llm_prompt_history
import llm_utils
import llm_api_client
import llm_dialogs
import llm_prompt_manager
import llm_state
import llm_init
import llm_completion
import llm_generation
import llm_keywords
import llm_prompts
import llm_interactive
import llm_history

# --- Shared service state ---
_root_window = None
_llm_progress_bar_widget = None
_theme_setting_getter_func = None
_active_editor_getter_func = None
_active_filepath_getter_func = None

_default_prompts = {
    "completion": "Complete this: {current_phrase_start}",
    "generation": "Generate text for this prompt: {user_prompt}"
}


def _check_service_ready(require_editor=True):
    editor = _active_editor_getter_func() if require_editor else None
    if not _root_window or not _llm_progress_bar_widget or (require_editor and not editor):
        messagebox.showerror("LLM Service Error", "LLM Service not fully initialized.")
        return False
    return True


def _load_default_prompts():
    global _default_prompts
    path = os.path.join(os.path.dirname(__file__), "default_prompts.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _default_prompts = json.load(f)
    except Exception:
        pass


_load_default_prompts()


# --- Initialization ---
def initialize_llm_service(root, progress_bar, theme_getter, editor_getter, filepath_getter):
    global _root_window, _llm_progress_bar_widget, _theme_setting_getter_func, _active_editor_getter_func, _active_filepath_getter_func
    _root_window = root
    _llm_progress_bar_widget = progress_bar
    _theme_setting_getter_func = theme_getter
    _active_editor_getter_func = editor_getter
    _active_filepath_getter_func = filepath_getter

    llm_init.initialize_llm_service(root, progress_bar, theme_getter, editor_getter, filepath_getter)

# --- Prompts management ---
def load_prompts_for_current_file():
    filepath = _active_filepath_getter_func() if callable(_active_filepath_getter_func) else None
    prompts = llm_prompt_manager.load_prompts_from_file(filepath, _default_prompts)
    llm_state.completion_prompt_template = prompts["completion"]
    llm_state.generation_prompt_template = prompts["generation"]


def update_prompts(completion_template, generation_template):
    llm_state.completion_prompt_template = completion_template
    llm_state.generation_prompt_template = generation_template
    filepath = _active_filepath_getter_func() if callable(_active_filepath_getter_func) else None

    if filepath:
        llm_prompt_manager.save_prompts_to_file({
            "completion": completion_template,
            "generation": generation_template
        }, filepath)
        prompts_filename = os.path.basename(llm_prompt_manager.get_prompts_filepath(filepath))
        interface.show_temporary_status_message(f"✅ Prompts saved: {prompts_filename}")
    else:
        interface.show_temporary_status_message("⚠️ Prompts updated for this session only (no file open).")


def get_current_prompts():
    return {
        "completion": llm_state.completion_prompt_template,
        "generation": llm_state.generation_prompt_template
    }


# --- Keyword Dialog ---
def open_set_keywords_dialog():
    if not _check_service_ready(False):
        return

    def _on_save(new_keywords):
        llm_state.llm_keywords_list = new_keywords
        if not new_keywords:
            messagebox.showinfo("Keywords Cleared", "LLM keywords list has been cleared.", parent=_root_window)
        else:
            messagebox.showinfo("Keywords Saved", f"LLM keywords registered:\n- {', '.join(new_keywords)}", parent=_root_window)

    llm_dialogs.show_set_llm_keywords_dialog(
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_llm_keywords_list=llm_state.llm_keywords_list,
        on_save_keywords_callback=_on_save
    )


# --- Prompt Editor ---
def open_edit_prompts_dialog():
    if not _check_service_ready(False):
        return

    llm_dialogs.show_edit_prompts_dialog(
        root_window=_root_window,
        theme_setting_getter_func=_theme_setting_getter_func,
        current_prompts=get_current_prompts(),
        default_prompts=_default_prompts,
        on_save_callback=update_prompts
    )


# --- History ---
def load_prompt_history_for_current_file():
    llm_history.load_prompt_history_for_current_file()


# --- Completion ---
def request_llm_to_complete_text():
    llm_completion.request_llm_to_complete_text()


# --- Generation ---
def open_generate_text_dialog(initial_prompt_text=None):
    llm_generation.open_generate_text_dialog(initial_prompt_text)
