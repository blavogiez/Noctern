"""
Monaco Editor-inspired performance optimizations for Noctern.
Ultra-high performance text editor optimization layer.
"""

import tkinter as tk
import time
import weakref
from collections import defaultdict
from typing import Optional, Dict, List, Tuple, Set
from utils import logs_console

class DeltaTracker:
    """Track only changed document parts like Monaco Editor."""
    
    def __init__(self, editor):
        self.editor_ref = weakref.ref(editor)
        self.last_content_hash = ""
        self.last_line_count = 0
        self.changed_lines = set()  # Store only actually changed lines
        self.last_cursor_line = 0
        
    def get_delta(self) -> Optional[Dict]:
        """Get only changes since last update - Monaco style."""
        editor = self.editor_ref()
        if not editor:
            return None
            
        try:
            # Get cursor position efficiently
            cursor_line = int(editor.index(tk.INSERT).split('.')[0])
            
            # Perform full check only if cursor moved significantly
            if abs(cursor_line - self.last_cursor_line) > 3:
                return self._full_delta_check(editor, cursor_line)
            
            # Track cursor movement for highlighting optimization
            delta = {
                'type': 'cursor_move',
                'cursor_line': cursor_line,
                'old_cursor': self.last_cursor_line,
                'changed_lines': {cursor_line, self.last_cursor_line}
            }
            
            self.last_cursor_line = cursor_line
            return delta
            
        except tk.TclError:
            return None
    
    def _full_delta_check(self, editor, cursor_line):
        """Perform full change detection only when necessary."""
        try:
            # Calculate line count efficiently
            line_count = int(editor.index("end-1c").split('.')[0])
            line_count_changed = line_count != self.last_line_count
            
            # Check only cursor area for small changes
            if not line_count_changed and abs(cursor_line - self.last_cursor_line) <= 10:
                start_check = max(1, cursor_line - 5)
                end_check = min(line_count, cursor_line + 5)
                changed_lines = self._check_lines_range(editor, start_check, end_check)
            else:
                # Use smart detection to avoid full document scan
                changed_lines = self._smart_change_detection(editor, line_count)
            
            delta = {
                'type': 'content_change',
                'cursor_line': cursor_line,
                'line_count': line_count,
                'line_count_changed': line_count_changed,
                'changed_lines': changed_lines
            }
            
            self.last_cursor_line = cursor_line
            self.last_line_count = line_count
            return delta
            
        except tk.TclError:
            return None
    
    def _check_lines_range(self, editor, start_line, end_line):
        """Check specific line range for changes."""
        changed = set()
        try:
            for line_num in range(start_line, end_line + 1):
                if line_num <= self.last_line_count:
                    # TODO: implement sophisticated caching
                    # Currently assume lines around cursor changed
                    changed.add(line_num)
        except tk.TclError:
            pass
        return changed
    
    def _smart_change_detection(self, editor, line_count):
        """Use smart detection avoiding full content comparison."""
        # Assume reasonable change area around cursor
        cursor_line = self.last_cursor_line
        buffer_size = min(50, line_count // 4)  # Use adaptive buffer size
        
        start_line = max(1, cursor_line - buffer_size)
        end_line = min(line_count, cursor_line + buffer_size)
        
        return set(range(start_line, end_line + 1))

class MonacoStyleUpdater:
    """Monaco-inspired update system with minimal overhead."""
    
    def __init__(self):
        self.delta_trackers = weakref.WeakKeyDictionary()
        self.pending_updates = weakref.WeakKeyDictionary()
        self.update_suppressions = weakref.WeakKeyDictionary()  # Enable temporary update blocking
        
    def track_editor(self, editor):
        """Start tracking editor Monaco-style."""
        if editor not in self.delta_trackers:
            self.delta_trackers[editor] = DeltaTracker(editor)
            self.update_suppressions[editor] = 0
    
    def suppress_updates(self, editor, duration_ms=100):
        """Temporarily suppress updates like Monaco during rapid typing."""
        self.update_suppressions[editor] = time.time() + (duration_ms / 1000)
    
    def should_update(self, editor) -> bool:
        """Check if updates should proceed."""
        if editor in self.update_suppressions:
            if time.time() < self.update_suppressions[editor]:
                return False  # Updates still suppressed
        
        # Prevent duplicate pending updates
        return editor not in self.pending_updates
    
    def get_update_delta(self, editor) -> Optional[Dict]:
        """Get what needs updating - Monaco differential style."""
        if not self.should_update(editor):
            return None
            
        tracker = self.delta_trackers.get(editor)
        if not tracker:
            self.track_editor(editor)
            tracker = self.delta_trackers[editor]
            
        return tracker.get_delta()
    
    def mark_update_pending(self, editor):
        """Mark update as pending."""
        self.pending_updates[editor] = time.time()
    
    def mark_update_complete(self, editor):
        """Mark update as complete."""
        if editor in self.pending_updates:
            del self.pending_updates[editor]

class UltraFastSyntaxHighlighter:
    """Ultra-optimized syntax highlighter - Monaco inspired."""
    
    def __init__(self):
        self.token_cache = {}  # Store line-based token cache
        self.viewport_cache = weakref.WeakKeyDictionary()
        
    def highlight_delta(self, editor, delta: Dict):
        """Highlight only changed parts - core Monaco principle."""
        if not delta or delta['type'] == 'cursor_move':
            # Update current line highlighting for cursor moves
            self._highlight_cursor_line(editor, delta.get('cursor_line', 1))
            return
            
        if delta['type'] == 'content_change':
            changed_lines = delta.get('changed_lines', set())
            
            # Highlight only changed lines with small buffer
            for line_num in changed_lines:
                self._highlight_line(editor, line_num)
    
    def _highlight_cursor_line(self, editor, line_num):
        """Highlight current cursor line with ultra fast processing."""
        try:
            # Extract line content
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            line_content = editor.get(line_start, line_end)
            
            # Clear existing tags on current line only
            tags = ['command', 'section', 'math', 'comment', 'number', 'bracket']
            for tag in tags:
                try:
                    editor.tag_remove(tag, line_start, line_end)
                except tk.TclError:
                    continue
            
            # Apply quick pattern matching for essential patterns only
            if line_content.strip().startswith('%'):
                editor.tag_add('comment', line_start, line_end)
            elif '\\section' in line_content:
                self._quick_section_highlight(editor, line_content, line_start)
            elif '\\' in line_content:
                self._quick_command_highlight(editor, line_content, line_start)
                
        except tk.TclError:
            pass
    
    def _highlight_line(self, editor, line_num):
        """Highlight specific line with full patterns."""
        try:
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            line_content = editor.get(line_start, line_end)
            
            if not line_content.strip():
                return
                
            # Clear existing tags for this line
            tags = ['command', 'section', 'math', 'comment', 'number', 'bracket']
            for tag in tags:
                try:
                    editor.tag_remove(tag, line_start, line_end)
                except tk.TclError:
                    continue
            
            # Apply patterns to current line only
            import re
            patterns = {
                'comment': re.compile(r'%[^\n]*'),
                'section': re.compile(r'\\(?:sub)*section\*?'),
                'command': re.compile(r'\\[a-zA-Z@]+')
            }
            
            for pattern_name, pattern in patterns.items():
                for match in pattern.finditer(line_content):
                    start_idx = f"{line_num}.{match.start()}"
                    end_idx = f"{line_num}.{match.end()}"
                    editor.tag_add(pattern_name, start_idx, end_idx)
                    
        except tk.TclError:
            pass
    
    def _quick_section_highlight(self, editor, line_content, line_start):
        """Apply ultra-fast section highlighting."""
        try:
            import re
            section_match = re.search(r'\\(?:sub)*section\*?', line_content)
            if section_match:
                start_idx = f"{line_start}+{section_match.start()}c"
                end_idx = f"{line_start}+{section_match.end()}c"
                editor.tag_add('section', start_idx, end_idx)
        except (tk.TclError, AttributeError):
            pass
    
    def _quick_command_highlight(self, editor, line_content, line_start):
        """Apply ultra-fast command highlighting."""
        try:
            import re
            for match in re.finditer(r'\\[a-zA-Z@]+', line_content):
                start_idx = f"{line_start}+{match.start()}c"
                end_idx = f"{line_start}+{match.end()}c"
                editor.tag_add('command', start_idx, end_idx)
        except (tk.TclError, AttributeError):
            pass

# Initialize global Monaco-style instances
_monaco_updater = MonacoStyleUpdater()
_ultra_highlighter = UltraFastSyntaxHighlighter()

def initialize_monaco_optimization(editor):
    """Initialize Monaco-style optimization for editor."""
    _monaco_updater.track_editor(editor)

def apply_monaco_highlighting(editor, force=False):
    """Apply Monaco-style differential highlighting."""
    if not force:
        delta = _monaco_updater.get_update_delta(editor)
        if not delta:
            return  # Skip when no update needed
    else:
        # Create fake delta to force update
        delta = {'type': 'content_change', 'changed_lines': {1}}
    
    _monaco_updater.mark_update_pending(editor)
    
    try:
        _ultra_highlighter.highlight_delta(editor, delta)
    finally:
        _monaco_updater.mark_update_complete(editor)

def suppress_monaco_updates(editor, duration_ms=100):
    """Suppress updates during rapid typing - Monaco style."""
    _monaco_updater.suppress_updates(editor, duration_ms)