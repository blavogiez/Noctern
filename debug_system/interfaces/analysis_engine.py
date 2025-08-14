"""
Core interfaces for the intelligent debug analysis engine.
SOLID architecture for LaTeX error analysis and auto-fixing.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from debug_system.latex_error_parser import LaTeXError


@dataclass
class AnalysisResult:
    """Results from LLM analysis of LaTeX errors."""
    explanation: str
    suggested_fix: Optional[str] = None
    confidence: float = 0.0
    quick_fixes: List['QuickFix'] = None
    corrected_code: Optional[str] = None
    raw_analysis: str = ""
    
    def __post_init__(self):
        if self.quick_fixes is None:
            self.quick_fixes = []


@dataclass
class QuickFix:
    """Represents a quick fix that can be applied automatically."""
    title: str
    description: str
    fix_type: str  # "replace", "insert", "remove"
    target_line: Optional[int] = None
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    confidence: float = 0.0
    auto_applicable: bool = False


@dataclass
class DebugContext:
    """Context information for debug analysis."""
    current_file_path: str
    current_content: str
    diff_content: Optional[str] = None
    log_content: Optional[str] = None
    errors: List[LaTeXError] = None
    last_successful_content: Optional[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class IAnalysisEngine(ABC):
    """Interface for LaTeX error analysis engines."""
    
    @abstractmethod
    def analyze_errors(self, context: DebugContext) -> AnalysisResult:
        """Analyze LaTeX errors and provide intelligent suggestions."""
        pass
    
    @abstractmethod
    def analyze_diff(self, diff_content: str, log_content: str = "") -> AnalysisResult:
        """Analyze diff and provide corrections."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the analysis engine is available and ready."""
        pass


class IQuickFixProvider(ABC):
    """Interface for providing quick fixes for common LaTeX errors."""
    
    @abstractmethod
    def get_quick_fixes(self, error: LaTeXError, context: DebugContext) -> List[QuickFix]:
        """Get quick fixes for a specific error."""
        pass
    
    @abstractmethod
    def can_handle_error(self, error: LaTeXError) -> bool:
        """Check if this provider can handle the given error."""
        pass


class IFixApplicator(ABC):
    """Interface for applying fixes to LaTeX code."""
    
    @abstractmethod
    def apply_quick_fix(self, fix: QuickFix, context: DebugContext) -> bool:
        """Apply a quick fix to the code."""
        pass
    
    @abstractmethod
    def apply_corrected_code(self, corrected_code: str, context: DebugContext) -> bool:
        """Apply fully corrected code."""
        pass
    
    @abstractmethod
    def preview_fix(self, fix: QuickFix, context: DebugContext) -> str:
        """Preview what the code would look like after applying the fix."""
        pass


class IAnalysisResultPresenter(ABC):
    """Interface for presenting analysis results to the user."""
    
    @abstractmethod
    def present_analysis(self, result: AnalysisResult, context: DebugContext):
        """Present analysis results to the user."""
        pass
    
    @abstractmethod
    def present_quick_fixes(self, fixes: List[QuickFix], context: DebugContext):
        """Present available quick fixes."""
        pass
    
    @abstractmethod
    def show_fix_preview(self, fix: QuickFix, preview: str):
        """Show preview of a fix before applying."""
        pass


class IDebugWorkflowOrchestrator(ABC):
    """Interface for orchestrating the complete debug workflow."""
    
    @abstractmethod
    def handle_compilation_failure(self, context: DebugContext):
        """Handle compilation failure with complete analysis workflow."""
        pass
    
    @abstractmethod
    def suggest_improvements(self, context: DebugContext):
        """Suggest improvements even for successful compilation."""
        pass
    
    @abstractmethod
    def auto_fix_if_possible(self, context: DebugContext) -> bool:
        """Attempt automatic fixing if confidence is high enough."""
        pass


class IDebugConfiguration(ABC):
    """Interface for debug system configuration."""
    
    @abstractmethod
    def get_auto_fix_threshold(self) -> float:
        """Get confidence threshold for automatic fixes."""
        pass
    
    @abstractmethod
    def is_auto_analysis_enabled(self) -> bool:
        """Check if automatic analysis is enabled."""
        pass
    
    @abstractmethod
    def get_preferred_model(self) -> str:
        """Get preferred LLM model for analysis."""
        pass
    
    @abstractmethod
    def get_analysis_timeout(self) -> int:
        """Get timeout for LLM analysis in seconds."""
        pass