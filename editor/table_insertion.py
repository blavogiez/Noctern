"""
Simple LaTeX table generation for AutomaTeX.
This module provides the TableGenerator class for creating LaTeX table code.
"""

from utils import logs_console


class TableGenerator:
    """Simple LaTeX table code generator with placeholder navigation."""
    
    @staticmethod
    def generate(rows, cols, has_header=True, alignment='c', caption='', label=''):
        """Generate LaTeX table with navigation placeholders."""
        logs_console.log(f"Generating {rows}x{cols} table", level='INFO')
        
        # Build column spec
        col_spec = alignment * cols
        lines = []
        
        # Table environment if needed
        if caption or label:
            lines.append("\\begin{table}[htbp]")
            lines.append("    \\centering")
        
        # Tabular environment
        lines.append(f"    \\begin{{tabular}}{{{col_spec}}}")
        lines.append("        \\hline")
        
        # Generate rows
        for i in range(rows):
            # Create row with placeholders
            cells = []
            for j in range(cols):
                if i == 0 and has_header:
                    cells.append(f"⟨Header {j+1}⟩")
                else:
                    row_num = i if not has_header else i
                    cells.append(f"⟨Cell {row_num+1},{j+1}⟩")
            
            line = "        " + " & ".join(cells) + " \\\\"
            lines.append(line)
            
            # Add horizontal line after header or at end
            if (i == 0 and has_header) or (i == rows - 1):
                lines.append("        \\hline")
        
        # Close tabular
        lines.append("    \\end{tabular}")
        
        # Add caption and label if provided
        if caption:
            lines.append(f"    \\caption{{{caption}}}")
        if label:
            lines.append(f"    \\label{{{label}}}")
            
        # Close table environment if opened
        if caption or label:
            lines.append("\\end{table}")
        
        return "\n".join(lines)