from types import SimpleNamespace

from app import status_utils


class DummyLabel:
    def __init__(self):
        self.text = None

    def config(self, **kwargs):
        self.text = kwargs.get("text", self.text)


class DummyEditor:
    def __init__(self, content):
        self._content = content

    def get(self, start, end):
        return self._content


class DummyContentCache:
    def __init__(self):
        self.store = {}

    def get_content_hash(self, content):
        return f"hash:{content}"

    def get_cached_wordcount(self, content_hash):
        return self.store.get(content_hash)

    def cache_wordcount(self, content_hash, value):
        self.store[content_hash] = value


status_utils._performance_optimizer = SimpleNamespace(content_cache=DummyContentCache())


def test_update_status_bar_text_uses_cache(monkeypatch):
    label = DummyLabel()
    status_utils.state.status_label = label
    status_utils.state.metrics_display = SimpleNamespace(update_word_count=lambda value: setattr(label, "metric", value))

    tab = SimpleNamespace(
        file_path="doc.tex",
        editor=DummyEditor("hello world"),
    )
    status_utils.state.get_current_tab = lambda: tab

    counts = []
    monkeypatch.setattr(status_utils.editor_wordcount, "update_word_count", lambda editor, label_widget: counts.append(5) or 5)

    status_utils.update_status_bar_text()
    assert label.text.endswith("words")
    assert getattr(label, "metric") == 5

    status_utils.update_status_bar_text()
    assert counts == [5]


def test_update_status_bar_text_without_tab():
    status_utils.state.status_label = DummyLabel()
    status_utils.state.get_current_tab = lambda: None

    status_utils.update_status_bar_text()
    assert status_utils.state.status_label.text == "..."
