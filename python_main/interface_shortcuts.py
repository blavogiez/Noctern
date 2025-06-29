import latex_compiler
import llm_service
import latex_translator
import editor_logic
import interface
import llm_rephrase

def bind_shortcuts(root):
    root.bind_all("<Control-Shift-G>", lambda event: llm_service.open_generate_text_dialog())
    root.bind_all("<Control-Shift-C>", lambda event: llm_service.request_llm_to_complete_text())
    root.bind_all("<Control-Shift-D>", lambda event: latex_compiler.run_chktex_check())
    root.bind_all("<Control-Shift-V>", lambda event: editor_logic.paste_image())
    root.bind_all("<Control-Shift-K>", lambda event: llm_service.open_set_keywords_dialog())
    root.bind_all("<Control-Shift-P>", lambda event: llm_service.open_edit_prompts_dialog())
    root.bind_all("<Control-o>", lambda event: interface.open_file())
    root.bind_all("<Control-s>", lambda event: interface.save_file())
    root.bind_all("<Control-w>", lambda event: interface.close_current_tab())
    root.bind_all("<Control-t>", lambda event: latex_translator.open_translate_dialog())
    root.bind_all("<Control-equal>", interface.zoom_in)
    root.bind_all("<Control-minus>", interface.zoom_out)
    root.bind_all("<Control-r>", lambda event: llm_rephrase.open_rephrase_dialog())
