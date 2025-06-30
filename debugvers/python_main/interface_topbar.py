from tkinter import ttk, Menu
import latex_compiler
import llm_service
import latex_translator
import interface
import debug_console
import llm_rephrase

def _log_action(action_name):
    """Helper function to log user actions."""
    debug_console.log(f"UI: User triggered '{action_name}'.", level='ACTION')

def create_top_buttons_frame(root):
    top_frame = ttk.Frame(root, padding=10)
    top_frame.pack(fill="x", pady=(0, 5))

    # --- Standard Action Buttons ---
    ttk.Button(top_frame, text="📂 Open", command=lambda: [_log_action("Open File"), interface.open_file()]).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="💾 Save", command=lambda: [_log_action("Save File"), interface.save_file()]).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="💾 Save As", command=lambda: [_log_action("Save File As"), interface.save_file_as()]).pack(side="left", padx=3, pady=3)
    
    ttk.Separator(top_frame, orient='vertical').pack(side='left', padx=5, fill='y')

    # --- Document Processing Buttons ---
    ttk.Button(top_frame, text="🛠 Compile", command=lambda: [_log_action("Compile"), latex_compiler.compile_latex()]).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🌐 Translate", command=lambda: [_log_action("Translate"), latex_translator.open_translate_dialog()]).pack(side="left", padx=3, pady=3)

    ttk.Separator(top_frame, orient='vertical').pack(side='left', padx=5, fill='y')

    # --- LLM Buttons ---
    ttk.Button(top_frame, text="✨ Complete", command=lambda: [_log_action("LLM Complete"), llm_service.request_llm_to_complete_text()]).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🎯 Generate", command=lambda: [_log_action("LLM Generate"), llm_service.open_generate_text_dialog()]).pack(side="left", padx=3, pady=3)
    
    # --- Theme Button (moved to the right) ---
    ttk.Button(top_frame, text="🌓 Theme", command=lambda: [_log_action("Toggle Theme"), interface.apply_theme("dark" if interface.current_theme == "light" else "light")]).pack(side="right", padx=3, pady=3)

    # --- Settings Menu Button (Cleaned up) ---
    settings_menubutton = ttk.Menubutton(top_frame, text="⚙️ Settings")
    settings_menubutton.pack(side="right", padx=3, pady=3)
    settings_menu = Menu(settings_menubutton, tearoff=0)
    settings_menubutton["menu"] = settings_menu
    
    # --- Tools Menu Button ---
    tools_menubutton = ttk.Menubutton(top_frame, text="🔧 Tools")
    tools_menubutton.pack(side="right", padx=3, pady=3)
    tools_menu = Menu(tools_menubutton, tearoff=0)
    tools_menubutton["menu"] = tools_menu

    # --- Populate Tools Menu ---
    tools_menu.add_command(label="Check Document (chktex)", command=lambda: [_log_action("Tools: chktex"), latex_compiler.run_chktex_check()])
    tools_menu.add_command(label="Rephrase Selected Text (Ctrl+R)", command=lambda: [_log_action("Tools: Rephrase"), llm_rephrase.open_rephrase_dialog()])
    tools_menu.add_command(label="Paste Image from Clipboard (Ctrl+Shift+V)", command=lambda: [_log_action("Tools: Paste Image"), interface.paste_image()])

    # --- Populate Settings Menu (Now more logical) ---
    settings_menu.add_command(label="Set LLM Keywords...", command=lambda: [_log_action("Settings: Set Keywords"), llm_service.open_set_keywords_dialog()])
    settings_menu.add_command(label="Edit LLM Prompts...", command=lambda: [_log_action("Settings: Edit Prompts"), llm_service.open_edit_prompts_dialog()])
    settings_menu.add_separator()
    settings_menu.add_checkbutton(
        label="Advanced Mode",
        variable=interface._advanced_mode_enabled,
        command=interface.toggle_advanced_mode # Logging is inside the function
    )
    settings_menu.add_command(
        label="Show Debug Console",
        command=lambda: [_log_action("Settings: Show Debug Console"), debug_console.show_console()],
        state="disabled"
    )
    
    return top_frame, settings_menu