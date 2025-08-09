"""
PDF Preview Manager Component
Manages the PDF preview functionality, including compilation triggering and synchronization.
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
    and synchronization between the editor and PDF viewer.
    """
    
    def __init__(self, root_window, get_current_tab_func):
        """
        Initialize the PDF preview manager.
        
        Args:
            root_window (tk.Tk): The main application window
            get_current_tab_func (callable): Function to get the current editor tab
        """
        self.root_window = root_window
        self.get_current_tab = get_current_tab_func
        self.viewer = None
        self.is_compiling = False
        self.last_compilation_time = 0
        self.compilation_delay = 1.0  # 1 second delay before compiling
        self.compilation_timer = None
        self.auto_refresh_enabled = True
        
        debug_console.log("PDF Preview Manager initialized", level='INFO')
    
    def create_preview_panel(self, parent):
        """
        Create the PDF preview panel.
        
        Args:
            parent (tk.Widget): Parent widget to place the panel in
            
        Returns:
            PDFPreviewViewer: The created viewer instance
        """
        self.viewer = PDFPreviewViewer(parent)
        return self.viewer
    
    def trigger_compilation(self):
        """
        Trigger PDF compilation after a delay to avoid continuous compilation
        during rapid editing.
        """
        # Only trigger if auto-refresh is enabled
        if not self.auto_refresh_enabled:
            return
            
        # Cancel any existing timer
        if self.compilation_timer:
            self.root_window.after_cancel(self.compilation_timer)
        
        # Set a new timer
        self.compilation_timer = self.root_window.after(
            int(self.compilation_delay * 1000), 
            self._compile_document
        )
    
    def _compile_document(self):
        """
        Compile the current document to PDF.
        This method should be called internally, not directly.
        """
        if self.is_compiling:
            return
            
        self.is_compiling = True
        current_tab = self.get_current_tab()
        
        if not current_tab:
            self.is_compiling = False
            return
            
        try:
            # Save current content to file
            editor_content = current_tab.editor.get("1.0", "end-1c")
            
            if current_tab.file_path:
                source_directory = os.path.dirname(current_tab.file_path)
                file_name = os.path.basename(current_tab.file_path)
                tex_file_path = current_tab.file_path
                
                # Save content to file
                with open(tex_file_path, "w", encoding="utf-8") as f:
                    f.write(editor_content)
                    
                debug_console.log(f"Saved content for compilation: {tex_file_path}", level='DEBUG')
            else:
                # For unsaved files, use temporary location
                source_directory = "output"
                file_name = "preview.tex"
                os.makedirs(source_directory, exist_ok=True)
                tex_file_path = os.path.join(source_directory, file_name)
                
                # Save content to temporary file
                with open(tex_file_path, "w", encoding="utf-8") as f:
                    f.write(editor_content)
                    
                debug_console.log(f"Saved temporary content for compilation: {tex_file_path}", level='DEBUG')
            
            # Compile in a separate thread to avoid blocking UI
            compilation_thread = threading.Thread(
                target=self._run_compilation,
                args=(source_directory, file_name, tex_file_path),
                daemon=True
            )
            compilation_thread.start()
            
        except Exception as e:
            debug_console.log(f"Error preparing compilation: {e}", level='ERROR')
            self.is_compiling = False
    
    def _run_compilation(self, source_directory, file_name, tex_file_path):
        """
        Run the actual PDF compilation process.
        
        Args:
            source_directory (str): Directory containing the .tex file
            file_name (str): Name of the .tex file
            tex_file_path (str): Full path to the .tex file
        """
        try:
            # Execute pdflatex command
            command = ["pdflatex", "-interaction=nonstopmode", file_name]
            debug_console.log(f"Compiling PDF: {' '.join(command)} in {source_directory}", level='DEBUG')
            
            result = subprocess.run(
                command, 
                cwd=source_directory, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                timeout=60, 
                check=False
            )
            
            # Update UI in main thread
            self.root_window.after(0, self._compilation_finished, result.returncode == 0, source_directory, file_name)
            
        except subprocess.TimeoutExpired:
            debug_console.log("PDF compilation timed out", level='ERROR')
            self.root_window.after(0, self._compilation_finished, False, source_directory, file_name)
        except Exception as e:
            debug_console.log(f"Error during PDF compilation: {e}", level='ERROR')
            self.root_window.after(0, self._compilation_finished, False, source_directory, file_name)
    
    def _compilation_finished(self, success, source_directory, file_name):
        """
        Handle completion of the compilation process.
        
        Args:
            success (bool): Whether compilation was successful
            source_directory (str): Directory containing the .tex file
            file_name (str): Name of the .tex file
        """
        self.is_compiling = False
        self.last_compilation_time = time.time()
        
        if success:
            debug_console.log("PDF compilation successful", level='SUCCESS')
            pdf_path = os.path.join(source_directory, file_name.replace(".tex", ".pdf"))
            
            if self.viewer and os.path.exists(pdf_path):
                self.viewer.load_pdf(pdf_path)
        else:
            debug_console.log("PDF compilation failed", level='ERROR')
            # In a full implementation, we might show compilation errors
    
    def synchronize_with_editor(self, line_number):
        """
        Synchronize the PDF view with the current editor position.
        
        Args:
            line_number (int): Current line number in the editor
        """
        if self.viewer:
            self.viewer.synchronize_with_editor(line_number)
    
    def on_editor_change(self):
        """
        Called when the editor content changes.
        Triggers compilation after a delay.
        """
        self.trigger_compilation()
    
    def refresh_preview(self):
        """
        Force refresh the PDF preview.
        """
        self.trigger_compilation()
    
    def load_existing_pdf(self, file_path):
        """
        Load an existing PDF file if it exists for the given .tex file.
        
        Args:
            file_path (str): Path to the .tex file
        """
        if not file_path or not file_path.endswith('.tex'):
            return
            
        # Derive PDF path from .tex file path
        pdf_path = file_path.replace('.tex', '.pdf')
        
        # Check if PDF exists
        if os.path.exists(pdf_path) and self.viewer:
            debug_console.log(f"Loading existing PDF: {pdf_path}", level='INFO')
            self.viewer.load_pdf(pdf_path)
    
    def set_auto_refresh(self, enabled):
        """
        Enable or disable automatic PDF refresh.
        
        Args:
            enabled (bool): Whether to enable auto-refresh
        """
        self.auto_refresh_enabled = enabled
        debug_console.log(f"Auto-refresh {'enabled' if enabled else 'disabled'}", level='INFO')
    
    def get_viewer(self):
        """
        Get the PDF viewer instance.
        
        Returns:
            PDFPreviewViewer: The viewer instance
        """
        return self.viewer