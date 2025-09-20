from types import SimpleNamespace

import pytest

from app import tab_operations


class DummyTab:
    def __init__(self, file_path, dirty=False, save_ok=True):
        self.file_path = file_path
        self._dirty = dirty
        self.save_ok = save_ok

    def is_dirty(self):
        return self._dirty

    def save_file(self):
        return self.save_ok


class DummyNotebook:
    def __init__(self):
        self._tabs = []
        self.selected = None
        self.forgotten = []

    def tabs(self):
        return list(self._tabs)

    def add(self, widget, text):
        self._tabs.append(str(widget))

    def select(self, tab_id=None):
        if tab_id is None:
            return self.selected
        self.selected = tab_id

    def forget(self, tab_id):
        self.forgotten.append(tab_id)
        if tab_id in self._tabs:
            self._tabs.remove(tab_id)


@pytest.fixture(autouse=True)
def silence_logs(monkeypatch):
    monkeypatch.setattr(tab_operations.logs_console, "log", lambda *args, **kwargs: None)


def test_close_current_tab_prompts_and_saves(monkeypatch):
    notebook = DummyNotebook()
    open_tabs = {"tab1": DummyTab("doc.tex", dirty=True)}
    notebook._tabs = ["tab1"]
    notebook.selected = "tab1"
    stack = []

    monkeypatch.setattr(tab_operations, "show_unsaved_changes_dialog", lambda *args, **kwargs: "save")

    tab_operations.close_current_tab(
        lambda: open_tabs["tab1"],
        SimpleNamespace(),
        notebook,
        lambda: True,
        lambda **kwargs: None,
        open_tabs,
        stack,
    )

    assert notebook.forgotten == ["tab1"]
    assert stack == ["doc.tex"]


def test_close_current_tab_cancel(monkeypatch):
    notebook = DummyNotebook()
    open_tabs = {"tab1": DummyTab("doc.tex", dirty=True)}
    notebook._tabs = ["tab1"]
    stack = []

    monkeypatch.setattr(tab_operations, "show_unsaved_changes_dialog", lambda *args, **kwargs: "cancel")

    tab_operations.close_current_tab(
        lambda: open_tabs["tab1"],
        SimpleNamespace(),
        notebook,
        lambda: True,
        lambda **kwargs: None,
        open_tabs,
        stack,
    )

    assert notebook.forgotten == []
    assert stack == []


def test_create_new_tab_switches_to_existing():
    notebook = DummyNotebook()
    open_tab = DummyTab("/path/to/file.tex")
    open_tabs = {"tab1": open_tab}
    notebook._tabs = ["tab1"]

    tab_operations.create_new_tab(
        file_path="/path/to/file.tex",
        notebook_widget=notebook,
        open_tabs_dict=open_tabs,
        apply_theme_callback=lambda: None,
        on_tab_changed_callback=lambda: None,
        EditorTab_class=lambda *args, **kwargs: None,
        schedule_heavy_updates_callback=lambda: None,
    )

    assert notebook.selected == "tab1"


def test_create_new_tab_creates_instance():
    notebook = DummyNotebook()
    open_tabs = {}
    created = {}

    class FakeTab:
        def __init__(self, parent, file_path=None, schedule_heavy_updates_callback=None):
            self.parent = parent
            self.file_path = file_path
            self.schedule_heavy_updates_callback = schedule_heavy_updates_callback

        def load_file(self):
            created["loaded"] = True

        def __str__(self):
            return "fake-tab"

        def config(self, **kwargs):
            pass

    tab_operations.create_new_tab(
        file_path=None,
        notebook_widget=notebook,
        open_tabs_dict=open_tabs,
        apply_theme_callback=lambda: created.setdefault("theme", True),
        on_tab_changed_callback=lambda: None,
        EditorTab_class=FakeTab,
        schedule_heavy_updates_callback=lambda: None,
    )

    assert str(notebook.selected) == "fake-tab"
    assert created["loaded"] is True
    assert created["theme"] is True
    assert "fake-tab" in open_tabs
