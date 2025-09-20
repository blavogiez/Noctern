import pytest

from app import llm_actions
from app import state


class Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return kwargs.get("return_value")


@pytest.fixture(autouse=True)
def reset_debug_coordinator():
    original = getattr(state, "debug_coordinator", None)
    yield
    state.debug_coordinator = original


@pytest.fixture
def panels_recorder(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(llm_actions.panels, "show_generation_panel", recorder)
    monkeypatch.setattr(llm_actions.panels, "show_proofreading_panel", recorder)
    monkeypatch.setattr(llm_actions.panels, "show_rephrase_panel", recorder)
    monkeypatch.setattr(llm_actions.panels, "show_keywords_panel", recorder)
    monkeypatch.setattr(llm_actions.panels, "show_prompts_panel", recorder)
    monkeypatch.setattr(llm_actions.panels, "show_global_prompts_panel", Recorder())
    monkeypatch.setattr(llm_actions.panels, "show_style_intensity_panel", recorder)
    return recorder


def test_open_generate_text_panel_triggers_llm(monkeypatch, panels_recorder):
    captured = {}

    def fake_prepare(initial_prompt, callback):
        captured["prompt"] = initial_prompt
        callback("hist", "on_generate", "on_add", "seed")

    monkeypatch.setattr(llm_actions.llm_generation, "prepare_text_generation", fake_prepare)

    llm_actions.open_generate_text_panel(initial_prompt_text="draft")

    assert captured["prompt"] == "draft"
    args, _ = panels_recorder.calls[0]
    assert args[0] == "hist"


def test_open_proofreading_panel(monkeypatch, panels_recorder):
    def fake_prepare(callback):
        callback("editor", "text")

    monkeypatch.setattr(llm_actions.llm_proofreading, "prepare_proofreading", fake_prepare)

    llm_actions.open_proofreading_panel()

    args, _ = panels_recorder.calls[0]
    assert args == ("editor", "text")


def test_open_rephrase_panel(monkeypatch, panels_recorder):
    def fake_prepare(**kwargs):
        kwargs["panel_callback"]("body", "confirm", "cancel")

    monkeypatch.setattr(llm_actions.llm_rephrase, "prepare_rephrase", fake_prepare)

    llm_actions.open_rephrase_panel()

    args, _ = panels_recorder.calls[0]
    assert args == ("body", "confirm", "cancel")


def test_open_keywords_panel(monkeypatch, panels_recorder):
    def fake_prepare(callback):
        callback("/tmp/file.tex")

    monkeypatch.setattr(llm_actions.llm_keywords, "prepare_keywords_panel", fake_prepare)

    llm_actions.open_set_keywords_panel()

    args, _ = panels_recorder.calls[0]
    assert args == ("/tmp/file.tex",)


def test_open_edit_prompts_panel(monkeypatch, panels_recorder):
    def fake_prepare(callback):
        callback("theme", "file.tex", {"a": 1}, {}, "load", "save")

    monkeypatch.setattr(llm_actions.llm_prompts, "prepare_edit_prompts_panel", fake_prepare)

    llm_actions.open_edit_prompts_panel()

    args, _ = panels_recorder.calls[0]
    assert args[0] == "theme"
    assert args[1] == "file.tex"


def test_open_global_prompts_editor(monkeypatch):
    triggered = {}

    def fake_prepare(callback):
        callback()

    def fake_show():
        triggered["shown"] = True

    monkeypatch.setattr(llm_actions.llm_prompts, "prepare_global_prompts_editor", fake_prepare)
    monkeypatch.setattr(llm_actions.panels, "show_global_prompts_panel", fake_show)

    llm_actions.open_global_prompts_editor()

    assert triggered.get("shown") is True


def test_style_selected_text(monkeypatch, panels_recorder):
    monkeypatch.setattr(llm_actions.logs_console, "log", lambda message, level="INFO": None)

    def fake_prepare(callback):
        callback("low", "confirm", "cancel")

    monkeypatch.setattr(llm_actions.llm_autostyle, "prepare_autostyle", fake_prepare)

    llm_actions.style_selected_text()

    args, _ = panels_recorder.calls[0]
    assert args == ("low", "confirm", "cancel")


def test_analyze_compilation_diff(monkeypatch):
    class DebugRecorder:
        def __init__(self):
            self.calls = []

        def handle_compilation_result(self, **payload):
            self.calls.append(payload)
    recorder = DebugRecorder()
    state.debug_coordinator = recorder

    def fake_prepare(callback):
        callback("diff", "log", "file.tex", "content")

    monkeypatch.setattr(llm_actions.llm_latex_debug, "prepare_compilation_analysis", fake_prepare)

    llm_actions.analyze_compilation_diff()

    payload = recorder.calls[0]
    assert payload["success"] is False
    assert payload["file_path"] == "file.tex"
    assert payload["log_content"] == "log"
    assert payload["current_content"] == "content"
