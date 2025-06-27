# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\editor_tab.py
import tkinter as tk
import editor_logic
from tkinter import ttk, messagebox
from tkinter.font import Font
import os
import re
try:
    from tkcode import CodeEditor
except ImportError:
    raise ImportError("tkcode module not found. Please install with 'pip install tkcode'.")

# --- PATCH for tkcode compatibility ---
# Some versions of tkcode require explicit setting of the lexer after initialization.
# This workaround ensures the editor does not fail with AttributeError: 'CodeEditor' object has no attribute '_lexer'
def _patch_tkcode_lexer(editor):
    if not hasattr(editor, "_lexer"):
        # Fallback: set a dummy lexer to avoid crashes
        import pygments.lexers
        editor._lexer = lambda: pygments.lexers.get_lexer_by_name("text")
        # Optionally, try to set the correct lexer if available
        try:
            editor.update_lexer("latex")
        except Exception:
            pass

INDENT_WIDTH = 4

class EditorTab(ttk.Frame):
    """Represents a single tab in the editor notebook."""
    def __init__(self, parent_notebook, file_path=None, schedule_heavy_updates_callback=None):
        super().__init__(parent_notebook)
        self.notebook = parent_notebook
        self.file_path = file_path
        self._schedule_heavy_updates_callback = schedule_heavy_updates_callback

        self.last_content_for_outline_parsing = ""
        self.last_parsed_outline_structure = []

        self.editor_font = Font(family="Consolas", size=12)

        # --- tkcode Editor Widget ---
        # Workaround: set language="text" to avoid tkcode's buggy latex lexer, then patch after creation
        self.editor = CodeEditor(
            self,
            width=1, height=1,
            language="text",  # Use "text" to avoid _lexer bug, patch below
            font=self.editor_font,
            highlighter="dracula",
            blockcursor=True,
            background="#232629",
            foreground="#f8f8f2",
            insertbackground="#f8f8f2",
            selectbackground="#44475a",
            selectforeground="#f8f8f2",
            padx=4, pady=4,
            wrap="word",
            undo=True
        )
        # Patch the lexer after creation to avoid AttributeError
        try:
            self.editor.update_lexer("latex")
        except Exception:
            pass
        self.editor.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.editor.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.editor.config(yscrollcommand=self.scrollbar.set)

        # Bind events
        self.editor.bind("<KeyRelease>", self._on_editor_event)
        self.editor.bind("<ButtonRelease-1>", self._on_editor_event)
        self.editor.bind("<FocusIn>", self._on_editor_event)
        self.editor.bind("<Configure>", self._on_editor_event)
        self.editor.bind("<Tab>", self._on_tab_key)
        self.editor.bind("<Shift-Tab>", self._on_shift_tab_key)
        self.editor.bind("<Control-BackSpace>", self._on_ctrl_backspace_key)

        self.editor.edit_modified(False)

    def _on_editor_event(self, event=None):
        """Central handler for events that should trigger updates."""
        self.update_tab_title()
        self.schedule_heavy_updates(event)

    def schedule_heavy_updates(self, event=None):
        """Schedules heavy updates for this specific tab by calling the main interface scheduler callback."""
        if self._schedule_heavy_updates_callback:
            self._schedule_heavy_updates_callback(event) # Call the passed callback

    def get_content(self):
        """Returns the full content of the editor widget."""
        return self.editor.get("1.0", tk.END)

    def is_dirty(self):
        """Checks if the editor content has changed since the last save."""
        return self.editor.edit_modified()

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
                    self.update_tab_title()
                    self.editor.edit_reset()
                    self.editor.edit_modified(False)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
        else:
            # This is a new, unsaved file
            self.update_tab_title()
            self.editor.edit_modified(False)

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
            self.update_tab_title()
            self.editor.edit_reset()
            self.editor.edit_modified(False)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{e}")
            return False

    def _on_tab_key(self, event):
        """Handles the Tab key for indentation."""
        try:
            self.editor.edit_separator()
            if self.editor.tag_ranges("sel"):
                # Multi-line selection: indent all selected lines
                start_index = self.editor.index("sel.first linestart")
                end_index = self.editor.index("sel.last lineend")

                selected_text = self.editor.get(start_index, end_index)
                lines = selected_text.split('\n')
                indented_lines = [" " * INDENT_WIDTH + line for line in lines]
                new_text = '\n'.join(indented_lines)

                self.editor.delete(start_index, end_index)
                self.editor.insert(start_index, new_text)
                # Re-select the indented block
                self.editor.tag_add("sel", start_index, self.editor.index(f"{start_index}+{len(new_text)}c"))
            else:
                # No selection: insert spaces at cursor
                self.editor.insert(tk.INSERT, " " * INDENT_WIDTH)
        finally:
            self.editor.edit_separator()
        return "break"  # Prevent default Tkinter tab behavior

    def _on_shift_tab_key(self, event):
        """Handles Shift+Tab for unindentation."""
        try:
            self.editor.edit_separator()
            if self.editor.tag_ranges("sel"):
                # Multi-line selection: unindent all selected lines
                start_index = self.editor.index("sel.first linestart")
                end_index = self.editor.index("sel.last lineend")

                selected_text = self.editor.get(start_index, end_index)
                lines = selected_text.split('\n')
                dedented_lines = []
                for line in lines:
                    if line.startswith(" " * INDENT_WIDTH):
                        dedented_lines.append(line[INDENT_WIDTH:])
                    elif line.startswith("\t"):
                        dedented_lines.append(line[1:])
                    else:
                        # If less than INDENT_WIDTH spaces, remove all leading spaces
                        leading_spaces_match = re.match(r"^\s*", line)
                        if leading_spaces_match:
                            num_leading_spaces = len(leading_spaces_match.group(0))
                            dedented_lines.append(line[num_leading_spaces:])
                        else:
                            dedented_lines.append(line)
                new_text = '\n'.join(dedented_lines)

                self.editor.delete(start_index, end_index)
                self.editor.insert(start_index, new_text)
                # Re-select the dedented block
                self.editor.tag_add("sel", start_index, self.editor.index(f"{start_index}+{len(new_text)}c"))
            else:
                # No selection: unindent current line
                current_line_start = self.editor.index("insert linestart")
                line_start_content = self.editor.get(current_line_start, f"{current_line_start} + {INDENT_WIDTH} chars")
                if line_start_content.startswith(" " * INDENT_WIDTH):
                    self.editor.delete(current_line_start, f"{current_line_start}+{INDENT_WIDTH}c") # Remove INDENT_WIDTH spaces
                elif line_start_content.startswith("\t"):
                    self.editor.delete(current_line_start, f"{current_line_start}+1c") # Remove one tab
                else:
                    # If less than INDENT_WIDTH spaces, remove all leading spaces
                    full_line_content = self.editor.get(current_line_start, f"{current_line_start} lineend")
                    leading_spaces_match = re.match(r"^\s*", full_line_content)
                    if leading_spaces_match:
                        num_leading_spaces = len(leading_spaces_match.group(0))
                        if num_leading_spaces > 0:
                            self.editor.delete(current_line_start, f"{current_line_start}+{num_leading_spaces}c")
        finally:
            self.editor.edit_separator()
        return "break"  # Prevent default Tkinter shift-tab behavior

    def _on_ctrl_backspace_key(self, event):
        """Handles Ctrl+Backspace for deleting a word backwards."""
        self.editor.delete("insert -1 chars wordstart", "insert")
        return "break"  # Prevent default behavior