"""
Générateur de différences textuelles optimisé pour LaTeX.
Respecte le principe de responsabilité unique (Single Responsibility Principle).
"""

import difflib
import re
from typing import List, Dict
from ..interfaces.diff_generator import IDiffGenerator, DiffLine, DiffType

class LaTeXDiffGenerator(IDiffGenerator):
    """Générateur de différences spécialisé pour les documents LaTeX."""
    
    def __init__(self):
        """Initialise le générateur de diff LaTeX."""
        # Patterns pour identifier les éléments critiques LaTeX
        self.critical_patterns = [
            r'\\(?:section|subsection|subsubsection)\{[^}]*\}',
            r'\\(?:begin|end)\{[^}]*\}',
            r'\\(?:documentclass|usepackage)\{[^}]*\}',
            r'\\(?:input|include|includegraphics)\{[^}]*\}',
            r'\\(?:label|ref|cite)\{[^}]*\}',
            r'\\(?:newcommand|renewcommand|def)\{[^}]*\}'
        ]
        self.compiled_patterns = [re.compile(pattern) for pattern in self.critical_patterns]
    
    def generate_diff(self, old_content: str, new_content: str) -> List[DiffLine]:
        """Génère les différences entre deux contenus."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        diff_lines = []
        
        # Utiliser difflib pour obtenir les opérations de différence
        differ = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        new_line_num = 1
        old_line_num = 1
        
        for op, old_start, old_end, new_start, new_end in differ.get_opcodes():
            if op == 'equal':
                # Lignes identiques
                for i in range(new_start, new_end):
                    diff_lines.append(DiffLine(
                        line_number=new_line_num,
                        content=new_lines[i],
                        diff_type=DiffType.UNCHANGED,
                        old_line_number=old_line_num
                    ))
                    new_line_num += 1
                    old_line_num += 1
            
            elif op == 'delete':
                # Lignes supprimées
                for i in range(old_start, old_end):
                    diff_lines.append(DiffLine(
                        line_number=new_line_num - 1,  # Position approximative
                        content=old_lines[i],
                        diff_type=DiffType.DELETION,
                        old_line_number=old_line_num
                    ))
                    old_line_num += 1
            
            elif op == 'insert':
                # Lignes ajoutées
                for i in range(new_start, new_end):
                    diff_lines.append(DiffLine(
                        line_number=new_line_num,
                        content=new_lines[i],
                        diff_type=DiffType.ADDITION
                    ))
                    new_line_num += 1
            
            elif op == 'replace':
                # Lignes modifiées (d'abord les suppressions, puis les ajouts)
                for i in range(old_start, old_end):
                    diff_lines.append(DiffLine(
                        line_number=new_line_num - 1,
                        content=old_lines[i],
                        diff_type=DiffType.DELETION,
                        old_line_number=old_line_num + i - old_start
                    ))
                    old_line_num += 1
                
                for i in range(new_start, new_end):
                    diff_lines.append(DiffLine(
                        line_number=new_line_num,
                        content=new_lines[i],
                        diff_type=DiffType.MODIFICATION
                    ))
                    new_line_num += 1
        
        return diff_lines
    
    def get_diff_statistics(self, diff_lines: List[DiffLine]) -> Dict[str, int]:
        """Calcule les statistiques du diff."""
        stats = {
            "additions": 0,
            "deletions": 0,
            "modifications": 0,
            "unchanged": 0,
            "total_lines": len(diff_lines)
        }
        
        for line in diff_lines:
            if line.diff_type == DiffType.ADDITION:
                stats["additions"] += 1
            elif line.diff_type == DiffType.DELETION:
                stats["deletions"] += 1
            elif line.diff_type == DiffType.MODIFICATION:
                stats["modifications"] += 1
            elif line.diff_type == DiffType.UNCHANGED:
                stats["unchanged"] += 1
        
        return stats
    
    def find_critical_changes(self, diff_lines: List[DiffLine]) -> List[DiffLine]:
        """Identifie les changements critiques."""
        critical_lines = []
        
        for line in diff_lines:
            if line.diff_type == DiffType.UNCHANGED:
                continue
            
            # Vérifier si la ligne contient des éléments LaTeX critiques
            if self._is_critical_line(line.content):
                critical_lines.append(line)
        
        return critical_lines
    
    def _is_critical_line(self, line: str) -> bool:
        """Vérifie si une ligne contient des éléments LaTeX critiques."""
        line_stripped = line.strip()
        
        # Ignorer les commentaires
        if line_stripped.startswith('%'):
            return False
        
        # Vérifier contre les patterns critiques
        for pattern in self.compiled_patterns:
            if pattern.search(line):
                return True
        
        # Vérifications supplémentaires
        critical_keywords = [
            '\\documentclass', '\\begin{document}', '\\end{document}',
            '\\maketitle', '\\tableofcontents', '\\bibliography'
        ]
        
        for keyword in critical_keywords:
            if keyword in line:
                return True
        
        return False
    
    def generate_unified_diff(self, old_content: str, new_content: str, 
                            context_lines: int = 3) -> str:
        """Génère un diff unifié (format standard)."""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines, 
            new_lines, 
            fromfile='Dernière version compilée',
            tofile='Version actuelle',
            n=context_lines
        )
        
        return ''.join(diff)
    
    def get_context_around_change(self, diff_lines: List[DiffLine], 
                                 target_line: int, context_size: int = 3) -> List[DiffLine]:
        """Récupère le contexte autour d'un changement."""
        target_index = None
        
        # Trouver l'index de la ligne cible
        for i, line in enumerate(diff_lines):
            if line.line_number == target_line and line.diff_type != DiffType.UNCHANGED:
                target_index = i
                break
        
        if target_index is None:
            return []
        
        # Extraire le contexte
        start_index = max(0, target_index - context_size)
        end_index = min(len(diff_lines), target_index + context_size + 1)
        
        return diff_lines[start_index:end_index]