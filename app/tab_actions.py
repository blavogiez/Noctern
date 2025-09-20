"""High-level helpers for notebook tabs and related file actions."""

from __future__ import annotations

import os
from typing import Callable, Optional

from app import state
from app import file_operations as interface_fileops
from app import tab_operations as interface_tabops
from editor import image_manager as editor_image_manager
from llm import service as llm_service
from utils import logs_console

StatusCallback = Callable[[str, Optional[int]], None]


def close_current_tab(save_current_file: Callable[[], bool], create_tab: Callable[..., None]):
    """Close the active tab, delegating prompts to tab_operations."""
    return interface_tabops.close_current_tab(
        state.get_current_tab,
        state.root,
        state.notebook,
        save_current_file,
        create_tab,
        state.tabs,
        state._closed_tabs_stack,
    )


def create_new_tab(
    file_path: Optional[str],
    apply_theme: Callable[[], None],
    on_tab_changed: Callable[..., None],
    schedule_heavy_updates: Callable[..., None],
    editor_factory,
):
    """Create a tab through tab_operations and register it in state."""
    interface_tabops.create_new_tab(
        file_path,
        state.notebook,
        state.tabs,
        apply_theme,
        on_tab_changed,
        editor_factory,
        schedule_heavy_updates,
    )


def restore_last_closed_tab(create_tab: Callable[..., None], status_callback: StatusCallback):
    """Reopen the most recently closed tab if one exists."""
    if state._closed_tabs_stack:
        file_path = state._closed_tabs_stack.pop()
        display_path = file_path or "Untitled"
        logs_console.log(f"Attempting to restore closed tab: {display_path}", level="ACTION")
        create_tab(file_path=file_path)
        return

    logs_console.log("No recently closed tabs available for restoration.", level="INFO")
    status_callback("\u2139\ufe0f No recently closed tabs to restore.")


def open_file(create_tab: Callable[..., None], status_callback: StatusCallback):
    """Open a file via dialog and load it in a new tab."""
    return interface_fileops.open_file(create_tab, status_callback)


def save_file(status_callback: StatusCallback, save_as: Callable[..., None]):
    """Save the current tab, syncing related assets first."""
    current_tab = state.get_current_tab()
    if current_tab:
        editor_image_manager.check_for_deleted_images(current_tab)
    return interface_fileops.save_file(state.get_current_tab, status_callback, save_as)


def save_file_as(status_callback: StatusCallback, on_tab_changed: Callable[..., None]):
    """Save the current tab to a new path."""
    current_tab = state.get_current_tab()
    if current_tab:
        editor_image_manager.check_for_deleted_images(current_tab)
    return interface_fileops.save_file_as(state.get_current_tab, status_callback, on_tab_changed)


def on_tab_changed(perform_heavy_updates: Callable[[], None]):
    """Update session state when the user switches tabs."""
    current_tab = state.get_current_tab()
    if current_tab is None:
        if hasattr(state, "metrics_display") and state.metrics_display:
            state.metrics_display.set_current_file(None)
        return

    tab_name = os.path.basename(current_tab.file_path) if current_tab.file_path else "Untitled"
    logs_console.log(f"Active tab changed to: '{tab_name}'.", level="ACTION")

    if hasattr(state, "metrics_display") and state.metrics_display:
        state.metrics_display.save_current_session()
        state.metrics_display.set_current_file(current_tab.file_path)

    llm_service.load_prompt_history_for_current_file()
    llm_service.load_prompts_for_current_file()
    perform_heavy_updates()
