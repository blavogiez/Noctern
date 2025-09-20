import configparser
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app import config


class DummyLogger:
    def __init__(self):
        self.calls = []

    def log(self, message, level=None):
        self.calls.append((level, message))


@pytest.fixture
def temp_config(monkeypatch, tmp_path):
    dummy_logger = DummyLogger()
    monkeypatch.setattr(config, "CONFIG_FILE", str(tmp_path / "settings.conf"))
    monkeypatch.setattr(config.logs_console, "log", dummy_logger.log)
    return dummy_logger


def test_load_config_creates_defaults_when_missing(temp_config):
    result = config.load_config()
    assert result == config.DEFAULT_VALUES
    assert Path(config.CONFIG_FILE).exists()


def test_load_config_adds_missing_keys(temp_config):
    cfg = configparser.ConfigParser()
    cfg[config.DEFAULT_SECTION] = {"theme": "darkly"}
    path = Path(config.CONFIG_FILE)
    with path.open("w", encoding="utf-8") as handle:
        cfg.write(handle)

    result = config.load_config()

    assert result["theme"] == "darkly"
    assert result["font_size"] == config.DEFAULT_VALUES["font_size"]


def test_normalize_settings_clamps_and_coerces():
    raw = {
        "font_size": "2",
        "treeview_font_size": "100",
        "treeview_row_height": "bad",
        "show_status_bar": "0",
        "gemini_api_key": None,
    }

    normalized = config._normalize_settings(raw)

    assert normalized["font_size"] == "8"
    assert normalized["treeview_font_size"] == "18"
    assert normalized["treeview_row_height"] == config.DEFAULT_VALUES["treeview_row_height"]
    assert normalized["show_status_bar"] == "False"
    assert normalized["gemini_api_key"] == ""


def test_get_treeview_font_settings_handles_font_errors(monkeypatch):
    def raise_error():
        raise RuntimeError("fonts unavailable")

    monkeypatch.setitem(sys.modules, "tkinter.font", SimpleNamespace(families=raise_error))

    settings = config.get_treeview_font_settings({})

    assert settings == {"family": "Segoe UI", "size": 10, "row_height": 30}


def test_get_editor_font_settings_handles_invalid():
    data = {"editor_font_family": "Courier", "font_size": "500"}

    settings = config.get_editor_font_settings(data)

    assert settings["family"] == "Courier"
    assert settings["size"] == 72
