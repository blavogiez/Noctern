"""
LaTeX error parser that extracts structured error information from compilation logs.
Supports TeXstudio-style error recognition and categorization.
"""

import re
from typing import List, Optional
from utils import logs_console
from debug_system.core import ErrorParser, LaTeXError


class LaTeXErrorParser(ErrorParser):
    """Parses LaTeX compilation logs to extract structured error information."""
    
    def __init__(self):
        """Initialize the parser with error patterns and strategies."""
        self.error_patterns = [
            (r'! LaTeX Error: (.+)', 'LaTeX Error: {0}'),
            (r'! (.+)', '{0}'),
            (r'.*?Error: (.+)', 'Error: {0}'),
            (r'.*?Warning: (.+)', 'Warning: {0}'),
            (r'Overfull \\hbox \((.+)\)', 'Overfull hbox: {0}'),
            (r'Underfull \\hbox \((.+)\)', 'Underfull hbox: {0}'),
        ]
        
        # Severity classification patterns
        self.severity_patterns = {
            'Error': [r'error', r'fatal', r'emergency', r'failed', r'! '],
            'Warning': [r'warning', r'overfull', r'underfull'],
            'Info': [r'info', r'note']
        }
        
        logs_console.log("LaTeX error parser initialized", level='DEBUG')
    
    def parse_log_content(self, log_content: str, file_path: str = None) -> List[LaTeXError]:
        """Parse log content and return structured errors."""
        if not log_content.strip():
            return []
        
        lines = log_content.splitlines()
        errors = []
        
        logs_console.log(f"Parsing log with {len(lines)} lines", level='DEBUG')
        
        for i, line in enumerate(lines):
            if self._is_error_line(line):
                error = self._parse_error_line(line, lines, i, file_path)
                if error:
                    errors.append(error)
                    logs_console.log(f"Parsed {error.severity}: {error.message} at line {error.line_number}", level='DEBUG')
        
        logs_console.log(f"Found {len(errors)} total errors/warnings", level='INFO')
        return errors
    
    def _is_error_line(self, line: str) -> bool:
        """Check if a line contains an error or warning."""
        error_indicators = ['!', 'Error:', 'Warning:', 'Overfull', 'Underfull', 'Fatal']
        return any(indicator in line for indicator in error_indicators)
    
    def _parse_error_line(self, log_line: str, context_lines: List[str], line_index: int, file_path: str) -> Optional[LaTeXError]:
        """Parse a single error line and extract structured information."""
        # Determine severity
        severity = self._determine_severity(log_line)
        
        # Extract error message
        error_text = self._extract_error_text(log_line)
        if not error_text:
            return None
        
        # Find line number in context
        line_number = self._extract_line_number(context_lines, line_index)
        
        # Try to match specific error patterns and generate suggestions
        message = error_text
        suggestion = None
        
        for pattern, template in self.error_patterns:
            match = re.search(pattern, log_line)
            if match:
                if "{0}" in template:
                    message = template.format(match.group(1))
                else:
                    message = template
                suggestion = self._get_suggestion_for_pattern(pattern, match)
                break
        
        # Special handling for specific error types
        if "File ended while scanning use of" in error_text:
            command_match = re.search(r'File ended while scanning use of \\(\w+)', error_text)
            if command_match:
                command = command_match.group(1)
                message = f"Unclosed command \\{command} - missing closing brace"
                suggestion = f"Add '}}' to close the \\{command} command"
        
        # Get context from surrounding lines
        context = self._extract_context(context_lines, line_index)
        
        return LaTeXError(
            line_number=line_number,
            severity=severity,
            message=message,
            suggestion=suggestion,
            context=context,
            raw_log_lines=[log_line] + context_lines[line_index+1:line_index+3]
        )
    
    def _determine_severity(self, line: str) -> str:
        """Determine the severity level of an error line."""
        line_lower = line.lower()
        
        for severity, patterns in self.severity_patterns.items():
            if any(re.search(pattern, line_lower) for pattern in patterns):
                return severity
        
        return 'Error'  # Default to Error if uncertain
    
    def _extract_error_text(self, line: str) -> str:
        """Extract the main error message from a log line."""
        # Remove common prefixes
        line = re.sub(r'^[!\s]*', '', line)
        line = re.sub(r'^LaTeX\s+', '', line)
        line = re.sub(r'^Error:\s*', '', line)
        line = re.sub(r'^Warning:\s*', '', line)
        
        return line.strip()
    
    def _extract_line_number(self, context_lines: List[str], start_index: int) -> int:
        """Extract line number from context lines."""
        # Try multiple patterns for line numbers
        patterns = [
            re.compile(r'l\.(\d+)'),  # Standard l.15 format
            re.compile(r'on input line (\d+)'),  # "on input line 9" format
            re.compile(r'line (\d+)'),  # Generic "line X" format
        ]
        
        # Search in a range around the error
        search_range = range(max(0, start_index - 2), min(start_index + 8, len(context_lines)))
        
        for i in search_range:
            line = context_lines[i]
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    return int(match.group(1))
        
        # Special handling for end-of-file errors
        if start_index < len(context_lines):
            error_line = context_lines[start_index]
            if "File ended while scanning" in error_line:
                return -1  # Special marker for end-of-file errors
        
        return 0  # Unknown line number
    
    def _extract_context(self, context_lines: List[str], start_index: int) -> Optional[str]:
        """Extract relevant context from surrounding lines."""
        context_parts = []
        
        # Look for context in the next few lines
        for i in range(start_index + 1, min(start_index + 4, len(context_lines))):
            line = context_lines[i].strip()
            if line and not line.startswith('!') and len(line) < 200:
                context_parts.append(line)
        
        return ' '.join(context_parts) if context_parts else None
    
    def _get_suggestion_for_pattern(self, pattern: str, match) -> Optional[str]:
        """Generate suggestion based on error pattern."""
        if "missing" in pattern.lower():
            return "Check for missing braces, brackets, or environment closures"
        elif "undefined" in pattern.lower():
            return "Check spelling or add required package"
        elif "overfull" in pattern.lower():
            return "Consider line breaks or text reformatting"
        
        return None