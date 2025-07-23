"""
This module is responsible for creating and managing the application's top bar,
which includes various action buttons and dropdown menus for functionalities
such as file operations, LaTeX compilation, LLM interactions, and application settings.
"""

import ttkbootstrap as ttk
from latex import compiler as latex_compiler
from llm import service as llm_service
from latex import translator as latex_translator
from app import main_window as interface
from utils import debug_console
from llm import rephrase as llm_rephrase
from editor import snippets as editor_snippets
from app import settings_window

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
        root (ttk.Window): The root ttkbootstrap window of the application.

    Returns:
        tuple: A tuple containing:
            - top_frame (ttk.Frame): The created top bar frame.
            - settings_menu (ttk.Menu): The settings menu, allowing external modification (e.g., enabling/disabling options).
    """
    # Create the main frame for the top bar, packed at the top of the root window.
    top_frame = ttk.Frame(root, padding=(5, 5, 5, 0))
    top_frame.pack(fill="x")

    # --- File Operation Buttons ---
    ttk.Button(top_frame, text="📂 Open", command=lambda: [_log_action("Open File"), interface.open_file()], bootstyle="primary-outline").pack(side="left", padx=3)
    ttk.Button(top_frame, text="💾 Save", command=lambda: [_log_action("Save File"), interface.save_file()], bootstyle="primary-outline").pack(side="left", padx=3)
    ttk.Button(top_frame, text="💾 Save As", command=lambda: [_log_action("Save File As"), interface.save_file_as()], bootstyle="primary-outline").pack(side="left", padx=3)
    
    ttk.Separator(top_frame, orient='vertical').pack(side='left', padx=10, fill='y')

    # --- LaTeX Processing Buttons ---
    ttk.Button(top_frame, text="🛠 Compile", command=lambda: [_log_action("Compile LaTeX"), latex_compiler.compile_latex()], bootstyle="info-outline").pack(side="left", padx=3)
    ttk.Button(top_frame, text="📄 View PDF", command=lambda: [_log_action("View PDF"), latex_compiler.view_pdf_external()], bootstyle="info-outline").pack(side="left", padx=3)
    ttk.Button(top_frame, text="🌐 Translate", command=lambda: [_log_action("Translate Text"), latex_translator.open_translate_dialog()], bootstyle="info-outline").pack(side="left", padx=3)
    
    ttk.Separator(top_frame, orient='vertical').pack(side='left', padx=10, fill='y')

    # --- LLM Interaction Buttons ---
    ttk.Button(top_frame, text="✨ Complete", command=lambda: [_log_action("LLM Complete Text"), llm_service.request_llm_to_complete_text()], bootstyle="success-outline").pack(side="left", padx=3)
    ttk.Button(top_frame, text="🎯 Generate", command=lambda: [_log_action("LLM Generate Text"), llm_service.open_generate_text_dialog()], bootstyle="success-outline").pack(side="left", padx=3)
    
    # --- Settings and Tools Menus ---
    # A Menubutton provides a dropdown for less frequent actions and settings.
    settings_menubutton = ttk.Menubutton(top_frame, text="⚙️ Settings", bootstyle="secondary-outline")
    settings_menubutton.pack(side="right", padx=3)
    settings_menu = ttk.Menu(settings_menubutton, tearoff=False)
    settings_menubutton["menu"] = settings_menu

    tools_menubutton = ttk.Menubutton(top_frame, text="🔧 Tools", bootstyle="secondary-outline")
    tools_menubutton.pack(side="right", padx=3)
    tools_menu = ttk.Menu(tools_menubutton, tearoff=False)
    tools_menubutton["menu"] = tools_menu

    # --- Populate Tools Menu ---
    tools_menu.add_command(label="Check Document (chktex)", command=lambda: [_log_action("Tools: chktex Check"), latex_compiler.run_chktex_check()])
    tools_menu.add_command(label="Rephrase Selected Text (Ctrl+R)", command=lambda: [_log_action("Tools: Rephrase Text"), llm_rephrase.open_rephrase_dialog()])
    tools_menu.add_command(label="Paste Image from Clipboard (Ctrl+Shift+V)", command=lambda: [_log_action("Tools: Paste Image"), interface.paste_image()])
    tools_menu.add_separator()
    tools_menu.add_command(label="Clean Project Directory", command=lambda: [_log_action("Tools: Clean Project"), latex_compiler.clean_project_directory()])

    # --- Populate Settings Menu ---
    settings_menu.add_command(label="Preferences...", command=lambda: [_log_action("Settings: Open Preferences"), settings_window.open_settings_window(root)])
    settings_menu.add_separator()
    
    # --- Theme Sub-menu ---
    theme_menu = ttk.Menu(settings_menu, tearoff=False)
    settings_menu.add_cascade(label="Theme", menu=theme_menu)
    
    def set_theme(theme_name):
        interface.root.style.theme_use(theme_name)
        interface.apply_theme()

    theme_menu.add_command(label="Light (Litera)", command=lambda: set_theme("litera"))
    theme_menu.add_command(label="Dark (Darkly)", command=lambda: set_theme("darkly"))
    theme_menu.add_command(label="Vapor", command=lambda: set_theme("vapor"))
    theme_menu.add_command(label="Flatly", command=lambda: set_theme("flatly"))
    theme_menu.add_command(label="Cyborg", command=lambda: set_theme("cyborg"))
    theme_menu.add_command(label="Journal", command=lambda: set_theme("journal"))
    
    settings_menu.add_separator()
    settings_menu.add_command(label="Set LLM Keywords...", command=lambda: [_log_action("Settings: Set LLM Keywords"), llm_service.open_set_keywords_dialog()])
    settings_menu.add_command(label="Edit LLM Prompts...", command=lambda: [_log_action("Settings: Edit LLM Prompts"), llm_service.open_edit_prompts_dialog()])
    settings_menu.add_command(label="Edit Snippets...", command=lambda: [_log_action("Settings: Edit Snippets"), editor_snippets.open_snippet_editor(root, interface.get_theme_settings())])
    settings_menu.add_separator()
    
    settings_menu.add_checkbutton(
        label="Auto-open PDF on .tex load",
        variable=interface._auto_open_pdf_var,
        command=interface.toggle_auto_open_pdf
    )
    
    settings_menu.add_command(
        label="Show Debug Console",
        command=lambda: [_log_action("Settings: Show Debug Console"), debug_console.show_console()],
    )
    settings_menu.add_command(
        label="Restart Application",
        command=lambda: [_log_action("Settings: Restart Application"), interface.restart_application()],
    )
    
    return top_frame, settings_menu
