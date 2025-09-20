import pytest

from app import state
from app import tab_actions


class DummyTab:
    def __init__(self, path=None):
        self.file_path = path

    def is_dirty(self):
        return False


class DummyMetrics:
    def __init__(self):
        self.history = []

    def save_current_session(self):
        self.history.append("save")

    def set_current_file(self, path):
        self.history.append(("file", path))


@pytest.fixture(autouse=True)
def clear_tabs():
    state.tabs = {}
    state._closed_tabs_stack = []


def test_close_current_tab_delegates(monkeypatch):
    state.root = object()
    state.notebook = object()
    state.tabs = {}
    state._closed_tabs_stack = []
    state.get_current_tab = lambda: DummyTab("doc.tex")

    captured = {}

    def fake_close(get_tab, root, notebook, save_cb, create_cb, tabs, stack):
        captured["called"] = (
            get_tab(),
            root,
            notebook,
            save_cb,
            create_cb,
            tabs,
            stack,
        )
        return "done"

    monkeypatch.setattr(tab_actions.interface_tabops, "close_current_tab", fake_close)

    result = tab_actions.close_current_tab(lambda: True, lambda **_: None)

    assert result == "done"
    current_tab, root, notebook, _, _, tabs, stack = captured["called"]
    assert current_tab.file_path == "doc.tex"
    assert root is state.root
    assert notebook is state.notebook
    assert tabs is state.tabs
    assert stack is state._closed_tabs_stack


def test_create_new_tab_passes_dependencies(monkeypatch):
    state.notebook = object()
    state.tabs = {}

    args = {}

    def fake_create(file_path, notebook, tabs, apply_theme, on_tab_changed, editor_factory, schedule_updates):
        args.update(
            file_path=file_path,
            notebook=notebook,
            tabs=tabs,
            apply=apply_theme,
            changed=on_tab_changed,
            editor=editor_factory,
            schedule=schedule_updates,
        )

    monkeypatch.setattr(tab_actions.interface_tabops, "create_new_tab", fake_create)

    tab_actions.create_new_tab(
        file_path="notes.tex",
        apply_theme=lambda: None,
        on_tab_changed=lambda *_: None,
        schedule_heavy_updates=lambda *_: None,
        editor_factory=object,
    )

    assert args["file_path"] == "notes.tex"
    assert args["notebook"] is state.notebook
    assert args["tabs"] is state.tabs


def test_restore_last_closed_tab_calls_create(monkeypatch):
    calls = {}
    state._closed_tabs_stack = ["paper.tex"]

    tab_actions.restore_last_closed_tab(
        lambda **kw: calls.setdefault("path", kw["file_path"]),
        lambda message: None,
    )

    assert calls["path"] == "paper.tex"
    assert state._closed_tabs_stack == []


def test_restore_last_closed_tab_empty_stack_reports():
    messages = []

    tab_actions.restore_last_closed_tab(lambda **_: None, lambda msg: messages.append(msg))

    assert messages == ["\u2139\ufe0f No recently closed tabs to restore."]


def test_save_file_checks_images(monkeypatch):
    tab = DummyTab("doc.tex")
    state.get_current_tab = lambda: tab

    called = {}
    monkeypatch.setattr(
        tab_actions.editor_image_manager,
        "check_for_deleted_images",
        lambda current: called.setdefault("image", current.file_path),
    )

    def fake_save(getter, status, save_as):
        called["ops"] = (getter(), status, save_as)
        return "saved"

    monkeypatch.setattr(tab_actions.interface_fileops, "save_file", fake_save)

    result = tab_actions.save_file(lambda msg: None, lambda: None)

    assert result == "saved"
    assert called["image"] == "doc.tex"
    getter_result, _, _ = called["ops"]
    assert getter_result.file_path == "doc.tex"


def test_save_file_as_forwards(monkeypatch):
    tab = DummyTab("doc.tex")
    state.get_current_tab = lambda: tab

    called = {}
    monkeypatch.setattr(
        tab_actions.editor_image_manager,
        "check_for_deleted_images",
        lambda current: called.setdefault("image", current.file_path),
    )

    def fake_save_as(getter, status, on_changed):
        called["ops"] = (getter(), status, on_changed)
        return "saved_as"

    monkeypatch.setattr(tab_actions.interface_fileops, "save_file_as", fake_save_as)

    result = tab_actions.save_file_as(lambda msg: None, lambda *_: None)

    assert result == "saved_as"
    assert called["image"] == "doc.tex"


def test_on_tab_changed_without_tab_clears_metrics():
    state.get_current_tab = lambda: None
    state.metrics_display = DummyMetrics()

    tab_actions.on_tab_changed(lambda: None)

    assert state.metrics_display.history == [("file", None)]


def test_on_tab_changed_with_tab_updates_services(monkeypatch):
    tab = DummyTab("thesis.tex")
    state.get_current_tab = lambda: tab
    state.metrics_display = DummyMetrics()

    calls = {}
    monkeypatch.setattr(
        tab_actions.llm_service,
        "load_prompt_history_for_current_file",
        lambda: calls.setdefault("history", True),
    )
    monkeypatch.setattr(
        tab_actions.llm_service,
        "load_prompts_for_current_file",
        lambda: calls.setdefault("prompts", True),
    )

    updates = []

    tab_actions.on_tab_changed(lambda: updates.append("updated"))

    assert ("file", "thesis.tex") in state.metrics_display.history
    assert calls == {"history": True, "prompts": True}
    assert updates == ["updated"]
