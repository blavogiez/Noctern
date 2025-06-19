import subprocess
import os
import platform
import webbrowser
import tkinter as tk
from tkinter import messagebox

# Access global variables defined in main.py or interface.py
editor = None
root = None
current_file_path = None

def set_compiler_globals(editor_widget, root_widget, file_path_var):
    """Sets the global references to the main widgets and file path."""
    global editor, root, current_file_path
    editor = editor_widget
    root = root_widget
    current_file_path = file_path_var # Note: file_path_var is the actual string path

def run_chktex_check():
    """Runs chktex on the current editor content."""
    if not editor or not root:
        return

    code = editor.get("1.0", tk.END)

    # Use the current file path or a temporary file
    if current_file_path:
        tex_path = current_file_path
        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
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
        except Exception as e:
            messagebox.showerror("Error Saving Temp File", f"Could not save temporary file for chktex:\n{e}")
            return

    try:
        # -q: quiet, -l: line numbers, -v0-2: verbosity levels 0 to 2 (errors and warnings)
        result = subprocess.run(
            ["chktex", "-q", "-l", "-v0-2", tex_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=False # Don't raise exception for non-zero exit code
        )

        output = result.stdout.strip()
        if not output:
            messagebox.showinfo("✅ chkTeX", "No critical errors or warnings found.")
        else:
            # Display errors in a new window
            error_window = tk.Toplevel(root)
            error_window.title("chkTeX - Critical Errors & Warnings")
            text_box = tk.Text(error_window, wrap="word", height=25, width=100)
            text_box.insert("1.0", output)
            text_box.config(state="disabled") # Make text box read-only
            text_box.pack(padx=10, pady=10)

    except FileNotFoundError:
        messagebox.showerror("Error", "chktex command not found. Please ensure it is installed and in your system's PATH.")
    except Exception as e:
        messagebox.showerror("chkTeX Error", str(e))
    finally:
        # Clean up temporary file if one was used
        if not current_file_path and os.path.exists(tex_path):
             try:
                 os.remove(tex_path)
             except OSError as e:
                 print(f"Warning: Could not remove temporary chktex file {tex_path}: {e}")

def compile_latex():
    """Compiles the current editor content using pdflatex."""
    global current_file_path # Access the global variable

    if not editor or not root:
        return

    code = editor.get("1.0", tk.END)

    source_dir = "output" # Default output directory
    file_name = "main.tex" # Default file name

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
        # Save to a default file in 'output' directory if no file is open
        os.makedirs(source_dir, exist_ok=True)
        current_file_path = os.path.join(source_dir, file_name)
        try:
            with open(current_file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            messagebox.showerror("Error Saving Temp File", f"Could not save temporary file for compilation:\n{e}")
            # Reset current_file_path as saving failed
            current_file_path = None
            return

    pdf_path = os.path.join(source_dir, file_name.replace(".tex", ".pdf"))

    try:
        # Run pdflatex command
        # -interaction=nonstopmode: don't stop for errors, just log them
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", file_name],
            cwd=source_dir, # Run command in the source directory
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30, # Increased timeout for larger documents
            check=False # Don't raise exception for non-zero exit code
        )

        log_output = result.stdout.decode("utf-8", errors="ignore")

        if result.returncode == 0:
            messagebox.showinfo("✅ Success", "LaTeX compilation successful.")
            display_pdf(pdf_path)
        else:
            messagebox.showerror("❌ LaTeX Error", "Compilation failed. See logs for details.")
            # Display log in a new window
            log_window = tk.Toplevel(root)
            log_window.title("Compilation Log")
            log_text = tk.Text(log_window, wrap="word", height=30, width=100)
            log_text.insert("1.0", log_output)
            log_text.config(state="disabled") # Make text box read-only
            log_text.pack(padx=10, pady=10)

    except FileNotFoundError:
        messagebox.showerror("Error", "pdflatex command not found. Please ensure LaTeX is installed and in your system's PATH.")
    except subprocess.TimeoutExpired:
        messagebox.showerror("Error", "Compilation timed out.")
    except Exception as e:
        messagebox.showerror("Compilation Error", f"An unexpected error occurred: {e}")

def display_pdf(pdf_path):
    """Opens the generated PDF file using a specified reader."""
    if not os.path.exists(pdf_path):
        messagebox.showerror("Error", f"PDF file not found:\n{pdf_path}")
        return

    # Path to the SumatraPDF reader (adjust if needed)
    pdf_reader_path = r"pdf_reader/SumatraPDF.exe"

    if not os.path.exists(pdf_reader_path):
        messagebox.showerror("Error", f"PDF reader not found:\n{pdf_reader_path}\nPlease ensure SumatraPDF.exe is in the 'pdf_reader' directory.")
        # Fallback to default system PDF viewer
        try:
            if platform.system() == "Windows":
                os.startfile(pdf_path)
            elif platform.system() == "Darwin": # macOS
                subprocess.call(["open", pdf_path])
            else: # Linux
                subprocess.call(["xdg-open", pdf_path])
        except Exception as e:
             messagebox.showwarning("Warning", f"Could not open PDF with default viewer:\n{e}")
        return

    try:
        # Use subprocess.Popen to open the PDF reader without waiting for it to close
        subprocess.Popen([pdf_reader_path, pdf_path])
    except Exception as e:
        messagebox.showerror("Error Opening PDF", str(e))