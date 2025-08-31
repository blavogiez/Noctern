"""
Text Search Engine Component
Provides intelligent text search with LaTeX-aware preprocessing and fuzzy matching.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple, NamedTuple
from difflib import SequenceMatcher
from utils import logs_console


class SearchResult(NamedTuple):
    """Represents a text search result with position and confidence."""
    page: int
    start_index: int
    length: int
    confidence: float  # 0.0 to 1.0
    matched_text: str
    context_before: str
    context_after: str


class LaTeXPreprocessor:
    """Handles LaTeX-specific text preprocessing for better search accuracy."""
    
    # Common LaTeX command mappings to their rendered equivalents
    LATEX_MAPPINGS = {
        r'\\textbf\{([^}]+)\}': r'\1',  # Bold text
        r'\\textit\{([^}]+)\}': r'\1',  # Italic text
        r'\\emph\{([^}]+)\}': r'\1',    # Emphasis
        r'\\texttt\{([^}]+)\}': r'\1',  # Typewriter text
        r'\\underline\{([^}]+)\}': r'\1',  # Underlined text
        r'\\textsc\{([^}]+)\}': r'\1',  # Small caps
        r'\\textrm\{([^}]+)\}': r'\1',  # Roman text
        r'\\textsf\{([^}]+)\}': r'\1',  # Sans serif
        
        # Math environments
        r'\$([^$]+)\$': r'\1',          # Inline math
        r'\$\$([^$]+)\$\$': r'\1',      # Display math
        r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}': r'\1',
        r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}': r'\1',
        
        # Common symbols
        r'\\&': '&',
        r'\\%': '%',
        r'\\\$': '$',
        r'\\#': '#',
        r'\\_': '_',
        r'\\\\': '\n',  # Line break
        r'\\newline': '\n',
        
        # Quotes
        r'``': '"',
        r"''": '"',
        r'`': "'",
        
        # Spaces and formatting
        r'\\,': ' ',      # Thin space
        r'\\ ': ' ',      # Explicit space
        r'\\quad': '    ', # Quad space
        r'\\qquad': '        ', # Double quad space
        r'~': ' ',        # Non-breaking space
        
        # Accents and special characters
        r"\\'e": 'é',
        r'\\"e': 'ë',
        r'\\`e': 'è',
        r'\\^e': 'ê',
        r"\\'a": 'á',
        r'\\"a': 'ä',
        r'\\`a': 'à',
        r'\\^a': 'â',
        r"\\'o": 'ó',
        r'\\"o': 'ö',
        r'\\`o': 'ò',
        r'\\^o': 'ô',
        r"\\'i": 'í',
        r'\\"i': 'ï',
        r'\\`i': 'ì',
        r'\\^i': 'î',
        r"\\'u": 'ú',
        r'\\"u': 'ü',
        r'\\`u': 'ù',
        r'\\^u': 'û',
        r'\\c\{c\}': 'ç',
    }
    
    def __init__(self):
        """Initialize LaTeX preprocessor."""
        self.compiled_patterns = {}
        for pattern, replacement in self.LATEX_MAPPINGS.items():
            try:
                self.compiled_patterns[re.compile(pattern, re.DOTALL | re.IGNORECASE)] = replacement
            except re.error as e:
                logs_console.log(f"Invalid regex pattern '{pattern}': {e}", level='WARNING')
    
    def preprocess_latex_text(self, latex_text: str) -> str:
        """
        Convert LaTeX source text to a form closer to rendered output.
        
        Args:
            latex_text (str): Raw LaTeX text
            
        Returns:
            str: Preprocessed text closer to PDF rendering
        """
        text = latex_text
        
        # Apply LaTeX command mappings
        for pattern, replacement in self.compiled_patterns.items():
            text = pattern.sub(replacement, text)
        
        # Remove comments
        text = re.sub(r'(?<!\\)%.*$', '', text, flags=re.MULTILINE)
        
        # Remove most remaining LaTeX commands (but preserve their arguments)
        text = re.sub(r'\\[a-zA-Z]+\*?\{([^}]*)\}', r'\1', text)
        text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\s*', ' ', text)
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for better matching (remove accents, case, etc.).
        
        Args:
            text (str): Input text
            
        Returns:
            str: Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove diacritics/accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text


class TextSearchEngine:
    """
    Intelligent text search engine with LaTeX awareness and fuzzy matching.
    Provides fallback search when SyncTeX is unavailable.
    """
    
    def __init__(self):
        """Initialize text search engine."""
        self.preprocessor = LaTeXPreprocessor()
        self.pdf_text_cache: Dict[int, str] = {}  # page -> extracted text
        self.normalized_cache: Dict[int, str] = {}  # page -> normalized text
        logs_console.log("Text Search Engine initialized", level='INFO')
    
    def search_in_pdf(self, pdf_path: str, search_text: str, context_before: str = "", 
                     context_after: str = "", min_confidence: float = 0.3) -> Optional[SearchResult]:
        """
        Search for text in PDF with intelligent LaTeX preprocessing.
        
        Args:
            pdf_path (str): Path to PDF file
            search_text (str): Text to search for
            context_before (str): Context before target text
            context_after (str): Context after target text
            min_confidence (float): Minimum confidence threshold
            
        Returns:
            Optional[SearchResult]: Best search result or None if not found
        """
        if not search_text.strip():
            return None
            
        try:
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                best_result = None
                best_confidence = 0.0
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract and cache page text
                    if page_num not in self.pdf_text_cache:
                        self.pdf_text_cache[page_num] = page.extract_text() or ""
                    
                    page_text = self.pdf_text_cache[page_num]
                    if not page_text:
                        continue
                    
                    # Try different search strategies
                    result = self._search_in_page_text(
                        page_text, search_text, context_before, context_after, 
                        page_num + 1, page.chars or []
                    )
                    
                    if result and result.confidence > best_confidence and result.confidence >= min_confidence:
                        best_confidence = result.confidence
                        best_result = result
                
                return best_result
                
        except ImportError:
            logs_console.log("pdfplumber not installed. Cannot search text in PDF.", level='ERROR')
            return None
        except Exception as e:
            logs_console.log(f"Error searching text in PDF: {e}", level='ERROR')
            return None
    
    def _search_in_page_text(self, page_text: str, search_text: str, 
                           context_before: str, context_after: str, 
                           page_num: int, chars: List) -> Optional[SearchResult]:
        """
        Search for text within a single page using multiple strategies.
        
        Args:
            page_text (str): Extracted page text
            search_text (str): Text to search for
            context_before (str): Context before target
            context_after (str): Context after target
            page_num (int): Page number (1-based)
            chars (List): Character data from pdfplumber
            
        Returns:
            Optional[SearchResult]: Search result or None
        """
        # Strategy 1: Exact match with full context
        if context_before or context_after:
            full_context = context_before + search_text + context_after
            result = self._exact_search(page_text, full_context, page_num, chars)
            if result:
                return result
        
        # Strategy 2: Exact match of target text only
        result = self._exact_search(page_text, search_text, page_num, chars)
        if result:
            return result
        
        # Strategy 3: LaTeX-aware preprocessing
        result = self._latex_aware_search(page_text, search_text, context_before, context_after, page_num, chars)
        if result:
            return result
        
        # Strategy 4: Fuzzy matching
        result = self._fuzzy_search(page_text, search_text, page_num, chars)
        if result:
            return result
        
        return None
    
    def _exact_search(self, page_text: str, search_text: str, page_num: int, chars: List) -> Optional[SearchResult]:
        """Perform exact text search."""
        search_lower = search_text.lower()
        page_lower = page_text.lower()
        
        start_idx = page_lower.find(search_lower)
        if start_idx != -1:
            return SearchResult(
                page=page_num,
                start_index=start_idx,
                length=len(search_text),
                confidence=1.0,
                matched_text=page_text[start_idx:start_idx + len(search_text)],
                context_before=page_text[max(0, start_idx - 50):start_idx],
                context_after=page_text[start_idx + len(search_text):start_idx + len(search_text) + 50]
            )
        
        return None
    
    def _latex_aware_search(self, page_text: str, search_text: str, 
                          context_before: str, context_after: str, 
                          page_num: int, chars: List) -> Optional[SearchResult]:
        """Perform LaTeX-aware search with preprocessing."""
        # Preprocess search text
        processed_search = self.preprocessor.preprocess_latex_text(search_text)
        processed_context_before = self.preprocessor.preprocess_latex_text(context_before)
        processed_context_after = self.preprocessor.preprocess_latex_text(context_after)
        
        # Normalize for comparison
        norm_search = self.preprocessor.normalize_text(processed_search)
        norm_page = self.preprocessor.normalize_text(page_text)
        
        # Try with full context first
        if processed_context_before or processed_context_after:
            full_context = processed_context_before + processed_search + processed_context_after
            norm_full_context = self.preprocessor.normalize_text(full_context)
            
            start_idx = norm_page.find(norm_full_context)
            if start_idx != -1:
                return SearchResult(
                    page=page_num,
                    start_index=start_idx,
                    length=len(norm_full_context),
                    confidence=0.9,
                    matched_text=page_text[start_idx:start_idx + len(norm_full_context)],
                    context_before=page_text[max(0, start_idx - 50):start_idx],
                    context_after=page_text[start_idx + len(norm_full_context):start_idx + len(norm_full_context) + 50]
                )
        
        # Try search text only
        start_idx = norm_page.find(norm_search)
        if start_idx != -1:
            return SearchResult(
                page=page_num,
                start_index=start_idx,
                length=len(norm_search),
                confidence=0.8,
                matched_text=page_text[start_idx:start_idx + len(norm_search)],
                context_before=page_text[max(0, start_idx - 50):start_idx],
                context_after=page_text[start_idx + len(norm_search):start_idx + len(norm_search) + 50]
            )
        
        return None
    
    def _fuzzy_search(self, page_text: str, search_text: str, page_num: int, chars: List) -> Optional[SearchResult]:
        """Perform fuzzy search using sequence matching."""
        norm_search = self.preprocessor.normalize_text(search_text)
        norm_page = self.preprocessor.normalize_text(page_text)
        
        if len(norm_search) < 3:  # Too short for fuzzy matching
            return None
        
        best_ratio = 0.0
        best_start = 0
        best_length = len(norm_search)
        
        # Sliding window fuzzy search
        search_len = len(norm_search)
        for i in range(len(norm_page) - search_len + 1):
            window = norm_page[i:i + search_len]
            ratio = SequenceMatcher(None, norm_search, window).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_start = i
                best_length = search_len
        
        # Also try with some length variation
        for length_var in [-2, -1, 1, 2]:
            adj_length = search_len + length_var
            if adj_length < 1 or adj_length > len(norm_page):
                continue
                
            for i in range(len(norm_page) - adj_length + 1):
                window = norm_page[i:i + adj_length]
                ratio = SequenceMatcher(None, norm_search, window).ratio()
                
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_start = i
                    best_length = adj_length
        
        if best_ratio >= 0.6:  # Minimum fuzzy match threshold
            return SearchResult(
                page=page_num,
                start_index=best_start,
                length=best_length,
                confidence=best_ratio * 0.7,  # Reduce confidence for fuzzy matches
                matched_text=page_text[best_start:best_start + best_length],
                context_before=page_text[max(0, best_start - 50):best_start],
                context_after=page_text[best_start + best_length:best_start + best_length + 50]
            )
        
        return None
    
    def clear_cache(self):
        """Clear cached text data."""
        self.pdf_text_cache.clear()
        self.normalized_cache.clear()
        logs_console.log("Text search cache cleared", level='DEBUG')
    
    def get_cache_size(self) -> int:
        """Get current cache size (number of cached pages)."""
        return len(self.pdf_text_cache)