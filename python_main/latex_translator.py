# c:\Users\lab\Documents\BUT1\AutomaTeX\alpha_tkinter\latex_translator.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading

try:
    import argostranslate.package
    import argostranslate.translate
    _ARGOS_TRANSLATE_AVAILABLE = True
except ImportError:
    _ARGOS_TRANSLATE_AVAILABLE = False
    print("Warning: argostranslate module not found. Translation functionality will be disabled.")

# Global variables to store references from the main application
_root = None
_theme_setting_getter_func = None
_show_temporary_status_message_func = None
_active_editor_getter_func = None
_active_filepath_getter_func = None

def initialize_translator(root_ref, theme_getter, status_message_func, active_editor_getter, active_filepath_getter):
    """
    Initializes the LaTeX translator service with necessary references from the main application.
    """
    global _root, _theme_setting_getter_func, _show_temporary_status_message_func
    global _active_editor_getter_func, _active_filepath_getter_func
    _root = root_ref
    _theme_setting_getter_func = theme_getter
    _show_temporary_status_message_func = status_message_func
    _active_editor_getter_func = active_editor_getter
    _active_filepath_getter_func = active_filepath_getter

def _get_available_translation_pairs():
    """
    Gets available translation pairs (source -> target) from argostranslate.
    Returns a list of tuples: (from_lang_code, to_lang_code, display_name).
    """
    if not _ARGOS_TRANSLATE_AVAILABLE:
        return []
    try:
        available_packages = argostranslate.package.get_available_packages()
        translation_pairs = []
        for p in available_packages:
            if p.from_code and p.to_code:
                # Check if the package is installed
                is_installed = any(
                    installed_p.from_code == p.from_code and installed_p.to_code == p.to_code
                    for installed_p in argostranslate.package.get_installed_packages()
                )
                status = " (Installed)" if is_installed else " (Not Installed)"
                translation_pairs.append((p.from_code, p.to_code, f"{p.from_name} -> {p.to_name}{status}"))
        return translation_pairs
    except Exception as e:
        print(f"Error getting Argos Translate packages: {e}")
        return []

def _install_language_package_threaded(from_code, to_code, dialog_window, callback):
    """
    Installs a language package in a separate thread.
    """
    if not _ARGOS_TRANSLATE_AVAILABLE:
        _root.after(0, lambda: messagebox.showerror("Installation Error", "Argos Translate module is not available.", parent=dialog_window))
        return

    def run_install():
        try:
            _root.after(0, lambda: _show_temporary_status_message_func(f"⏳ Installing {from_code} to {to_code} language package... This may take a while."))
            argostranslate.package.install_from_path(
                argostranslate.package.get_package_path(from_code, to_code)
            )
            _root.after(0, lambda: _show_temporary_status_message_func(f"✅ Language package {from_code} to {to_code} installed."))
            _root.after(0, callback) # Call back to refresh dialog or proceed
        except Exception as e:
            _root.after(0, lambda: messagebox.showerror("Installation Error", f"Failed to install language package: {e}", parent=dialog_window))
            _root.after(0, lambda: _show_temporary_status_message_func(f"❌ Installation failed for {from_code} to {to_code}."))

    threading.Thread(target=run_install, daemon=True).start()

def _perform_translation_threaded(source_text, from_code, to_code, original_filepath, dialog_window):
    """
    Performs the actual translation in a separate thread and saves the result.
    """
    if not _ARGOS_TRANSLATE_AVAILABLE:
        _root.after(0, lambda: messagebox.showerror("Translation Error", "Argos Translate module is not available.", parent=dialog_window))
        _root.after(0, dialog_window.destroy)
        return

    def run_translation():
        try:
            _root.after(0, lambda: _show_temporary_status_message_func(f"⏳ Translating from {from_code} to {to_code}..."))
            translated_text = argostranslate.translate.translate(source_text, from_code, to_code)

            if original_filepath:
                base_name, ext = os.path.splitext(os.path.basename(original_filepath))
                translated_filename = f"{to_code}_{base_name}{ext}"
                translated_filepath = os.path.join(os.path.dirname(original_filepath), translated_filename)
            else:
                # If no file is open, save to a default temp location
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                translated_filename = f"{to_code}_temp_document.tex"
                translated_filepath = os.path.join(output_dir, translated_filename)

            with open(translated_filepath, "w", encoding="utf-8") as f:
                f.write(translated_text)

            _root.after(0, lambda: _show_temporary_status_message_func(f"✅ Document translated and saved to {os.path.basename(translated_filepath)}"))
            _root.after(0, lambda: messagebox.showinfo("Translation Success", f"Document translated and saved to:\n{translated_filepath}", parent=dialog_window))
        except Exception as e:
            _root.after(0, lambda: messagebox.showerror("Translation Error", f"An error occurred during translation: {e}", parent=dialog_window))
            _root.after(0, lambda: _show_temporary_status_message_func(f"❌ Translation failed: {e}"))
        finally:
            _root.after(0, dialog_window.destroy) # Close dialog after translation attempt

    threading.Thread(target=run_translation, daemon=True).start()

