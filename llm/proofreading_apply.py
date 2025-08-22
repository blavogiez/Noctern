"""
Apply proofreading corrections module.
Handle bulk application of corrections and file generation.
"""
import os
from typing import List, Tuple, Optional
from tkinter import messagebox

from llm.proofreading_service import ProofreadingError
from llm import state as llm_state
from utils import debug_console


class ProofreadingApplier:
    """Handle application of proofreading corrections."""
    
    def __init__(self):
        self.last_applied_count = 0
        self.last_file_path = None
    
    def apply_all_corrections(self, 
                            errors: List[ProofreadingError], 
                            original_text: str,
                            parent_window=None) -> Tuple[bool, Optional[str]]:
        """
        Apply all approved corrections and save to corrected file.
        
        Args:
            errors: List of proofreading errors (only approved ones will be applied)
            original_text: Original text content
            parent_window: Parent window for dialogs
            
        Returns:
            Tuple of (success, corrected_file_path)
        """
        # Filter to only approved errors
        approved_errors = [error for error in errors if error.is_approved]
        
        if not approved_errors:
            if parent_window:
                messagebox.showwarning("No Approved Corrections", "No corrections have been approved for application.", parent=parent_window)
            return False, None
        
        try:
            # Apply corrections to text (only approved ones)
            corrected_text = self._apply_corrections_to_text(original_text, approved_errors)
            
            # Generate corrected file path
            corrected_filepath = self._generate_corrected_filepath()
            
            # Save corrected file
            self._save_corrected_file(corrected_text, corrected_filepath)
            
            # Mark approved errors as applied
            for error in approved_errors:
                error.is_applied = True
            
            # Store results
            self.last_applied_count = len(approved_errors)
            self.last_file_path = corrected_filepath
            
            # Show success message
            if parent_window:
                messagebox.showinfo(
                    "Corrections Applied", 
                    f"Applied {len(approved_errors)} approved corrections and saved to:\n{corrected_filepath}",
                    parent=parent_window
                )
            
            debug_console.log(f"Applied {len(approved_errors)} approved corrections and saved to: {corrected_filepath}", level='SUCCESS')
            return True, corrected_filepath
            
        except Exception as e:
            error_msg = f"Failed to apply corrections: {str(e)}"
            debug_console.log(error_msg, level='ERROR')
            if parent_window:
                messagebox.showerror("Application Error", error_msg, parent=parent_window)
            return False, None
    
    def _apply_corrections_to_text(self, original_text: str, errors: List[ProofreadingError]) -> str:
        """Apply corrections to text content with perfect positioning."""
        
        # Create list of corrections with positions (avoid duplicates)
        corrections = []
        used_positions = set()
        
        for i, error in enumerate(errors, 1):
            start_pos = original_text.find(error.original)
            if start_pos != -1:
                # Check if this exact position range is already used
                position_key = (start_pos, start_pos + len(error.original))
                if position_key not in used_positions:
                    corrections.append({
                        'start': start_pos,
                        'end': start_pos + len(error.original),
                        'original': error.original,
                        'suggestion': error.suggestion,
                        'explanation': error.explanation,
                        'anchor': i,
                        'error': error
                    })
                    used_positions.add(position_key)
                    debug_console.log(f"Added correction at pos {start_pos}-{start_pos + len(error.original)}: '{error.original[:30]}...'", level='DEBUG')
                else:
                    debug_console.log(f"Duplicate position {start_pos}-{start_pos + len(error.original)} skipped for: '{error.original[:30]}...'", level='DEBUG')
            else:
                debug_console.log(f"Original text not found: '{error.original[:50]}...'", level='WARNING')
        
        # Sort corrections by start position (from end to beginning to preserve positions)
        corrections.sort(key=lambda x: x['start'], reverse=True)
        
        # Remove overlapping corrections intelligently
        filtered_corrections = []
        for correction in corrections:
            should_add = True
            existing_to_remove = []
            
            for existing in filtered_corrections:
                # Check if there's any overlap
                if (correction['start'] < existing['end'] and correction['end'] > existing['start']):
                    # Priority rules:
                    # 1. If one correction completely contains the other, keep the larger one
                    # 2. If corrections partially overlap, keep the one with higher priority
                    
                    correction_contains_existing = (correction['start'] <= existing['start'] and correction['end'] >= existing['end'])
                    existing_contains_correction = (existing['start'] <= correction['start'] and existing['end'] >= correction['end'])
                    
                    if correction_contains_existing:
                        # Current correction completely contains existing one - replace it
                        existing_to_remove.append(existing)
                    elif existing_contains_correction:
                        # Existing correction contains current one - skip current
                        should_add = False
                        break
                    else:
                        # Partial overlap - keep the longer/more specific one
                        if len(correction['original']) > len(existing['original']):
                            existing_to_remove.append(existing)
                        else:
                            should_add = False
                            break
            
            # Remove any existing corrections that should be replaced
            for existing in existing_to_remove:
                filtered_corrections.remove(existing)
            
            if should_add:
                filtered_corrections.append(correction)
        
        # Sort again by position (end to beginning)
        filtered_corrections.sort(key=lambda x: x['start'], reverse=True)
        
        debug_console.log(f"Applying {len(filtered_corrections)} non-overlapping corrections", level='INFO')
        
        # Apply corrections from end to beginning to preserve positions
        corrected_text = original_text
        applied_count = 0
        
        for correction in filtered_corrections:
            start = correction['start']
            end = correction['end']
            
            if correction['suggestion']:
                # Replacement with comment
                replacement = f"% ⟨{correction['anchor']}⟩ Original: \"{correction['original']}\"\n{correction['suggestion']}"
            else:
                # Deletion with comment
                replacement = f"% ⟨{correction['anchor']}⟩ Original: \"{correction['original']}\"\n"
            
            # Apply the correction at exact position
            corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
            correction['error'].is_applied = True
            applied_count += 1
            
            action = "Deleted" if not correction['suggestion'] else "Replaced"
            debug_console.log(f"{action} at pos {start}-{end}: '{correction['original']}' -> '{correction['suggestion']}'", level='DEBUG')
        
        # Verify consistency
        total_applied = sum(1 for error in errors if error.is_applied)
        debug_console.log(f"Applied {applied_count} corrections, marked {total_applied} errors as applied", level='INFO')
        
        return corrected_text
    
    def _generate_corrected_filepath(self) -> str:
        """Generate filepath for corrected file."""
        try:
            current_filepath = llm_state.get_active_filepath()
        except (AttributeError, TypeError):
            current_filepath = None
        
        if current_filepath and os.path.exists(os.path.dirname(current_filepath)):
            # Use current file directory and name
            dir_path = os.path.dirname(current_filepath)
            filename = os.path.basename(current_filepath)
            name, ext = os.path.splitext(filename)
            
            # Create corrected filename
            corrected_filename = f"{name}_corrected{ext}"
            corrected_filepath = os.path.join(dir_path, corrected_filename)
        else:
            # Fallback if no active file or directory doesn't exist
            corrected_filepath = os.path.join(os.getcwd(), "corrected_document.tex")
        
        debug_console.log(f"Generated corrected filepath: {corrected_filepath}", level='INFO')
        return corrected_filepath
    
    def _save_corrected_file(self, corrected_text: str, filepath: str) -> None:
        """Save corrected text to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(corrected_text)
        
        debug_console.log(f"Saved corrected file: {filepath}", level='INFO')
    
    def get_last_results(self) -> Tuple[int, Optional[str]]:
        """Get results from last application."""
        return self.last_applied_count, self.last_file_path


# Global applier instance
_proofreading_applier = ProofreadingApplier()


def apply_all_corrections(errors: List[ProofreadingError], 
                         original_text: str,
                         parent_window=None) -> Tuple[bool, Optional[str]]:
    """
    Apply all approved proofreading corrections and save to corrected file.
    
    Args:
        errors: List of proofreading errors (only approved ones will be applied)
        original_text: Original text content  
        parent_window: Parent window for dialogs
        
    Returns:
        Tuple of (success, corrected_file_path)
    """
    return _proofreading_applier.apply_all_corrections(errors, original_text, parent_window)


def get_last_application_results() -> Tuple[int, Optional[str]]:
    """Get results from last correction application."""
    return _proofreading_applier.get_last_results()