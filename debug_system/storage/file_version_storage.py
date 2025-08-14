"""
Implémentation du stockage des versions basé sur des fichiers.
Respecte le principe de responsabilité unique (Single Responsibility Principle).
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict
from ..interfaces.version_storage import IVersionStorage

class FileVersionStorage(IVersionStorage):
    """Stockage des versions dans des fichiers JSON."""
    
    def __init__(self, storage_dir: str = ".automatex_versions"):
        """
        Initialise le stockage de versions.
        
        Args:
            storage_dir: Répertoire de stockage des versions
        """
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self) -> None:
        """Crée le répertoire de stockage s'il n'existe pas."""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_storage_path(self, file_path: str) -> str:
        """
        Génère le chemin de stockage pour un fichier donné.
        
        Args:
            file_path: Chemin vers le fichier original
            
        Returns:
            Chemin vers le fichier de versions
        """
        # Créer un nom de fichier unique basé sur le chemin
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:12]
        filename = f"{os.path.basename(file_path)}_{path_hash}.json"
        return os.path.join(self.storage_dir, filename)
    
    def _generate_version_id(self, content: str, timestamp: datetime) -> str:
        """Génère un ID unique pour une version."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        time_stamp = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{time_stamp}_{content_hash}"
    
    def store_version(self, file_path: str, content: str, timestamp: datetime, compilation_success: bool) -> str:
        """Stocke une version d'un document."""
        storage_path = self._get_storage_path(file_path)
        version_id = self._generate_version_id(content, timestamp)
        
        # Charger l'historique existant ou créer un nouveau
        versions_data = self._load_versions_data(storage_path)
        
        # Ajouter la nouvelle version
        new_version = {
            "id": version_id,
            "content": content,
            "timestamp": timestamp.isoformat(),
            "compilation_success": compilation_success,
            "file_path": file_path
        }
        
        versions_data["versions"].insert(0, new_version)  # Ajouter en tête
        versions_data["last_updated"] = timestamp.isoformat()
        
        # Sauvegarder
        self._save_versions_data(storage_path, versions_data)
        
        return version_id
    
    def get_last_successful_version(self, file_path: str) -> Optional[Dict]:
        """Récupère la dernière version compilée avec succès."""
        storage_path = self._get_storage_path(file_path)
        versions_data = self._load_versions_data(storage_path)
        
        for version in versions_data["versions"]:
            if version["compilation_success"]:
                return {
                    "id": version["id"],
                    "content": version["content"],
                    "timestamp": datetime.fromisoformat(version["timestamp"])
                }
        
        return None
    
    def get_version_history(self, file_path: str, limit: int = 10) -> List[Dict]:
        """Récupère l'historique des versions d'un fichier."""
        storage_path = self._get_storage_path(file_path)
        versions_data = self._load_versions_data(storage_path)
        
        history = []
        for version in versions_data["versions"][:limit]:
            history.append({
                "id": version["id"],
                "timestamp": datetime.fromisoformat(version["timestamp"]),
                "compilation_success": version["compilation_success"],
                "content_preview": version["content"][:200] + "..." if len(version["content"]) > 200 else version["content"]
            })
        
        return history
    
    def cleanup_old_versions(self, file_path: str, keep_count: int = 5) -> int:
        """Nettoie les anciennes versions."""
        storage_path = self._get_storage_path(file_path)
        versions_data = self._load_versions_data(storage_path)
        
        if len(versions_data["versions"]) <= keep_count:
            return 0
        
        # Garder les versions les plus récentes et au moins une version compilée avec succès
        versions_to_keep = versions_data["versions"][:keep_count]
        
        # S'assurer qu'on garde au moins une version compilée avec succès
        has_successful = any(v["compilation_success"] for v in versions_to_keep)
        if not has_successful:
            for version in versions_data["versions"][keep_count:]:
                if version["compilation_success"]:
                    versions_to_keep.append(version)
                    break
        
        removed_count = len(versions_data["versions"]) - len(versions_to_keep)
        versions_data["versions"] = versions_to_keep
        
        self._save_versions_data(storage_path, versions_data)
        return removed_count
    
    def _load_versions_data(self, storage_path: str) -> Dict:
        """Charge les données de versions depuis le fichier."""
        if not os.path.exists(storage_path):
            return {
                "versions": [],
                "created": datetime.now().isoformat(),
                "last_updated": None
            }
        
        try:
            with open(storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Fichier corrompu, recommencer
            return {
                "versions": [],
                "created": datetime.now().isoformat(),
                "last_updated": None
            }
    
    def _save_versions_data(self, storage_path: str, data: Dict) -> None:
        """Sauvegarde les données de versions dans le fichier."""
        try:
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Impossible de sauvegarder les versions: {e}")