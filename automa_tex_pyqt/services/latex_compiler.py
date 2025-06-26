# File: latex_compiler.py
import subprocess
import os
import platform
import webbrowser
from PyQt6 import QtWidgets, QtCore, QtGui

root = None
get_current_tab_func = None # Callback to get the current tab

def initialize_compiler(root_widget, get_current_tab_callback):
    """Sets the global reference to the root window."""
    global root
    global get_current_tab_func
    root = root_widget
    get_current_tab_func = get_current_tab_callback

    # Connect buttons and actions
    root.btn_compile.clicked.connect(compile_latex)
    root.btn_check.clicked.connect(run_chktex_check)
    root.action_check.triggered.connect(run_chktex_check)

def run_chktex_check():
    """Runs chktex on the current editor content."""
    current_tab = get_current_tab_func()
    if not current_tab: return
    editor = current_tab.editor
    code = editor.toPlainText()

    if not code.strip():
        QtWidgets.QMessageBox.information(root, "chkTeX", "Editor is empty. Nothing to check.")
        return

    # Use the current file path or a temporary file
    tex_path = None
    if current_tab.file_path:
        tex_path = current_tab.file_path
        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            QtWidgets.QMessageBox.critical(root, "Error Saving File", f"Could not save current content to {tex_path} for chktex:\n{e}")
            return
    else:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        tex_path = os.path.join(output_dir, "temp_chktex.tex")
        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            QtWidgets.QMessageBox.critical(root, "Error Saving Temp File", f"Could not save temporary file for chktex:\n{e}")
            return

    try:
        result = subprocess.run(
            ["chktex", "-q", "-l", "-v0-2", tex_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=False
        )

        output = result.stdout.strip()
        if not output:
            QtWidgets.QMessageBox.information(root, "✅ chkTeX", "No critical errors or warnings found.")
        else:
            msg_box = QtWidgets.QMessageBox(root)
            msg_box.setWindowTitle("chkTeX - Critical Errors & Warnings")
            msg_box.setText("chkTeX found issues:")
            msg_box.setInformativeText("See details below.")
            msg_box.setDetailedText(output)
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg_box.exec()

    except FileNotFoundError:
        QtWidgets.QMessageBox.critical(root, "Error", "chktex command not found. Please ensure it is installed and in your system's PATH.")
    except Exception as e:
        QtWidgets.QMessageBox.critical(root, "chkTeX Error", str(e))
    finally:
        if not current_tab.file_path and tex_path and os.path.exists(tex_path):
             try:
                 os.remove(tex_path)
             except OSError as e:
                 print(f"Warning: Could not remove temporary chktex file {tex_path}: {e}")

def compile_latex():
    """Compiles the current editor content using pdflatex."""
    current_tab = get_current_tab_func()
    if not current_tab: return
    editor = current_tab.editor
    code = editor.toPlainText()
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
            QtWidgets.QMessageBox.critical(root, "Error Saving File", f"Could not save current content to {current_file_path} for compilation:\n{e}")
            return
    else:
        os.makedirs(source_dir, exist_ok=True)
        current_file_path = os.path.join(source_dir, file_name)
        try:
            with open(current_file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            QtWidgets.QMessageBox.critical(root, "Error Saving Temp File", f"Could not save temporary file for compilation:\n{e}")
            current_file_path = None
            return

    pdf_path = os.path.join(source_dir, file_name.replace(".tex", ".pdf"))

    try:
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", file_name],
            cwd=source_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False
        )

        log_output = result.stdout if isinstance(result.stdout, str) else result.stdout.decode("utf-8", errors="ignore")

        if result.returncode == 0:
            QtWidgets.QMessageBox.information(root, "✅ Success", "LaTeX compilation successful.")
            display_pdf(pdf_path)
        else:
            msg_box = QtWidgets.QMessageBox(root)
            msg_box.setWindowTitle("❌ LaTeX Error")
            msg_box.setText("Compilation failed. See logs for details.")
            msg_box.setDetailedText(log_output)
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            msg_box.exec()

    except FileNotFoundError:
        QtWidgets.QMessageBox.critical(root, "Error", "pdflatex command not found. Please ensure LaTeX is installed and in your system's PATH.")
    except subprocess.TimeoutExpired:
        QtWidgets.QMessageBox.critical(root, "Error", "Compilation timed out.")
    except Exception as e:
        QtWidgets.QMessageBox.critical(root, "Compilation Error", f"An unexpected error occurred: {e}")

def display_pdf(pdf_path):
    """Opens the generated PDF file using a specified reader."""
    if not os.path.exists(pdf_path):
        QtWidgets.QMessageBox.critical(root, "Error", f"PDF file not found:\n{pdf_path}")
        return

    pdf_reader_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pdf_reader", "SumatraPDF.exe")

    if not os.path.exists(pdf_reader_path):
        QtWidgets.QMessageBox.warning(root, "Error", f"PDF reader not found:\n{pdf_reader_path}\nPlease ensure SumatraPDF.exe is in the 'pdf_reader' directory.")
        try:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(pdf_path))
        except Exception as e:
             QtWidgets.QMessageBox.warning(root, "Warning", f"Could not open PDF with default viewer:\n{e}")
        return

    try:
        subprocess.Popen([pdf_reader_path, pdf_path])
    except Exception as e:
        QtWidgets.QMessageBox.critical(root, "Error Opening PDF", str(e))
