import tkinter as tk
from tkinter import ttk
import time
import hashlib
from utils import logs_console
from app.config import get_treeview_font_settings

class Outline:
    """
    Simple document outline manager.
    Display sections with arrows and allow navigation.
    """
    def __init__(self, parent_frame, get_current_tab_callback, config_settings=None):
        # Create a frame to contain the title and treeview
        self.frame = ttk.Frame(parent_frame)
        self.frame.pack(fill="both", expand=True)
        
        # Create a frame for the title with tab-like styling
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(side="top", fill="x", padx=2, pady=(2, 2))
        
        self.title = ttk.Label(
            title_frame, 
            text="Document outline",
            style="Title.TLabel",
            anchor="w"  # Align left
        )
        self.title.pack(side="top", fill="x", ipady=3, padx=(6, 6))  # Adjusted padding to match tabs
        
        # Create Treeview without + and - symbols
        self.tree = ttk.Treeview(self.frame, show="tree", selectmode="browse")
        self.tree.pack(side="top", fill="both", expand=True)
        self.tree.configure(style="NoPlus.Treeview")
        
        # Callback to get current tab
        self.get_current_tab_callback = get_current_tab_callback
        
        # Store config settings for font configuration
        self.config_settings = config_settings
        
        # Configure styles
        self._configure_styles()
        
        # When clicking on a section
        self.tree.bind("<<TreeviewSelect>>", self._on_click_section)
        self.tree.bind("<Button-1>", self._on_single_click)
        
        # Monaco-style optimization cache
        self._last_content_hash = None
        self._last_update_time = 0
        self._update_cooldown = 0.3  # Reduced to 300ms for more responsive updates
        self._last_section_hash = None  # Hash of just section lines for better change detection
        self._bound_editor = None  # Track which editor we're bound to
        self._update_scheduled = False  # Prevent multiple scheduled updates
        
    def _configure_styles(self):
        """Configure styles for outline Treeview and title."""
        # Get validated font settings from config
        if self.config_settings:
            font_settings = get_treeview_font_settings(self.config_settings)
            treeview_font_family = font_settings["family"]
            treeview_font_size = font_settings["size"]
            treeview_row_height = font_settings["row_height"]
        else:
            treeview_font_family = "Segoe UI"
            treeview_font_size = 10
            treeview_row_height = 30
        
        # Style for the Treeview
        style = ttk.Style()
        style.configure("NoPlus.Treeview", 
                       rowheight=treeview_row_height,  
                       font=(treeview_font_family, treeview_font_size))
        # Hide + and - symbols
        style.layout("NoPlus.Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        
        # Style for the title with unified font
        title_style = ttk.Style()
        title_style.configure("Title.TLabel", 
                             font=("Segoe UI", 9),
                             foreground=title_style.lookup("TLabel", "foreground"))  # Use theme's foreground color

    def get_widget(self):
        """Return frame containing title and Treeview widget."""
        return self.frame

    def _on_click_section(self, event):
        """Navigate to selected section using dynamic search."""
        current_tab = self.get_current_tab_callback()
        if not current_tab or not hasattr(current_tab, 'editor'):
            return
        
        selected = self.tree.selection()
        if not selected:
            return

        # Get section title from the selected item
        item_id = selected[0]
        section_title = self._get_section_info_from_item(item_id)
        
        if not section_title:
            return
            
        # Get current content from editor
        editor = current_tab.editor
        try:
            content = editor.get("1.0", tk.END)
            
            # Find the section dynamically in current content
            line_number = self._find_section_in_content(content, section_title)
            
            if line_number:
                # Navigate to the found line
                editor.yview(f"{line_number}.0")
                editor.mark_set("insert", f"{line_number}.0")
                editor.focus()
            else:
                # Fallback to original behavior if dynamic search fails
                values = self.tree.item(item_id, "values")
                if values:
                    fallback_line = values[0]
                    editor.yview(f"{fallback_line}.0")
                    editor.mark_set("insert", f"{fallback_line}.0")
                    editor.focus()
                    
        except tk.TclError:
            # Widget might be destroyed
            pass

    def _on_single_click(self, event):
        """Open/close sections when clicked."""
        item = self.tree.identify('item', event.x, event.y)
        if item and self.tree.get_children(item):
            # If section has children, toggle open/close
            if self.tree.item(item, 'open'):
                self.tree.item(item, open=False)
                self._update_arrow(item, False)
            else:
                self.tree.item(item, open=True)
                self._update_arrow(item, True)

    def _update_arrow(self, item, is_open):
        """Update arrow (▶ or ▼)."""
        text = self.tree.item(item, "text")
        
        if is_open:
            # Change ▶ to ▼
            if text.startswith("▶"):
                new_text = "▼" + text[1:]
                self.tree.item(item, text=new_text)
        else:
            # Change ▼ to ▶
            if text.startswith("▼"):
                new_text = "▶" + text[1:]
                self.tree.item(item, text=new_text)

    def _find_sections(self, text_content):
        """Find all sections in the text."""
        lines = text_content.split("\n")
        sections = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Look for \section{title}
            if line.startswith("\\section{"):
                title = self._extract_title(line, "\\section{")
                if title:
                    sections.append(("section", title, line_num + 1, []))
            
            # Look for \subsection{title}
            elif line.startswith("\\subsection{"):
                title = self._extract_title(line, "\\subsection{")
                if title:
                    sections.append(("subsection", title, line_num + 1, []))
            
            # Look for \subsubsection{title}
            elif line.startswith("\\subsubsection{"):
                title = self._extract_title(line, "\\subsubsection{")
                if title:
                    sections.append(("subsubsection", title, line_num + 1, []))
        
        return self._organize_hierarchy(sections)

    def _extract_title(self, line, command):
        """Extract title from a LaTeX line."""
        # Remove command from beginning
        line = line[len(command):]
        # Find closing brace
        end = line.find('}')
        if end == -1:
            return None
        return line[:end].strip()

    def _organize_hierarchy(self, sections):
        """Organize sections in hierarchy."""
        result = []
        stack = [(result, "")]  # (current_list, parent_level)
        
        for section_type, title, line_num, children in sections:
            # Move up in stack according to level
            if section_type == "section":
                stack = [(result, "")]
            elif section_type == "subsection":
                # Keep only up to section level
                stack = [item for item in stack if item[1] in ["", "section"]]
            elif section_type == "subsubsection":
                # Keep up to subsection level
                stack = [item for item in stack if item[1] in ["", "section", "subsection"]]
            
            # Add to current list
            new_item = (title, line_num, [])
            stack[-1][0].append(new_item)
            stack.append((new_item[2], section_type))
        
        return result

    def bind_to_editor(self, editor_widget):
        """Bind outline updates to editor events for real-time updates."""
        if self._bound_editor == editor_widget:
            return  # Already bound
            
        # Unbind from previous editor if any
        if self._bound_editor:
            try:
                self._bound_editor.unbind("<<Modified>>", self._editor_modified_tag)
            except (tk.TclError, AttributeError):
                pass
        
        # Bind to new editor
        self._bound_editor = editor_widget
        if editor_widget:
            # Generate a unique tag for this binding
            self._editor_modified_tag = f"outline_update_{id(self)}"
            editor_widget.bind("<<Modified>>", self._on_editor_modified, add='+')
            editor_widget.bind("<KeyRelease>", self._on_key_release, add='+')

    def _on_editor_modified(self, event):
        """Handle editor modification events."""
        if self._update_scheduled:
            return
        
        # Schedule update with delay to avoid rapid fire updates
        self._update_scheduled = True
        if hasattr(self, 'frame') and self.frame.winfo_exists():
            self.frame.after(300, self._delayed_update)

    def _on_key_release(self, event):
        """Handle key release events for more responsive section detection."""
        # Only trigger on potential section-related keys
        if event.keysym in ['braceright', 'Return', 'BackSpace', 'Delete']:
            # Check if we're potentially in a section context
            try:
                editor = event.widget
                cursor_pos = editor.index(tk.INSERT)
                line_start = f"{cursor_pos.split('.')[0]}.0"
                line_end = f"{cursor_pos.split('.')[0]}.end"
                current_line = editor.get(line_start, line_end).strip()
                
                # If current line contains section-related LaTeX commands, force immediate update
                if ('\\section{' in current_line or '\\subsection{' in current_line or 
                    '\\subsubsection{' in current_line):
                    self.force_update(editor)
                else:
                    self._on_editor_modified(event)
            except (tk.TclError, AttributeError):
                self._on_editor_modified(event)

    def _delayed_update(self):
        """Perform delayed outline update."""
        self._update_scheduled = False
        current_tab = self.get_current_tab_callback()
        if current_tab and hasattr(current_tab, 'editor'):
            self.update_outline(current_tab.editor)

    def force_update(self, editor_widget=None):
        """Force immediate outline update, bypassing cooldowns."""
        if not editor_widget:
            current_tab = self.get_current_tab_callback()
            if current_tab and hasattr(current_tab, 'editor'):
                editor_widget = current_tab.editor
        
        if editor_widget:
            # Reset cooldown and force update
            self._last_update_time = 0
            self._last_content_hash = None
            self._last_section_hash = None
            self.update_outline(editor_widget)

    def _get_section_info_from_item(self, item_id):
        """Extract section type and title from a treeview item."""
        text = self.tree.item(item_id, "text")
        
        # Remove arrow and numbering to get clean title
        if text.startswith("▶") or text.startswith("▼"):
            text = text[1:].strip()
        
        # Remove numbering (e.g., "1.2.3 Title" -> "Title")
        # Look for pattern: numbers followed by dots, then space, then title
        import re
        match = re.match(r'^[\d\.]+\s+(.+)$', text)
        if match:
            title = match.group(1).strip()
        else:
            title = text.strip()
            
        return title

    def _find_section_in_content(self, content, title):
        """Find the current line number of a section by its title in the editor content."""
        lines = content.split("\n")
        
        # Normalize the search title (remove extra spaces, convert to lower for comparison)
        normalized_title = ' '.join(title.split()).lower()
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for section commands
            for command in ["\\section{", "\\subsection{", "\\subsubsection{"]:
                if line_stripped.startswith(command):
                    # Extract title from the line
                    line_title = self._extract_title_fast(line_stripped, command)
                    if line_title:
                        # Normalize the line title for comparison
                        normalized_line_title = ' '.join(line_title.split()).lower()
                        if normalized_line_title == normalized_title:
                            return line_num + 1  # +1 for 1-based indexing
        
        return None

    def _add_to_tree(self, parent_id, items, prefix=""):
        """Add items to the Treeview."""
        for i, (title, line_num, children) in enumerate(items):
            number = f"{prefix}{i + 1}."
            
            # Add arrow if there are children
            if children:
                display_text = f"▶ {number} {title}"
            else:
                display_text = f"{number} {title}"
            
            # Create the item
            item_id = self.tree.insert(parent_id, "end", text=display_text, values=(line_num,))
            
            # Add children
            if children:
                self._add_to_tree(item_id, children, prefix=number)

    def update_outline(self, editor_widget):
        """Monaco-style ultra-fast outline updates with aggressive caching."""
        if not editor_widget:
            self.tree.delete(*self.tree.get_children())
            return
        
        # Ensure we're bound to this editor for real-time updates
        self.bind_to_editor(editor_widget)
        
        # Monaco-style: Skip update if too frequent
        current_time = time.time()
        if current_time - self._last_update_time < self._update_cooldown:
            return  # Skip this update - too frequent
        
        try:
            # Ultra-fast content hash check
            content = editor_widget.get("1.0", tk.END)
            if not content.strip():
                self.tree.delete(*self.tree.get_children())
                self._last_content_hash = None
                return
            
            # Check for structural changes first (most important)
            if not self._has_structural_changes(content):
                return  # No structural changes - keep current outline
            
            # Quick content hash using section-relevant parts + length
            # Include areas where sections are likely to appear
            content_sample = content[:2000] + content[-1000:] + str(len(content))
            content_hash = hashlib.md5(content_sample.encode('utf-8', errors='ignore')).hexdigest()[:16]
            
            # Skip update if content hasn't changed (backup check)
            if content_hash == self._last_content_hash:
                return  # No change - skip expensive update
                
            self._last_content_hash = content_hash
            self._last_update_time = current_time
            
            # Find sections efficiently
            sections = self._find_sections_fast(content)
            
            # Update tree
            self.tree.delete(*self.tree.get_children())
            self._add_to_tree("", sections)
            
        except tk.TclError:
            # Widget might be destroyed
            pass
    
    def _has_structural_changes(self, content):
        """Quick check if content has structural changes (sections added/removed/modified)."""
        # Extract just the section lines for comparison
        lines = content.split('\n')
        section_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            if (line_stripped.startswith('\\section{') or 
                line_stripped.startswith('\\subsection{') or 
                line_stripped.startswith('\\subsubsection{')):
                section_lines.append(line_stripped)
        
        # Create hash of section lines only
        section_content = '\n'.join(section_lines)
        section_hash = hashlib.md5(section_content.encode('utf-8', errors='ignore')).hexdigest()[:16]
        
        # Compare with last known section hash
        has_changes = section_hash != self._last_section_hash
        self._last_section_hash = section_hash
        
        return has_changes
    
    def _find_sections_fast(self, content):
        """Ultra-fast section finding - Monaco optimized."""
        sections = []
        lines = content.split('\n')
        
        # Only check lines that might contain sections
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Quick checks first
            if not line_stripped or not line_stripped.startswith('\\'):
                continue
                
            # Fast section detection
            if line_stripped.startswith('\\section{'):
                title = self._extract_title_fast(line_stripped, '\\section{')
                if title:
                    sections.append(("section", title, line_num + 1, []))
            elif line_stripped.startswith('\\subsection{'):
                title = self._extract_title_fast(line_stripped, '\\subsection{')
                if title:
                    sections.append(("subsection", title, line_num + 1, []))
            elif line_stripped.startswith('\\subsubsection{'):
                title = self._extract_title_fast(line_stripped, '\\subsubsection{')
                if title:
                    sections.append(("subsubsection", title, line_num + 1, []))
        
        return self._organize_sections_fast(sections)
    
    def _extract_title_fast(self, line, prefix):
        """Fast title extraction without regex."""
        try:
            start = line.find(prefix)
            if start == -1:
                return None
            
            start += len(prefix)
            end = line.find('}', start)
            
            if end == -1:
                return None
                
            title = line[start:end].strip()
            return title[:50] if title else None  # Limit title length
            
        except (IndexError, ValueError):
            return None
    
    def _organize_sections_fast(self, sections):
        """Fast organization of sections into hierarchical structure."""
        if not sections:
            return []
            
        result = []
        stack = [(result, "")]  # (current_list, section_type)
        
        for section_type, title, line_num, _ in sections:
            # Maintain proper hierarchy
            if section_type == "section":
                stack = [(result, "")]
            elif section_type == "subsection":
                # Keep up to section level
                stack = [item for item in stack if item[1] in ["", "section"]]
            elif section_type == "subsubsection":
                # Keep up to subsection level  
                stack = [item for item in stack if item[1] in ["", "section", "subsection"]]
            
            # Add to current list
            new_item = (title, line_num, [])
            stack[-1][0].append(new_item)
            stack.append((new_item[2], section_type))
        
        return result