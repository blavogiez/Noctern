"""
Coordinateur principal du système de debug ultra-rapide.
Respecte le principe de responsabilité unique et d'inversion de dépendance (SOLID).
"""

from datetime import datetime
from typing import Optional, Callable, List
from .interfaces.version_storage import IVersionStorage
from .interfaces.diff_generator import IDiffGenerator
from .interfaces.error_detector import IErrorDetector, LaTeXError
from .interfaces.ui_presenter import IDebugPresenter, IDiffViewer

class DebugCoordinator:
    """Coordinateur principal du système de debug."""
    
    def __init__(self, 
                 version_storage: IVersionStorage,
                 diff_generator: IDiffGenerator,
                 error_detector: IErrorDetector,
                 debug_presenter: IDebugPresenter,
                 diff_viewer: IDiffViewer):
        """
        Initialise le coordinateur avec toutes ses dépendances.
        
        Args:
            version_storage: Service de stockage des versions
            diff_generator: Générateur de différences
            error_detector: Détecteur d'erreurs
            debug_presenter: Présenteur pour l'interface
            diff_viewer: Visualiseur de différences
        """
        self.version_storage = version_storage
        self.diff_generator = diff_generator
        self.error_detector = error_detector
        self.debug_presenter = debug_presenter
        self.diff_viewer = diff_viewer
        
        # État actuel
        self.current_file_path: Optional[str] = None
        self.current_content: Optional[str] = None
        self.last_errors: List[LaTeXError] = []
        
        # Callbacks
        self.on_goto_line: Optional[Callable[[int], None]] = None
    
    def set_current_document(self, file_path: str, content: str):
        """
        Définit le document actuel à analyser.
        
        Args:
            file_path: Chemin vers le fichier
            content: Contenu actuel du document
        """
        self.current_file_path = file_path
        self.current_content = content
        
        # Analyser immédiatement
        self._analyze_current_document()
    
    def store_successful_compilation(self, file_path: str, content: str):
        """
        Stocke une version après compilation réussie.
        
        Args:
            file_path: Chemin vers le fichier
            content: Contenu compilé avec succès
        """
        try:
            version_id = self.version_storage.store_version(
                file_path, content, datetime.now(), compilation_success=True
            )
            print(f"OK: Version stockée: {version_id}")
            
            # Nettoyer les anciennes versions
            cleaned = self.version_storage.cleanup_old_versions(file_path)
            if cleaned > 0:
                print(f"NETTOYAGE: {cleaned} anciennes versions supprimées")
                
        except Exception as e:
            print(f"Erreur lors du stockage: {e}")
    
    def show_diff_with_last_version(self):
        """Affiche la comparaison avec la dernière version compilée."""
        print("DEBUG: show_diff_with_last_version called")
        print(f"DEBUG: current_file_path = {self.current_file_path}")
        print(f"DEBUG: has content = {bool(self.current_content)}")
        print(f"DEBUG: has diff_viewer = {bool(self.diff_viewer)}")
        
        if not self.current_file_path or not self.current_content:
            print("ERREUR: Aucun document actuel défini")
            return
        
        if not self.diff_viewer:
            print("ERREUR: Visualiseur de diff non disponible")
            return
        
        # Récupérer la dernière version compilée
        last_version = self.version_storage.get_last_successful_version(self.current_file_path)
        if not last_version:
            print("ERREUR: Aucune version précédente trouvée")
            return
        
        try:
            # Générer le diff
            diff_lines = self.diff_generator.generate_diff(
                last_version["content"],
                self.current_content
            )
            
            # Identifier les changements critiques
            critical_changes = self.diff_generator.find_critical_changes(diff_lines)
            
            # Afficher dans le visualiseur
            self.diff_viewer.display_side_by_side(
                last_version["content"],
                self.current_content,
                diff_lines
            )
            
            # Mettre en surbrillance les changements critiques
            if critical_changes:
                self.diff_viewer.highlight_critical_changes(critical_changes)
            
            # Configurer la navigation
            if self.on_goto_line:
                self.diff_viewer.set_navigation_callback(self.on_goto_line)
            
            print(f"STATS: Diff généré: {len(diff_lines)} lignes analysées")
            
        except Exception as e:
            print(f"ERREUR: Erreur lors de la génération du diff: {e}")
    
    def get_quick_diff_summary(self) -> Optional[dict]:
        """
        Retourne un résumé rapide des différences.
        
        Returns:
            Dict avec statistiques ou None si pas de version précédente
        """
        if not self.current_file_path or not self.current_content:
            return None
        
        last_version = self.version_storage.get_last_successful_version(self.current_file_path)
        if not last_version:
            return None
        
        try:
            diff_lines = self.diff_generator.generate_diff(
                last_version["content"],
                self.current_content
            )
            
            stats = self.diff_generator.get_diff_statistics(diff_lines)
            critical_changes = self.diff_generator.find_critical_changes(diff_lines)
            
            return {
                **stats,
                "critical_changes": len(critical_changes),
                "last_version_timestamp": last_version["timestamp"],
                "has_changes": stats["additions"] > 0 or stats["deletions"] > 0 or stats["modifications"] > 0
            }
            
        except Exception as e:
            print(f"ERREUR: Erreur lors du calcul du résumé: {e}")
            return None
    
    def set_navigation_callback(self, callback: Callable[[int], None]):
        """
        Définit le callback pour la navigation vers une ligne.
        
        Args:
            callback: Fonction appelée avec le numéro de ligne
        """
        self.on_goto_line = callback
    
    def _analyze_current_document(self):
        """Analyse le document actuel et met à jour l'interface."""
        if not self.current_file_path or not self.current_content:
            return
        
        try:
            # Ne plus détecter les erreurs automatiquement
            self.last_errors = []
            
            # Vérifier s'il y a une version précédente
            has_last_version = self.version_storage.get_last_successful_version(
                self.current_file_path
            ) is not None
            
            # Mettre à jour l'interface
            self.debug_presenter.show_debug_panel(has_last_version)
            
            print(f"ANALYSE: Document analysé, version précédente: {has_last_version}")
            
        except Exception as e:
            print(f"ERREUR: Erreur lors de l'analyse: {e}")
    
    def get_version_history(self, limit: int = 10) -> List[dict]:
        """
        Retourne l'historique des versions.
        
        Args:
            limit: Nombre maximum de versions à retourner
            
        Returns:
            Liste des versions
        """
        if not self.current_file_path:
            return []
        
        try:
            return self.version_storage.get_version_history(self.current_file_path, limit)
        except Exception as e:
            print(f"ERREUR: Erreur lors de la récupération de l'historique: {e}")
            return []
    
    def force_cleanup_versions(self, keep_count: int = 5) -> int:
        """
        Force le nettoyage des anciennes versions.
        
        Args:
            keep_count: Nombre de versions à conserver
            
        Returns:
            Nombre de versions supprimées
        """
        if not self.current_file_path:
            return 0
        
        try:
            return self.version_storage.cleanup_old_versions(self.current_file_path, keep_count)
        except Exception as e:
            print(f"ERREUR: Erreur lors du nettoyage: {e}")
            return 0


