"""
This module defines the `LineNumbers` and `EditorTab` classes, which are core components
of the text editor interface. `LineNumbers` provides a visual display of line numbers
adjacent to a `tk.Text` widget, while `EditorTab` encapsulates a single editable
document tab within the application's notebook.
"""

import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
import os
from tkinter import messagebox
import llm_state
import debug_console
import interface_shortcuts


class LineNumbers(tk.Canvas):
    """
    A custom Tkinter Canvas widget responsible for displaying line numbers
    alongside a `tk.Text` widget.

    It synchronizes its scrolling with the associated text editor and dynamically
    adjusts its width based on the number of digits in the highest line number.
    """
    def __init__(self, master, editor_widget, font, **kwargs):
        """
        Initializes the LineNumbers canvas.

        Args:
            master (tk.Widget): The parent widget (typically an EditorTab instance).
            editor_widget (tk.Text): The `tk.Text` widget for which line numbers are displayed.
            font (tkinter.font.Font): The font to use for rendering line numbers.
            **kwargs: Arbitrary keyword arguments passed to the `tk.Canvas` constructor.
        """
        super().__init__(master, **kwargs)
        self.editor = editor_widget
        self.font = font
        # Default colors for the line number display.
        self.text_color = "#6a737d"  # Grey text for line numbers.
        self.bg_color = "#f0f0f0"    # Light grey background for the line number bar.
        self.config(width=40, bg=self.bg_color, highlightthickness=0, bd=0)

    def update_theme(self, text_color, bg_color):
        """
        Updates the foreground and background colors of the line number bar.

        Args:
            text_color (str): The new color for the line number text.
            bg_color (str): The new background color for the line number bar.
        """
        self.text_color = text_color
        self.bg_color = bg_color
        self.config(bg=self.bg_color)
        self.redraw() # Redraw the line numbers with the new colors.

    def redraw(self, *args):
        """
        Redraws the line numbers on the canvas.

        This method is called whenever the editor's content or scroll position changes.
        It calculates which lines are visible and draws their corresponding numbers,
        adjusting the canvas width as needed.
        """
        self.delete("all") # Clear all existing drawings on the canvas.
        # Ensure the editor widget and the canvas itself still exist.
        if not self.editor or not self.winfo_exists():
            return
        
        # Get the Tkinter index of the first visible line in the editor.
        first_visible_line_index = self.editor.index("@0,0")
        # Get the Tkinter index of the last character in the entire document.
        last_document_char_index = self.editor.index("end-1c")
        
        try:
            # Extract the line number from the last document character index.
            last_document_line_number = int(last_document_char_index.split('.')[0])
            # Special handling for an empty document where "end-1c" might still return "1.0".
            if last_document_char_index == "1.0" and not self.editor.get("1.0", "1.end"):
                 last_document_line_number = 0
        except (ValueError, tk.TclError):
            last_document_line_number = 0 # Default to 0 if line number extraction fails.

        # Calculate the required width for the line number canvas based on the largest line number.
        # This ensures enough space for all digits.
        max_digits = len(str(last_document_line_number)) if last_document_line_number > 0 else 1
        required_width = self.font.measure("0" * max_digits) + 10 # Add padding.
        
        # Adjust canvas width if it significantly differs from the required width.
        if abs(self.winfo_width() - required_width) > 2:
             self.config(width=required_width)

        # Iterate through visible lines and draw their numbers.
        current_line_index = first_visible_line_index
        while True:
            # Get information about the current visible line (x, y, height, etc.).
            dline_info = self.editor.dlineinfo(current_line_index)
            if dline_info is None: break # Break if no more visible lines.
            
            # Unpack line information.
            x, y, width, height, baseline = dline_info
            # Extract the line number as a string.
            line_number_str = current_line_index.split(".")[0]
            
            # Draw the line number on the canvas.
            self.create_text(required_width - 5, y, anchor="ne",
                             text=line_number_str, font=self.font, fill=self.text_color)
            
            # Move to the next line in the editor.
            next_line_index = self.editor.index(f"{current_line_index}+1line")
            # Break if we've reached the end of the document or no more lines.
            if next_line_index == current_line_index: break 
            current_line_index = next_line_index
            
            # Safety break to prevent infinite loops in very large or malformed files.
            if int(current_line_index.split('.')[0]) > last_document_line_number + 100: break

