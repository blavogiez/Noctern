
"""
This module provides functionality for translating LaTeX document content using the Hugging Face `transformers` library.
It is optimized to run on a CUDA-enabled GPU if available and includes logic to avoid translating LaTeX commands,
ensuring the structural integrity of the document.
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
        debug_console.log(f"Translator service initialized. PyTorch CUDA available: {is_gpu_available}. Device set to: {_device.upper()}", level='INFO')
        if not is_gpu_available:
            debug_console.log("GPU not detected by PyTorch. Translation will run on CPU and may be slow.", level='WARNING')
    else:
        debug_console.log("Transformers library not available. Translation is disabled.", level='ERROR')

def _get_model_and_tokenizer(model_name):
    """Loads and caches a translation model and tokenizer, moving the model to the correct device."""
    if model_name in _model_cache:
        debug_console.log(f"Loading model '{model_name}' from cache.", level='DEBUG')
        # Ensure cached model is on the correct device, in case the device changed (highly unlikely)
        model, tokenizer = _model_cache[model_name]
        model.to(_device)
        return model, tokenizer

    debug_console.log(f"Model '{model_name}' not in cache. Loading from Hugging Face Hub...", level='INFO')
    _show_temporary_status_message_func(f"⏳ Downloading model '{model_name}'...")
    
    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        
        debug_console.log(f"Moving model to device: {_device.upper()}", level='DEBUG')
        model.to(_device)
        debug_console.log(f"Model device confirmed: {model.device}", level='INFO') # Log the actual device
        
        _model_cache[model_name] = (model, tokenizer)
        debug_console.log(f"Model '{model_name}' loaded and cached successfully.", level='SUCCESS')
        _show_temporary_status_message_func(f"✅ Model '{model_name}' ready.")
        return model, tokenizer
    except Exception as e:
        debug_console.log(f"Failed to load model '{model_name}': {e}", level='ERROR')
        messagebox.showerror("Model Error", f"Could not download or load model '{model_name}'. Check internet connection.")
        return None, None

def _translate_latex_safely(text, model, tokenizer):
    """Translates LaTeX text by protecting commands and processing in batches."""
    commands = []
    pattern = re.compile(r"""
        (
            \[a-zA-Z]+(?:\\[.*?\\])?(?:\{.*?\})? | # Commands with optional args
            \\(?:begin|end)\\{[a-zA-Z*]+\} |      # Begin/End environments
            \$\$[^\]+\$\$ |                       # Display math mode
            \$[^\]]+\$ |                           # Inline math mode
            %.* |                                  # Comments
            \\[&%$_#]                              # Escaped special characters
        )
    """, re.VERBOSE)

    def protect(m):
        commands.append(m.group(1))
        return f"__LATEX_CMD_{len(commands)-1}__"

    protected_text = pattern.sub(protect, text)
    
    sentences = re.split(r'(?<=[.!?])\s+', protected_text)
    translated_text = ""

    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
        
        debug_console.log(f"Translating sentence {i+1}/{len(sentences)}. Moving tensor to {model.device}", level='DEBUG')
        inputs = tokenizer(sentence, return_tensors="pt", padding=True, truncation=True).to(model.device)
        
        # Log the device of the input tensor
        debug_console.log(f"Input tensor device: {inputs.input_ids.device}", level='DEBUG')

        translated_ids = model.generate(**inputs)
        batch_result = tokenizer.batch_decode(translated_ids, skip_special_tokens=True)[0]
        translated_text += batch_result + " "

    def unprotect(m):
        index = int(m.group(1))
        return commands[index] if 0 <= index < len(commands) else m.group(0)

    return re.sub(r"__LATEX_CMD_(\d+)__", unprotect, translated_text.strip())

def _perform_translation_threaded(source_text, model_name, original_filepath, dialog_window):
    """Manages the translation process in a background thread."""
    def run_translation():
        try:
            _root.after(0, lambda: _show_temporary_status_message_func(f"⏳ Initializing translation on {_device.upper()}..."))
            
            model, tokenizer = _get_model_and_tokenizer(model_name)
            if not model or not tokenizer:
                _root.after(0, dialog_window.destroy)
                return

            _root.after(0, lambda: _show_temporary_status_message_func(f"⏳ Translating document on {model.device}..."))
            
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
            debug_console.log(f"An error occurred during translation: {e}", level='ERROR')
            _root.after(0, lambda: messagebox.showerror("Translation Error", f"An error occurred: {e}", parent=dialog_window))
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

    # The button text now directly reflects the _device variable set at initialization
    translate_button = ttk.Button(main_frame, text=f"Translate on {_device.upper()}", command=on_translate)
    translate_button.pack(pady=10)

    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.wait_window()
