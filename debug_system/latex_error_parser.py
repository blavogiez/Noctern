"""
SOLID LaTeX Error Parser - TeXstudio style error display.
Respecte les principes SOLID et utilise debug_console.
"""

import re
import os
from typing import List, Dict, Optional, NamedTuple
from dataclasses import dataclass
from utils import debug_console

@dataclass
class LaTeXError:
    """Represents a LaTeX compilation error with TeXstudio-style formatting."""
    line_number: int
    severity: str  # "Error", "Warning", "Info"
    message: str
    file_path: Optional[str] = None
    context: Optional[str] = None
    suggestion: Optional[str] = None
    raw_log_lines: List[str] = None

class IErrorParser:
    """Interface for error parsing strategies."""
    
    def can_parse(self, log_line: str) -> bool:
        """Check if this parser can handle the given log line."""
        raise NotImplementedError
    
    def parse(self, log_line: str, context_lines: List[str], line_index: int) -> Optional[LaTeXError]:
        """Parse the error from log line and context."""
        raise NotImplementedError

class CriticalErrorParser(IErrorParser):
    """Parser for critical LaTeX errors."""
    
    def __init__(self):
        self.error_patterns = [
            (r"! LaTeX Error: File `([^']+)' not found", "Missing file: {0}"),
            (r"! LaTeX Error: Unknown option `([^']+)'", "Unknown option: {0}"),
            (r"! LaTeX Error: Can be used only in preamble", "Command not allowed here - move to preamble"),
            (r"! LaTeX Error: Environment (\w+) undefined", "Unknown environment: {0}"),
            (r"! Undefined control sequence", "Undefined command"),
            (r"! Missing \\begin\{document\}", "Missing \\begin{document}"),
            (r"! Extra alignment tab has been changed to \\cr", "Too many columns in table"),
            (r"! Missing \$ inserted", "Math mode error - missing $"),
        ]
    
    def can_parse(self, log_line: str) -> bool:
        return log_line.startswith("! ")
    
    def parse(self, log_line: str, context_lines: List[str], line_index: int) -> Optional[LaTeXError]:
        error_text = log_line[2:].strip()  # Remove "! "
        
        # Find line number in context
        line_number = self._extract_line_number(context_lines, line_index)
        
        # Try to match specific error patterns
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
        
        # Special handling for "File ended while scanning" errors
        if "File ended while scanning use of" in error_text:
            # Try to extract the command that wasn't closed
            command_match = re.search(r'File ended while scanning use of \\(\w+)', error_text)
            if command_match:
                command = command_match.group(1)
                message = f"Unclosed command \\{command} - missing closing brace"
                suggestion = f"Add '}}' to close the \\{command} command"
        
        # Get context from next lines
        context = self._extract_context(context_lines, line_index)
        
        return LaTeXError(
            line_number=line_number,
            severity="Error",
            message=message,
            context=context,
            suggestion=suggestion,
            raw_log_lines=[log_line] + context_lines[line_index+1:line_index+3]
        )
    
    def _extract_line_number(self, context_lines: List[str], start_index: int) -> int:
        """Extract line number from context lines."""
        # Try multiple patterns for line numbers
        patterns = [
            re.compile(r'l\.(\d+)'),  # Standard l.15 format
            re.compile(r'on input line (\d+)'),  # "on input line 9" format
            re.compile(r'line (\d+)'),  # Generic "line X" format
        ]
        
        # Search in a wider range around the error
        search_range = range(max(0, start_index - 2), min(start_index + 8, len(context_lines)))
        
        for i in search_range:
            line = context_lines[i]
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    return int(match.group(1))
        
        # If no line number found, try to infer from common error patterns
        if start_index < len(context_lines):
            error_line = context_lines[start_index]
            # For "File ended while scanning use of \textbf" type errors,
            # the problem is usually at the end of the file
            if "File ended while scanning" in error_line:
                return -1  # Special marker for "end of file" errors
        
        return 0
    
    def _extract_context(self, context_lines: List[str], start_index: int) -> Optional[str]:
        """Extract relevant context from surrounding lines."""
        context_parts = []
        
        for i in range(start_index + 1, min(start_index + 4, len(context_lines))):
            line = context_lines[i].strip()
            if line and not line.startswith('l.') and not line.startswith('?'):
                context_parts.append(line)
        
        return ' '.join(context_parts) if context_parts else None
    
    def _get_suggestion_for_pattern(self, pattern: str, match) -> Optional[str]:
        """Get suggestion based on error pattern."""
        suggestions = {
            r"File `([^']+)' not found": f"Install package or check file path: {match.group(1)}",
            r"Unknown option `([^']+)'": f"Remove option '{match.group(1)}' or check package documentation",
            r"Environment (\w+) undefined": f"Load package that defines '{match.group(1)}' environment",
            r"Undefined control sequence": "Check command spelling or load required package",
            r"Missing \\begin\{document\}": "Add \\begin{document} after preamble",
            r"Extra alignment tab": "Check table column count and alignment",
            r"Missing \$ inserted": "Add $ before and after math expressions"
        }
        
        for pat, suggestion in suggestions.items():
            if pat in pattern:
                return suggestion
        return None

