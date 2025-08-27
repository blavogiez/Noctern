"""
This module is responsible for creating and managing the application's top bar,
which includes various action buttons and dropdown menus for functionalities
such as file operations, LaTeX compilation, LLM interactions, and application settings.
"""

import ttkbootstrap as ttk
from latex import compiler as latex_compiler
from llm import service as llm_service
from latex import translator as latex_translator
from app import interface, state
from utils import logs_console
from llm import rephrase as llm_rephrase
from editor import snippets as editor_snippets
from app import settings_window
from utils.animations import move_widget
from app.panels import show_metrics_panel, show_settings_panel

def _log_action(action_name):
    """Helper function to log user actions triggered from the UI elements."""
    logs_console.log(f"UI Action: User triggered '{action_name}'.", level='ACTION')

def create_top_buttons_frame(root):
    """
    Creates and populates the top bar frame with buttons and menus for application control.
    This version uses .place() for layout to allow for hover animations.
    """
    top_frame = ttk.Frame(root, height=65)
    top_frame.pack(fill="x", padx=0, pady=0)

    # --- Animation Constants ---
    Y_POS = 5
    Y_HOVER = 3
    BUTTON_PADDING = 8
    
    # --- Button Creation and Placement ---
    buttons = []
    
    # Helper to create, place, and bind a button
    def create_animated_button(text, command, bootstyle):
        original_style = bootstyle
        # Enhanced hover effect - removes outline and adds subtle emphasis
        if "outline" in bootstyle:
            hover_style = bootstyle.replace("-outline", "")
        else:
            # For solid buttons, lighten on hover
            hover_style = f"{bootstyle.split('-')[0]}-outline" if "-" in bootstyle else "secondary"

        button = ttk.Button(
            top_frame, 
            text=text, 
            command=command, 
            bootstyle=original_style,
            padding=(12, 8)
        )
            
        # Enhanced animations with smoother transitions
        def on_enter(e):
            move_widget(button, Y_HOVER)
            button.config(bootstyle=hover_style)
            
        def on_leave(e):
            move_widget(button, Y_POS)  
            button.config(bootstyle=original_style)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        # Add subtle focus styling
        button.bind("<FocusIn>", lambda e: button.config(bootstyle=hover_style))
        button.bind("<FocusOut>", lambda e: button.config(bootstyle=original_style))
        
        buttons.append(button)
        return button

    # File Operations
    create_animated_button("Open", lambda: [_log_action("Open File"), interface.open_file()], "primary-outline")
    create_animated_button("Save", lambda: [_log_action("Save File"), interface.save_file()], "primary-outline")
    create_animated_button("Save As", lambda: [_log_action("Save File As"), interface.save_file_as()], "primary-outline")
    
    # Add some spacing between groups
    spacer1 = ttk.Frame(top_frame, width=10)
    spacer1.place(x=0, y=0)
    buttons.append(spacer1)
    
    # LaTeX Processing
    create_animated_button("Compile", lambda: [_log_action("Compile LaTeX"), latex_compiler.compile_latex()], "info-outline")
    create_animated_button("View PDF", lambda: [_log_action("View PDF"), latex_compiler.view_pdf_external()], "info-outline")
    create_animated_button("Translate", lambda: [_log_action("Translate Text"), latex_translator.open_translate_panel()], "info-outline")

    # Add some spacing between groups
    spacer2 = ttk.Frame(top_frame, width=10)
    spacer2.place(x=0, y=0)
    buttons.append(spacer2)
    
    # LLM Interaction
    create_animated_button("Complete", lambda: [_log_action("LLM Complete Text"), llm_service.request_llm_to_complete_text()], "success-outline")
    create_animated_button("Generate", lambda: [_log_action("LLM Generate Text"), llm_service.open_generate_text_panel()], "success-outline")
    
    # Add some spacing between groups
    spacer3 = ttk.Frame(top_frame, width=10)
    spacer3.place(x=0, y=0)
    buttons.append(spacer3)
    
    # PDF Navigation
    create_animated_button("Go to line in PDF", lambda: [_log_action("Go to line in PDF"), interface.go_to_line_in_pdf()], "warning-outline")

    # Place buttons dynamically
    current_x = 5
    for button in buttons:
        # Skip spacers for width calculation but still place them
        if isinstance(button, ttk.Frame) and button.winfo_width() == 10:
            button.place(x=current_x, y=Y_POS)
            current_x += 10  # Fixed width for spacer
        else:
            button.place(x=current_x, y=Y_POS)
            # Update current_x for the next button, adding width and padding
            root.update_idletasks() # Ensures winfo_width() is accurate
            current_x += button.winfo_width() + BUTTON_PADDING

    # --- Menus (placed on the right) ---
    def create_animated_menubutton(text, bootstyle):
        original_style = bootstyle
        # Enhanced hover effect matching buttons
        if "outline" in bootstyle:
            hover_style = bootstyle.replace("-outline", "")
        else:
            hover_style = f"{bootstyle.split('-')[0]}-outline" if "-" in bootstyle else "secondary"

        menubutton = ttk.Menubutton(
            top_frame, 
            text=text, 
            bootstyle=original_style,
            padding=(12, 8)
        )
        
        # Enhanced animations matching buttons
        def on_enter(e):
            move_widget(menubutton, Y_HOVER)
            menubutton.config(bootstyle=hover_style)
            
        def on_leave(e):
            move_widget(menubutton, Y_POS)
            menubutton.config(bootstyle=original_style)
            
        menubutton.bind("<Enter>", on_enter)
        menubutton.bind("<Leave>", on_leave)
        
        # Add focus styling for keyboard navigation
        menubutton.bind("<FocusIn>", lambda e: menubutton.config(bootstyle=hover_style))
        menubutton.bind("<FocusOut>", lambda e: menubutton.config(bootstyle=original_style))
        
        return menubutton

    tools_menubutton = create_animated_menubutton("Tools", "secondary-outline")
    tools_menubutton.place(relx=1.0, x=-160, y=Y_POS, anchor="ne")
    tools_menu = ttk.Menu(tools_menubutton, tearoff=False)
    tools_menubutton["menu"] = tools_menu

    settings_menubutton = create_animated_menubutton("Settings", "secondary-outline")
    settings_menubutton.place(relx=1.0, x=-5, y=Y_POS, anchor="ne")
    settings_menu = ttk.Menu(settings_menubutton, tearoff=False)
    settings_menubutton["menu"] = settings_menu

    # --- Populate Menus ---
    tools_menu.add_command(label="Smart Style (Ctrl+Shift+S)...", command=lambda: [_log_action("Tools: Smart Style"), interface.style_selected_text()])
    tools_menu.add_separator()
    tools_menu.add_command(label="Rephrase Selected Text (Ctrl+R)", command=lambda: [_log_action("Tools: Rephrase Text"), interface.open_rephrase_panel()])
    tools_menu.add_command(label="Proofread Document (Ctrl+Shift+P)", command=lambda: [_log_action("Tools: Proofread Document"), llm_service.open_proofreading_panel()])
    tools_menu.add_command(label="Paste Image from Clipboard (Ctrl+Shift+V)", command=lambda: [_log_action("Tools: Paste Image"), interface.paste_image()])
    tools_menu.add_command(label="Insert Table (Ctrl+Shift+B)", command=lambda: [_log_action("Tools: Insert Table"), interface.insert_table()])
    tools_menu.add_separator()
    tools_menu.add_command(label="Clean Project Directory", command=lambda: [_log_action("Tools: Clean Project"), latex_compiler.clean_project_directory()])
    tools_menu.add_separator()
    tools_menu.add_command(label="Usage Metrics", command=lambda: [_log_action("Tools: Usage Metrics"), show_metrics_panel()])

    settings_menu.add_command(label="Preferences", command=lambda: [_log_action("Settings: Open Preferences"), show_settings_panel()])
    settings_menu.add_separator()
    
    theme_menu = ttk.Menu(settings_menu, tearoff=False)
    settings_menu.add_cascade(label="Theme", menu=theme_menu)
    
    def set_theme(theme_name):
        interface.apply_theme(theme_name)

    # Original theme
    theme_menu.add_command(label="Original", command=lambda: set_theme("original"))
    theme_menu.add_separator()
    
    # Light themes
    light_themes = [
        ("Cosmo", "cosmo"), ("Flatly", "flatly"), ("Litera", "litera"), 
        ("Minty", "minty"), ("Lumen", "lumen"), ("Sandstone", "sandstone"),
        ("Yeti", "yeti"), ("Pulse", "pulse"), ("United", "united"),
        ("Morph", "morph"), ("Journal", "journal"), ("Simplex", "simplex"), 
        ("Cerculean", "cerculean")
    ]
    
    for label, theme in light_themes:
        theme_menu.add_command(label=label, command=lambda t=theme: set_theme(t))
    
    theme_menu.add_separator()
    
    # Dark themes  
    dark_themes = [
        ("Darkly", "darkly"), ("Superhero", "superhero"), ("Solar", "solar"),
        ("Cyborg", "cyborg"), ("Vapor", "vapor")
    ]
    
    for label, theme in dark_themes:
        theme_menu.add_command(label=label, command=lambda t=theme: set_theme(t))
    
    settings_menu.add_separator()
    settings_menu.add_command(label="Edit LLM Keywords (per file)", command=lambda: [_log_action("Settings: Set LLM Keywords"), llm_service.open_set_keywords_panel()])
    settings_menu.add_command(label="Edit LLM Prompts (per file)", command=lambda: [_log_action("Settings: Edit LLM Prompts"), llm_service.open_edit_prompts_panel()])
    settings_menu.add_command(label="Edit Snippets (global)", command=lambda: [_log_action("Settings: Edit Snippets"), editor_snippets.open_snippet_editor(root, state.get_theme_settings())])
    settings_menu.add_separator()
    
    
    settings_menu.add_command(label="Show Debug Console", command=lambda: [_log_action("Settings: Show Debug Console"), logs_console.show_console()])
    settings_menu.add_command(label="Restart Application", command=lambda: [_log_action("Settings: Restart Application"), interface.restart_application()])
    
    # Add separator before UI visibility options
    return top_frame, settings_menu
