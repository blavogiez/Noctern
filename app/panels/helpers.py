"""
Helper functions for integrated panel management.

These functions provide easy-to-use interfaces for showing different types
of panels in the left sidebar, replacing the original dialog functions.
"""

from app import state
from .proofreading import ProofreadingPanel
from .keywords import KeywordsPanel
from .generation import GenerationPanel
from .rephrase import RephrasePanel
from .translate import TranslatePanel
from .prompts import PromptsPanel
from .snippets import SnippetsPanel
from .metrics import MetricsPanel
from .table_insertion import TableInsertionPanel
from .image_details import ImageDetailsPanel
from .global_prompts import GlobalPromptsPanel
from .style_intensity import StyleIntensityPanel
from .settings import SettingsPanel


def show_style_intensity_panel(last_intensity=5, on_confirm_callback=None, on_cancel_callback=None):
    """
    Show the style intensity panel in the left sidebar.
    
    Args:
        last_intensity: Last used intensity value
        on_confirm_callback: Callback when confirmed (intensity)
        on_cancel_callback: Callback when cancelled
    """
    if not state.panel_manager:
        return
        
    panel = StyleIntensityPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        last_intensity=last_intensity,
        on_confirm_callback=on_confirm_callback,
        on_cancel_callback=on_cancel_callback
    )
    
    state.panel_manager.show_panel(panel)


def show_global_prompts_panel():
    """
    Show the global prompts editor panel in the left sidebar.
    """
    if not state.panel_manager:
        return
        
    panel = GlobalPromptsPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting
    )
    
    state.panel_manager.show_panel(panel)


def show_image_details_panel(suggested_label: str, on_ok_callback, on_cancel_callback=None):
    """
    Show the image details panel in the left sidebar.
    
    Args:
        suggested_label: Suggested label text
        on_ok_callback: Callback when OK is pressed (caption, label)
        on_cancel_callback: Optional callback when cancelled
    """
    if not state.panel_manager:
        return
        
    panel = ImageDetailsPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        suggested_label=suggested_label,
        on_ok_callback=on_ok_callback,
        on_cancel_callback=on_cancel_callback
    )
    
    state.panel_manager.show_panel(panel)


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


def show_rephrase_panel(original_text: str, on_rephrase_callback, on_cancel_callback=None):
    """
    Show the rephrase panel in the left sidebar.
    
    Args:
        original_text: Text to be rephrased
        on_rephrase_callback: Callback when rephrase is requested
        on_cancel_callback: Optional callback when cancelled
    """
    if not state.panel_manager:
        return
        
    panel = RephrasePanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        original_text=original_text,
        on_rephrase_callback=on_rephrase_callback,
        on_cancel_callback=on_cancel_callback
    )
    
    state.panel_manager.show_panel(panel)


def show_translate_panel(source_text: str, supported_translations, on_translate_callback, device="CPU"):
    """
    Show the translate panel in the left sidebar.
    
    Args:
        source_text: Text to be translated
        supported_translations: Dictionary of translation pairs
        on_translate_callback: Callback for translation requests
        device: Device to run translation on
    """
    if not state.panel_manager:
        return
        
    panel = TranslatePanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        source_text=source_text,
        supported_translations=supported_translations,
        on_translate_callback=on_translate_callback,
        device=device
    )
    
    state.panel_manager.show_panel(panel)


def show_prompts_panel(current_prompts, default_prompts, on_save_callback):
    """
    Show the prompts editor panel in the left sidebar.
    
    Args:
        current_prompts: Dictionary of current prompts
        default_prompts: Dictionary of default prompts
        on_save_callback: Callback when prompts are saved
    """
    if not state.panel_manager:
        return
        
    panel = PromptsPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        current_prompts=current_prompts,
        default_prompts=default_prompts,
        on_save_callback=on_save_callback
    )
    
    state.panel_manager.show_panel(panel)


def show_snippets_panel(current_snippets, save_callback):
    """
    Show the snippets editor panel in the left sidebar.
    
    Args:
        current_snippets: Dictionary of current snippets
        save_callback: Callback to save snippets
    """
    if not state.panel_manager:
        return
        
    panel = SnippetsPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        current_snippets=current_snippets,
        save_callback=save_callback
    )
    
    state.panel_manager.show_panel(panel)


def show_metrics_panel():
    """
    Show the metrics panel in the left sidebar.
    """
    if not state.panel_manager:
        return
    
    # Get current file path for productivity metrics
    current_file_path = None
    current_tab = state.get_current_tab()
    if current_tab and hasattr(current_tab, 'file_path'):
        current_file_path = current_tab.file_path
        
    panel = MetricsPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        file_path=current_file_path
    )
    
    state.panel_manager.show_panel(panel)


def show_table_insertion_panel(insert_callback):
    """
    Show the table insertion panel in the left sidebar.
    
    Args:
        insert_callback: Callback to insert the generated table
    """
    if not state.panel_manager:
        return
        
    panel = TableInsertionPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting,
        insert_callback=insert_callback
    )
    
    state.panel_manager.show_panel(panel)




def show_settings_panel():
    """
    Show the settings panel in the left sidebar.
    """
    if not state.panel_manager:
        return
        
    panel = SettingsPanel(
        parent_container=None,  # Will be set by panel manager
        theme_getter=state.get_theme_setting
    )
    
    state.panel_manager.show_panel(panel)