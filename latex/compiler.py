
"""
This module provides functionalities for compiling LaTeX documents,
cleaning auxiliary files, and displaying the generated PDF.
It integrates with external command-line tools like `pdflatex`.
"""

import subprocess
import os
import platform
import tkinter as tk
from tkinter import messagebox
import shutil # Import shutil for file operations
import difflib # Import difflib for diffing
from utils import debug_console
from latex import error_parser


# Global reference to the root Tkinter window, initialized during application setup.
root = None
get_current_tab = None
show_console = None
hide_console = None
_pdf_monitor_setting = "Default" # Default value

def initialize_compiler(root_widget, get_current_tab_func, show_console_func, hide_console_func, pdf_monitor_setting="Default"):
    """
    Initializes the LaTeX compiler module by setting the root Tkinter window.

    This is necessary for displaying message boxes and other UI elements.

    Args:
        root_widget (tk.Tk): The main Tkinter application window.
    """
    global root, get_current_tab, show_console, hide_console, _pdf_monitor_setting
    root = root_widget
    get_current_tab = get_current_tab_func
    show_console = show_console_func
    hide_console = hide_console_func
    _pdf_monitor_setting = pdf_monitor_setting
    debug_console.log("LaTeX Compiler module initialized.", level='INFO')

def clean_project_directory(event=None):
    """
    Deletes common auxiliary files generated during LaTeX compilation from the project directory.

    This helps in keeping the project directory clean and can resolve certain compilation issues.
    The function identifies the project directory based on the currently active file's path.

    Args:
        event (tk.Event, optional): The Tkinter event object, if called from a binding. Defaults to None.
    """
    debug_console.log("Clean Project Directory command initiated.", level='ACTION')
    current_tab = get_current_tab()
    if not current_tab or not current_tab.file_path:
        messagebox.showwarning("Action Failed", "Please save your current file first to define a project directory for cleaning.")
        debug_console.log("Clean project failed: No active file path available.", level='WARNING')
        return

    try:
        project_directory = os.path.dirname(current_tab.file_path)
        
        # List of common LaTeX auxiliary file extensions to be deleted.
        extensions_to_delete = [
            '.aux', '.log', '.toc', '.bbl', '.bcf', '.blg', '.lof', '.lot', 
            '.out', '.run.xml', '.synctex.gz', '.fls', '.fdb_latexmk', '.nav', '.snm', '.vrb', '.dvi', '.ps'
        ]
        
        files_deleted_count = 0
        # Iterate through all files in the project directory.
        for filename in os.listdir(project_directory):
            # Check if the file ends with any of the specified auxiliary extensions.
            if any(filename.endswith(ext) for ext in extensions_to_delete):
                file_path_to_delete = os.path.join(project_directory, filename)
                try:
                    if os.path.exists(file_path_to_delete):
                        os.remove(file_path_to_delete)
                        files_deleted_count += 1
                        debug_console.log(f"Successfully deleted auxiliary file: {file_path_to_delete}", level='DEBUG')
                except OSError as e:
                    debug_console.log(f"Error deleting file '{file_path_to_delete}': {e}", level='ERROR')

        if files_deleted_count > 0:
            debug_console.log(f"Successfully cleaned {files_deleted_count} auxiliary file(s).", level='SUCCESS')
            messagebox.showinfo(
                "Project Cleaned",
                f"Successfully deleted {files_deleted_count} auxiliary file(s) from:\n\n{project_directory}"
            )
        else:
            debug_console.log("No auxiliary files found to clean in the project directory.", level='INFO')
            messagebox.showinfo("Project Clean", "No auxiliary files found to clean.")
    except Exception as e:
        error_msg = f"Error during project cleaning: {e}"
        messagebox.showerror("Error", error_msg)
        debug_console.log(error_msg, level='ERROR')



