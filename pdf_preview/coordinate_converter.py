"""
PDF Coordinate Converter
Handles precise conversion between PDF coordinates, SyncTeX coordinates, and viewer coordinates.
"""

from typing import Tuple, Optional
from utils import logs_console


class PDFPreviewCoordinateConverter:
    """
    Converts between different coordinate systems:
    - SyncTeX coordinates (scaled points, origin bottom-left)
    - PDF coordinates (points, origin bottom-left)  
    - Viewer coordinates (pixels, origin top-left)
    """
    
    def __init__(self):
        """Initialize coordinate converter."""
        # SyncTeX uses scaled points (sp) where 1 pt = 65536 sp
        self.SYNCTEX_UNIT_TO_POINTS = 1.0 / 65536.0
        
        # Standard PDF DPI for coordinate calculations
        self.PDF_DPI = 72.0
        
    
    def synctex_to_pdf_points(self, synctex_x: float, synctex_y: float) -> Tuple[float, float]:
        """
        Convert SyncTeX coordinates to PDF points.
        
        Args:
            synctex_x (float): X coordinate in SyncTeX units (sp)
            synctex_y (float): Y coordinate in SyncTeX units (sp)
            
        Returns:
            Tuple[float, float]: (x, y) in PDF points
        """
        pdf_x = synctex_x * self.SYNCTEX_UNIT_TO_POINTS
        pdf_y = synctex_y * self.SYNCTEX_UNIT_TO_POINTS
        
        return pdf_x, pdf_y
    
    def pdf_to_viewer_coordinates(self, pdf_x: float, pdf_y: float, 
                                 page_width: float, page_height: float,
                                 viewer_width: int, viewer_height: int,
                                 viewer_y_offset: int = 0) -> Tuple[int, int]:
        """
        Convert PDF coordinates to viewer pixel coordinates.
        
        Args:
            pdf_x (float): X coordinate in PDF points
            pdf_y (float): Y coordinate in PDF points (bottom-left origin)
            page_width (float): PDF page width in points
            page_height (float): PDF page height in points
            viewer_width (int): Displayed page width in pixels
            viewer_height (int): Displayed page height in pixels
            viewer_y_offset (int): Y offset of page in viewer
            
        Returns:
            Tuple[int, int]: (x, y) in viewer pixel coordinates
        """
        # Calculate scaling factors
        scale_x = viewer_width / page_width
        scale_y = viewer_height / page_height
        
        # Convert coordinates
        viewer_x = int(pdf_x * scale_x)
        
        # Flip Y coordinate (PDF origin bottom-left, viewer origin top-left)
        viewer_y = int((page_height - pdf_y) * scale_y) + viewer_y_offset
        
        
        return viewer_x, viewer_y
    
    def synctex_to_viewer_coordinates(self, synctex_x: float, synctex_y: float,
                                     page_width: float, page_height: float,
                                     viewer_width: int, viewer_height: int,
                                     viewer_y_offset: int = 0) -> Tuple[int, int]:
        """
        Direct conversion from SyncTeX to viewer coordinates.
        
        Args:
            synctex_x (float): X coordinate in SyncTeX units
            synctex_y (float): Y coordinate in SyncTeX units
            page_width (float): PDF page width in points
            page_height (float): PDF page height in points
            viewer_width (int): Displayed page width in pixels
            viewer_height (int): Displayed page height in pixels
            viewer_y_offset (int): Y offset of page in viewer
            
        Returns:
            Tuple[int, int]: (x, y) in viewer pixel coordinates
        """
        # Convert SyncTeX to PDF points first
        pdf_x, pdf_y = self.synctex_to_pdf_points(synctex_x, synctex_y)
        
        # Then convert to viewer coordinates
        return self.pdf_to_viewer_coordinates(
            pdf_x, pdf_y, page_width, page_height,
            viewer_width, viewer_height, viewer_y_offset
        )
    
    def calculate_scroll_position(self, viewer_y: int, total_height: int) -> float:
        """
        Calculate scroll position for viewer navigation.
        
        Args:
            viewer_y (int): Target Y coordinate in viewer
            total_height (int): Total height of scrollable area
            
        Returns:
            float: Scroll position (0.0 to 1.0)
        """
        scroll_pos = max(0.0, min(1.0, viewer_y / total_height))
        return scroll_pos
    
    def get_text_bounds_from_chars(self, chars: list, start_idx: int, length: int,
                                  page_width: float, page_height: float,
                                  viewer_width: int, viewer_height: int,
                                  viewer_y_offset: int = 0) -> Optional[Tuple[int, int, int, int]]:
        """
        Get bounding rectangle for text from pdfplumber character data.
        
        Args:
            chars (list): Character data from pdfplumber
            start_idx (int): Start index in characters
            length (int): Number of characters
            page_width (float): PDF page width in points
            page_height (float): PDF page height in points
            viewer_width (int): Displayed page width in pixels
            viewer_height (int): Displayed page height in pixels
            viewer_y_offset (int): Y offset of page in viewer
            
        Returns:
            Optional[Tuple[int, int, int, int]]: (x, y, width, height) in viewer coordinates or None
        """
        if not chars or start_idx >= len(chars) or length <= 0:
            return None
        
        end_idx = min(start_idx + length, len(chars))
        text_chars = chars[start_idx:end_idx]
        
        if not text_chars:
            return None
        
        # Get bounding box in PDF coordinates
        min_x = min(char['x0'] for char in text_chars)
        max_x = max(char['x1'] for char in text_chars)
        min_y = min(char['top'] for char in text_chars)
        max_y = max(char['bottom'] for char in text_chars)
        
        # Convert corners to viewer coordinates
        top_left = self.pdf_to_viewer_coordinates(
            min_x, max_y, page_width, page_height,
            viewer_width, viewer_height, viewer_y_offset
        )
        
        bottom_right = self.pdf_to_viewer_coordinates(
            max_x, min_y, page_width, page_height,
            viewer_width, viewer_height, viewer_y_offset
        )
        
        # Calculate bounding rectangle
        x = top_left[0]
        y = top_left[1]
        width = bottom_right[0] - top_left[0]
        height = bottom_right[1] - top_left[1]
        
        
        return (x, y, width, height)
    
    def estimate_line_position(self, line_number: int, total_lines: int,
                              page_height: float, viewer_height: int,
                              viewer_y_offset: int = 0) -> int:
        """
        Estimate viewer position for a line number when no SyncTeX data is available.
        
        Args:
            line_number (int): Target line number
            total_lines (int): Total lines in document
            page_height (float): PDF page height in points
            viewer_height (int): Displayed page height in pixels
            viewer_y_offset (int): Y offset of page in viewer
            
        Returns:
            int: Estimated Y position in viewer coordinates
        """
        if total_lines <= 0:
            return viewer_y_offset
        
        # Estimate line position as fraction of page height
        line_fraction = (line_number - 1) / max(total_lines, line_number)
        
        # Convert to viewer coordinates (remember Y flip)
        estimated_y = int((1.0 - line_fraction) * viewer_height) + viewer_y_offset
        
        
        return estimated_y