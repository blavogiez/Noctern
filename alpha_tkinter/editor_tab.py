# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\editor_tab.py
import tkinter as tk
import editor_logic
from tkinter import ttk, messagebox
from tkinter.font import Font
import os

class LineNumbers(tk.Canvas):
    """A Canvas widget to display line numbers for a Text editor widget."""
    def __init__(self, master, editor_widget, font, **kwargs):
        super().__init__(master, **kwargs)
        self.editor = editor_widget
        self.font = font
        self.text_color = "#6a737d" # Default color, will be overridden by theme
        self.text_color_current = "#d4d4d4" # Default current line color, will be overridden by theme
        self.font_bold = self.font.copy()
        self.font_bold.configure(weight="bold")
        self.bg_color = "#f0f0f0"
        
        self.config(
            width=40, # Initial width, will adjust dynamically
            bg=self.bg_color,
            highlightthickness=0, bd=0,
            cursor="arrow" # Standard cursor
        )
        
        # Bind scroll events to synchronize with editor
        # Note: These are bound to the editor, not the canvas itself, to capture editor scrolls
        self.editor.bind("<MouseWheel>", self._on_mousewheel)
        self.editor.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        self.editor.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down
        self.editor.bind("<Configure>", self._on_configure)  # For resizing the editor, which might affect line numbers

    def update_theme(self, text_color, bg_color, current_line_text_color):
        self.text_color = text_color
        self.bg_color = bg_color
        self.text_color_current = current_line_text_color
        self.config(bg=self.bg_color)
        self.redraw() # Redraw content to apply new colors

    def redraw(self):
        """Updates the line numbers displayed in the widget."""
        self.delete("all") # Clear existing numbers on the canvas

        if not self.editor or not self.winfo_exists():
            return
        
        # Get total lines in the document for width calculation
        last_doc_line_index = self.editor.index("end-1c") # Last character in the document
        # Handle empty editor case: "end-1c" on empty editor is "1.0", so check content
        if last_doc_line_index == "1.0" and not self.editor.get("1.0", "1.end").strip():
            total_lines_in_doc = 0
        else:
            total_lines_in_doc = int(last_doc_line_index.split('.')[0])

        # Determine the maximum line number that might be displayed for width calculation
        # This should be the total lines in the document, or a reasonable minimum for empty files
        max_line_num_for_width = max(total_lines_in_doc, 1) # Ensure at least 1 for width calc
        max_digits = len(str(max_line_num_for_width)) if max_line_num_for_width > 0 else 1
        
        required_width = self.font.measure("0" * max_digits) + 10 # 10 for padding
        
        # Adjust canvas width if needed
        if abs(self.winfo_width() - required_width) > 2: # Only reconfigure if significant change
             self.config(width=required_width)

        # Iterate through visible lines in the editor
        first_visible_line_index = self.editor.index("@0,0") # Get index of the first visible character
        last_visible_line_index = self.editor.index(f"@0,{self.editor.winfo_height()}")
        
        # Start from the first visible line
        current_line_index = first_visible_line_index
        
        # Get the current line number from the editor's insert cursor
        current_editor_line_num = int(self.editor.index(tk.INSERT).split('.')[0])
        
        while True:
            dline = self.editor.dlineinfo(current_line_index)
            if dline is None: break # No more lines visible or invalid index

            x, y, width, height, baseline = dline
            line_num = int(current_line_index.split(".")[0])
            
            # Determine font and color for the line number
            if line_num == current_editor_line_num:
                font_to_use = self.font_bold
                color_to_use = self.text_color_current
            else:
                font_to_use = self.font
                color_to_use = self.text_color

            # Draw the line number on the canvas
            self.create_text(required_width - 5, y, anchor="ne",
                             text=str(line_num), font=font_to_use, fill=color_to_use)

            # Move to the next line
            next_line_index = self.editor.index(f"{current_line_index}+1line")
            if next_line_index == current_line_index: break # No more lines
            
            # Stop if we've drawn past the visible area.
            # Adding a small buffer (e.g., 2 lines) can prevent flicker at the bottom.
            if self.editor.compare(current_line_index, ">", last_visible_line_index + "+2lines"):
                break
            
            current_line_index = next_line_index

    def _on_mousewheel(self, event):
        """Propagates mouse wheel scroll from editor to line numbers."""
        pass

    def _on_configure(self, event):
        """Handles configure events (e.g., resize) to redraw line numbers."""
        self.redraw()

    def highlight_line(self, line_num):
        """
        This method is no longer needed as highlighting is done directly in redraw.
        It's kept as a placeholder or can be removed if no external calls rely on it.
        """
        # The current line highlighting is now handled directly within redraw()
        # by checking if line_num == current_editor_line_num.
        # This method can be simplified or removed if not used elsewhere.
        self.redraw() # Force a redraw to update the highlight