def open_translate_dialog():
    """
    Opens a dialog for the user to select source and target languages for translation.
    """
    editor = _active_editor_getter_func()
    if not editor or not _root or not _theme_setting_getter_func or not _show_temporary_status_message_func:
        messagebox.showerror("Translator Error", "Translator service not fully initialized.")
        return

    if not _ARGOS_TRANSLATE_AVAILABLE:
        messagebox.showerror("Argos Translate Error", "The 'argostranslate' Python module is not installed. Please install it using 'pip install argostranslate' to enable translation features.")
        return
    
    source_text = editor.get("1.0", tk.END)
    if not source_text.strip():
        messagebox.showwarning("Translation", "The editor is empty. Nothing to translate.")
        return

    dialog = tk.Toplevel(_root)
    dialog.title("Translate Document")
    dialog.transient(_root)
    dialog.grab_set()
    dialog.geometry("450x300")

    # Theming
    dialog_bg = _theme_setting_getter_func("root_bg", "#f0f0f0")
    dialog_fg = _theme_setting_getter_func("fg_color", "#000000")
    dialog.configure(bg=dialog_bg)

    main_frame = ttk.Frame(dialog, padding=15)
    main_frame.pack(fill="both", expand=True)

    # Language selection
    ttk.Label(main_frame, text="Select Translation Pair:").pack(pady=(0, 5), anchor="w")

    # Combobox for translation pairs
    translation_pairs_data = _get_available_translation_pairs()
    display_options = [item[2] for item in translation_pairs_data]
    if not display_options:
        messagebox.showerror("Argos Translate Error", "No translation packages found. Please download language packages using 'argos-translate --gui' or ensure internet connection.", parent=dialog)
        dialog.destroy()
        return

    selected_pair_var = tk.StringVar(dialog)
    lang_combobox = ttk.Combobox(main_frame, textvariable=selected_pair_var, values=display_options, state="readonly")
    lang_combobox.pack(fill="x", pady=(0, 10))
    if display_options:
        lang_combobox.set(display_options[0]) # Set default selection

    def on_translate_button_click():
        selected_display_text = selected_pair_var.get()
        if not selected_display_text:
            messagebox.showwarning("Selection Error", "Please select a translation pair.", parent=dialog)
            return

        # Find the corresponding codes
        selected_pair = next((item for item in translation_pairs_data if item[2] == selected_display_text), None)
        if not selected_pair:
            messagebox.showerror("Error", "Invalid selection.", parent=dialog)
            return

        from_code, to_code, _ = selected_pair

        # Check if package is installed
        is_installed = any(
            p.from_code == from_code and p.to_code == to_code
            for p in argostranslate.package.get_installed_packages()
        )

        if not is_installed:
            response = messagebox.askyesno(
                "Install Language Package",
                f"The language package for {from_code} to {to_code} is not installed. Do you want to install it now? This may take some time.",
                parent=dialog
            )
            if response:
                # Install in a thread, then proceed with translation after installation
                _install_language_package_threaded(from_code, to_code, dialog,
                                                   lambda: _perform_translation_threaded(
                                                       source_text, from_code, to_code,
                                                       _active_filepath_getter_func(), dialog
                                                   ))
            else:
                dialog.destroy()
            return

        # If installed, proceed directly to translation
        _perform_translation_threaded(source_text, from_code, to_code, _active_filepath_getter_func(), dialog)

    translate_button = ttk.Button(main_frame, text="Translate", command=on_translate_button_click)
    translate_button.pack(pady=10)

    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.wait_window()