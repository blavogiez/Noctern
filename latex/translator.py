"""
This module provides functionality for translating LaTeX document content using the Hugging Face `transformers` library.
It is optimized to run on a CUDA-enabled GPU if available and includes a robust protection mechanism
to avoid translating LaTeX commands, environments, and other syntax, ensuring document compilability.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import re
from utils import debug_console

try:
    import torch
    from transformers import MarianMTModel, MarianTokenizer
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    debug_console.log("The 'transformers' or 'torch' module was not found. Translation functionality will be disabled.", level='WARNING')

# --- Globals ---
_root = None
_theme_setting_getter_func = None
_show_temporary_status_message_func = None
_active_editor_getter_func = None
_active_filepath_getter_func = None

# --- Model Cache ---
_model_cache = {}
_device = None

# --- Supported Languages ---
SUPPORTED_TRANSLATIONS = {
    "Français -> Anglais": "Helsinki-NLP/opus-mt-fr-en",
    "Anglais -> Français": "Helsinki-NLP/opus-mt-en-fr",
    "Français -> Espagnol": "Helsinki-NLP/opus-mt-fr-es",
    "Espagnol -> Français": "Helsinki-NLP/opus-mt-es-fr",
    "Français -> Allemand": "Helsinki-NLP/opus-mt-fr-de",
    "Allemand -> Français": "Helsinki-NLP/opus-mt-de-fr",
    "Anglais -> Espagnol": "Helsinki-NLP/opus-mt-en-es",
    "Espagnol -> Anglais": "Helsinki-NLP/opus-mt-es-en",
    "Anglais -> Allemand": "Helsinki-NLP/opus-mt-en-de",
    "Allemand -> Anglais": "Helsinki-NLP/opus-mt-de-en",
}

# This regex tokenizes the text into fundamental LaTeX components.
# It handles \verb, commands, comments, math, and special characters.
LATEX_SPLIT_PATTERN = re.compile(r'(\\verb(.).*?\2|\\[a-zA-Z@]+(?:\*)?|\\[^a-zA-Z]|%.*?$|\$[^$]*\$|\$\$[^$]*\$\$|[{}[\]&])', re.MULTILINE)

# --- CORE FIX: Commands whose arguments are KEYWORDS, not translatable content ---
# These commands have arguments that are part of the LaTeX syntax and must be protected.
KEYWORD_ARG_COMMANDS = {
    '\\documentclass', '\\usepackage', '\\include', '\\input',
    '\\begin', '\\end',
    '\\label', '\\ref', '\\pageref', '\\cite',
    '\\includegraphics', '\\bibliographystyle', '\\bibliography',
    '\\newcounter', '\\setcounter', '\\newenvironment', '\\newcommand', '\\renewcommand',
    '\\rowcolor', '\\columncolor',
    '\\codeboxlang',  # The language name is a keyword
    '\\policeprincipale', '\\policesecondaire', # Custom commands with keyword-like args
    '\\rotatebox', '\\multirow'
}

def initialize_translator(root_ref, theme_getter, status_message_func, active_editor_getter, active_filepath_getter):
    """Initializes the translator service and determines the compute device."""
    global _root, _theme_setting_getter_func, _show_temporary_status_message_func
    global _active_editor_getter_func, _active_filepath_getter_func, _device

    _root = root_ref
    _theme_setting_getter_func = theme_getter
    _show_temporary_status_message_func = status_message_func
    _active_editor_getter_func = active_editor_getter
    _active_filepath_getter_func = active_filepath_getter

    if _TRANSFORMERS_AVAILABLE:
        is_gpu_available = torch.cuda.is_available()
        _device = "cuda" if is_gpu_available else "cpu"
        debug_console.log(f"Translator service initialized. Device set to: {_device.upper()}", level='INFO')
    else:
        debug_console.log("Transformers library not available. Translation is disabled.", level='ERROR')

def _get_model_and_tokenizer(model_name):
    """Loads and caches a translation model and tokenizer, moving the model to the correct device."""
    if model_name in _model_cache:
        model, tokenizer = _model_cache[model_name]
        model.to(_device)
        return model, tokenizer

    _show_temporary_status_message_func(f"Downloading model '{model_name}'...")
    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        model.to(_device)
        debug_console.log(f"Model '{model_name}' loaded and moved to {model.device}", level='INFO')
        _model_cache[model_name] = (model, tokenizer)
        _show_temporary_status_message_func(f"Model '{model_name}' ready.")
        return model, tokenizer
    except Exception as e:
        debug_console.log(f"Failed to load model '{model_name}': {e}", level='ERROR')
        messagebox.showerror("Model Error", f"Could not load model '{model_name}'. Check internet connection.")
        return None, None

def _translate_text_chunk(text, model, tokenizer):
    """
    Translates a single block of text, preserving surrounding whitespace.
    """
    if not text.strip():
        return text

    leading_whitespace = text[:len(text) - len(text.lstrip())]
    trailing_whitespace = text[len(text.rstrip()):]
    trimmed_text = text.strip()

    if not trimmed_text:
        return text

    try:
        inputs = tokenizer(trimmed_text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(_device)
        with torch.no_grad():
            translated_ids = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
        translated_text = tokenizer.batch_decode(translated_ids, skip_special_tokens=True)[0]
        return leading_whitespace + translated_text + trailing_whitespace
    except Exception as e:
        debug_console.log(f"Error translating text chunk: {e}", level='WARNING')
        return text

def _find_first_section(text):
    """Finds the position of the first \section command in the document."""
    match = re.search(r'\\section\s*\{', text, re.IGNORECASE)
    return match.start() if match else None

def _translate_latex_safely(text, model, tokenizer, skip_preamble=False):
    """
    Translates LaTeX text using a stateful parser to protect command arguments that are keywords.
    """
    original_text = text
    preamble = ""
    if skip_preamble:
        first_section_pos = _find_first_section(text)
        if first_section_pos is not None:
            preamble = text[:first_section_pos]
            text = text[first_section_pos:]
            debug_console.log(f"Skipping preamble of {len(preamble)} characters", level='INFO')

    parts = LATEX_SPLIT_PATTERN.split(text)
    
    # Filter out empty strings from the split
    parts = [p for p in parts if p]

    # Smartly count translatable parts
    num_parts_to_translate = 0
    i = 0
    while i < len(parts):
        part = parts[i]
        command_name = part.rstrip('*') if part.startswith('\\') else ''

        if command_name in KEYWORD_ARG_COMMANDS:
            # Skip this command and its argument block
            i += 1
            brace_depth = 0
            arg_started = False
            while i < len(parts):
                if not arg_started:
                    if parts[i].strip() == '': # Skip whitespace
                        i += 1
                        continue
                    if parts[i] == '{':
                        arg_started = True
                        brace_depth = 1
                    else: # Command without a brace argument (e.g., \tableofcontents)
                        break
                else:
                    if parts[i] == '{': brace_depth += 1
                    elif parts[i] == '}': brace_depth -= 1
                i += 1
                if arg_started and brace_depth == 0: break
            continue
        
        if not LATEX_SPLIT_PATTERN.match(part):
            stripped = part.strip()
            if len(stripped) > 3 and any(c.isalpha() for c in stripped):
                num_parts_to_translate += 1
        i += 1

    if num_parts_to_translate == 0:
        debug_console.log("No translatable content found", level='INFO')
        return original_text
    
    _root.after(0, lambda: _show_temporary_status_message_func(
        f"Translating {num_parts_to_translate} text segments on {model.device}..."
    ))
    
    translated_parts = []
    translated_count = 0
    i = 0
    while i < len(parts):
        part = parts[i]
        command_name = part.rstrip('*') if part.startswith('\\') else ''

        # If the part is a command with a keyword argument, append it and its argument without translation
        if command_name in KEYWORD_ARG_COMMANDS:
            block_to_keep = [part]
            i += 1
            brace_depth = 0
            arg_started = False
            # Look for the start of the argument
            while i < len(parts):
                next_part = parts[i]
                block_to_keep.append(next_part)
                
                if not arg_started:
                    if next_part.strip() == '':
                        i+=1
                        continue
                    if next_part == '{':
                        arg_started = True
                        brace_depth = 1
                    else:
                        break # No brace argument, protection ends
                else: # Argument has started, track braces
                    if next_part == '{': brace_depth += 1
                    elif next_part == '}': brace_depth -= 1

                i += 1
                if arg_started and brace_depth == 0:
                    break
            translated_parts.extend(block_to_keep)
            continue

        # If it is a different command/symbol, just append it
        if LATEX_SPLIT_PATTERN.match(part):
            translated_parts.append(part)
        else:
            # This is plain text, check if it should be translated
            stripped = part.strip()
            if len(stripped) > 3 and any(c.isalpha() for c in stripped):
                translated_chunk = _translate_text_chunk(part, model, tokenizer)
                translated_parts.append(translated_chunk)
                translated_count += 1
                if translated_count % 10 == 0:
                    progress = f"Translated {translated_count}/{num_parts_to_translate} segments..."
                    _root.after(0, lambda p=progress: _show_temporary_status_message_func(p))
            else:
                # Keep short text or whitespace as is
                translated_parts.append(part)
        i += 1
            
    return preamble + "".join(translated_parts)

def _perform_translation_threaded(source_text, model_name, original_filepath, dialog_window, skip_preamble):
    """Manages the translation process in a background thread."""
    def run_translation():
        try:
            _root.after(0, lambda: _show_temporary_status_message_func(f"Initializing translation on {_device.upper()}..."))
            
            model, tokenizer = _get_model_and_tokenizer(model_name)
            if not model or not tokenizer:
                _root.after(0, dialog_window.destroy)
                return
            
            translated_text = _translate_latex_safely(source_text, model, tokenizer, skip_preamble)

            if original_filepath:
                base, ext = os.path.splitext(os.path.basename(original_filepath))
                target_lang = model_name.split('-')[-1]
                translated_filename = f"{base}_{target_lang}{ext}"
                translated_filepath = os.path.join(os.path.dirname(original_filepath), translated_filename)
            else:
                os.makedirs("output", exist_ok=True)
                translated_filepath = os.path.join("output", "translated_document.tex")

            with open(translated_filepath, "w", encoding="utf-8") as f:
                f.write(translated_text)

            debug_console.log(f"Translation complete. Saved to: {translated_filepath}", level='SUCCESS')
            _root.after(0, lambda: _show_temporary_status_message_func(f"Translation saved to {os.path.basename(translated_filepath)}"))
            _root.after(0, lambda: messagebox.showinfo("Translation Success", f"Document translated and saved to:\n{translated_filepath}", parent=dialog_window))

        except Exception as e:
            error_message = f"An error occurred during translation: {e}"
            debug_console.log(error_message, level='ERROR')
            _root.after(0, lambda msg=error_message: messagebox.showerror("Translation Error", msg, parent=dialog_window))
        finally:
            _root.after(0, dialog_window.destroy)

    threading.Thread(target=run_translation, daemon=True).start()

def open_translate_dialog():
    """Opens a dialog for the user to select a translation language pair and options."""
    if not _TRANSFORMERS_AVAILABLE:
        messagebox.showerror("Translation Error", "The 'transformers' library is not installed. Please run 'pip install transformers sentencepiece'.")
        return

    editor_widget = _active_editor_getter_func()
    source_text = editor_widget.get("1.0", tk.END)
    if not source_text.strip():
        messagebox.showwarning("Translation", "The editor is empty.")
        return

    dialog = tk.Toplevel(_root)
    dialog.title("Translate Document")
    dialog.transient(_root)
    dialog.grab_set()
    dialog.geometry("500x280")

    bg_color = _theme_setting_getter_func("root_bg", "#f0f0f0")
    dialog.configure(bg=bg_color)

    main_frame = ttk.Frame(dialog, padding=15)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Select Translation:").pack(pady=(0, 5), anchor="w")

    selected_pair_var = tk.StringVar(dialog)
    display_options = list(SUPPORTED_TRANSLATIONS.keys())
    lang_combobox = ttk.Combobox(main_frame, textvariable=selected_pair_var, values=display_options, state="readonly")
    lang_combobox.pack(fill="x", pady=(0, 15))
    if display_options:
        lang_combobox.set(display_options[0])

    options_frame = ttk.LabelFrame(main_frame, text="Translation Options", padding=10)
    options_frame.pack(fill="x", pady=(0, 15))

    skip_preamble_var = tk.BooleanVar(value=True)
    skip_preamble_check = ttk.Checkbutton(
        options_frame, 
        text="Skip preamble (don't translate before first \\section)", 
        variable=skip_preamble_var
    )
    skip_preamble_check.pack(anchor="w")

    info_label = ttk.Label(
        options_frame, 
        text="Recommended: Preserves document structure and LaTeX commands",
        font=("TkDefaultFont", 8),
        foreground="gray"
    )
    info_label.pack(anchor="w", pady=(2, 0))

    def on_translate():
        selection = selected_pair_var.get()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a translation pair.", parent=dialog)
            return
        
        model_name = SUPPORTED_TRANSLATIONS[selection]
        filepath = _active_filepath_getter_func()
        skip_preamble = skip_preamble_var.get()
        
        debug_console.log(f"User selected translation: {selection} ({model_name}), skip_preamble: {skip_preamble}", level='ACTION')
        
        _perform_translation_threaded(source_text, model_name, filepath, dialog, skip_preamble)

    translate_button = ttk.Button(main_frame, text=f"Translate on {_device.upper()}", command=on_translate)
    translate_button.pack(pady=10)

    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.wait_window()