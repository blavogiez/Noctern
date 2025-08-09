"""
PDF Preview Viewer Component
Handles the display and navigation of PDF documents with synchronization features.
"""

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import Canvas, Scrollbar
from PIL import Image, ImageTk
import os
import threading
from utils import debug_console


class PDFPreviewViewer:
    """
    A PDF preview viewer component that displays PDF documents and provides
    navigation and synchronization features.
    """
    
    def __init__(self, parent, pdf_path=None):
        """
        Initialize the PDF preview viewer.
        
        Args:
            parent (tk.Widget): Parent widget to place the viewer in
            pdf_path (str, optional): Path to the PDF file to display
        """
        self.parent = parent
        self.pdf_path = pdf_path
        self.current_page = 1
        self.total_pages = 1
        self.zoom_level = 1.0
        
        # Caching and performance
        self.master_images = {}  # Cache for high-res master page images
        self.display_photo = None # To prevent garbage collection
        self.render_lock = threading.Lock()
        self.prerender_thread = None
        self.MASTER_DPI = 200 # Fixed high DPI for master images
        
        self._create_widgets()
        if pdf_path and os.path.exists(pdf_path):
            self.load_pdf(pdf_path)
    
    def _create_widgets(self):
        """Create and configure the viewer widgets."""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        # Toolbar
        self._create_toolbar()
        
        # Canvas for PDF display with scrollbars
        self.canvas_frame = ttk.Frame(self.frame)
        self.canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create canvas with scrollbars
        self.canvas = Canvas(self.canvas_frame, bg="lightgray")
        self.v_scrollbar = Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind events for zooming
        self.canvas.bind("<Control-MouseWheel>", self._on_zoom)
        self.canvas.bind("<Control-Button-4>", self._on_zoom_in)
        self.canvas.bind("<Control-Button-5>", self._on_zoom_out)
    
    def _create_toolbar(self):
        """Create the toolbar with navigation controls."""
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # Navigation buttons
        self.prev_button = ttk.Button(toolbar, text="◀ Previous", command=self.previous_page, state="disabled")
        self.prev_button.pack(side="left", padx=(0, 5))
        
        self.page_label = ttk.Label(toolbar, text="Page 1 of 1")
        self.page_label.pack(side="left", padx=10)
        
        self.next_button = ttk.Button(toolbar, text="Next ▶", command=self.next_page, state="disabled")
        self.next_button.pack(side="left", padx=(5, 10))
        
        # Zoom controls
        ttk.Label(toolbar, text="Zoom:").pack(side="left", padx=(10, 5))
        
        self.zoom_out_button = ttk.Button(toolbar, text="−", width=3, command=self.zoom_out, state="disabled")
        self.zoom_out_button.pack(side="left", padx=(0, 2))
        
        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_in_button = ttk.Button(toolbar, text="+", width=3, command=self.zoom_in, state="disabled")
        self.zoom_in_button.pack(side="left", padx=(2, 10))
        
        # Refresh button
        self.refresh_button = ttk.Button(toolbar, text="Refresh", command=self.refresh)
        self.refresh_button.pack(side="right")
        
        # Page jump
        ttk.Label(toolbar, text="Go to page:").pack(side="right", padx=(20, 5))
        self.page_entry = ttk.Entry(toolbar, width=5)
        self.page_entry.pack(side="right", padx=5)
        self.page_entry.bind("<Return>", self._on_page_entry)
        
        # Go button
        self.go_button = ttk.Button(toolbar, text="Go", command=self._go_to_page, state="disabled")
        self.go_button.pack(side="right", padx=(0, 5))
    
    def _on_page_entry(self, event):
        """Handle page entry submission."""
        self._go_to_page()
    
    def _go_to_page(self):
        """Go to the page specified in the entry."""
        try:
            page_num = int(self.page_entry.get())
            if 1 <= page_num <= self.total_pages:
                self.current_page = page_num
                self._update_page_display()
        except ValueError:
            pass  # Ignore invalid input
    
    def _on_zoom(self, event):
        """Handle zoom with mouse wheel."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def _on_zoom_in(self, event):
        """Handle zoom in with mouse wheel (Linux)."""
        self.zoom_in()
    
    def _on_zoom_out(self, event):
        """Handle zoom out with mouse wheel (Linux)."""
        self.zoom_out()
    
    def _create_placeholder(self):
        """Create a placeholder display when no PDF is loaded."""
        self.canvas.delete("all")
        
        # Clear page cache
        self._clear_page_cache()
        
        # Reset page info
        self.current_page = 1
        self.total_pages = 1
        self.zoom_level = 1.0
        
        # Update UI
        self.page_label.configure(text="Page 1 of 1")
        self.zoom_label.configure(text="100%")
        self._disable_toolbar()
        
        # Draw placeholder
        width, height = 600, 800
        self.canvas.configure(scrollregion=(0, 0, width, height))
        
        # Background
        self.canvas.create_rectangle(0, 0, width, height, fill="white", outline="gray")
        
        # Placeholder text
        self.canvas.create_text(
            width // 2, height // 2 - 50,
            text="PDF Preview",
            font=("Arial", 24, "bold"),
            fill="gray"
        )
        
        self.canvas.create_text(
            width // 2, height // 2,
            text="No PDF document loaded",
            font=("Arial", 16),
            fill="lightgray"
        )
        
        self.canvas.create_text(
            width // 2, height // 2 + 50,
            text="Open a .tex file with an associated .pdf to preview it here",
            font=("Arial", 12),
            fill="lightgray"
        )
    
    def load_pdf(self, pdf_path):
        """
        Load a PDF file for preview.
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        if not os.path.exists(pdf_path):
            debug_console.log(f"PDF file not found: {pdf_path}", level='ERROR')
            self._create_placeholder()
            return
            
        self.pdf_path = pdf_path
        self._clear_page_cache()
        debug_console.log(f"Loading PDF: {pdf_path}", level='INFO')
        
        try:
            # Get page count using PyPDF2
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            self.total_pages = len(reader.pages)
            
            debug_console.log(f"PDF has {self.total_pages} pages", level='INFO')
            
            # Reset to first page
            self.current_page = 1
            
            # Enable toolbar
            self._enable_toolbar()
            
            # Render first page
            self._update_page_display()
            
        except ImportError as e:
            debug_console.log(f"PDF rendering libraries not available: {e}", level='ERROR')
            self._show_pdf_info()
        except Exception as e:
            debug_console.log(f"Error loading PDF: {e}", level='ERROR')
            self._create_placeholder()
    
    def _show_pdf_info(self):
        """Show PDF information when rendering is not available."""
        self.canvas.delete("all")
        
        width, height = 600, 400
        self.canvas.configure(scrollregion=(0, 0, width, height))
        
        # Background
        self.canvas.create_rectangle(0, 0, width, height, fill="white", outline="gray")
        
        # Title
        self.canvas.create_text(
            width // 2, 50,
            text="PDF Preview",
            font=("Arial", 24, "bold"),
            fill="black"
        )
        
        # PDF info
        if self.pdf_path:
            filename = os.path.basename(self.pdf_path)
            self.canvas.create_text(
                width // 2, 120,
                text=f"File: {filename}",
                font=("Arial", 14),
                fill="black"
            )
            
            self.canvas.create_text(
                width // 2, 160,
                text=f"Path: {self.pdf_path}",
                font=("Arial", 12),
                fill="gray"
            )
            
            self.canvas.create_text(
                width // 2, 200,
                text=f"Pages: {self.total_pages}",
                font=("Arial", 12),
                fill="black"
            )
        
        # Install message
        self.canvas.create_text(
            width // 2, 300,
            text="To enable full PDF rendering, install required packages:",
            font=("Arial", 12),
            fill="blue"
        )
        
        self.canvas.create_text(
            width // 2, 330,
            text="pip install pdf2image Pillow PyPDF2",
            font=("Courier", 12),
            fill="red"
        )
    
    def _get_master_image(self, page_num):
        """
        Get the high-resolution master image for a page, rendering if not cached.
        """
        if page_num in self.master_images:
            return self.master_images[page_num]
        
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            return None
        
        # Render the page if not in cache
        try:
            from pdf2image import convert_from_path
            
            debug_console.log(f"Rendering master image for page {page_num} at {self.MASTER_DPI} DPI", level='DEBUG')
            images = convert_from_path(
                self.pdf_path,
                first_page=page_num,
                last_page=page_num,
                dpi=self.MASTER_DPI,
                grayscale=False
            )
            
            if images:
                self.master_images[page_num] = images[0]
                return images[0]
                
        except ImportError:
            self.parent.after(0, self._show_pdf_info)
        except Exception as e:
            debug_console.log(f"Error rendering master page {page_num}: {e}", level='ERROR')
        
        return None

    def _update_page_display(self):
        """
        Update the canvas with the current page at the current zoom level.
        """
        master_image = self._get_master_image(self.current_page)
        
        if not master_image:
            return

        # Resize master image based on zoom level
        original_width, original_height = master_image.size
        new_width = int(original_width * self.zoom_level * (100 / self.MASTER_DPI))
        new_height = int(original_height * self.zoom_level * (100 / self.MASTER_DPI))

        # Use ANTIALIAS for better quality resizing
        resized_image = master_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        self.canvas.delete("all")
        
        # Convert PIL image to PhotoImage
        self.display_photo = ImageTk.PhotoImage(resized_image)
        
        # Configure scroll region
        self.canvas.configure(scrollregion=(0, 0, new_width, new_height))
        
        # Display image
        self.canvas.create_image(0, 0, anchor="nw", image=self.display_photo)
        
        # Update page label
        self.page_label.configure(text=f"Page {self.current_page} of {self.total_pages}")
        
        # Update zoom label
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_label.configure(text=f"{zoom_percent}%")

        # Start pre-rendering adjacent pages
        self._start_prerender()

    def _start_prerender(self):
        """Start a background thread to pre-render adjacent pages."""
        if self.prerender_thread and self.prerender_thread.is_alive():
            return # A thread is already running

        self.prerender_thread = threading.Thread(
            target=self._prerender_worker,
            args=(self.current_page,),
            daemon=True
        )
        self.prerender_thread.start()

    def _prerender_worker(self, initial_page):
        """
        Worker thread to pre-render pages around the initial page.
        """
        # Pre-render next pages
        for i in range(1, 4):
            page_to_render = initial_page + i
            if page_to_render > self.total_pages:
                break
            if page_to_render not in self.master_images:
                self._get_master_image(page_to_render)
        
        # Pre-render previous pages
        for i in range(1, 3):
            page_to_render = initial_page - i
            if page_to_render < 1:
                break
            if page_to_render not in self.master_images:
                self._get_master_image(page_to_render)

    def _enable_toolbar(self):
        """Enable toolbar buttons when PDF is loaded."""
        self.prev_button.configure(state="normal")
        self.next_button.configure(state="normal")
        self.zoom_out_button.configure(state="normal")
        self.zoom_in_button.configure(state="normal")
        self.go_button.configure(state="normal")
    
    def _disable_toolbar(self):
        """Disable toolbar buttons when no PDF is loaded."""
        self.prev_button.configure(state="disabled")
        self.next_button.configure(state="disabled")
        self.zoom_out_button.configure(state="disabled")
        self.zoom_in_button.configure(state="disabled")
        self.go_button.configure(state="disabled")
    
    def previous_page(self):
        """Navigate to the previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_page_display()
    
    def next_page(self):
        """Navigate to the next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._update_page_display()
    
    def zoom_in(self):
        """Increase the zoom level."""
        if self.zoom_level < 3.0:  # Max 300%
            self.zoom_level *= 1.2
            self._update_page_display()
    
    def zoom_out(self):
        """Decrease the zoom level."""
        if self.zoom_level > 0.2:  # Min 20%
            self.zoom_level /= 1.2
            self._update_page_display()
    
    def _clear_page_cache(self):
        """Clear all page caches."""
        self.master_images.clear()
    
    def refresh(self):
        """Refresh the PDF display."""
        if self.pdf_path:
            debug_console.log("Refreshing PDF preview", level='INFO')
            self._clear_page_cache()
            self.load_pdf(self.pdf_path)
    
    def synchronize_with_editor(self, line_number):
        """
        Synchronize the PDF view with a specific line in the editor.
        
        Args:
            line_number (int): Line number in the LaTeX editor
        """
        debug_console.log(f"Synchronizing PDF with editor line {line_number}", level='DEBUG')
        # In a full implementation, this would scroll to the relevant page/position
    
    def get_widget(self):
        """
        Get the main widget for this viewer.
        
        Returns:
            ttk.Frame: The main frame containing the viewer
        """
        return self.frame