def compile_latex(event=None):
    """
    Compiles the current LaTeX document into a PDF using `pdflatex`.

    The content of the active editor tab is saved to a .tex file (either its original path
    or a temporary file), and `pdflatex` is executed. Upon successful compilation, a success
    message is shown. Compilation errors are shown in a log window.

    Args:
        event (tk.Event, optional): The Tkinter event object, if called from a binding. Defaults to None.
    """
    debug_console.log("LaTeX compilation process started.", level='ACTION')
    current_tab = get_current_tab()
    if not current_tab:
        debug_console.log("LaTeX compilation aborted: No active editor tab.", level='WARNING')
        return
    
    editor_content = current_tab.editor.get("1.0", tk.END)
    temp_file_created = False

    # Determine the source directory and file name for compilation.
    if current_tab.file_path:
        source_directory = os.path.dirname(current_tab.file_path)
        file_name = os.path.basename(current_tab.file_path)
        tex_file_path = current_tab.file_path
        try:
            # Save current editor content to the file.
            with open(tex_file_path, "w", encoding="utf-8") as f:
                f.write(editor_content)
            debug_console.log(f"Saved current content to '{tex_file_path}' for compilation.", level='DEBUG')
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Could not save current content to {tex_file_path} for compilation:\n{e}")
            debug_console.log(f"Error saving file for compilation: {e}", level='ERROR')
            return
    else:
        # For unsaved files, save to a temporary 'main.tex' in the 'output' directory.
        source_directory = "output"
        file_name = "main.tex"
        os.makedirs(source_directory, exist_ok=True)
        tex_file_path = os.path.join(source_directory, file_name)
        try:
            with open(tex_file_path, "w", encoding="utf-8") as f:
                f.write(editor_content)
            temp_file_created = True
            debug_console.log(f"Created temporary file '{tex_file_path}' for compilation.", level='DEBUG')
        except Exception as e:
            messagebox.showerror("Error Saving Temp File", f"Could not save temporary file for compilation:\n{e}")
            debug_console.log(f"Error saving temporary file for compilation: {e}", level='ERROR')
            return

    # Create output directory for cached successful compilations
    # This matches the existing cache mechanism used by the debug system
    output_directory = "output"
    os.makedirs(output_directory, exist_ok=True)
    cached_tex_path = os.path.join(output_directory, f"cached_{file_name}")

    # Compile in the source directory
    try:
        # Execute pdflatex command in the source directory
        command = ["pdflatex", "-interaction=nonstopmode", file_name]
        debug_console.log(f"Executing pdflatex command: {' '.join(command)} in directory: {source_directory}", level='DEBUG')
        result = subprocess.run(command, cwd=source_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
        
        # Path to log file and PDF in source directory
        log_file_path = os.path.join(source_directory, file_name.replace(".tex", ".log"))
        pdf_output_path = os.path.join(source_directory, file_name.replace(".tex", ".pdf"))

        # Get log content for both success and failure cases
        log_content = ""
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f_log:
                log_content = f_log.read()
        except FileNotFoundError:
            debug_console.log("Log file not found, proceeding with empty log.", level='WARNING')

        if result.returncode == 0:
            messagebox.showinfo("✅ Compilation Successful", "LaTeX document compiled successfully to PDF.")
            debug_console.log("LaTeX compilation successful.", level='SUCCESS')
            
            # Store successful version in the new debug system
            try:
                from app import state
                if hasattr(state, 'debug_coordinator') and state.debug_coordinator:
                    state.debug_coordinator.handle_compilation_result(
                        success=True,
                        log_content=log_content,
                        file_path=current_tab.file_path or tex_file_path,
                        current_content=editor_content
                    )
                    debug_console.log("Compilation result handled by debug system", level='INFO')
            except Exception as e:
                debug_console.log(f"Error handling compilation result in debug system: {e}", level='WARNING')
            
            # Cache successful compilation (legacy - for existing diff mechanism)
            try:
                shutil.copy2(tex_file_path, cached_tex_path)
                debug_console.log(f"Cached successful version to {cached_tex_path}", level='INFO')
            except Exception as e:
                debug_console.log(f"Failed to cache successful .tex file: {e}", level='ERROR')
            
            hide_console()
        else:
            messagebox.showerror("❌ LaTeX Compilation Failed", "Compilation failed. Check debug panel for details.")
            debug_console.log("LaTeX compilation failed. Updating debug panel.", level='ERROR')
            
            # Handle compilation failure with new debug system
            try:
                from app import state
                if hasattr(state, 'debug_coordinator') and state.debug_coordinator:
                    state.debug_coordinator.handle_compilation_result(
                        success=False,
                        log_content=log_content,
                        file_path=current_tab.file_path or tex_file_path,
                        current_content=editor_content
                    )
                    debug_console.log("Compilation errors handled by TeXstudio debug system", level='INFO')
                else:
                    # Fallback to old console display if debug system not available
                    error_summary = error_parser.parse_log_file(log_content)
                    show_console(error_summary)
                    debug_console.log("Used fallback error display", level='WARNING')
            except Exception as e:
                debug_console.log(f"Error handling compilation failure in debug system: {e}", level='ERROR')
                # Final fallback
                try:
                    error_summary = error_parser.parse_log_file(log_content)
                    show_console(error_summary)
                except Exception as e2:
                    debug_console.log(f"Error in fallback error display: {e2}", level='ERROR')
                    show_console(f"Error processing compilation log: {e2}")
    except FileNotFoundError:
        messagebox.showerror("Error", "`pdflatex` command not found. Please ensure LaTeX is installed and in your system's PATH.")
        debug_console.log("pdflatex command not found.", level='ERROR')
    except subprocess.TimeoutExpired:
        messagebox.showerror("Error", "LaTeX compilation timed out (exceeded 120 seconds).")
        debug_console.log("LaTeX compilation timed out.", level='ERROR')
    except Exception as e:
        messagebox.showerror("Compilation Error", f"An unexpected error occurred during compilation: {e}")
        debug_console.log(f"Unexpected error during LaTeX compilation: {e}", level='ERROR')
    finally:
        # Clean up the temporary .tex file if one was created.
        if temp_file_created and os.path.exists(tex_file_path):
             try:
                 os.remove(tex_file_path)
                 debug_console.log(f"Removed temporary compilation file: {tex_file_path}", level='DEBUG')
             except OSError as e:
                 debug_console.log(f"Error removing temporary compilation file '{tex_file_path}': {e}", level='ERROR')

def display_pdf(pdf_path):
    """
    Opens the generated PDF file using an external PDF viewer.

    It first attempts to use a bundled SumatraPDF viewer (on Windows). If not found
    or on other operating systems, it falls back to the system's default PDF viewer.

    Args:
        pdf_path (str): The absolute path to the PDF file to display.
    """
    if not pdf_path or not isinstance(pdf_path, str):
        messagebox.showerror("Error", "Invalid PDF path provided.")
        debug_console.log("Invalid PDF path provided for display.", level='ERROR')
        return
        
    if not os.path.exists(pdf_path):
        messagebox.showerror("Error", f"PDF file not found at:\n{pdf_path}")
        debug_console.log(f"PDF file not found for display: {pdf_path}", level='ERROR')
        return

    try:
        # Path to the bundled SumatraPDF viewer (Windows specific).
        sumatra_pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_reader", "SumatraPDF.exe")
        
        if platform.system() == "Windows" and os.path.exists(sumatra_pdf_path):
            try:
                # Use subprocess.Popen to open SumatraPDF without waiting for it to close.
                subprocess.Popen([sumatra_pdf_path, pdf_path])
                debug_console.log(f"Opened PDF with SumatraPDF: {pdf_path}", level='INFO')
            except Exception as e:
                messagebox.showerror("Error Opening PDF", f"Could not open PDF with SumatraPDF: {e}")
                debug_console.log(f"Error opening PDF with SumatraPDF: {e}", level='ERROR')
        else:
            # Fallback to system default viewer for other OS or if SumatraPDF is not found.
            debug_console.log("SumatraPDF not found, using system default viewer.", level='INFO')
            try:
                if platform.system() == "Windows":
                    os.startfile(pdf_path) # Windows default application.
                elif platform.system() == "Darwin":
                    subprocess.run(["open", pdf_path], check=True) # macOS default application.
                elif platform.system() == "Linux":
                    subprocess.run(["xdg-open", pdf_path], check=True) # Linux default application.
                else:
                    # Fallback for other systems
                    import webbrowser
                    webbrowser.open(f"file://{os.path.abspath(pdf_path)}")
                debug_console.log(f"Opened PDF with system default viewer: {pdf_path}", level='INFO')
            except Exception as e:
                 messagebox.showwarning("Warning", f"Could not open PDF with system default viewer:\n{e}")
                 debug_console.log(f"Error opening PDF with system default viewer: {e}", level='ERROR')
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error while opening PDF: {e}")
        debug_console.log(f"Unexpected error while opening PDF: {e}", level='ERROR')

def view_pdf_external(event=None, pdf_path=None):
    """
    Opens the PDF for the current .tex file in an external viewer,
    attempting to use fullscreen on a secondary monitor if available.
    
    Args:
        pdf_path (str, optional): Direct path to the PDF. If None, it's derived from the current tab.
    """
    debug_console.log("View PDF externally command initiated.", level='ACTION')
    
    try:
        if pdf_path is None:
            current_tab = get_current_tab()
            if not current_tab or not current_tab.file_path:
                messagebox.showwarning("Action Failed", "Please save your file first to locate the corresponding PDF.")
                debug_console.log("View PDF failed: No active file path.", level='WARNING')
                return

            source_directory = os.path.dirname(current_tab.file_path)
            file_name = os.path.basename(current_tab.file_path)
            pdf_path = os.path.join(source_directory, file_name.replace(".tex", ".pdf"))

        # Validate PDF path
        if not pdf_path or not isinstance(pdf_path, str):
            messagebox.showerror("Error", "Invalid PDF path.")
            debug_console.log("Invalid PDF path for viewing.", level='ERROR')
            return
            
        if not os.path.exists(pdf_path):
            messagebox.showerror("PDF Not Found", f"The PDF file was not found at:\n{pdf_path}\n\nPlease compile the document first.")
            debug_console.log(f"PDF file not found for viewing: {pdf_path}", level='ERROR')
            return

        # Try to open with SumatraPDF if available
        sumatra_pdf_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'pdf_reader', 'SumatraPDF.exe'))
        
        command = []
        if platform.system() == "Windows" and os.path.exists(sumatra_pdf_path):
            command.append(sumatra_pdf_path)
            command.append(pdf_path) # File path should come before options
            
            monitor_index = None
            if _pdf_monitor_setting != "Default":
                try:
                    # "Monitor 1: 1920x1080" -> index 1
                    monitor_index = int(_pdf_monitor_setting.split(':')[0].split(' ')[1])
                except (ValueError, IndexError):
                    debug_console.log(f"Could not parse monitor setting '{_pdf_monitor_setting}'.", level='WARNING')
            
            if monitor_index:
                command.append("-monitor")
                command.append(str(monitor_index))
            
            try:
                subprocess.Popen(command)
                debug_console.log(f"Opening PDF with SumatraPDF command: {' '.join(command)}", level='INFO')
            except Exception as e:
                messagebox.showerror("Error Opening PDF", f"Could not open PDF with SumatraPDF: {e}")
                debug_console.log(f"Error opening PDF with SumatraPDF: {e}", level='ERROR')
        else:
            # Fallback for non-Windows or if Sumatra is not found
            display_pdf(pdf_path)
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error while viewing PDF: {e}")
        debug_console.log(f"Unexpected error while viewing PDF: {e}", level='ERROR')
