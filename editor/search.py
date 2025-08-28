"""
Search functionality for AutomaTeX editor.
Clean, VSCode-style search bar with replace and undo.
"""

import tkinter as tk
import ttkbootstrap as ttk
import re
from typing import Optional, List, Tuple
from app import state
from utils import logs_console
from utils.icons import IconButton

# Animation constants
ANIMATION_FPS = 60
ENTRY_DURATION = 120  # ms 
EXIT_DURATION = 100   # ms
BAR_OFFSET_X = -35    # pixels from right edge


class SearchEngine:
    """Handle logic for searching text in editor."""
    
    def __init__(self):
        self.matches: List[Tuple[str, int, int]] = []  # Store (line, start_pos, end_pos)
        self.current_match_index = -1
        self.editor_widget = None
        
    def search(self, text_widget: tk.Text, search_term: str, case_sensitive: bool = True) -> List[Tuple[str, int, int]]:
        """
        Search for a term in the text widget and return all matches.
        
        Args:
            text_widget: The text widget to search in
            search_term: The term to search for
            case_sensitive: Whether the search should be case sensitive (default True)
            
        Returns:
            List of tuples (line_number, start_position, end_position)
        """
        self.matches = []
        self.current_match_index = -1
        self.editor_widget = text_widget
        
        if not search_term:
            return self.matches
            
        try:
            content = text_widget.get("1.0", "end-1c")
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.escape(search_term)
            
            for match in re.finditer(pattern, content, flags):
                start_pos = match.start()
                end_pos = match.end()
                
                # Convert flat position to line and column
                start_line = content[:start_pos].count('\n') + 1
                end_line = content[:end_pos].count('\n') + 1
                
                # Calculate column positions
                start_line_start = content.rfind('\n', 0, start_pos) + 1
                start_col = start_pos - start_line_start
                
                end_line_start = content.rfind('\n', 0, end_pos) + 1
                end_col = end_pos - end_line_start
                
                self.matches.append((str(start_line), start_col, end_col))
            
            # Find closest match to current cursor position
            if self.matches:
                self._find_closest_match()
                
        except re.error as e:
            logs_console.log(f"Search pattern error: {e}", level='WARNING')
            
        return self.matches
    
    def _find_closest_match(self):
        """Find the closest match to current cursor position (looking down first)."""
        if not self.editor_widget or not self.matches:
            return
            
        try:
            # Get current cursor position
            cursor_pos = self.editor_widget.index(tk.INSERT)
            cursor_line, cursor_col = map(int, cursor_pos.split('.'))
            
            # Find first match at or after cursor position
            closest_index = -1
            
            for i, (line, start_col, end_col) in enumerate(self.matches):
                match_line = int(line)
                
                # Match is after current line
                if match_line > cursor_line:
                    closest_index = i
                    break
                # Match is on current line and at or after cursor column
                elif match_line == cursor_line and start_col >= cursor_col:
                    closest_index = i
                    break
            
            # If no match found after cursor, use first match (wrap around)
            if closest_index == -1:
                closest_index = 0
                
            self.current_match_index = closest_index
            
        except (tk.TclError, ValueError):
            # Fallback to first match if cursor position can't be determined
            self.current_match_index = 0
    
    def get_current_match(self) -> Optional[Tuple[str, int, int]]:
        """Get the current match based on the current index."""
        if not self.matches or self.current_match_index < 0:
            return None
        return self.matches[self.current_match_index]
    
    def get_total_matches(self) -> int:
        """Get the total number of matches."""
        return len(self.matches)
    
    def get_current_match_number(self) -> int:
        """Get the current match number (1-indexed)."""
        if self.current_match_index >= 0:
            return self.current_match_index + 1
        return 0
    
    def next_match(self) -> Optional[Tuple[str, int, int]]:
        """Move to the next match and return it (with cycling)."""
        if not self.matches:
            return None
            
        # If we're at the last match, cycle to first
        if self.current_match_index >= len(self.matches) - 1:
            self.current_match_index = 0
        else:
            self.current_match_index += 1
            
        return self.get_current_match()
    
    def previous_match(self) -> Optional[Tuple[str, int, int]]:
        """Move to the previous match and return it (with cycling)."""
        if not self.matches:
            return None
            
        # If we're at the first match, cycle to last
        if self.current_match_index <= 0:
            self.current_match_index = len(self.matches) - 1
        else:
            self.current_match_index -= 1
            
        return self.get_current_match()
    
    def reset(self):
        """Reset the search engine state."""
        self.matches = []
        self.current_match_index = -1


