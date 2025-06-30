# llm_service.py

# This file acts as a clean public-facing API (a "facade") for the LLM functionalities.
# It delegates calls to the appropriate specialized modules. This keeps the code organized
# and easy to maintain, following the Single Responsibility Principle.

import llm_init
import llm_completion
import llm_generation
import llm_keywords
import llm_prompts
import llm_history

# All functions called by shortcuts now accept an optional `event=None`
# parameter to conform to the new unified shortcut system.

def initialize_llm_service(root, progress_bar, theme_getter, editor_getter, filepath_getter):
    """Initializes the entire LLM service by calling the dedicated init module."""
    llm_init.initialize_llm_service(root, progress_bar, theme_getter, editor_getter, filepath_getter)

def load_prompts_for_current_file():
    """Delegates loading prompts to the prompts module."""
    llm_prompts.load_prompts_for_current_file()

def open_set_keywords_dialog(event=None):
    """Delegates opening the keywords dialog to the keywords module."""
    llm_keywords.open_set_keywords_dialog()

def open_edit_prompts_dialog(event=None):
    """Delegates opening the prompts dialog to the prompts module."""
    llm_prompts.open_edit_prompts_dialog()

def load_prompt_history_for_current_file():
    """Delegates loading history to the history module."""
    llm_history.load_prompt_history_for_current_file()

def request_llm_to_complete_text(event=None):
    """Delegates a text completion request to the completion module."""
    llm_completion.request_llm_to_complete_text()

# FIXED: The parameter order was changed here. `event` now comes first.
# This ensures that when the shortcut system calls this function with the event object,
# it's correctly assigned to the `event` parameter, and `initial_prompt_text`
# correctly defaults to `None`.
def open_generate_text_dialog(event=None, initial_prompt_text=None):
    """
    Delegates opening the generation dialog to the generation module.
    The parameter order is crucial for correct argument assignment from shortcuts.
    """
    # We pass the initial_prompt_text explicitly using a keyword argument for clarity
    # and to avoid any future ambiguity.
    llm_generation.open_generate_text_dialog(initial_prompt_text=initial_prompt_text)