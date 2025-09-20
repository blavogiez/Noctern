from types import SimpleNamespace

import pytest

from app import status


class DummyLabel:
    def __init__(self):
        self.text = None

    def config(self, **kwargs):
        self.text = kwargs.get("text", self.text)

    def winfo_exists(self):
        return True


def test_update_gpu_status_with_data(monkeypatch):
    gpu = SimpleNamespace(load=0.5, memoryUsed=200, memoryTotal=400)
    monkeypatch.setattr(status.GPUtil, "getGPUs", lambda: [gpu])
    label = DummyLabel()

    status.update_gpu_status(label)

    assert "50.0%" in label.text
    assert "200/400" in label.text


def test_update_gpu_status_handles_exception(monkeypatch):
    monkeypatch.setattr(status.GPUtil, "getGPUs", lambda: (_ for _ in ()).throw(RuntimeError("fail")))
    logs = []
    monkeypatch.setattr(status.logs_console, "log", lambda message, level=None: logs.append((level, message)))
    label = DummyLabel()

    status.update_gpu_status(label)

    assert label.text == "GPU: Error"
    assert logs and logs[0][0] == "WARNING"


def test_start_gpu_status_loop(monkeypatch):
    calls = []
    monkeypatch.setattr(status, "update_gpu_status", lambda label: calls.append("updated"))

    label = DummyLabel()
    root = SimpleNamespace(after=lambda delay, callback: calls.append((delay, callback)))

    status.start_gpu_status_loop(label, root)

    assert calls[0] == "updated"
    assert calls[1][0] == 5000
