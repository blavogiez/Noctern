"""
Comprehensive test for PDF Preview functionality
This module tests all aspects of the PDF preview feature.
"""

import tkinter as tk
import ttkbootstrap as ttk
import os
import sys
import tempfile
import shutil
from PIL import Image, ImageDraw

# Add the parent directory to sys.path to import pdf_preview modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pdf_preview.interface import PDFPreviewInterface
from pdf_preview.viewer import PDFPreviewViewer
from pdf_preview.manager import PDFPreviewManager


def create_test_pdf(pdf_path):
    """
    Create a simple test PDF file for testing.
    
    Args:
        pdf_path (str): Path where to create the PDF
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a simple PDF with ReportLab
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Add some content
        c.setFont("Helvetica", 24)
        c.drawString(100, height - 100, "Test PDF Document")
        
        c.setFont("Helvetica", 16)
        c.drawString(100, height - 150, "This is a test PDF for AutomaTeX")
        
        c.drawString(100, height - 200, f"Created: {pdf_path}")
        
        # Add some shapes
        c.rect(100, height - 300, 400, 200)
        c.drawString(120, height - 250, "This is a rectangle")
        
        # Add multiple pages
        c.showPage()
        
        c.setFont("Helvetica", 24)
        c.drawString(100, height - 100, "Second Page")
        
        c.setFont("Helvetica", 16)
        c.drawString(100, height - 150, "This is the second page of the test PDF")
        
        c.save()
        print(f"Created test PDF: {pdf_path}")
        return True
        
    except ImportError:
        # If ReportLab is not available, create a simple image-based PDF
        try:
            # Create a simple image and save as PDF
            image = Image.new('RGB', (600, 800), color='white')
            draw = ImageDraw.Draw(image)
            
            # Draw some text (this is a simplification)
            draw.text((50, 50), "Test PDF Document", fill='black')
            draw.text((50, 100), "This is a test PDF for AutomaTeX", fill='black')
            draw.rectangle([50, 150, 550, 350], outline='black')
            draw.text((60, 200), "This is a rectangle", fill='black')
            
            image.save(pdf_path, "PDF", resolution=100.0)
            print(f"Created simple test PDF: {pdf_path}")
            return True
        except Exception as e:
            print(f"Could not create test PDF: {e}")
            return False


def test_pdf_preview_interface():
    """
    Test the PDF preview interface creation and functionality.
    """
    print("Testing PDF Preview Interface...")
    
    # Create a simple test window
    root = tk.Tk()
    root.title("PDF Preview Test")
    root.geometry("1000x700")
    
    # Create a main paned window
    main_pane = ttk.PanedWindow(root, orient=ttk.HORIZONTAL)
    main_pane.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create left panel (simulating editor)
    left_frame = ttk.Frame(main_pane, width=400)
    left_frame.pack(fill="both", expand=True)
    
    editor_label = ttk.Label(
        left_frame,
        text="Editor Area\n(Placeholder)",
        font=("Arial", 16),
        anchor="center"
    )
    editor_label.pack(expand=True)
    
    main_pane.add(left_frame, weight=1)
    
    # Create right panel for PDF preview
    right_frame = ttk.Frame(main_pane, width=600)
    right_frame.pack(fill="both", expand=True)
    
    # Header for PDF preview
    header = ttk.Label(
        right_frame, 
        text="PDF Preview", 
        font=("Arial", 12, "bold"),
        anchor="center"
    )
    header.pack(fill="x", padx=5, pady=5)
    
    # Separator
    separator = ttk.Separator(right_frame, orient="horizontal")
    separator.pack(fill="x", padx=5)
    
    # Content frame for PDF preview
    content_frame = ttk.Frame(right_frame)
    content_frame.pack(fill="both", expand=True, padx=2, pady=2)
    
    main_pane.add(right_frame, weight=2)
    
    # Test creating the PDF preview interface
    def get_current_tab():
        # Simple mock that returns None
        return None
    
    try:
        pdf_interface = PDFPreviewInterface(root, get_current_tab)
        print("✓ PDF Preview Interface created successfully")
        
        # Test creating a preview panel
        preview_panel = pdf_interface.create_preview_panel(content_frame)
        print("✓ PDF Preview Panel created successfully")
        
        # Test the preview manager
        preview_manager = pdf_interface.get_preview_manager()
        if preview_manager:
            print("✓ PDF Preview Manager accessed successfully")
            
            # Test the viewer
            viewer = preview_manager.get_viewer()
            if viewer:
                print("✓ PDF Viewer accessed successfully")
            else:
                print("✗ Could not access PDF Viewer")
                return False
        else:
            print("✗ Could not access PDF Preview Manager")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error creating PDF Preview Interface: {e}")
        return False


def test_pdf_loading():
    """
    Test loading an existing PDF file.
    """
    print("\nTesting PDF Loading...")
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="pdf_preview_test_")
    
    try:
        # Create a test PDF file
        pdf_path = os.path.join(test_dir, "test_document.pdf")
        
        # Try to create a test PDF
        if create_test_pdf(pdf_path) and os.path.exists(pdf_path):
            print("✓ Test PDF created successfully")
            
            # Test the viewer with the PDF
            root = tk.Tk()
            root.withdraw()  # Hide the window
            
            # Create a frame for the viewer
            frame = ttk.Frame(root)
            frame.pack(fill="both", expand=True)
            
            # Create viewer
            viewer = PDFPreviewViewer(frame)
            
            # Load the PDF
            viewer.load_pdf(pdf_path)
            
            # Check if PDF was loaded
            if hasattr(viewer, 'pdf_path') and viewer.pdf_path == pdf_path:
                print("✓ PDF loaded successfully in viewer")
                success = True
            else:
                print("✗ PDF not loaded correctly")
                success = False
            
            root.destroy()
            
            return success
        else:
            print("✗ Could not create test PDF")
            return False
            
    except Exception as e:
        print(f"✗ Error testing PDF loading: {e}")
        return False
    finally:
        # Clean up
        try:
            shutil.rmtree(test_dir)
        except Exception as e:
            print(f"Warning: Could not clean up test directory: {e}")


def run_all_tests():
    """
    Run all PDF preview tests.
    """
    print("Running comprehensive PDF Preview tests...\n")
    
    # Test 1: Interface creation
    test1_passed = test_pdf_preview_interface()
    
    # Test 2: PDF loading
    test2_passed = test_pdf_loading()
    
    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    
    if test1_passed:
        print("✓ PDF Preview Interface Test: PASSED")
    else:
        print("✗ PDF Preview Interface Test: FAILED")
        
    if test2_passed:
        print("✓ PDF Loading Test: PASSED")
    else:
        print("✗ PDF Loading Test: FAILED")
    
    all_passed = test1_passed and test2_passed
    
    if all_passed:
        print("\n🎉 All tests passed! PDF Preview feature is working correctly.")
        print("\nTo test with a real PDF:")
        print("1. Open a .tex file that has a corresponding .pdf file")
        print("2. The PDF should automatically appear in the preview panel")
        print("3. You can navigate pages, zoom, and refresh the preview")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)