import subprocess
import os
import platform
import webbrowser
import tkinter as tk
from tkinter import messagebox

# Import the interface module to get access to the current tab
import interface
import debug_console

root = None

def initialize_compiler(root_widget):
    """Sets the global reference to the root window."""
    global root
    root = root_widget
    debug_console.log("LaTeX Compiler initialized.", level='INFO')

def run_chktex_check():
    """Runs chktex on the current editor content."""
    debug_console.log("Running chktex check.", level='ACTION')
    current_tab = interface.get_current_tab()
    if not current_tab: return
    editor = current_tab.editor
    code = editor.get("1.0", tk.END)

    # Use the current file path or a temporary file
    if current_tab.file_path:
        tex_path = current_tab.file_path
        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            debug_console.log(f"Could not save content to {tex_path} for chktex: {e}", level='ERROR')
            messagebox.showerror("Error Saving File", f"Could not save current content to {tex_path} for chktex:\n{e}")
            return
    else:
        # Save to a temporary file in 'output' directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        tex_path = os.path.join(output_dir, "temp_chktex.tex")
        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(code)
            debug_console.log(f"Saved content to temporary file for chktex: {tex_path}", level='DEBUG')
        except Exception as e:
            debug_console.log(f"Could not save temporary file for chktex: {e}", level='ERROR')
            messagebox.showerror("Error Saving Temp File", f"Could not save temporary file for chktex:\n{e}")
            return

    try:
        command = ["chktex", "-q", "-l", "-v0-2", tex_path]
        debug_console.log(f"Executing command: {' '.join(command)}", level='INFO')
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=False 
        )

        output = result.stdout.strip()
        if not output:
            debug_console.log("chkTeX found no critical errors or warnings.", level='SUCCESS')
            messagebox.showinfo("✅ chkTeX", "No critical errors or warnings found.")
        else:
            debug_console.log(f"chkTeX found issues:\n{output}", level='WARNING')
            # Display errors in a new window
            error_window = tk.Toplevel(root)
            error_window.title("chkTeX - Critical Errors & Warnings")
            text_box = tk.Text(error_window, wrap="word", height=25, width=100)
            text_box.insert("1.0", output)
            text_box.config(state="disabled") # Make text box read-only
            text_box.pack(padx=10, pady=10)

    except FileNotFoundError:
        debug_console.log("chktex command not found in system PATH.", level='ERROR')
        messagebox.showerror("Error", "chktex command not found. Please ensure it is installed and in your system's PATH.")
    except Exception as e:
        debug_console.log(f"An unexpected error occurred during chktex execution: {e}", level='ERROR')
        messagebox.showerror("chkTeX Error", str(e))
    finally:
        # Clean up temporary file if one was used
        if not current_tab.file_path and os.path.exists(tex_path):
             try:
                 os.remove(tex_path)
                 debug_console.log(f"Removed temporary chktex file: {tex_path}", level='DEBUG')
             except OSError as e:
                 debug_console.log(f"Could not remove temporary chktex file {tex_path}: {e}", level='WARNING')

