"""Apply proofreading corrections to text."""
import os
from typing import List, Tuple, Optional
from tkinter import messagebox

from llm import state


class ProofreadingApplier:
    """Handles application of approved proofreading corrections."""
    def __init__(self):
        """Initialize applier."""
        self.last_applied_count = 0
        self.last_file_path = None
    
    def apply_all_corrections(self, errors, original_text, parent_window=None):
        """Apply all approved corrections and save to file."""
        approved_errors = [error for error in errors if error.is_approved]
        
        if not approved_errors:
            if parent_window:
                messagebox.showwarning("No Approved Corrections", "No corrections have been approved for application.", parent=parent_window)
            return False, None
        
        try:
            corrected_text = self.apply_corrections_to_text(original_text, approved_errors)
            corrected_filepath = self.generate_corrected_filepath()
            
            self.save_corrected_file(corrected_text, corrected_filepath)
            
            for error in approved_errors:
                error.is_applied = True
            
            self.last_applied_count = len(approved_errors)
            self.last_file_path = corrected_filepath
            
            if parent_window:
                messagebox.showinfo(
                    "Corrections Applied", 
                    f"Applied {len(approved_errors)} approved corrections and saved to:\n{corrected_filepath}",
                    parent=parent_window
                )
            
            return True, corrected_filepath
        except Exception as e:
            error_msg = f"Failed to apply corrections: {str(e)}"
            if parent_window:
                messagebox.showerror("Application Error", error_msg, parent=parent_window)
            return False, None
    
    def apply_corrections_to_text(self, original_text, errors):
        """Apply corrections to text content."""
        corrections = []
        used_positions = set()
        
        for i, error in enumerate(errors, 1):
            start_pos = original_text.find(error.original)
            if start_pos != -1:
                position_key = (start_pos, start_pos + len(error.original))
                if position_key not in used_positions:
                    corrections.append({
                        'start': start_pos,
                        'end': start_pos + len(error.original),
                        'original': error.original,
                        'suggestion': error.suggestion,
                        'anchor': i,
                        'error': error
                    })
                    used_positions.add(position_key)
        
        corrections.sort(key=lambda x: x['start'], reverse=True)
        
        filtered_corrections = []
        for correction in corrections:
            should_add = True
            existing_to_remove = []
            
            for existing in filtered_corrections:
                if (correction['start'] < existing['end'] and correction['end'] > existing['start']):
                    correction_contains_existing = (correction['start'] <= existing['start'] and correction['end'] >= existing['end'])
                    existing_contains_correction = (existing['start'] <= correction['start'] and existing['end'] >= correction['end'])
                    
                    if correction_contains_existing:
                        existing_to_remove.append(existing)
                    elif existing_contains_correction:
                        should_add = False
                        break
                    else:
                        if len(correction['original']) > len(existing['original']):
                            existing_to_remove.append(existing)
                        else:
                            should_add = False
                            break
            
            for existing in existing_to_remove:
                filtered_corrections.remove(existing)
            
            if should_add:
                filtered_corrections.append(correction)
        
        filtered_corrections.sort(key=lambda x: x['start'], reverse=True)
        
        corrected_text = original_text
        for correction in filtered_corrections:
            start = correction['start']
            end = correction['end']
            
            if correction['suggestion']:
                replacement = f"% <{correction['anchor']}> Original: \"{correction['original']}\"\n{correction['suggestion']}"
            else:
                replacement = ""
            
            corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
            correction['error'].is_applied = True
        
        return corrected_text
    
    def generate_corrected_filepath(self):
        """Generate filepath for corrected file."""
        try:
            current_filepath = state.get_active_filepath()
        except:
            current_filepath = None
        
        if current_filepath and os.path.exists(os.path.dirname(current_filepath)):
            dir_path = os.path.dirname(current_filepath)
            filename = os.path.basename(current_filepath)
            name, ext = os.path.splitext(filename)
            
            corrected_filename = f"{name}_corrected{ext}"
            corrected_filepath = os.path.join(dir_path, corrected_filename)
        else:
            corrected_filepath = os.path.join(os.getcwd(), "corrected_document.tex")
        
        return corrected_filepath
    
    def save_corrected_file(self, corrected_text, filepath):
        """Save corrected text to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(corrected_text)
    
    def get_last_results(self):
        """Get results from last application."""
        return self.last_applied_count, self.last_file_path


proofreading_applier = ProofreadingApplier()


def apply_all_corrections(errors, original_text, parent_window=None):
    """Apply all approved corrections and save to file."""
    return proofreading_applier.apply_all_corrections(errors, original_text, parent_window)


def get_last_application_results():
    """Get results from last correction application."""
    return proofreading_applier.get_last_results()