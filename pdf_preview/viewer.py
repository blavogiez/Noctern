"""
PDF Preview Viewer Component
Handles the display and navigation of PDF documents with continuous scrolling.
"""

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import Canvas, Scrollbar
from PIL import Image, ImageTk
import os
import threading
import time
from utils import debug_console

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

# Import the new navigator component
from pdf_preview.navigator import PDFTextNavigator
from pdf_preview.sync import PDFSyncManager
# Import the new circular magnifier component
from pdf_preview.magnifier import CircularMagnifier


class PDFPreviewViewer:
    """
    A PDF preview viewer component that displays PDF documents with continuous scrolling.
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
        self.zoom_level = 0.7  # Start with a smaller zoom level for better initial view
        
        # Caching and performance
        self.page_cache = {}  # LRU cache for rendered pages
        self.page_layouts = {}  # Layout information for each page
        self.total_height = 0
        self.render_thread = None
        self.pdf_doc = None  # Store PDF document reference
        self.total_pages = 0
        self.RENDER_DPI = 150
        self.MAX_CACHE_SIZE = 8  # Maximum cached pages
        self.visible_pages = set()  # Currently visible page numbers
        self.cache_order = []  # LRU tracking
        
        # Status tracking
        self.last_compilation_time = None
        self.compilation_status = "Not yet compiled"
        self.status_update_job = None
        
        # Text navigator component
        self.text_navigator = PDFTextNavigator(self)
        
        # Sync manager for text search (share instance with interface to avoid duplication)
        self.sync_manager = None  # Will be set by interface when needed
        
        # Magnifier properties
        self.magnifier_active = False
        self.magnifier = None
        
        self._create_widgets()
        if pdf_path and os.path.exists(pdf_path):
            self.load_pdf(pdf_path)
    
    def _create_widgets(self):
        """Create and configure the viewer widgets."""
        # Main frame
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        # Status label (replaces "PDF Preview" title)
        self.status_label = ttk.Label(self.frame, text="Not yet compiled", anchor="w")
        self.status_label.pack(fill="x", padx=5, pady=(5, 0))
        
        # Toolbar (with previous/next buttons)
        self._create_toolbar()
        
        # Canvas for PDF display with scrollbars
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create canvas with scrollbars
        self.canvas = Canvas(canvas_frame, bg="lightgray")
        v_scrollbar = Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        h_scrollbar = Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind events for zooming and scrolling
        self.canvas.bind("<Control-MouseWheel>", self._on_zoom)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel_up)
        self.canvas.bind("<Button-5>", self._on_mouse_wheel_down)
    
    def _create_toolbar(self):
        """Create the toolbar with navigation controls."""
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # Zoom controls
        ttk.Label(toolbar, text="Zoom:").pack(side="left", padx=(0, 5))
        
        self.zoom_out_button = ttk.Button(toolbar, text="−", width=3, command=self.zoom_out, state="disabled")
        self.zoom_out_button.pack(side="left", padx=(0, 2))
        
        self.zoom_label = ttk.Label(toolbar, text="100%")
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_in_button = ttk.Button(toolbar, text="+", width=3, command=self.zoom_in, state="disabled")
        self.zoom_in_button.pack(side="left", padx=(2, 10))
        
        # Magnifier button
        self.magnifier_button = ttk.Button(toolbar, text="🔍 Magnifier", command=self.toggle_magnifier)
        self.magnifier_button.pack(side="left", padx=(0, 10))
        
        # Refresh button
        self.refresh_button = ttk.Button(toolbar, text="Refresh", command=self.refresh)
        self.refresh_button.pack(side="right")
        
        # Magnifier state
        self.magnifier_active = False
        self.magnifier = None
    
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.canvas.after_idle(self._update_visible_pages)
        
    def _on_mouse_wheel_up(self, event):
        """Handle mouse wheel up scrolling (Linux)."""
        self.canvas.yview_scroll(-1, "units")
        self.canvas.after_idle(self._update_visible_pages)
        
    def _on_mouse_wheel_down(self, event):
        """Handle mouse wheel down scrolling (Linux)."""
        self.canvas.yview_scroll(1, "units")
        self.canvas.after_idle(self._update_visible_pages)
    
    def _on_zoom(self, event):
        """Handle zoom with mouse wheel."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def _create_placeholder(self):
        """Create a placeholder display when no PDF is loaded."""
        self.canvas.delete("all")
        self._clear_caches()
        self.zoom_level = 1.0
        self.zoom_label.configure(text="100%")
        self._disable_toolbar()
        
        width, height = 600, 800
        self.canvas.configure(scrollregion=(0, 0, width, height))
        
        # Background
        self.canvas.create_rectangle(0, 0, width, height, fill="white", outline="gray")
        
        # Placeholder text
        self.canvas.create_text(
            width // 2, height // 2,
            text="No PDF document loaded",
            font=("Arial", 16),
            fill="lightgray"
        )
        
        self._update_status_label()
    
    def _clear_caches(self):
        """Clear all page caches."""
        self.page_cache.clear()
        self.page_layouts.clear()
        self.cache_order.clear()
        self.visible_pages.clear()
        if self.pdf_doc:
            self.pdf_doc = None
    
    def load_pdf(self, pdf_path):
        """
        Load a PDF file for preview.
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        if not os.path.exists(pdf_path):
            self._create_placeholder()
            return
            
        self.pdf_path = pdf_path
        self._clear_caches()
        
        # Clear any text highlights
        if hasattr(self, 'text_navigator'):
            self.text_navigator.clear_highlights()
        
        # Cancel any existing render thread
        if self.render_thread and self.render_thread.is_alive():
            return
            
        # Start rendering in a separate thread
        self.render_thread = threading.Thread(target=self._render_all_pages, daemon=True)
        self.render_thread.start()
    
    def _render_all_pages(self):
        """Initialize PDF document and get page count in a separate thread."""
        try:
            if HAS_FITZ:
                self.pdf_doc = fitz.open(self.pdf_path)
                self.total_pages = len(self.pdf_doc)
                # Update UI in main thread
                self.parent.after(0, self._initialize_layout)
            else:
                raise ImportError("PyMuPDF not available")
        except (ImportError, Exception):
            # Fallback to pdf2image if PyMuPDF not available
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(self.pdf_path, dpi=self.RENDER_DPI, first_page=1, last_page=1)
                if images:
                    # Get total page count without loading all pages
                    from pdf2image.pdf2image import pdfinfo_from_path
                    info = pdfinfo_from_path(self.pdf_path)
                    self.total_pages = info.get('Pages', 1)
                    self.parent.after(0, self._initialize_layout)
            except Exception as fallback_e:
                debug_console.log(f"Error with fallback PDF loading: {fallback_e}", level='ERROR')
                self.parent.after(0, self._create_placeholder)
        except Exception as e:
            debug_console.log(f"Error loading PDF: {e}", level='ERROR')
            self.parent.after(0, self._create_placeholder)
    
    def _initialize_layout(self):
        """Initialize the layout with placeholder rectangles for all pages."""
        self.canvas.delete("all")
        self.page_layouts.clear()
        
        # Get sample page dimensions
        sample_width, sample_height = self._get_page_dimensions(1)
        if not sample_width or not sample_height:
            self._create_placeholder()
            return
            
        y_offset = 10
        max_width = 0
        
        # Create layout for all pages without rendering them
        for page_num in range(1, self.total_pages + 1):
            # Calculate display dimensions
            disp_w = int(sample_width * self.zoom_level)
            disp_h = int(sample_height * self.zoom_level)
            
            # Store layout information
            self.page_layouts[page_num] = {
                'y_offset': y_offset,
                'height': disp_h,
                'width': disp_w
            }
            
            # Create placeholder rectangle
            self.canvas.create_rectangle(
                10, y_offset, 10 + disp_w, y_offset + disp_h,
                fill="white", outline="gray", tags=f"page_{page_num}"
            )
            
            # Update offset and width
            y_offset += disp_h + 10
            if disp_w > max_width:
                max_width = disp_w
                
        # Set scroll region
        self.total_height = y_offset
        self.canvas.configure(scrollregion=(0, 0, max_width + 20, self.total_height))
        
        # Enable toolbar
        self._enable_toolbar()
        
        # Update status
        self._update_status_label()
        
        # Bind scroll events to trigger lazy loading
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-1>", self._on_canvas_scroll)
        self.canvas.bind("<B1-Motion>", self._on_canvas_scroll)
        
        # Load initial visible pages
        self._update_visible_pages()
        
    def _get_page_dimensions(self, page_num):
        """Get dimensions of a specific page without fully rendering it."""
        try:
            if HAS_FITZ and self.pdf_doc:  # PyMuPDF
                page = self.pdf_doc[page_num - 1]
                rect = page.rect
                return rect.width, rect.height
            else:  # Fallback to pdf2image
                from pdf2image import convert_from_path
                images = convert_from_path(self.pdf_path, dpi=self.RENDER_DPI, first_page=page_num, last_page=page_num)
                if images:
                    return images[0].size
        except Exception as e:
            debug_console.log(f"Error getting page dimensions: {e}", level='ERROR')
        return None, None
        
    def _render_page(self, page_num):
        """Render a specific page and return the PIL Image."""
        try:
            if HAS_FITZ and self.pdf_doc:  # PyMuPDF - faster rendering
                page = self.pdf_doc[page_num - 1]
                # Calculate zoom factor for desired DPI
                zoom = self.RENDER_DPI / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(img_data))
                return img
            else:  # Fallback to pdf2image
                from pdf2image import convert_from_path
                images = convert_from_path(self.pdf_path, dpi=self.RENDER_DPI, first_page=page_num, last_page=page_num)
                if images:
                    return images[0]
        except Exception as e:
            debug_console.log(f"Error rendering page {page_num}: {e}", level='ERROR')
        return None
        
    def _get_cached_page(self, page_num):
        """Get a page from cache or render it if not cached."""
        # Check if page is in cache
        if page_num in self.page_cache:
            # Move to end of LRU list
            self.cache_order.remove(page_num)
            self.cache_order.append(page_num)
            return self.page_cache[page_num]
            
        # Render the page
        img = self._render_page(page_num)
        if not img:
            return None
            
        # Add to cache
        self._add_to_cache(page_num, img)
        return img
        
    def _add_to_cache(self, page_num, img):
        """Add a page to the cache, evicting oldest if necessary."""
        # Remove oldest pages if cache is full
        while len(self.page_cache) >= self.MAX_CACHE_SIZE:
            oldest_page = self.cache_order.pop(0)
            del self.page_cache[oldest_page]
            
        # Add new page
        self.page_cache[page_num] = img
        self.cache_order.append(page_num)
        
    def _update_visible_pages(self):
        """Update the set of visible pages and render them."""
        if not self.page_layouts:
            return
            
        # Get visible area
        canvas_height = self.canvas.winfo_height()
        scroll_top = self.canvas.canvasy(0)
        scroll_bottom = scroll_top + canvas_height
        
        # Find visible pages
        new_visible_pages = set()
        for page_num, layout in self.page_layouts.items():
            page_top = layout['y_offset']
            page_bottom = page_top + layout['height']
            
            # Check if page overlaps with visible area (with buffer)
            buffer = 200  # Load pages slightly outside viewport
            if page_bottom >= scroll_top - buffer and page_top <= scroll_bottom + buffer:
                new_visible_pages.add(page_num)
                
        # Render newly visible pages
        for page_num in new_visible_pages - self.visible_pages:
            self._render_visible_page(page_num)
            
        # Remove non-visible pages from display (but keep in cache)
        for page_num in self.visible_pages - new_visible_pages:
            self.canvas.delete(f"page_img_{page_num}")
            
        self.visible_pages = new_visible_pages
        
    def _render_visible_page(self, page_num):
        """Render and display a specific visible page."""
        if page_num not in self.page_layouts:
            return
            
        layout = self.page_layouts[page_num]
        img = self._get_cached_page(page_num)
        
        if img:
            # Calculate display dimensions
            disp_w = int(img.width * self.zoom_level)
            disp_h = int(img.height * self.zoom_level)
            
            # Resize image for display
            if disp_w != layout['width'] or disp_h != layout['height']:
                # Update layout if dimensions changed due to zoom
                layout['width'] = disp_w
                layout['height'] = disp_h
                
            display_img = img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(display_img)
            
            # Remove placeholder and add image
            self.canvas.delete(f"page_{page_num}")
            image_id = self.canvas.create_image(10, layout['y_offset'], anchor="nw", image=photo, tags=f"page_img_{page_num}")
            
            # Store photo reference to prevent garbage collection
            setattr(self.canvas, f"photo_{page_num}", photo)
            
    def _on_canvas_configure(self, event=None):
        """Handle canvas resize events."""
        self.canvas.after_idle(self._update_visible_pages)
        
    def _on_canvas_scroll(self, event=None):
        """Handle canvas scroll events."""
        self.canvas.after_idle(self._update_visible_pages)
        
    def _update_zoom(self):
        """Update display after zoom change."""
        if not self.page_layouts:
            return
            
        # Get sample page dimensions
        sample_width, sample_height = self._get_page_dimensions(1)
        if not sample_width or not sample_height:
            return
            
        # Clear current display
        self.canvas.delete("all")
        
        # Update layouts and recreate placeholders
        y_offset = 10
        max_width = 0
        
        for page_num in range(1, self.total_pages + 1):
            # Calculate new display dimensions
            disp_w = int(sample_width * self.zoom_level)
            disp_h = int(sample_height * self.zoom_level)
            
            # Update layout
            self.page_layouts[page_num].update({
                'y_offset': y_offset,
                'height': disp_h,
                'width': disp_w
            })
            
            # Create placeholder rectangle
            self.canvas.create_rectangle(
                10, y_offset, 10 + disp_w, y_offset + disp_h,
                fill="white", outline="gray", tags=f"page_{page_num}"
            )
            
            y_offset += disp_h + 10
            if disp_w > max_width:
                max_width = disp_w
                
        # Update scroll region
        self.total_height = y_offset
        self.canvas.configure(scrollregion=(0, 0, max_width + 20, self.total_height))
        
        # Clear cache of scaled images (they need to be re-rendered at new zoom)
        for page_num in list(self.page_cache.keys()):
            del self.page_cache[page_num]
        self.cache_order.clear()
        self.visible_pages.clear()
        
        # Re-render visible pages
        self._update_visible_pages()

    def _enable_toolbar(self):
        """Enable toolbar buttons."""
        for btn in [self.zoom_in_button, self.zoom_out_button]:
            btn.configure(state="normal")
    
    def _disable_toolbar(self):
        """Disable toolbar buttons."""
        for btn in [self.zoom_in_button, self.zoom_out_button]:
            btn.configure(state="disabled")
    
    def zoom_in(self):
        """Zoom in on the PDF."""
        if self.zoom_level < 3.0:
            self.zoom_level *= 1.2
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
            self._update_zoom()
    
    def zoom_out(self):
        """Zoom out on the PDF."""
        if self.zoom_level > 0.3:
            self.zoom_level /= 1.2
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
            self._update_zoom()
    
    def previous_page(self):
        """Scroll to the previous page."""
        if not self.page_layouts:
            return
            
        # Get current view position
        current_y = self.canvas.yview()[0] * self.total_height
        
        # Find current page
        current_page = 1
        for page_num, layout in self.page_layouts.items():
            if layout['y_offset'] <= current_y < layout['y_offset'] + layout['height']:
                current_page = page_num
                break
                
        # Scroll to previous page
        if current_page > 1:
            prev_layout = self.page_layouts[current_page - 1]
            self.canvas.yview_moveto(prev_layout['y_offset'] / self.total_height)
    
    def next_page(self):
        """Scroll to the next page."""
        if not self.page_layouts:
            return
            
        # Get current view position
        current_y = self.canvas.yview()[0] * self.total_height
        
        # Find current page
        current_page = 1
        for page_num, layout in self.page_layouts.items():
            if layout['y_offset'] <= current_y < layout['y_offset'] + layout['height']:
                current_page = page_num
                
        # Scroll to next page
        if current_page < len(self.page_layouts):
            next_layout = self.page_layouts[current_page + 1]
            self.canvas.yview_moveto(next_layout['y_offset'] / self.total_height)
    
    def refresh(self):
        """Refresh the PDF display."""
        if self.pdf_path:
            self.load_pdf(self.pdf_path)
    
    def _update_status_label(self):
        """Update the status label with compilation information."""
        status_text = self.compilation_status
        time_ago = ""
        
        if self.last_compilation_time:
            seconds = int(time.time() - self.last_compilation_time)
            if seconds < 60:
                time_ago = "Last compiled less than a minute ago"
            else:
                minutes = seconds // 60
                if minutes == 1:
                    time_ago = "Last compiled about a minute ago"
                else:
                    time_ago = f"Last compiled {minutes} minutes ago"
        
        full_text = f"{time_ago}\n{status_text}" if time_ago else status_text
        self.status_label.config(text=full_text)
    
    def set_compilation_status(self, status, last_compilation_time=None):
        """
        Set the compilation status and update the display.
        
        Args:
            status (str): Compilation status ("Compilable", "Compiling...", "Not compilable")
            last_compilation_time (float, optional): Timestamp of last compilation
        """
        self.compilation_status = status
        if last_compilation_time:
            self.last_compilation_time = last_compilation_time
        self._update_status_label()
    
    def get_widget(self):
        """
        Get the main widget for this viewer.
        
        Returns:
            ttk.Frame: The main frame widget
        """
        return self.frame
        
    def go_to_text(self, text, context_before="", context_after=""):
        """
        Navigate to the specified text in the PDF using the text navigator component.
        
        Args:
            text (str): Text to search for in the PDF
            context_before (str): Text before the target text
            context_after (str): Text after the target text
        """
        self.text_navigator.go_to_text(text, context_before, context_after)
        
    def toggle_magnifier(self):
        """Toggle the magnifier tool."""
        self.magnifier_active = not self.magnifier_active
        if self.magnifier_active:
            self.magnifier_button.configure(style="primary.TButton")  # Highlight when active
            self._create_magnifier()
        else:
            self.magnifier_button.configure(style="secondary.TButton")  # Normal when inactive
            self._destroy_magnifier()

    def _create_magnifier(self):
        """Create the magnifier window."""
        if self.magnifier:
            return
            
        # Create new circular magnifier
        self.magnifier = CircularMagnifier(self.parent, self)
        
        # Bind mouse motion to update magnifier
        self.canvas.bind("<Motion>", self._update_magnifier)
        self.canvas.bind("<Leave>", self._hide_magnifier)

    def _destroy_magnifier(self):
        """Destroy the magnifier window."""
        if self.magnifier:
            self.magnifier.destroy()
            self.magnifier = None
            
        # Unbind mouse events
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<Leave>")

    def _update_magnifier(self, event):
        """Update the magnifier view based on mouse position."""
        if not self.magnifier_active or not self.magnifier:
            return
            
        # Get mouse position relative to canvas
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Update magnifier window position
        self.magnifier.update_position(event.x_root, event.y_root)
        
        # Find which page we're hovering over
        current_page = None
        for page_num, layout in self.page_layouts.items():
            if (layout['y_offset'] <= canvas_y <= layout['y_offset'] + layout['height'] and
                10 <= canvas_x <= layout['width'] + 10):  # 10px margin
                current_page = page_num
                break
                
        if current_page:
            # Get the original image from cache
            original_img = self._get_cached_page(current_page)
            
            # Calculate the region to magnify
            # Convert canvas coordinates to image coordinates
            img_x = int((canvas_x - 10) / self.zoom_level)
            img_y = int((canvas_y - layout['y_offset']) / self.zoom_level)
            
            # Update the magnified view
            self.magnifier.update_view(original_img, img_x, img_y)

    def _hide_magnifier(self, event):
        """Hide the magnifier when mouse leaves the canvas."""
        if self.magnifier:
            self.magnifier.hide()