"""
Rendu visuel des différences avec interface Tkinter.
Respecte le principe de responsabilité unique (Single Responsibility Principle).
"""

import tkinter as tk
from tkinter import ttk, font
from typing import List, Callable, Optional, Dict
from ..interfaces.diff_generator import DiffLine, DiffType
from ..interfaces.ui_presenter import IDiffViewer

class TkinterDiffViewer(IDiffViewer):
    """Visualiseur de différences utilisant Tkinter."""
    
    def __init__(self, parent_window=None):
        """
        Initialise le visualiseur de différences.
        
        Args:
            parent_window: Fenêtre parent (optionnel)
        """
        self.parent_window = parent_window
        self.navigation_callback = None
        self.diff_window = None
        
        # Configuration des couleurs
        self.colors = {
            DiffType.ADDITION: {"bg": "#d4edda", "fg": "#155724"},
            DiffType.DELETION: {"bg": "#f8d7da", "fg": "#721c24"},
            DiffType.MODIFICATION: {"bg": "#fff3cd", "fg": "#856404"},
            DiffType.UNCHANGED: {"bg": "white", "fg": "black"}
        }
        
        # Police monospace pour le code
        self.code_font = None
    
    def display_side_by_side(self, old_content: str, new_content: str, 
                           diff_lines: List[DiffLine]) -> None:
        """Affiche les différences côte à côte."""
        if self.diff_window and self.diff_window.winfo_exists():
            self.diff_window.lift()
            return
        
        self._create_diff_window()
        self._setup_side_by_side_layout(old_content, new_content, diff_lines)
    
    def highlight_critical_changes(self, critical_lines: List[DiffLine]) -> None:
        """Met en surbrillance les changements critiques."""
        if not hasattr(self, 'left_text') or not hasattr(self, 'right_text'):
            return
        
        # Ajouter un tag pour les changements critiques
        for widget in [self.left_text, self.right_text]:
            widget.tag_configure("critical", background="#ff6b6b", foreground="white", font=self.code_font)
        
        # Appliquer le tag aux lignes critiques
        for line in critical_lines:
            line_start = f"{line.line_number}.0"
            line_end = f"{line.line_number}.end"
            
            if line.diff_type in [DiffType.DELETION, DiffType.MODIFICATION]:
                if hasattr(self, 'left_text'):
                    self.left_text.tag_add("critical", line_start, line_end)
            
            if line.diff_type in [DiffType.ADDITION, DiffType.MODIFICATION]:
                if hasattr(self, 'right_text'):
                    self.right_text.tag_add("critical", line_start, line_end)
    
    def set_navigation_callback(self, callback: Callable[[int], None]) -> None:
        """Définit le callback pour naviguer vers une ligne."""
        self.navigation_callback = callback
    
    def _create_diff_window(self):
        """Crée la fenêtre de diff."""
        self.diff_window = tk.Toplevel(self.parent_window)
        self.diff_window.title("Comparaison avec la dernière version compilée")
        self.diff_window.geometry("1200x800")
        
        # Configuration de la police
        try:
            self.code_font = font.Font(family="Consolas", size=10)
        except:
            self.code_font = font.Font(family="Courier", size=10)
        
        # Toolbar
        self._create_toolbar()
        
        # Frame principal avec scrollbars
        main_frame = ttk.Frame(self.diff_window)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configuration du grid
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        self.main_frame = main_frame
    
    def _create_toolbar(self):
        """Crée la barre d'outils."""
        toolbar = ttk.Frame(self.diff_window)
        toolbar.pack(fill="x", padx=5, pady=2)
        
        # Boutons de navigation
        ttk.Button(toolbar, text="Changement précédent", 
                  command=self._go_to_previous_change).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Changement suivant", 
                  command=self._go_to_next_change).pack(side="left", padx=2)
        
        ttk.Separator(toolbar, orient="vertical").pack(side="left", padx=10, fill="y")
        
        # Options d'affichage
        self.show_unchanged = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="Afficher lignes inchangées", 
                       variable=self.show_unchanged,
                       command=self._refresh_display).pack(side="left", padx=5)
        
        # Statistiques
        self.stats_label = ttk.Label(toolbar, text="")
        self.stats_label.pack(side="right", padx=5)
    
    def _setup_side_by_side_layout(self, old_content: str, new_content: str, 
                                  diff_lines: List[DiffLine]):
        """Configure l'affichage côte à côte."""
        # Headers
        ttk.Label(self.main_frame, text="Dernière version compilée", 
                 font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(self.main_frame, text="Version actuelle", 
                 font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # Frames pour les textes avec scrollbars
        left_frame = ttk.Frame(self.main_frame)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 2))
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=1)
        
        right_frame = ttk.Frame(self.main_frame)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(2, 0))
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)
        
        # Widgets Text avec numéros de ligne
        self.left_text = tk.Text(left_frame, font=self.code_font, wrap="none", 
                                state="disabled", cursor="arrow")
        self.left_text.grid(row=0, column=1, sticky="nsew")
        
        self.right_text = tk.Text(right_frame, font=self.code_font, wrap="none", 
                                 state="disabled", cursor="arrow")
        self.right_text.grid(row=0, column=1, sticky="nsew")
        
        # Numéros de ligne
        self.left_line_numbers = tk.Text(left_frame, font=self.code_font, width=4, 
                                        state="disabled", cursor="arrow")
        self.left_line_numbers.grid(row=0, column=0, sticky="ns")
        
        self.right_line_numbers = tk.Text(right_frame, font=self.code_font, width=4, 
                                         state="disabled", cursor="arrow")
        self.right_line_numbers.grid(row=0, column=0, sticky="ns")
        
        # Scrollbars
        left_scroll = ttk.Scrollbar(left_frame, orient="vertical")
        left_scroll.grid(row=0, column=2, sticky="ns")
        
        right_scroll = ttk.Scrollbar(right_frame, orient="vertical")
        right_scroll.grid(row=0, column=2, sticky="ns")
        
        # Configuration des scrollbars
        self._configure_scrollbars(left_scroll, right_scroll)
        
        # Remplir le contenu
        self._populate_diff_content(old_content, new_content, diff_lines)
        
        # Bindings pour navigation
        self._setup_navigation_bindings()
        
        # Afficher les statistiques
        self._update_statistics(diff_lines)
        
        # Stocker les diff_lines pour navigation
        self.diff_lines = diff_lines
        self.current_change_index = 0
    
    def _configure_scrollbars(self, left_scroll, right_scroll):
        """Configure la synchronisation des scrollbars."""
        def sync_scroll(*args):
            self.left_text.yview(*args)
            self.left_line_numbers.yview(*args)
            self.right_text.yview(*args)
            self.right_line_numbers.yview(*args)
        
        left_scroll.configure(command=sync_scroll)
        right_scroll.configure(command=sync_scroll)
        
        for text_widget in [self.left_text, self.right_text]:
            text_widget.configure(yscrollcommand=lambda *args, s=left_scroll: s.set(*args))
    
    def _populate_diff_content(self, old_content: str, new_content: str, diff_lines: List[DiffLine]):
        """Remplit le contenu des deux panneaux."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        # Activer l'édition temporairement
        for widget in [self.left_text, self.right_text, self.left_line_numbers, self.right_line_numbers]:
            widget.configure(state="normal")
            widget.delete("1.0", "end")
        
        # Configurer les tags de couleur
        for widget in [self.left_text, self.right_text]:
            for diff_type, color_config in self.colors.items():
                tag_name = diff_type.value
                widget.tag_configure(tag_name, **color_config, font=self.code_font)
        
        left_line_num = 1
        right_line_num = 1
        
        # Traiter chaque ligne de diff
        for diff_line in diff_lines:
            tag_name = diff_line.diff_type.value
            
            if diff_line.diff_type == DiffType.UNCHANGED:
                if self.show_unchanged.get():
                    # Afficher dans les deux panneaux
                    self.left_text.insert("end", diff_line.content + "\n", tag_name)
                    self.left_line_numbers.insert("end", f"{left_line_num:>3}\n")
                    
                    self.right_text.insert("end", diff_line.content + "\n", tag_name)
                    self.right_line_numbers.insert("end", f"{right_line_num:>3}\n")
                    
                    left_line_num += 1
                    right_line_num += 1
            
            elif diff_line.diff_type == DiffType.DELETION:
                self.left_text.insert("end", diff_line.content + "\n", tag_name)
                self.left_line_numbers.insert("end", f"{left_line_num:>3}\n")
                left_line_num += 1
            
            elif diff_line.diff_type == DiffType.ADDITION:
                self.right_text.insert("end", diff_line.content + "\n", tag_name)
                self.right_line_numbers.insert("end", f"{right_line_num:>3}\n")
                right_line_num += 1
            
            elif diff_line.diff_type == DiffType.MODIFICATION:
                self.right_text.insert("end", diff_line.content + "\n", tag_name)
                self.right_line_numbers.insert("end", f"{right_line_num:>3}\n")
                right_line_num += 1
        
        # Désactiver l'édition
        for widget in [self.left_text, self.right_text, self.left_line_numbers, self.right_line_numbers]:
            widget.configure(state="disabled")
    
    def _setup_navigation_bindings(self):
        """Configure les bindings pour la navigation."""
        for widget in [self.left_text, self.right_text]:
            widget.bind("<Double-Button-1>", self._on_double_click)
    
    def _on_double_click(self, event):
        """Gère le double-clic pour navigation."""
        widget = event.widget
        line_index = widget.index("@%s,%s" % (event.x, event.y)).split(".")[0]
        
        if self.navigation_callback:
            try:
                line_num = int(line_index)
                self.navigation_callback(line_num)
            except ValueError:
                pass
    
    def _go_to_previous_change(self):
        """Navigue vers le changement précédent."""
        if not hasattr(self, 'diff_lines'):
            return
        
        changes = [i for i, line in enumerate(self.diff_lines) 
                  if line.diff_type != DiffType.UNCHANGED]
        
        if changes and self.current_change_index > 0:
            self.current_change_index -= 1
            self._highlight_current_change(changes[self.current_change_index])
    
    def _go_to_next_change(self):
        """Navigue vers le changement suivant."""
        if not hasattr(self, 'diff_lines'):
            return
        
        changes = [i for i, line in enumerate(self.diff_lines) 
                  if line.diff_type != DiffType.UNCHANGED]
        
        if changes and self.current_change_index < len(changes) - 1:
            self.current_change_index += 1
            self._highlight_current_change(changes[self.current_change_index])
    
    def _highlight_current_change(self, line_index):
        """Met en surbrillance le changement actuel."""
        # Implementation de la mise en surbrillance
        pass
    
    def _refresh_display(self):
        """Rafraîchit l'affichage après changement d'options."""
        if hasattr(self, 'diff_lines'):
            # Re-remplir le contenu avec les nouvelles options
            old_content = "\n".join(line.content for line in self.diff_lines if line.diff_type == DiffType.DELETION)
            new_content = "\n".join(line.content for line in self.diff_lines if line.diff_type == DiffType.ADDITION)
            self._populate_diff_content(old_content, new_content, self.diff_lines)
    
    def _update_statistics(self, diff_lines: List[DiffLine]):
        """Met à jour les statistiques affichées."""
        from ..diff.text_diff_generator import LaTeXDiffGenerator
        generator = LaTeXDiffGenerator()
        stats = generator.get_diff_statistics(diff_lines)
        
        stats_text = f"Ajouts: {stats['additions']} | Suppressions: {stats['deletions']} | Modifications: {stats['modifications']}"
        self.stats_label.configure(text=stats_text)