def compile_latex():
    """Compiles the current editor content using pdflatex."""
    debug_console.log("LaTeX compilation started.", level='ACTION')
    current_tab = interface.get_current_tab()
    if not current_tab: return
    editor = current_tab.editor
    code = editor.get("1.0", tk.END)
    current_file_path = current_tab.file_path

    source_dir = "output" # Default output directory
    file_name = "main.tex" # Default file name

    if current_file_path:
        source_dir = os.path.dirname(current_file_path)
        file_name = os.path.basename(current_file_path)
        try:
            with open(current_file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            debug_console.log(f"Could not save content to {current_file_path} for compilation: {e}", level='ERROR')
            messagebox.showerror("Error Saving File", f"Could not save current content to {current_file_path} for compilation:\n{e}")
            return
    else:
        # Save to a default file in 'output' directory if no file is open
        os.makedirs(source_dir, exist_ok=True)
        current_file_path = os.path.join(source_dir, file_name)
        try:
            with open(current_file_path, "w", encoding="utf-8") as f:
                f.write(code)
            debug_console.log(f"Saved content to temporary file for compilation: {current_file_path}", level='DEBUG')
        except Exception as e:
            debug_console.log(f"Could not save temporary file for compilation: {e}", level='ERROR')
            messagebox.showerror("Error Saving Temp File", f"Could not save temporary file for compilation:\n{e}")
            return

    pdf_path = os.path.join(source_dir, file_name.replace(".tex", ".pdf"))

    try:
        command = ["pdflatex", "-interaction=nonstopmode", file_name]
        debug_console.log(f"Executing command: {' '.join(command)} in CWD: {source_dir}", level='INFO')
        result = subprocess.run(
            command,
            cwd=source_dir, # Run command in the source directory
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30, 
            check=False
        )

        log_output = result.stdout.decode("utf-8", errors="ignore")

        if result.returncode == 0:
            debug_console.log("LaTeX compilation successful.", level='SUCCESS')
            messagebox.showinfo("✅ Success", "LaTeX compilation successful.")
            display_pdf(pdf_path)
        else:
            debug_console.log(f"LaTeX compilation failed. See full log.", level='ERROR')
            debug_console.log(log_output, level='DEBUG')
            messagebox.showerror("❌ LaTeX Error", "Compilation failed. See logs for details.")
            # Display log in a new window
            log_window = tk.Toplevel(root)
            log_window.title("Compilation Log")
            log_text = tk.Text(log_window, wrap="word", height=30, width=100)
            log_text.insert("1.0", log_output)
            log_text.config(state="disabled") # Make text box read-only
            log_text.pack(padx=10, pady=10)

    except FileNotFoundError:
        debug_console.log("pdflatex command not found in system PATH.", level='ERROR')
        messagebox.showerror("Error", "pdflatex command not found. Please ensure LaTeX is installed and in your system's PATH.")
    except subprocess.TimeoutExpired:
        debug_console.log("pdflatex compilation timed out after 30 seconds.", level='ERROR')
        messagebox.showerror("Error", "Compilation timed out.")
    except Exception as e:
        debug_console.log(f"An unexpected error occurred during pdflatex execution: {e}", level='ERROR')
        messagebox.showerror("Compilation Error", f"An unexpected error occurred: {e}")

def display_pdf(pdf_path):
    """Opens the generated PDF file using a specified reader."""
    if not os.path.exists(pdf_path):
        debug_console.log(f"PDF file not found at path: {pdf_path}", level='ERROR')
        messagebox.showerror("Error", f"PDF file not found:\n{pdf_path}")
        return

    pdf_reader_path = r"pdf_reader/SumatraPDF.exe"
    debug_console.log(f"Attempting to open PDF with SumatraPDF: {pdf_reader_path}", level='INFO')

    if not os.path.exists(pdf_reader_path):
        debug_console.log("SumatraPDF not found. Falling back to system default PDF viewer.", level='WARNING')
        messagebox.showwarning("PDF Reader Not Found", f"SumatraPDF.exe not found in 'pdf_reader' directory. Attempting to use system default viewer.")
        try:
            if platform.system() == "Windows":
                os.startfile(pdf_path)
            elif platform.system() == "Darwin": # macOS
                subprocess.call(["open", pdf_path])
            else: # Linux
                subprocess.call(["xdg-open", pdf_path])
        except Exception as e:
             debug_console.log(f"Could not open PDF with default viewer: {e}", level='ERROR')
             messagebox.showwarning("Warning", f"Could not open PDF with default viewer:\n{e}")
        return

    try:
        subprocess.Popen([pdf_reader_path, pdf_path])
        debug_console.log(f"Successfully launched SumatraPDF for {pdf_path}", level='SUCCESS')
    except Exception as e:
        debug_console.log(f"Failed to launch SumatraPDF: {e}", level='ERROR')
        messagebox.showerror("Error Opening PDF", str(e))