"""
PDF Preview Manager Component.
Manage PDF preview functionality including compilation triggering and status updates.
"""

import os
import threading
import time
import subprocess
import shutil
import tempfile
import platform
from utils import logs_console
from pdf_preview.viewer import PDFPreviewViewer


class PDFPreviewManager:
    """
    Manage PDF preview functionality including automatic compilation and status updates.
    """
    
    def __init__(self, root_window, get_current_tab_func, header_label=None):
        """
        Initialize PDF preview manager.
        """
        self.root_window = root_window
        self.get_current_tab = get_current_tab_func
        self.header_label = header_label
        self.viewer = None
        self.is_compiling = False
        
        # Initialize compilation and status tracking
        self.last_compilation_time = None
        self.compilation_status = "Not yet compiled"
        self.compilation_delay = 1.0
        self.compilation_timer = None
        self.status_update_job = None
        self.auto_refresh_enabled = True
        
        logs_console.log("PDF Preview Manager initialized", level='INFO')
        self._update_status_label()

    def get_viewer(self):
        """Get current PDF viewer instance."""
        return self.viewer
        
    def create_preview_panel(self, parent):
        """Create a new PDF preview panel."""
        # Always create a fresh viewer with the correct initial zoom
        self.viewer = PDFPreviewViewer(parent)
        # Set the shared sync manager if available
        if hasattr(self, 'sync_manager') and self.sync_manager:
            self.viewer.sync_manager = self.sync_manager
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
            figures_path = self._get_figures_path(current_tab.file_path) if current_tab.file_path else None
            
            comp_thread = threading.Thread(target=self._compile_from_memory, args=(editor_content, figures_path), daemon=True)
            comp_thread.start()
            
        except Exception as e:
            logs_console.log(f"Error preparing compilation: {e}", level='ERROR')
            self.is_compiling = False

    def _get_figures_path(self, file_path):
        """Get figures directory path if it exists"""
        if not file_path:
            return None
        base_dir = os.path.dirname(file_path)
        figures_dir = os.path.join(base_dir, "figures")
        return figures_dir if os.path.exists(figures_dir) else None

    def _compile_from_memory(self, latex_content, figures_path):
        """Compile LaTeX content in temporary memory location"""
        try:
            temp_base = self._get_temp_base()
            
            with tempfile.TemporaryDirectory(dir=temp_base, prefix='automatex_') as temp_dir:
                self._setup_compilation_files(temp_dir, latex_content, figures_path)
                result = self._execute_latex_compilation(temp_dir)
                self._process_compilation_result(temp_dir, result, latex_content)
                    
        except Exception as e:
            logs_console.log(f"Memory compilation error: {e}", level='ERROR')
            self.root_window.after(0, self._on_compilation_failure, "", latex_content)

    def _get_temp_base(self):
        """Get optimal temporary directory for compilation"""
        if platform.system() in ['Linux', 'Darwin'] and os.path.exists('/dev/shm'):
            return '/dev/shm'
        return tempfile.gettempdir()

    def _setup_compilation_files(self, temp_dir, latex_content, figures_path):
        """Setup files required for compilation"""
        if figures_path:
            self._copy_figures_to_temp(figures_path, temp_dir)
        
        tex_file = os.path.join(temp_dir, "preview.tex")
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)

    def _execute_latex_compilation(self, temp_dir):
        """Execute pdflatex compilation in temporary directory"""
        return subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "preview.tex"], 
            cwd=temp_dir,
            capture_output=True, 
            timeout=60, 
            check=False
        )

    def _process_compilation_result(self, temp_dir, result, latex_content):
        """Process compilation result and handle success or failure"""
        log_content = self._read_log_file(temp_dir)
        pdf_path = os.path.join(temp_dir, "preview.pdf")
        success = result.returncode == 0 and os.path.exists(pdf_path)
        
        if success:
            persistent_pdf = self._save_preview_pdf(pdf_path)
            self.root_window.after(0, self._on_compilation_success, persistent_pdf, log_content, latex_content)
        else:
            self.root_window.after(0, self._on_compilation_failure, log_content, latex_content)

    def _read_log_file(self, temp_dir):
        """Read compilation log file"""
        log_path = os.path.join(temp_dir, "preview.log")
        if not os.path.exists(log_path):
            return ""
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logs_console.log(f"Log read error: {e}", level='WARNING')
            return ""

    def _copy_figures_to_temp(self, figures_path, temp_dir):
        """Copy figures directory to temporary location"""
        try:
            temp_figures = os.path.join(temp_dir, "figures")
            shutil.copytree(figures_path, temp_figures)
        except Exception as e:
            logs_console.log(f"Figure copy error: {e}", level='ERROR')

    def _save_preview_pdf(self, pdf_path):
        """Save preview PDF to persistent location and return path"""
        persistent_dir = os.path.join(tempfile.gettempdir(), "automatex_preview")
        os.makedirs(persistent_dir, exist_ok=True)
        persistent_pdf = os.path.join(persistent_dir, "preview.pdf")
        shutil.copy2(pdf_path, persistent_pdf)
        return persistent_pdf

    def _on_compilation_success(self, pdf_path, log_content="", latex_content=""):
        """Handle successful compilation"""
        self.is_compiling = False
        self.last_compilation_time = time.time()
        self.compilation_status = "Compilable"
        
        if self.viewer:
            self.viewer.load_pdf(pdf_path)
            self.viewer.set_compilation_status("Compilable", self.last_compilation_time)
        self._start_status_updates()
        
        self._save_successful_version(latex_content)
        self._notify_debug_system(True, log_content, latex_content)
        logs_console.log("PDF preview updated from memory", level='INFO')

    def _on_compilation_failure(self, log_content="", latex_content=""):
        """Handle compilation failure"""
        self.is_compiling = False
        self.compilation_status = "Not compilable"
        if self.viewer:
            self.viewer.set_compilation_status("Not compilable", self.last_compilation_time)
        self._stop_status_updates()
        
        self._notify_debug_system(False, log_content, latex_content)
        logs_console.log("PDF compilation from memory failed", level='WARNING')

    def _save_successful_version(self, latex_content):
        """Cache successful compilation for diff system"""
        try:
            current_tab = self.get_current_tab()
            if not current_tab or not current_tab.file_path:
                return
                
            source_directory = os.path.dirname(current_tab.file_path)
            file_name = os.path.basename(current_tab.file_path)
            tex_base_name = os.path.splitext(file_name)[0]
            cache_directory = os.path.join(source_directory, f"{tex_base_name}.cache")
            os.makedirs(cache_directory, exist_ok=True)
            
            cached_tex_path = os.path.join(cache_directory, f"{tex_base_name}_last_successful.tex")
            with open(cached_tex_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
        except Exception as e:
            logs_console.log(f"Cache save error: {e}", level='WARNING')

    def _notify_debug_system(self, success, log_content, latex_content):
        """Send compilation result to debug system"""
        try:
            from app import state
            current_tab = self.get_current_tab()
            if hasattr(state, 'debug_coordinator') and state.debug_coordinator and current_tab:
                file_path = current_tab.file_path or "preview.tex"
                state.debug_coordinator.handle_compilation_result(
                    success=success,
                    log_content=log_content,
                    file_path=file_path,
                    current_content=latex_content
                )
        except Exception as e:
            logs_console.log(f"Debug system notification error: {e}", level='WARNING')
    
    def _compilation_finished(self, success, source_directory, file_name):
        self.is_compiling = False
        if success:
            self.last_compilation_time = time.time()
            self.compilation_status = "Compilable"
            pdf_path = os.path.join(source_directory, file_name.replace(".tex", ".pdf"))
            
            # Cache successful compilation using existing cache directory in same directory as tex file
            try:
                tex_base_name = os.path.splitext(file_name)[0]
                cache_directory = os.path.join(source_directory, f"{tex_base_name}.cache")
                os.makedirs(cache_directory, exist_ok=True)
                cached_tex_path = os.path.join(cache_directory, f"{tex_base_name}_last_successful.tex")
                tex_file_path = os.path.join(source_directory, file_name)
                shutil.copy2(tex_file_path, cached_tex_path)
                logs_console.log(f"Auto-compilation: Cached successful version to {cached_tex_path}", level='INFO')
            except Exception as e:
                logs_console.log(f"Auto-compilation: Failed to cache successful .tex file: {e}", level='ERROR')
            
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
            
            # Send compilation errors to the debug system
            self._handle_compilation_failure(source_directory, file_name)
        
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

    def _handle_compilation_failure(self, source_directory, file_name):
        """
        Handle compilation failure by sending errors to the debug system.
        
        Args:
            source_directory: Directory where compilation was attempted
            file_name: Name of the .tex file that failed to compile
        """
        try:
            # Get current tab info
            current_tab = self.get_current_tab()
            if not current_tab:
                logs_console.log("No current tab for error handling", level='WARNING')
                return
            
            # Read log file
            log_file_path = os.path.join(source_directory, file_name.replace(".tex", ".log"))
            log_content = ""
            
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    logs_console.log(f"Auto-compilation: Read log file {log_file_path} ({len(log_content)} chars)", level='DEBUG')
                except Exception as e:
                    logs_console.log(f"Auto-compilation: Error reading log file: {e}", level='ERROR')
                    return
            else:
                logs_console.log(f"Auto-compilation: Log file not found: {log_file_path}", level='WARNING')
                return
            
            # Get current file content
            current_content = current_tab.editor.get("1.0", "end-1c")
            file_path = current_tab.file_path or os.path.join(source_directory, file_name)
            
            # Send to debug system
            try:
                from app import state
                if hasattr(state, 'debug_coordinator') and state.debug_coordinator:
                    logs_console.log("Auto-compilation: Sending errors to debug system", level='INFO')
                    state.debug_coordinator.handle_compilation_result(
                        success=False,
                        log_content=log_content,
                        file_path=file_path,
                        current_content=current_content
                    )
                else:
                    logs_console.log("Auto-compilation: Debug coordinator not available", level='WARNING')
            except Exception as e:
                logs_console.log(f"Auto-compilation: Error sending to debug system: {e}", level='ERROR')
                
        except Exception as e:
            logs_console.log(f"Auto-compilation: Error in _handle_compilation_failure: {e}", level='ERROR')

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