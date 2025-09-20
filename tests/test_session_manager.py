import configparser
import json

import pytest

from app import session_manager
from app import state
from utils import logs_console


class StubTab:
    def __init__(self, path):
        self.file_path = path


def _write_config(path, payload):
    config = configparser.ConfigParser()
    config[session_manager.SESSION_SECTION] = payload
    with open(path, "w", encoding="utf-8") as handle:
        config.write(handle)


@pytest.fixture
def temp_config(tmp_path, monkeypatch):
    config_path = tmp_path / "settings.conf"
    monkeypatch.setattr(session_manager, "CONFIG_FILE", str(config_path))
    return config_path


@pytest.fixture
def capture_logs(monkeypatch):
    entries = []
    monkeypatch.setattr(logs_console, "log", lambda message, level="INFO": entries.append((level, message)))
    return entries


def test_save_session_writes_unique_paths(tmp_path, temp_config):
    valid = tmp_path / "doc.tex"
    valid.write_text("example", encoding="utf-8")
    duplicate = tmp_path / "notes.tex"
    duplicate.write_text("data", encoding="utf-8")

    state.tabs = {
        "a": StubTab(str(valid)),
        "b": StubTab(str(duplicate)),
        "c": StubTab(str(duplicate)),
        "d": StubTab(None),
    }

    session_manager.save_session()

    parser = configparser.ConfigParser()
    parser.read(temp_config)
    stored = json.loads(parser[session_manager.SESSION_SECTION]["open_files"])

    assert stored == [str(valid), str(duplicate)]


def test_load_session_reopens_existing_files(tmp_path, temp_config, capture_logs):
    existing = tmp_path / "paper.tex"
    existing.write_text("hello", encoding="utf-8")
    missing = tmp_path / "missing.tex"

    _write_config(
        temp_config,
        {"open_files": json.dumps([str(existing), str(missing), str(existing)])},
    )

    opened = []
    session_manager.load_session(lambda path: opened.append(path))

    assert opened == [str(existing)]
    assert any("not reopening" in message for _, message in capture_logs)


def test_load_session_handles_invalid_payload(temp_config, capture_logs):
    _write_config(temp_config, {"open_files": "not-json"})

    session_manager.load_session(lambda path: None)

    assert any(level == "WARNING" for level, _ in capture_logs)
