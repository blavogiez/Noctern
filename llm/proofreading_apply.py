"""Apply proofreading corrections to text."""
import os
from typing import List, Tuple, Optional
from tkinter import messagebox

from llm import state
from utils import logs_console


def apply_all_corrections(errors, original_text: str, parent_window=None) -> Tuple[bool, Optional[str]]:
    """Apply all approved corrections and save to file."""
    approved_errors = [error for error in errors if error.is_approved]
    
    if not approved_errors:
        if parent_window:
            messagebox.showwarning("No Corrections", "No corrections have been approved.", parent=parent_window)
        return False, None
    
    logs_console.log(f"Applying {len(approved_errors)} approved corrections", level='INFO')
    
    try:
        # Apply corrections to text
        corrected_text = apply_corrections_to_text(original_text, approved_errors)
        
        # Generate output file path
        corrected_filepath = generate_output_filepath()
        
        # Save corrected file
        save_corrected_file(corrected_text, corrected_filepath)
        
        # Mark corrections as applied
        for error in approved_errors:
            error.is_applied = True
        
        logs_console.log(f"Successfully applied corrections to {corrected_filepath}", level='INFO')
        
        if parent_window:
            messagebox.showinfo(
                "Success", 
                f"Applied {len(approved_errors)} corrections and saved to:\n{corrected_filepath}",
                parent=parent_window
            )
        
        return True, corrected_filepath
        
    except Exception as e:
        logs_console.log(f"Failed to apply corrections: {e}", level='ERROR')
        error_msg = f"Failed to apply corrections: {str(e)}"
        if parent_window:
            messagebox.showerror("Error", error_msg, parent=parent_window)
        return False, None


def apply_corrections_to_text(original_text: str, errors: List) -> str:
    """Apply corrections to text content."""
    logs_console.log(f"Processing {len(errors)} corrections", level='INFO')
    
    # Find all correction positions
    corrections = []
    used_positions = set()
    
    for i, error in enumerate(errors, 1):
        start_pos = original_text.find(error.original)
        if start_pos != -1:
            end_pos = start_pos + len(error.original)
            position_key = (start_pos, end_pos)
            
            if position_key not in used_positions:
                corrections.append({
                    'start': start_pos,
                    'end': end_pos,
                    'original': error.original,
                    'suggestion': error.suggestion,
                    'anchor': i,
                    'error': error
                })
                used_positions.add(position_key)
    
    logs_console.log(f"Found {len(corrections)} unique correction positions", level='INFO')
    
    # Sort corrections by position (reverse order for safe replacement)
    corrections.sort(key=lambda x: x['start'], reverse=True)
    
    # Remove overlapping corrections (keep longer ones)
    filtered_corrections = remove_overlapping_corrections(corrections)
    logs_console.log(f"After overlap filtering: {len(filtered_corrections)} corrections", level='INFO')
    
    # Apply corrections to text
    corrected_text = original_text
    for correction in filtered_corrections:
        start = correction['start']
        end = correction['end']
        
        # Build replacement text with comment annotation
        if correction['suggestion']:
            replacement = f"% <{correction['anchor']}> Original: \"{correction['original']}\"\n{correction['suggestion']}"
        else:
            replacement = ""  # Deletion
        
        corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
        correction['error'].is_applied = True
    
    return corrected_text


def remove_overlapping_corrections(corrections: List[dict]) -> List[dict]:
    """Remove overlapping corrections, keeping longer ones."""
    filtered_corrections = []
    
    for correction in corrections:
        should_add = True
        existing_to_remove = []
        
        for existing in filtered_corrections:
            # Check for overlap
            if (correction['start'] < existing['end'] and correction['end'] > existing['start']):
                correction_length = len(correction['original'])
                existing_length = len(existing['original'])
                
                if correction_length > existing_length:
                    # Current correction is longer, remove existing
                    existing_to_remove.append(existing)
                else:
                    # Existing correction is longer or equal, skip current
                    should_add = False
                    break
        
        # Remove shorter corrections
        for existing in existing_to_remove:
            filtered_corrections.remove(existing)
        
        if should_add:
            filtered_corrections.append(correction)
    
    return filtered_corrections


def generate_output_filepath() -> str:
    """Generate a non-conflicting filepath for corrected file.

    - Saves next to the active file if available, else in CWD.
    - Appends `_corrected` suffix; if already present or exists, adds numeric suffix.
    """
    try:
        current_filepath = state.get_active_filepath()
    except Exception:
        current_filepath = None

    if current_filepath and os.path.exists(os.path.dirname(current_filepath)):
        dir_path = os.path.dirname(current_filepath)
        filename = os.path.basename(current_filepath)
        name, ext = os.path.splitext(filename)
        base = name
        # Avoid double `_corrected` suffix
        if base.lower().endswith("_corrected"):
            base = base
        else:
            base = f"{base}_corrected"

        candidate = os.path.join(dir_path, f"{base}{ext}")
        if not os.path.exists(candidate):
            return candidate
        # If exists, add numeric suffix
        idx = 1
        while True:
            candidate = os.path.join(dir_path, f"{base}_{idx}{ext}")
            if not os.path.exists(candidate):
                return candidate
            idx += 1
    else:
        # Fall back to current directory (LaTeX default extension)
        dir_path = os.getcwd()
        base = "corrected_document"
        ext = ".tex"
        candidate = os.path.join(dir_path, f"{base}{ext}")
        if not os.path.exists(candidate):
            return candidate
        idx = 1
        while True:
            candidate = os.path.join(dir_path, f"{base}_{idx}{ext}")
            if not os.path.exists(candidate):
                return candidate
            idx += 1


def save_corrected_file(corrected_text: str, filepath: str):
    """Save corrected text to file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(corrected_text)
    logs_console.log(f"Saved corrected text to {filepath}", level='INFO')


# Legacy compatibility - global applier instance
class ProofreadingApplier:
    """Legacy compatibility wrapper."""
    def __init__(self):
        self.last_applied_count = 0
        self.last_file_path = None
    
    def apply_all_corrections(self, errors, original_text, parent_window=None):
        """Apply corrections using new function."""
        success, filepath = apply_all_corrections(errors, original_text, parent_window)
        if success:
            self.last_applied_count = sum(1 for error in errors if error.is_approved)
            self.last_file_path = filepath
        return success, filepath
    
    def apply_corrections_to_text(self, original_text, errors):
        """Apply corrections using new function."""
        return apply_corrections_to_text(original_text, errors)
    
    def get_last_results(self):
        """Get results from last application."""
        return self.last_applied_count, self.last_file_path


# Global instance for compatibility
proofreading_applier = ProofreadingApplier()


def get_last_application_results():
    """Get results from last correction application."""
    return proofreading_applier.get_last_results()
