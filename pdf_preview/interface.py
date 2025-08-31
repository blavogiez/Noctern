"""Integrate PDF preview functionality into main application interface."""

import tkinter as tk
import ttkbootstrap as ttk
from pdf_preview.manager import PDFPreviewManager
from pdf_preview.viewer import PDFPreviewViewer
from pdf_preview.sync_manager import PDFSyncManager
from utils import logs_console


class PDFPreviewInterface:
    """Manage PDF preview integration with main application interface."""
    
    def __init__(self, root_window, get_current_tab_func):
        """Initialize PDF preview interface with window and tab references."""
        self.root_window = root_window
        self.get_current_tab = get_current_tab_func
        
        # Setup PDF preview component instances
        self.preview_manager = PDFPreviewManager(root_window, get_current_tab_func)
        self.sync_manager = PDFSyncManager()
        
        # Share the sync manager with the preview manager's viewer
        # This will be set when the viewer is created
        
        # UI elements
        self.preview_pane = None
        self.preview_viewer = None
        self.toggle_button = None
        
        logs_console.log("PDF Preview Interface initialized", level='INFO')
    
    def integrate_into_main_window(self, main_pane):
        """
        Integrate the PDF preview into the main window layout.
        
        Args:
            main_pane (ttk.PanedWindow): The main horizontal paned window
        """
        # This method would be used if we were restructuring the main window
        # For now, we're using the existing pane structure
        pass
    
    def create_preview_panel(self, parent):
        """
        Create the PDF preview panel in a specified parent.
        
        Args:
            parent (tk.Widget): Parent widget for the preview panel
            
        Returns:
            PDFPreviewViewer: The preview viewer instance
        """
        self.preview_viewer = self.preview_manager.create_preview_panel(parent)
        return self.preview_viewer
    
    def toggle_preview_visibility(self):
        """
        Toggle the visibility of the PDF preview panel.
        """
        # This would implement showing/hiding the preview panel
        # Implementation depends on the exact UI structure
        pass
    
    def on_editor_content_change(self):
        """
        Called when the editor content changes.
        Triggers PDF compilation and preview update.
        """
        self.preview_manager.on_editor_change()
    
    def on_editor_navigation(self, line_number):
        """
        Called when the editor cursor position changes.
        Synchronizes the PDF view with the current editor position.
        
        Args:
            line_number (int): Current line number in the editor
        """
        pdf_position = self.sync_manager.on_editor_navigation(line_number)
        if pdf_position and self.preview_manager.get_viewer():
            # In a full implementation, this would scroll to the specific position
            self.preview_manager.synchronize_with_editor(line_number)
    
    def on_pdf_navigation(self, pdf_page):
        """
        Called when the PDF view position changes.
        Synchronizes the editor with the current PDF position.
        
        Args:
            pdf_page (int): Current page number in the PDF
        """
        editor_line = self.sync_manager.on_pdf_navigation(pdf_page)
        if editor_line:
            # In a full implementation, this would navigate the editor to the line
            current_tab = self.get_current_tab()
            if current_tab and current_tab.editor:
                try:
                    current_tab.editor.see(f"{editor_line}.0")
                    current_tab.editor.mark_set("insert", f"{editor_line}.0")
                except tk.TclError:
                    pass  # Ignore errors if line doesn't exist
    
    def refresh_preview(self):
        """
        Force refresh the PDF preview.
        """
        self.preview_manager.refresh_preview()
    
    def get_preview_manager(self):
        """
        Get the preview manager instance.
        
        Returns:
            PDFPreviewManager: The preview manager
        """
        return self.preview_manager
    
    def get_sync_manager(self):
        """
        Get the synchronization manager instance.
        
        Returns:
            PDFSyncManager: The synchronization manager
        """
        return self.sync_manager
    
    def load_existing_pdf_for_tab(self, tab):
        """
        Load existing PDF for a tab if it exists.
        
        Args:
            tab: The editor tab
        """
        if tab and tab.file_path and self.preview_manager:
            self.preview_manager.load_existing_pdf(tab.file_path)
    
    def set_auto_refresh(self, enabled):
        """
        Enable or disable automatic PDF refresh.
        
        Args:
            enabled (bool): Whether to enable auto-refresh
        """
        if self.preview_manager:
            self.preview_manager.set_auto_refresh(enabled)
            
    def navigate_to_exact_line(self, line_number: int, source_text: str = "", 
                              context_before: str = "", context_after: str = "", 
                              source_content: str = "") -> bool:
        """
        Navigate to exact line number in PDF with precision.
        
        Args:
            line_number (int): Line number in LaTeX source
            source_text (str): Text on the line for disambiguation
            context_before (str): Context before the line
            context_after (str): Context after the line
            source_content (str): Full LaTeX source content
            
        Returns:
            bool: True if navigation successful
        """
        if self.preview_manager:
            return self.preview_manager.navigate_to_exact_line(
                line_number, source_text, context_before, context_after, source_content
            )
        return False

    def go_to_text_in_pdf(self, text, context_before="", context_after=""):
        """
        Navigate to the specified text in the PDF using the preview manager.
        
        Args:
            text (str): Text to search for in the PDF
            context_before (str): Text before the target text
            context_after (str): Text after the target text
        """
        if self.preview_manager:
            self.preview_manager.go_to_text_in_pdf(text, context_before, context_after)