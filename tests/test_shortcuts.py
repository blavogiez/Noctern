from types import SimpleNamespace

import pytest

from app import shortcuts, state


class DummyRoot:
    def __init__(self):
        self.bindings = {}
        self._focus = None

    def bind_all(self, key, func):
        self.bindings[key] = func

    def focus_get(self):
        return self._focus


@pytest.fixture(autouse=True)
def patch_text_widget(monkeypatch):
    monkeypatch.setattr(shortcuts.tk, "Text", type("Text", (), {}))


@pytest.fixture
def setup_shortcuts(monkeypatch):
    call_order = []

    def recorder(name):
        def _inner(*args, **kwargs):
            call_order.append(name)
        return _inner

    functions_to_patch = [
        "create_new_tab",
        "open_file",
        "save_file",
        "close_current_tab",
        "restore_last_closed_tab",
        "open_generate_text_panel",
        "open_set_keywords_panel",
        "open_proofreading_panel",
        "open_edit_prompts_panel",
        "style_selected_text",
        "open_rephrase_panel",
        "paste_image",
        "insert_table",
        "zoom_in",
        "zoom_out",
    ]
    for name in functions_to_patch:
        monkeypatch.setattr(shortcuts.interface, name, recorder(f"interface.{name}"))

    monkeypatch.setattr(shortcuts.llm_service, "request_llm_to_complete_text", recorder("llm.complete"))
    monkeypatch.setattr(shortcuts.latex_translator, "open_translate_panel", recorder("latex.translate"))

    search_bar = SimpleNamespace(is_visible=False)
    monkeypatch.setattr(shortcuts.editor_search, "_search_bar", search_bar, raising=False)
    monkeypatch.setattr(shortcuts.editor_search, "initialize_search_bar", recorder("search.init"))
    monkeypatch.setattr(shortcuts.editor_search, "show_search_bar", lambda: setattr(search_bar, "is_visible", True))
    monkeypatch.setattr(shortcuts.editor_search, "hide_search_bar", lambda: setattr(search_bar, "is_visible", False))

    monkeypatch.setattr(shortcuts.editor_snippets, "handle_snippet_expansion", recorder("snippets.expand"))
    monkeypatch.setattr(shortcuts.logs_console, "log", lambda *args, **kwargs: None)

    panel_calls = []
    panel_stub = SimpleNamespace(
        switch_to_next_panel=lambda: panel_calls.append("next"),
        switch_to_previous_panel=lambda: panel_calls.append("previous"),
        close_current_panel=lambda: panel_calls.append("close_current"),
        close_all_panels=lambda: panel_calls.append("close_all"),
    )
    monkeypatch.setattr(state, "panel_manager", panel_stub)

    return call_order, panel_calls, search_bar


def test_bind_global_shortcuts_triggers_callbacks(setup_shortcuts):
    call_order, panel_calls, search_bar = setup_shortcuts
    root = DummyRoot()

    shortcuts.bind_global_shortcuts(root)

    assert "<Control-n>" in root.bindings
    result = root.bindings["<Control-n>"]()
    assert result == "break"
    assert call_order[0] == "search.init"
    assert call_order[1] == "interface.create_new_tab"

    root.bindings["<Control-f>"]()
    assert search_bar.is_visible is True

    search_bar.is_visible = True
    root.bindings["<Escape>"](None)
    assert search_bar.is_visible is False

    root.bindings["<Control-Tab>"]()
    root.bindings["<Control-Shift-Tab>"]()
    root.bindings["<Control-Shift-W>"]()
    root.bindings["<Control-Shift-Alt-W>"]()
    assert panel_calls == ["next", "previous", "close_current", "close_all"]

    root.bindings["<Control-space>"](None)
    assert "snippets.expand" in call_order

    root.bindings["<Control-Shift-G>"]()
    assert "interface.open_generate_text_panel" in call_order

    root.bindings["<Control-Shift-C>"]()
    assert "llm.complete" in call_order
