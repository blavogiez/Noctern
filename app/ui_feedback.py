"""Console and status feedback helpers."""

from __future__ import annotations

from tkinter import END

from app import state
from app import status_utils
from app import statusbar as interface_statusbar
from utils import animations

__all__ = [
    "show_console",
    "hide_console",
    "show_temporary_status_message",
    "clear_temporary_status_message",
]


def show_console(content: str) -> None:
    """Display the console pane with the provided text."""
    if not state.console_pane or not state.console_output:
        return

    if str(state.console_pane) not in state.vertical_pane.panes():
        state.vertical_pane.add(state.console_pane, height=150)

    state.console_output.config(state="normal")
    state.console_output.delete("1.0", END)
    state.console_output.insert("1.0", content)
    state.console_output.config(state="disabled")


def hide_console() -> None:
    """Hide the console pane when it is visible."""
    if not state.console_pane:
        return

    if str(state.console_pane) in state.vertical_pane.panes():
        state.vertical_pane.remove(state.console_pane)


def show_temporary_status_message(message: str, duration_ms: int = 2500) -> None:
    """Flash the status bar and display a temporary message."""
    state._temporary_status_active = True

    if state.status_label:
        original_color = state.get_theme_setting("statusbar_bg", "#f0f0f0")
        flash_color = state.get_theme_setting("success", "#77dd77")
        animations.flash_widget(state.status_label, flash_color, original_color)

    interface_statusbar.show_temporary_status_message(
        message,
        duration_ms,
        state.status_label,
        state.root,
        clear_temporary_status_message,
    )


def clear_temporary_status_message() -> None:
    """Restore the default status text after a temporary message."""
    state._temporary_status_active = False
    status_utils.update_status_bar_text()
    interface_statusbar.clear_temporary_status_message()
