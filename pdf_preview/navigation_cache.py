"""
Navigation Cache Component
Provides high-performance caching for PDF navigation operations.
"""

import time
import threading
from typing import Dict, Optional, Any, NamedTuple, Set
from collections import OrderedDict
import hashlib
from utils import logs_console
from pdf_preview.line_coordinate_mapper import CoordinatePosition


class CacheEntry(NamedTuple):
    """Represents a cached navigation result."""
    data: Any
    timestamp: float
    access_count: int
    size_bytes: int


class CacheStats(NamedTuple):
    """Cache performance statistics."""
    hit_rate: float
    miss_count: int
    hit_count: int
    total_entries: int
    memory_usage_bytes: int
    eviction_count: int


class NavigationCache:
    """
    High-performance cache for PDF navigation operations with intelligent eviction.
    Optimizes repeated coordinate lookups and text searches.
    """
    
    def __init__(self, max_memory_mb: int = 50, max_entries: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize navigation cache.
        
        Args:
            max_memory_mb (int): Maximum memory usage in MB
            max_entries (int): Maximum number of cache entries
            ttl_seconds (int): Time-to-live for cache entries
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        
        # Cache storage
        self._line_coordinate_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._text_search_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._synctex_data_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._inverse_search_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._current_memory = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Recently accessed keys for better eviction decisions
        self._recently_accessed: Set[str] = set()
        self._last_cleanup = time.time()
        
        logs_console.log(f"Navigation Cache initialized: {max_memory_mb}MB, {max_entries} entries, {ttl_seconds}s TTL", level='INFO')
    
    def get_line_coordinates(self, line_number: int, pdf_path: str, source_hash: str) -> Optional[CoordinatePosition]:
        """
        Get cached line-to-coordinate mapping.
        
        Args:
            line_number (int): Line number
            pdf_path (str): PDF file path
            source_hash (str): Hash of source content for cache validation
            
        Returns:
            Optional[CoordinatePosition]: Cached coordinates or None
        """
        cache_key = self._generate_line_cache_key(line_number, pdf_path, source_hash)
        return self._get_from_cache(self._line_coordinate_cache, cache_key)
    
    def set_line_coordinates(self, line_number: int, pdf_path: str, source_hash: str, coordinates: CoordinatePosition) -> None:
        """
        Cache line-to-coordinate mapping.
        
        Args:
            line_number (int): Line number
            pdf_path (str): PDF file path
            source_hash (str): Hash of source content
            coordinates (CoordinatePosition): Coordinate data to cache
        """
        cache_key = self._generate_line_cache_key(line_number, pdf_path, source_hash)
        size_bytes = self._estimate_coordinate_size(coordinates)
        self._set_in_cache(self._line_coordinate_cache, cache_key, coordinates, size_bytes)
    
    def get_text_search_result(self, search_text: str, pdf_path: str, context_hash: str) -> Optional[Any]:
        """
        Get cached text search result.
        
        Args:
            search_text (str): Search text
            pdf_path (str): PDF file path
            context_hash (str): Hash of context for cache validation
            
        Returns:
            Optional[Any]: Cached search result or None
        """
        cache_key = self._generate_text_search_key(search_text, pdf_path, context_hash)
        return self._get_from_cache(self._text_search_cache, cache_key)
    
    def set_text_search_result(self, search_text: str, pdf_path: str, context_hash: str, result: Any) -> None:
        """
        Cache text search result.
        
        Args:
            search_text (str): Search text
            pdf_path (str): PDF file path
            context_hash (str): Hash of context
            result (Any): Search result to cache
        """
        cache_key = self._generate_text_search_key(search_text, pdf_path, context_hash)
        size_bytes = self._estimate_object_size(result)
        self._set_in_cache(self._text_search_cache, cache_key, result, size_bytes)
    
    def get_synctex_data(self, synctex_path: str, file_hash: str) -> Optional[Any]:
        """
        Get cached SyncTeX data.
        
        Args:
            synctex_path (str): Path to SyncTeX file
            file_hash (str): Hash of SyncTeX file for validation
            
        Returns:
            Optional[Any]: Cached SyncTeX data or None
        """
        cache_key = f"synctex:{synctex_path}:{file_hash}"
        return self._get_from_cache(self._synctex_data_cache, cache_key)
    
    def set_synctex_data(self, synctex_path: str, file_hash: str, data: Any) -> None:
        """
        Cache SyncTeX data.
        
        Args:
            synctex_path (str): Path to SyncTeX file
            file_hash (str): Hash of SyncTeX file
            data (Any): SyncTeX data to cache
        """
        cache_key = f"synctex:{synctex_path}:{file_hash}"
        size_bytes = self._estimate_object_size(data)
        self._set_in_cache(self._synctex_data_cache, cache_key, data, size_bytes)
    
    def get_inverse_search_result(self, page: int, x: float, y: float, pdf_path: str) -> Optional[tuple]:
        """
        Get cached inverse search result.
        
        Args:
            page (int): PDF page number
            x (float): X coordinate
            y (float): Y coordinate
            pdf_path (str): PDF file path
            
        Returns:
            Optional[tuple]: Cached result or None
        """
        cache_key = f"inverse:{pdf_path}:{page}:{x:.2f}:{y:.2f}"
        return self._get_from_cache(self._inverse_search_cache, cache_key)
    
    def set_inverse_search_result(self, page: int, x: float, y: float, pdf_path: str, result: tuple) -> None:
        """
        Cache inverse search result.
        
        Args:
            page (int): PDF page number
            x (float): X coordinate
            y (float): Y coordinate
            pdf_path (str): PDF file path
            result (tuple): Result to cache
        """
        cache_key = f"inverse:{pdf_path}:{page}:{x:.2f}:{y:.2f}"
        size_bytes = self._estimate_object_size(result)
        self._set_in_cache(self._inverse_search_cache, cache_key, result, size_bytes)
    
    def invalidate_pdf_cache(self, pdf_path: str) -> None:
        """
        Invalidate all cache entries for a specific PDF file.
        
        Args:
            pdf_path (str): PDF file path
        """
        with self._lock:
            pdf_path_encoded = pdf_path.encode('utf-8')
            
            # Remove from all caches
            caches = [
                self._line_coordinate_cache,
                self._text_search_cache,
                self._synctex_data_cache,
                self._inverse_search_cache
            ]
            
            for cache in caches:
                keys_to_remove = []
                for key in cache:
                    if pdf_path_encoded in key.encode('utf-8'):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    entry = cache.pop(key, None)
                    if entry:
                        self._current_memory -= entry.size_bytes
                        self._recently_accessed.discard(key)
        
        logs_console.log(f"Invalidated cache for PDF: {pdf_path}", level='DEBUG')
    
    def clear_cache(self) -> None:
        """Clear all cache data."""
        with self._lock:
            self._line_coordinate_cache.clear()
            self._text_search_cache.clear()
            self._synctex_data_cache.clear()
            self._inverse_search_cache.clear()
            self._recently_accessed.clear()
            self._current_memory = 0
            self._evictions = 0
        
        logs_console.log("Navigation cache cleared", level='DEBUG')
    
    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            total_entries = (
                len(self._line_coordinate_cache) +
                len(self._text_search_cache) +
                len(self._synctex_data_cache) +
                len(self._inverse_search_cache)
            )
            
            return CacheStats(
                hit_rate=hit_rate,
                miss_count=self._misses,
                hit_count=self._hits,
                total_entries=total_entries,
                memory_usage_bytes=self._current_memory,
                eviction_count=self._evictions
            )
    
    def cleanup_expired_entries(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            int: Number of entries removed
        """
        current_time = time.time()
        removed_count = 0
        
        with self._lock:
            caches = [
                self._line_coordinate_cache,
                self._text_search_cache,
                self._synctex_data_cache,
                self._inverse_search_cache
            ]
            
            for cache in caches:
                expired_keys = []
                for key, entry in cache.items():
                    if current_time - entry.timestamp > self.ttl_seconds:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    entry = cache.pop(key)
                    self._current_memory -= entry.size_bytes
                    self._recently_accessed.discard(key)
                    removed_count += 1
            
            self._last_cleanup = current_time
        
        if removed_count > 0:
            logs_console.log(f"Cleaned up {removed_count} expired cache entries", level='DEBUG')
        
        return removed_count
    
    def _get_from_cache(self, cache: OrderedDict, key: str) -> Optional[Any]:
        """Get item from specific cache."""
        with self._lock:
            # Periodic cleanup
            if time.time() - self._last_cleanup > 300:  # 5 minutes
                self.cleanup_expired_entries()
            
            entry = cache.get(key)
            if entry:
                # Check if expired
                if time.time() - entry.timestamp > self.ttl_seconds:
                    cache.pop(key)
                    self._current_memory -= entry.size_bytes
                    self._recently_accessed.discard(key)
                    self._misses += 1
                    return None
                
                # Update access info
                updated_entry = entry._replace(access_count=entry.access_count + 1)
                cache[key] = updated_entry
                cache.move_to_end(key)  # Mark as recently used
                self._recently_accessed.add(key)
                self._hits += 1
                return entry.data
            
            self._misses += 1
            return None
    
    def _set_in_cache(self, cache: OrderedDict, key: str, data: Any, size_bytes: int) -> None:
        """Set item in specific cache."""
        with self._lock:
            current_time = time.time()
            
            # Remove existing entry if present
            if key in cache:
                old_entry = cache.pop(key)
                self._current_memory -= old_entry.size_bytes
            
            # Check memory limits and evict if necessary
            self._evict_if_needed(size_bytes)
            
            # Add new entry
            entry = CacheEntry(
                data=data,
                timestamp=current_time,
                access_count=1,
                size_bytes=size_bytes
            )
            
            cache[key] = entry
            self._current_memory += size_bytes
            self._recently_accessed.add(key)
    
    def _evict_if_needed(self, new_entry_size: int) -> None:
        """Evict entries if memory or count limits would be exceeded."""
        # Check if we need to evict based on memory or count
        while (self._current_memory + new_entry_size > self.max_memory_bytes or 
               self._get_total_entries() >= self.max_entries):
            
            # Find least recently used entry across all caches
            oldest_key = None
            oldest_time = float('inf')
            oldest_cache = None
            
            caches = [
                self._line_coordinate_cache,
                self._text_search_cache,
                self._synctex_data_cache,
                self._inverse_search_cache
            ]
            
            for cache in caches:
                if not cache:
                    continue
                
                # Get the least recently used item (first in OrderedDict)
                first_key = next(iter(cache))
                entry = cache[first_key]
                
                # Prefer evicting entries not recently accessed and older
                priority_score = entry.timestamp
                if first_key not in self._recently_accessed:
                    priority_score -= 3600  # Prefer evicting non-recent items
                
                if priority_score < oldest_time:
                    oldest_time = priority_score
                    oldest_key = first_key
                    oldest_cache = cache
            
            # Evict the chosen entry
            if oldest_key and oldest_cache:
                entry = oldest_cache.pop(oldest_key)
                self._current_memory -= entry.size_bytes
                self._recently_accessed.discard(oldest_key)
                self._evictions += 1
            else:
                break  # No entries to evict
    
    def _get_total_entries(self) -> int:
        """Get total number of cached entries."""
        return (
            len(self._line_coordinate_cache) +
            len(self._text_search_cache) +
            len(self._synctex_data_cache) +
            len(self._inverse_search_cache)
        )
    
    def _generate_line_cache_key(self, line_number: int, pdf_path: str, source_hash: str) -> str:
        """Generate cache key for line coordinate mapping."""
        return f"line:{pdf_path}:{line_number}:{source_hash}"
    
    def _generate_text_search_key(self, search_text: str, pdf_path: str, context_hash: str) -> str:
        """Generate cache key for text search."""
        text_hash = hashlib.md5(search_text.encode('utf-8')).hexdigest()[:8]
        return f"search:{pdf_path}:{text_hash}:{context_hash}"
    
    def _estimate_coordinate_size(self, coordinates: CoordinatePosition) -> int:
        """Estimate memory size of coordinate data."""
        # Base size for CoordinatePosition fields
        return 200  # Conservative estimate for floats, strings, etc.
    
    def _estimate_object_size(self, obj: Any) -> int:
        """Estimate memory size of arbitrary object."""
        if obj is None:
            return 8
        elif isinstance(obj, (int, float)):
            return 24
        elif isinstance(obj, str):
            return 50 + len(obj.encode('utf-8'))
        elif isinstance(obj, (list, tuple)):
            return 100 + sum(self._estimate_object_size(item) for item in obj)
        elif isinstance(obj, dict):
            return 200 + sum(self._estimate_object_size(k) + self._estimate_object_size(v) 
                           for k, v in obj.items())
        else:
            return 500  # Conservative estimate for complex objects