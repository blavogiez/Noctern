"""
Interface pour la présentation des données de debug dans l'interface utilisateur.
Respecte le principe de ségrégation d'interfaces (Interface Segregation Principle).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Optional
from .diff_generator import DiffLine
from .error_detector import LaTeXError

class IDebugPresenter(ABC):
    """Interface pour la présentation des informations de debug."""

    @abstractmethod
    def show_diff_comparison(self, diff_lines: List[DiffLine], title: str = "Document Diff") -> None:
        """
        Affiche une comparaison visuelle des différences.
        
        Args:
            diff_lines: Liste des lignes de différence
            title: Titre de la fenêtre de comparaison
        """
        pass

    @abstractmethod
    def show_error_list(self, errors: List[LaTeXError], on_error_click: Callable[[int], None] = None) -> None:
        """
        Affiche la liste des erreurs détectées.
        
        Args:
            errors: Liste des erreurs
            on_error_click: Callback appelé quand on clique sur une erreur
        """
        pass

    @abstractmethod
    def show_debug_panel(self, has_last_version: bool = False) -> None:
        """
        Affiche le panel de debug principal.
        
        Args:
            has_last_version: True si une version précédente existe
        """
        pass

class IDiffViewer(ABC):
    """Interface spécialisée pour l'affichage des différences."""

    @abstractmethod
    def display_side_by_side(self, old_content: str, new_content: str, 
                           diff_lines: List[DiffLine]) -> None:
        """
        Affiche les différences côte à côte.
        
        Args:
            old_content: Contenu original
            new_content: Nouveau contenu  
            diff_lines: Lignes de différence
        """
        pass

    @abstractmethod
    def highlight_critical_changes(self, critical_lines: List[DiffLine]) -> None:
        """
        Met en surbrillance les changements critiques.
        
        Args:
            critical_lines: Lignes contenant des changements critiques
        """
        pass

    @abstractmethod
    def set_navigation_callback(self, callback: Callable[[int], None]) -> None:
        """
        Définit le callback pour naviguer vers une ligne dans l'éditeur.
        
        Args:
            callback: Fonction appelée avec le numéro de ligne
        """
        pass