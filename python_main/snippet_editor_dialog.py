# snippet_editor_dialog.py

import tkinter as tk
from tkinter import ttk, messagebox
import debug_console

class SnippetEditorDialog(tk.Toplevel):
    """
    A full-featured dialog for viewing, creating, editing, and deleting snippets.
    """
    def __init__(self, parent, theme_settings, current_snippets, save_callback):
        super().__init__(parent)
        self.transient(parent)
        self.title("Snippet Editor")
        self.geometry("900x600")
        self.grab_set()

        self.theme = theme_settings
        self.snippets = current_snippets.copy()  # Work on a copy
        self.save_callback = save_callback

        self._setup_ui()
        self._populate_listbox()
        self._update_button_states()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)

    def _setup_ui(self):
        """Builds the entire user interface for the dialog."""
        self.configure(bg=self.theme.get("root_bg", "#f0f0f0"))

        # Main Paned Window for a resizable layout
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, sashwidth=6)
        main_pane.configure(bg=self.theme.get("panedwindow_sash", "#d0d0d0"))
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Left Pane: Snippet List ---
        left_frame = ttk.Frame(main_pane, padding=5)
        ttk.Label(left_frame, text="Snippets").pack(anchor="w", pady=(0, 5))
        
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill="both", expand=True)
        self.snippet_listbox = tk.Listbox(
            listbox_frame, exportselection=False,
            bg=self.theme.get("editor_bg"), fg=self.theme.get("editor_fg"),
            selectbackground=self.theme.get("sel_bg"), selectforeground=self.theme.get("sel_fg"),
            highlightthickness=0, borderwidth=0, relief=tk.FLAT
        )
        self.snippet_listbox.pack(side="left", fill="both", expand=True)
        list_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.snippet_listbox.yview)
        list_scrollbar.pack(side="right", fill="y")
        self.snippet_listbox.config(yscrollcommand=list_scrollbar.set)
        self.snippet_listbox.bind("<<ListboxSelect>>", self._on_snippet_select)
        
        main_pane.add(left_frame, width=250, minsize=200)

        # --- Right Pane: Editor ---
        right_frame = ttk.Frame(main_pane, padding=5)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(3, weight=1)

        # Keyword entry
        ttk.Label(right_frame, text="Keyword:").grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.keyword_entry = ttk.Entry(right_frame, font=("Segoe UI", 10))
        self.keyword_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Content text area
        ttk.Label(right_frame, text="Snippet Content:").grid(row=2, column=0, sticky="w", pady=(0, 2))
        text_frame = ttk.Frame(right_frame)
        text_frame.grid(row=3, column=0, sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.content_text = tk.Text(
            text_frame, wrap="word", undo=True, font=("Consolas", 10),
            bg=self.theme.get("editor_bg"), fg=self.theme.get("editor_fg"),
            selectbackground=self.theme.get("sel_bg"), selectforeground=self.theme.get("sel_fg"),
            insertbackground=self.theme.get("editor_insert_bg"),
            relief=tk.FLAT, borderwidth=0, highlightthickness=0
        )
        self.content_text.grid(row=0, column=0, sticky="nsew")
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.content_text.yview)
        text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.content_text.config(yscrollcommand=text_scrollbar.set)

        # Action Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=4, column=0, sticky="e", pady=(10, 0))
        self.save_button = ttk.Button(button_frame, text="Save", command=self._save_snippet)
        self.save_button.pack(side="left", padx=5)
        self.delete_button = ttk.Button(button_frame, text="Delete Snippet", command=self._delete_snippet)
        self.delete_button.pack(side="left", padx=5)
        ttk.Button(button_frame, text="New Snippet", command=self._new_snippet).pack(side="left")

        main_pane.add(right_frame, stretch="always")

    def _populate_listbox(self):
        """Clears and refills the listbox with current snippet keywords."""
        self.snippet_listbox.delete(0, tk.END)
        # Sort keywords alphabetically for easier navigation
        for keyword in sorted(self.snippets.keys()):
            self.snippet_listbox.insert(tk.END, keyword)

    def _on_snippet_select(self, event=None):
        """Handles selection change in the listbox."""
        selection_indices = self.snippet_listbox.curselection()
        if not selection_indices:
            return
        
        selected_keyword = self.snippet_listbox.get(selection_indices[0])
        
        self.keyword_entry.delete(0, tk.END)
        self.keyword_entry.insert(0, selected_keyword)
        
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", self.snippets.get(selected_keyword, ""))
        
        self._update_button_states()

    def _new_snippet(self):
        """Clears the fields to prepare for a new snippet entry."""
        self.snippet_listbox.selection_clear(0, tk.END)
        self.keyword_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)
        self.keyword_entry.focus_set()
        self._update_button_states()

    def _save_snippet(self):
        """Saves the current snippet (new or existing) and updates the app."""
        keyword = self.keyword_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not keyword:
            messagebox.showwarning("Missing Keyword", "Snippet keyword cannot be empty.", parent=self)
            return
        if not re.match(r'^\w+$', keyword):
            messagebox.showwarning("Invalid Keyword", "Keyword can only contain letters, numbers, and underscores.", parent=self)
            return

        # If a snippet was selected, check if the keyword was renamed.
        # If so, we need to remove the old one.
        selection_indices = self.snippet_listbox.curselection()
        if selection_indices:
            old_keyword = self.snippet_listbox.get(selection_indices[0])
            if old_keyword != keyword and old_keyword in self.snippets:
                del self.snippets[old_keyword]

        self.snippets[keyword] = content
        
        if self.save_callback(self.snippets):
            debug_console.log(f"Snippet '{keyword}' saved successfully.", level='SUCCESS')
            self._populate_listbox()
            # Reselect the saved item for a smooth UX
            if keyword in self.snippet_listbox.get(0, tk.END):
                idx = self.snippet_listbox.get(0, tk.END).index(keyword)
                self.snippet_listbox.selection_set(idx)
                self.snippet_listbox.activate(idx)
        else:
            messagebox.showerror("Save Error", "Could not save snippets to file.", parent=self)

    def _delete_snippet(self):
        """Deletes the selected snippet after confirmation."""
        selection_indices = self.snippet_listbox.curselection()
        if not selection_indices:
            return
            
        keyword = self.snippet_listbox.get(selection_indices[0])
        
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the snippet '{keyword}'?", parent=self):
            if keyword in self.snippets:
                del self.snippets[keyword]
                if self.save_callback(self.snippets):
                    debug_console.log(f"Snippet '{keyword}' deleted.", level='SUCCESS')
                    self._populate_listbox()
                    self._new_snippet() # Clear fields after deletion
                else:
                    messagebox.showerror("Save Error", "Could not save changes after deletion.", parent=self)

    def _update_button_states(self):
        """Enables or disables buttons based on the current selection state."""
        has_selection = self.snippet_listbox.curselection()
        self.delete_button.config(state=tk.NORMAL if has_selection else tk.DISABLED)