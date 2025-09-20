import os
from types import SimpleNamespace

import pytest

from app import file_operations


class DummyTab:
    def __init__(self, file_path=None, save_result=True):
        self.file_path = file_path
        self._save_result = save_result
        self.saved_with = None

    def save_file(self, new_path=None):
        if new_path:
            self.file_path = new_path
            self.saved_with = new_path
        return self._save_result


@pytest.fixture(autouse=True)
def silence_logs(monkeypatch):
    monkeypatch.setattr(file_operations.logs_console, "log", lambda *args, **kwargs: None)


def test_open_file_creates_tab(monkeypatch, tmp_path):
    chosen = tmp_path / "doc.tex"
    chosen.write_text("content", encoding="utf-8")

    calls = {}

    monkeypatch.setattr(
        file_operations.filedialog,
        "askopenfilename",
        lambda **kwargs: str(chosen),
    )

    file_operations.open_file(
        lambda **kwargs: calls.setdefault("tab", kwargs),
        lambda message: calls.setdefault("status", message),
    )

    assert calls["tab"]["file_path"] == str(chosen)
    assert os.path.basename(str(chosen)) in calls["status"]


def test_open_file_cancel(monkeypatch):
    monkeypatch.setattr(file_operations.filedialog, "askopenfilename", lambda **kwargs: "")

    called = {}

    file_operations.open_file(
        lambda **kwargs: called.setdefault("tab", True),
        lambda message: called.setdefault("status", message),
    )

    assert "tab" not in called


def test_save_file_with_existing_path(monkeypatch):
    tab = DummyTab(file_path="doc.tex", save_result=True)

    status = {}

    result = file_operations.save_file(
        lambda: tab,
        lambda message: status.setdefault("message", message),
        lambda: False,
    )

    assert result is True
    assert "doc.tex" in status["message"]


def test_save_file_redirects_when_no_path(monkeypatch):
    tab = DummyTab(file_path=None)

    result = file_operations.save_file(
        lambda: tab,
        lambda message: None,
        lambda: True,
    )

    assert result is True


def test_save_file_without_tab():
    result = file_operations.save_file(lambda: None, lambda message: None, lambda: False)

    assert result is False


def test_save_file_as_success(monkeypatch, tmp_path):
    new_path = tmp_path / "out.tex"
    tab = DummyTab(file_path="old.tex")

    monkeypatch.setattr(
        file_operations.filedialog,
        "asksaveasfilename",
        lambda **kwargs: str(new_path),
    )

    calls = {"changed": 0}

    def on_tab_changed():
        calls["changed"] += 1

    result = file_operations.save_file_as(
        lambda: tab,
        lambda message: calls.setdefault("status", message),
        on_tab_changed,
    )

    assert result is True
    assert tab.file_path == str(new_path)
    assert calls["changed"] == 1
    assert os.path.basename(str(new_path)) in calls["status"]


def test_save_file_as_cancel(monkeypatch):
    tab = DummyTab(file_path="old.tex")
    monkeypatch.setattr(file_operations.filedialog, "asksaveasfilename", lambda **kwargs: "")

    result = file_operations.save_file_as(
        lambda: tab,
        lambda message: None,
        lambda: None,
    )

    assert result is False
