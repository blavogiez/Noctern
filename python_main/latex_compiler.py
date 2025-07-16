
"""
This module provides functionalities for compiling LaTeX documents, running static analysis
with `chktex`, cleaning auxiliary files, and displaying the generated PDF.
It integrates with external command-line tools like `pdflatex` and `chktex`.
"""

import subprocess
import os
import platform
import webbrowser
import tkinter as tk
from tkinter import messagebox
import interface
import debug_console

# Global reference to the root Tkinter window, initialized during application setup.
root = None

def initialize_compiler(root_widget):
    """
    Initializes the LaTeX compiler module by setting the root Tkinter window.

    This is necessary for displaying message boxes and other UI elements.

    Args:
        root_widget (tk.Tk): The main Tkinter application window.
    """
    global root
    root = root_widget
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
    current_tab = interface.get_current_tab()
    if not current_tab or not current_tab.file_path:
        messagebox.showwarning("Action Failed", "Please save your current file first to define a project directory for cleaning.")
        debug_console.log("Clean project failed: No active file path available.", level='WARNING')
        return

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

def run_chktex_check(event=None):
    """
    Runs the `chktex` static analysis tool on the current LaTeX document.

    The content of the active editor tab is saved to a temporary file (or its original path
    if it's a saved file), and `chktex` is executed against it. Any critical errors or
    warnings reported by `chktex` are displayed in a new Tkinter window.

    Args:
        event (tk.Event, optional): The Tkinter event object, if called from a binding. Defaults to None.
    """
    debug_console.log("Initiating chktex static analysis check.", level='ACTION')
    current_tab = interface.get_current_tab()
    if not current_tab:
        debug_console.log("chktex check aborted: No active editor tab.", level='WARNING')
        return
    
    editor_content = current_tab.editor.get("1.0", tk.END)
    temp_file_created = False

    if current_tab.file_path:
        # If the file is already saved, use its path.
        tex_file_path = current_tab.file_path
        try:
            # Save current editor content to the file before running chktex.
            with open(tex_file_path, "w", encoding="utf-8") as f:
                f.write(editor_content)
            debug_console.log(f"Saved current content to '{tex_file_path}' for chktex.", level='DEBUG')
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Could not save current content to {tex_file_path} for chktex:\n{e}")
            debug_console.log(f"Error saving file for chktex: {e}", level='ERROR')
            return
    else:
        # For unsaved files, create a temporary .tex file in the 'output' directory.
        output_directory = "output"
        os.makedirs(output_directory, exist_ok=True)
        tex_file_path = os.path.join(output_directory, "temp_chktex.tex")
        try:
            with open(tex_file_path, "w", encoding="utf-8") as f:
                f.write(editor_content)
            temp_file_created = True
            debug_console.log(f"Created temporary file '{tex_file_path}' for chktex.", level='DEBUG')
        except Exception as e:
            messagebox.showerror("Error Saving Temp File", f"Could not save temporary file for chktex:\n{e}")
            debug_console.log(f"Error saving temporary file for chktex: {e}", level='ERROR')
            return

    try:
        # Execute the chktex command.
        # -q: quiet, -l: list errors, -v0-2: verbosity level for critical errors and warnings.
        command = ["chktex", "-q", "-l", "-v0-2", tex_file_path]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", check=False)
        chktex_output = result.stdout.strip()
        
        if not chktex_output:
            messagebox.showinfo("✅ chkTeX", "No critical errors or warnings found by chkTeX.")
            debug_console.log("chktex check completed: No issues found.", level='SUCCESS')
        else:
            # Display chktex output in a new window.
            error_window = tk.Toplevel(root)
            error_window.title("chkTeX - Critical Errors & Warnings")
            text_box = tk.Text(error_window, wrap="word", height=25, width=100)
            text_box.insert("1.0", chktex_output)
            text_box.config(state="disabled") # Make the text box read-only.
            text_box.pack(padx=10, pady=10)
            debug_console.log("chktex check completed with issues. Displaying results.", level='WARNING')
    except FileNotFoundError:
        messagebox.showerror("Error", "`chktex` command not found. Please ensure it is installed and in your system's PATH.")
        debug_console.log("chktex command not found.", level='ERROR')
    except Exception as e:
        messagebox.showerror("chkTeX Error", f"An unexpected error occurred during chkTeX execution: {e}")
        debug_console.log(f"Unexpected error during chktex execution: {e}", level='ERROR')
    finally:
        # Clean up the temporary file if one was created.
        if temp_file_created and os.path.exists(tex_file_path):
             try:
                 os.remove(tex_file_path)
                 debug_console.log(f"Removed temporary chktex file: {tex_file_path}", level='DEBUG')
             except OSError as e:
                 debug_console.log(f"Error removing temporary chktex file '{tex_file_path}': {e}", level='ERROR')

