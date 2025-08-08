import re
import os

class Checker:
    def __init__(self):
        """
        Initializes the pre-compiler checker.
        It detects structural issues and missing file references.
        """
        self.graphics_ext = ['.png', '.jpg', '.jpeg', '.pdf', '.eps', '.svg', '.gif']
        self.tex_ext = ['.tex']
    
    def _resolve_and_check_path(self, base_dir, partial_path, extensions):
        """
        Resolves a relative path against a base directory and checks for its existence,
        trying a list of extensions if none is provided in the path.
        
        Args:
            base_dir (str): Base directory to resolve relative paths
            partial_path (str): Path to check (can be relative or absolute)
            extensions (list): List of extensions to try if path has no extension
            
        Returns:
            bool: True if file exists, False otherwise
        """
        clean_path = partial_path.strip()
        
        # Handle empty paths
        if not clean_path:
            return False
        
        # If the path is absolute, use it directly. Otherwise, join with base_dir.
        if os.path.isabs(clean_path):
            filepath = clean_path
        else:
            filepath = os.path.join(base_dir, clean_path)
        
        # Normalize the path to handle .. and . components
        filepath = os.path.normpath(filepath)
        
        # 1. Check if the path exists as is.
        if os.path.exists(filepath):
            return True
        
        # 2. If the path has no extension, try common ones.
        if not os.path.splitext(filepath)[1]:
            for ext in extensions:
                test_path = filepath + ext
                if os.path.exists(test_path):
                    return True
        
        # 3. For graphics, also try with different case (common on Windows/Mac)
        if extensions == self.graphics_ext:
            base_path = os.path.splitext(filepath)[0]
            existing_ext = os.path.splitext(filepath)[1].lower()
            
            # Try with different case for existing extension
            if existing_ext:
                for ext in extensions:
                    if ext.lower() == existing_ext:
                        test_path = base_path + ext
                        if os.path.exists(test_path):
                            return True
                        # Also try uppercase
                        test_path = base_path + ext.upper()
                        if os.path.exists(test_path):
                            return True
        
        return False
    
    def _extract_graphics_path(self, includegraphics_match):
        """
        Extracts the actual file path from an \\includegraphics command,
        handling optional parameters properly.
        
        Args:
            includegraphics_match: Regex match object for includegraphics command
            
        Returns:
            str: The file path
        """
        full_match = includegraphics_match.group(0)
        
        # More robust regex to handle optional parameters
        # Matches: \includegraphics[...]{filename} or \includegraphics{filename}
        detailed_pattern = r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}'
        match = re.search(detailed_pattern, full_match)
        
        if match:
            return match.group(1)
        
        # Fallback to original method
        return includegraphics_match.group(1)
    
    def check(self, text, file_path=None):
        """
        Checks the document text for pre-compilation errors.
        
        Args:
            text (str): The full content of the document.
            file_path (str, optional): The absolute path of the document being checked.
                                       Used to resolve relative paths for included files.
        Returns:
            list: A list of error dictionaries.
        """
        errors = []
        
        # Use the document's directory as the base for relative paths.
        # Fallback to the current working directory for new, unsaved files.
        if file_path and os.path.exists(file_path):
            base_dir = os.path.dirname(os.path.abspath(file_path))
        else:
            base_dir = os.getcwd()
        
        # Improved regex patterns
        # Handle \input and \include commands
        input_pattern = re.compile(r'\\(?:input|include)\{([^}]+)\}')
        
        # Improved pattern for \includegraphics that handles optional parameters better
        image_pattern = re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')
        
        # Split text into lines for processing
        lines = text.splitlines()
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Skip commented lines (basic check)
            stripped_line = line.strip()
            if stripped_line.startswith('%'):
                continue
            
            # Check for mismatched braces and brackets (only in non-commented parts)
            # Remove comments first
            comment_pos = line.find('%')
            if comment_pos != -1:
                # Check if % is escaped
                if comment_pos == 0 or line[comment_pos - 1] != '\\':
                    line_to_check = line[:comment_pos]
                else:
                    line_to_check = line
            else:
                line_to_check = line
            
            if line_to_check.count('{') != line_to_check.count('}'):
                errors.append({"line": line_num, "error": "Mismatched braces"})
            
            if line_to_check.count('[') != line_to_check.count(']'):
                errors.append({"line": line_num, "error": "Mismatched brackets"})
            
            # Check for missing \input or \include files
            for match in input_pattern.finditer(line):
                filename = match.group(1).strip()
                if filename and not self._resolve_and_check_path(base_dir, filename, self.tex_ext):
                    errors.append({
                        "line": line_num, 
                        "error": f"Missing TeX file: {filename}"
                    })
            
            # Check for missing \includegraphics files
            for match in image_pattern.finditer(line):
                filename = self._extract_graphics_path(match).strip()
                if filename and not self._resolve_and_check_path(base_dir, filename, self.graphics_ext):
                    # Provide more helpful error message
                    tried_extensions = []
                    base_path = os.path.splitext(filename)[0]
                    if not os.path.splitext(filename)[1]:
                        tried_extensions = [base_path + ext for ext in self.graphics_ext]
                    else:
                        tried_extensions = [filename]
                    
                    errors.append({
                        "line": line_num, 
                        "error": f"Missing image: {filename}",
                        "details": f"Searched in: {base_dir}",
                        "tried_paths": tried_extensions[:3]  # Limit to first 3 to avoid clutter
                    })
        
        return errors