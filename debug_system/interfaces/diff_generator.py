"""
Interface pour la génération de différences entre versions de documents.
Respecte le principe de responsabilité unique (Single Responsibility Principle).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
from enum import Enum

class DiffType(Enum):
    """Types de différences possibles."""
    ADDITION = "addition"
    DELETION = "deletion" 
    MODIFICATION = "modification"
    UNCHANGED = "unchanged"

class DiffLine:
    """Représente une ligne dans un diff."""
    
    def __init__(self, line_number: int, content: str, diff_type: DiffType, old_line_number: int = None):
        self.line_number = line_number
        self.content = content
        self.diff_type = diff_type
        self.old_line_number = old_line_number  # Pour les lignes modifiées

class IDiffGenerator(ABC):
    """Interface pour la génération de différences."""

    @abstractmethod
    def generate_diff(self, old_content: str, new_content: str) -> List[DiffLine]:
        """
        Génère les différences entre deux contenus.
        
        Args:
            old_content: Contenu original
            new_content: Nouveau contenu
            
        Returns:
            Liste des lignes avec leurs types de différence
        """
        pass

    @abstractmethod
    def get_diff_statistics(self, diff_lines: List[DiffLine]) -> Dict[str, int]:
        """
        Calcule les statistiques du diff.
        
        Args:
            diff_lines: Liste des lignes de différence
            
        Returns:
            Dict avec les compteurs {additions, deletions, modifications}
        """
        pass

    @abstractmethod
    def find_critical_changes(self, diff_lines: List[DiffLine]) -> List[DiffLine]:
        """
        Identifie les changements critiques (sections, commandes LaTeX importantes).
        
        Args:
            diff_lines: Liste des lignes de différence
            
        Returns:
            Liste des lignes contenant des changements critiques
        """
        pass