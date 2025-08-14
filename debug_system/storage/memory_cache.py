"""
Cache mémoire pour améliorer les performances du système de versions.
Respecte le principe de responsabilité unique (Single Responsibility Principle).
"""

import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class MemoryCache:
    """Cache mémoire avec expiration automatique."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes par défaut
        """
        Initialise le cache mémoire.
        
        Args:
            default_ttl: Durée de vie par défaut en secondes
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: Clé de l'élément
            
        Returns:
            Valeur cachée ou None si expirée/inexistante
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if self._is_expired(entry):
            del self._cache[key]
            return None
        
        # Mettre à jour l'accès
        entry["last_accessed"] = datetime.now()
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Stocke une valeur dans le cache.
        
        Args:
            key: Clé de l'élément
            value: Valeur à stocker
            ttl: Durée de vie en secondes (utilise default_ttl si None)
        """
        ttl = ttl or self.default_ttl
        expiry_time = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            "value": value,
            "expires_at": expiry_time,
            "created_at": datetime.now(),
            "last_accessed": datetime.now()
        }
    
    def delete(self, key: str) -> bool:
        """
        Supprime une entrée du cache.
        
        Args:
            key: Clé de l'élément
            
        Returns:
            True si l'élément existait et a été supprimé
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Vide complètement le cache."""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Nettoie les entrées expirées.
        
        Returns:
            Nombre d'entrées supprimées
        """
        expired_keys = []
        for key, entry in self._cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache.
        
        Returns:
            Dict avec les statistiques
        """
        total_entries = len(self._cache)
        expired_count = sum(1 for entry in self._cache.values() if self._is_expired(entry))
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_count,
            "expired_entries": expired_count,
            "memory_usage_mb": self._estimate_memory_usage()
        }
    
    def _is_expired(self, entry: Dict) -> bool:
        """Vérifie si une entrée est expirée."""
        return datetime.now() > entry["expires_at"]
    
    def _estimate_memory_usage(self) -> float:
        """Estime l'usage mémoire du cache en MB."""
        import sys
        total_size = 0
        
        for entry in self._cache.values():
            total_size += sys.getsizeof(entry["value"])
            total_size += sys.getsizeof(entry)
        
        return total_size / (1024 * 1024)  # Convertir en MB


class CachedVersionStorage:
    """Wrapper qui ajoute un cache à n'importe quelle implémentation de stockage."""
    
    def __init__(self, storage_impl, cache_ttl: int = 300):
        """
        Initialise le stockage avec cache.
        
        Args:
            storage_impl: Implémentation du stockage (doit implémenter IVersionStorage)
            cache_ttl: Durée de vie du cache en secondes
        """
        self.storage = storage_impl
        self.cache = MemoryCache(cache_ttl)
    
    def get_last_successful_version(self, file_path: str):
        """Récupère la dernière version avec cache."""
        cache_key = f"last_success_{file_path}"
        cached_result = self.cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        result = self.storage.get_last_successful_version(file_path)
        if result:
            self.cache.set(cache_key, result, ttl=60)  # Cache court pour données critiques
        
        return result
    
    def store_version(self, file_path: str, content: str, timestamp: datetime, compilation_success: bool):
        """Stocke une version et invalide le cache."""
        # Invalider le cache pour ce fichier
        cache_key = f"last_success_{file_path}"
        self.cache.delete(cache_key)
        
        return self.storage.store_version(file_path, content, timestamp, compilation_success)
    
    def get_version_history(self, file_path: str, limit: int = 10):
        """Récupère l'historique avec cache."""
        cache_key = f"history_{file_path}_{limit}"
        cached_result = self.cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        result = self.storage.get_version_history(file_path, limit)
        self.cache.set(cache_key, result, ttl=120)  # Cache de 2 minutes
        
        return result
    
    def cleanup_old_versions(self, file_path: str, keep_count: int = 5):
        """Nettoie les versions et invalide le cache."""
        # Invalider tous les caches pour ce fichier
        cache_keys_to_delete = []
        for key in self.cache._cache.keys():
            if file_path in key:
                cache_keys_to_delete.append(key)
        
        for key in cache_keys_to_delete:
            self.cache.delete(key)
        
        return self.storage.cleanup_old_versions(file_path, keep_count)