class EditorTab(ttk.Frame):
    """
    Represents a single editable tab within the application's notebook widget.

    Each `EditorTab` contains a `tk.Text` widget for document editing, a `LineNumbers`
    canvas for displaying line numbers, and a scrollbar. It manages file loading,
    saving, dirty state, and integrates with syntax highlighting and image deletion logic.
    """
    def __init__(self, parent_notebook, file_path=None, schedule_heavy_updates_callback=None):
        """
        Initializes an EditorTab instance.

        Args:
            parent_notebook (ttk.Notebook): The parent notebook widget this tab belongs to.
            file_path (str, optional): The absolute path to the file associated with this tab.
                                       Defaults to None for new, unsaved files.
            schedule_heavy_updates_callback (callable, optional): A callback function
                                                                 to schedule computationally
                                                                 intensive updates (e.g., syntax highlighting).
        """
        super().__init__(parent_notebook)
        self.notebook = parent_notebook
        self.file_path = file_path
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback
        self.last_saved_content = "" # Stores content of the last saved version for dirty checking.
        self.error_labels = []       # List to hold references to embedded error widgets (e.g., for missing images).
        self.auto_pairs = {'(': ')', '{': '}', '[': ']', '"': '"', "'": "'"}

        self.editor_font = Font(family="Consolas", size=12) # Define the font for the editor.

        # Configure tags for bracket highlighting
        self.editor.tag_configure("matching_bracket", background="#D0E0F0") # Light blue background

        # Create the main text editing area.
        self.editor = tk.Text(self, wrap="word", font=self.editor_font, undo=True,
                              relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        
        # Create a vertical scrollbar and link it to the editor.
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.editor.yview)
        # Create the line numbers canvas and link it to the editor.
        self.line_numbers = LineNumbers(self, editor_widget=self.editor, font=self.editor_font)
        
        # Pack widgets into the frame.
        self.line_numbers.pack(side="left", fill="y")
        self.scrollbar.pack(side="right", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)

        # Define a function to synchronize scrolling between the editor and line numbers.
        def sync_scroll_and_redraw(*args):
            """
            Synchronizes the scrollbar and line numbers with the editor's vertical scroll.
            This function is set as the `yscrollcommand` for the editor.
            """
            self.scrollbar.set(*args) # Update the scrollbar position.
            # Move the line numbers canvas to match the editor's vertical scroll.
            self.line_numbers.yview_moveto(self.editor.yview()[0])
            self.line_numbers.redraw() # Redraw line numbers to reflect new view.

        self.editor.config(yscrollcommand=sync_scroll_and_redraw)
        
        # Bind key events to update tab state and schedule heavy updates.
        self.editor.bind("<KeyRelease>", self.on_key_release)
        self.editor.bind("<Configure>", self.schedule_heavy_updates) # For window resizing.
        self.editor.bind("<Tab>", self._on_tab_key) # Custom Tab key handling.
        self.editor.bind("<Shift-Tab>", self._on_shift_tab_key) # Custom Shift+Tab handling.
        self.editor.bind("<Return>", self._on_return_key)
        self.editor.bind("<KeyPress>", self._on_key_press)
        self.editor.bind("<ButtonRelease-1>", self._on_mouse_release) # For mouse clicks
        self.editor.bind("<<Selection>>", self._on_selection_change) # For selection changes

        interface_shortcuts.bind_editor_specific_shortcuts(self.editor)

    def _on_tab_key(self, event=None):
        """
        Handles the Tab key press for indentation.

        If text is selected, it indents all selected lines. Otherwise, it inserts
        4 spaces at the cursor position. Prevents default Tkinter tab behavior.

        Args:
            event (tk.Event, optional): The Tkinter event object. Defaults to None.

        Returns:
            str: "break" to stop further event propagation.
        """
        # If LLM is generating, let its interactive session handle the tab key.
        if llm_state._is_generating: 
            return # Do not return "break" here, let the LLM handler process it.

        if self.editor.tag_ranges("sel"): # Check if there is a text selection.
            start_index, end_index = self.editor.index("sel.first"), self.editor.index("sel.last")
            start_line = int(start_index.split('.')[0])
            end_line = int(end_index.split('.')[0])
            # Adjust end_line if the selection ends exactly at the beginning of a line.
            if end_index.split('.')[1] == '0': 
                end_line -= 1
            
            # Insert 4 spaces at the beginning of each selected line.
            for line_num in range(start_line, end_line + 1):
                self.editor.insert(f"{line_num}.0", "    ")
            
            # Re-select the indented block.
            self.editor.tag_add("sel", f"{start_line}.0", f"{end_line+1}.0")
            self.on_key_release()
            return "break"
        else:
            # If no selection, just insert 4 spaces at the current cursor position.
            self.editor.insert(tk.INSERT, "    ")
            self.on_key_release()
            return "break"

    def _on_shift_tab_key(self, event=None):
        """
        Handles the Shift+Tab key press for outdentation.

        If text is selected, it outdents all selected lines by removing a tab
        or 4 spaces from the beginning of each line. Prevents default Tkinter
        shift-tab behavior.

        Args:
            event (tk.Event, optional): The Tkinter event object. Defaults to None.

        Returns:
            str: "break" to stop further event propagation.
        """
        # If LLM is generating, let its interactive session handle the shift-tab key.
        if llm_state._is_generating: 
            return # Do not return "break" here, let the LLM handler process it.

        if self.editor.tag_ranges("sel"): # Check if there is a text selection.
            start_index, end_index = self.editor.index("sel.first"), self.editor.index("sel.last")
            start_line = int(start_index.split('.')[0])
            end_line = int(end_index.split('.')[0])
            # Adjust end_line if the selection ends exactly at the beginning of a line.
            if end_index.split('.')[1] == '0': 
                end_line -= 1
            
            # Iterate through selected lines to remove indentation.
            for line_num in range(start_line, end_line + 1):
                line_start_index = f"{line_num}.0"
                line_content = self.editor.get(line_start_index, f"{line_num}.end")
                
                if line_content.startswith('    '):
                    self.editor.delete(line_start_index, f"{line_start_index}+4c")
                elif line_content.startswith('\t'):
                    self.editor.delete(line_start_index, f"{line_start_index}+1c")

            # Re-select the outdented block.
            self.editor.tag_add("sel", f"{start_line}.0", f"{end_line+1}.0")
            self.on_key_release()
            return "break"
        return "break" # Prevent focus change even with no selection.

    def _on_return_key(self, event=None):
        """
        Handles the Enter key press for auto-indentation.

        Inserts a newline and then adds the same indentation as the previous line.

        Returns:
            str: "break" to stop further event propagation.
        """
        # Get the current line and its indentation
        cursor_index = self.editor.index(tk.INSERT)
        current_line_number = int(cursor_index.split('.')[0])
        current_line_content = self.editor.get(f"{current_line_number}.0", f"{current_line_number}.end")
        
        indentation = ""
        for char in current_line_content:
            if char in " \t":
                indentation += char
            else:
                break

        # Get the text after the cursor
        text_after_cursor = self.editor.get(cursor_index, f"{current_line_number}.end")
        
        # Delete the text after the cursor
        self.editor.delete(cursor_index, f"{current_line_number}.end")

        # Insert a newline, the indentation and the text after the cursor
        self.editor.insert(tk.INSERT, f"\n{indentation}{text_after_cursor}")
        
        self.on_key_release()
        return "break"

    def _on_key_press(self, event=None):
        """
        Handles key presses for auto-pairing of brackets and quotes.
        """
        if not event.char or not event.char.isprintable():
            return

        char = event.char
        if char in self.auto_pairs:
            # If text is selected, wrap it
            if self.editor.tag_ranges("sel"):
                start, end = self.editor.index("sel.first"), self.editor.index("sel.last")
                selected_text = self.editor.get(start, end)
                
                # Special case for quotes: if text is already quoted, unwrap it
                if char in "'\"" and selected_text.startswith(char) and selected_text.endswith(char):
                    self.editor.delete(start, end)
                    self.editor.insert(start, selected_text[1:-1])
                    return "break"

                self.editor.delete(start, end)
                self.editor.insert(start, char + selected_text + self.auto_pairs[char])
                return "break"
            else:
                # Otherwise, insert the pair and move the cursor between them
                cursor_pos = self.editor.index(tk.INSERT)
                self.editor.insert(cursor_pos, char + self.auto_pairs[char])
                self.editor.mark_set(tk.INSERT, f"{cursor_pos}+{len(char)}c")
                return "break"
        
        # Handle typing a closing character when one is already present
        if char in self.auto_pairs.values():
            cursor_pos = self.editor.index(tk.INSERT)
            next_char = self.editor.get(cursor_pos, f"{cursor_pos}+1c")
            if char == next_char:
                self.editor.mark_set(tk.INSERT, f"{cursor_pos}+1c")
                return "break"
        
        self.on_key_release()

    def _on_mouse_release(self, event=None):
        self._highlight_matching_bracket()

    def _on_selection_change(self, event=None):
        self._highlight_matching_bracket()

    def _highlight_matching_bracket(self):
        self.editor.tag_remove("matching_bracket", "1.0", tk.END)
        
        cursor_pos = self.editor.index(tk.INSERT)
        char_before = self.editor.get(f"{cursor_pos}-1c", cursor_pos)
        char_after = self.editor.get(cursor_pos, f"{cursor_pos}+1c")

        brackets = {'(': ')', '{': '}', '[': ']', ')': '(', '}': '{', ']': '['}

        if char_before in brackets:
            target_char = char_before
            start_index = f"{cursor_pos}-1c"
            direction = tk.BACKWARD
        elif char_after in brackets:
            target_char = char_after
            start_index = cursor_pos
            direction = tk.FORWARD
        else:
            return

        # Find the matching bracket
        count = 0
        found_match = False
        search_index = start_index

        while True:
            search_index = self.editor.search(target_char, search_index, stopindex=tk.END if direction == tk.FORWARD else "1.0", backwards=(direction == tk.BACKWARD), regexp=False)
            if not search_index:
                break

            current_char = self.editor.get(search_index)
            if current_char == target_char:
                count += 1
            elif current_char == brackets[target_char]:
                count -= 1
            
            if count == 0:
                self.editor.tag_add("matching_bracket", start_index, f"{start_index}+1c")
                self.editor.tag_add("matching_bracket", search_index, f"{search_index}+1c")
                found_match = True
                break
            
            if direction == tk.FORWARD:
                search_index = f"{search_index}+1c"
            else:
                search_index = f"{search_index}-1c"
        
        if not found_match:
            # If no match found, highlight only the single bracket under or next to cursor
            if char_before in brackets:
                self.editor.tag_add("matching_bracket", f"{cursor_pos}-1c", cursor_pos)
            elif char_after in brackets:
                self.editor.tag_add("matching_bracket", cursor_pos, f"{cursor_pos}+1c")

    def on_key_release(self, event=None):
        """
        Callback function executed on any key release event in the editor.

        This updates the tab title to reflect the dirty state and schedules
        any heavy updates like syntax highlighting or outline tree updates.

        Args:
            event (tk.Event, optional): The Tkinter event object. Defaults to None.
        """
        self.update_tab_title() # Update the tab title to show if the file is modified.
        self.schedule_heavy_updates(event) # Trigger a debounced update for heavy operations.
        self._highlight_matching_bracket() # Update bracket highlighting on key release.

    def schedule_heavy_updates(self, event=None):
        """
        Calls the debounced update scheduler provided by the main interface.

        This mechanism prevents frequent, performance-intensive operations (like
        syntax highlighting or outline updates) from running on every keystroke,
        instead delaying them until a brief pause in typing.

        Args:
            event (tk.Event, optional): The Tkinter event object. Defaults to None.
        """
        if self._schedule_heavy_updates_callback:
            self._schedule_heavy_updates_callback(event)

    def get_content(self):
        """
        Retrieves the entire text content from the editor widget.

        Returns:
            str: The complete text content of the editor.
        """
        return self.editor.get("1.0", tk.END)

    def is_dirty(self):
        """
        Checks if the current editor content has been modified since the last save.

        Returns:
            bool: True if the content has changed, False otherwise.
        """
        return self.get_content() != self.last_saved_content

    def update_tab_title(self):
        """
        Updates the text displayed on the tab in the notebook.

        It appends an asterisk (*) to the file name if the document has unsaved changes.
        """
        # Get the base name of the file, or "Untitled" if it's a new file.
        base_name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        # Construct the new title, adding an asterisk if the file is dirty.
        title = f"{base_name}{'*' if self.is_dirty() else ''}"
        self.notebook.tab(self, text=title) # Set the tab's text.

    def load_file(self):
        """
        Loads content into the editor from the associated file path or a template for new files.

        If `self.file_path` is set and the file exists, its content is loaded. Otherwise,
        it attempts to load content from a `new_file_template.tex`. If the template is
        unavailable, an empty editor is presented.
        """
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as file_handle:
                    content = file_handle.read()
                    self.editor.delete("1.0", tk.END) # Clear existing content.
                    self.editor.insert("1.0", content) # Insert new content.
                    self.last_saved_content = self.get_content() # Mark as clean.
                    debug_console.log(f"Successfully loaded file: {self.file_path}", level='INFO')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
                debug_console.log(f"Error loading file '{self.file_path}': {e}", level='ERROR')
        else:
            # This branch handles new, unsaved files.
            debug_console.log("Attempting to load content for a new or non-existent file.", level='INFO')
            try:
                # Try to load content from a predefined template file.
                with open("new_file_template.tex", "r", encoding="utf-8") as template_file:
                    content = template_file.read()
                    self.editor.delete("1.0", tk.END)
                    self.editor.insert("1.0", content)
                # A new file with template content is considered dirty until explicitly saved.
                self.last_saved_content = "\n" # Set to a known initial state for dirty checking.
                debug_console.log("Loaded content from new_file_template.tex.", level='INFO')
            except Exception as e:
                # Fallback: if template loading fails, create a completely empty file.
                self.editor.delete("1.0", tk.END)
                self.last_saved_content = self.get_content() # Should be an empty string or "\n".
                debug_console.log(f"Could not load new_file_template.tex (Reason: {e}). Creating empty file.", level='WARNING')
        
        self.update_tab_title() # Update the tab title to reflect loaded state.
        self.editor.edit_reset() # Clear the undo/redo stack for the new content.

    def save_file(self, new_path=None):
        """
        Saves the current editor content to the associated file path.

        If `new_path` is provided, the tab's `file_path` is updated before saving.
        The `last_saved_content` is updated, and the tab title is refreshed.

        Args:
            new_path (str, optional): A new path to save the file to. Defaults to None.

        Returns:
            bool: True if the file was saved successfully, False otherwise.
        """
        if new_path:
            self.file_path = new_path # Update the file path if a new one is provided.
        
        if not self.file_path:
            # This scenario should ideally be handled by a "Save As" dialog in the main interface.
            debug_console.log("Save operation aborted in EditorTab: No file path specified for saving.", level='WARNING')
            return False

        try:
            content_to_save = self.get_content()
            with open(self.file_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(content_to_save)
            self.last_saved_content = content_to_save # Update last saved content.
            self.update_tab_title() # Refresh the tab title (removes asterisk).
            debug_console.log(f"Successfully saved file: {self.file_path}", level='INFO')
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{e}")
            debug_console.log(f"Failed to save file '{self.file_path}': {e}", level='ERROR')
            return False