class EditorTab(ttk.Frame):
    """Represents a single tab in the editor notebook."""
    def __init__(self, parent_notebook, file_path=None, schedule_heavy_updates_callback=None):
        super().__init__(parent_notebook)
        self.notebook = parent_notebook
        self.file_path = file_path
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback # Store the callback
        self.last_saved_content = "" if file_path else "\n"

        # Each tab has its own font object to manage zoom level independently
        self.editor_font = Font(family="Consolas", size=12)

        # --- Editor Widgets for this tab ---
        self.editor = tk.Text(self, wrap="word", font=self.editor_font, undo=True,
                              relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        
        # Configure a tag for highlighting the current line in the editor
        self.editor.tag_configure("current_line", background="#e8f0f8") # Default color
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.editor.yview) # Main editor scrollbar
        self.line_numbers = LineNumbers(self, editor_widget=self.editor, font=self.editor_font)
        
        self.line_numbers.pack(side="left", fill="y")
        self.scrollbar.pack(side="right", fill="y") # Pack main editor scrollbar
        self.editor.pack(side="left", fill="both", expand=True)

        # --- Configure scroll and events ---
        def sync_scroll_and_redraw(*args):
            self.scrollbar.set(*args)
            # Line numbers redraw is now handled by perform_heavy_updates, which is debounced.
            self.schedule_heavy_updates() # Schedule heavy updates (syntax, outline, and line numbers) with a debounce

        self.editor.config(yscrollcommand=sync_scroll_and_redraw)
        
        # Bind events to the editor instance of this tab
        self.editor.bind("<KeyRelease>", self._on_editor_event)
        self.editor.bind("<ButtonRelease-1>", self._on_editor_event)
        self.editor.bind("<FocusIn>", self._on_editor_event)
        self.editor.bind("<Configure>", self._on_editor_event)

    def _on_editor_event(self, event=None):
        """
        Central handler for events that should trigger updates.
        This includes key presses, mouse clicks, and configuration changes.
        """
        self.update_tab_title()
        self.schedule_heavy_updates(event)
        self._highlight_current_line()

    def schedule_heavy_updates(self, event=None):
        """Schedules heavy updates for this specific tab by calling the main interface scheduler callback."""
        if self._schedule_heavy_updates_callback:
            self._schedule_heavy_updates_callback(event) # Call the passed callback

    def get_content(self):
        """Returns the full content of the editor widget."""
        return self.editor.get("1.0", tk.END)

    def is_dirty(self):
        """Checks if the editor content has changed since the last save."""
        return self.get_content() != self.last_saved_content

    def update_tab_title(self):
        """Updates the notebook tab text to show a '*' if the file is dirty."""
        base_name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        title = f"{base_name}{'*' if self.is_dirty() else ''}"
        self.notebook.tab(self, text=title)

    def load_file(self):
        """Loads content from self.file_path into the editor."""
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.editor.delete("1.0", tk.END)
                    self.editor.insert("1.0", content)
                    self.last_saved_content = self.get_content()
                    self.update_tab_title()
                    
                    # --- NEW: Apply full syntax highlighting on load ---
                    # This ensures the entire document is highlighted initially.
                    # It's a direct call, bypassing the debounce for immediate visual feedback.
                    editor_logic.apply_syntax_highlighting(self.editor, full_document=True)
                    
                    # Use 'after' to ensure the highlight is applied after the mainloop is idle
                    self.after(10, self._highlight_current_line)
                    self.editor.edit_reset() # Clear undo stack
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
        else:
            # This is a new, unsaved file
            self.update_tab_title()
            # For new files, still apply initial highlight (empty document) and current line
            editor_logic.apply_syntax_highlighting(self.editor, full_document=True)
            self.after(10, self._highlight_current_line)

    def _highlight_current_line(self, event=None):
        """Highlights the current line in the editor and the corresponding line number."""
        self.editor.tag_remove("current_line", "1.0", "end")
        self.editor.tag_add("current_line", "insert linestart", "insert lineend+1c")
        # Line numbers redraw is now handled by perform_heavy_updates, which is debounced.

    def save_file(self, new_path=None):
        """
        Saves the editor content. If new_path is provided, it's a 'Save As' operation.
        Returns True on success, False on failure (e.g., user cancelled Save As).
        """
        if new_path:
            self.file_path = new_path
        
        if not self.file_path:
            return False # Should have been handled by a 'save as' dialog before calling this

        try:
            content = self.get_content()
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.last_saved_content = content
            self.update_tab_title()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{e}")
            return False