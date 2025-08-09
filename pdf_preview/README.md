# PDF Preview Module

This module provides live PDF preview functionality for the AutomaTeX application with synchronization between the LaTeX editor and PDF viewer.

## Features

1. **Live PDF Preview**: Automatically compiles and displays PDF previews of LaTeX documents
2. **Existing PDF Loading**: Automatically loads existing PDF files when opening .tex files
3. **Navigation Controls**: Page navigation, zoom controls, and refresh functionality
4. **Responsive Design**: Integrates seamlessly with the existing application interface
5. **Keyboard Shortcuts**: Ctrl+Mouse Wheel for zooming

## Components

### PDFPreviewViewer
Handles the display and navigation of PDF documents with full rendering capabilities.

### PDFPreviewManager
Manages the PDF preview functionality, including automatic compilation and synchronization.

### PDFSyncManager
Manages synchronization between the LaTeX editor and PDF preview, allowing bidirectional navigation.

### PDFPreviewInterface
Manages the integration of PDF preview functionality into the main application interface.

## Installation

### Required Python Packages
```bash
pip install pdf2image Pillow PyPDF2
```

Or run the provided batch file:
```bash
install_pdf_deps.bat
```

### System Requirements
- A TeX distribution with `pdflatex` (like MiKTeX or TeX Live)
- `poppler-utils` for PDF rendering (included in most installations)

## Usage

The PDF preview panel is automatically integrated into the main application window. It appears as a panel on the right side of the editor interface.

### Automatic Features
- When you open a .tex file that has a corresponding .pdf file, it's automatically loaded
- When you edit and save a .tex file, the PDF is automatically recompiled and refreshed
- Navigation controls allow you to move between pages and zoom in/out

### Manual Controls
- **Previous/Next Page**: Navigate through PDF pages
- **Zoom In/Out**: Adjust the zoom level (20% to 300%)
- **Refresh**: Force a recompilation and refresh of the PDF
- **Go to Page**: Jump to a specific page number
- **Ctrl+Mouse Wheel**: Zoom in/out

## Implementation Details

- The preview updates automatically when the editor content changes (with a 1-second delay)
- Compilation is triggered with a delay to avoid continuous compilation during rapid editing
- PDF rendering uses pdf2image to convert PDF pages to images for display
- Page images are cached for better performance when navigating
- The viewer includes comprehensive navigation controls and zoom functionality

## Troubleshooting

### PDF Not Displaying
1. Ensure `pdf2image`, `Pillow`, and `PyPDF2` are installed
2. Check that the .pdf file exists in the same directory as the .tex file
3. Verify that the PDF file is not corrupted

### Rendering Issues
1. If PDF pages appear blurry, try zooming in
2. If performance is slow, reduce the zoom level
3. Large PDF files may take longer to render

### Compilation Errors
1. Check that `pdflatex` is installed and in your system PATH
2. Ensure your .tex file compiles without errors
3. Check the application console for detailed error messages