"""
PDF-Editor Synchronization Component
Handles synchronization between the LaTeX editor and PDF preview.
"""

import re
from utils import debug_console


class PDFSyncManager:
    """
    Manages synchronization between the LaTeX editor and PDF preview,
    allowing bidirectional navigation between source and output.
    """
    
    def __init__(self):
        """
        Initialize the synchronization manager.
        """
        self.sync_points = {}  # Maps editor positions to PDF positions
        self.inverse_sync_points = {}  # Maps PDF positions to editor positions
        debug_console.log("PDF Synchronization Manager initialized", level='INFO')
    
    def create_sync_map(self, tex_content, pdf_pages):
        """
        Create a mapping between editor positions and PDF positions.
        
        Args:
            tex_content (str): Content of the LaTeX file
            pdf_pages (list): List of PDF page information
        """
        # Reset existing mappings
        self.sync_points = {}
        self.inverse_sync_points = {}
        
        # Parse the LaTeX content to identify sections, figures, etc.
        self._parse_latex_structure(tex_content)
        
        # In a full implementation, this would also parse the PDF for 
        # corresponding positions, possibly using synctex or similar tools
        
        debug_console.log(f"Created sync map with {len(self.sync_points)} points", level='DEBUG')
    
    def _parse_latex_structure(self, tex_content):
        """
        Parse the LaTeX content to identify structural elements.
        
        Args:
            tex_content (str): Content of the LaTeX file
        """
        lines = tex_content.split('\n')
        
        # Find sections
        section_pattern = r'\\(section|subsection|subsubsection)\*?\{([^}]+)\}'
        for line_num, line in enumerate(lines, 1):
            match = re.search(section_pattern, line)
            if match:
                section_type = match.group(1)
                section_title = match.group(2)
                self.sync_points[line_num] = {
                    'type': section_type,
                    'title': section_title,
                    'pdf_page_hint': self._estimate_pdf_page(line_num)
                }
        
        # Find figures and tables
        float_pattern = r'\\begin\{(figure|table)\*?\}'
        for line_num, line in enumerate(lines, 1):
            match = re.search(float_pattern, line)
            if match:
                float_type = match.group(1)
                self.sync_points[line_num] = {
                    'type': f'{float_type}',
                    'pdf_page_hint': self._estimate_pdf_page(line_num)
                }
        
        # Find equations
        equation_pattern = r'\\begin\{(equation|align|gather)\*?\}'
        for line_num, line in enumerate(lines, 1):
            match = re.search(equation_pattern, line)
            if match:
                eq_type = match.group(1)
                self.sync_points[line_num] = {
                    'type': f'equation_{eq_type}',
                    'pdf_page_hint': self._estimate_pdf_page(line_num)
                }
    
    def _estimate_pdf_page(self, line_number):
        """
        Estimate the PDF page for a given line number.
        This is a simplified heuristic and would be more accurate with synctex.
        
        Args:
            line_number (int): Line number in the LaTeX file
            
        Returns:
            int: Estimated PDF page number
        """
        # Very simple heuristic: assume ~50 lines per page
        # In a real implementation, this would use synctex or similar
        return max(1, line_number // 50)
    
    def get_pdf_position(self, line_number):
        """
        Get the PDF position for a given editor line number.
        
        Args:
            line_number (int): Line number in the editor
            
        Returns:
            dict: PDF position information or None if not found
        """
        # Find the closest sync point at or before the line number
        closest_line = None
        closest_point = None
        
        for sync_line, point in self.sync_points.items():
            if sync_line <= line_number and (closest_line is None or sync_line > closest_line):
                closest_line = sync_line
                closest_point = point
        
        return closest_point
    
    def get_editor_position(self, pdf_page):
        """
        Get the editor position for a given PDF page.
        
        Args:
            pdf_page (int): Page number in the PDF
            
        Returns:
            int: Estimated line number in the editor or None if not found
        """
        # Find the closest sync point for the given page
        closest_page = None
        closest_line = None
        
        for line_num, point in self.sync_points.items():
            page_hint = point.get('pdf_page_hint', 1)
            if page_hint <= pdf_page and (closest_page is None or page_hint > closest_page):
                closest_page = page_hint
                closest_line = line_num
        
        return closest_line
    
    def on_editor_navigation(self, line_number):
        """
        Handle navigation in the editor to synchronize PDF view.
        
        Args:
            line_number (int): New line number in the editor
            
        Returns:
            dict: PDF position information or None
        """
        pdf_position = self.get_pdf_position(line_number)
        if pdf_position:
            debug_console.log(
                f"Editor navigation to line {line_number} -> PDF page ~{pdf_position.get('pdf_page_hint', 1)}", 
                level='DEBUG'
            )
        return pdf_position
    
    def on_pdf_navigation(self, pdf_page):
        """
        Handle navigation in the PDF to synchronize editor view.
        
        Args:
            pdf_page (int): New page number in the PDF
            
        Returns:
            int: Estimated line number in the editor or None
        """
        editor_line = self.get_editor_position(pdf_page)
        if editor_line:
            debug_console.log(
                f"PDF navigation to page {pdf_page} -> Editor line ~{editor_line}", 
                level='DEBUG'
            )
        return editor_line
        
    def find_text_in_pdf(self, pdf_path, text):
        """
        Find the specified text in the PDF and return its position.
        
        Args:
            pdf_path (str): Path to the PDF file
            text (str): Text to search for
            
        Returns:
            dict: Position information (page number, coordinates) or None
        """
        try:
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text with bounding boxes
                    chars = page.chars
                    if chars:
                        # Simple text search
                        page_text = ''.join([char['text'] for char in chars])
                        if text.lower() in page_text.lower():
                            # Found the text on this page
                            return {
                                'page': page_num + 1,
                                'approx_y': 0.5  # Middle of page as approximation
                            }
                            
            return None
        except ImportError:
            debug_console.log("pdfplumber not installed. Cannot search text in PDF.", level='ERROR')
            return None
        except Exception as e:
            debug_console.log(f"Error searching text in PDF: {e}", level='ERROR')
            return None