"""
LaTeX syntax patterns for ultra-fast highlighting.
Optimized regex patterns with smart context detection.
"""
import re

# Enhanced color scheme with high visibility colors
COLORS = {
    # Document structure - More vibrant purples
    'documentclass': '#9C27B0',     # Bright purple for document class
    'package': '#673AB7',           # Deep violet for packages
    'section': '#0D47A1',           # Deep blue for sections
    'subsection': '#1565C0',        # Medium blue for subsections
    'title_commands': '#C2185B',    # Bright pink for title/author/date
    
    # Environments - More visible greens
    'environment': '#2E7D32',       # Forest green for begin/end environments
    'list_env': '#43A047',          # Bright green for itemize/enumerate
    'math_env': '#D32F2F',          # Bright red for math environments
    'figure_env': '#FF8F00',        # Bright amber for figure/table environments
    
    # Commands and text formatting - Enhanced visibility
    'command': '#1976D2',           # Bright blue for general commands
    'text_format': '#E65100',       # Bright orange for textbf, textit, etc.
    'font_size': '#7B1FA2',         # Bright purple for font size commands
    'geometry': '#5D4037',          # Dark brown for geometry and layout
    
    # References and citations - Enhanced teals
    'ref_cite': '#00838F',          # Bright teal for references and citations
    'label': '#006064',             # Dark cyan for labels
    'hyperref': '#0277BD',          # Light blue for hyperref commands
    
    # Math elements - Vibrant reds and pinks
    'math': '#D32F2F',              # Bright red for inline math
    'math_symbols': '#E91E63',      # Hot pink for special math symbols
    
    # Text content - New additions
    'proper_names': '#8E24AA',      # Purple for proper names (Jean Blanc, etc.)
    'braced_content': '#2E7D32',    # Forest green for content in braces {}
    
    # Basic elements - Enhanced visibility
    'comment': '#616161',           # Darker gray for better contrast
    'number': '#F44336',            # Bright red for numbers
    'bracket': '#FF9800',           # Bright orange for brackets
    'string': '#558B2F',            # Dark green for general strings
    
    # Special characters - High contrast
    'special_chars': '#FF5722',     # Red-orange for special characters
    'units': '#3F51B5',             # Indigo for units and measurements
    
    # Text formatting content - Visual styling
    'textit_content': '#E65100',    # Orange for italic content
    'textbf_content': '#000000',    # Black for bold content
    
    # Navigation placeholders - Ultra-visible highlighting
    'placeholder': '#FF1744'        # Bright red for navigation placeholders ⟨content⟩
}

# Optimized regex patterns - ordered from most specific to most general
PATTERNS = {
    # Comments (highest priority)
    'comment': re.compile(r'%[^\n]*', re.MULTILINE),
    
    # Document structure (very specific)
    'documentclass': re.compile(r'\\documentclass(?:\[[^\]]*\])?\{[^}]*\}', re.MULTILINE),
    'package': re.compile(r'\\usepackage(?:\[[^\]]*\])?\{[^}]*\}', re.MULTILINE),
    
    # Sections
    'section': re.compile(r'\\section\*?(?![a-zA-Z])', re.MULTILINE),
    'subsection': re.compile(r'\\(?:sub)+section\*?(?![a-zA-Z])', re.MULTILINE),
    'title_commands': re.compile(r'\\(?:title|author|date)(?![a-zA-Z])', re.MULTILINE),
    
    # Environments (before general patterns)
    'list_env': re.compile(r'\\(?:begin|end)\{(?:itemize|enumerate|description)\}', re.MULTILINE),
    'math_env': re.compile(r'\\(?:begin|end)\{(?:equation|align|gather|split|math|displaymath|eqnarray)\*?\}', re.MULTILINE),
    'figure_env': re.compile(r'\\(?:begin|end)\{(?:figure|table|tabular|array|longtable|tblr|matrix|pmatrix|bmatrix|vmatrix|Vmatrix|Bmatrix|cases|numcases|substack)\*?\}', re.MULTILINE),
    'environment': re.compile(r'\\(?:begin|end)\{[^}]+\}', re.MULTILINE),
    
    # Text formatting
    'text_format': re.compile(r'\\(?:textbf|textit|texttt|textsc|emph|underline|textcolor)(?![a-zA-Z])', re.MULTILINE),
    'font_size': re.compile(r'\\(?:tiny|scriptsize|footnotesize|small|normalsize|large|Large|LARGE|huge|Huge)(?![a-zA-Z])', re.MULTILINE),
    
    # Math content
    'math': re.compile(r'\$[^$\n]*\$|\\\([^)]*\\\)', re.MULTILINE),
    'math_symbols': re.compile(r'\\(?:alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|phi|psi|omega|sum|int|prod|sqrt|frac|partial|infty|nabla|times|cdot|ldots|pm|mp|leq|geq|neq|approx|equiv|subset|supset|in|cup|cap|forall|exists)(?![a-zA-Z])', re.MULTILINE),
    
    # References and citations
    'ref_cite': re.compile(r'\\(?:ref|cite|citet|citep|autoref|nameref|pageref|eqref)(?![a-zA-Z])', re.MULTILINE),
    'label': re.compile(r'\\label\{[^}]*\}', re.MULTILINE),
    'hyperref': re.compile(r'\\(?:href|url|hyperref)(?![a-zA-Z])', re.MULTILINE),
    
    # Text formatting with content
    'textit_content': re.compile(r'\\textit\{([^{}]*)\}', re.MULTILINE),
    'textbf_content': re.compile(r'\\textbf\{([^{}]*)\}', re.MULTILINE),
    
    # Text content patterns
    'proper_names': re.compile(r'(?<!\w)[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?!\w)', re.MULTILINE),
    'braced_content': re.compile(r'\{[^{}]*\}', re.MULTILINE),
    
    # Navigation placeholders (high priority for visibility)
    'placeholder': re.compile(r'⟨[^⟩]*⟩', re.MULTILINE),
    
    # Numbers and basic elements
    'number': re.compile(r'(?<!\w)\d+(?:\.\d+)?(?!\w)', re.MULTILINE),
    'brackets': re.compile(r'[{}\[\]()]', re.MULTILINE),
    
    # General commands (lowest priority)
    'command': re.compile(r'\\[a-zA-Z@]+(?![a-zA-Z@])', re.MULTILINE)
}

