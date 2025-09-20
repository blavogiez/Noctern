from types import SimpleNamespace

from app import statusbar


class DummyLabel:
    def __init__(self):
        self.text = None

    def config(self, **kwargs):
        self.text = kwargs.get("text", self.text)


class DummyRoot:
    def __init__(self):
        self.after_calls = []
        self.cancelled = []

    def after(self, duration, callback):
        self.after_calls.append((duration, callback))
        return "timer-id"

    def after_cancel(self, timer_id):
        self.cancelled.append(timer_id)


def test_show_temporary_status_message_sets_timer():
    label = DummyLabel()
    root = DummyRoot()

    statusbar._temporary_status_timer_id = None
    statusbar.show_temporary_status_message("Working", 1000, label, root, lambda: None)

    assert label.text == "Working"
    assert statusbar._temporary_status_timer_id == "timer-id"
    assert root.after_calls[0][0] == 1000


def test_show_temporary_status_message_cancels_existing():
    label = DummyLabel()
    root = DummyRoot()

    statusbar._temporary_status_timer_id = "old"
    statusbar.show_temporary_status_message("Again", 500, label, root, lambda: None)

    assert root.cancelled == ["old"]
    assert statusbar._temporary_status_timer_id == "timer-id"


def test_clear_temporary_status_message():
    statusbar._temporary_status_timer_id = "timer"
    statusbar.clear_temporary_status_message()
    assert statusbar._temporary_status_timer_id is None
