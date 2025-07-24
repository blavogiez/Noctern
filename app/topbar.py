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
from utils.animations import move_widget

def _log_action(action_name):
    """Helper function to log user actions triggered from the UI elements."""
    debug_console.log(f"UI Action: User triggered '{action_name}'.", level='ACTION')

def create_top_buttons_frame(root):
    """
    Creates and populates the top bar frame with buttons and menus for application control.
    This version uses .place() for layout to allow for hover animations.
    """
    top_frame = ttk.Frame(root, height=45)
    top_frame.pack(fill="x", padx=5, pady=(5,0))

    # --- Animation Constants ---
    Y_POS = 5
    Y_HOVER = 2
    
    # --- Button Creation and Placement ---
    buttons = []
    
    # Helper to create, place, and bind a button
    def create_animated_button(text, command, bootstyle):
        button = ttk.Button(top_frame, text=text, command=command, bootstyle=bootstyle)
        button.bind("<Enter>", lambda e, w=button: move_widget(w, Y_HOVER))
        button.bind("<Leave>", lambda e, w=button: move_widget(w, Y_POS))
        buttons.append(button)
        return button

    # File Operations
    create_animated_button("📂 Open", lambda: [_log_action("Open File"), interface.open_file()], "primary-outline")
    create_animated_button("💾 Save", lambda: [_log_action("Save File"), interface.save_file()], "primary-outline")
    create_animated_button("💾 Save As", lambda: [_log_action("Save File As"), interface.save_file_as()], "primary-outline")
    
    # LaTeX Processing
    create_animated_button("🛠 Compile", lambda: [_log_action("Compile LaTeX"), latex_compiler.compile_latex()], "info-outline")
    create_animated_button("📄 View PDF", lambda: [_log_action("View PDF"), latex_compiler.view_pdf_external()], "info-outline")
    create_animated_button("🌐 Translate", lambda: [_log_action("Translate Text"), latex_translator.open_translate_dialog()], "info-outline")

    # LLM Interaction
    create_animated_button("✨ Complete", lambda: [_log_action("LLM Complete Text"), llm_service.request_llm_to_complete_text()], "success-outline")
    create_animated_button("🎯 Generate", lambda: [_log_action("LLM Generate Text"), llm_service.open_generate_text_dialog()], "success-outline")

    # Place buttons dynamically
    current_x = 5
    for button in buttons:
        button.place(x=current_x, y=Y_POS)
        # Update current_x for the next button, adding width and padding
        root.update_idletasks() # Ensures winfo_width() is accurate
        current_x += button.winfo_width() + 5

    # --- Menus (placed on the right) ---
    tools_menubutton = ttk.Menubutton(top_frame, text="🔧 Tools", bootstyle="secondary-outline")
    tools_menubutton.place(relx=1.0, x=-180, y=Y_POS, anchor="ne")
    tools_menubutton.bind("<Enter>", lambda e, w=tools_menubutton: move_widget(w, Y_HOVER))
    tools_menubutton.bind("<Leave>", lambda e, w=tools_menubutton: move_widget(w, Y_POS))
    tools_menu = ttk.Menu(tools_menubutton, tearoff=False)
    tools_menubutton["menu"] = tools_menu

    settings_menubutton = ttk.Menubutton(top_frame, text="⚙️ Settings", bootstyle="secondary-outline")
    settings_menubutton.place(relx=1.0, x=-5, y=Y_POS, anchor="ne")
    settings_menubutton.bind("<Enter>", lambda e, w=settings_menubutton: move_widget(w, Y_HOVER))
    settings_menubutton.bind("<Leave>", lambda e, w=settings_menubutton: move_widget(w, Y_POS))
    settings_menu = ttk.Menu(settings_menubutton, tearoff=False)
    settings_menubutton["menu"] = settings_menu

    # --- Populate Menus ---
    tools_menu.add_command(label="Check Document (chktex)", command=lambda: [_log_action("Tools: chktex Check"), latex_compiler.run_chktex_check()])
    tools_menu.add_command(label="Rephrase Selected Text (Ctrl+R)", command=lambda: [_log_action("Tools: Rephrase Text"), llm_rephrase.open_rephrase_dialog()])
    tools_menu.add_command(label="Paste Image from Clipboard (Ctrl+Shift+V)", command=lambda: [_log_action("Tools: Paste Image"), interface.paste_image()])
    tools_menu.add_separator()
    tools_menu.add_command(label="Clean Project Directory", command=lambda: [_log_action("Tools: Clean Project"), latex_compiler.clean_project_directory()])

    settings_menu.add_command(label="Preferences...", command=lambda: [_log_action("Settings: Open Preferences"), settings_window.open_settings_window(root)])
    settings_menu.add_separator()
    
    theme_menu = ttk.Menu(settings_menu, tearoff=False)
    settings_menu.add_cascade(label="Theme", menu=theme_menu)
    
    def set_theme(theme_name):
        interface.apply_theme(theme_name)

    theme_menu.add_command(label="Original", command=lambda: set_theme("original"))
    theme_menu.add_separator()
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
    
    settings_menu.add_checkbutton(label="Auto-open PDF on .tex load", variable=interface._auto_open_pdf_var, command=interface.toggle_auto_open_pdf)
    settings_menu.add_command(label="Show Debug Console", command=lambda: [_log_action("Settings: Show Debug Console"), debug_console.show_console()])
    settings_menu.add_command(label="Restart Application", command=lambda: [_log_action("Settings: Restart Application"), interface.restart_application()])
    
    return top_frame, settings_menu
