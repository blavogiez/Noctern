"""
PDF Text Locator Component
Handles precise text location and highlighting within PDF documents using the new navigation system.
"""

import os
import tkinter as tk
from utils import logs_console
from pdf_preview.precise_navigator import PreciseNavigator
from pdf_preview.coordinate_converter import CoordinateConverter

class PDFTextLocator:
    """
    Manages precise text location and highlighting within PDF documents.
    Uses the new PreciseNavigator system for enhanced accuracy.
    """
    
    def __init__(self, pdf_viewer):
        """
        Initialize the PDF text locator.
        
        Args:
            pdf_viewer: The PDF viewer instance to navigate
        """
        self.pdf_viewer = pdf_viewer
        self.navigator = PreciseNavigator()
        self.coordinate_converter = CoordinateConverter()
        self.highlight_rectangles = []  # Store highlight rectangles for cleanup
        logs_console.log("PDF Text Locator initialized", level='INFO')
    
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
                    logs_console.log(f"Page {page_num} not found in PDF.", level='WARNING')
                    return
        except Exception as e:
            logs_console.log(f"Error getting page dimensions: {e}", level='ERROR')
            return

        # Ensure dimensions are not zero to avoid division by zero
        if not page_width or not page_height:
            logs_console.log(f"Invalid page dimensions for page {page_num}.", level='WARNING')
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
                
                # Add vertical margin for highlight
                v_margin = 25  # Pixels
                
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
                
                logs_console.log(f"Highlighted text on page {page_num}", level='INFO')
    
    def set_document_files(self, pdf_path: str, synctex_path: str = None, source_content: str = "") -> None:
        """
        Set the document files for precise navigation.
        
        Args:
            pdf_path (str): Path to PDF file
            synctex_path (str): Path to SyncTeX file
            source_content (str): LaTeX source content
        """
        self.navigator.set_document_files(pdf_path, synctex_path, source_content)
    
    def navigate_to_line(self, line_number: int, source_text: str = "", 
                        context_before: str = "", context_after: str = "") -> bool:
        """
        Navigate to specific line number with precise positioning.
        
        Args:
            line_number (int): Line number in LaTeX source (0 = text search mode)
            source_text (str): Text on the line for disambiguation
            context_before (str): Context before the line
            context_after (str): Context after the line
            
        Returns:
            bool: True if navigation successful
        """
        # Clear previous highlights
        self.clear_highlights()
        
        # Special handling for text search mode (line_number = 0)
        if line_number == 0 and source_text:
            return self._enhanced_text_search(source_text, context_before, context_after)
        
        # Normal line-based navigation
        result = self.navigator.navigate_to_line(line_number, source_text, context_before, context_after)
        
        if result.success:
            # Navigate to the precise position and center it
            self._scroll_to_position(result.page, result.x, result.y)
            
            logs_console.log(f"Navigated to line {line_number} on page {result.page} using {result.method} (confidence: {result.confidence:.2f})", level='INFO')
            return True
        else:
            logs_console.log(f"Failed to navigate to line {line_number}: {result.details}", level='WARNING')
            return False
    
    def _enhanced_text_search(self, text: str, context_before: str, context_after: str) -> bool:
        """
        Enhanced text search with multiple strategies.
        
        Args:
            text (str): Text to search for
            context_before (str): Context before the text
            context_after (str): Context after the text
            
        Returns:
            bool: True if text found and highlighted
        """
        if not self.pdf_viewer.pdf_path or not os.path.exists(self.pdf_viewer.pdf_path):
            logs_console.log("No PDF loaded for text search.", level='WARNING')
            return False
        
        try:
            import pdfplumber
            
            with pdfplumber.open(self.pdf_viewer.pdf_path) as pdf:
                search_strategies = [
                    # Strategy 1: Full context match
                    (context_before + text + context_after, "full_context"),
                    # Strategy 2: Text + partial context
                    (text + context_after[:50], "text_plus_after"),
                    (context_before[-50:] + text, "before_plus_text"),
                    # Strategy 3: Just the text
                    (text, "text_only"),
                    # Strategy 4: Cleaned text (remove LaTeX commands)
                    (self._clean_latex_text(text), "cleaned_text")
                ]
                
                for search_text, strategy in search_strategies:
                    if not search_text.strip():
                        continue
                        
                    result = self._search_text_in_pages(pdf, search_text, strategy)
                    if result:
                        page_num, char_info = result
                        layout = self.pdf_viewer.page_layouts.get(page_num)
                        if layout:
                            # Force render and center the page
                            self.pdf_viewer.force_render_page_for_navigation(page_num)
                            
                            # Calculate center position for the page
                            page_center_y = layout['y_offset'] + (layout['height'] // 2)
                            scroll_y = self.coordinate_converter.calculate_scroll_position(
                                page_center_y - 200,  # Center page in view
                                self.pdf_viewer.total_height
                            )
                            self.pdf_viewer.canvas.yview_moveto(scroll_y)
                            
                            # Ensure visible pages are updated
                            self.pdf_viewer.canvas.after_idle(self.pdf_viewer._update_visible_pages)
                            
                            logs_console.log(f"Found and centered text using {strategy} on page {page_num}", level='INFO')
                            return True
                
                logs_console.log(f"Text '{text}' not found in PDF using any strategy", level='WARNING')
                return False
                
        except ImportError:
            logs_console.log("pdfplumber not installed. Cannot search text in PDF.", level='ERROR')
            return False
        except Exception as e:
            logs_console.log(f"Error in enhanced text search: {e}", level='ERROR')
            return False
    
    def _search_text_in_pages(self, pdf, search_text: str, strategy: str):
        """Search for text in all PDF pages."""
        search_lower = search_text.lower().strip()
        if not search_lower:
            return None
            
        for page_num, page in enumerate(pdf.pages):
            try:
                page_text = page.extract_text()
                if page_text and search_lower in page_text.lower():
                    # Try to get character-level information
                    chars = getattr(page, 'chars', None)
                    if chars:
                        # Find position in page text
                        page_text_lower = page_text.lower()
                        start_idx = page_text_lower.find(search_lower)
                        
                        if start_idx >= 0:
                            return (page_num + 1, {
                                'chars': chars,
                                'start_idx': start_idx,
                                'length': len(search_text),
                                'strategy': strategy
                            })
                    else:
                        # Basic match without character info
                        return (page_num + 1, None)
            except Exception as e:
                logs_console.log(f"Error searching page {page_num + 1}: {e}", level='DEBUG')
                continue
                
        return None
    
    def _clean_latex_text(self, text: str) -> str:
        """Remove common LaTeX commands from text for better matching."""
        import re
        
        # Remove common LaTeX commands
        cleaned = re.sub(r'\\[a-zA-Z]+\*?\s*', '', text)
        cleaned = re.sub(r'\{|\}', '', cleaned)
        cleaned = re.sub(r'\\\\', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _create_text_highlight(self, page_num: int, char_info: dict, strategy: str) -> None:
        """Create highlight for text search results using precise coordinate conversion."""
        if not char_info or page_num not in self.pdf_viewer.page_layouts:
            return
            
        try:
            layout = self.pdf_viewer.page_layouts[page_num]
            chars = char_info['chars']
            start_idx = char_info['start_idx']
            length = char_info['length']
            
            # Get page dimensions
            page_width, page_height = self.pdf_viewer._get_page_dimensions(page_num)
            if not page_width or not page_height:
                logs_console.log(f"Cannot highlight text: no page dimensions for page {page_num}", level='WARNING')
                return
            
            # Use coordinate converter to get precise text bounds
            bounds = self.coordinate_converter.get_text_bounds_from_chars(
                chars, start_idx, length,
                page_width, page_height,
                layout['width'], layout['height'], layout['y_offset']
            )
            
            if bounds:
                x, y, width, height = bounds
                confidence = 0.9 if strategy == "full_context" else 0.7 if strategy in ["text_plus_after", "before_plus_text"] else 0.5
                
                # Create highlight rectangle with strategy-based styling
                if confidence > 0.8:
                    fill_color = "lightgreen"
                    outline_color = "darkgreen"
                    stipple = "gray25"
                    line_width = 3
                elif confidence > 0.6:
                    fill_color = "lightblue"
                    outline_color = "darkblue"
                    stipple = "gray37"
                    line_width = 2
                else:
                    fill_color = "yellow"
                    outline_color = "orange"
                    stipple = "gray50"
                    line_width = 1
                
                # Add some padding for visibility
                padding = 3
                rect = self.pdf_viewer.canvas.create_rectangle(
                    x - padding, y - padding,
                    x + width + padding, y + height + padding,
                    fill=fill_color,
                    stipple=stipple,
                    outline=outline_color,
                    width=line_width
                )
                
                self.highlight_rectangles.append(rect)
                self.pdf_viewer.canvas.tag_raise(rect)
                
                logs_console.log(f"✅ Text highlight created using {strategy}: bounds ({x}, {y}, {width}x{height}), confidence {confidence:.2f}", level='INFO')
            else:
                # Fallback to old method
                self.highlight_text(page_num, chars, start_idx, length)
                logs_console.log(f"Used fallback highlight method for {strategy}", level='DEBUG')
                
        except Exception as e:
            logs_console.log(f"Error creating text highlight: {e}", level='WARNING')

    def go_to_text(self, text, context_before="", context_after=""):
        """
        Navigate to the specified text in the PDF and highlight it.
        
        Args:
            text (str): Text to search for in the PDF
            context_before (str): Text before the target text
            context_after (str): Text after the target text
        """
        # Use text-based navigation (line number 0 indicates text search)
        success = self.navigate_to_line(0, text, context_before, context_after)
        if not success:
            # Fallback to legacy search
            self._legacy_text_search(text, context_before, context_after)
    
    def _scroll_to_position(self, page: int, x: float, y: float) -> None:
        """Scroll PDF viewer to specific position and center it with immediate rendering."""
        if page not in self.pdf_viewer.page_layouts:
            logs_console.log(f"Page {page} not in layouts", level='WARNING')
            return
            
        layout = self.pdf_viewer.page_layouts[page]
        
        # Get page dimensions for proper coordinate conversion
        page_width, page_height = self.pdf_viewer._get_page_dimensions(page)
        if not page_width or not page_height:
            logs_console.log(f"Could not get page dimensions for page {page}", level='WARNING')
            return
        
        # Force render the target page and adjacent pages immediately
        self.pdf_viewer.force_render_page_for_navigation(page)
        
        # Calculate center position for the page
        page_center_y = layout['y_offset'] + (layout['height'] // 2)
        
        # Calculate scroll position to center the page in view
        scroll_y = self.coordinate_converter.calculate_scroll_position(
            page_center_y - 200,  # Offset to center page in view
            self.pdf_viewer.total_height
        )
        
        logs_console.log(f"Centering page {page} in view: scroll position {scroll_y:.3f}", level='INFO')
        
        # Scroll to center the page
        self.pdf_viewer.canvas.yview_moveto(scroll_y)
        
        # Trigger visible pages update to ensure all visible content is rendered
        self.pdf_viewer.canvas.after_idle(self.pdf_viewer._update_visible_pages)
    
    def _create_precise_highlight(self, page: int, x: float, y: float, confidence: float) -> None:
        """Create precise highlight at PDF coordinates using precise coordinate conversion."""
        if page not in self.pdf_viewer.page_layouts:
            logs_console.log(f"Cannot highlight: page {page} not in layouts", level='WARNING')
            return
            
        layout = self.pdf_viewer.page_layouts[page]
        
        # Get page dimensions for proper coordinate conversion
        page_width, page_height = self.pdf_viewer._get_page_dimensions(page)
        if not page_width or not page_height:
            logs_console.log(f"Cannot highlight: no page dimensions for page {page}", level='WARNING')
            return
        
        # Use precise coordinate converter
        viewer_x, viewer_y = self.coordinate_converter.pdf_to_viewer_coordinates(
            x, y, page_width, page_height,
            layout['width'], layout['height'], layout['y_offset']
        )
        
        # Create highlight with confidence-based styling
        if confidence > 0.8:
            fill_color = "lightblue"
            outline_color = "darkblue"
            stipple = "gray25"
            line_width = 3
            width = 300  # Wider for visibility
            height = 20   # Taller for better visibility
        else:
            fill_color = "yellow"
            outline_color = "orange"
            stipple = "gray50"
            line_width = 2
            width = 400  # Even wider for lower confidence
            height = 25
        
        # Center highlight around the target position
        highlight_x = max(10, viewer_x - width // 4)  # Start slightly before target
        highlight_y = viewer_y - height // 2  # Center vertically on target
        
        # Ensure highlight stays within page boundaries
        highlight_x = min(highlight_x, layout['width'] - width + 10)
        highlight_y = max(layout['y_offset'], highlight_y)
        highlight_y = min(highlight_y, layout['y_offset'] + layout['height'] - height)
        
        logs_console.log(f"Creating highlight: PDF ({x:.1f}, {y:.1f}) -> viewer ({viewer_x}, {viewer_y}) -> rect ({highlight_x}, {highlight_y}, {width}x{height})", level='INFO')
        
        rect = self.pdf_viewer.canvas.create_rectangle(
            highlight_x, highlight_y,
            highlight_x + width, highlight_y + height,
            fill=fill_color,
            stipple=stipple,
            outline=outline_color,
            width=line_width
        )
        
        self.highlight_rectangles.append(rect)
        self.pdf_viewer.canvas.tag_raise(rect)
        
        logs_console.log(f"✅ Highlight created on page {page} (confidence {confidence:.2f})", level='INFO')
    
    def _legacy_text_search(self, text: str, context_before: str, context_after: str) -> None:
        """Legacy text search fallback."""
        if not self.pdf_viewer.pdf_path or not os.path.exists(self.pdf_viewer.pdf_path):
            logs_console.log("No PDF loaded for text search.", level='WARNING')
            return
            
        try:
            import pdfplumber
            
            with pdfplumber.open(self.pdf_viewer.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text and text.lower() in page_text.lower():
                        if page_num + 1 in self.pdf_viewer.page_layouts:
                            layout = self.pdf_viewer.page_layouts[page_num + 1]
                            
                            # Force render and center the page
                            self.pdf_viewer.force_render_page_for_navigation(page_num + 1)
                            
                            # Calculate center position for the page
                            page_center_y = layout['y_offset'] + (layout['height'] // 2)
                            scroll_y = self.coordinate_converter.calculate_scroll_position(
                                page_center_y - 200,  # Center page in view
                                self.pdf_viewer.total_height
                            )
                            self.pdf_viewer.canvas.yview_moveto(scroll_y)
                            
                            # Ensure visible pages are updated
                            self.pdf_viewer.canvas.after_idle(self.pdf_viewer._update_visible_pages)
                            
                            logs_console.log(f"Found and centered text on page {page_num + 1} (legacy search)", level='INFO')
                            return
                        
            logs_console.log(f"Text '{text}' not found in PDF", level='INFO')
        except ImportError:
            logs_console.log("pdfplumber not installed. Cannot search text in PDF.", level='ERROR')
        except Exception as e:
            logs_console.log(f"Error searching text in PDF: {e}", level='ERROR')