"""
Debug system for LaTeX compilation error analysis.
"""

from .core import DebugContext, AnalysisResult, LaTeXError, DebugUI
from .coordinator import DebugCoordinator, create_debug_system
from .error_parser import LaTeXErrorParser
from .llm_analyzer import LLMAnalyzer
from .legacy_fix_applicator import LegacyFixApplicator
from .diff_service import CachedDiffGenerator
from .debug_ui import TabbedDebugUI

__all__ = [
    'DebugContext',
    'AnalysisResult',
    'LaTeXError',
    'DebugUI',
    'DebugCoordinator',
    'create_debug_system',
    'LaTeXErrorParser',
    'LLMAnalyzer',
    'LegacyFixApplicator',
    'CachedDiffGenerator',
    'TabbedDebugUI'
]