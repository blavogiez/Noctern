"""
Integrated panel system for AutomaTeX left sidebar.

This module provides a unified system for managing interactive panels
in the left sidebar, replacing separate dialog windows with integrated
UI components.
"""

from .manager import PanelManager
from .base_panel import BasePanel
from .helpers import show_proofreading_panel, show_keywords_panel, show_generation_panel

__all__ = ['PanelManager', 'BasePanel', 'show_proofreading_panel', 'show_keywords_panel', 'show_generation_panel']