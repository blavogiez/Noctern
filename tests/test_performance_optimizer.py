from types import SimpleNamespace

import pytest

from app.performance_optimizer import ContentCache, ViewportTracker, PerformanceOptimizer, PerfConfig


def test_content_cache_detects_changes_and_eviction():
    cache = ContentCache(max_size=2)
    editor_a = object()
    editor_b = object()
    editor_c = object()

    changed, hash_a = cache.is_content_changed(editor_a, "hello")
    assert changed is True

    changed, hash_a_again = cache.is_content_changed(editor_a, "hello")
    assert changed is False
    assert hash_a == hash_a_again

    cache.cache_wordcount(hash_a, 5)
    assert cache.get_cached_wordcount(hash_a) == 5

    cache.is_content_changed(editor_b, "world")
    cache.is_content_changed(editor_c, "!")
    assert len(cache.content_hashes) <= cache.max_size


def test_viewport_tracker_detects_change():
    class DummyEditor:
        def __init__(self, top, bottom, total_lines):
            self._top = top
            self._bottom = bottom
            self._total = total_lines

        def yview(self):
            return (self._top, self._bottom)

        def index(self, value):
            return f"{self._total}.0"

    editor = DummyEditor(0.1, 0.2, 200)
    tracker = ViewportTracker(editor)

    assert tracker.has_viewport_changed() is True
    tracker.visible_start, tracker.visible_end = tracker.get_viewport_bounds()
    editor._top = 0.11
    editor._bottom = 0.21
    assert tracker.has_viewport_changed() is False


def test_get_file_size_category(monkeypatch):
    monkeypatch.setattr(PerformanceOptimizer, "_start_monitoring", lambda self: None)
    optimizer = PerformanceOptimizer()

    assert optimizer.get_file_size_category(100) == "small"
    assert optimizer.get_file_size_category(PerfConfig.LARGE_FILE_THRESHOLD) == "large"
    assert optimizer.get_file_size_category(PerfConfig.HUGE_FILE_THRESHOLD) == "huge"
