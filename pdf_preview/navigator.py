"""
PDF Text Navigator Component
Handles navigation to specific text within PDF documents.
"""

import os
import tkinter as tk
from utils import debug_console

class PDFTextNavigator:
    """
    Manages navigation to specific text within PDF documents.
    """
    
    def __init__(self, pdf_viewer):
        """
        Initialize the PDF text navigator.
        
        Args:
            pdf_viewer: The PDF viewer instance to navigate
        """
        self.pdf_viewer = pdf_viewer
        debug_console.log("PDF Text Navigator initialized", level='INFO')
    
    def go_to_text(self, text):
        """
        Navigate to the specified text in the PDF.
        
        Args:
            text (str): Text to search for in the PDF
        """
        if not self.pdf_viewer.pdf_path or not os.path.exists(self.pdf_viewer.pdf_path):
            debug_console.log("No PDF loaded for text search.", level='WARNING')
            return
            
        # Try to use the sync manager for more accurate text search
        from pdf_preview.sync import PDFSyncManager
        sync_manager = PDFSyncManager()
        position = sync_manager.find_text_in_pdf(self.pdf_viewer.pdf_path, text)
        
        if position:
            # Found the text, scroll to this page
            page_num = position['page']
            if page_num in self.pdf_viewer.page_layouts:
                layout = self.pdf_viewer.page_layouts[page_num]
                # Scroll to the page
                self.pdf_viewer.canvas.yview_moveto(layout['y_offset'] / self.pdf_viewer.total_height)
                debug_console.log(f"Found text on page {page_num}", level='INFO')
                return
        
        # Fallback to simple search if sync manager fails
        try:
            # Import pdfplumber for text extraction
            import pdfplumber
            
            # Search for text in PDF
            with pdfplumber.open(self.pdf_viewer.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text from the page
                    page_text = page.extract_text()
                    if page_text and text.lower() in page_text.lower():
                        # Found the text, scroll to this page
                        if page_num + 1 in self.pdf_viewer.page_layouts:
                            layout = self.pdf_viewer.page_layouts[page_num + 1]
                            # Scroll to the page
                            self.pdf_viewer.canvas.yview_moveto(layout['y_offset'] / self.pdf_viewer.total_height)
                            debug_console.log(f"Found text on page {page_num + 1}", level='INFO')
                            return
                        
            debug_console.log(f"Text '{text}' not found in PDF", level='INFO')
        except ImportError:
            debug_console.log("pdfplumber not installed. Cannot search text in PDF.", level='ERROR')
        except Exception as e:
            debug_console.log(f"Error searching text in PDF: {e}", level='ERROR')