class WarningParser(IErrorParser):
    """Parser for LaTeX warnings."""
    
    def can_parse(self, log_line: str) -> bool:
        return any(keyword in log_line.lower() for keyword in [
            "warning", "overfull", "underfull", "reference", "citation"
        ])
    
    def parse(self, log_line: str, context_lines: List[str], line_index: int) -> Optional[LaTeXError]:
        # Extract warning type and message
        if "overfull" in log_line.lower():
            message = "Overfull hbox - text extends beyond margin"
            severity = "Warning"
        elif "underfull" in log_line.lower():
            message = "Underfull hbox - poor line spacing"
            severity = "Warning"
        elif "reference" in log_line.lower():
            message = "Undefined reference"
            severity = "Warning"
        elif "citation" in log_line.lower():
            message = "Undefined citation"
            severity = "Warning"
        else:
            message = log_line.strip()
            severity = "Warning"
        
        line_number = self._extract_line_number(context_lines, line_index)
        
        return LaTeXError(
            line_number=line_number,
            severity=severity,
            message=message,
            raw_log_lines=[log_line]
        )
    
    def _extract_line_number(self, context_lines: List[str], start_index: int) -> int:
        """Extract line number from context."""
        line_pattern = re.compile(r'line (\d+)')
        
        for i in range(max(0, start_index-2), min(start_index + 3, len(context_lines))):
            match = line_pattern.search(context_lines[i])
            if match:
                return int(match.group(1))
        return 0

class TeXstudioStyleErrorParser:
    """
    Main parser that combines different parsing strategies.
    Follows Open/Closed Principle - easy to extend with new parsers.
    """
    
    def __init__(self):
        self.parsers: List[IErrorParser] = [
            CriticalErrorParser(),
            WarningParser()
        ]
        debug_console.log("TeXstudio-style error parser initialized", level='DEBUG')
    
    def parse_log_content(self, log_content: str, source_file: str = None) -> List[LaTeXError]:
        """
        Parse LaTeX log content and return list of errors in TeXstudio style.
        
        Args:
            log_content: Content of the .log file
            source_file: Path to source .tex file for context
            
        Returns:
            List of parsed LaTeX errors
        """
        if not log_content:
            debug_console.log("Empty log content provided", level='WARNING')
            return []
        
        lines = log_content.splitlines()
        errors = []
        
        debug_console.log(f"Parsing log with {len(lines)} lines", level='DEBUG')
        
        for i, line in enumerate(lines):
            for parser in self.parsers:
                if parser.can_parse(line):
                    try:
                        error = parser.parse(line, lines, i)
                        if error:
                            errors.append(error)
                            debug_console.log(f"Parsed {error.severity}: {error.message} at line {error.line_number}", level='DEBUG')
                        break  # Use first matching parser
                    except Exception as e:
                        debug_console.log(f"Error parsing line {i}: {e}", level='WARNING')
        
        # Sort errors by line number for TeXstudio-like display
        errors.sort(key=lambda x: (x.line_number, x.severity == "Error"))
        
        debug_console.log(f"Found {len(errors)} total errors/warnings", level='INFO')
        return errors
    
    def format_error_for_display(self, error: LaTeXError) -> str:
        """Format error for display in error panel (TeXstudio style)."""
        icon = {"Error": "❌", "Warning": "⚠️", "Info": "ℹ️"}.get(error.severity, "•")
        
        if error.line_number > 0:
            display_text = f"{icon} Line {error.line_number}: {error.message}"
        elif error.line_number == -1:
            display_text = f"{icon} End of file: {error.message}"
        else:
            display_text = f"{icon} {error.message}"
        
        # Truncate for display
        if len(display_text) > 100:
            display_text = display_text[:97] + "..."
        
        return display_text
    
    def get_error_details(self, error: LaTeXError) -> str:
        """Get detailed error information for tooltip/details view."""
        details = [f"Severity: {error.severity}"]
        
        if error.line_number > 0:
            details.append(f"Line: {error.line_number}")
        
        details.append(f"Message: {error.message}")
        
        if error.context:
            details.append(f"Context: {error.context}")
        
        if error.suggestion:
            details.append(f"Suggestion: {error.suggestion}")
        
        return "\n".join(details)
    
    def add_parser(self, parser: IErrorParser):
        """Add a new error parser (Open/Closed Principle)."""
        self.parsers.append(parser)
        debug_console.log(f"Added new error parser: {parser.__class__.__name__}", level='DEBUG')

# Factory for creating parser instances
class ErrorParserFactory:
    """Factory for creating error parser instances."""
    
    @staticmethod
    def create_texstudio_parser() -> TeXstudioStyleErrorParser:
        """Create a TeXstudio-style error parser."""
        return TeXstudioStyleErrorParser()
    
    @staticmethod
    def create_with_custom_parsers(*parsers: IErrorParser) -> TeXstudioStyleErrorParser:
        """Create parser with custom parser strategies."""
        parser = TeXstudioStyleErrorParser()
        parser.parsers.clear()  # Remove default parsers
        for custom_parser in parsers:
            parser.add_parser(custom_parser)
        return parser