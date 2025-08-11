"""
PDF Preview Manager Component
Manages the PDF preview functionality, including compilation triggering and status updates.
"""

import os
import threading
import time
import subprocess
from utils import debug_console
from pdf_preview.viewer import PDFPreviewViewer


class PDFPreviewManager:
    """
    Manages the PDF preview functionality, including automatic compilation
    and status updates.
    """
    
    def __init__(self, root_window, get_current_tab_func, header_label=None):
        """
        Initialize the PDF preview manager.
        
        Args:
            root_window (tk.Tk): The main application window
            get_current_tab_func (callable): Function to get the current editor tab
            header_label (ttk.Label, optional): The label for status updates.
        """
        self.root_window = root_window
        self.get_current_tab = get_current_tab_func
        self.header_label = header_label
        self.viewer = None
        self.is_compiling = False
        
        # Compilation and status tracking
        self.last_compilation_time = None
        self.compilation_status = "Not yet compiled"
        self.compilation_delay = 1.0
        self.compilation_timer = None
        self.status_update_job = None
        self.auto_refresh_enabled = True
        
        debug_console.log("PDF Preview Manager initialized", level='INFO')
        self._update_status_label()

    def get_viewer(self):
        """Get the current PDF viewer instance."""
        return self.viewer
        
    def create_preview_panel(self, parent):
        """Create a new PDF preview panel."""
        # Always create a fresh viewer with the correct initial zoom
        self.viewer = PDFPreviewViewer(parent)
        return self.viewer

    def trigger_compilation(self):
        if not self.auto_refresh_enabled: return
        if self.compilation_timer: self.root_window.after_cancel(self.compilation_timer)
        self.compilation_timer = self.root_window.after(int(self.compilation_delay * 1000), self._compile_document)
    
    def _compile_document(self):
        if self.is_compiling: return
        current_tab = self.get_current_tab()
        if not current_tab: return
            
        self.is_compiling = True
        self.compilation_status = "Compiling..."
        self._update_status_label()
        
        try:
            editor_content = current_tab.editor.get("1.0", "end-1c")
            file_path = current_tab.file_path
            
            if file_path:
                source_dir = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                with open(file_path, "w", encoding="utf-8") as f: f.write(editor_content)
            else: # Unsaved file
                source_dir, file_name = "output", "preview.tex"
                os.makedirs(source_dir, exist_ok=True)
                with open(os.path.join(source_dir, file_name), "w", encoding="utf-8") as f: f.write(editor_content)

            comp_thread = threading.Thread(target=self._run_compilation, args=(source_dir, file_name), daemon=True)
            comp_thread.start()
            
        except Exception as e:
            debug_console.log(f"Error preparing compilation: {e}", level='ERROR')
            self.is_compiling = False

    def _run_compilation(self, source_directory, file_name):
        try:
            command = ["pdflatex", "-interaction=nonstopmode", file_name]
            result = subprocess.run(command, cwd=source_directory, capture_output=True, timeout=60, check=False)
            self.root_window.after(0, self._compilation_finished, result.returncode == 0, source_directory, file_name)
        except Exception as e:
            debug_console.log(f"Error during PDF compilation: {e}", level='ERROR')
            self.root_window.after(0, self._compilation_finished, False, source_directory, file_name)
    
    def _compilation_finished(self, success, source_directory, file_name):
        self.is_compiling = False
        if success:
            self.last_compilation_time = time.time()
            self.compilation_status = "Compilable"
            pdf_path = os.path.join(source_directory, file_name.replace(".tex", ".pdf"))
            if self.viewer and os.path.exists(pdf_path):
                self.viewer.load_pdf(pdf_path)
                # Update viewer status
                self.viewer.set_compilation_status("Compilable", self.last_compilation_time)
            self._start_status_updates()
        else:
            # En cas d'échec de compilation, on garde l'ancien PDF affiché
            self.compilation_status = "Not compilable"
            if self.viewer:
                self.viewer.set_compilation_status("Not compilable", self.last_compilation_time)
            self._stop_status_updates()
        
        self._update_status_label()

    def _start_status_updates(self):
        if self.status_update_job: self.root_window.after_cancel(self.status_update_job)
        self._update_status_label()

    def _stop_status_updates(self):
        if self.status_update_job: self.root_window.after_cancel(self.status_update_job)
        self.status_update_job = None

    def _update_status_label(self):
        if not self.header_label: return
        
        status_text = f"Current state: {self.compilation_status}"
        time_ago = ""
        
        if self.last_compilation_time:
            seconds = int(time.time() - self.last_compilation_time)
            if seconds < 60:
                time_ago = "Last PDF output less than a minute ago"
            else:
                minutes = seconds // 60
                if minutes == 1:
                    time_ago = "Last PDF output about a minute ago"
                else:
                    time_ago = f"Last PDF output {minutes} minutes ago"
        
        full_text = f"{time_ago}\n{status_text}" if time_ago else status_text
        self.header_label.config(text=full_text)

        if self.compilation_status == "Compilable":
            self.status_update_job = self.root_window.after(1000, self._update_status_label)

    def on_editor_change(self):
        self.trigger_compilation()
    
    def refresh_preview(self):
        self.trigger_compilation()
    
    def load_existing_pdf(self, file_path):
        if not file_path or not file_path.endswith('.tex'): return
        pdf_path = file_path.replace('.tex', '.pdf')
        if os.path.exists(pdf_path) and self.viewer:
            self.viewer.load_pdf(pdf_path)
            self.last_compilation_time = os.path.getmtime(pdf_path)
            self.compilation_status = "Compilable"
            self.viewer.set_compilation_status("Compilable", self.last_compilation_time)
            self._start_status_updates()

    def set_auto_refresh(self, enabled):
        self.auto_refresh_enabled = enabled
        
    def go_to_text_in_pdf(self, text, context_before="", context_after=""):
        """
        Navigate to the specified text in the PDF using the viewer's text navigator.
        
        Args:
            text (str): Text to search for in the PDF
            context_before (str): Text before the target text
            context_after (str): Text after the target text
        """
        if self.viewer:
            self.viewer.go_to_text(text, context_before, context_after)