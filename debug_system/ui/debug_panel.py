"""
Panel de debug ultra-rapide avec comparaison de versions.
Respecte le principe de responsabilité unique (Single Responsibility Principle).
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
from ..interfaces.error_detector import LaTeXError, ErrorSeverity
from ..interfaces.ui_presenter import IDebugPresenter

class UltraFastDebugPanel(ttk.Frame, IDebugPresenter):
    """Panel de debug intégré avec fonctionnalités avancées."""
    
    def __init__(self, parent, on_goto_line: Callable[[int], None] = None,
                 on_show_diff: Callable[[], None] = None):
        """
        Initialise le panel de debug.
        
        Args:
            parent: Widget parent
            on_goto_line: Callback pour navigation vers une ligne
            on_show_diff: Callback pour afficher la comparaison
        """
        super().__init__(parent)
        self.on_goto_line = on_goto_line
        self.on_show_diff = on_show_diff
        self.errors: List[LaTeXError] = []
        self.has_last_version = False
        
        print(f"DEBUG: Panel initialized with on_show_diff={self.on_show_diff is not None}")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        # Header avec titre et bouton de diff
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=2, pady=(2, 0))
        
        # Titre
        self.title_label = ttk.Label(
            header_frame,
            text="Debug",
            style="Title.TLabel",
            anchor="w"
        )
        self.title_label.pack(side="left", fill="x", expand=True, padx=(6, 0))
        
        # Bouton de comparaison - configuration simplifiée
        self.diff_button = ttk.Button(header_frame)
        self.diff_button.configure(
            text="Compare with last version",
            command=self._on_diff_button_click,
            state="normal"
        )
        self.diff_button.pack(side="right", padx=(5, 6))
        print("DEBUG: Button created and configured")
        
        # Separator
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", padx=2, pady=2)
        
        # Status frame - simplifié
        status_frame = ttk.Frame(self)
        status_frame.pack(fill="x", padx=5, pady=2)
        
        self.status_label = ttk.Label(
            status_frame,
            text="Ready for debugging",
            foreground="blue"
        )
        self.status_label.pack(side="left")
        
        # Placeholder pour le contenu (vide pour l'instant)
        content_frame = ttk.Frame(self)
        content_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        placeholder_label = ttk.Label(
            content_frame,
            text="Click 'Compare with last version' to debug compilation issues",
            foreground="#666",
            font=("Arial", 9)
        )
        placeholder_label.pack(expand=True)
    
    def update_errors(self, errors: List[LaTeXError], has_last_version: bool = False):
        """
        Met à jour l'état du debug panel.
        
        Args:
            errors: Liste des erreurs détectées (ignorée pour l'instant)
            has_last_version: True si une version précédente existe
        """
        self.has_last_version = has_last_version
        
        # Mettre à jour l'état du bouton diff - TOUJOURS ACTIVÉ POUR TEST
        self.diff_button.configure(state="normal")
        print(f"DEBUG: Button state set to normal, has_last_version={has_last_version}")
        
        # Mettre à jour le status
        if has_last_version:
            self._update_status("Debug available - click Compare button", "green")
        else:
            self._update_status("No previous version for comparison", "orange")
    
    
    def _update_status(self, message: str, color: str):
        """Met à jour le message de status."""
        self.status_label.configure(text=message, foreground=color)
    
    
    def _on_diff_button_click(self):
        """Gère le clic sur le bouton de diff."""
        print("DEBUG: Bouton clicked!")
        
        # Test simple avec messagebox pour voir si le bouton répond
        try:
            import tkinter.messagebox as mb
            mb.showinfo("Debug", "Button clicked! This proves the button works.")
            print("DEBUG: Messagebox shown")
        except:
            print("DEBUG: Cannot show messagebox")
        
        if self.on_show_diff:
            print("DEBUG: Calling on_show_diff callback...")
            try:
                self.on_show_diff()
                print("DEBUG: Callback executed successfully")
            except Exception as e:
                print(f"DEBUG: Error in callback: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("DEBUG: No on_show_diff callback available")
    
    
    # Implémentation de l'interface IDebugPresenter
    def show_diff_comparison(self, diff_lines, title: str = "Document Diff") -> None:
        """Affiche une comparaison visuelle des différences."""
        # Cette méthode sera appelée par le coordinateur
        pass
    
    def show_error_list(self, errors: List[LaTeXError], on_error_click: Callable[[int], None] = None) -> None:
        """Affiche la liste des erreurs détectées."""
        # Ne fait rien - on n'affiche plus les erreurs
        pass
    
    def show_debug_panel(self, has_last_version: bool = False) -> None:
        """Affiche le panel de debug principal."""
        self.has_last_version = has_last_version
        self.diff_button.configure(
            state="normal" if has_last_version else "disabled"
        )