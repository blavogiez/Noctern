"""
Integrated snippets editor panel for the left sidebar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from typing import Optional, Dict, Callable, List
from .base_panel import BasePanel
from .panel_factory import PanelStyle, StandardComponents
from utils import debug_console


class SnippetsPanel(BasePanel):
    """
    Integrated snippets editor panel that replaces the dialog window.
    """
    
    def __init__(self, parent_container: tk.Widget, theme_getter,
                 current_snippets: Dict,
                 save_callback: Callable,
                 on_close_callback=None):
        super().__init__(parent_container, theme_getter, on_close_callback)
        
        # Work on copy of snippets to allow cancellation
        self.snippets = current_snippets.copy()
        self.save_callback = save_callback
        
        # UI components
        self.snippets_listbox: Optional[tk.Listbox] = None
        self.name_entry: Optional[tk.Entry] = None
        self.trigger_entry: Optional[tk.Entry] = None
        self.content_text: Optional[tk.Text] = None
        self.save_button: Optional[tk.Button] = None
        self.delete_button: Optional[tk.Button] = None
        
        # Current editing state
        self.current_snippet_index = -1
        self.is_editing = False
        
    def get_panel_title(self) -> str:
        return "Snippet Editor"
    
    def get_layout_style(self) -> PanelStyle:
        """Use split layout for snippets list and editor."""
        return PanelStyle.SPLIT
    
    def create_content(self):
        """Create the snippets editor panel content using standardized layout."""
        # Use the standardized split layout
        paned_window = self.main_container
        
        # Left pane: snippet list
        self._create_snippet_list(paned_window)
        
        # Right pane: snippet editor
        self._create_snippet_editor(paned_window)
        
        # Initialize
        self._populate_listbox()
        self._update_button_states()
        self._new_snippet()
        
    def _create_snippet_list(self, parent):
        """Create the snippet list section."""
        left_frame = ttk.Frame(parent)
        left_frame.pack_propagate(False)  # Maintain size
        
        # Header with standardized components
        header_section = StandardComponents.create_section(left_frame, "")
        header_section.pack(fill="x", padx=0, pady=(0, StandardComponents.ELEMENT_SPACING))
        
        header_frame = ttk.Frame(header_section)
        header_frame.pack(fill="x")
        
        ttk.Label(header_frame, text="Snippets", font=StandardComponents.TITLE_FONT).pack(side="left")
        
        new_button = StandardComponents.create_button_input(
            header_frame,
            "New",
            self._new_snippet,
            width=8
        )
        new_button.pack(side="right")
        
        # Listbox section
        list_section = StandardComponents.create_section(left_frame, "")
        list_section.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Listbox with scrollbar in grid layout for full space usage
        list_section.grid_rowconfigure(0, weight=1)
        list_section.grid_columnconfigure(0, weight=1)
        
        self.snippets_listbox = tk.Listbox(
            list_section,
            font=StandardComponents.BODY_FONT,
            bg=self.get_theme_color("treeview_bg", "#ffffff"),
            fg=self.get_theme_color("editor_fg", "#000000"),
            selectbackground=self.get_theme_color("sel_bg", "#0078d4"),
            selectforeground=self.get_theme_color("sel_fg", "#ffffff"),
            relief="solid",
            borderwidth=1
        )
        self.snippets_listbox.grid(row=0, column=0, sticky="nsew")
        
        list_scrollbar = ttk.Scrollbar(list_section, orient="vertical", command=self.snippets_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky="ns")
        self.snippets_listbox.config(yscrollcommand=list_scrollbar.set)
        
        # Bind selection event
        self.snippets_listbox.bind("<<ListboxSelect>>", self._on_snippet_selected)
        
        parent.add(left_frame, weight=1)
        
    def _create_snippet_editor(self, parent):
        """Create the snippet editor section."""
        right_frame = ttk.Frame(parent)
        
        # Use standardized sections for consistent layout
        details_section = StandardComponents.create_section(right_frame, "Snippet Details")
        details_section.pack(fill="x", pady=(0, StandardComponents.ELEMENT_SPACING))
        
        # Create form grid inside section
        form_frame = ttk.Frame(details_section)
        form_frame.pack(fill="x")
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)
        
        # Name and Trigger fields in same row
        ttk.Label(form_frame, text="Name:", font=StandardComponents.BODY_FONT).grid(
            row=0, column=0, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=StandardComponents.ELEMENT_SPACING//2)
        self.name_entry = StandardComponents.create_entry_input(form_frame, width=15)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=(0, StandardComponents.PADDING), pady=StandardComponents.ELEMENT_SPACING//2)
        self.name_entry.bind("<KeyRelease>", self._on_field_changed)
        
        ttk.Label(form_frame, text="Trigger:", font=StandardComponents.BODY_FONT).grid(
            row=0, column=2, sticky="w", padx=(0, StandardComponents.ELEMENT_SPACING), pady=StandardComponents.ELEMENT_SPACING//2)
        self.trigger_entry = StandardComponents.create_entry_input(form_frame, width=12)
        self.trigger_entry.grid(row=0, column=3, sticky="ew", pady=StandardComponents.ELEMENT_SPACING//2)
        self.trigger_entry.bind("<KeyRelease>", self._on_field_changed)
        
        # Content section - takes remaining space
        content_section = StandardComponents.create_section(right_frame, "Content")
        content_section.pack(fill="both", expand=True, pady=(0, StandardComponents.ELEMENT_SPACING))
        
        # Content text area
        content_section.grid_rowconfigure(0, weight=1)
        content_section.grid_columnconfigure(0, weight=1)
        
        self.content_text = StandardComponents.create_text_input(content_section, height=20)
        self.content_text.configure(
            font=StandardComponents.CODE_FONT,
            bg=self.get_theme_color("editor_bg", "#ffffff"),
            fg=self.get_theme_color("editor_fg", "#000000"),
            selectbackground=self.get_theme_color("sel_bg", "#0078d4"),
            selectforeground=self.get_theme_color("sel_fg", "#ffffff"),
            insertbackground=self.get_theme_color("editor_insert_bg", "#000000")
        )
        self.content_text.pack(fill="both", expand=True)
        self.content_text.bind("<KeyRelease>", self._on_field_changed)
        
        # Help text
        help_section = ttk.Frame(right_frame)
        help_section.pack(fill="x", pady=(0, StandardComponents.ELEMENT_SPACING))
        
        ttk.Label(
            help_section,
            text="Use ${cursor} to mark cursor position after snippet insertion",
            font=StandardComponents.SMALL_FONT,
            foreground=self.get_theme_color("muted_text", "#666666")
        ).pack(anchor="w")
        
        # Action buttons
        button_section = ttk.Frame(right_frame)
        button_section.pack(fill="x")
        
        button_frame = ttk.Frame(button_section)
        button_frame.pack(fill="x")
        button_frame.grid_columnconfigure(2, weight=1)
        
        self.save_button = StandardComponents.create_button_input(
            button_frame, "Save Snippet", self._save_current_snippet, width=12)
        self.save_button.grid(row=0, column=0, padx=(0, StandardComponents.BUTTON_SPACING))
        
        self.delete_button = StandardComponents.create_button_input(
            button_frame, "Delete", self._delete_current_snippet, width=8)
        self.delete_button.grid(row=0, column=1, padx=(0, StandardComponents.BUTTON_SPACING))
        
        save_all_button = StandardComponents.create_button_input(
            button_frame, "Save All Changes", self._save_all_snippets, width=15)
        save_all_button.grid(row=0, column=3)
        
        parent.add(right_frame, weight=2)
        
    def focus_main_widget(self):
        """Focus the main interactive widget."""
        if self.name_entry:
            self.name_entry.focus_set()
    
    def _populate_listbox(self):
        """Populate the snippets listbox."""
        self.snippets_listbox.delete(0, tk.END)
        
        # Handle both old format (dict key->content) and new format (list of objects)
        if isinstance(self.snippets, dict):
            for trigger, content in self.snippets.items():
                display_text = f"{trigger}"
                self.snippets_listbox.insert(tk.END, display_text)
        else:
            # New format - list of snippet objects
            for snippet in self.snippets:
                name = snippet.get("name", "Unnamed")
                trigger = snippet.get("trigger", "")
                display_text = f"{name} [{trigger}]" if trigger else name
                self.snippets_listbox.insert(tk.END, display_text)
    
    def _on_snippet_selected(self, event):
        """Handle snippet selection."""
        selection = self.snippets_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if isinstance(self.snippets, dict):
            triggers = list(self.snippets.keys())
            if 0 <= index < len(triggers):
                self._load_snippet_from_dict(triggers[index])
        else:
            if 0 <= index < len(self.snippets):
                self._load_snippet(index)
    
    def _load_snippet_from_dict(self, trigger: str):
        """Load a snippet from dict format into the editor."""
        content = self.snippets[trigger]
        
        self.current_snippet_index = list(self.snippets.keys()).index(trigger)
        self.is_editing = True
        
        # Load snippet data (convert from dict format)
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, trigger.capitalize())
        
        self.trigger_entry.delete(0, tk.END)
        self.trigger_entry.insert(0, trigger)
        
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", content)
        
        self._update_button_states()
    
    def _load_snippet(self, index: int):
        """Load a snippet into the editor."""
        snippet = self.snippets[index]
        
        self.current_snippet_index = index
        self.is_editing = True
        
        # Load snippet data
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, snippet.get("name", ""))
        
        self.trigger_entry.delete(0, tk.END)
        self.trigger_entry.insert(0, snippet.get("trigger", ""))
        
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", snippet.get("body", ""))
        
        self._update_button_states()
    
    def _new_snippet(self):
        """Start creating a new snippet."""
        self.current_snippet_index = -1
        self.is_editing = False
        
        # Clear fields
        self.name_entry.delete(0, tk.END)
        self.trigger_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)
        
        # Clear listbox selection
        self.snippets_listbox.selection_clear(0, tk.END)
        
        self._update_button_states()
        self.name_entry.focus_set()
    
    def _save_current_snippet(self):
        """Save the current snippet being edited."""
        name = self.name_entry.get().strip()
        trigger = self.trigger_entry.get().strip()
        content = self.content_text.get("1.0", tk.END + "-1c").strip()
        
        if not name:
            messagebox.showwarning(
                "Missing Name",
                "Please enter a name for the snippet.",
                parent=self.panel_frame
            )
            return
        
        if not trigger:
            messagebox.showwarning(
                "Missing Trigger",
                "Please enter a trigger for the snippet.",
                parent=self.panel_frame
            )
            return
        
        if not content:
            messagebox.showwarning(
                "Missing Content",
                "Please enter content for the snippet.",
                parent=self.panel_frame
            )
            return
        
        # Validate trigger format (no spaces, special chars)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', trigger):
            messagebox.showwarning(
                "Invalid Trigger",
                "Trigger must be alphanumeric and start with a letter or underscore.",
                parent=self.panel_frame
            )
            return
        
        # Check for duplicate triggers
        if isinstance(self.snippets, dict):
            # Dict format - simple check
            if trigger in self.snippets and not (self.is_editing and self.trigger_entry.get() == trigger):
                messagebox.showwarning(
                    "Duplicate Trigger",
                    f"A snippet with trigger '{trigger}' already exists.",
                    parent=self.panel_frame
                )
                return
            
            # Save in dict format
            old_trigger = None
            if self.is_editing:
                triggers = list(self.snippets.keys())
                if 0 <= self.current_snippet_index < len(triggers):
                    old_trigger = triggers[self.current_snippet_index]
                    
            # Remove old entry if trigger changed
            if old_trigger and old_trigger != trigger:
                del self.snippets[old_trigger]
                
            # Add/update snippet
            self.snippets[trigger] = content
            debug_console.log(f"Saved snippet: {trigger}", level='ACTION')
        else:
            # List format - check all snippets
            for i, snippet in enumerate(self.snippets):
                if i != self.current_snippet_index and snippet.get("trigger") == trigger:
                    messagebox.showwarning(
                        "Duplicate Trigger",
                        f"A snippet with trigger '{trigger}' already exists.",
                        parent=self.panel_frame
                    )
                    return
            
            # Create snippet data
            snippet_data = {
                "name": name,
                "trigger": trigger,
                "body": content,
                "description": f"Custom snippet: {name}"
            }
            
            if self.is_editing and 0 <= self.current_snippet_index < len(self.snippets):
                # Update existing snippet
                self.snippets[self.current_snippet_index] = snippet_data
                debug_console.log(f"Updated snippet: {name}", level='ACTION')
            else:
                # Add new snippet
                self.snippets.append(snippet_data)
                debug_console.log(f"Added new snippet: {name}", level='ACTION')
                self.current_snippet_index = len(self.snippets) - 1
                self.is_editing = True
        
        # Refresh listbox
        self._populate_listbox()
        
        # Select the saved snippet
        self.snippets_listbox.selection_set(self.current_snippet_index)
        
        self._update_button_states()
        
        # Show success message briefly
        original_text = self.save_button.cget("text")
        self.save_button.config(text="Saved!")
        self.panel_frame.after(1500, lambda: (
            self.save_button.config(text=original_text)
            if self.save_button and self.save_button.winfo_exists() else None
        ))
    
    def _delete_current_snippet(self):
        """Delete the currently selected snippet."""
        if not self.is_editing or self.current_snippet_index < 0:
            return
        
        if isinstance(self.snippets, dict):
            triggers = list(self.snippets.keys())
            if 0 <= self.current_snippet_index < len(triggers):
                trigger = triggers[self.current_snippet_index]
                result = messagebox.askyesno(
                    "Delete Snippet",
                    f"Are you sure you want to delete the snippet '{trigger}'?",
                    parent=self.panel_frame
                )
                
                if result:
                    del self.snippets[trigger]
                    debug_console.log(f"Deleted snippet: {trigger}", level='ACTION')
        else:
            snippet_name = self.snippets[self.current_snippet_index].get("name", "Unnamed")
            
            result = messagebox.askyesno(
                "Delete Snippet",
                f"Are you sure you want to delete the snippet '{snippet_name}'?",
                parent=self.panel_frame
            )
            
            if result:
                del self.snippets[self.current_snippet_index]
                debug_console.log(f"Deleted snippet: {snippet_name}", level='ACTION')
        
        self._populate_listbox()
        self._new_snippet()
    
    def _save_all_snippets(self):
        """Save all snippets to file."""
        if self.save_callback:
            self.save_callback(self.snippets)
            
        debug_console.log(f"Saved {len(self.snippets)} snippets to file", level='SUCCESS')
        
        messagebox.showinfo(
            "Snippets Saved",
            f"Successfully saved {len(self.snippets)} snippets.",
            parent=self.panel_frame
        )
    
    def _update_button_states(self):
        """Update button states based on current context."""
        if self.is_editing:
            self.save_button.config(state="normal")
            self.delete_button.config(state="normal")
        else:
            self.save_button.config(state="normal")  # Can save new snippet
            self.delete_button.config(state="disabled")
    
    def _on_field_changed(self, event=None):
        """Handle field change events."""
        # Enable save button when fields are modified
        self.save_button.config(state="normal")