from types import SimpleNamespace

import pytest

from app import exit_handler, state
from app import config as app_config
import app.interface as interface_module
from llm import state as llm_state


class DummyTab:
    def __init__(self, file_path, dirty=False, save_result=True):
        self.file_path = file_path
        self._dirty = dirty
        self._save_result = save_result

    def is_dirty(self):
        return self._dirty

    def save_file(self, new_path=None):
        if new_path:
            self.file_path = new_path
        return self._save_result


class DummyNotebook:
    def __init__(self, tab_ids):
        self._tab_ids = tab_ids
        self.selected = None

    def tabs(self):
        return list(self._tab_ids)

    def select(self, tab_id):
        self.selected = tab_id

    def forget(self, tab_id):
        self._tab_ids.remove(tab_id)


class DummyRoot:
    def __init__(self, fullscreen=False, window_state="normal"):
        self._fullscreen = fullscreen
        self._window_state = window_state
        self.destroy_called = False

    def attributes(self, name):
        return self._fullscreen if name == "-fullscreen" else None

    def state(self):
        return self._window_state

    def destroy(self):
        self.destroy_called = True


@pytest.fixture(autouse=True)
def reset_notebook():
    state.notebook = None
    yield
    state.notebook = None


def test_handle_unsaved_changes_no_dirty_tabs():
    state.tabs = {}

    result = exit_handler.handle_unsaved_changes()

    assert result == "dont_save"


def test_handle_unsaved_changes_with_dirty_tabs(monkeypatch):
    state.tabs = {
        "a": DummyTab("C:/docs/one.tex", dirty=True),
        "b": DummyTab(None, dirty=False),
    }
    captured = {}

    def fake_dialog(files, root):
        captured["files"] = files
        return "save"

    monkeypatch.setattr(exit_handler, "show_unsaved_changes_dialog_multiple_files", fake_dialog)

    result = exit_handler.handle_unsaved_changes()

    assert result == "save"
    assert captured["files"] == ["one.tex"]


def test_save_all_dirty_tabs_success(monkeypatch):
    tab1 = DummyTab("file1.tex", dirty=True)
    tab2 = DummyTab("file2.tex", dirty=False)
    state.tabs = {"tab1": tab1, "tab2": tab2}
    state.notebook = DummyNotebook(["tab1", "tab2"])

    calls = []

    def fake_save_file():
        calls.append("save")
        return True

    monkeypatch.setattr(interface_module, "save_file", fake_save_file)

    assert exit_handler.save_all_dirty_tabs() is True
    assert calls == ["save"]
    assert state.notebook.selected == "tab1"


def test_save_all_dirty_tabs_stops_on_failure(monkeypatch):
    tab = DummyTab("file1.tex", dirty=True)
    state.tabs = {"tab1": tab}
    state.notebook = DummyNotebook(["tab1"])

    monkeypatch.setattr(interface_module, "save_file", lambda: False)

    assert exit_handler.save_all_dirty_tabs() is False


def test_save_application_state_writes_updates(monkeypatch):
    state.root = DummyRoot(fullscreen=False, window_state="zoomed")
    state.current_theme = "flatly"

    saved_updates = {}

    monkeypatch.setattr(app_config, "load_config", lambda: {"gemini_api_key": "abc"})
    monkeypatch.setattr(app_config, "update_and_save_config", saved_updates.update)

    # Prepare llm state attributes
    llm_state.model_completion = "m1"
    llm_state.model_generation = "m2"
    llm_state.model_rephrase = "m3"
    llm_state.model_debug = "m4"
    llm_state.model_style = "m5"
    llm_state.model_proofreading = "m6"

    save_session_called = {}
    monkeypatch.setattr(interface_module, "save_session", lambda: save_session_called.setdefault("called", True))

    exit_handler.save_application_state()

    assert saved_updates["window_state"] == "Maximized"
    assert saved_updates["theme"] == "flatly"
    assert saved_updates["gemini_api_key"] == "abc"
    assert saved_updates["model_completion"] == "m1"
    assert save_session_called.get("called") is True


def test_exit_application_cancel(monkeypatch):
    monkeypatch.setattr(exit_handler, "handle_unsaved_changes", lambda: "cancel")

    assert exit_handler.exit_application() is False


def test_exit_application_success(monkeypatch):
    state.root = DummyRoot()
    state.metrics_display = SimpleNamespace(save_current_session=lambda: None)

    order = []

    monkeypatch.setattr(exit_handler, "handle_unsaved_changes", lambda: "save")
    monkeypatch.setattr(exit_handler, "save_all_dirty_tabs", lambda: order.append("save_all") or True)
    monkeypatch.setattr(exit_handler, "save_application_state", lambda: order.append("save_state"))

    result = exit_handler.exit_application()

    assert result is True
    assert order == ["save_all", "save_state"]
    assert state.root.destroy_called is True


def test_restart_application_executes(monkeypatch):
    executed = {}

    monkeypatch.setattr(exit_handler, "handle_unsaved_changes", lambda: "dont_save")
    monkeypatch.setattr(exit_handler, "save_all_dirty_tabs", lambda: True)
    monkeypatch.setattr(exit_handler, "save_application_state", lambda: executed.setdefault("state", True))
    monkeypatch.setattr(exit_handler.os, "execl", lambda *args: executed.setdefault("execl", args))

    result = exit_handler.restart_application()

    assert result is True
    assert executed["state"] is True
    assert "execl" in executed
