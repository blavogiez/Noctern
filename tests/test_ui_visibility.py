from types import SimpleNamespace

from app import ui_visibility, state


def test_is_status_bar_visible_handles_missing():
    state.status_bar_frame = None
    assert ui_visibility.is_status_bar_visible() is False


class FrameStub:
    def __init__(self, viewable=True):
        self._viewable = viewable

    def winfo_viewable(self):
        return self._viewable


def test_is_status_bar_visible_when_frame_present():
    state.status_bar_frame = FrameStub(viewable=True)
    assert ui_visibility.is_status_bar_visible() is True


def test_is_pdf_preview_visible():
    pane_master = SimpleNamespace()
    pane = SimpleNamespace(master=pane_master)

    class ParentStub:
        def panes(self):
            return [pane_master]

    state.pdf_preview_interface = object()
    state.pdf_preview_pane = pane
    state.pdf_preview_parent = ParentStub()

    assert ui_visibility.is_pdf_preview_visible() is True

    state.pdf_preview_parent = ParentStub()
    state.pdf_preview_interface = None
    assert ui_visibility.is_pdf_preview_visible() is False
