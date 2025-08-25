"""Provide LaTeX document translation using Hugging Face transformers library."""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import re
from utils import logs_console

try:
    import torch
    from transformers import MarianMTModel, MarianTokenizer
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    logs_console.log("The 'transformers' or 'torch' module was not found. Translation functionality will be disabled.", level='WARNING')

# Global variables for service configuration
_root = None
_theme_setting_getter_func = None
_show_temporary_status_message_func = None
_active_editor_getter_func = None
_active_filepath_getter_func = None

# Model caching and device configuration
_model_cache = {}
_device = None
_is_initialized = False

# Supported translation language pairs
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

# Tokenize text into fundamental LaTeX components
LATEX_SPLIT_PATTERN = re.compile(r'(\\verb(.).*?\2|\\[a-zA-Z@]+(?:\*)?|\\[^a-zA-Z]|%.*?$|\$[^$]*\$|\$\$[^$]*\$\$|[{}[\]&])', re.MULTILINE)

# Commands whose arguments should be treated as keywords and not translated
KEYWORD_ARG_COMMANDS = {
    '\\documentclass', '\\usepackage', '\\include', '\\input',
    '\\begin', '\\end',
    '\\label', '\\ref', '\\pageref', '\\cite', '\\autocite',
    '\\includegraphics', '\\insererfigure',
    '\\bibliographystyle', '\\bibliography',
    '\\newcounter', '\\setcounter', '\\newenvironment', '\\newcommand', '\\renewcommand',
    '\\rowcolor', '\\columncolor',
    '\\codeboxlang',  # The language name is a keyword
    '\\policeprincipale', '\\policesecondaire', # Custom commands with keyword-like args
    '\\rotatebox', '\\multirow', '\\multicolumn',
    '\\documentclass', '\\addbibresource', '\\printbibliography'
}

def _ensure_translator_initialized():
    """Ensure translator service is initialized before use."""
    global _root, _theme_setting_getter_func, _show_temporary_status_message_func
    global _active_editor_getter_func, _active_filepath_getter_func, _device, _is_initialized
    
    # Skip if already initialized
    if _is_initialized:
        return True
        
    # Initialize now if not done at startup
    if (_root is None or _theme_setting_getter_func is None or _show_temporary_status_message_func is None or 
        _active_editor_getter_func is None or _active_filepath_getter_func is None):
        logs_console.log("Translator service not properly configured.", level='ERROR')
        return False

    if _TRANSFORMERS_AVAILABLE:
        is_gpu_available = torch.cuda.is_available()
        _device = "cuda" if is_gpu_available else "cpu"
        logs_console.log(f"Translator service initialized. Device set to: {_device.upper()}", level='INFO')
    else:
        logs_console.log("Transformers library not available. Translation is disabled.", level='ERROR')
        return False
    
    _is_initialized = True
    return True

def initialize_translator(root_ref, theme_getter, status_message_func, active_editor_getter, active_filepath_getter):
    """Initialize translator service and determine compute device."""
    global _root, _theme_setting_getter_func, _show_temporary_status_message_func
    global _active_editor_getter_func, _active_filepath_getter_func, _device, _is_initialized

    _root = root_ref
    _theme_setting_getter_func = theme_getter
    _show_temporary_status_message_func = status_message_func
    _active_editor_getter_func = active_editor_getter
    _active_filepath_getter_func = active_filepath_getter

    # Defer device initialization to speed up startup
    logs_console.log("Translator service configured for on-demand initialization.", level='INFO')
    _is_initialized = False  # Mark as not fully initialized

def _get_model_and_tokenizer(model_name):
    """Load and cache translation model and tokenizer."""
    if model_name in _model_cache:
        model, tokenizer = _model_cache[model_name]
        model.to(_device)
        return model, tokenizer
    _show_temporary_status_message_func(f"Downloading model '{model_name}'...")
    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        model.to(_device)
        _model_cache[model_name] = (model, tokenizer)
        _show_temporary_status_message_func(f"Model '{model_name}' ready.")
        return model, tokenizer
    except Exception as e:
        messagebox.showerror("Model Error", f"Could not load model '{model_name}'. Check internet connection.")
        return None, None

