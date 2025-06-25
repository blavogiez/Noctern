import tkinter as tk
import platform
from tkinter import ttk # Import ttk module
import ctypes

# Import modules for different functionalities
import editor_logic
import latex_compiler # Handles LaTeX compilation and chktex checks
import latex_translator # Manages translation functionality
import llm_service # Orchestrates all LLM-related operations

# Import newly fragmented GUI modules
import gui_main_window
import gui_file_tab_manager
import gui_theme_manager
import gui_status_bar
import gui_editor_view

if __name__ == "__main__":
    # Improve rendering on HiDPI screens under Windows
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception as e:
            print(f"Note: Could not set DPI awareness - {e}")

    # Setup the main GUI window and widgets
    # This function returns a dictionary of all created core GUI components.
    gui_components = gui_main_window.setup_gui()
    root = gui_components["root"]
    top_frame = gui_components["top_frame"]
    main_pane = gui_components["main_pane"]
    outline_tree = gui_components["outline_tree"]
    notebook = gui_components["notebook"]
    welcome_screen = gui_components["welcome_screen"]
    welcome_button_frame = gui_components["welcome_button_frame"] # Frame to add welcome screen buttons
    llm_progress_bar = gui_components["llm_progress_bar"]
    status_bar = gui_components["status_bar"]
    tabs_dict = gui_components["tabs_dict"] # The global dictionary to hold EditorTab instances

    # --- Initialize Services ---
    # Initialize GUI sub-modules first, as other services depend on them.
    # The order of initialization below is important due to inter-module dependencies.

    # 1. Initialize Status Bar Manager: Needs root and status_bar widget.
    gui_status_bar.initialize(root_ref=root, status_bar_ref=status_bar)

    # 2. Initialize Editor Logic: Needs outline_tree and a way to get the current tab.
    #    The get_current_tab function will be provided by gui_file_tab_manager once it's initialized.
    editor_logic.initialize_editor_logic(outline_tree, lambda: gui_file_tab_manager.get_current_tab())

    # 3. Initialize Editor View Manager: Needs root, a way to get current tab, outline_tree, and editor_logic module.
    gui_editor_view.initialize(
        root_ref=root,
        get_current_tab_cb=lambda: gui_file_tab_manager.get_current_tab(), # Callback to get the active tab
        outline_tree_ref=outline_tree,
        editor_logic_module=editor_logic # Pass the editor_logic module for heavy updates
    )

    # 4. Initialize File/Tab Manager: Needs references to notebook, tabs dictionary, welcome screen, root,
    #    and callbacks for tab changes and heavy updates.
    gui_file_tab_manager.initialize(
        notebook_ref=notebook,
        tabs_dict_ref=tabs_dict,
        welcome_screen_ref=welcome_screen,
        root_ref=root,
        # Callback for when a tab changes: loads LLM history/prompts and schedules heavy UI updates.
        on_tab_changed_cb=lambda: (llm_service.load_prompt_history_for_current_file(),
                                   llm_service.load_generation_history_for_current_file(), # NEW
                                   llm_service.load_keywords_for_current_file(), # NEW: Load keywords on tab change
                                   llm_service.load_prompts_for_current_file(),
                                   gui_editor_view.perform_heavy_updates()),
        schedule_heavy_updates_cb=gui_editor_view.schedule_heavy_updates, # Callback for scheduling heavy updates
        welcome_button_frame_ref=welcome_button_frame, # Frame to add buttons to welcome screen
        # NEW: Pass a callback to re-apply the current theme when a new tab is created.
        # This ensures new widgets get the correct theme colors.
        apply_theme_cb=lambda: gui_theme_manager.apply_theme(gui_theme_manager._current_theme)
    )

    # 5. Initialize Theme Manager: Needs root, the tabs dictionary, and a callback for heavy updates.
    gui_theme_manager.initialize(
        root_ref=root,
        tabs_dict_ref=tabs_dict, # Pass the tabs dictionary directly for theme application
        perform_heavy_updates_cb=gui_editor_view.perform_heavy_updates # Callback to re-apply syntax highlighting etc.
    )

    # Initialize other core application services
    latex_compiler.initialize_compiler(root, lambda: gui_file_tab_manager.get_current_tab())

    # LLM Service initialization: Needs various GUI component references and callbacks.
    llm_service.initialize_llm_service(
        root_window_ref=root,
        progress_bar_widget_ref=llm_progress_bar,
        theme_setting_getter_func=gui_theme_manager.get_theme_setting,
        active_editor_getter=lambda: gui_file_tab_manager.get_current_tab().editor if gui_file_tab_manager.get_current_tab() else None, # Pass getter for active editor
        active_filepath_getter=lambda: gui_file_tab_manager.get_current_tab().file_path if gui_file_tab_manager.get_current_tab() else None, # Pass getter for active file path
        show_temporary_status_message_func=gui_status_bar.show_temporary_status_message # Pass status message func
    )

    # LaTeX Translator initialization: Needs various GUI component references and callbacks.
    latex_translator.initialize_translator(
        root_ref=root,
        theme_getter=gui_theme_manager.get_theme_setting,
        status_message_func=gui_status_bar.show_temporary_status_message,
        active_editor_getter=lambda: gui_file_tab_manager.get_current_tab().editor if gui_file_tab_manager.get_current_tab() else None,
        active_filepath_getter=lambda: gui_file_tab_manager.get_current_tab().file_path if gui_file_tab_manager.get_current_tab() else None
    )





    # --- Setup UI Buttons (Top Frame) ---
    ttk.Button(top_frame, text="📂 Open", command=lambda: gui_file_tab_manager.open_file(gui_status_bar.show_temporary_status_message)).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="💾 Save", command=lambda: gui_file_tab_manager.save_file(gui_status_bar.show_temporary_status_message)).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="💾 Save As", command=lambda: gui_file_tab_manager.save_file_as(gui_status_bar.show_temporary_status_message)).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🛠 Compile", command=latex_compiler.compile_latex).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🔍 Check", command=latex_compiler.run_chktex_check).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="✨ Complete", command=llm_service.request_llm_to_complete_text).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🎯 Generate", command=llm_service.open_generate_text_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🔑 Keywords", command=llm_service.open_set_keywords_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="📝 Prompts", command=llm_service.open_edit_prompts_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🌐 Translate", command=latex_translator.open_translate_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🌓 Theme", command=lambda: gui_theme_manager.apply_theme("dark" if gui_theme_manager._current_theme == "light" else "light")).pack(side="right", padx=3, pady=3)

    # --- Bind Keyboard Shortcuts (Application-wide) ---
    root.bind_all("<Control-Shift-G>", lambda event: llm_service.open_generate_text_dialog())
    root.bind_all("<Control-Shift-C>", lambda event: llm_service.request_llm_to_complete_text())
    root.bind_all("<Control-Shift-D>", lambda event: latex_compiler.run_chktex_check())
    root.bind_all("<Control-Shift-V>", lambda event: editor_logic.paste_image())
    root.bind_all("<Control-Shift-K>", lambda event: llm_service.open_set_keywords_dialog())
    root.bind_all("<Control-Shift-P>", lambda event: llm_service.open_edit_prompts_dialog())
    root.bind_all("<Control-o>", lambda event: gui_file_tab_manager.open_file(gui_status_bar.show_temporary_status_message))
    root.bind_all("<Control-n>", lambda event: gui_file_tab_manager.create_new_tab(file_path=None))
    root.bind_all("<Control-s>", lambda event: gui_file_tab_manager.save_file(gui_status_bar.show_temporary_status_message))
    root.bind_all("<Control-w>", lambda event: gui_file_tab_manager.close_current_tab())
    root.bind_all("<Control-t>", lambda event: latex_translator.open_translate_dialog())
    root.bind_all("<Control-equal>", gui_editor_view.zoom_in)
    root.bind_all("<Control-minus>", gui_editor_view.zoom_out)

    # Intercept the window close ('X') button to check for unsaved changes
    root.protocol("WM_DELETE_WINDOW", lambda: gui_main_window.on_close_request(
        gui_file_tab_manager.get_current_tab, # Pass getter for current tab
        lambda: gui_file_tab_manager.save_file(gui_status_bar.show_temporary_status_message), # Pass save function
        root,
        tabs_dict # Pass the tabs dictionary
    ))

    # Bind outline tree selection after gui_file_tab_manager is ready
    outline_tree.bind("<<TreeviewSelect>>", lambda event: editor_logic.go_to_section(gui_file_tab_manager.get_current_tab().editor if gui_file_tab_manager.get_current_tab() else None, event))

    # Show the welcome screen initially, as no tabs are open
    gui_file_tab_manager.toggle_welcome_screen()

    # Apply the initial theme (e.g., dark mode by default)
    gui_theme_manager.apply_theme("dark")

    # Start the GPU status update loop
    gui_status_bar.update_gpu_status()

    # Initial call to ensure everything is drawn correctly after the window is visible.
    root.after(100, gui_editor_view.perform_heavy_updates)

    # Start the Tkinter event loop
    root.mainloop()
