"""
Ultra-fast line change tracking for differential syntax highlighting.
Only tracks what actually changed - maximum performance.
"""
import tkinter as tk
import weakref

class LineTracker:
    """Ultra-fast line change tracking for differential highlighting."""
    
    def __init__(self, editor):
        self.editor_ref = weakref.ref(editor)
        self.line_cache = {}  # line_num -> content_hash
        self.last_cursor_line = 1
        self.forced_changed_lines = set()
        
    def get_changed_lines(self):
        """Get only the lines that actually changed - ultra efficient."""
        editor = self.editor_ref()
        if not editor:
            return set()
            
        try:
            # Consume any forced-changed lines signaled by bulk operations
            forced = set(self.forced_changed_lines)
            self.forced_changed_lines.clear()

            cursor_pos = editor.index(tk.INSERT)
            current_cursor_line = int(cursor_pos.split('.')[0])
            
            # For single character changes, only check current line + context
            if abs(current_cursor_line - self.last_cursor_line) <= 1:
                changed_lines = self._check_focused_lines(editor, current_cursor_line)
            else:
                # Cursor moved significantly - check range
                start = min(self.last_cursor_line, current_cursor_line) - 1
                end = max(self.last_cursor_line, current_cursor_line) + 1
                changed_lines = self._check_range_lines(editor, start, end)
            
            self.last_cursor_line = current_cursor_line
            # Update cache for forced lines without rescanning
            if forced:
                self._snapshot_lines(editor, forced)
            # Union and return
            return changed_lines.union(forced)
            
        except tk.TclError:
            return set()
    
    def _check_focused_lines(self, editor, focus_line):
        """Check only the focused line and immediate context."""
        changed = set()
        
        # Check only current line and neighbors for maximum performance
        for line_num in range(max(1, focus_line - 1), focus_line + 2):
            if self._line_changed(editor, line_num):
                changed.add(line_num)
                
        return changed
    
    def _check_range_lines(self, editor, start_line, end_line):
        """Check a specific range of lines efficiently."""
        changed = set()
        
        try:
            total_lines = int(editor.index("end-1c").split('.')[0])
            start_line = max(1, start_line)
            end_line = min(total_lines, end_line)
            
            for line_num in range(start_line, end_line + 1):
                if self._line_changed(editor, line_num):
                    changed.add(line_num)
                    
        except tk.TclError:
            pass
            
        return changed
    
    def _line_changed(self, editor, line_num):
        """Check if a specific line changed."""
        try:
            line_content = editor.get(f"{line_num}.0", f"{line_num}.end")
            content_hash = hash(line_content)
            
            if line_num not in self.line_cache or self.line_cache[line_num] != content_hash:
                self.line_cache[line_num] = content_hash
                return True
            return False
            
        except tk.TclError:
            return False
    
    def invalidate_cache(self):
        """Clear the line cache for full refresh."""
        self.line_cache.clear()

    def mark_range_changed(self, start_line: int, end_line: int):
        """Mark an inclusive line range as changed (bulk insert/update)."""
        editor = self.editor_ref()
        if not editor:
            return
        try:
            total_lines = int(editor.index("end-1c").split('.')[0])
            start_line = max(1, int(start_line))
            end_line = min(total_lines, int(end_line))
            if end_line < start_line:
                start_line, end_line = end_line, start_line
            for ln in range(start_line, end_line + 1):
                self.forced_changed_lines.add(ln)
        except tk.TclError:
            pass

    def _snapshot_lines(self, editor, lines):
        """Update cache for specified lines to current content hash."""
        for ln in lines:
            try:
                content = editor.get(f"{ln}.0", f"{ln}.end")
                self.line_cache[ln] = hash(content)
            except tk.TclError:
                continue

# Global line trackers
_line_trackers = weakref.WeakKeyDictionary()

def get_line_tracker(editor):
    """Get or create line tracker for an editor."""
    if editor not in _line_trackers:
        _line_trackers[editor] = LineTracker(editor)
    return _line_trackers[editor]

def clear_line_tracker(editor):
    """Clear line tracker for an editor."""
    if editor in _line_trackers:
        del _line_trackers[editor]

def mark_range_changed(editor, start_line: int, end_line: int):
    """Convenience helper to mark a line range as changed for an editor."""
    tracker = get_line_tracker(editor)
    tracker.mark_range_changed(start_line, end_line)
