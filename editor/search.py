"""
Implement search functionality for AutomaTeX editor.
Modern, integrated search bar with clean design.
"""

import tkinter as tk
import ttkbootstrap as ttk
import re
from typing import Optional, List, Tuple
from app import state
from utils import logs_console
from utils.icons import IconButton


class SearchEngine:
    """Handle logic for searching text in editor."""
    
    def __init__(self):
        self.matches: List[Tuple[str, int, int]] = []  # Store (line, start_pos, end_pos)
        self.current_match_index = -1
        
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
                
        except re.error as e:
            logs_console.log(f"Regex error in search: {e}", level='ERROR')
            
        return self.matches
    
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
        # Compact frame adapted to theme
        self.frame.configure(
            bootstyle="secondary",
            padding=2,
            relief="solid",
            borderwidth=1
        )
        
        # Create search container with icon
        self.search_container = ttk.Frame(self.frame, bootstyle="secondary")
        
        # Search icon inside entry
        self.search_icon = IconButton(
            self.search_container,
            "search",
            bootstyle="secondary-link",
            command=lambda: self.search_entry.focus()
        )
        
        # Search entry with compact styling
        self.search_entry = ttk.Entry(
            self.search_container,
            width=16,
            bootstyle="secondary",
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
        
        # Match counter with compact styling
        self.counter_label = ttk.Label(
            self.frame,
            text="No results",
            bootstyle="secondary",
            font=("Segoe UI", 8),
            width=7,
            anchor="center"
        )
        
        # Case sensitive toggle button
        self.case_sensitive_var = tk.BooleanVar()
        self.case_sensitive_check = ttk.Checkbutton(
            self.frame,
            text="Aa",
            variable=self.case_sensitive_var,
            bootstyle="secondary-toolbutton",
            command=self._on_search_change
        )
        
        # Close button
        self.close_button = IconButton(
            self.frame,
            "close",
            bootstyle="secondary-outline",
            command=self.hide
        )
        
        
        # Compact layout: [🔍search] [↑] [↓] [count] [Aa] [×]
        self.search_icon.pack(side="left", padx=(2, 0))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        self.search_container.grid(row=0, column=0, sticky="ew", padx=(0, 1))
        self.prev_button.grid(row=0, column=1, padx=0)
        self.next_button.grid(row=0, column=2, padx=(0, 2))
        self.counter_label.grid(row=0, column=3, padx=(0, 2))
        self.case_sensitive_check.grid(row=0, column=4, padx=(0, 2))
        self.close_button.grid(row=0, column=5)
        
        self.frame.columnconfigure(0, weight=1)
        
    def _bind_events(self):
        """Bind events to widgets."""
        self.search_entry.bind("<KeyRelease>", self._on_search_change)
        self.search_entry.bind("<Escape>", lambda e: self.hide())
        self.search_entry.bind("<Return>", lambda e: (self._next_match(), "break"))
        self.search_entry.bind("<Shift-Return>", lambda e: (self._previous_match(), "break"))
        
        
        
    def _on_search_change(self, event=None):
        """Handle search term changes."""
        # Ignore Enter and Shift key releases to avoid resetting the search
        if event and event.keysym in ("Return", "Shift_L", "Shift_R"):
            return

        print("_on_search_change called")
        search_term = self.search_entry.get()
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
            # Set index to -1 to indicate we're at the start but haven't navigated yet
            self.search_engine.current_match_index = -1
        else:
            # No matches found
            self.search_engine.current_match_index = -1
            
    def _highlight_matches(self, editor: tk.Text, matches: List[Tuple[str, int, int]]):
        """Highlight all matches in the editor."""
        for line, start_col, end_col in matches:
            start_pos = f"{line}.{start_col}"
            end_pos = f"{line}.{end_col}"
            editor.tag_add("search_match", start_pos, end_pos)
            
        # Configure the highlight tags with VSCode colors
        editor.tag_configure(
            "search_match",
            background="#613315",  # VSCode match background (brownish)
            foreground="#ffffff"   # White text for contrast
        )
        
        # Highlight current match with VSCode orange
        editor.tag_configure(
            "current_search_match", 
            background="#ff6600",  # VSCode current match orange
            foreground="#000000"   # Black text on orange
        )
        
    def _clear_highlights(self, editor: tk.Text):
        """Clear all search highlights."""
        editor.tag_remove("search_match", "1.0", "end")
        editor.tag_remove("current_search_match", "1.0", "end")
        
    def _update_counter(self):
        """Update the match counter label VSCode-style."""
        if not self.frame or not hasattr(self, 'counter_label'):
            return
        total = self.search_engine.get_total_matches()
        current = self.search_engine.get_current_match_number()
        
        if total == 0:
            self.counter_label.config(text="No results")
        elif current > 0:
            self.counter_label.config(text=f"{current} of {total}")
        else:
            self.counter_label.config(text=f"{total} results")
        
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
        
        # Position in top-right corner of the editor
        self.frame.place(relx=1.0, rely=0.0, anchor="ne", x=-15, y=10)
            
        self.is_visible = True
        self.search_entry.focus()
        
        # Pre-fill with selected text if any
        try:
            selected_text = current_tab.editor.selection_get()
            if selected_text:
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, selected_text)
                self._on_search_change()
        except tk.TclError:
            pass
                
                
    def hide(self):
        """Hide the search bar and clear highlights."""
        if not self.is_visible or not self.frame:
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
            # VSCode behavior: keep the current match selected when closing search
            
        self.current_tab = None
            


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