def _translate_text_chunk(text, model, tokenizer):
    """Translate single text block preserving surrounding whitespace."""
    if not text.strip(): return text
    leading_ws = text[:len(text) - len(text.lstrip())]
    trailing_ws = text[len(text.rstrip()):]
    trimmed_text = text.strip()
    if not trimmed_text: return text
    try:
        inputs = tokenizer(trimmed_text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(_device)
        with torch.no_grad():
            translated_ids = model.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
        translated_text = tokenizer.batch_decode(translated_ids, skip_special_tokens=True)[0]
        return leading_ws + translated_text + trailing_ws
    except Exception as e:
        logs_console.log(f"Error translating text chunk: {e}", level='WARNING')
        return text

def _find_first_section(text):
    """Find position of first section command in document."""
    match = re.search(r'\\section\s*\{', text, re.IGNORECASE)
    return match.start() if match else None

def _translate_latex_safely(text, model, tokenizer, skip_preamble=False):
    """Translate LaTeX text using stateful parser to protect command arguments."""
    preamble = ""
    if skip_preamble:
        first_section_pos = _find_first_section(text)
        if first_section_pos is not None:
            preamble = text[:first_section_pos]
            text = text[first_section_pos:]

    parts = [p for p in LATEX_SPLIT_PATTERN.split(text) if p]
    
    # Stateful parser implementation
    final_parts = []
    text_buffer = []
    i = 0
    
    def flush_buffer():
        nonlocal text_buffer
        if text_buffer:
            buffered_text = "".join(text_buffer)
            # Translate only meaningful non-command text
            stripped = buffered_text.strip()
            if len(stripped) > 3 and any(c.isalpha() for c in stripped):
                translated_chunk = _translate_text_chunk(buffered_text, model, tokenizer)
                final_parts.append(translated_chunk)
            else:
                final_parts.append(buffered_text)  # Keep short/non-alpha text as-is
            text_buffer = []

    while i < len(parts):
        part = parts[i]
        command_name = part.rstrip('*') if part.startswith('\\') else ''

        if LATEX_SPLIT_PATTERN.match(part):
            flush_buffer()  # Translate accumulated text before command/symbol

            if command_name in KEYWORD_ARG_COMMANDS:
                block_to_keep = [part]
                i += 1
                # Capture optional arguments
                while i < len(parts) and parts[i].strip() == '':  # Skip whitespace
                    block_to_keep.append(parts[i])
                    i += 1
                if i < len(parts) and parts[i] == '[':
                    bracket_depth = 1
                    block_to_keep.append(parts[i])
                    i += 1
                    while i < len(parts) and bracket_depth > 0:
                        if parts[i] == '[': bracket_depth += 1
                        elif parts[i] == ']': bracket_depth -= 1
                        block_to_keep.append(parts[i])
                        i += 1
                
                # Capture required arguments
                while i < len(parts) and parts[i].strip() == '':  # Skip whitespace
                    block_to_keep.append(parts[i])
                    i += 1
                if i < len(parts) and parts[i] == '{':
                    brace_depth = 1
                    block_to_keep.append(parts[i])
                    i += 1
                    while i < len(parts) and brace_depth > 0:
                        if parts[i] == '{': brace_depth += 1
                        elif parts[i] == '}': brace_depth -= 1
                        block_to_keep.append(parts[i])
                        i += 1
                final_parts.append("".join(block_to_keep))
                continue  # Restart main loop from new position
            else:
                final_parts.append(part)  # Keep command/symbol but not keyword command
        else:
            text_buffer.append(part)  # Add plain text to buffer for translation
        i += 1
    
    flush_buffer()  # Translate any remaining text at document end
            
    return preamble + "".join(final_parts)

def _perform_translation_threaded(source_text, model_name, original_filepath, dialog_window, skip_preamble):
    """Manage translation process in background thread."""
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

            _root.after(0, lambda: _show_temporary_status_message_func(f"Translation saved to {os.path.basename(translated_filepath)}"))
            _root.after(0, lambda: messagebox.showinfo("Translation Success", f"Document translated and saved to:\n{translated_filepath}", parent=dialog_window))

        except Exception as e:
            logs_console.log(f"An error occurred during translation: {e}", level='ERROR')
            _root.after(0, lambda: messagebox.showerror("Translation Error", f"An error occurred during translation: {e}", parent=dialog_window))
        finally:
            _root.after(0, dialog_window.destroy)

    threading.Thread(target=run_translation, daemon=True).start()

def open_translate_panel():
    """Open integrated translate panel in left sidebar."""
    from app.panels import show_translate_panel
    
    # Initialize translator before use
    if not _ensure_translator_initialized():
        messagebox.showerror("Translation Error", "Failed to initialize translation service.")
        return
    
    if not _TRANSFORMERS_AVAILABLE:
        messagebox.showerror("Translation Error", "The 'transformers' library is not installed. Please run 'pip install transformers sentencepiece'.")
        return

    editor_widget = _active_editor_getter_func()
    source_text = editor_widget.get("1.0", tk.END)
    if not source_text.strip():
        messagebox.showwarning("Translation", "The editor is empty.")
        return

    def on_translate_callback(selected_pair, skip_preamble):
        """Handle translation request from panel."""
        model_name = SUPPORTED_TRANSLATIONS[selected_pair]
        filepath = _active_filepath_getter_func()
        
        # Create a minimal dialog window for the threaded operation status
        status_dialog = tk.Toplevel(_root)
        status_dialog.title("Translating...")
        status_dialog.transient(_root)
        status_dialog.grab_set()
        status_dialog.geometry("300x100")
        
        bg_color = _theme_setting_getter_func("root_bg", "#f0f0f0")
        status_dialog.configure(bg=bg_color)
        
        ttk.Label(status_dialog, text="Translation in progress...").pack(expand=True)
        
        _perform_translation_threaded(source_text, model_name, filepath, status_dialog, skip_preamble)

    # Show the integrated translate panel  
    show_translate_panel(source_text, SUPPORTED_TRANSLATIONS, on_translate_callback, _device)