def compile_latex(event=None):
    """
    Compiles the current LaTeX document into a PDF using `pdflatex`.

    The content of the active editor tab is saved to a .tex file (either its original path
    or a temporary file), and `pdflatex` is executed. Upon successful compilation, the
    generated PDF is displayed. Compilation errors are shown in a log window.

    Args:
        event (tk.Event, optional): The Tkinter event object, if called from a binding. Defaults to None.
    """
    debug_console.log("LaTeX compilation process started.", level='ACTION')
    current_tab = interface.get_current_tab()
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

    # Construct the path to the expected PDF output.
    pdf_output_path = os.path.join(source_directory, file_name.replace(".tex", ".pdf"))

    try:
        # Execute pdflatex command.
        # -interaction=nonstopmode: prevents pdflatex from pausing for user input.
        command = ["pdflatex", "-interaction=nonstopmode", file_name]
        debug_console.log(f"Executing pdflatex command: {' '.join(command)} in directory: {source_directory}", level='DEBUG')
        result = subprocess.run(command, cwd=source_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, check=False)
        compilation_log_output = result.stdout.decode("utf-8", errors="ignore")

        if result.returncode == 0:
            messagebox.showinfo("✅ Compilation Successful", "LaTeX document compiled successfully to PDF.")
            debug_console.log("LaTeX compilation successful.", level='SUCCESS')
            display_pdf(pdf_output_path) # Display the generated PDF.
        else:
            messagebox.showerror("❌ LaTeX Compilation Failed", "Compilation failed. Please check the log for details.")
            debug_console.log("LaTeX compilation failed. Displaying log.", level='ERROR')
            # Display compilation log in a new window.
            log_window = tk.Toplevel(root)
            log_window.title("LaTeX Compilation Log")
            log_text_box = tk.Text(log_window, wrap="word", height=30, width=100)
            log_text_box.insert("1.0", compilation_log_output)
            log_text_box.config(state="disabled") # Make read-only.
            log_text_box.pack(padx=10, pady=10)
    except FileNotFoundError:
        messagebox.showerror("Error", "`pdflatex` command not found. Please ensure LaTeX is installed and in your system's PATH.")
        debug_console.log("pdflatex command not found.", level='ERROR')
    except subprocess.TimeoutExpired:
        messagebox.showerror("Error", "LaTeX compilation timed out (exceeded 60 seconds).")
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
    if not os.path.exists(pdf_path):
        messagebox.showerror("Error", f"PDF file not found at:\n{pdf_path}")
        debug_console.log(f"PDF file not found for display: {pdf_path}", level='ERROR')
        return

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
        messagebox.showwarning("PDF Reader Not Found", "SumatraPDF.exe not found or not on Windows. Attempting to use system default PDF viewer.")
        try:
            if platform.system() == "Windows":
                os.startfile(pdf_path) # Windows default application.
            elif platform.system() == "Darwin":
                subprocess.run(["open", pdf_path], check=True) # macOS default application.
            else:
                subprocess.run(["xdg-open", pdf_path], check=True) # Linux default application.
            debug_console.log(f"Opened PDF with system default viewer: {pdf_path}", level='INFO')
        except Exception as e:
             messagebox.showwarning("Warning", f"Could not open PDF with system default viewer:\n{e}")
             debug_console.log(f"Error opening PDF with system default viewer: {e}", level='ERROR')
