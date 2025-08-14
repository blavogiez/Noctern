"""
Interface pour la détection d'erreurs dans les documents LaTeX.
Respecte le principe ouvert/fermé (Open/Closed Principle).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum

class ErrorSeverity(Enum):
    """Niveaux de gravité des erreurs."""
    CRITICAL = "critical"  # Empêche la compilation
    WARNING = "warning"    # Peut causer des problèmes
    INFO = "info"         # Information seulement

class LaTeXError:
    """Représente une erreur LaTeX détectée."""
    
    def __init__(self, line_number: int, error_message: str, severity: ErrorSeverity, 
                 error_type: str = None, suggestion: str = None):
        self.line_number = line_number
        self.error_message = error_message
        self.severity = severity
        self.error_type = error_type or "unknown"
        self.suggestion = suggestion
        self.context_lines = []  # Lignes autour de l'erreur pour contexte

class IErrorDetector(ABC):
    """Interface pour la détection d'erreurs."""

    @abstractmethod
    def detect_errors(self, content: str, file_path: str = None) -> List[LaTeXError]:
        """
        Détecte les erreurs dans le contenu LaTeX.
        
        Args:
            content: Contenu du document LaTeX
            file_path: Chemin du fichier (optionnel, pour résolution des chemins)
            
        Returns:
            Liste des erreurs détectées
        """
        pass

    @abstractmethod
    def get_error_categories(self) -> List[str]:
        """
        Retourne les catégories d'erreurs que ce détecteur peut identifier.
        
        Returns:
            Liste des types d'erreurs détectables
        """
        pass

    @abstractmethod
    def is_compilation_blocking(self, error: LaTeXError) -> bool:
        """
        Détermine si une erreur empêche la compilation.
        
        Args:
            error: L'erreur à analyser
            
        Returns:
            True si l'erreur empêche la compilation
        """
        pass