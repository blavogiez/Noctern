"""
This module provides functionality for translating LaTeX document content using the Hugging Face `transformers` library.
It is optimized to run on a CUDA-enabled GPU if available and includes a robust protection mechanism
to avoid translating LaTeX commands, environments, and other syntax, ensuring document compilability.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
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

    _show_temporary_status_message_func(f"⏳ Downloading model '{model_name}'...")
    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        model.to(_device)
        debug_console.log(f"Model '{model_name}' loaded and moved to {model.device}", level='INFO')
        _model_cache[model_name] = (model, tokenizer)
        _show_temporary_status_message_func(f"✅ Model '{model_name}' ready.")
        return model, tokenizer
    except Exception as e:
        debug_console.log(f"Failed to load model '{model_name}': {e}", level='ERROR')
        messagebox.showerror("Model Error", f"Could not load model '{model_name}'. Check internet connection.")
        return None, None

def _parse_latex_text(text):
    """
    Simple character-by-character parser that protects all LaTeX commands and math.
    Returns list of (content, is_protected) tuples.
    """
    chunks = []
    current_chunk = ""
    current_protected = ""
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # Handle backslash (start of LaTeX command)
        if char == '\\':
            # Save current translatable text
            if current_chunk.strip():
                chunks.append((current_chunk, False))
                current_chunk = ""
            
            # Start collecting protected command
            current_protected = char
            i += 1
            
            # Collect command name (letters only)
            while i < len(text) and text[i].isalpha():
                current_protected += text[i]
                i += 1
            
            # Handle command arguments and options
            while i < len(text):
                if text[i] in ' \t\n':
                    current_protected += text[i]
                    i += 1
                elif text[i] == '[':
                    # Optional argument
                    bracket_count = 1
                    current_protected += text[i]
                    i += 1
                    while i < len(text) and bracket_count > 0:
                        if text[i] == '[':
                            bracket_count += 1
                        elif text[i] == ']':
                            bracket_count -= 1
                        current_protected += text[i]
                        i += 1
                elif text[i] == '{':
                    # Required argument
                    brace_count = 1
                    current_protected += text[i]
                    i += 1
                    while i < len(text) and brace_count > 0:
                        if text[i] == '{':
                            brace_count += 1
                        elif text[i] == '}':
                            brace_count -= 1
                        current_protected += text[i]
                        i += 1
                else:
                    break
            
            # Save protected command
            chunks.append((current_protected, True))
            current_protected = ""
            continue
        
        # Handle dollar signs (math mode)
        elif char == '$':
            # Save current translatable text
            if current_chunk.strip():
                chunks.append((current_chunk, False))
                current_chunk = ""
            
            # Check for double dollar
            if i + 1 < len(text) and text[i + 1] == '$':
                # Display math $$...$$
                current_protected = '$$'
                i += 2
                while i < len(text):
                    current_protected += text[i]
                    if text[i] == '$' and i + 1 < len(text) and text[i + 1] == '$':
                        current_protected += text[i + 1]
                        i += 2
                        break
                    i += 1
            else:
                # Inline math $...$
                current_protected = '$'
                i += 1
                while i < len(text):
                    current_protected += text[i]
                    if text[i] == '$':
                        i += 1
                        break
                    i += 1
            
            chunks.append((current_protected, True))
            current_protected = ""
            continue
        
        # Handle comments
        elif char == '%':
            # Save current translatable text
            if current_chunk.strip():
                chunks.append((current_chunk, False))
                current_chunk = ""
            
            # Collect entire comment line
            current_protected = ""
            while i < len(text) and text[i] != '\n':
                current_protected += text[i]
                i += 1
            
            chunks.append((current_protected, True))
            current_protected = ""
            continue
        
        # Regular character
        else:
            current_chunk += char
            i += 1
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append((current_chunk, False))
    if current_protected:
        chunks.append((current_protected, True))
    
    return chunks

def _clean_translatable_text(text):
    """Clean text for better translation quality."""
    # Normalize whitespace
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
        elif cleaned_lines and cleaned_lines[-1]:  # Preserve paragraph breaks
            cleaned_lines.append('')
    
    return '\n'.join(cleaned_lines).strip()

def _translate_latex_safely(text, model, tokenizer):
    """
    Translate LaTeX text while protecting all commands and math.
    """
    chunks = _parse_latex_text(text)
    
    if not chunks:
        return text
    
    # Count translatable chunks
    translatable_chunks = [chunk for chunk, is_protected in chunks 
                          if not is_protected and chunk.strip()]
    num_translatable = len(translatable_chunks)
    
    if num_translatable == 0:
        debug_console.log("No translatable text found in document.", level='INFO')
        return text
    
    _root.after(0, lambda: _show_temporary_status_message_func(
        f"⏳ Translating {num_translatable} text segments on {model.device}..."
    ))
    
    translated_chunks = []
    translated_count = 0
    
    for chunk, is_protected in chunks:
        if is_protected:
            # Keep protected content as-is
            translated_chunks.append(chunk)
        else:
            # Clean and translate
            clean_text = _clean_translatable_text(chunk)
            
            if not clean_text:
                translated_chunks.append(chunk)
                continue
            
            try:
                # Translate in smaller pieces if text is too long
                max_length = 400
                if len(clean_text) > max_length:
                    # Split by sentences or paragraphs
                    sentences = clean_text.replace('\n\n', ' [PARAGRAPH] ').split('. ')
                    translated_sentences = []
                    
                    for sentence in sentences:
                        if not sentence.strip():
                            continue
                        
                        sentence = sentence.strip()
                        if not sentence.endswith('.') and '[PARAGRAPH]' not in sentence:
                            sentence += '.'
                        
                        inputs = tokenizer(sentence, return_tensors="pt", 
                                         padding=True, truncation=True).to(model.device)
                        
                        with torch.no_grad():
                            translated_ids = model.generate(**inputs, max_length=200,
                                                           num_beams=2, early_stopping=True)
                        
                        translated_sentence = tokenizer.batch_decode(
                            translated_ids, skip_special_tokens=True)[0]
                        translated_sentences.append(translated_sentence)
                    
                    translated_text = '. '.join(translated_sentences)
                    translated_text = translated_text.replace(' [PARAGRAPH] ', '\n\n')
                else:
                    # Translate normally
                    inputs = tokenizer(clean_text, return_tensors="pt", 
                                     padding=True, truncation=True).to(model.device)
                    
                    with torch.no_grad():
                        translated_ids = model.generate(**inputs, max_length=512,
                                                       num_beams=2, early_stopping=True)
                    
                    translated_text = tokenizer.batch_decode(
                        translated_ids, skip_special_tokens=True)[0]
                
                translated_chunks.append(translated_text)
                translated_count += 1
                
                # Update progress
                if translated_count % 5 == 0:
                    progress = f"⏳ Translated {translated_count}/{num_translatable} segments..."
                    _root.after(0, lambda p=progress: _show_temporary_status_message_func(p))
                
            except Exception as e:
                debug_console.log(f"Error translating chunk: {e}", level='WARNING')
                translated_chunks.append(chunk)  # Keep original if translation fails
    
    return ''.join(translated_chunks)

def _perform_translation_threaded(source_text, model_name, original_filepath, dialog_window):
    """Manages the translation process in a background thread."""
    def run_translation():
        try:
            _root.after(0, lambda: _show_temporary_status_message_func(f"⏳ Initializing translation on {_device.upper()}..."))
            
            model, tokenizer = _get_model_and_tokenizer(model_name)
            if not model or not tokenizer:
                _root.after(0, dialog_window.destroy)
                return
            
            translated_text = _translate_latex_safely(source_text, model, tokenizer)

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
            _root.after(0, lambda: _show_temporary_status_message_func(f"✅ Translation saved to {os.path.basename(translated_filepath)}"))
            _root.after(0, lambda: messagebox.showinfo("Translation Success", f"Document translated and saved to:\n{translated_filepath}", parent=dialog_window))

        except Exception as e:
            error_message = f"An error occurred during translation: {e}"
            debug_console.log(error_message, level='ERROR')
            _root.after(0, lambda msg=error_message: messagebox.showerror("Translation Error", msg, parent=dialog_window))
        finally:
            _root.after(0, dialog_window.destroy)

    threading.Thread(target=run_translation, daemon=True).start()

def open_translate_dialog():
    """Opens a dialog for the user to select a translation language pair."""
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
    dialog.geometry("450x200")

    bg_color = _theme_setting_getter_func("root_bg", "#f0f0f0")
    dialog.configure(bg=bg_color)

    main_frame = ttk.Frame(dialog, padding=15)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Select Translation:").pack(pady=(0, 5), anchor="w")

    selected_pair_var = tk.StringVar(dialog)
    display_options = list(SUPPORTED_TRANSLATIONS.keys())
    lang_combobox = ttk.Combobox(main_frame, textvariable=selected_pair_var, values=display_options, state="readonly")
    lang_combobox.pack(fill="x", pady=(0, 10))
    if display_options:
        lang_combobox.set(display_options[0])

    def on_translate():
        selection = selected_pair_var.get()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a translation pair.", parent=dialog)
            return
        
        model_name = SUPPORTED_TRANSLATIONS[selection]
        filepath = _active_filepath_getter_func()
        
        debug_console.log(f"User selected translation: {selection} ({model_name})", level='ACTION')
        
        _perform_translation_threaded(source_text, model_name, filepath, dialog)

    translate_button = ttk.Button(main_frame, text=f"Translate on {_device.upper()}", command=on_translate)
    translate_button.pack(pady=10)

    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.wait_window()