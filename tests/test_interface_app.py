from types import SimpleNamespace

import pytest

from app import interface, state
import app.performance_optimizer as perf_opt


@pytest.fixture(autouse=True)
def silence_logs(monkeypatch):
    monkeypatch.setattr(interface.logs_console, "log", lambda *args, **kwargs: None)


def make_tab(file_path="doc.tex"):
    editor = SimpleNamespace(get=lambda *args: "content")
    return SimpleNamespace(file_path=file_path, editor=editor)


def test_perform_heavy_updates_without_tab(monkeypatch):
    outline_calls = []
    state.heavy_update_timer_id = "timer"
    state.get_current_tab = lambda: None
    state.outline = SimpleNamespace(update_outline=lambda value: outline_calls.append(value))

    interface.perform_heavy_updates()

    assert state.heavy_update_timer_id is None
    assert outline_calls == [None]


def test_perform_heavy_updates_with_tab(monkeypatch):
    schedule_calls = []

    def fake_schedule(editor, update_types, force=False):
        schedule_calls.append((editor, update_types, force))

    monkeypatch.setattr(perf_opt, "schedule_optimized_update", fake_schedule)

    debug_calls = []
    state.debug_coordinator = SimpleNamespace(set_current_document=lambda path, content: debug_calls.append((path, content)))
    state.get_current_tab = lambda: make_tab()

    interface.perform_heavy_updates()

    assert schedule_calls
    editor, update_types, force = schedule_calls[0]
    assert force is True
    assert perf_opt.UpdateType.ALL in update_types
    assert debug_calls[0][0].endswith("doc.tex")


def test_schedule_heavy_updates_without_tab(monkeypatch):
    state.get_current_tab = lambda: None
    calls = []

    monkeypatch.setattr(perf_opt, "schedule_optimized_update", lambda *args, **kwargs: calls.append(True))

    interface.schedule_heavy_updates()

    assert calls == []


def test_schedule_heavy_updates_with_tab(monkeypatch):
    tab = make_tab()
    state.get_current_tab = lambda: tab
    calls = []

    def fake_schedule(editor, update_types, force=False):
        calls.append((editor, update_types, force))

    monkeypatch.setattr(perf_opt, "schedule_optimized_update", fake_schedule)

    interface.schedule_heavy_updates()

    assert calls
    editor, update_types, force = calls[0]
    assert editor is tab.editor
    assert force is False