class DebugCoordinatorFactory:
    """Factory pour créer des instances du coordinateur avec les bonnes dépendances."""
    
    @staticmethod
    def create_default_coordinator(parent_window=None, 
                                 on_goto_line: Callable[[int], None] = None,
                                 storage_dir: str = ".automatex_versions"):
        """
        Crée un coordinateur avec les implémentations par défaut.
        
        Args:
            parent_window: Fenêtre parent pour l'interface
            on_goto_line: Callback pour navigation
            storage_dir: Répertoire de stockage des versions
            
        Returns:
            Instance du coordinateur configurée
        """
        # Imports des implémentations concrètes
        from .storage.file_version_storage import FileVersionStorage
        from .storage.memory_cache import CachedVersionStorage
        from .diff.text_diff_generator import LaTeXDiffGenerator
        from .diff.visual_diff_renderer import TkinterDiffViewer
        from .detection.compilation_detector import CompilationErrorDetector
        from .ui.debug_panel import UltraFastDebugPanel
        
        # Créer les instances
        base_storage = FileVersionStorage(storage_dir)
        version_storage = CachedVersionStorage(base_storage)
        diff_generator = LaTeXDiffGenerator()
        error_detector = CompilationErrorDetector()
        
        # Créer le diff viewer seulement si on a une fenêtre parent
        try:
            diff_viewer = TkinterDiffViewer(parent_window)
        except:
            # Mode test ou sans GUI
            diff_viewer = None
        
        # Créer le coordinateur
        coordinator = DebugCoordinator(
            version_storage, diff_generator, error_detector, None, diff_viewer
        )
        
        # Créer le debug panel avec les callbacks
        debug_panel = UltraFastDebugPanel(
            parent_window,
            on_goto_line=on_goto_line,
            on_show_diff=coordinator.show_diff_with_last_version
        )
        
        # Connecter le présenteur
        coordinator.debug_presenter = debug_panel
        coordinator.set_navigation_callback(on_goto_line)
        
        return coordinator, debug_panel