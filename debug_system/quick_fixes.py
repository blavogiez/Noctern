"""
Quick fix system for automatic LaTeX error corrections.
Provides pattern-based fixes and applies them to the editor.
"""

import re
from typing import List, Optional
from utils import debug_console
from debug_system.core import QuickFixProvider, FixApplicator, QuickFix, LaTeXError, DebugContext


class LaTeXQuickFixProvider(QuickFixProvider):
    """Provides quick fixes for common LaTeX errors."""
    
    def __init__(self):
        """Initialize the provider with fix patterns."""
        self.fix_patterns = {
            "unclosed_bracket": {
                "pattern": r"unclosed|missing.*brace|missing.*}",
                "fixes": [
                    QuickFix(
                        title="Add Closing Brace",
                        description="Add missing '}' at end of line",
                        fix_type="insert",
                        new_text="}",
                        confidence=0.9,
                        auto_applicable=True
                    )
                ]
            },
            "missing_begin_document": {
                "pattern": r"missing.*begin.*document",
                "fixes": [
                    QuickFix(
                        title="Add \\begin{document}",
                        description="Add missing \\begin{document} after preamble",
                        fix_type="insert",
                        new_text="\\begin{document}",
                        confidence=0.95,
                        auto_applicable=True
                    )
                ]
            },
            "math_mode_error": {
                "pattern": r"missing.*\$|math mode",
                "fixes": [
                    QuickFix(
                        title="Add Math Mode",
                        description="Wrap content in $ $ for inline math",
                        fix_type="replace",
                        new_text="${}$",
                        confidence=0.8,
                        auto_applicable=False
                    )
                ]
            }
        }
        debug_console.log("LaTeX QuickFix provider initialized", level='DEBUG')
    
    def get_quick_fixes(self, error: LaTeXError, context: DebugContext) -> List[QuickFix]:
        """Generate quick fixes for a specific error."""
        fixes = []
        error_message = error.message.lower()
        
        for fix_type, fix_info in self.fix_patterns.items():
            if re.search(fix_info["pattern"], error_message):
                base_fixes = fix_info["fixes"]
                customized_fixes = self._customize_fixes(base_fixes, error, context)
                fixes.extend(customized_fixes)
        
        # Add parser suggestion as quick fix if available
        if error.suggestion:
            fixes.append(QuickFix(
                title="Apply Parser Suggestion",
                description=error.suggestion,
                fix_type="manual",
                confidence=0.7,
                auto_applicable=False
            ))
        
        debug_console.log(f"Generated {len(fixes)} quick fixes for error: {error.message}", level='DEBUG')
        return fixes
    
    def can_handle_error(self, error: LaTeXError) -> bool:
        """Check if this provider can handle the given error."""
        error_message = error.message.lower()
        
        for fix_info in self.fix_patterns.values():
            if re.search(fix_info["pattern"], error_message):
                return True
        
        return error.suggestion is not None
    
    def _customize_fixes(self, base_fixes: List[QuickFix], error: LaTeXError, context: DebugContext) -> List[QuickFix]:
        """Customize fixes based on error context."""
        customized = []
        
        for fix in base_fixes:
            # Clone and customize the fix
            new_fix = QuickFix(
                title=fix.title,
                description=fix.description,
                fix_type=fix.fix_type,
                target_line=error.line_number if error.line_number > 0 else fix.target_line,
                old_text=fix.old_text,
                new_text=fix.new_text,
                confidence=fix.confidence,
                auto_applicable=fix.auto_applicable
            )
            
            # Position brace fixes at end of file for unclosed commands
            if "unclosed" in error.message.lower() and fix.fix_type == "insert":
                new_fix = self._position_brace_fix(new_fix, error, context)
            
            customized.append(new_fix)
        
        return customized
    
    def _position_brace_fix(self, fix: QuickFix, error: LaTeXError, context: DebugContext) -> QuickFix:
        """Position brace fix at the correct location."""
        if error.line_number == -1:  # End of file error
            # Find the last non-empty line
            lines = context.current_content.splitlines()
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip():
                    fix.target_line = i + 1
                    break
        
        return fix


class EditorFixApplicator(FixApplicator):
    """Applies fixes to LaTeX code in the editor."""
    
    def __init__(self):
        """Initialize the fix applicator."""
        debug_console.log("Editor fix applicator initialized", level='DEBUG')
    
    def apply_quick_fix(self, fix: QuickFix, context: DebugContext) -> bool:
        """Apply a quick fix to the code."""
        try:
            debug_console.log(f"Applying quick fix: {fix.title}", level='INFO')
            
            if fix.fix_type == "replace":
                return self._apply_replace_fix(fix, context)
            elif fix.fix_type == "insert":
                return self._apply_insert_fix(fix, context)
            elif fix.fix_type == "remove":
                return self._apply_remove_fix(fix, context)
            else:
                debug_console.log(f"Unknown fix type: {fix.fix_type}", level='WARNING')
                return False
                
        except Exception as e:
            debug_console.log(f"Error applying fix: {e}", level='ERROR')
            return False
    
    def apply_corrected_code(self, corrected_code: str, context: DebugContext) -> bool:
        """Apply fully corrected code."""
        try:
            debug_console.log("Applying corrected code from LLM", level='INFO')
            
            # Get current editor
            from app import state
            current_tab = state.get_current_tab()
            if not current_tab or not hasattr(current_tab, 'editor'):
                debug_console.log("No active editor for applying correction", level='ERROR')
                return False
            
            # Replace entire content
            editor = current_tab.editor
            editor.delete("1.0", "end")
            editor.insert("1.0", corrected_code)
            
            debug_console.log("Corrected code applied successfully", level='SUCCESS')
            return True
            
        except Exception as e:
            debug_console.log(f"Error applying corrected code: {e}", level='ERROR')
            return False
    
    def _apply_replace_fix(self, fix: QuickFix, context: DebugContext) -> bool:
        """Apply replace-type fix."""
        from app import state
        current_tab = state.get_current_tab()
        if not current_tab or not hasattr(current_tab, 'editor'):
            return False
        
        editor = current_tab.editor
        current_content = editor.get("1.0", "end-1c")
        
        if fix.old_text and fix.old_text in current_content:
            new_content = current_content.replace(fix.old_text, fix.new_text, 1)
            editor.delete("1.0", "end")
            editor.insert("1.0", new_content)
            return True
        
        return False
    
    def _apply_insert_fix(self, fix: QuickFix, context: DebugContext) -> bool:
        """Apply insert-type fix."""
        from app import state
        current_tab = state.get_current_tab()
        if not current_tab or not hasattr(current_tab, 'editor'):
            return False
        
        editor = current_tab.editor
        
        if fix.target_line and fix.target_line > 0:
            # Insert at specific line
            position = f"{fix.target_line}.end"
            editor.insert(position, fix.new_text)
        else:
            # Insert at current cursor or end
            try:
                position = editor.index("insert")
                editor.insert(position, fix.new_text)
            except:
                editor.insert("end", fix.new_text)
        
        return True
    
    def _apply_remove_fix(self, fix: QuickFix, context: DebugContext) -> bool:
        """Apply remove-type fix."""
        from app import state
        current_tab = state.get_current_tab()
        if not current_tab or not hasattr(current_tab, 'editor'):
            return False
        
        editor = current_tab.editor
        current_content = editor.get("1.0", "end-1c")
        
        if fix.old_text and fix.old_text in current_content:
            new_content = current_content.replace(fix.old_text, "", 1)
            editor.delete("1.0", "end")
            editor.insert("1.0", new_content)
            return True
        
        return False