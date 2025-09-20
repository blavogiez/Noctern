"""Persist and restore editor sessions."""

from __future__ import annotations

import configparser
import json
import os
from typing import Callable, Iterable, List

from app import state
from app.config import CONFIG_FILE, DEFAULT_SECTION
from utils import logs_console

SESSION_SECTION = "Session"


def save_session() -> None:
    """Persist the paths of all open tabs."""
    open_files = _collect_open_files()
    config = _load_config()
    if DEFAULT_SECTION not in config:
        config[DEFAULT_SECTION] = {}
    if SESSION_SECTION not in config:
        config[SESSION_SECTION] = {}

    config[SESSION_SECTION]["open_files"] = json.dumps(open_files)

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as handle:
            config.write(handle)
        logs_console.log(f"Session state saved to {CONFIG_FILE}", level="INFO")
    except Exception as exc:
        logs_console.log(f"Error saving session state: {exc}", level="ERROR")


def load_session(create_tab: Callable[[str], None]) -> None:
    """Reopen files recorded in the last session."""
    try:
        config = _load_config()
        if SESSION_SECTION not in config:
            return

        raw_paths = config[SESSION_SECTION].get("open_files", "")
        if not raw_paths:
            return
        try:
            stored_paths: Iterable[str] = json.loads(raw_paths)
        except json.JSONDecodeError as exc:
            logs_console.log(f"Invalid session data: {exc}", level="WARNING")
            return

        seen: set[str] = set()
        for file_path in stored_paths:
            if not isinstance(file_path, str) or not file_path:
                continue
            if file_path in seen:
                continue
            seen.add(file_path)

            if os.path.exists(file_path):
                create_tab(file_path)
            else:
                logs_console.log(
                    f"File not found, not reopening: {file_path}",
                    level="WARNING",
                )
    except Exception as exc:
        logs_console.log(f"Error loading session state: {exc}", level="ERROR")


def _collect_open_files() -> List[str]:
    """Return a list of open file paths, keeping order and removing duplicates."""
    unique: List[str] = []
    seen: set[str] = set()
    for tab in state.tabs.values():
        file_path = getattr(tab, "file_path", None)
        if not file_path or not os.path.exists(file_path):
            continue
        if file_path in seen:
            continue
        seen.add(file_path)
        unique.append(file_path)
    return unique


def _load_config() -> configparser.ConfigParser:
    """Read the settings file if it exists."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config
