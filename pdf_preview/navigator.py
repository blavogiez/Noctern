"""
PDF Text Navigator Component
Handles navigation to specific text within PDF documents and highlights the found text.
"""

import os
import tkinter as tk
from utils import debug_console
import pdfplumber

class PDFTextNavigator:
    """
    Manages navigation to specific text within PDF documents and highlights the found text.
    """
    
    def __init__(self, pdf_viewer):
        """
        Initialize the PDF text navigator.
        
        Args:
            pdf_viewer: The PDF viewer instance to navigate
        """
        self.pdf_viewer = pdf_viewer
        self.highlight_rectangles = []  # Store highlight rectangles for cleanup
        debug_console.log("PDF Text Navigator initialized", level='INFO')
    
    def clear_highlights(self):
        """
        Clear all highlighted rectangles from the PDF viewer.
        """
        for rect in self.highlight_rectangles:
            self.pdf_viewer.canvas.delete(rect)
        self.highlight_rectangles.clear()
    
    def highlight_text(self, page_num, chars, start_idx, text_length):
        """
        Highlight the specified text on the PDF page.
        
        Args:
            page_num (int): Page number (1-based)
            chars (list): List of character data from pdfplumber
            start_idx (int): Start index of text in page
            text_length (int): Length of text to highlight
        """
        # Clear previous highlights
        self.clear_highlights()
        
        if page_num not in self.pdf_viewer.page_layouts:
            return
            
        layout = self.pdf_viewer.page_layouts[page_num]
        y_offset = layout['y_offset']
        
        # Get page dimensions from pdfplumber to calculate scaling factor
        try:
            with pdfplumber.open(self.pdf_viewer.pdf_path) as pdf:
                if page_num - 1 < len(pdf.pages):
                    page = pdf.pages[page_num - 1]
                    page_width = page.width
                    page_height = page.height
                else:
                    debug_console.log(f"Page {page_num} not found in PDF.", level='WARNING')
                    return
        except Exception as e:
            debug_console.log(f"Error getting page dimensions: {e}", level='ERROR')
            return

        # Ensure dimensions are not zero to avoid division by zero
        if not page_width or not page_height:
            debug_console.log(f"Invalid page dimensions for page {page_num}.", level='WARNING')
            return

        scale_x = layout['width'] / float(page_width)
        scale_y = layout['height'] / float(page_height)
        
        # Calculate the bounding box for the text
        if start_idx + text_length <= len(chars):
            # Get the characters for the text
            text_chars = chars[start_idx:start_idx + text_length]
            
            if text_chars:
                # Get the bounding box of the first character
                first_char = text_chars[0]
                min_x, max_x = first_char['x0'], first_char['x1']
                min_y, max_y = first_char['top'], first_char['bottom']
                
                # Get the bounding box of all characters
                for char in text_chars:
                    min_x = min(min_x, char['x0'])
                    max_x = max(max_x, char['x1'])
                    min_y = min(min_y, char['top'])
                    max_y = max(max_y, char['bottom'])
                
                # Apply scaling
                scaled_min_x = min_x * scale_x
                scaled_max_x = max_x * scale_x
                scaled_min_y = min_y * scale_y
                scaled_max_y = max_y * scale_y
                
                # Add a vertical margin for the highlight
                v_margin = 25  # pixels
                
                # Create a semi-transparent green rectangle that spans the full width
                rect = self.pdf_viewer.canvas.create_rectangle(
                    10, y_offset + scaled_min_y - v_margin,
                    10 + layout['width'], y_offset + scaled_max_y + v_margin,
                    fill="green", stipple="gray50", outline="darkgreen", width=1
                )
                
                # Store the rectangle for later cleanup
                self.highlight_rectangles.append(rect)
                
                # Bring the rectangle to the front
                self.pdf_viewer.canvas.tag_raise(rect)
                
                debug_console.log(f"Highlighted text on page {page_num}", level='INFO')
    
    def go_to_text(self, text, context_before="", context_after=""):
        """
        Navigate to the specified text in the PDF and highlight it.
        
        Args:
            text (str): Text to search for in the PDF
            context_before (str): Text before the target text
            context_after (str): Text after the target text
        """
        # Clear previous highlights
        self.clear_highlights()
        
        if not self.pdf_viewer.pdf_path or not os.path.exists(self.pdf_viewer.pdf_path):
            debug_console.log("No PDF loaded for text search.", level='WARNING')
            return
            
        # Try to use the sync manager for more accurate text search
        # Use the sync manager from the viewer if available, otherwise create a new one
        if hasattr(self.pdf_viewer, 'sync_manager') and self.pdf_viewer.sync_manager:
            sync_manager = self.pdf_viewer.sync_manager
        else:
            from pdf_preview.sync import PDFSyncManager
            sync_manager = PDFSyncManager()
            
        position = sync_manager.find_text_in_pdf(
            self.pdf_viewer.pdf_path, text, context_before, context_after
        )
        
        if position:
            # Found the text, scroll to this page
            page_num = position['page']
            if page_num in self.pdf_viewer.page_layouts:
                layout = self.pdf_viewer.page_layouts[page_num]
                # Scroll to the page
                self.pdf_viewer.canvas.yview_moveto(layout['y_offset'] / self.pdf_viewer.total_height)
                
                # Highlight the text
                self.highlight_text(
                    page_num, 
                    position['chars'], 
                    position['start_index'], 
                    position['text_length']
                )
                
                debug_console.log(f"Found and highlighted text on page {page_num}", level='INFO')
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
                            
                            # Try to highlight the text (approximate)
                            start_idx = page_text.lower().find(text.lower())
                            if hasattr(page, 'chars'):
                                self.highlight_text(
                                    page_num + 1, 
                                    page.chars, 
                                    start_idx, 
                                    len(text)
                                )
                            
                            debug_console.log(f"Found text on page {page_num + 1}", level='INFO')
                            return
                        
            debug_console.log(f"Text '{text}' not found in PDF", level='INFO')
        except ImportError:
            debug_console.log("pdfplumber not installed. Cannot search text in PDF.", level='ERROR')
        except Exception as e:
            debug_console.log(f"Error searching text in PDF: {e}", level='ERROR')