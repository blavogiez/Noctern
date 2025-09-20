import pytest

from app import state
from app import ui_feedback


class DummyPane:
    def __init__(self, name="console"):
        self.name = name

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


class DummyPaneContainer:
    def __init__(self):
        self._ids = []
        self.add_calls = []
        self.remove_calls = []

    def panes(self):
        return tuple(self._ids)

    def add(self, pane, height):
        self._ids.append(str(pane))
        self.add_calls.append((pane, height))

    def remove(self, pane):
        pane_id = str(pane)
        if pane_id in self._ids:
            self._ids.remove(pane_id)
        self.remove_calls.append(pane)


class DummyText:
    def __init__(self):
        self.state = None
        self.content = None
        self.deleted = []

    def config(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]

    def delete(self, start, end):
        self.deleted.append((start, end))

    def insert(self, index, content):
        self.content = content


@pytest.fixture
def console_setup():
    pane = DummyPane()
    pane_container = DummyPaneContainer()
    text_widget = DummyText()

    state.console_pane = pane
    state.console_output = text_widget
    state.vertical_pane = pane_container

    return pane, pane_container, text_widget


def test_show_console_adds_pane_and_writes_content(console_setup):
    pane, container, text_widget = console_setup

    ui_feedback.show_console("compiler output")

    assert container.add_calls == [(pane, 150)]
    assert text_widget.deleted[-1] == ("1.0", ui_feedback.END)
    assert text_widget.content == "compiler output"
    assert text_widget.state == "disabled"


def test_show_console_skip_when_pane_missing():
    state.console_pane = None
    state.console_output = None

    ui_feedback.show_console("nothing happens")


def test_hide_console_removes_existing(console_setup):
    pane, container, _ = console_setup
    container.add(pane, 150)

    ui_feedback.hide_console()

    assert container.remove_calls == [pane]
    assert pane.name not in container.panes()


def test_show_temporary_status_message_sets_flag(monkeypatch):
    events = {}

    def fake_flash(widget, flash_color, original_color):
        events["flash"] = (widget, flash_color, original_color)

    def fake_show(message, duration, label, root, callback):
        events["status"] = (message, duration, label, root, callback)

    monkeypatch.setattr(ui_feedback.animations, "flash_widget", fake_flash)
    monkeypatch.setattr(
        ui_feedback.interface_statusbar,
        "show_temporary_status_message",
        fake_show,
    )

    state.status_label = object()
    state.root = object()
    state._theme_settings = {"statusbar_bg": "base", "success": "flash"}

    ui_feedback.show_temporary_status_message("Saved")

    assert state._temporary_status_active is True
    assert events["flash"][1:] == ("flash", "base")
    assert events["status"][0] == "Saved"
    assert events["status"][-1] is ui_feedback.clear_temporary_status_message


def test_clear_temporary_status_message_resets_flag(monkeypatch):
    calls = {}

    monkeypatch.setattr(
        ui_feedback.status_utils,
        "update_status_bar_text",
        lambda: calls.setdefault("updated", True),
    )
    monkeypatch.setattr(
        ui_feedback.interface_statusbar,
        "clear_temporary_status_message",
        lambda: calls.setdefault("cleared", True),
    )

    state._temporary_status_active = True

    ui_feedback.clear_temporary_status_message()

    assert state._temporary_status_active is False
    assert calls == {"updated": True, "cleared": True}
