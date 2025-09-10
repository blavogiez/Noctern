"""
Integrated panel system for Noctern left sidebar.

This module provides a unified system for managing interactive panels
in the left sidebar, replacing separate dialog windows with integrated
UI components.
"""

from .manager import PanelManager
from .base_panel import BasePanel
from .helpers import (
    show_style_intensity_panel,
    show_global_prompts_panel,
    show_image_details_panel,
    show_proofreading_panel, 
    show_keywords_panel, 
    show_generation_panel,
    show_rephrase_panel,
    show_translate_panel,
    show_prompts_panel,
    show_snippets_panel,
    show_metrics_panel,
    show_table_insertion_panel,
    show_settings_panel
)

__all__ = [
    'PanelManager', 
    'BasePanel', 
    'show_style_intensity_panel',
    'show_global_prompts_panel',
    'show_image_details_panel',
    'show_proofreading_panel', 
    'show_keywords_panel', 
    'show_generation_panel',
    'show_rephrase_panel',
    'show_translate_panel',
    'show_prompts_panel',
    'show_snippets_panel',
    'show_metrics_panel',
    'show_table_insertion_panel',
    'show_settings_panel'
]