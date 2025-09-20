from pathlib import Path

import pytest

from app import icons


@pytest.fixture(autouse=True)
def reset_cache():
    icons._icon_cache.clear()
    yield
    icons._icon_cache.clear()


def test_get_icon_returns_none_when_missing(monkeypatch):
    monkeypatch.setattr(icons.os.path, "exists", lambda path: False)
    result = icons.get_icon("missing.svg")
    assert result is None


def test_get_icon_loads_svg_and_caches(monkeypatch, tmp_path):
    icons_dir = tmp_path / "icons"
    icons_dir.mkdir()
    svg_path = icons_dir / "test.svg"
    svg_path.write_text('<svg stroke="currentColor"></svg>', encoding="utf-8")

    monkeypatch.setattr(icons.os.path, "join", lambda *parts: str(svg_path))
    monkeypatch.setattr(icons.os.path, "exists", lambda path: Path(path) == svg_path)

    class DummySvgImage:
        def __init__(self, data, scaletowidth):
            self.data = data
            self.scaletowidth = scaletowidth

    monkeypatch.setattr(icons.tksvg, "SvgImage", DummySvgImage)

    first = icons.get_icon("test.svg", size=24, color="#ffffff")
    second = icons.get_icon("test.svg", size=24, color="#ffffff")

    assert isinstance(first, DummySvgImage)
    assert first is second
    assert 'stroke="#ffffff"' in first.data
