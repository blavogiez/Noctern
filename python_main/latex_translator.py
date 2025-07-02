
"""
This module provides functionality for translating LaTeX document content using the `argostranslate` library.
It includes features for selecting translation pairs, installing missing language packages,
and performing translations in a separate thread to keep the UI responsive.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import debug_console

try:
    import argostranslate.package
    import argostranslate.translate
    _ARGOS_TRANSLATE_AVAILABLE = True
except ImportError:
    _ARGOS_TRANSLATE_AVAILABLE = False
    debug_console.log("The 'argostranslate' module was not found. Translation functionality will be disabled.", level='WARNING')


# Global variables to store references to main application components.
# These are initialized via the `initialize_translator` function.
_root = None  # Reference to the main Tkinter root window.
_theme_setting_getter_func = None  # Function to get theme settings.
_show_temporary_status_message_func = None  # Function to display temporary status messages.
_active_editor_getter_func = None  # Function to get the current active editor widget.
_active_filepath_getter_func = None  # Function to get the file path of the active editor.

def initialize_translator(root_ref, theme_getter, status_message_func, active_editor_getter, active_filepath_getter):
    """
    Initializes the LaTeX translator service with necessary references from the main application.

    This function must be called once during application startup to set up the dependencies
    required for the translation dialog and operations.

    Args:
        root_ref (tk.Tk): The main Tkinter root window.
        theme_getter (callable): A function to retrieve theme settings.
        status_message_func (callable): A function to display temporary status messages.
        active_editor_getter (callable): A function to get the currently active editor widget.
        active_filepath_getter (callable): A function to get the file path of the active editor.
    """
    global _root, _theme_setting_getter_func, _show_temporary_status_message_func
    global _active_editor_getter_func, _active_filepath_getter_func
    
    _root = root_ref
    _theme_setting_getter_func = theme_getter
    _show_temporary_status_message_func = status_message_func
    _active_editor_getter_func = active_editor_getter
    _active_filepath_getter_func = active_filepath_getter
    debug_console.log("Translator service successfully initialized.", level='INFO')

def _get_available_translation_pairs():
    """
    Retrieves a list of available translation language pairs from `argostranslate`.

    Each pair includes the source language code, target language code, and a display name
    indicating whether the corresponding language package is installed.

    Returns:
        list: A list of tuples, where each tuple contains (from_lang_code, to_lang_code, display_name).
              Returns an empty list if `argostranslate` is not available or an error occurs.
    """
    if not _ARGOS_TRANSLATE_AVAILABLE:
        debug_console.log("Argos Translate is not available. Cannot fetch translation packages.", level='WARNING')
        return []
    try:
        debug_console.log("Fetching available Argos Translate language packages.", level='DEBUG')
        # Get all available packages (installed or not).
        available_packages = argostranslate.package.get_available_packages()
        # Get currently installed packages for status checking.
        installed_packages = argostranslate.package.get_installed_packages()
        
        translation_pairs = []
        for package in available_packages:
            if package.from_code and package.to_code:
                # Check if the current package is installed.
                is_installed = any(
                    installed_pkg.from_code == package.from_code and installed_pkg.to_code == package.to_code
                    for installed_pkg in installed_packages
                )
                status_indicator = " (Installed)" if is_installed else " (Not Installed)"
                display_name = f"{package.from_name} -> {package.to_name}{status_indicator}"
                translation_pairs.append((package.from_code, package.to_code, display_name))
        debug_console.log(f"Found {len(translation_pairs)} available translation pairs.", level='DEBUG')
        return translation_pairs
    except Exception as e:
        debug_console.log(f"Error retrieving Argos Translate packages: {e}", level='ERROR')
        return []

def _install_language_package_threaded(from_code, to_code, dialog_window, callback_on_completion):
    """
    Installs a language package for `argostranslate` in a separate thread.

    This prevents the UI from freezing during the potentially long installation process.
    Upon completion (success or failure), it calls a provided callback function.

    Args:
        from_code (str): The language code of the source language.
        to_code (str): The language code of the target language.
        dialog_window (tk.Toplevel): The parent dialog window for displaying error messages.
        callback_on_completion (callable): A function to call after the installation attempt completes.
    """
    if not _ARGOS_TRANSLATE_AVAILABLE:
        _root.after(0, lambda: messagebox.showerror("Installation Error", "Argos Translate module is not available.", parent=dialog_window))
        return

    def run_installation():
        debug_console.log(f"Starting installation for language package: {from_code} -> {to_code}.", level='INFO')
        try:
            # Display a temporary status message indicating installation is in progress.
            _root.after(0, lambda: _show_temporary_status_message_func(f"⏳ Installing {from_code} to {to_code} language package... This may take a while."))
            
            # Perform the installation.
            argostranslate.package.install_from_path(
                argostranslate.package.get_package_path(from_code, to_code)
            )
            debug_console.log(f"Successfully installed language package: {from_code} -> {to_code}.", level='SUCCESS')
            # Display success message.
            _root.after(0, lambda: _show_temporary_status_message_func(f"✅ Language package {from_code} to {to_code} installed."))
            # Call the completion callback.
            _root.after(0, callback_on_completion) 
        except Exception as e:
            debug_console.log(f"Failed to install language package {from_code} -> {to_code}: {e}", level='ERROR')
            # Display error message.
            _root.after(0, lambda: messagebox.showerror("Installation Error", f"Failed to install language package: {e}", parent=dialog_window))
            _root.after(0, lambda: _show_temporary_status_message_func(f"❌ Installation failed for {from_code} to {to_code}."))

    # Start the installation in a new daemon thread.
    threading.Thread(target=run_installation, daemon=True).start()

def _perform_translation_threaded(source_text, from_code, to_code, original_filepath, dialog_window):
    """
    Performs the actual text translation using `argostranslate` in a separate thread.

    After translation, the result is saved to a new file, and appropriate status
    messages and success/error dialogs are displayed.

    Args:
        source_text (str): The text content to be translated.
        from_code (str): The language code of the source text.
        to_code (str): The language code of the target translation.
        original_filepath (str): The file path of the original document (used for naming the translated file).
        dialog_window (tk.Toplevel): The parent dialog window for displaying messages.
    """
    if not _ARGOS_TRANSLATE_AVAILABLE:
        _root.after(0, lambda: messagebox.showerror("Translation Error", "Argos Translate module is not available.", parent=dialog_window))
        _root.after(0, dialog_window.destroy) # Close dialog if translation is not possible.
        return

    def run_translation():
        debug_console.log(f"Starting translation process from {from_code} to {to_code}.", level='INFO')
        translated_filepath = "" # Initialize translated_filepath
        try:
            _root.after(0, lambda: _show_temporary_status_message_func(f"⏳ Translating from {from_code} to {to_code}..."))
            translated_text = argostranslate.translate.translate(source_text, from_code, to_code)

            if original_filepath:
                # Construct the translated filename based on the original file.
                base_name, ext = os.path.splitext(os.path.basename(original_filepath))
                translated_filename = f"{base_name}_{to_code}{ext}"
                translated_filepath = os.path.join(os.path.dirname(original_filepath), translated_filename)
            else:
                # If no original file, save to a default temporary location.
                output_directory = "output"
                os.makedirs(output_directory, exist_ok=True)
                translated_filename = f"temp_document_{to_code}.tex"
                translated_filepath = os.path.join(output_directory, translated_filename)
            
            debug_console.log(f"Translation complete. Saving translated content to: {translated_filepath}", level='INFO')
            with open(translated_filepath, "w", encoding="utf-8") as f:
                f.write(translated_text)

            debug_console.log("Translated document saved successfully.", level='SUCCESS')
            _root.after(0, lambda: _show_temporary_status_message_func(f"✅ Document translated and saved to {os.path.basename(translated_filepath)}"))
            _root.after(0, lambda: messagebox.showinfo("Translation Success", f"Document translated and saved to:\n{translated_filepath}", parent=dialog_window))
        except Exception as e:
            debug_console.log(f"An error occurred during translation: {e}", level='ERROR')
            _root.after(0, lambda: messagebox.showerror("Translation Error", f"An error occurred during translation: {e}", parent=dialog_window))
            _root.after(0, lambda: _show_temporary_status_message_func(f"❌ Translation failed: {e}"))
        finally:
            # Ensure the dialog is closed after the translation attempt.
            _root.after(0, dialog_window.destroy)

    # Start the translation in a new daemon thread.
    threading.Thread(target=run_translation, daemon=True).start()

def open_translate_dialog():
    """
    Opens a dialog window allowing the user to select source and target languages for translation.

    This dialog fetches available translation packages, prompts for installation if necessary,
    and initiates the translation process for the content of the active editor.
    """
    debug_console.log("Opening translation dialog.", level='ACTION')
    editor_widget = _active_editor_getter_func()
    
    # Pre-check for necessary initializations and Argos Translate availability.
    if not editor_widget or not _root or not _theme_setting_getter_func or not _show_temporary_status_message_func:
        debug_console.log("Translator service not fully initialized or missing dependencies. Aborting dialog.", level='ERROR')
        messagebox.showerror("Translator Error", "Translator service not fully initialized. Please restart the application.")
        return

    if not _ARGOS_TRANSLATE_AVAILABLE:
        messagebox.showerror("Argos Translate Error", "The 'argostranslate' Python module is not installed. Please install it using 'pip install argostranslate' to enable translation features.")
        return
    
    source_text_content = editor_widget.get("1.0", tk.END)
    if not source_text_content.strip():
        debug_console.log("Translation dialog: Editor content is empty. No translation needed.", level='INFO')
        messagebox.showwarning("Translation", "The editor is empty. Nothing to translate.")
        return

    # Create the main translation dialog window.
    dialog = tk.Toplevel(_root)
    dialog.title("Translate Document")
    dialog.transient(_root) # Make the dialog appear on top of the main window.
    dialog.grab_set() # Grab all input until the dialog is closed.
    dialog.geometry("450x300")

    # Apply theme settings to the dialog.
    dialog_background_color = _theme_setting_getter_func("root_bg", "#f0f0f0")
    dialog.configure(bg=dialog_background_color)

    main_frame = ttk.Frame(dialog, padding=15)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Select Translation Pair:").pack(pady=(0, 5), anchor="w")

    # Get available translation pairs and prepare them for the combobox.
    translation_pairs_data = _get_available_translation_pairs()
    display_options = [item[2] for item in translation_pairs_data]
    if not display_options:
        debug_console.log("No Argos Translate packages found or available for download.", level='ERROR')
        messagebox.showerror("Argos Translate Error", "No translation packages found. Please ensure internet connection or download packages using 'argos-translate --gui'.", parent=dialog)
        dialog.destroy()
        return

    selected_pair_var = tk.StringVar(dialog)
    lang_combobox = ttk.Combobox(main_frame, textvariable=selected_pair_var, values=display_options, state="readonly")
    lang_combobox.pack(fill="x", pady=(0, 10))
    if display_options:
        lang_combobox.set(display_options[0]) # Set the first available pair as default.

    def on_translate_button_click():
        """
        Handles the logic when the 'Translate' button in the dialog is clicked.
        Checks for package installation and initiates translation or installation.
        """
        selected_display_text = selected_pair_var.get()
        if not selected_display_text:
            messagebox.showwarning("Selection Error", "Please select a translation pair from the list.", parent=dialog)
            return

        # Find the selected translation pair data (codes and display name).
        selected_pair_info = next((item for item in translation_pairs_data if item[2] == selected_display_text), None)
        if not selected_pair_info:
            messagebox.showerror("Error", "Invalid translation pair selection.", parent=dialog)
            return

        from_language_code, to_language_code, _ = selected_pair_info
        debug_console.log(f"User selected translation pair: {from_language_code} -> {to_language_code}", level='ACTION')

        # Check if the required language package is installed.
        is_package_installed = any(
            pkg.from_code == from_language_code and pkg.to_code == to_language_code
            for pkg in argostranslate.package.get_installed_packages()
        )

        if not is_package_installed:
            debug_console.log(f"Language package {from_language_code}->{to_language_code} is not installed. Prompting user for installation.", level='INFO')
            response = messagebox.askyesno(
                "Install Language Package",
                f"The language package for {from_language_code} to {to_language_code} is not installed. Do you want to install it now? This may take some time and requires an internet connection.",
                parent=dialog
            )
            if response:
                debug_console.log("User chose to install language package.", level='ACTION')
                # Install the package, then perform translation upon successful installation.
                _install_language_package_threaded(from_language_code, to_language_code, dialog,
                                                   lambda: _perform_translation_threaded(
                                                       source_text_content, from_language_code, to_language_code,
                                                       _active_filepath_getter_func(), dialog
                                                   ))
            else:
                debug_console.log("User declined language package installation. Translation aborted.", level='INFO')
                dialog.destroy() # Close the dialog if installation is declined.
            return

        # If the package is installed, proceed directly with translation.
        _perform_translation_threaded(source_text_content, from_language_code, to_language_code, _active_filepath_getter_func(), dialog)

    translate_button = ttk.Button(main_frame, text="Translate", command=on_translate_button_click)
    translate_button.pack(pady=10)

    # Handle window close event.
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.wait_window() # Block until the dialog is closed.
