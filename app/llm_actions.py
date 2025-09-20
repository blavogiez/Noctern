"""UI helpers dedicated to LLM-driven interactions."""

from app import panels
from utils import logs_console
from llm import autostyle as llm_autostyle
from llm import generation as llm_generation
from llm import keywords as llm_keywords
from llm import latex_debug as llm_latex_debug
from llm import proofreading as llm_proofreading
from llm import prompts as llm_prompts
from llm import rephrase as llm_rephrase


__all__ = [
    "open_generate_text_panel",
    "open_proofreading_panel",
    "open_rephrase_panel",
    "open_set_keywords_panel",
    "open_edit_prompts_panel",
    "open_global_prompts_editor",
    "style_selected_text",
    "analyze_compilation_diff",
]


def open_generate_text_panel(event=None, initial_prompt_text=None):
    """Open text generation panel configured for the LLM service."""

    def panel_callback(prompt_history, on_generate_callback, on_history_add_callback, initial_prompt):
        panels.show_generation_panel(prompt_history, on_generate_callback, on_history_add_callback, initial_prompt)

    llm_generation.prepare_text_generation(initial_prompt_text, panel_callback)


def open_proofreading_panel(event=None):
    """Open proofreading panel with current editor context."""

    def panel_callback(editor, text_to_check):
        panels.show_proofreading_panel(editor, text_to_check)

    llm_proofreading.prepare_proofreading(panel_callback)


def open_rephrase_panel(event=None):
    """Open rephrase panel for AI assisted paraphrasing."""

    def panel_callback(original_text, on_rephrase_callback, on_cancel_callback):
        panels.show_rephrase_panel(original_text, on_rephrase_callback, on_cancel_callback)

    llm_rephrase.prepare_rephrase(panel_callback=panel_callback)


def open_set_keywords_panel(event=None):
    """Open keyword suggestion panel bound to the active file."""

    def panel_callback(active_file_path):
        panels.show_keywords_panel(active_file_path)

    llm_keywords.prepare_keywords_panel(panel_callback)


def open_edit_prompts_panel(event=None):
    """Open prompts editing panel and keep persistence hooks."""

    def panel_callback(theme_getter, active_file_path, prompts, default_prompts, load_callback, save_callback):
        panels.show_prompts_panel(theme_getter, active_file_path, prompts, default_prompts, load_callback, save_callback)

    llm_prompts.prepare_edit_prompts_panel(panel_callback)


def open_global_prompts_editor(event=None):
    """Open global prompts editor without needing UI context."""

    def panel_callback():
        panels.show_global_prompts_panel()

    llm_prompts.prepare_global_prompts_editor(panel_callback)


def style_selected_text(event=None):
    """Apply automatic styling to the current selection."""
    logs_console.log("Initiating Smart Styling action.", level="ACTION")

    def panel_callback(last_intensity, on_confirm_callback, on_cancel_callback):
        panels.show_style_intensity_panel(last_intensity, on_confirm_callback, on_cancel_callback)

    llm_autostyle.prepare_autostyle(panel_callback)


def analyze_compilation_diff(event=None):
    """Analyze LaTeX compilation results with the debug coordinator."""

    def debug_callback(diff_content, log_content, file_path, current_content):
        from app import state

        if state.debug_coordinator:
            state.debug_coordinator.handle_compilation_result(
                success=False,
                log_content=log_content,
                file_path=file_path,
                current_content=current_content,
            )

    llm_latex_debug.prepare_compilation_analysis(debug_callback)
