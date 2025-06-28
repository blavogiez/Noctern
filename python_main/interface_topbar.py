from tkinter import ttk
import latex_compiler
import llm_service
import latex_translator
import interface

def create_top_buttons_frame(root):
    top_frame = ttk.Frame(root, padding=10)
    top_frame.pack(fill="x", pady=(0, 5))
    ttk.Button(top_frame, text="📂 Open", command=interface.open_file).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="💾 Save", command=interface.save_file).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="💾 Save As", command=interface.save_file_as).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🛠 Compile", command=latex_compiler.compile_latex).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🔍 Check", command=latex_compiler.run_chktex_check).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="✨ Complete", command=llm_service.request_llm_to_complete_text).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🎯 Generate", command=llm_service.open_generate_text_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🔑 Keywords", command=llm_service.open_set_keywords_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="📝 Prompts", command=llm_service.open_edit_prompts_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🌐 Translate", command=latex_translator.open_translate_dialog).pack(side="left", padx=3, pady=3)
    ttk.Button(top_frame, text="🌓 Theme", command=lambda: interface.apply_theme("dark" if interface.current_theme == "light" else "light")).pack(side="right", padx=3, pady=3)
    return top_frame
