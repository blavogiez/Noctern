from types import SimpleNamespace
import sys

import pytest

from app import zoom, state


class FakeFont:
    def __init__(self, family, size, weight="normal", slant="roman"):
        self._values = {"family": family, "size": size, "weight": weight, "slant": slant}

    def cget(self, key):
        return self._values[key]


class DummyEditor:
    def __init__(self):
        self.configured = None

    def config(self, **kwargs):
        self.configured = kwargs.get("font")


class DummyLineNumbers:
    def __init__(self):
        self.font = None


def make_tab(size=12):
    editor_font = FakeFont("Consolas", size)
    editor = DummyEditor()
    line_numbers = DummyLineNumbers()
    return SimpleNamespace(editor=editor, editor_font=editor_font, line_numbers=line_numbers, file_path="test.tex")


@pytest.fixture
def patched_zoom(monkeypatch):
    monkeypatch.setattr(zoom, "Font", FakeFont)

    # mock the interface module import inside zoom methods
    mock_interface = SimpleNamespace(perform_heavy_updates=lambda: None)
    monkeypatch.setitem(sys.modules, "app.interface", mock_interface)

    updates = []
    # mock the line number update function import
    mock_line_manager = SimpleNamespace(force_line_number_update=lambda widget: updates.append(widget))
    monkeypatch.setitem(sys.modules, "editor.line_number_manager", mock_line_manager)
    return updates


def test_zoom_in_increases_font(patched_zoom):
    updates = patched_zoom
    tab = make_tab(size=10)
    state.get_current_tab = lambda: tab
    state.zoom_factor = 1.2
    state.max_font_size = 20
    state.min_font_size = 8
    state.tabs = {"tab1": tab}
    manager = zoom.ZoomManager(state)

    manager.zoom_in()

    assert tab.editor.configured.cget("size") <= state.max_font_size
    assert tab.editor_font.cget("size") > 10
    assert updates


def test_zoom_out_decreases_font(patched_zoom):
    make_updates = patched_zoom  # ensure fixture applied
    tab = make_tab(size=14)
    state.get_current_tab = lambda: tab
    state.zoom_factor = 1.5
    state.max_font_size = 30
    state.min_font_size = 8
    manager = zoom.ZoomManager(state)

    manager.zoom_out()

    assert tab.editor_font.cget("size") < 14
    assert tab.editor_font.cget("size") >= state.min_font_size


def test_update_font_family_applies_to_all_tabs(patched_zoom):
    tab1 = make_tab(size=11)
    tab2 = make_tab(size=13)
    state.tabs = {"1": tab1, "2": tab2}
    manager = zoom.ZoomManager(state)

    manager.update_font_family("Fira Code")

    assert tab1.editor_font.cget("family") == "Fira Code"
    assert tab2.editor_font.cget("family") == "Fira Code"
