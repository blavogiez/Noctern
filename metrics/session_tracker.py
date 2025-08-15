"""Track file-based productivity metrics for editing sessions."""

import time
import json
import os
from datetime import datetime
from pathlib import Path


class SessionTracker:
    """Track session metrics for specific file."""
    
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.session_start_time = time.time()
        self.current_session_id = datetime.now().isoformat()
        self.initial_word_count = 0
        self.current_word_count = 0
        self._cache_dir = None
        
        if file_path:
            self.set_file_path(file_path)
    
    def set_file_path(self, file_path):
        """Set or change file being tracked."""
        self.file_path = file_path
        self._cache_dir = self._get_cache_directory()
        self._ensure_cache_directory()
        
        # Reset session for new file
        self.session_start_time = time.time()
        self.current_session_id = datetime.now().isoformat()
        self.initial_word_count = 0
        self.current_word_count = 0
    
    def _get_cache_directory(self):
        """Get cache directory path for current file."""
        if not self.file_path:
            return None
        
        file_dir = os.path.dirname(self.file_path)
        file_name = os.path.splitext(os.path.basename(self.file_path))[0]
        return os.path.join(file_dir, f"{file_name}.cache")
    
    def _ensure_cache_directory(self):
        """Ensure cache directory exists."""
        if self._cache_dir and not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir, exist_ok=True)
    
    def _get_metrics_file_path(self):
        """Get path to metrics file."""
        if not self._cache_dir:
            return None
        return os.path.join(self._cache_dir, "session_metrics.json")
    
    def load_existing_metrics(self):
        """Load existing metrics for file."""
        metrics_file = self._get_metrics_file_path()
        if not metrics_file or not os.path.exists(metrics_file):
            return {"sessions": []}
        
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"sessions": []}
    
    def save_session_metrics(self):
        """Save current session metrics to cache file."""
        if not self._cache_dir:
            return
        
        metrics_file = self._get_metrics_file_path()
        existing_metrics = self.load_existing_metrics()
        
        # Calculate session data
        session_duration = time.time() - self.session_start_time
        words_typed = max(0, self.current_word_count - self.initial_word_count)
        
        session_data = {
            "session_id": self.current_session_id,
            "start_time": self.session_start_time,
            "duration_seconds": session_duration,
            "words_typed": words_typed,
            "initial_word_count": self.initial_word_count,
            "final_word_count": self.current_word_count,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "productivity_score": self._calculate_productivity_score(words_typed, session_duration)
        }
        
        existing_metrics["sessions"].append(session_data)
        
        try:
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(existing_metrics, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving session metrics: {e}")
    
    def _calculate_productivity_score(self, words_typed, duration_seconds):
        """Calculate productivity score based on words per minute."""
        if duration_seconds <= 0:
            return 0
        
        duration_minutes = duration_seconds / 60
        return words_typed / duration_minutes if duration_minutes > 0 else 0
    
    def update_word_count(self, word_count):
        """Update current word count."""
        if self.initial_word_count == 0:
            self.initial_word_count = word_count
        self.current_word_count = word_count
    
    def get_session_time(self):
        """Get current session time in seconds."""
        return time.time() - self.session_start_time
    
    def get_words_typed_this_session(self):
        """Get number of words typed in current session."""
        return max(0, self.current_word_count - self.initial_word_count)
    
    def get_session_summary(self):
        """Get summary of current session."""
        duration = self.get_session_time()
        words_typed = self.get_words_typed_this_session()
        
        return {
            "duration_seconds": duration,
            "duration_formatted": self._format_duration(duration),
            "words_typed": words_typed,
            "productivity_score": self._calculate_productivity_score(words_typed, duration)
        }
    
    def _format_duration(self, seconds):
        """Format duration in human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def get_historical_metrics(self):
        """Get all historical metrics for file."""
        return self.load_existing_metrics()
    
    def get_daily_summary(self, date_str=None):
        """Get summary metrics for specific date."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        metrics = self.load_existing_metrics()
        daily_sessions = [s for s in metrics.get("sessions", []) if s.get("date") == date_str]
        
        if not daily_sessions:
            return {
                "date": date_str,
                "total_duration": 0,
                "total_words": 0,
                "session_count": 0,
                "avg_productivity": 0
            }
        
        total_duration = sum(s.get("duration_seconds", 0) for s in daily_sessions)
        total_words = sum(s.get("words_typed", 0) for s in daily_sessions)
        avg_productivity = sum(s.get("productivity_score", 0) for s in daily_sessions) / len(daily_sessions)
        
        return {
            "date": date_str,
            "total_duration": total_duration,
            "total_words": total_words,
            "session_count": len(daily_sessions),
            "avg_productivity": avg_productivity
        }