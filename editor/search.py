"""
This module implements a search functionality for the AutomaTeX editor,
inspired by VSCode's search feature with a modern, clean design.
"""

import tkinter as tk
from tkinter import ttk
import re
from typing import Optional, List, Tuple
from app import state
from utils import debug_console
from utils.icons import IconButton


class SearchEngine:
    """Handles the logic for searching text in the editor."""
    
    def __init__(self):
        self.matches: List[Tuple[str, int, int]] = []  # (line, start_pos, end_pos)
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
            debug_console.log(f"Regex error in search: {e}", level='ERROR')
            
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
        """Move to the next match and return it."""
        # Print debug info
        print(f"next_match called: matches={len(self.matches)}, current_index={self.current_match_index}")
        
        if not self.matches:
            print("No matches, returning None")
            return None
            
        # If we're at the last match, don't go further
        if self.current_match_index >= len(self.matches) - 1:
            print("At last match, returning None")
            return None
            
        self.current_match_index += 1
        result = self.get_current_match()
        print(f"Moving to index {self.current_match_index}, result={result}")
        return result
    
    def previous_match(self) -> Optional[Tuple[str, int, int]]:
        """Move to the previous match and return it."""
        if not self.matches:
            return None
            
        # If we're at the first match, don't go further
        if self.current_match_index <= 0:
            return None
            
        self.current_match_index -= 1
        return self.get_current_match()
    
    def reset(self):
        """Reset the search engine state."""
        self.matches = []
        self.current_match_index = -1


