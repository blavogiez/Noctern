"""
This module is responsible for creating and managing the application's top bar,
which includes various action buttons and dropdown menus for functionalities
such as file operations, LaTeX compilation, LLM interactions, and application settings.
"""

from tkinter import ttk, Menu
from latex import compiler as latex_compiler
from llm import service as llm_service
from latex import translator as latex_translator
from app import main_window as interface
from utils import debug_console
from llm import rephrase as llm_rephrase
from editor import snippets as editor_snippets

def _log_action(action_name):
    """
    Helper function to log user actions triggered from the UI elements.

    Args:
        action_name (str): A descriptive name of the action being performed.
    """
    debug_console.log(f"UI Action: User triggered '{action_name}'.", level='ACTION')

def create_top_buttons_frame(root):
    """
    Creates and populates the top bar frame with buttons and menus for application control.

    This function sets up the layout for file operations, compilation, LLM features,
    and provides access to various settings and tools through dropdown menus.

    Args:
        root (tk.Tk): The root Tkinter window of the application.

    Returns:
        tuple: A tuple containing:
            - top_frame (ttk.Frame): The created top bar frame.
            - settings_menu (tk.Menu): The settings menu, allowing external modification (e.g., enabling/disabling options).
    """
    # Create the main frame for the top bar, packed at the top of the root window.
    top_frame = ttk.Frame(root, padding=10)
    top_frame.pack(fill="x", pady=(0, 5))

    # --- File Operation Buttons ---
    # Open File button: Triggers the open file dialog.
    ttk.Button(top_frame, text="📂 Open", command=lambda: [_log_action("Open File"), interface.open_file()]).pack(side="left", padx=3, pady=3)
    # Save File button: Saves the current active file.
    ttk.Button(top_frame, text="💾 Save", command=lambda: [_log_action("Save File"), interface.save_file()]).pack(side="left", padx=3, pady=3)
    # Save As button: Saves the current file to a new location/name.
    ttk.Button(top_frame, text="💾 Save As", command=lambda: [_log_action("Save File As"), interface.save_file_as()]).pack(side="left", padx=3, pady=3)
    
    # Separator for visual grouping.
    ttk.Separator(top_frame, orient='vertical').pack(side='left', padx=5, fill='y')

    # --- LaTeX Processing Buttons ---
    # Compile button: Triggers LaTeX compilation.
    ttk.Button(top_frame, text="🛠 Compile", command=lambda: [_log_action("Compile LaTeX"), latex_compiler.compile_latex()]).pack(side="left", padx=3, pady=3)
    # Translate button: Opens the translation dialog.
    ttk.Button(top_frame, text="🌐 Translate", command=lambda: [_log_action("Translate Text"), latex_translator.open_translate_dialog()]).pack(side="left", padx=3, pady=3)
    
    # Separator for visual grouping.
    ttk.Separator(top_frame, orient='vertical').pack(side='left', padx=5, fill='y')

    # --- LLM Interaction Buttons ---
    # Complete button: Triggers LLM text completion.
    ttk.Button(top_frame, text="✨ Complete", command=lambda: [_log_action("LLM Complete Text"), llm_service.request_llm_to_complete_text()]).pack(side="left", padx=3, pady=3)
    # Generate button: Opens the LLM text generation dialog.
    ttk.Button(top_frame, text="🎯 Generate", command=lambda: [_log_action("LLM Generate Text"), llm_service.open_generate_text_dialog()]).pack(side="left", padx=3, pady=3)
    
    # Theme Toggle button: Switches between light and dark themes.
    ttk.Button(top_frame, text="🌓 Theme", command=lambda: [_log_action("Toggle Theme"), interface.apply_theme("dark" if interface.current_theme == "light" else "light")]).pack(side="right", padx=3, pady=3)

    # --- Settings Menu Button ---
    settings_menubutton = ttk.Menubutton(top_frame, text="⚙️ Settings")
    settings_menubutton.pack(side="right", padx=3, pady=3)
    settings_menu = Menu(settings_menubutton, tearoff=0) # Create a dropdown menu.
    settings_menubutton["menu"] = settings_menu # Associate the menu with the menubutton.
    
    # --- Tools Menu Button ---
    tools_menubutton = ttk.Menubutton(top_frame, text="🔧 Tools")
    tools_menubutton.pack(side="right", padx=3, pady=3)
    tools_menu = Menu(tools_menubutton, tearoff=0) # Create a dropdown menu.
    tools_menubutton["menu"] = tools_menu # Associate the menu with the menubutton.

    # --- Populate Tools Menu ---
    tools_menu.add_command(label="Check Document (chktex)", command=lambda: [_log_action("Tools: chktex Check"), latex_compiler.run_chktex_check()])
    tools_menu.add_command(label="Rephrase Selected Text (Ctrl+R)", command=lambda: [_log_action("Tools: Rephrase Text"), llm_rephrase.open_rephrase_dialog()])
    tools_menu.add_command(label="Paste Image from Clipboard (Ctrl+Shift+V)", command=lambda: [_log_action("Tools: Paste Image"), interface.paste_image()])
    tools_menu.add_separator() # Add a visual separator.
    tools_menu.add_command(label="Clean Project Directory", command=lambda: [_log_action("Tools: Clean Project"), latex_compiler.clean_project_directory()])

    # --- Populate Settings Menu ---
    settings_menu.add_command(label="Set LLM Keywords...", command=lambda: [_log_action("Settings: Set LLM Keywords"), llm_service.open_set_keywords_dialog()])
    settings_menu.add_command(label="Edit LLM Prompts...", command=lambda: [_log_action("Settings: Edit LLM Prompts"), llm_service.open_edit_prompts_dialog()])
    settings_menu.add_command(label="Edit Snippets...", command=lambda: [_log_action("Settings: Edit Snippets"), editor_snippets.open_snippet_editor()])
    settings_menu.add_separator() # Add a visual separator.
    
    # Advanced Mode Checkbutton: Toggles advanced features.
    settings_menu.add_checkbutton(
        label="Advanced Mode",
        variable=interface._advanced_mode_enabled, # Linked to a BooleanVar in interface.py.
        command=interface.toggle_advanced_mode # Callback to toggle advanced features.
    )
    # Show Debug Console option (initially disabled, enabled by Advanced Mode).
    settings_menu.add_command(
        label="Show Debug Console",
        command=lambda: [_log_action("Settings: Show Debug Console"), debug_console.show_console()],
        state="disabled" # Initially disabled.
    )
    # Restart Application option (initially disabled, enabled by Advanced Mode).
    settings_menu.add_command(
        label="Restart Application",
        command=lambda: [_log_action("Settings: Restart Application"), interface.restart_application()],
        state="disabled" # Initially disabled.
    )
    
    return top_frame, settings_menu
