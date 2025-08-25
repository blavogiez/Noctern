"""
Debug system for LaTeX compilation error analysis and quick fixes.
"""

from .core import DebugContext, AnalysisResult, QuickFix, LaTeXError, DebugUI
from .coordinator import DebugCoordinator, create_debug_system
from .error_parser import LaTeXErrorParser
from .llm_analyzer import LLMAnalyzer
from .quick_fixes import LaTeXQuickFixProvider, EditorFixApplicator
from .diff_service import CachedDiffGenerator
from .debug_ui import TabbedDebugUI

__all__ = [
    'DebugContext',
    'AnalysisResult', 
    'QuickFix',
    'LaTeXError',
    'DebugUI',
    'DebugCoordinator',
    'create_debug_system',
    'LaTeXErrorParser',
    'LLMAnalyzer',
    'LaTeXQuickFixProvider',
    'EditorFixApplicator',
    'CachedDiffGenerator',
    'TabbedDebugUI'
]