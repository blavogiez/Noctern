"""
Détecteur d'erreurs de compilation LaTeX.
Respecte le principe ouvert/fermé (Open/Closed Principle).
"""

import re
import os
from typing import List, Dict
from ..interfaces.error_detector import IErrorDetector, LaTeXError, ErrorSeverity

class CompilationErrorDetector(IErrorDetector):
    """Détecteur d'erreurs spécialisé pour la compilation LaTeX."""
    
    def __init__(self):
        """Initialise le détecteur d'erreurs."""
        self.error_patterns = self._initialize_error_patterns()
        self.graphics_extensions = ['.png', '.jpg', '.jpeg', '.pdf', '.eps', '.svg', '.gif']
        self.tex_extensions = ['.tex']
    
    def _initialize_error_patterns(self) -> List[Dict]:
        """Initialise les patterns de détection d'erreurs."""
        return [
            # Erreurs critiques
            {
                "pattern": r"\\begin\{(\w+)\}.*?(?!\\end\{\1\})",
                "type": "unclosed_environment",
                "severity": ErrorSeverity.CRITICAL,
                "message": "Environnement '{env}' non fermé",
                "suggestion": "Ajoutez \\end{{{env}}}"
            },
            {
                "pattern": r"\\end\{(\w+)\}",
                "type": "unmatched_end",
                "severity": ErrorSeverity.CRITICAL,
                "message": "\\end{{{env}}} sans \\begin{{{env}}} correspondant",
                "suggestion": "Vérifiez l'ouverture de l'environnement"
            },
            {
                "pattern": r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*(?!\})",
                "type": "unclosed_brace",
                "severity": ErrorSeverity.CRITICAL,
                "message": "Accolade '{' non fermée",
                "suggestion": "Ajoutez '}' manquante"
            },
            {
                "pattern": r"\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*(?!\])",
                "type": "unclosed_bracket",
                "severity": ErrorSeverity.CRITICAL,
                "message": "Crochet '[' non fermé",
                "suggestion": "Ajoutez ']' manquant"
            },
            
            # Erreurs de références
            {
                "pattern": r"\\(?:input|include)\{([^}]+)\}",
                "type": "missing_file",
                "severity": ErrorSeverity.CRITICAL,
                "message": "Fichier '{file}' introuvable",
                "suggestion": "Vérifiez le chemin et l'existence du fichier"
            },
            {
                "pattern": r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",
                "type": "missing_image",
                "severity": ErrorSeverity.CRITICAL,
                "message": "Image '{file}' introuvable",
                "suggestion": "Vérifiez le chemin et l'existence de l'image"
            },
            
            # Avertissements
            {
                "pattern": r"\\ref\{([^}]*)\}",
                "type": "undefined_reference",
                "severity": ErrorSeverity.WARNING,
                "message": "Référence '{ref}' potentiellement non définie",
                "suggestion": "Assurez-vous qu'un \\label{{{ref}}} existe"
            },
            {
                "pattern": r"\\cite\{([^}]*)\}",
                "type": "undefined_citation",
                "severity": ErrorSeverity.WARNING,
                "message": "Citation '{cite}' potentiellement non définie",
                "suggestion": "Vérifiez votre fichier de bibliographie"
            },
            
            # Informations
            {
                "pattern": r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}",
                "type": "package_usage",
                "severity": ErrorSeverity.INFO,
                "message": "Package '{package}' utilisé",
                "suggestion": None
            }
        ]
    
    def detect_errors(self, content: str, file_path: str = None) -> List[LaTeXError]:
        """Détecte les erreurs dans le contenu LaTeX."""
        errors = []
        lines = content.splitlines()
        
        # Déterminer le répertoire de base pour les fichiers
        base_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else os.getcwd()
        
        # Analyser ligne par ligne
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires complets
            if line_stripped.startswith('%'):
                continue
            
            # Supprimer les commentaires en fin de ligne
            comment_pos = line.find('%')
            if comment_pos != -1 and (comment_pos == 0 or line[comment_pos - 1] != '\\'):
                line_to_check = line[:comment_pos]
            else:
                line_to_check = line
            
            # Appliquer tous les patterns
            for pattern_info in self.error_patterns:
                errors.extend(self._check_pattern(
                    pattern_info, line_to_check, line_num, base_dir
                ))
        
        # Vérifications globales
        errors.extend(self._check_global_structure(content))
        
        return errors
    
    def _check_pattern(self, pattern_info: Dict, line: str, line_num: int, base_dir: str) -> List[LaTeXError]:
        """Vérifie un pattern spécifique sur une ligne."""
        errors = []
        pattern = pattern_info["pattern"]
        matches = re.finditer(pattern, line)
        
        for match in matches:
            error_type = pattern_info["type"]
            severity = pattern_info["severity"]
            
            # Construire le message d'erreur
            message = pattern_info["message"]
            suggestion = pattern_info["suggestion"]
            
            # Remplacer les placeholders dans le message
            if error_type == "missing_file":
                filename = match.group(1)
                if not self._file_exists(base_dir, filename, self.tex_extensions):
                    message = message.format(file=filename)
                    if suggestion:
                        suggestion = suggestion.format(file=filename)
                else:
                    continue  # Fichier existe, pas d'erreur
            
            elif error_type == "missing_image":
                filename = match.group(1)
                if not self._file_exists(base_dir, filename, self.graphics_extensions):
                    message = message.format(file=filename)
                    if suggestion:
                        suggestion = suggestion.format(file=filename)
                else:
                    continue  # Image existe, pas d'erreur
            
            elif "env" in message:
                env_name = match.group(1) if match.lastindex >= 1 else "unknown"
                message = message.format(env=env_name)
                if suggestion:
                    suggestion = suggestion.format(env=env_name)
            
            elif "ref" in message:
                ref_name = match.group(1) if match.lastindex >= 1 else "unknown"
                message = message.format(ref=ref_name)
                if suggestion:
                    suggestion = suggestion.format(ref=ref_name)
            
            elif "cite" in message:
                cite_name = match.group(1) if match.lastindex >= 1 else "unknown"
                message = message.format(cite=cite_name)
                if suggestion:
                    suggestion = suggestion.format(cite=cite_name)
            
            elif "package" in message:
                package_name = match.group(1) if match.lastindex >= 1 else "unknown"
                message = message.format(package=package_name)
                if suggestion:
                    suggestion = suggestion.format(package=package_name)
            
            # Créer l'erreur
            error = LaTeXError(
                line_number=line_num,
                error_message=message,
                severity=severity,
                error_type=error_type,
                suggestion=suggestion
            )
            
            errors.append(error)
        
        return errors
    
    def _check_global_structure(self, content: str) -> List[LaTeXError]:
        """Effectue des vérifications globales sur la structure du document."""
        errors = []
        
        # Vérifier les environnements non fermés
        errors.extend(self._check_unmatched_environments(content))
        
        # Vérifier les accolades non appariées
        errors.extend(self._check_unmatched_braces(content))
        
        return errors
    
    def _check_unmatched_environments(self, content: str) -> List[LaTeXError]:
        """Vérifie les environnements non appariés."""
        errors = []
        lines = content.splitlines()
        env_stack = []
        
        for line_num, line in enumerate(lines, 1):
            # Trouver les \begin
            begin_matches = re.finditer(r'\\begin\{(\w+)\}', line)
            for match in begin_matches:
                env_name = match.group(1)
                env_stack.append((env_name, line_num))
            
            # Trouver les \end
            end_matches = re.finditer(r'\\end\{(\w+)\}', line)
            for match in end_matches:
                env_name = match.group(1)
                
                if not env_stack:
                    # \end sans \begin correspondant
                    errors.append(LaTeXError(
                        line_number=line_num,
                        error_message=f"\\end{{{env_name}}} sans \\begin{{{env_name}}} correspondant",
                        severity=ErrorSeverity.CRITICAL,
                        error_type="unmatched_end",
                        suggestion=f"Ajoutez \\begin{{{env_name}}} avant cette ligne"
                    ))
                elif env_stack[-1][0] != env_name:
                    # Environnements imbriqués incorrectement
                    expected_env, expected_line = env_stack[-1]
                    errors.append(LaTeXError(
                        line_number=line_num,
                        error_message=f"\\end{{{env_name}}} ne correspond pas à \\begin{{{expected_env}}} (ligne {expected_line})",
                        severity=ErrorSeverity.CRITICAL,
                        error_type="mismatched_environment",
                        suggestion=f"Utilisez \\end{{{expected_env}}} ou vérifiez l'imbrication"
                    ))
                else:
                    # Environnement correctement fermé
                    env_stack.pop()
        
        # Environnements non fermés
        for env_name, line_num in env_stack:
            errors.append(LaTeXError(
                line_number=line_num,
                error_message=f"Environnement {env_name} non fermé",
                severity=ErrorSeverity.CRITICAL,
                error_type="unclosed_environment",
                suggestion=f"Ajoutez \\end{{{env_name}}}"
            ))
        
        return errors
    
    def _check_unmatched_braces(self, content: str) -> List[LaTeXError]:
        """Vérifie les accolades non appariées."""
        errors = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Compter les accolades en ignorant les échappées
            brace_count = 0
            i = 0
            while i < len(line):
                if line[i] == '\\' and i + 1 < len(line):
                    # Ignorer le caractère échappé
                    i += 2
                elif line[i] == '{':
                    brace_count += 1
                    i += 1
                elif line[i] == '}':
                    brace_count -= 1
                    i += 1
                else:
                    i += 1
            
            if brace_count != 0:
                error_message = "Accolades non appariées sur cette ligne"
                if brace_count > 0:
                    error_message += f" ({brace_count} '{{' de plus)"
                    suggestion = f"Ajoutez {brace_count} '}}' manquante(s)"
                else:
                    error_message += f" ({-brace_count} '}}' de plus)"
                    suggestion = f"Supprimez {-brace_count} '}}' en trop"
                
                errors.append(LaTeXError(
                    line_number=line_num,
                    error_message=error_message,
                    severity=ErrorSeverity.CRITICAL,
                    error_type="unmatched_braces",
                    suggestion=suggestion
                ))
        
        return errors
    
    def _file_exists(self, base_dir: str, filename: str, extensions: List[str]) -> bool:
        """Vérifie si un fichier existe avec les extensions possibles."""
        # Même logique que l'ancien pre-compiler
        clean_path = filename.strip()
        if not clean_path:
            return False
        
        if os.path.isabs(clean_path):
            filepath = clean_path
        else:
            filepath = os.path.join(base_dir, clean_path)
        
        filepath = os.path.normpath(filepath)
        
        # Vérifier tel quel
        if os.path.exists(filepath):
            return True
        
        # Essayer avec extensions si pas d'extension
        if not os.path.splitext(filepath)[1]:
            for ext in extensions:
                test_path = filepath + ext
                if os.path.exists(test_path):
                    return True
        
        return False
    
    def get_error_categories(self) -> List[str]:
        """Retourne les catégories d'erreurs détectables."""
        return [
            "unclosed_environment",
            "unmatched_end", 
            "unclosed_brace",
            "unclosed_bracket",
            "missing_file",
            "missing_image",
            "undefined_reference",
            "undefined_citation",
            "package_usage",
            "mismatched_environment",
            "unmatched_braces"
        ]
    
    def is_compilation_blocking(self, error: LaTeXError) -> bool:
        """Détermine si une erreur empêche la compilation."""
        return error.severity == ErrorSeverity.CRITICAL