class SearchBar:
    """A modern search bar widget positioned over the editor."""
    
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.search_engine = SearchEngine()
        self.is_visible = False
        self.current_tab = None
        
        # Create the search frame (initially without parent)
        self.frame = None
        
        
    def _create_widgets(self):
        """Create all widgets for the search bar exactly like VSCode."""
        # Clean frame adapted to theme
        self.frame.configure(
            padding=3,
            relief="solid",
            borderwidth=1
        )
        
        # Search entry with clean styling
        self.search_entry = ttk.Entry(
            self.frame,
            width=18,
            font=("Segoe UI", 9)
        )
        
        # Previous match button (up arrow)
        self.prev_button = IconButton(
            self.frame,
            "up", 
            bootstyle="secondary-outline",
            command=self._previous_match
        )
        
        # Next match button (down arrow) 
        self.next_button = IconButton(
            self.frame,
            "down",
            bootstyle="secondary-outline", 
            command=self._next_match
        )
        
        # Match counter with minimal styling
        self.counter_label = ttk.Label(
            self.frame,
            text="",
            font=("Segoe UI", 8),
            width=5,
            anchor="center"
        )
        
        # Case sensitive toggle button
        self.case_sensitive_var = tk.BooleanVar()
        self.case_sensitive_check = ttk.Checkbutton(
            self.frame,
            text="Aa",
            variable=self.case_sensitive_var,
            bootstyle="secondary-toolbutton",
            command=self._update_search
        )
        
        # Replace toggle button (at left like VSCode)
        self.show_replace = False
        self.replace_toggle = IconButton(
            self.frame,
            "expand",
            bootstyle="secondary-toolbutton",
            command=self._toggle_replace
        )
        
        # Close button
        self.close_button = IconButton(
            self.frame,
            "close",
            bootstyle="secondary-outline",
            command=self.hide
        )
        
        # VSCode layout: [⌄] [search] [↑] [↓] [1/5] [Aa] [×]
        self.replace_toggle.grid(row=0, column=0, padx=(0, 2))
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 4))
        self.prev_button.grid(row=0, column=2, padx=0)
        self.next_button.grid(row=0, column=3, padx=(0, 4))
        self.counter_label.grid(row=0, column=4, padx=(0, 4))
        self.case_sensitive_check.grid(row=0, column=5, padx=(0, 4))
        self.close_button.grid(row=0, column=6)
        
        self.frame.columnconfigure(1, weight=1)
        
        # Replace row (initially hidden)
        self._create_replace_widgets()
        
        # Bind events after all widgets are created
        self._bind_replace_events()
        
    def _create_replace_widgets(self):
        """Create replace widgets (VSCode style)."""
        # Replace entry
        self.replace_entry = ttk.Entry(
            self.frame,
            width=18,
            font=("Segoe UI", 9)
        )
        
        # Replace current button
        self.replace_current_button = IconButton(
            self.frame,
            "replace",
            bootstyle="secondary-outline",
            command=self._replace_current
        )
        
        # Replace all button  
        self.replace_all_button = ttk.Button(
            self.frame,
            text="All",
            bootstyle="secondary-outline",
            width=3,
            command=self._replace_all
        )
        
        # Undo button (initially hidden)
        self.undo_button = ttk.Button(
            self.frame,
            text="↶",
            bootstyle="secondary-outline",
            width=3,
            command=self._undo_replace
        )
        self.undo_available = False
        
        # Hide replace row initially
        self._hide_replace()
        
    def _toggle_replace(self):
        """Toggle replace section visibility."""
        self.show_replace = not self.show_replace
        if self.show_replace:
            self._show_replace()
        else:
            self._hide_replace()
    
    def _show_replace(self):
        """Show replace widgets in row 1."""
        # Align with search entry (skip toggle column)
        self.replace_entry.grid(row=1, column=1, sticky="ew", padx=(0, 4), pady=(2, 0))
        self.replace_current_button.grid(row=1, column=2, padx=0, pady=(2, 0))
        self.replace_all_button.grid(row=1, column=3, padx=(0, 2), pady=(2, 0))
        
        # Show undo button if available
        if self.undo_available:
            self.undo_button.grid(row=1, column=4, padx=(0, 4), pady=(2, 0))
        
    def _hide_replace(self):
        """Hide replace widgets."""
        try:
            self.replace_entry.grid_remove()
            self.replace_current_button.grid_remove() 
            self.replace_all_button.grid_remove()
            self.undo_button.grid_remove()
        except AttributeError:
            pass  # Widgets not created yet
            
    def _replace_current(self):
        """Replace current match with replacement text."""
        if not hasattr(self, 'replace_entry'):
            return
            
        current_tab = state.get_current_tab()
        if not current_tab or not current_tab.editor:
            return
            
        # Get current match
        current_match = self.search_engine.get_current_match()
        if not current_match:
            return
            
        # Get replacement text
        replacement_text = self.replace_entry.get()
        
        # Replace current match
        line, start_col, end_col = current_match
        start_pos = f"{line}.{start_col}"
        end_pos = f"{line}.{end_col}"
        
        # Mark undo separator before replace
        current_tab.editor.edit_separator()
        
        # Replace text in editor
        current_tab.editor.delete(start_pos, end_pos)
        current_tab.editor.insert(start_pos, replacement_text)
        
        # Mark that undo is available
        self._mark_undo_available()
        
        # Update search to find next match
        self._refresh_search_after_replace()
        
    def _replace_all(self):
        """Replace all matches with replacement text."""
        if not hasattr(self, 'replace_entry'):
            return
            
        current_tab = state.get_current_tab()
        if not current_tab or not current_tab.editor:
            return
            
        search_term = self.search_entry.get()
        replacement_text = self.replace_entry.get()
        
        if not search_term:
            return
            
        # Get all matches
        matches = self.search_engine.matches
        if not matches:
            return
            
        # Mark undo separator before replace all
        current_tab.editor.edit_separator()
        
        # Replace all matches from end to beginning to maintain positions
        for line, start_col, end_col in reversed(matches):
            start_pos = f"{line}.{start_col}"
            end_pos = f"{line}.{end_col}"
            
            # Replace text in editor
            current_tab.editor.delete(start_pos, end_pos)
            current_tab.editor.insert(start_pos, replacement_text)
        
        # Mark that undo is available
        self._mark_undo_available()
        
        # Refresh search to show no matches
        self._refresh_search_after_replace()
        
    def _undo_replace(self):
        """Undo the last replace operation."""
        current_tab = state.get_current_tab()
        if not current_tab or not current_tab.editor:
            return
            
        try:
            current_tab.editor.edit_undo()
            # Refresh search after undo
            self._update_search()
        except tk.TclError:
            pass  # Nothing to undo
    
    def _mark_undo_available(self):
        """Mark that undo is available and update UI."""
        self.undo_available = True
        if self.show_replace and hasattr(self, 'undo_button'):
            self.undo_button.grid(row=1, column=4, padx=(0, 4), pady=(2, 0))
        
    def _refresh_search_after_replace(self):
        """Refresh search results after replacement."""
        # Re-run search to update matches
        self._update_search()
        
        # Move to next match if available
        if self.search_engine.matches:
            if self.search_engine.current_match_index >= len(self.search_engine.matches):
                self.search_engine.current_match_index = 0
            self._go_to_current_match()
        
    def _bind_events(self):
        """Bind events to widgets."""
        # Use StringVar to track text changes only
        self.search_text_var = tk.StringVar()
        self.search_entry.config(textvariable=self.search_text_var)
        self.search_text_var.trace('w', lambda *args: self._update_search())
        
        self.search_entry.bind("<Escape>", lambda e: self.hide())
        self.search_entry.bind("<Return>", lambda e: (self._next_match(), "break"))
        self.search_entry.bind("<Shift-Return>", lambda e: (self._previous_match(), "break"))
        
    def _bind_replace_events(self):
        """Bind events to replace widgets."""
        if hasattr(self, 'replace_entry'):
            self.replace_entry.bind("<Return>", lambda e: (self._replace_current(), "break"))
            self.replace_entry.bind("<Escape>", lambda e: self.hide())
        
        
    def _update_search(self):
        """Update search results when text changes."""
        search_term = self.search_text_var.get()
        case_sensitive = self.case_sensitive_var.get()
        
        current_tab = state.get_current_tab()
        if not current_tab or not current_tab.editor:
            return
            
        # Clear previous highlights
        self._clear_highlights(current_tab.editor)
        
        # Perform search
        matches = self.search_engine.search(
            current_tab.editor, 
            search_term, 
            case_sensitive
        )
        
        # Update counter if frame exists
        if self.frame:
            self._update_counter()
        
        # Highlight matches
        if matches:
            self._highlight_matches(current_tab.editor, matches)
            # Go to the closest match immediately
            self._go_to_current_match()
        else:
            # No matches found
            self.search_engine.current_match_index = -1
            
    def _highlight_matches(self, editor: tk.Text, matches: List[Tuple[str, int, int]]):
        """Highlight all matches in the editor."""
        for line, start_col, end_col in matches:
            start_pos = f"{line}.{start_col}"
            end_pos = f"{line}.{end_col}"
            editor.tag_add("search_match", start_pos, end_pos)
            
        # Configure the highlight tags with theme-adapted colors
        editor.tag_configure(
            "search_match",
            background=state.get_theme_setting("search_match_bg", "#4a4a00"),
            foreground=state.get_theme_setting("search_match_fg", "#ffffff")
        )
        
        # Highlight current match with theme orange
        editor.tag_configure(
            "current_search_match", 
            background=state.get_theme_setting("current_search_match_bg", "#ff6600"),
            foreground=state.get_theme_setting("current_search_match_fg", "#000000")
        )
        
    def _clear_highlights(self, editor: tk.Text):
        """Clear all search highlights."""
        editor.tag_remove("search_match", "1.0", "end")
        editor.tag_remove("current_search_match", "1.0", "end")
        
    def _update_counter(self):
        """Update the match counter label with short text."""
        if not self.frame or not hasattr(self, 'counter_label'):
            return
        total = self.search_engine.get_total_matches()
        current = self.search_engine.get_current_match_number()
        
        if total == 0:
            self.counter_label.config(text="")
        elif current > 0:
            self.counter_label.config(text=f"{current}/{total}")
        else:
            self.counter_label.config(text=f"{total}")
        
    def _go_to_current_match(self):
        """Scroll to and highlight the current match."""
        current_tab = state.get_current_tab()
        if not current_tab or not current_tab.editor:
            return
            
        match = self.search_engine.get_current_match()
        if not match:
            return
            
        line, start_col, end_col = match
        pos = f"{line}.{start_col}"
        
        # Remove previous current match highlight
        current_tab.editor.tag_remove("current_search_match", "1.0", "end")
        
        # Add current match highlight
        start_pos = f"{line}.{start_col}"
        end_pos = f"{line}.{end_col}"
        current_tab.editor.tag_add("current_search_match", start_pos, end_pos)
        
        # Scroll to the match and select it entirely (VSCode behavior)
        current_tab.editor.see(pos)
        current_tab.editor.mark_set("insert", start_pos)
        current_tab.editor.tag_remove("sel", "1.0", "end")
        current_tab.editor.tag_add("sel", start_pos, end_pos)
        current_tab.editor.mark_set("sel.first", start_pos)
        current_tab.editor.mark_set("sel.last", end_pos)
        
        # Update counter if frame exists
        if self.frame:
            self._update_counter()
        
        # Maintenir le focus sur la barre de recherche
        if self.frame and hasattr(self, 'search_entry'):
            self.search_entry.focus()
        
        
    def _next_match(self):
        """Navigate to the next match (with cycling)."""
        if not self.search_engine.matches:
            return
            
        match = self.search_engine.next_match()
        if match:
            self._go_to_current_match()
            
    def _previous_match(self):
        """Navigate to the previous match (with cycling)."""
        if not self.search_engine.matches:
            return
            
        match = self.search_engine.previous_match()
        if match:
            self._go_to_current_match()
            
    def _flash_counter(self):
        """Provide visual feedback by flashing the counter label."""
        if not self.frame or not hasattr(self, 'counter_label'):
            return
        # Store original color
        original_fg = self.counter_label.cget("foreground")
        
        # Flash to red and back
        self.counter_label.config(foreground="red")
        self.counter_label.after(100, lambda: self.counter_label.config(foreground=original_fg) if hasattr(self, 'counter_label') else None)
            
    def show(self):
        """Show the search bar positioned over the active editor."""
        # Get current active tab/editor
        current_tab = state.get_current_tab()
        if not current_tab or not current_tab.editor:
            return
            
        # If already visible in the same tab, just focus
        if self.is_visible and self.current_tab == current_tab:
            self.search_entry.focus()
            return
            
        # Hide if visible in another tab
        if self.is_visible:
            self.hide()
            
        # Create frame in the current editor tab
        self.current_tab = current_tab
        self.frame = ttk.Frame(current_tab)
        self._create_widgets()
        self._bind_events()
        
        # Start entry animation
        self._animate_entry()
            
        self.is_visible = True
        self.search_entry.focus()
        
        # Pre-fill with selected text if any
        try:
            selected_text = current_tab.editor.selection_get()
            if selected_text:
                self.search_text_var.set(selected_text)
        except tk.TclError:
            pass
                
                
    def hide(self):
        """Hide the search bar with slide-up animation."""
        if not self.is_visible or not self.frame:
            return
            
        # Start exit animation
        self._animate_exit()
        
    def _finish_hide(self):
        """Complete the hiding process after animation."""
        if not self.frame:
            return
            
        self.frame.place_forget()
        self.frame.destroy()
        self.frame = None
        self.is_visible = False
        
        # Clear highlights
        if self.current_tab and self.current_tab.editor:
            self._clear_highlights(self.current_tab.editor)
            
        # Reset search engine
        self.search_engine.reset()
        
        # Focus back to editor and maintain selection if exists
        if self.current_tab and self.current_tab.editor:
            self.current_tab.editor.focus()
            
        self.current_tab = None
        
    def _animate_entry(self):
        """Animate search bar sliding down."""
        self._animate_slide(-30, 10, ENTRY_DURATION)
        
    def _animate_exit(self):
        """Animate search bar sliding up."""
        self._animate_slide(10, -30, EXIT_DURATION, self._finish_hide)
        
    def _animate_slide(self, start_y, end_y, duration, callback=None):
        """Generic slide animation."""
        step_delay = 1000 // ANIMATION_FPS
        steps = duration // step_delay
        y_increment = (end_y - start_y) / steps
        
        def animate_step(step):
            if step <= steps and self.frame:
                current_y = start_y + (y_increment * step)
                self.frame.place(relx=1.0, rely=0.0, anchor="ne", x=BAR_OFFSET_X, y=int(current_y))
                
                if step < steps:
                    self.frame.after(step_delay, lambda: animate_step(step + 1))
                else:
                    if callback:
                        callback()
            
        animate_step(1)
            


# Global search bar instance
_search_bar: Optional[SearchBar] = None


def initialize_search_bar(root: tk.Widget):
    """Initialize the global search bar instance."""
    global _search_bar
    if _search_bar is None:
        _search_bar = SearchBar(root)
        
        
def show_search_bar():
    """Show the search bar."""
    if _search_bar:
        _search_bar.show()
        
        
def hide_search_bar():
    """Hide the search bar."""
    if _search_bar:
        _search_bar.hide()