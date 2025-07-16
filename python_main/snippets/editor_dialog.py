"""
This module defines the `SnippetEditorDialog` class, a comprehensive Tkinter dialog
for managing user-defined code snippets. It allows users to view, create, edit,
and delete snippets through a graphical interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from utils import debug_console

class SnippetEditorDialog(tk.Toplevel):
    """
    A full-featured dialog for viewing, creating, editing, and deleting code snippets.

    This dialog provides a user-friendly interface with a resizable layout, featuring
    a list of snippet keywords on the left and an editor panel on the right for
    modifying the selected snippet's keyword and content. It operates by interacting
    with a provided save callback function to persist changes.
    """
    def __init__(self, parent, theme_settings, current_snippets, save_callback):
        """
        Initializes the SnippetEditorDialog.

        Args:
            parent (tk.Tk or tk.Toplevel): The parent window of this dialog.
            theme_settings (dict): A dictionary containing theme-specific color settings.
            current_snippets (dict): A dictionary of existing snippets (keyword: content).
            save_callback (callable): A function to call when snippets need to be saved.
                                      Expected signature: `save_callback(updated_snippets_dict)`.
        """
        super().__init__(parent)
        self.transient(parent) # Make the dialog transient to its parent.
        self.title("Snippet Editor")
        self.geometry("900x600") # Set initial size.
        self.minsize(600, 400) # Set minimum size for resizing.
        self.grab_set() # Grab all input events until the dialog is closed.

        self.theme = theme_settings
        # Work on a copy of snippets to allow cancellation without affecting original data.
        self.snippets = current_snippets.copy()  
        self.save_callback = save_callback

        self._setup_ui() # Build the user interface.
        self._populate_listbox() # Populate the snippet list.
        self._update_button_states() # Set initial button states.
        self._new_snippet() # Start with a clean slate for creating a new snippet.

        self.protocol("WM_DELETE_WINDOW", self.destroy) # Handle window close button.
        self.wait_window(self) # Block until the dialog is closed.

    def _setup_ui(self):
        """
        Builds the entire user interface for the snippet editor dialog.

        This method configures the main window's background, sets up a paned window
        for a resizable layout, and creates the snippet listbox and editor panel
        with their respective widgets and styling.
        """
        self.configure(bg=self.theme.get("root_bg", "#f0f0f0"))

        # Main Paned Window for a resizable horizontal layout.
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
        main_pane.configure(bg=self.theme.get("panedwindow_sash", "#d0d0d0"))
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Left Pane: Snippet List ---
        left_frame = ttk.Frame(main_pane, padding=5)
        ttk.Label(left_frame, text="Snippets").pack(anchor="w", pady=(0, 5))
        
        self.snippet_listbox = tk.Listbox(
            left_frame, exportselection=False, # Allows multiple selections without clearing previous.
            bg=self.theme.get("editor_bg"), fg=self.theme.get("editor_fg"),
            selectbackground=self.theme.get("sel_bg"), selectforeground=self.theme.get("sel_fg"),
            highlightthickness=0, borderwidth=1, relief=tk.FLAT
        )
        self.snippet_listbox.pack(fill="both", expand=True)
        # Bind selection event to load snippet details.
        self.snippet_listbox.bind("<<ListboxSelect>>", self._on_snippet_select)
        main_pane.add(left_frame, width=250, minsize=200)

        # --- Right Pane: Editor for Snippet Details ---
        right_frame = ttk.Frame(main_pane, padding=5)
        right_frame.columnconfigure(0, weight=1) # Allow keyword and content to expand horizontally.
        right_frame.rowconfigure(3, weight=1) # Allow content text area to expand vertically.

        # Keyword input field.
        ttk.Label(right_frame, text="Keyword:").grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.keyword_entry = ttk.Entry(right_frame, font=("Segoe UI", 10))
        self.keyword_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Snippet content text area.
        ttk.Label(right_frame, text="Snippet Content:").grid(row=2, column=0, sticky="w", pady=(0, 2))
        self.content_text = tk.Text(
            right_frame, wrap="word", undo=True, font=("Consolas", 10),
            bg=self.theme.get("editor_bg"), fg=self.theme.get("editor_fg"),
            selectbackground=self.theme.get("sel_bg"), selectforeground=self.theme.get("sel_fg"),
            insertbackground=self.theme.get("editor_insert_bg"),
            relief=tk.FLAT, borderwidth=1, highlightthickness=0
        )
        self.content_text.grid(row=3, column=0, sticky="nsew")

        # --- Action Buttons for Snippet Management ---
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=4, column=0, sticky="e", pady=(10, 0))
        
        self.save_button = ttk.Button(button_frame, text="Save Snippet", command=self._save_snippet)
        self.save_button.pack(side="left", padx=5)
        
        self.delete_button = ttk.Button(button_frame, text="Delete Snippet", command=self._delete_snippet)
        self.delete_button.pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="New Snippet", command=self._new_snippet).pack(side="left")

        main_pane.add(right_frame, stretch="always") # Add right frame to the paned window.

    def _populate_listbox(self):
        """
        Clears the snippet listbox and repopulates it with current snippet keywords.
        Snippets are sorted alphabetically by keyword.
        """
        self.snippet_listbox.delete(0, tk.END) # Clear existing items.
        for keyword in sorted(self.snippets.keys()):
            self.snippet_listbox.insert(tk.END, keyword) # Insert each keyword.

    def _on_snippet_select(self, event=None):
        """
        Handles the selection change event in the snippet listbox.

        When a snippet is selected, its keyword and content are loaded into the
        respective editor fields for viewing or editing.
        """
        selection_indices = self.snippet_listbox.curselection()
        if not selection_indices:
            self._update_button_states() # Update button states if nothing is selected.
            return
        
        selected_keyword = self.snippet_listbox.get(selection_indices[0])
        
        # Populate the keyword entry and content text area.
        self.keyword_entry.delete(0, tk.END)
        self.keyword_entry.insert(0, selected_keyword)
        
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", self.snippets.get(selected_keyword, ""))
        
        self._update_button_states() # Update button states based on selection.

    def _new_snippet(self):
        """
        Clears the keyword and content editor fields to prepare for entering a new snippet.
        Also clears any listbox selection and sets focus to the keyword entry.
        """
        self.snippet_listbox.selection_clear(0, tk.END) # Deselect any item in the listbox.
        self.keyword_entry.delete(0, tk.END) # Clear keyword entry.
        self.content_text.delete("1.0", tk.END) # Clear content text area.
        self.keyword_entry.focus_set() # Set focus to the keyword entry for immediate input.
        self._update_button_states() # Update button states (e.g., disable delete).

    def _save_snippet(self):
        """
        Validates the input and saves the current snippet (either new or updated).

        It performs validation on the keyword, handles renaming of existing snippets,
        updates the internal `snippets` dictionary, and then calls the external
        `save_callback` to persist the changes.
        """
        keyword = self.keyword_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not keyword:
            messagebox.showwarning("Missing Keyword", "Snippet keyword cannot be empty.", parent=self)
            return
        # Validate keyword format (alphanumeric and underscores only).
        if not re.match(r'^\w+$', keyword):
            messagebox.showwarning("Invalid Keyword", "Keyword can only contain letters, numbers, and underscores.", parent=self)
            return

        # If a snippet was selected and its keyword was changed, remove the old entry.
        selection_indices = self.snippet_listbox.curselection()
        if selection_indices:
            old_keyword = self.snippet_listbox.get(selection_indices[0])
            if old_keyword != keyword and old_keyword in self.snippets:
                del self.snippets[old_keyword]

        self.snippets[keyword] = content # Add or update the snippet in the internal dictionary.
        
        # Call the external save callback to persist changes to file.
        if self.save_callback(self.snippets):
            debug_console.log(f"Snippet '{keyword}' saved successfully.", level='SUCCESS')
            self._populate_listbox() # Refresh the listbox to reflect changes.
            # Reselect the newly saved/updated item for a smooth user experience.
            try:
                idx = list(sorted(self.snippets.keys())).index(keyword)
                self.snippet_listbox.selection_set(idx)
                self.snippet_listbox.activate(idx)
                self.snippet_listbox.see(idx)
            except ValueError:
                pass # Should not happen if populate_listbox and save were successful.
        else:
            messagebox.showerror("Save Error", "Could not save snippets to file. Check console for details.", parent=self)

    def _delete_snippet(self):
        """
        Deletes the currently selected snippet after user confirmation.

        It removes the snippet from the internal dictionary and then calls the
        external `save_callback` to persist the deletion.
        """
        selection_indices = self.snippet_listbox.curselection()
        if not selection_indices:
            return # Do nothing if no snippet is selected.
            
        keyword_to_delete = self.snippet_listbox.get(selection_indices[0])
        
        # Ask for user confirmation before deleting.
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the snippet '{keyword_to_delete}'? This action cannot be undone.", parent=self, icon='warning'):
            if keyword_to_delete in self.snippets:
                del self.snippets[keyword_to_delete] # Remove from internal dictionary.
                if self.save_callback(self.snippets):
                    debug_console.log(f"Snippet '{keyword_to_delete}' deleted successfully.", level='SUCCESS')
                    self._populate_listbox() # Refresh the listbox.
                    self._new_snippet() # Clear editor fields after deletion.
                else:
                    # If saving fails, re-add the snippet to maintain internal consistency.
                    self.snippets[keyword_to_delete] = "" 
                    messagebox.showerror("Save Error", "Could not save changes after deletion. Snippet might not be fully removed.", parent=self)

    def _update_button_states(self):
        """
        Updates the enabled/disabled state of the 'Delete Snippet' button.

        The button is enabled only if a snippet is currently selected in the listbox.
        """
        has_selection = self.snippet_listbox.curselection() # Check if any item is selected.
        self.delete_button.config(state=tk.NORMAL if has_selection else tk.DISABLED)
