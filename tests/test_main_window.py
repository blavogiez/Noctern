from types import SimpleNamespace

import pytest

from app import main_window


class DummyWindow:
    def __init__(self):
        self.geometry_calls = []
        self.state_calls = []
        self.minsize_value = None
        self.attributes_values = {}

    def geometry(self, value):
        self.geometry_calls.append(value)

    def state(self, value=None):
        if value is None:
            return self.state_calls[-1] if self.state_calls else "normal"
        self.state_calls.append(value)

    def attributes(self, name, value=None):
        if value is None:
            return self.attributes_values.get(name, False)
        self.attributes_values[name] = value

    def minsize(self, width, height):
        self.minsize_value = (width, height)


def make_monitor(index, width=1920, height=1080, primary=False):
    return SimpleNamespace(
        x=index * width,
        y=0,
        width=width,
        height=height,
        is_primary=primary,
    )


@pytest.fixture(autouse=True)
def silence_logs(monkeypatch):
    monkeypatch.setattr(main_window.logs_console, "log", lambda *args, **kwargs: None)


def test_apply_startup_settings_without_monitors(monkeypatch):
    window = DummyWindow()
    monkeypatch.setattr(main_window.screen_utils, "get_monitors", lambda: [])

    main_window._apply_startup_window_settings(window, {})

    assert window.geometry_calls == ["1200x800"]


def test_apply_startup_settings_maximized(monkeypatch):
    monitor_primary = make_monitor(0, primary=True)
    monitor_secondary = make_monitor(1)
    monkeypatch.setattr(main_window.screen_utils, "get_monitors", lambda: [monitor_primary, monitor_secondary])

    window = DummyWindow()
    config = {"app_monitor": "Monitor 2: 1920x1080", "window_state": "Maximized"}

    main_window._apply_startup_window_settings(window, config)

    assert window.geometry_calls[0].startswith("+")
    assert window.state_calls == ["zoomed"]


def test_apply_startup_settings_fullscreen(monkeypatch):
    monitor = make_monitor(0, primary=True)
    monkeypatch.setattr(main_window.screen_utils, "get_monitors", lambda: [monitor])

    window = DummyWindow()
    config = {"window_state": "Fullscreen"}

    main_window._apply_startup_window_settings(window, config)

    assert window.attributes_values["-fullscreen"] is True
