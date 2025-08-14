"""
SOLID Diff Service using existing compiler diff mechanism.
Integrates perfectly with AutomaTeX's existing infrastructure.
"""

import os
import difflib
from typing import Optional, Tuple, List
from utils import debug_console

class IDiffProvider:
    """Interface for providing diff functionality."""
    
    def get_last_successful_version(self, current_file_path: str) -> Optional[str]:
        """Get content of last successful compilation."""
        raise NotImplementedError
    
    def generate_diff(self, old_content: str, new_content: str, old_filename: str = "last_version", new_filename: str = "current") -> str:
        """Generate unified diff between versions."""
        raise NotImplementedError

class ExistingCacheDiffProvider(IDiffProvider):
    """
    Diff provider that uses AutomaTeX's existing cache mechanism.
    Integrates with the cached .tex files from successful compilations.
    """
    
    def __init__(self):
        debug_console.log("ExistingCacheDiffProvider initialized", level='DEBUG')
    
    def get_last_successful_version(self, current_file_path: str) -> Optional[str]:
        """Get content from the existing cache mechanism."""
        if not current_file_path:
            debug_console.log("No current file path provided", level='WARNING')
            return None
        
        # Use the same cache logic as compiler.py
        filename = os.path.basename(current_file_path)
        cached_tex_path = os.path.join("output", f"cached_{filename}")
        
        if not os.path.exists(cached_tex_path):
            debug_console.log(f"No cached version found at {cached_tex_path}", level='DEBUG')
            return None
        
        try:
            with open(cached_tex_path, 'r', encoding='utf-8') as f:
                content = f.read()
                debug_console.log(f"Loaded cached version from {cached_tex_path} ({len(content)} chars)", level='DEBUG')
                return content
        except Exception as e:
            debug_console.log(f"Error reading cached file: {e}", level='ERROR')
            return None
    
    def generate_diff(self, old_content: str, new_content: str, old_filename: str = "last_successful", new_filename: str = "current") -> str:
        """Generate unified diff using the same method as compiler.py."""
        if not old_content or not new_content:
            debug_console.log("Cannot generate diff: missing content", level='WARNING')
            return ""
        
        try:
            # Use the same diff method as in compiler.py
            old_lines = old_content.splitlines(keepends=True)
            new_lines = new_content.splitlines(keepends=True)
            
            diff = difflib.unified_diff(
                old_lines, 
                new_lines, 
                fromfile=old_filename,
                tofile=new_filename,
                lineterm=''
            )
            
            diff_content = '\n'.join(diff)
            debug_console.log(f"Generated diff ({len(diff_content)} chars)", level='DEBUG')
            
            return diff_content
            
        except Exception as e:
            debug_console.log(f"Error generating diff: {e}", level='ERROR')
            return ""

class DiffAnalysisService:
    """
    Service that coordinates diff analysis using existing mechanisms.
    Follows Single Responsibility Principle.
    """
    
    def __init__(self, diff_provider: IDiffProvider):
        self.diff_provider = diff_provider
        debug_console.log("DiffAnalysisService initialized", level='DEBUG')
    
    def analyze_current_vs_last_successful(self, current_file_path: str, current_content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Analyze current content vs last successful version.
        
        Args:
            current_file_path: Path to current file
            current_content: Current file content
            
        Returns:
            Tuple of (has_previous_version, diff_content, last_successful_content)
        """
        debug_console.log(f"Analyzing diff for {os.path.basename(current_file_path) if current_file_path else 'unknown'}", level='INFO')
        
        # Get last successful version
        last_content = self.diff_provider.get_last_successful_version(current_file_path)
        
        if not last_content:
            debug_console.log("No previous successful version found", level='INFO')
            return False, None, None
        
        # Generate diff
        diff_content = self.diff_provider.generate_diff(last_content, current_content)
        
        if not diff_content.strip():
            debug_console.log("No differences found between versions", level='INFO')
            return True, "", last_content
        
        debug_console.log("Differences found - diff generated", level='INFO')
        return True, diff_content, last_content
    
    def trigger_existing_llm_analysis(self, diff_content: str, log_content: str = ""):
        """
        Log diff analysis - LLM analysis disabled to avoid conflicts.
        The TeXstudio-style debug panel handles error display directly.
        """
        if not diff_content.strip():
            debug_console.log("No diff content to analyze", level='DEBUG')
            return
        
        # Log the diff for debugging purposes
        debug_console.log("Diff analysis available but LLM analysis disabled to avoid UI conflicts", level='INFO')
        debug_console.log(f"Diff summary: {len(diff_content.splitlines())} lines changed", level='INFO')
        
        # Note: The TeXstudio error panel now handles error display directly
        # without needing the old LLM dialog system

class DiffServiceFactory:
    """Factory for creating diff service instances."""
    
    @staticmethod
    def create_with_existing_cache() -> DiffAnalysisService:
        """Create diff service using existing cache mechanism."""
        provider = ExistingCacheDiffProvider()
        return DiffAnalysisService(provider)
    
    @staticmethod
    def create_with_custom_provider(provider: IDiffProvider) -> DiffAnalysisService:
        """Create diff service with custom provider."""
        return DiffAnalysisService(provider)