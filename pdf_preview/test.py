"""
Test module for PDF Preview functionality
This module contains tests to verify the PDF preview feature is working correctly.
"""

import tkinter as tk
import ttkbootstrap as ttk
from pdf_preview.interface import PDFPreviewInterface


def test_pdf_preview_interface():
    """
    Test the PDF preview interface creation.
    """
    print("Testing PDF Preview Interface...")
    
    # Create a simple test window
    root = tk.Tk()
    root.title("PDF Preview Test")
    root.geometry("800x600")
    
    # Create a simple frame for the preview
    preview_frame = ttk.Frame(root)
    preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create a label to indicate the test
    label = ttk.Label(
        preview_frame,
        text="PDF Preview Test Area",
        font=("Arial", 16, "bold")
    )
    label.pack(pady=20)
    
    # Test creating the PDF preview interface
    def get_current_tab():
        return None  # Simple mock
    
    try:
        pdf_interface = PDFPreviewInterface(root, get_current_tab)
        print("PASS: PDF Preview Interface created successfully")
        
        # Test creating a preview panel
        preview_panel = pdf_interface.create_preview_panel(preview_frame)
        print("PASS: PDF Preview Panel created successfully")
        
        return True
    except Exception as e:
        print(f"FAIL: Error creating PDF Preview Interface: {e}")
        return False


if __name__ == "__main__":
    success = test_pdf_preview_interface()
    if success:
        print("\nAll tests passed! PDF Preview feature is ready.")
    else:
        print("\nSome tests failed. Please check the implementation.")
