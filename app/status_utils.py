"""
This module provides utility functions for updating the status bar with
file information and word count.
"""

from app import state
from editor import wordcount as editor_wordcount

def update_status_bar_text():
    """
    Updates the status bar text with cached word count for better performance.
    """
    # Check if status bar exists
    if not state.status_label:
        return
        
    current_tab = state.get_current_tab()
    if current_tab:
        # Try to use performance optimizer cache
        try:
            from app.performance_optimizer import _performance_optimizer
            
            # Get content and check cache
            content = current_tab.editor.get("1.0", "end")
            content_hash = _performance_optimizer.content_cache.get_content_hash(content)
            cached_word_count = _performance_optimizer.content_cache.get_cached_wordcount(content_hash)
            
            if cached_word_count is not None:
                # Use cached word count
                word_count_text = f"{cached_word_count} words"
            else:
                # Calculate and cache word count
                word_count = editor_wordcount.update_word_count(current_tab.editor, state.status_label)
                _performance_optimizer.content_cache.cache_wordcount(content_hash, word_count)
                word_count_text = f"{word_count} words"
            
        except ImportError:
            # Fallback to original implementation
            word_count = editor_wordcount.update_word_count(current_tab.editor, state.status_label)
            word_count_text = f"{word_count} words"
        
        # Show file path if available
        if current_tab.file_path:
            state.status_label.config(text=f"{current_tab.file_path} | {word_count_text}")
        else:
            state.status_label.config(text=f"Untitled | {word_count_text}")
    else:
        state.status_label.config(text="...")