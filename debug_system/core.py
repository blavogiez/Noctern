"""
Core debug system interfaces and data structures.
Defines the contracts that all debug components must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class LaTeXError:
    """Represents a LaTeX compilation error with location and context information."""
    line_number: int
    severity: str  # 'Error', 'Warning', 'Info'
    message: str
    suggestion: Optional[str] = None
    context: Optional[str] = None
    raw_log_lines: List[str] = None
    
    def __post_init__(self):
        if self.raw_log_lines is None:
            self.raw_log_lines = []


@dataclass
class QuickFix:
    """Represents an automatic fix that can be applied to resolve an error."""
    title: str
    description: str
    fix_type: str  # 'replace', 'insert', 'remove'
    target_line: Optional[int] = None
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    confidence: float = 0.0
    auto_applicable: bool = False


@dataclass
class AnalysisResult:
    """Results from AI analysis of LaTeX errors."""
    explanation: str
    suggested_fix: Optional[str] = None
    confidence: float = 0.0
    quick_fixes: List[QuickFix] = None
    corrected_code: Optional[str] = None
    raw_analysis: str = ""
    
    def __post_init__(self):
        if self.quick_fixes is None:
            self.quick_fixes = []


@dataclass
class DebugContext:
    """Context information for debug operations."""
    current_file_path: str
    current_content: str
    diff_content: Optional[str] = None
    log_content: Optional[str] = None
    errors: List[LaTeXError] = None
    last_successful_content: Optional[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ErrorParser(ABC):
    """Parses LaTeX compilation logs to extract structured error information."""
    
    @abstractmethod
    def parse_log_content(self, log_content: str, file_path: str = None) -> List[LaTeXError]:
        """Parse log content and return structured errors."""
        pass


class AnalysisEngine(ABC):
    """Analyzes LaTeX errors using AI to provide intelligent suggestions."""
    
    @abstractmethod
    def analyze_errors(self, context: DebugContext) -> AnalysisResult:
        """Analyze errors and provide intelligent suggestions."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the analysis engine is ready to use."""
        pass


class QuickFixProvider(ABC):
    """Provides automatic fixes for common LaTeX errors."""
    
    @abstractmethod
    def get_quick_fixes(self, error: LaTeXError, context: DebugContext) -> List[QuickFix]:
        """Generate quick fixes for a specific error."""
        pass
    
    @abstractmethod
    def can_handle_error(self, error: LaTeXError) -> bool:
        """Check if this provider can handle the given error."""
        pass


class FixApplicator(ABC):
    """Applies fixes to LaTeX code."""
    
    @abstractmethod
    def apply_quick_fix(self, fix: QuickFix, context: DebugContext) -> bool:
        """Apply a quick fix to the code."""
        pass
    
    @abstractmethod
    def apply_corrected_code(self, corrected_code: str, context: DebugContext) -> bool:
        """Apply fully corrected code."""
        pass


class DiffGenerator(ABC):
    """Generates diffs between current and last successful compilation."""
    
    @abstractmethod
    def analyze_current_vs_last_successful(self, file_path: str, current_content: str) -> tuple:
        """Analyze current content vs last successful version.
        
        Returns:
            tuple: (has_previous, diff_content, last_content)
        """
        pass
    
    @abstractmethod
    def display_diff(self, diff_content: str, parent_window=None):
        """Display diff content to user."""
        pass


class DebugUI(ABC):
    """Debug user interface for displaying errors and analysis results."""
    
    @abstractmethod
    def update_compilation_errors(self, log_content: str, file_path: str = None, current_content: str = None):
        """Update UI with compilation errors."""
        pass
    
    @abstractmethod
    def display_analysis_result(self, result: AnalysisResult):
        """Display AI analysis result."""
        pass
    
    @abstractmethod
    def clear_display(self):
        """Clear all displays."""
        pass