"""
Helper functions for integrated panel management.

These functions provide easy-to-use interfaces for showing different types
of panels in the left sidebar, replacing the original dialog functions.
"""

from app import state
from .proofreading import ProofreadingPanel
from .keywords import KeywordsPanel
from .generation import GenerationPanel


def show_proofreading_panel(editor, initial_text: str):
    """
    Show the proofreading panel in the left sidebar.
    
    Args:
        editor: The text editor widget
        initial_text: Text to be proofread
    """
    if not state.panel_manager:
        return
        
    panel = ProofreadingPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        editor=editor,
        initial_text=initial_text
    )
    
    state.panel_manager.show_panel(panel)


def show_keywords_panel(file_path: str):
    """
    Show the keywords panel in the left sidebar.
    
    Args:
        file_path: Path to the file being edited
    """
    if not state.panel_manager:
        return
        
    panel = KeywordsPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        file_path=file_path
    )
    
    state.panel_manager.show_panel(panel)


def show_generation_panel(prompt_history, on_generate_callback, 
                         on_history_add_callback, initial_prompt=None):
    """
    Show the text generation panel in the left sidebar.
    
    Args:
        prompt_history: List of (prompt, response) tuples
        on_generate_callback: Callback for generation requests
        on_history_add_callback: Callback for adding history entries
        initial_prompt: Optional initial prompt text
    """
    if not state.panel_manager:
        return
        
    panel = GenerationPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        prompt_history=prompt_history,
        on_generate_callback=on_generate_callback,
        on_history_add_callback=on_history_add_callback,
        initial_prompt=initial_prompt
    )
    
    state.panel_manager.show_panel(panel)