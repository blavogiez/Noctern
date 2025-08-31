"""
Line-to-Coordinate Mapping System
Provides exact line number to PDF coordinate mapping using SyncTeX and intelligent fallbacks.
"""

import os
from typing import Optional, Tuple, NamedTuple
from utils import logs_console
from pdf_preview.synctex_parser import SyncTexParser, SyncTexRecord
from pdf_preview.text_search_engine import TextSearchEngine, SearchResult


class CoordinatePosition(NamedTuple):
    """Represents a precise position in PDF coordinates."""
    page: int
    x: float  # Horizontal position (PDF units)
    y: float  # Vertical position (PDF units) 
    width: float
    height: float
    confidence: float  # 0.0 to 1.0
    source: str  # 'synctex' or 'text_search'


class LineCoordinateMapper:
    """
    Maps LaTeX source line numbers to precise PDF coordinates.
    Uses SyncTeX as primary method with intelligent text search fallback.
    Handles duplicate content by using line position and context.
    """
    
    def __init__(self):
        """Initialize line coordinate mapper."""
        self.synctex_parser = SyncTexParser()
        self.text_search_engine = TextSearchEngine()
        self.current_pdf_path = None
        self.current_synctex_path = None
        self.synctex_available = False
        logs_console.log("Line Coordinate Mapper initialized", level='INFO')
    
    def set_pdf_files(self, pdf_path: str, synctex_path: Optional[str] = None) -> None:
        """
        Set the current PDF and SyncTeX files.
        
        Args:
            pdf_path (str): Path to PDF file
            synctex_path (Optional[str]): Path to SyncTeX file
        """
        self.current_pdf_path = pdf_path
        self.current_synctex_path = synctex_path
        self.synctex_available = False
        
        # Try to load SyncTeX data
        if synctex_path and os.path.exists(synctex_path):
            if self.synctex_parser.parse_synctex_file(synctex_path):
                self.synctex_available = True
                logs_console.log(f"SyncTeX loaded: {synctex_path}", level='INFO')
            else:
                logs_console.log(f"Failed to parse SyncTeX: {synctex_path}", level='WARNING')
        else:
            logs_console.log("No SyncTeX file available, using text search fallback", level='INFO')
        
        # Clear text search cache for new PDF
        self.text_search_engine.clear_cache()
    
    def get_coordinates_for_line(self, line_number: int, source_text: str = "", 
                               context_before: str = "", context_after: str = "") -> Optional[CoordinatePosition]:
        """
        Get precise PDF coordinates for a LaTeX source line number.
        
        Args:
            line_number (int): Line number in LaTeX source
            source_text (str): Text on the line (for disambiguation)
            context_before (str): Context before the line
            context_after (str): Context after the line
            
        Returns:
            Optional[CoordinatePosition]: Precise position or None if not found
        """
        if not self.current_pdf_path:
            logs_console.log("No PDF file set for coordinate mapping", level='WARNING')
            return None
        
        # Primary strategy: Use SyncTeX if available
        if self.synctex_available:
            synctex_result = self._get_synctex_coordinates(line_number)
            if synctex_result:
                logs_console.log(f"SyncTeX mapping: line {line_number} -> page {synctex_result.page} ({synctex_result.x:.1f}, {synctex_result.y:.1f})", level='DEBUG')
                return synctex_result
        
        # Fallback strategy: Use intelligent text search
        if source_text.strip():
            search_result = self._get_text_search_coordinates(source_text, context_before, context_after)
            if search_result:
                logs_console.log(f"Text search mapping: line {line_number} -> page {search_result.page} (confidence: {search_result.confidence:.2f})", level='DEBUG')
                return search_result
        
        # Last resort: Estimate based on available data
        if self.synctex_available:
            estimated_result = self._estimate_coordinates(line_number)
            if estimated_result:
                logs_console.log(f"Estimated mapping: line {line_number} -> page {estimated_result.page}", level='DEBUG')
                return estimated_result
        
        logs_console.log(f"Could not map line {line_number} to PDF coordinates", level='WARNING')
        return None
    
    def get_line_for_coordinates(self, page: int, x: float, y: float) -> Optional[Tuple[int, float]]:
        """
        Get source line number for PDF coordinates (inverse search).
        
        Args:
            page (int): PDF page number
            x (float): Horizontal position
            y (float): Vertical position
            
        Returns:
            Optional[Tuple[int, float]]: (line_number, confidence) or None
        """
        if not self.current_pdf_path:
            return None
        
        # Try SyncTeX inverse search first
        if self.synctex_available:
            synctex_record = self.synctex_parser.get_source_position(page, x, y)
            if synctex_record:
                return (synctex_record.line, 1.0)
        
        # For text search inverse, we would need more complex logic
        # This would require extracting text at the coordinates and matching back to source
        logs_console.log(f"Inverse search not fully implemented for coordinates ({x}, {y}) on page {page}", level='DEBUG')
        return None
    
    def _get_synctex_coordinates(self, line_number: int) -> Optional[CoordinatePosition]:
        """Get coordinates using SyncTeX data."""
        synctex_record = self.synctex_parser.get_pdf_position(line_number)
        if synctex_record:
            return CoordinatePosition(
                page=synctex_record.pdf_page,
                x=synctex_record.h_position,
                y=synctex_record.v_position,
                width=synctex_record.width,
                height=synctex_record.height,
                confidence=1.0,
                source='synctex'
            )
        return None
    
    def _get_text_search_coordinates(self, source_text: str, context_before: str, context_after: str) -> Optional[CoordinatePosition]:
        """Get coordinates using intelligent text search."""
        search_result = self.text_search_engine.search_in_pdf(
            self.current_pdf_path, source_text, context_before, context_after
        )
        
        if search_result:
            # Convert text position to PDF coordinates
            # This is approximate since we don't have exact character positioning from pdfplumber
            coordinates = self._convert_text_position_to_coordinates(search_result)
            if coordinates:
                return CoordinatePosition(
                    page=coordinates[0],
                    x=coordinates[1],
                    y=coordinates[2],
                    width=coordinates[3],
                    height=coordinates[4],
                    confidence=search_result.confidence,
                    source='text_search'
                )
        
        return None
    
    def _convert_text_position_to_coordinates(self, search_result: SearchResult) -> Optional[Tuple[int, float, float, float, float]]:
        """
        Convert text search result to approximate PDF coordinates.
        
        Args:
            search_result (SearchResult): Text search result
            
        Returns:
            Optional[Tuple]: (page, x, y, width, height) or None
        """
        try:
            import pdfplumber
            
            with pdfplumber.open(self.current_pdf_path) as pdf:
                if search_result.page - 1 >= len(pdf.pages):
                    return None
                
                page = pdf.pages[search_result.page - 1]
                chars = page.chars
                
                if chars and search_result.start_index < len(chars):
                    # Get character at start position
                    start_char = chars[min(search_result.start_index, len(chars) - 1)]
                    
                    # Estimate end position
                    end_index = min(search_result.start_index + search_result.length, len(chars))
                    if end_index > search_result.start_index:
                        end_char = chars[end_index - 1]
                        width = end_char['x1'] - start_char['x0']
                        height = max(start_char['bottom'] - start_char['top'], 12)  # Minimum height
                    else:
                        width = start_char['x1'] - start_char['x0']
                        height = start_char['bottom'] - start_char['top']
                    
                    return (
                        search_result.page,
                        start_char['x0'],
                        start_char['top'],
                        width,
                        height
                    )
                
        except ImportError:
            logs_console.log("pdfplumber not available for coordinate conversion", level='WARNING')
        except Exception as e:
            logs_console.log(f"Error converting text position to coordinates: {e}", level='ERROR')
        
        return None
    
    def _estimate_coordinates(self, line_number: int) -> Optional[CoordinatePosition]:
        """
        Estimate coordinates based on available SyncTeX data and heuristics.
        
        Args:
            line_number (int): Target line number
            
        Returns:
            Optional[CoordinatePosition]: Estimated position or None
        """
        if not self.synctex_available:
            return None
        
        # Get line range from SyncTeX data
        line_range = self.synctex_parser.get_line_range()
        if line_range[0] == 0 and line_range[1] == 0:
            return None
        
        min_line, max_line = line_range
        
        # If line is outside known range, extrapolate
        if line_number < min_line:
            # Use first known position
            record = self.synctex_parser.get_pdf_position(min_line)
        elif line_number > max_line:
            # Use last known position
            record = self.synctex_parser.get_pdf_position(max_line)
        else:
            # Find closest known line
            closest_line = None
            min_diff = float('inf')
            
            for known_line in range(min_line, max_line + 1):
                if line_number == known_line:
                    record = self.synctex_parser.get_pdf_position(known_line)
                    if record:
                        break
                
                diff = abs(known_line - line_number)
                if diff < min_diff:
                    temp_record = self.synctex_parser.get_pdf_position(known_line)
                    if temp_record:
                        min_diff = diff
                        closest_line = known_line
            else:
                record = self.synctex_parser.get_pdf_position(closest_line) if closest_line else None
        
        if record:
            return CoordinatePosition(
                page=record.pdf_page,
                x=record.h_position,
                y=record.v_position,
                width=record.width,
                height=record.height,
                confidence=0.5,  # Low confidence for estimates
                source='synctex_estimated'
            )
        
        return None
    
    def has_synctex_data(self) -> bool:
        """Check if SyncTeX data is available and loaded."""
        return self.synctex_available
    
    def get_mapping_info(self) -> dict:
        """Get information about current mapping capabilities."""
        info = {
            'pdf_path': self.current_pdf_path,
            'synctex_path': self.current_synctex_path,
            'synctex_available': self.synctex_available,
            'text_search_cache_size': self.text_search_engine.get_cache_size()
        }
        
        if self.synctex_available:
            line_range = self.synctex_parser.get_line_range()
            info['synctex_line_range'] = line_range
            info['synctex_page_count'] = self.synctex_parser.get_page_count()
        
        return info
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.text_search_engine.clear_cache()
        logs_console.log("Line coordinate mapper cache cleared", level='DEBUG')