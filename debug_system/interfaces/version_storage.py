"""
Interface pour le stockage des versions de documents LaTeX.
Respecte le principe de ségrégation d'interfaces (Interface Segregation Principle).
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime

class IVersionStorage(ABC):
    """Interface pour le stockage des versions de documents."""

    @abstractmethod
    def store_version(self, file_path: str, content: str, timestamp: datetime, compilation_success: bool) -> str:
        """
        Stocke une version d'un document.
        
        Args:
            file_path: Chemin vers le fichier
            content: Contenu du document
            timestamp: Horodatage de la version
            compilation_success: True si la compilation a réussi
            
        Returns:
            ID unique de la version stockée
        """
        pass

    @abstractmethod
    def get_last_successful_version(self, file_path: str) -> Optional[Dict]:
        """
        Récupère la dernière version compilée avec succès.
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Dict contenant {id, content, timestamp} ou None
        """
        pass

    @abstractmethod
    def get_version_history(self, file_path: str, limit: int = 10) -> List[Dict]:
        """
        Récupère l'historique des versions d'un fichier.
        
        Args:
            file_path: Chemin vers le fichier
            limit: Nombre maximum de versions à retourner
            
        Returns:
            Liste des versions triées par timestamp décroissant
        """
        pass

    @abstractmethod
    def cleanup_old_versions(self, file_path: str, keep_count: int = 5) -> int:
        """
        Nettoie les anciennes versions pour économiser l'espace.
        
        Args:
            file_path: Chemin vers le fichier
            keep_count: Nombre de versions à conserver
            
        Returns:
            Nombre de versions supprimées
        """
        pass