"""
Legacy fix applicator for corrected code application only.
Maintains only the corrected code application functionality.
"""

from utils import logs_console
from latex_debug_system.core import FixApplicator, DebugContext


class LegacyFixApplicator(FixApplicator):
    """Applies corrected code from LLM analysis only."""

    def __init__(self):
        """Initialize the legacy fix applicator."""
        logs_console.log("Legacy fix applicator initialized", level='DEBUG')

    def apply_corrected_code(self, corrected_code: str, context: DebugContext) -> bool:
        """Apply fully corrected code."""
        try:
            logs_console.log("Applying corrected code from LLM", level='INFO')

            # Get current editor
            from app import state
            current_tab = state.get_current_tab()
            if not current_tab or not hasattr(current_tab, 'editor'):
                logs_console.log("No active editor for applying correction", level='ERROR')
                return False

            # Replace entire content
            editor = current_tab.editor
            editor.delete("1.0", "end")
            editor.insert("1.0", corrected_code)

            logs_console.log("Corrected code applied successfully", level='SUCCESS')
            return True

        except Exception as e:
            logs_console.log(f"Error applying corrected code: {e}", level='ERROR')
            return False