# latex_compiler.py

import subprocess
import os
import platform
import webbrowser
import tkinter as tk
from tkinter import messagebox
import interface
import debug_console

root = None

def initialize_compiler(root_widget):
    global root
    root = root_widget
    debug_console.log("LaTeX Compiler initialized.", level='INFO')

# FIXED: Added event=None to match the new unified shortcut system.
def clean_project_directory(event=None):
    debug_console.log("Clean Project Directory command initiated.", level='ACTION')
    current_tab = interface.get_current_tab()
    if not current_tab or not current_tab.file_path:
        messagebox.showwarning("Action Failed", "Please save your file first to define a project directory.")
        debug_console.log("Clean project failed: no file path available.", level='WARNING')
        return

    project_dir = os.path.dirname(current_tab.file_path)
    
    extensions_to_delete = [
        '.aux', '.log', '.toc', '.bbl', '.bcf', '.blg', '.lof', '.lot', 
        '.out', '.run.xml', '.synctex.gz', '.fls', '.fdb_latexmk'
    ]
    
    files_deleted_count = 0
    for filename in os.listdir(project_dir):
        if any(filename.endswith(ext) for ext in extensions_to_delete):
            file_path = os.path.join(project_dir, filename)
            try:
                os.remove(file_path)
                files_deleted_count += 1
                debug_console.log(f"Deleted auxiliary file: {file_path}", level='DEBUG')
            except OSError as e:
                debug_console.log(f"Could not delete file '{file_path}': {e}", level='ERROR')

    if files_deleted_count > 0:
        debug_console.log(f"Successfully cleaned {files_deleted_count} files.", level='SUCCESS')
        messagebox.showinfo(
            "Project Cleaned",
            f"Successfully deleted {files_deleted_count} auxiliary file(s) from:\n\n{project_dir}"
        )
    else:
        debug_console.log("No auxiliary files found to clean.", level='INFO')
        messagebox.showinfo("Project Clean", "No auxiliary files found to clean.")

# FIXED: Added event=None to match the new unified shortcut system.
def run_chktex_check(event=None):
    debug_console.log("Running chktex check.", level='ACTION')
    current_tab = interface.get_current_tab()
    if not current_tab: return
    # ... le reste de la fonction est inchangé ...
    editor = current_tab.editor
    code = editor.get("1.0", tk.END)

    if current_tab.file_path:
        tex_path = current_tab.file_path
        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Could not save current content to {tex_path} for chktex:\n{e}")
            return
    else:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        tex_path = os.path.join(output_dir, "temp_chktex.tex")
        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            messagebox.showerror("Error Saving Temp File", f"Could not save temporary file for chktex:\n{e}")
            return

    try:
        command = ["chktex", "-q", "-l", "-v0-2", tex_path]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", check=False)
        output = result.stdout.strip()
        if not output:
            messagebox.showinfo("✅ chkTeX", "No critical errors or warnings found.")
        else:
            error_window = tk.Toplevel(root)
            error_window.title("chkTeX - Critical Errors & Warnings")
            text_box = tk.Text(error_window, wrap="word", height=25, width=100)
            text_box.insert("1.0", output)
            text_box.config(state="disabled")
            text_box.pack(padx=10, pady=10)
    except FileNotFoundError:
        messagebox.showerror("Error", "chktex command not found. Please ensure it is installed and in your system's PATH.")
    except Exception as e:
        messagebox.showerror("chkTeX Error", str(e))
    finally:
        if not current_tab.file_path and os.path.exists(tex_path):
             try:
                 os.remove(tex_path)
             except OSError:
                 pass

# FIXED: Added event=None to match the new unified shortcut system.
def compile_latex(event=None):
    debug_console.log("LaTeX compilation started.", level='ACTION')
    current_tab = interface.get_current_tab()
    if not current_tab: return
    # ... le reste de la fonction est inchangé ...
    editor = current_tab.editor
    code = editor.get("1.0", tk.END)
    current_file_path = current_tab.file_path

    source_dir = "output"
    file_name = "main.tex"

    if current_file_path:
        source_dir = os.path.dirname(current_file_path)
        file_name = os.path.basename(current_file_path)
        try:
            with open(current_file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Could not save current content to {current_file_path} for compilation:\n{e}")
            return
    else:
        os.makedirs(source_dir, exist_ok=True)
        current_file_path = os.path.join(source_dir, file_name)
        try:
            with open(current_file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            messagebox.showerror("Error Saving Temp File", f"Could not save temporary file for compilation:\n{e}")
            return

    pdf_path = os.path.join(source_dir, file_name.replace(".tex", ".pdf"))

    try:
        command = ["pdflatex", "-interaction=nonstopmode", file_name]
        result = subprocess.run(command, cwd=source_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
        log_output = result.stdout.decode("utf-8", errors="ignore")

        if result.returncode == 0:
            messagebox.showinfo("✅ Success", "LaTeX compilation successful.")
            display_pdf(pdf_path)
        else:
            messagebox.showerror("❌ LaTeX Error", "Compilation failed. See logs for details.")
            log_window = tk.Toplevel(root)
            log_window.title("Compilation Log")
            log_text = tk.Text(log_window, wrap="word", height=30, width=100)
            log_text.insert("1.0", log_output)
            log_text.config(state="disabled")
            log_text.pack(padx=10, pady=10)
    except FileNotFoundError:
        messagebox.showerror("Error", "pdflatex command not found. Please ensure LaTeX is installed and in your system's PATH.")
    except subprocess.TimeoutExpired:
        messagebox.showerror("Error", "Compilation timed out.")
    except Exception as e:
        messagebox.showerror("Compilation Error", f"An unexpected error occurred: {e}")

def display_pdf(pdf_path):
    # ... cette fonction n'est pas appelée par un raccourci, donc pas de changement ...
    if not os.path.exists(pdf_path):
        messagebox.showerror("Error", f"PDF file not found:\n{pdf_path}")
        return

    pdf_reader_path = r"pdf_reader/SumatraPDF.exe"
    if not os.path.exists(pdf_reader_path):
        messagebox.showwarning("PDF Reader Not Found", "SumatraPDF.exe not found. Attempting to use system default viewer.")
        try:
            if platform.system() == "Windows": os.startfile(pdf_path)
            elif platform.system() == "Darwin": subprocess.run(["open", pdf_path], check=True)
            else: subprocess.run(["xdg-open", pdf_path], check=True)
        except Exception as e:
             messagebox.showwarning("Warning", f"Could not open PDF with default viewer:\n{e}")
        return

    try:
        subprocess.Popen([pdf_reader_path, pdf_path])
    except Exception as e:
        messagebox.showerror("Error Opening PDF", str(e))