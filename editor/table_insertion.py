"""
Professional LaTeX table generation for AutomaTeX.
This module provides multiple table generators for different LaTeX packages.
"""

from utils import logs_console
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
from enum import Enum


class TablePackage(Enum):
    """Available LaTeX table packages."""
    BASIC = "basic"
    BOOKTABS = "booktabs"
    TABULARRAY = "tabularray"
    LONGTABLE = "longtable"
    ARRAY = "array"
    MATRIX = "matrix"
    CASES = "cases"


class PackageTableGenerator(ABC):
    """Abstract base class for LaTeX table generators."""
    
    @property
    @abstractmethod
    def package_name(self) -> str:
        """Package name for LaTeX."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """User-friendly display name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of the package."""
        pass
    
    @property
    @abstractmethod
    def required_packages(self) -> List[str]:
        """LaTeX packages that need to be included."""
        pass
    
    @abstractmethod
    def get_available_options(self) -> Dict[str, Dict[str, Any]]:
        """Get available options for this package."""
        pass
    
    @abstractmethod
    def generate(self, rows: int, cols: int, options: Dict[str, Any]) -> str:
        """Generate LaTeX table code."""
        pass
    
    def get_preview_example(self) -> str:
        """Get a small preview example of the table style."""
        return self.generate(2, 2, self.get_default_options())
    
    def get_default_options(self) -> Dict[str, Any]:
        """Get default options for this generator."""
        defaults = {}
        for option_key, option_config in self.get_available_options().items():
            defaults[option_key] = option_config.get('default')
        return defaults


class BasicTableGenerator(PackageTableGenerator):
    """Standard tabular environment with basic styling."""
    
    @property
    def package_name(self) -> str:
        return "tabular"
    
    @property
    def display_name(self) -> str:
        return "Basic"
    
    @property
    def description(self) -> str:
        return "Standard tabular with customizable borders"
    
    @property
    def required_packages(self) -> List[str]:
        return []  # Built-in LaTeX
    
    def get_available_options(self) -> Dict[str, Dict[str, Any]]:
        return {
            'has_header': {
                'type': 'boolean',
                'label': 'Header row',
                'default': True
            },
            'alignment': {
                'type': 'choice',
                'label': 'Column alignment',
                'choices': [('Left', 'l'), ('Center', 'c'), ('Right', 'r')],
                'default': 'c'
            },
            'vertical_borders': {
                'type': 'boolean',
                'label': 'Vertical borders',
                'default': True
            },
            'horizontal_borders': {
                'type': 'choice',
                'label': 'Horizontal borders',
                'choices': [('None', 'none'), ('Header only', 'header'), ('All rows', 'all')],
                'default': 'header'
            },
            'table_position': {
                'type': 'choice',
                'label': 'Table position',
                'choices': [('Here', 'h'), ('Top', 't'), ('Bottom', 'b'), ('Page', 'p'), ('Here preferred', 'htbp')],
                'default': 'htbp'
            },
            'caption': {
                'type': 'string',
                'label': 'Caption (optional)',
                'default': ''
            },
            'label': {
                'type': 'string',
                'label': 'Label (optional)',
                'default': ''
            }
        }
    
    def generate(self, rows: int, cols: int, options: Dict[str, Any]) -> str:
        """Generate basic tabular table."""
        logs_console.log(f"Generating basic {rows}×{cols} table", level='INFO')
        
        has_header = options.get('has_header', True)
        alignment = options.get('alignment', 'c')
        v_borders = options.get('vertical_borders', True)
        h_borders = options.get('horizontal_borders', 'header')
        position = options.get('table_position', 'htbp')
        caption = options.get('caption', '')
        label = options.get('label', '')
        
        lines = []
        
        # Table environment if caption or label
        if caption or label:
            lines.append(f"\\begin{{table}}[{position}]")
            lines.append("    \\centering")
        
        # Build column spec
        col_spec = alignment * cols
        if v_borders:
            col_spec = '|' + '|'.join(list(col_spec)) + '|'
        
        # Tabular environment
        lines.append(f"    \\begin{{tabular}}{{{col_spec}}}")
        
        # Top border
        if h_borders in ['header', 'all']:
            lines.append("        \\hline")
        
        # Generate rows
        for row in range(rows):
            if row == 0 and has_header:
                cells = [f"⟨Header {i+1}⟩" for i in range(cols)]
                row_text = " & ".join([f"\\textbf{{{cell}}}" for cell in cells]) + " \\\\"
            else:
                data_row = row if not has_header else row
                cells = [f"⟨Data {data_row+1}.{i+1}⟩" for i in range(cols)]
                row_text = " & ".join(cells) + " \\\\"
            
            lines.append(f"        {row_text}")
            
            # Add horizontal lines
            if h_borders == 'all' or (h_borders == 'header' and row == 0 and has_header):
                lines.append("        \\hline")
        
        # Bottom border
        if h_borders in ['header', 'all']:
            lines.append("        \\hline")
        
        lines.append("    \\end{tabular}")
        
        # Caption and label
        if caption or label:
            if caption:
                lines.append(f"    \\caption{{{caption}}}")
            else:
                lines.append("    \\caption{⟨Caption⟩}")
            
            if label:
                lines.append(f"    \\label{{tab:{label}}}")
            else:
                lines.append("    \\label{tab:⟨label⟩}")
            
            lines.append("\\end{table}")
        
        return "\n".join(lines)


class BooktabsGenerator(PackageTableGenerator):
    """Professional tables using booktabs package."""
    
    @property
    def package_name(self) -> str:
        return "booktabs"
    
    @property
    def display_name(self) -> str:
        return "Professional"
    
    @property
    def description(self) -> str:
        return "Clean professional style with booktabs"
    
    @property
    def required_packages(self) -> List[str]:
        return ["booktabs"]
    
    def get_available_options(self) -> Dict[str, Dict[str, Any]]:
        return {
            'has_header': {
                'type': 'boolean',
                'label': 'Header row',
                'default': True
            },
            'alignment': {
                'type': 'choice',
                'label': 'Column alignment',
                'choices': [('Left', 'l'), ('Center', 'c'), ('Right', 'r')],
                'default': 'c'
            },
            'rule_style': {
                'type': 'choice',
                'label': 'Rule style',
                'choices': [('Standard', 'standard'), ('Minimal', 'minimal'), ('Full', 'full')],
                'default': 'standard'
            },
            'column_separation': {
                'type': 'boolean',
                'label': 'Column separations',
                'default': False
            },
            'table_position': {
                'type': 'choice',
                'label': 'Table position',
                'choices': [('Here', 'h'), ('Top', 't'), ('Bottom', 'b'), ('Page', 'p'), ('Here preferred', 'htbp')],
                'default': 'htbp'
            },
            'caption': {
                'type': 'string',
                'label': 'Caption (optional)',
                'default': ''
            },
            'label': {
                'type': 'string',
                'label': 'Label (optional)',
                'default': ''
            }
        }
    
    def generate(self, rows: int, cols: int, options: Dict[str, Any]) -> str:
        """Generate booktabs table."""
        logs_console.log(f"Generating booktabs {rows}×{cols} table", level='INFO')
        
        has_header = options.get('has_header', True)
        alignment = options.get('alignment', 'c')
        rule_style = options.get('rule_style', 'standard')
        col_sep = options.get('column_separation', False)
        position = options.get('table_position', 'htbp')
        caption = options.get('caption', '')
        label = options.get('label', '')
        
        lines = []
        
        # Required packages comment
        if self.required_packages:
            packages_str = ", ".join(self.required_packages)
            lines.append(f"% Required: \\usepackage{{{packages_str}}}")
            lines.append("")
        
        # Table environment if caption or label
        if caption or label:
            lines.append(f"\\begin{{table}}[{position}]")
            lines.append("    \\centering")
        
        # Column spec
        col_spec = alignment * cols
        
        # Tabular environment
        lines.append(f"    \\begin{{tabular}}{{{col_spec}}}")
        
        # Top rule
        lines.append("        \\toprule")
        
        # Generate rows
        for row in range(rows):
            if row == 0 and has_header:
                cells = [f"⟨Header {i+1}⟩" for i in range(cols)]
                row_text = " & ".join([f"\\textbf{{{cell}}}" for cell in cells]) + " \\\\"
                lines.append(f"        {row_text}")
                
                # Mid rule after header
                if rule_style in ['standard', 'full']:
                    lines.append("        \\midrule")
            else:
                data_row = row if not has_header else row
                cells = [f"⟨Data {data_row+1}.{i+1}⟩" for i in range(cols)]
                row_text = " & ".join(cells) + " \\\\"
                lines.append(f"        {row_text}")
                
                # Column separations
                if col_sep and row < rows - 1:
                    mid_cols = cols // 2
                    lines.append(f"        \\cmidrule(lr){{1-{mid_cols}}} \\cmidrule(lr){{{mid_cols+1}-{cols}}}")
        
        # Bottom rule
        lines.append("        \\bottomrule")
        lines.append("    \\end{tabular}")
        
        # Caption and label
        if caption or label:
            if caption:
                lines.append(f"    \\caption{{{caption}}}")
            else:
                lines.append("    \\caption{⟨Caption⟩}")
            
            if label:
                lines.append(f"    \\label{{tab:{label}}}")
            else:
                lines.append("    \\label{tab:⟨label⟩}")
            
            lines.append("\\end{table}")
        
        return "\n".join(lines)


class TabulArrayGenerator(PackageTableGenerator):
    """Modern tables using tabularray package."""
    
    @property
    def package_name(self) -> str:
        return "tabularray"
    
    @property
    def display_name(self) -> str:
        return "Advanced"
    
    @property
    def description(self) -> str:
        return "Modern styling with tabularray features"
    
    @property
    def required_packages(self) -> List[str]:
        return ["tabularray"]
    
    def get_available_options(self) -> Dict[str, Dict[str, Any]]:
        return {
            'has_header': {
                'type': 'boolean',
                'label': 'Header row',
                'default': True
            },
            'alignment': {
                'type': 'choice',
                'label': 'Column alignment',
                'choices': [('Left', 'l'), ('Center', 'c'), ('Right', 'r')],
                'default': 'c'
            },
            'border_style': {
                'type': 'choice',
                'label': 'Border style',
                'choices': [('None', 'none'), ('Outer only', 'outer'), ('All borders', 'all'), ('Custom', 'custom')],
                'default': 'all'
            },
            'header_style': {
                'type': 'choice',
                'label': 'Header styling',
                'choices': [('Bold', 'bold'), ('Background', 'background'), ('Both', 'both')],
                'default': 'both'
            },
            'width_mode': {
                'type': 'choice',
                'label': 'Width mode',
                'choices': [('Auto', 'auto'), ('Fixed', 'fixed'), ('Text width', 'textwidth')],
                'default': 'auto'
            },
            'table_position': {
                'type': 'choice',
                'label': 'Table position',
                'choices': [('Here', 'h'), ('Top', 't'), ('Bottom', 'b'), ('Page', 'p'), ('Here preferred', 'htbp')],
                'default': 'htbp'
            },
            'caption': {
                'type': 'string',
                'label': 'Caption (optional)',
                'default': ''
            },
            'label': {
                'type': 'string',
                'label': 'Label (optional)',
                'default': ''
            }
        }
    
    def generate(self, rows: int, cols: int, options: Dict[str, Any]) -> str:
        """Generate tabularray table."""
        logs_console.log(f"Generating tabularray {rows}×{cols} table", level='INFO')
        
        has_header = options.get('has_header', True)
        alignment = options.get('alignment', 'c')
        border_style = options.get('border_style', 'all')
        header_style = options.get('header_style', 'both')
        width_mode = options.get('width_mode', 'auto')
        position = options.get('table_position', 'htbp')
        caption = options.get('caption', '')
        label = options.get('label', '')
        
        lines = []
        
        # Required packages comment
        if self.required_packages:
            packages_str = ", ".join(self.required_packages)
            lines.append(f"% Required: \\usepackage{{{packages_str}}}")
            lines.append("")
        
        # Table environment if caption or label
        if caption or label:
            lines.append(f"\\begin{{table}}[{position}]")
            lines.append("    \\centering")
        
        # Build tblr options
        tblr_options = []
        
        # Width specification
        if width_mode == 'textwidth':
            tblr_options.append("width = \\textwidth")
        elif width_mode == 'fixed':
            tblr_options.append(f"colspec = {{*{{{cols}}}{{X[c]}}}}")
        else:
            tblr_options.append(f"colspec = {{{alignment * cols}}}")
        
        # Border specifications
        if border_style == 'all':
            tblr_options.append("hlines, vlines")
        elif border_style == 'outer':
            tblr_options.append("hline{1,Z} = {solid}, vline{1,Z} = {solid}")
        elif border_style == 'custom':
            tblr_options.append("hline{1} = {2pt}, hline{2} = {1pt}, hline{Z} = {2pt}")
        
        # Header row styling
        if has_header and header_style in ['background', 'both']:
            tblr_options.append("row{1} = {bg=azure9}")
        
        # Tabularray environment
        if tblr_options:
            options_str = ",\n        ".join(tblr_options)
            lines.append(f"    \\begin{{tblr}}{{")
            lines.append(f"        {options_str}")
            lines.append("    }")
        else:
            lines.append("    \\begin{tblr}{}")
        
        # Generate rows
        for row in range(rows):
            if row == 0 and has_header:
                cells = [f"⟨Header {i+1}⟩" for i in range(cols)]
                if header_style in ['bold', 'both']:
                    row_text = " & ".join([f"\\textbf{{{cell}}}" for cell in cells]) + " \\\\"
                else:
                    row_text = " & ".join(cells) + " \\\\"
            else:
                data_row = row if not has_header else row
                cells = [f"⟨Data {data_row+1}.{i+1}⟩" for i in range(cols)]
                row_text = " & ".join(cells) + " \\\\"
            
            lines.append(f"        {row_text}")
        
        lines.append("    \\end{tblr}")
        
        # Caption and label
        if caption or label:
            if caption:
                lines.append(f"    \\caption{{{caption}}}")
            else:
                lines.append("    \\caption{⟨Caption⟩}")
            
            if label:
                lines.append(f"    \\label{{tab:{label}}}")
            else:
                lines.append("    \\label{tab:⟨label⟩}")
            
            lines.append("\\end{table}")
        
        return "\n".join(lines)


class LongTableGenerator(PackageTableGenerator):
    """Multi-page tables using longtable package."""
    
    @property
    def package_name(self) -> str:
        return "longtable"
    
    @property
    def display_name(self) -> str:
        return "Multi-page"
    
    @property
    def description(self) -> str:
        return "Tables that can span multiple pages"
    
    @property
    def required_packages(self) -> List[str]:
        return ["longtable", "booktabs"]
    
    def get_available_options(self) -> Dict[str, Dict[str, Any]]:
        return {
            'has_header': {
                'type': 'boolean',
                'label': 'Header row',
                'default': True
            },
            'alignment': {
                'type': 'choice',
                'label': 'Column alignment',
                'choices': [('Left', 'l'), ('Center', 'c'), ('Right', 'r')],
                'default': 'c'
            },
            'repeat_header': {
                'type': 'boolean',
                'label': 'Repeat header on each page',
                'default': True
            },
            'page_footer': {
                'type': 'boolean',
                'label': 'Continuation footer',
                'default': True
            },
            'rule_style': {
                'type': 'choice',
                'label': 'Rule style',
                'choices': [('Standard', 'standard'), ('Booktabs', 'booktabs'), ('Minimal', 'minimal')],
                'default': 'booktabs'
            },
            'caption': {
                'type': 'string',
                'label': 'Caption (optional)',
                'default': ''
            },
            'label': {
                'type': 'string',
                'label': 'Label (optional)',
                'default': ''
            }
        }
    
    def generate(self, rows: int, cols: int, options: Dict[str, Any]) -> str:
        """Generate longtable table."""
        logs_console.log(f"Generating longtable {rows}×{cols} table", level='INFO')
        
        has_header = options.get('has_header', True)
        alignment = options.get('alignment', 'c')
        repeat_header = options.get('repeat_header', True)
        page_footer = options.get('page_footer', True)
        rule_style = options.get('rule_style', 'booktabs')
        caption = options.get('caption', '')
        label = options.get('label', '')
        
        lines = []
        
        # Required packages comment
        if self.required_packages:
            packages_str = ", ".join(self.required_packages)
            lines.append(f"% Required: \\usepackage{{{packages_str}}}")
            lines.append("")
        
        # Column spec
        col_spec = alignment * cols
        
        # Longtable environment
        lines.append(f"\\begin{{longtable}}{{{col_spec}}}")
        
        # Caption and label at the top
        if caption:
            lines.append(f"\\caption{{{caption}}} \\\\")
        else:
            lines.append("\\caption{⟨Caption⟩} \\\\")
        
        if label:
            lines.append(f"\\label{{tab:{label}}}")
        else:
            lines.append("\\label{tab:⟨label⟩}")
        
        # First head (appears on first page)
        if rule_style == 'booktabs':
            lines.append("\\toprule")
        else:
            lines.append("\\hline")
        
        if has_header:
            cells = [f"⟨Header {i+1}⟩" for i in range(cols)]
            header_text = " & ".join([f"\\textbf{{{cell}}}" for cell in cells]) + " \\\\"
            lines.append(f"{header_text}")
            
            if rule_style == 'booktabs':
                lines.append("\\midrule")
            else:
                lines.append("\\hline")
        
        lines.append("\\endfirsthead")
        
        # Head for continuation pages
        if repeat_header and has_header:
            lines.append("\\multicolumn{" + str(cols) + "}{c}{\\tablename\\ \\thetable{} -- continued from previous page} \\\\")
            if rule_style == 'booktabs':
                lines.append("\\toprule")
            else:
                lines.append("\\hline")
            
            lines.append(f"{header_text}")
            
            if rule_style == 'booktabs':
                lines.append("\\midrule")
            else:
                lines.append("\\hline")
        
        lines.append("\\endhead")
        
        # Foot for continuation pages
        if page_footer:
            if rule_style == 'booktabs':
                lines.append("\\bottomrule")
            else:
                lines.append("\\hline")
            lines.append("\\multicolumn{" + str(cols) + "}{r}{Continued on next page} \\\\")
        
        lines.append("\\endfoot")
        
        # Last foot (appears on last page)
        if rule_style == 'booktabs':
            lines.append("\\bottomrule")
        else:
            lines.append("\\hline")
        
        lines.append("\\endlastfoot")
        
        # Generate data rows
        start_row = 1 if has_header else 0
        for row in range(start_row, rows):
            data_row = row if not has_header else row
            cells = [f"⟨Data {data_row+1}.{i+1}⟩" for i in range(cols)]
            row_text = " & ".join(cells) + " \\\\"
            lines.append(f"{row_text}")
        
        lines.append("\\end{longtable}")
        
        return "\n".join(lines)


class ArrayGenerator(PackageTableGenerator):
    """Mathematical arrays using array environment."""
    
    @property
    def package_name(self) -> str:
        return "array"
    
    @property
    def display_name(self) -> str:
        return "Math Array"
    
    @property
    def description(self) -> str:
        return "Mathematical arrays with alignment control"
    
    @property
    def required_packages(self) -> List[str]:
        return ["array", "amsmath"]
    
    def get_available_options(self) -> Dict[str, Dict[str, Any]]:
        return {
            'alignment': {
                'type': 'choice',
                'label': 'Column alignment',
                'choices': [('Left', 'l'), ('Center', 'c'), ('Right', 'r')],
                'default': 'c'
            },
            'environment': {
                'type': 'choice',
                'label': 'Math environment',
                'choices': [('Inline', '$'), ('Display', '$$'), ('Equation', 'equation'), ('Align', 'align')],
                'default': '$$'
            },
            'delimiters': {
                'type': 'choice',
                'label': 'Array delimiters',
                'choices': [('None', 'none'), ('Parentheses', 'paren'), ('Brackets', 'bracket'), ('Braces', 'brace'), ('Vertical bars', 'vert')],
                'default': 'none'
            },
            'column_sep': {
                'type': 'choice',
                'label': 'Column separation',
                'choices': [('Default', 'default'), ('Tight', 'tight'), ('Wide', 'wide')],
                'default': 'default'
            }
        }
    
    def generate(self, rows: int, cols: int, options: Dict[str, Any]) -> str:
        """Generate array table."""
        logs_console.log(f"Generating array {rows}×{cols} table", level='INFO')
        
        alignment = options.get('alignment', 'c')
        environment = options.get('environment', '$$')
        delimiters = options.get('delimiters', 'none')
        col_sep = options.get('column_sep', 'default')
        
        lines = []
        
        # Required packages comment
        if self.required_packages:
            packages_str = ", ".join(self.required_packages)
            lines.append(f"% Required: \\usepackage{{{packages_str}}}")
            lines.append("")
        
        # Math environment start
        if environment == '$':
            lines.append("$")
        elif environment == '$$':
            lines.append("$$")
        elif environment == 'equation':
            lines.append("\\begin{equation}")
        elif environment == 'align':
            lines.append("\\begin{align}")
        
        # Delimiter start
        if delimiters == 'paren':
            lines.append("\\left(")
        elif delimiters == 'bracket':
            lines.append("\\left[")
        elif delimiters == 'brace':
            lines.append("\\left\\{")
        elif delimiters == 'vert':
            lines.append("\\left|")
        
        # Array environment
        col_spec = alignment * cols
        if col_sep == 'tight':
            col_spec = '@{}'.join(list(col_spec))
        elif col_sep == 'wide':
            col_spec = '@{\\quad}'.join(list(col_spec))
        
        lines.append(f"\\begin{{array}}{{{col_spec}}}")
        
        # Generate rows
        for row in range(rows):
            cells = [f"⟨a_{{{row+1},{col+1}}}⟩" for col in range(cols)]
            row_text = " & ".join(cells) + " \\\\"
            lines.append(f"    {row_text}")
        
        lines.append("\\end{array}")
        
        # Delimiter end
        if delimiters == 'paren':
            lines.append("\\right)")
        elif delimiters == 'bracket':
            lines.append("\\right]")
        elif delimiters == 'brace':
            lines.append("\\right\\}")
        elif delimiters == 'vert':
            lines.append("\\right|")
        
        # Math environment end
        if environment == '$':
            lines.append("$")
        elif environment == '$$':
            lines.append("$$")
        elif environment == 'equation':
            lines.append("\\end{equation}")
        elif environment == 'align':
            lines.append("\\end{align}")
        
        return "\n".join(lines)


class MatrixGenerator(PackageTableGenerator):
    """AMS matrices using various matrix environments."""
    
    @property
    def package_name(self) -> str:
        return "matrix"
    
    @property
    def display_name(self) -> str:
        return "Matrix"
    
    @property
    def description(self) -> str:
        return "AMS matrix environments with different brackets"
    
    @property
    def required_packages(self) -> List[str]:
        return ["amsmath"]
    
    def get_available_options(self) -> Dict[str, Dict[str, Any]]:
        return {
            'matrix_type': {
                'type': 'choice',
                'label': 'Matrix type',
                'choices': [
                    ('Plain matrix', 'matrix'), 
                    ('Parentheses ()', 'pmatrix'), 
                    ('Brackets []', 'bmatrix'),
                    ('Braces {}', 'Bmatrix'), 
                    ('Vertical bars ||', 'vmatrix'), 
                    ('Double bars ||||', 'Vmatrix')
                ],
                'default': 'pmatrix'
            },
            'environment': {
                'type': 'choice',
                'label': 'Math environment',
                'choices': [('Inline', '$'), ('Display', '$$'), ('Equation', 'equation'), ('Align', 'align')],
                'default': '$$'
            },
            'element_type': {
                'type': 'choice',
                'label': 'Matrix elements',
                'choices': [('Variables', 'variables'), ('Numbers', 'numbers'), ('Fractions', 'fractions'), ('Custom', 'custom')],
                'default': 'variables'
            },
            'variable_base': {
                'type': 'string',
                'label': 'Variable base (for variables)',
                'default': 'a'
            }
        }
    
    def generate(self, rows: int, cols: int, options: Dict[str, Any]) -> str:
        """Generate matrix."""
        logs_console.log(f"Generating matrix {rows}×{cols} table", level='INFO')
        
        matrix_type = options.get('matrix_type', 'pmatrix')
        environment = options.get('environment', '$$')
        element_type = options.get('element_type', 'variables')
        var_base = options.get('variable_base', 'a')
        
        lines = []
        
        # Required packages comment
        if self.required_packages:
            packages_str = ", ".join(self.required_packages)
            lines.append(f"% Required: \\usepackage{{{packages_str}}}")
            lines.append("")
        
        # Math environment start
        if environment == '$':
            lines.append("$")
        elif environment == '$$':
            lines.append("$$")
        elif environment == 'equation':
            lines.append("\\begin{equation}")
        elif environment == 'align':
            lines.append("\\begin{align}")
        
        # Matrix environment
        lines.append(f"\\begin{{{matrix_type}}}")
        
        # Generate rows
        for row in range(rows):
            cells = []
            for col in range(cols):
                if element_type == 'variables':
                    cells.append(f"⟨{var_base}_{{{row+1},{col+1}}}⟩")
                elif element_type == 'numbers':
                    cells.append(f"⟨{(row+1)*(col+1)}⟩")
                elif element_type == 'fractions':
                    cells.append(f"⟨\\frac{{{row+1}}}{{{col+1}}}⟩")
                else:  # custom
                    cells.append(f"⟨{row+1},{col+1}⟩")
            
            row_text = " & ".join(cells) + " \\\\"
            lines.append(f"    {row_text}")
        
        lines.append(f"\\end{{{matrix_type}}}")
        
        # Math environment end
        if environment == '$':
            lines.append("$")
        elif environment == '$$':
            lines.append("$$")
        elif environment == 'equation':
            lines.append("\\end{equation}")
        elif environment == 'align':
            lines.append("\\end{align}")
        
        return "\n".join(lines)


class CasesGenerator(PackageTableGenerator):
    """Cases environment for piecewise functions."""
    
    @property
    def package_name(self) -> str:
        return "cases"
    
    @property
    def display_name(self) -> str:
        return "Cases"
    
    @property
    def description(self) -> str:
        return "Piecewise functions and case distinctions"
    
    @property
    def required_packages(self) -> List[str]:
        return ["amsmath"]
    
    def get_available_options(self) -> Dict[str, Dict[str, Any]]:
        return {
            'cases_type': {
                'type': 'choice',
                'label': 'Cases type',
                'choices': [('Standard cases', 'cases'), ('Numbered cases', 'numcases'), ('Substack', 'substack')],
                'default': 'cases'
            },
            'environment': {
                'type': 'choice',
                'label': 'Math environment',
                'choices': [('Inline', '$'), ('Display', '$$'), ('Equation', 'equation'), ('Align', 'align')],
                'default': '$$'
            },
            'function_name': {
                'type': 'string',
                'label': 'Function name (optional)',
                'default': 'f(x)'
            },
            'condition_style': {
                'type': 'choice',
                'label': 'Condition style',
                'choices': [('Text', 'text'), ('Math', 'math'), ('Mixed', 'mixed')],
                'default': 'text'
            }
        }
    
    def generate(self, rows: int, cols: int, options: Dict[str, Any]) -> str:
        """Generate cases environment."""
        logs_console.log(f"Generating cases with {rows} cases", level='INFO')
        
        cases_type = options.get('cases_type', 'cases')
        environment = options.get('environment', '$$')
        function_name = options.get('function_name', 'f(x)')
        condition_style = options.get('condition_style', 'text')
        
        lines = []
        
        # Required packages comment
        if self.required_packages:
            packages_str = ", ".join(self.required_packages)
            lines.append(f"% Required: \\usepackage{{{packages_str}}}")
            lines.append("")
        
        # Math environment start
        if environment == '$':
            lines.append("$")
        elif environment == '$$':
            lines.append("$$")
        elif environment == 'equation':
            lines.append("\\begin{equation}")
        elif environment == 'align':
            lines.append("\\begin{align}")
        
        # Function definition if provided
        if function_name.strip():
            lines.append(f"{function_name} = ")
        
        # Cases environment
        lines.append(f"\\begin{{{cases_type}}}")
        
        # Generate cases (ignore cols for cases, only use rows)
        for row in range(rows):
            if condition_style == 'text':
                condition = f"\\text{{if }} ⟨condition {row+1}⟩"
            elif condition_style == 'math':
                condition = f"⟨condition_{row+1}⟩"
            else:  # mixed
                condition = f"\\text{{if }} x ⟨op⟩ ⟨{row+1}⟩"
            
            case_line = f"⟨expression_{row+1}⟩ & {condition} \\\\"
            lines.append(f"    {case_line}")
        
        lines.append(f"\\end{{{cases_type}}}")
        
        # Math environment end
        if environment == '$':
            lines.append("$")
        elif environment == '$$':
            lines.append("$$")
        elif environment == 'equation':
            lines.append("\\end{equation}")
        elif environment == 'align':
            lines.append("\\end{align}")
        
        return "\n".join(lines)


class TableGenerator:
    """Factory class for table generators."""
    
    _generators = {
        TablePackage.BASIC: BasicTableGenerator(),
        TablePackage.BOOKTABS: BooktabsGenerator(),
        TablePackage.TABULARRAY: TabulArrayGenerator(),
        TablePackage.LONGTABLE: LongTableGenerator(),
        TablePackage.ARRAY: ArrayGenerator(),
        TablePackage.MATRIX: MatrixGenerator(),
        TablePackage.CASES: CasesGenerator()
    }
    
    @classmethod
    def get_generator(cls, package: TablePackage) -> PackageTableGenerator:
        """Get generator for specified package."""
        return cls._generators[package]
    
    @classmethod
    def get_all_generators(cls) -> Dict[TablePackage, PackageTableGenerator]:
        """Get all available generators."""
        return cls._generators.copy()
    
    @classmethod
    def get_package_info(cls, package: TablePackage) -> Tuple[str, str, str]:
        """Get package display info."""
        generator = cls.get_generator(package)
        return generator.display_name, generator.description, generator.package_name
    
    @staticmethod
    def generate(rows, cols, has_header=True, alignment='c', caption='', label=''):
        """Legacy method for backward compatibility."""
        options = {
            'has_header': has_header,
            'alignment': alignment,
            'caption': caption,
            'label': label,
            'vertical_borders': True,
            'horizontal_borders': 'header',
            'table_position': 'htbp'
        }
        return TableGenerator.get_generator(TablePackage.BASIC).generate(rows, cols, options)