class SearchBar:
    """A modern search bar widget that appears at the top of the main window."""
    
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.search_engine = SearchEngine()
        self.is_visible = False
        
        # Create the search frame with a modern style
        self.frame = ttk.Frame(parent, padding=(10, 8))
        
        # Style configuration
        self._setup_styles()
        
        # Create UI elements
        self._create_widgets()
        
        # Bind events
        self._bind_events()
        
        # Initially hide the search bar
        self.frame.place_forget()
        
    def _setup_styles(self):
        """Setup custom styles for the search bar."""
        style = ttk.Style()
        
        # Configure frame style
        style.configure("SearchBar.TFrame",
                       background=state.get_theme_setting("bg", "#ffffff"))
        
        # Configure entry style
        style.configure("Search.TEntry", 
                       fieldbackground=state.get_theme_setting("bg", "#ffffff"),
                       foreground=state.get_theme_setting("fg", "#000000"),
                       borderwidth=1,
                       relief="solid")
        
        # Configure button style
        style.configure("Search.TButton",
                       background=state.get_theme_setting("button_bg", "#e0e0e0"),
                       foreground=state.get_theme_setting("button_fg", "#000000"),
                       borderwidth=0,
                       padding=(2, 2))
        
        # Configure label style
        style.configure("Search.TLabel",
                       background=state.get_theme_setting("bg", "#ffffff"),
                       foreground=state.get_theme_setting("fg", "#666666"))
        
        # Apply frame style
        self.frame.configure(style="SearchBar.TFrame")
        
    def _create_widgets(self):
        """Create all widgets for the search bar."""
        # Search icon label
        self.search_icon = ttk.Label(self.frame, text="🔍", 
                                    style="Search.TLabel")
        
        # Search entry with search icon
        self.search_entry = ttk.Entry(self.frame, width=30, style="Search.TEntry")
        
        # Previous match button with icon
        self.prev_button = IconButton(
            self.frame, 
            "previous",
            width=3,
            style="Search.TButton",
            command=self._previous_match
        )
        
        # Next match button with icon
        self.next_button = IconButton(
            self.frame, 
            "next",
            width=3,
            style="Search.TButton",
            command=self._next_match
        )
        
        # Match counter label
        self.counter_label = ttk.Label(
            self.frame, 
            text="0 / 0",
            style="Search.TLabel"
        )
        
        # Close button with icon
        self.close_button = IconButton(
            self.frame, 
            "close",
            width=3,
            style="Search.TButton",
            command=self.hide
        )
        
        # Case sensitive checkbox
        self.case_sensitive_var = tk.BooleanVar()
        self.case_sensitive_check = ttk.Checkbutton(
            self.frame,
            text="Aa",
            variable=self.case_sensitive_var,
            command=self._on_search_change
        )
        
        # Layout with better spacing
        self.search_icon.grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.search_entry.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        self.prev_button.grid(row=0, column=2, padx=(0, 2))
        self.next_button.grid(row=0, column=3, padx=(0, 10))
        self.counter_label.grid(row=0, column=4, padx=(0, 10))
        self.case_sensitive_check.grid(row=0, column=5, padx=(0, 5))
        self.close_button.grid(row=0, column=6)
        
        self.frame.columnconfigure(1, weight=1)
        
    def _bind_events(self):
        """Bind events to widgets."""
        self.search_entry.bind("<KeyRelease>", self._on_search_change)
        self.search_entry.bind("<Escape>", lambda e: self.hide())
        self.search_entry.bind("<Return>", lambda e: (self._next_match(), "break"))
        self.search_entry.bind("<Shift-Return>", lambda e: (self._previous_match(), "break"))
        
        # Bind focus events for visual feedback
        self.search_entry.bind("<FocusIn>", self._on_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_focus_out)
        
    def _on_focus_in(self, event=None):
        """Handle focus in event."""
        style = ttk.Style()
        style.configure("Search.TEntry", 
                       fieldbackground=state.get_theme_setting("bg", "#ffffff"),
                       foreground=state.get_theme_setting("fg", "#000000"),
                       bordercolor=state.get_theme_setting("accent", "#0078d4"))
        
    def _on_focus_out(self, event=None):
        """Handle focus out event."""
        style = ttk.Style()
        style.configure("Search.TEntry", 
                       fieldbackground=state.get_theme_setting("bg", "#ffffff"),
                       foreground=state.get_theme_setting("fg", "#000000"),
                       bordercolor="#cccccc")
        
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
        
        # Update counter
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
            
        # Configure the highlight tag
        editor.tag_configure(
            "search_match",
            background=state.get_theme_setting("search_match_bg", "#ffff00"),
            foreground=state.get_theme_setting("search_match_fg", "#000000")
        )
        
        # Highlight current match differently
        editor.tag_configure(
            "current_search_match",
            background=state.get_theme_setting("current_search_match_bg", "#ff9900"),
            foreground=state.get_theme_setting("current_search_match_fg", "#ffffff")
        )
        
    def _clear_highlights(self, editor: tk.Text):
        """Clear all search highlights."""
        editor.tag_remove("search_match", "1.0", "end")
        editor.tag_remove("current_search_match", "1.0", "end")
        
    def _update_counter(self):
        """Update the match counter label."""
        total = self.search_engine.get_total_matches()
        current = self.search_engine.get_current_match_number()
        self.counter_label.config(text=f"{current} / {total}")
        
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
        
        # Scroll to the match
        current_tab.editor.see(pos)
        current_tab.editor.mark_set("insert", pos)
        # Ne pas donner le focus à l'éditeur pour garder le focus sur la barre de recherche
        
        # Simple animation for the current match
        self._animate_match_highlight(current_tab.editor, start_pos, end_pos)
        
        # Update counter
        self._update_counter()
        
        # Maintenir le focus sur la barre de recherche
        self.search_entry.focus()
        
    def _animate_match_highlight(self, editor, start_pos, end_pos):
        """Simple animation for highlighting the current match."""
        # This is a placeholder for a simple animation
        # We could implement a brief highlight effect here if desired
        pass
        
    def _next_match(self):
        """Navigate to the next match."""
        print("_next_match called")
        match = self.search_engine.next_match()
        if match:
            print("Got match, going to current match")
            self._go_to_current_match()
        else:
            print("No match, flashing counter")
            # No more matches or no matches at all
            self._flash_counter()
            
    def _previous_match(self):
        """Navigate to the previous match."""
        match = self.search_engine.previous_match()
        if match:
            self._go_to_current_match()
        else:
            # No more matches or no matches at all
            self._flash_counter()
            
    def _flash_counter(self):
        """Provide visual feedback by flashing the counter label."""
        # Store original color
        original_fg = self.counter_label.cget("foreground")
        
        # Flash to red and back
        self.counter_label.config(foreground="red")
        self.counter_label.after(100, lambda: self.counter_label.config(foreground=original_fg))
            
    def show(self):
        """Show the search bar with a smooth animation."""
        if self.is_visible:
            self.search_entry.focus()
            return
            
        # Position the search bar at the top of the parent
        self.frame.place(relx=0.5, rely=0.02, anchor="n", relwidth=0.5)
        
        # Add a subtle fade-in effect
        self.frame.winfo_toplevel().after(10, lambda: self.search_entry.focus())
        self.is_visible = True
        
        # Simple slide-down animation
        self._animate_show()
        
        # Pre-fill with selected text if any
        current_tab = state.get_current_tab()
        if current_tab and current_tab.editor:
            try:
                selected_text = current_tab.editor.selection_get()
                if selected_text:
                    self.search_entry.delete(0, "end")
                    self.search_entry.insert(0, selected_text)
                    self._on_search_change()
            except tk.TclError:
                # No text selected
                pass
                
    def _animate_show(self):
        """Simple slide-down animation for showing the search bar."""
        # We'll implement a simple animation by moving the frame down
        start_y = -self.frame.winfo_reqheight()
        end_y = 0.02 * self.parent.winfo_height()
        steps = 10
        duration = 100  # ms
        
        step_delay = duration // steps
        y_step = (end_y - start_y) // steps
        
        def animate_step(step):
            if step <= steps:
                y_pos = start_y + (y_step * step)
                relative_y = y_pos / self.parent.winfo_height()
                self.frame.place(relx=0.5, rely=relative_y, anchor="n", relwidth=0.5)
                self.frame.after(step_delay, lambda: animate_step(step + 1))
            else:
                # Final position
                self.frame.place(relx=0.5, rely=0.02, anchor="n", relwidth=0.5)
                
        # Start animation
        self.frame.place(relx=0.5, rely=start_y/self.parent.winfo_height(), anchor="n", relwidth=0.5)
        animate_step(1)
                
    def hide(self):
        """Hide the search bar and clear highlights."""
        # Simple slide-up animation
        self._animate_hide()
        # Perform the actual hide after a short delay to allow animation to complete
        self.frame.after(100, self._perform_hide)
            
    def _perform_hide(self):
        """Actually hide the search bar."""
        self.frame.place_forget()
        self.is_visible = False
        
        # Clear highlights
        current_tab = state.get_current_tab()
        if current_tab and current_tab.editor:
            self._clear_highlights(current_tab.editor)
            
        # Reset search engine
        self.search_engine.reset()
        
        # Clear entry
        self.search_entry.delete(0, "end")
        self.counter_label.config(text="0 / 0")
        
        # Focus back to editor
        if current_tab and current_tab.editor:
            current_tab.editor.focus()
            
    def _animate_hide(self):
        """Simple slide-up animation for hiding the search bar."""
        # We'll implement a simple animation by moving the frame up
        start_y = 0.02 * self.parent.winfo_height()
        end_y = -self.frame.winfo_reqheight()
        steps = 10
        duration = 100  # ms
        
        step_delay = duration // steps
        y_step = (end_y - start_y) // steps
        
        def animate_step(step):
            if step <= steps:
                y_pos = start_y + (y_step * step)
                relative_y = y_pos / self.parent.winfo_height()
                self.frame.place(relx=0.5, rely=relative_y, anchor="n", relwidth=0.5)
                self.frame.after(step_delay, lambda: animate_step(step + 1))
            else:
                # Final position (hidden)
                self.frame.place_forget()
                
        # Start animation
        animate_step(1)


# Global search bar instance
_search_bar: Optional[SearchBar] = None


def initialize_search_bar(root: tk.Tk):
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