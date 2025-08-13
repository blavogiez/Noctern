import tkinter as tk
from tkinter import ttk
import time
import hashlib
from utils import debug_console

class Outline:
    """
    Simple document outline manager.
    Displays sections with arrows and allows navigation.
    """
    def __init__(self, parent_frame, get_current_tab_callback):
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
        
        # Configure styles
        self._configure_styles()
        
        # When clicking on a section
        self.tree.bind("<<TreeviewSelect>>", self._on_click_section)
        self.tree.bind("<Button-1>", self._on_single_click)
        
        # Monaco-style optimization cache
        self._last_content_hash = None
        self._last_update_time = 0
        self._update_cooldown = 1.0  # Minimum 1 second between updates
        
    def _configure_styles(self):
        """Configure the styles for the outline Treeview and title."""
        # Style for the Treeview
        style = ttk.Style()
        style.configure("NoPlus.Treeview", 
                       rowheight=28,  # Increased row height for better readability
                       font=("Arial", 10))  # Use a cleaner font
        # Hide + and - symbols
        style.layout("NoPlus.Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        
        # Style for the title
        title_style = ttk.Style()
        title_style.configure("Title.TLabel", 
                             font=("Arial", 11, "bold"),  # Bold title with better font
                             foreground=title_style.lookup("TLabel", "foreground"))  # Use theme's foreground color

    def get_widget(self):
        """Returns the frame containing the title and Treeview widget."""
        return self.frame

    def _on_click_section(self, event):
        """Navigate to selected section in the editor."""
        current_tab = self.get_current_tab_callback()
        if not current_tab or not hasattr(current_tab, 'editor'):
            return
        
        selected = self.tree.selection()
        if not selected:
            return

        # Get line number
        values = self.tree.item(selected[0], "values")
        if values:
            line_number = values[0]
            editor = current_tab.editor
            editor.yview(f"{line_number}.0")
            editor.mark_set("insert", f"{line_number}.0")
            editor.focus()

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
            
            # Quick content hash using only first 1000 chars + length
            # Monaco-style: avoid hashing entire content
            content_sample = content[:1000] + str(len(content))
            content_hash = hashlib.md5(content_sample.encode('utf-8', errors='ignore')).hexdigest()[:16]
            
            # Skip update if content hasn't changed
            if content_hash == self._last_content_hash:
                return  # No change - skip expensive update
            
            # Only update if we see section-related changes
            if self._last_content_hash and not self._has_structural_changes(content):
                return  # No structural changes - keep current outline
                
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
        """Quick check if content has structural changes (sections added/removed)."""
        # Count sections quickly
        section_count = content.count('\\section{') + content.count('\\subsection{') + content.count('\\subsubsection{')
        
        # Store previous count for comparison
        if not hasattr(self, '_last_section_count'):
            self._last_section_count = 0
        
        has_changes = section_count != self._last_section_count
        self._last_section_count = section_count
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