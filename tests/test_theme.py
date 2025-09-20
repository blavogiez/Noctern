from types import SimpleNamespace

import pytest

from app import theme


def test_get_luminance_bounds():
    assert pytest.approx(theme._get_luminance("#ffffff"), rel=1e-3) == 1.0
    assert pytest.approx(theme._get_luminance("#000000"), rel=1e-3) == 0.0
    assert theme._get_luminance("invalid") == 0.5


def test_adjust_brightness_lighten_and_darken():
    lighter = theme._adjust_brightness("#202020", 0.5)
    darker = theme._adjust_brightness("#808080", -0.5)
    assert lighter.startswith("#") and lighter != "#202020"
    assert darker.startswith("#") and darker != "#808080"


def test_calculate_contrast_ratio():
    ratio = theme._calculate_contrast_ratio("#ffffff", "#000000")
    assert ratio > 7


def test_get_contrasted_secondary():
    colors = SimpleNamespace(light="#ffffff", dark="#000000")
    assert theme._get_contrasted_secondary(colors, is_dark=True) == "#E8E8E8"
    assert theme._get_contrasted_secondary(colors, is_dark=False) == "#2A2A2A"
