"""
Precise PDF Navigator Component
Central orchestrator for exact PDF navigation with SyncTeX and intelligent fallbacks.
Production-ready architecture with optimized performance.
"""

import os
import time
import hashlib
from typing import Optional, Tuple, Dict, Any
from utils import logs_console
from pdf_preview.synctex_parser import SyncTexParser
from pdf_preview.text_search_engine import TextSearchEngine
from pdf_preview.line_coordinate_mapper import LineCoordinateMapper, CoordinatePosition
from pdf_preview.navigation_cache import NavigationCache


class NavigationResult:
    """Represents the result of a PDF navigation operation."""
    
    def __init__(self, success: bool, page: int = 0, x: float = 0.0, y: float = 0.0, 
                 confidence: float = 0.0, method: str = "", details: str = ""):
        self.success = success
        self.page = page
        self.x = x
        self.y = y
        self.confidence = confidence
        self.method = method  # 'synctex', 'text_search', 'estimation'
        self.details = details
    
    def __repr__(self):
        return f"NavigationResult(success={self.success}, page={self.page}, pos=({self.x:.1f}, {self.y:.1f}), confidence={self.confidence:.2f}, method='{self.method}')"


class PDFPreviewNavigator:
    """
    High-precision PDF navigation system with SyncTeX integration and intelligent fallbacks.
    Handles exact line-to-coordinate mapping with performance optimization.
    """
    
    def __init__(self, cache_size_mb: int = 30):
        """
        Initialize precise navigator.
        
        Args:
            cache_size_mb (int): Cache size in megabytes
        """
        # Core components
        self.line_mapper = LineCoordinateMapper()
        self.cache = NavigationCache(max_memory_mb=cache_size_mb)
        
        # Current state
        self.current_pdf_path = None
        self.current_synctex_path = None
        self.current_source_hash = None
        
        # Performance tracking
        self.navigation_count = 0
        self.cache_hit_count = 0
        self.synctex_success_count = 0
        
        logs_console.log("Precise Navigator initialized", level='INFO')
    
    def set_document_files(self, pdf_path: str, synctex_path: Optional[str] = None, 
                          source_content: str = "") -> bool:
        """
        Set the current document files for navigation.
        
        Args:
            pdf_path (str): Path to PDF file
            synctex_path (Optional[str]): Path to SyncTeX file  
            source_content (str): LaTeX source content for validation
            
        Returns:
            bool: True if files loaded successfully
        """
        if not os.path.exists(pdf_path):
            logs_console.log(f"PDF file not found: {pdf_path}", level='ERROR')
            return False
        
        # Generate hash of source content for cache validation
        source_hash = hashlib.md5(source_content.encode('utf-8')).hexdigest()[:12]
        
        # Check if we need to update
        if (self.current_pdf_path == pdf_path and 
            self.current_synctex_path == synctex_path and 
            self.current_source_hash == source_hash):
            return True  # Already loaded
        
        # Invalidate old cache if PDF changed
        if self.current_pdf_path != pdf_path:
            self.cache.invalidate_pdf_cache(self.current_pdf_path or "")
        
        # Update state
        self.current_pdf_path = pdf_path
        self.current_synctex_path = synctex_path
        self.current_source_hash = source_hash
        
        # Configure line mapper
        self.line_mapper.set_pdf_files(pdf_path, synctex_path)
        
        info = self.line_mapper.get_mapping_info()
        logs_console.log(f"Document files loaded: PDF={os.path.basename(pdf_path)}, SyncTeX={'Yes' if info['synctex_available'] else 'No'}", level='INFO')
        
        return True
    
    def navigate_to_line(self, line_number: int, source_text: str = "", 
                        context_before: str = "", context_after: str = "") -> NavigationResult:
        """
        Navigate to exact line number in PDF with disambiguation support.
        
        Args:
            line_number (int): Line number in LaTeX source
            source_text (str): Text on the line for disambiguation
            context_before (str): Context before the line
            context_after (str): Context after the line
            
        Returns:
            NavigationResult: Navigation result with position and confidence
        """
        if not self.current_pdf_path:
            logs_console.log("Navigation failed: No PDF file loaded", level='ERROR')
            return NavigationResult(False, details="No PDF file loaded")
        
        self.navigation_count += 1
        start_time = time.time()
        
        # Log navigation attempt with detailed context
        logs_console.log(f"Starting navigation to line {line_number}", level='INFO')
        logs_console.log(f"  Source text: '{source_text[:50]}{'...' if len(source_text) > 50 else ''}'", level='DEBUG')
        logs_console.log(f"  Context before: '{context_before[-30:] if context_before else 'None'}'", level='DEBUG')
        logs_console.log(f"  Context after: '{context_after[:30] if context_after else 'None'}'", level='DEBUG')
        logs_console.log(f"  PDF: {os.path.basename(self.current_pdf_path)}", level='DEBUG')
        logs_console.log(f"  SyncTeX: {'Available' if self.line_mapper.has_synctex_data() else 'Not available'}", level='DEBUG')
        
        # Try cache first
        cached_result = self._get_cached_navigation(line_number, source_text, context_before, context_after)
        if cached_result:
            self.cache_hit_count += 1
            logs_console.log(f"Cache hit for line {line_number} - returning cached result", level='INFO')
            logs_console.log(f"  Cached result: page {cached_result.page}, confidence {cached_result.confidence:.2f}", level='DEBUG')
            return cached_result
        
        # Get coordinates using line mapper
        logs_console.log(f"Attempting coordinate mapping for line {line_number}", level='INFO')
        coordinates = self.line_mapper.get_coordinates_for_line(
            line_number, source_text, context_before, context_after
        )
        
        if coordinates:
            result = NavigationResult(
                success=True,
                page=coordinates.page,
                x=coordinates.x,
                y=coordinates.y,
                confidence=coordinates.confidence,
                method=coordinates.source,
                details=f"Mapped to page {coordinates.page} using {coordinates.source}"
            )
            
            logs_console.log(f"Navigation successful for line {line_number}", level='INFO')
            logs_console.log(f"Method: {coordinates.source}", level='INFO')
            logs_console.log(f"Target: page {coordinates.page}, coords ({coordinates.x:.1f}, {coordinates.y:.1f})", level='INFO')
            logs_console.log(f"Confidence: {coordinates.confidence:.2f}", level='INFO')
            
            # Track SyncTeX success
            if coordinates.source == 'synctex':
                self.synctex_success_count += 1
                logs_console.log(f"📍 SyncTeX mapping successful - total successes: {self.synctex_success_count}", level='DEBUG')
            
            # Cache the result
            self._cache_navigation_result(line_number, source_text, context_before, context_after, result)
            
        else:
            result = NavigationResult(
                False, 
                details=f"Could not map line {line_number} to PDF coordinates"
            )
            
            logs_console.log(f"Navigation failed for line {line_number}", level='WARNING')
            logs_console.log(f"Reason: No coordinate mapping found", level='WARNING')
            
            # Log diagnostic information
            mapping_info = self.line_mapper.get_mapping_info()
            logs_console.log(f"  Diagnostic info:", level='DEBUG')
            logs_console.log(f"    SyncTeX available: {mapping_info.get('synctex_available', False)}", level='DEBUG')
            logs_console.log(f"    Line range: {mapping_info.get('synctex_line_range', 'Unknown')}", level='DEBUG')
            logs_console.log(f"    Text search cache size: {mapping_info.get('text_search_cache_size', 0)}", level='DEBUG')
        
        elapsed_time = time.time() - start_time
        logs_console.log(f"Navigation completed in {elapsed_time:.3f}s (success: {result.success})", level='INFO')
        
        return result
    
    def navigate_from_coordinates(self, page: int, x: float, y: float) -> Optional[Tuple[int, float]]:
        """
        Inverse navigation: get source line from PDF coordinates.
        
        Args:
            page (int): PDF page number
            x (float): X coordinate
            y (float): Y coordinate
            
        Returns:
            Optional[Tuple[int, float]]: (line_number, confidence) or None
        """
        if not self.current_pdf_path:
            return None
        
        # Try cache first
        cached_result = self.cache.get_inverse_search_result(page, x, y, self.current_pdf_path)
        if cached_result:
            return cached_result
        
        # Use line mapper for inverse search
        result = self.line_mapper.get_line_for_coordinates(page, x, y)
        
        if result:
            # Cache the result
            self.cache.set_inverse_search_result(page, x, y, self.current_pdf_path, result)
        
        return result
    
    def get_navigation_capabilities(self) -> Dict[str, Any]:
        """
        Get information about current navigation capabilities.
        
        Returns:
            Dict[str, Any]: Capability information
        """
        if not self.current_pdf_path:
            return {'status': 'no_document_loaded'}
        
        info = self.line_mapper.get_mapping_info()
        cache_stats = self.cache.get_stats()
        
        return {
            'status': 'ready',
            'pdf_file': os.path.basename(self.current_pdf_path),
            'synctex_available': info['synctex_available'],
            'synctex_line_range': info.get('synctex_line_range', (0, 0)),
            'synctex_page_count': info.get('synctex_page_count', 0),
            'navigation_count': self.navigation_count,
            'cache_hit_rate': cache_stats.hit_rate,
            'synctex_success_rate': self.synctex_success_count / max(self.navigation_count, 1),
            'cache_memory_mb': cache_stats.memory_usage_bytes / 1024 / 1024,
            'performance_score': self._calculate_performance_score(cache_stats)
        }
    
    def optimize_performance(self) -> Dict[str, int]:
        """
        Perform performance optimizations.
        
        Returns:
            Dict[str, int]: Optimization results
        """
        # Clean expired cache entries
        expired_removed = self.cache.cleanup_expired_entries()
        
        # Clear text search cache if too large
        text_cache_cleared = 0
        if hasattr(self.line_mapper.text_search_engine, 'get_cache_size'):
            cache_size = self.line_mapper.text_search_engine.get_cache_size()
            if cache_size > 100:  # More than 100 pages cached
                self.line_mapper.text_search_engine.clear_cache()
                text_cache_cleared = cache_size
        
        return {
            'expired_entries_removed': expired_removed,
            'text_cache_entries_cleared': text_cache_cleared
        }
    
    def reset_navigation_state(self) -> None:
        """Reset navigation state and clear all caches."""
        self.current_pdf_path = None
        self.current_synctex_path = None
        self.current_source_hash = None
        self.navigation_count = 0
        self.cache_hit_count = 0
        self.synctex_success_count = 0
        
        self.cache.clear_cache()
        self.line_mapper.clear_cache()
        
        logs_console.log("Navigation state reset", level='INFO')
    
    def _get_cached_navigation(self, line_number: int, source_text: str, 
                              context_before: str, context_after: str) -> Optional[NavigationResult]:
        """Get cached navigation result."""
        if not self.current_source_hash:
            return None
        
        coordinates = self.cache.get_line_coordinates(
            line_number, self.current_pdf_path, self.current_source_hash
        )
        
        if coordinates:
            return NavigationResult(
                success=True,
                page=coordinates.page,
                x=coordinates.x,
                y=coordinates.y,
                confidence=coordinates.confidence,
                method=f"{coordinates.source}_cached",
                details=f"Cached result for line {line_number}"
            )
        
        return None
    
    def _cache_navigation_result(self, line_number: int, source_text: str, 
                               context_before: str, context_after: str, 
                               result: NavigationResult) -> None:
        """Cache navigation result."""
        if not self.current_source_hash or not result.success:
            return
        
        coordinates = CoordinatePosition(
            page=result.page,
            x=result.x,
            y=result.y,
            width=0.0,  # We don't track width/height in navigation results
            height=0.0,
            confidence=result.confidence,
            source=result.method
        )
        
        self.cache.set_line_coordinates(
            line_number, self.current_pdf_path, self.current_source_hash, coordinates
        )
    
    def _calculate_performance_score(self, cache_stats) -> float:
        """
        Calculate performance score (0.0 to 1.0).
        
        Args:
            cache_stats: Cache statistics
            
        Returns:
            float: Performance score
        """
        if self.navigation_count == 0:
            return 1.0
        
        # Weight different performance factors
        cache_factor = cache_stats.hit_rate * 0.4
        synctex_factor = (self.synctex_success_count / self.navigation_count) * 0.6
        
        return min(1.0, cache_factor + synctex_factor)