def get_relevant_patterns(line_content):
    """
    Ultra-fast pattern filtering based on line content.
    Returns only patterns that could match this line.
    """
    patterns = {}
    
    # Quick pre-filtering
    has_backslash = '\\' in line_content
    has_percent = '%' in line_content
    has_math = '$' in line_content
    has_uppercase = any(c.isupper() for c in line_content)
    has_digits = any(c.isdigit() for c in line_content)
    has_placeholder = '⟨' in line_content and '⟩' in line_content
    
    # Comments
    if has_percent:
        patterns['comment'] = PATTERNS['comment']
    
    # LaTeX patterns (only if backslash present)
    if has_backslash:
        # Document structure
        if 'documentclass' in line_content:
            patterns['documentclass'] = PATTERNS['documentclass']
        if 'usepackage' in line_content:
            patterns['package'] = PATTERNS['package']
        
        # Sections
        if 'section' in line_content:
            patterns['section'] = PATTERNS['section']
            patterns['subsection'] = PATTERNS['subsection']
        if any(cmd in line_content for cmd in ['title', 'author', 'date']):
            patterns['title_commands'] = PATTERNS['title_commands']
        
        # Environments
        if 'begin' in line_content or 'end' in line_content:
            patterns['environment'] = PATTERNS['environment']
            patterns['list_env'] = PATTERNS['list_env']
            patterns['math_env'] = PATTERNS['math_env']
            patterns['figure_env'] = PATTERNS['figure_env']
        
        # Text formatting
        if any(fmt in line_content for fmt in ['textbf', 'textit', 'emph']):
            patterns['text_format'] = PATTERNS['text_format']
            patterns['textit_content'] = PATTERNS['textit_content']
            patterns['textbf_content'] = PATTERNS['textbf_content']
        if any(size in line_content for size in ['tiny', 'large', 'huge']):
            patterns['font_size'] = PATTERNS['font_size']
        
        # References
        if any(ref in line_content for ref in ['ref', 'cite', 'label']):
            patterns['ref_cite'] = PATTERNS['ref_cite']
            patterns['label'] = PATTERNS['label']
        if any(href in line_content for href in ['href', 'url']):
            patterns['hyperref'] = PATTERNS['hyperref']
        
        # General commands (always check if backslash present)
        patterns['command'] = PATTERNS['command']
    
    # Math
    if has_math:
        patterns['math'] = PATTERNS['math']
        patterns['math_symbols'] = PATTERNS['math_symbols']
    
    # Text patterns
    if has_uppercase:
        patterns['proper_names'] = PATTERNS['proper_names']
    if '{' in line_content or '}' in line_content:
        patterns['braced_content'] = PATTERNS['braced_content']
        patterns['brackets'] = PATTERNS['brackets']
    
    # Numbers
    if has_digits:
        patterns['number'] = PATTERNS['number']
    
    # Navigation placeholders (high priority for visibility)
    if has_placeholder:
        patterns['placeholder'] = PATTERNS['placeholder']
    
    return patterns