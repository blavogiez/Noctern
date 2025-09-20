import pytest

from app import state

_TRACKED_ATTRS = [
    "console_pane",
    "console_output",
    "vertical_pane",
    "status_label",
    "_temporary_status_active",
    "_theme_settings",
    "root",
    "notebook",
    "tabs",
    "_closed_tabs_stack",
    "metrics_display",
]


@pytest.fixture(autouse=True)
def reset_app_state():
    snapshot = {name: getattr(state, name, None) for name in _TRACKED_ATTRS}
    yield
    for name, value in snapshot.items():
        setattr(state, name, value)
