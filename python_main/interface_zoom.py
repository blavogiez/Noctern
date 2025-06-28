from tkinter.font import Font

def zoom_in(get_current_tab, perform_heavy_updates, min_font_size, max_font_size, zoom_factor):
    current_tab = get_current_tab()
    if not current_tab:
        return
    current_size = current_tab.editor_font.cget("size")
    new_size = int(current_size * zoom_factor)
    new_size = min(new_size, max_font_size)
    if new_size != current_size:
        current_tab.editor_font = Font(
            family=current_tab.editor_font.cget("family"),
            size=new_size,
            weight=current_tab.editor_font.cget("weight"),
            slant=current_tab.editor_font.cget("slant")
        )
        current_tab.editor.config(font=current_tab.editor_font)
        if current_tab.line_numbers:
            current_tab.line_numbers.font = current_tab.editor_font
            current_tab.line_numbers.redraw()
        perform_heavy_updates()

def zoom_out(get_current_tab, perform_heavy_updates, min_font_size, max_font_size, zoom_factor):
    current_tab = get_current_tab()
    if not current_tab:
        return
    current_size = current_tab.editor_font.cget("size")
    new_size = int(current_size / zoom_factor)
    new_size = max(new_size, min_font_size)
    if new_size != current_size:
        current_tab.editor_font = Font(
            family=current_tab.editor_font.cget("family"),
            size=new_size,
            weight=current_tab.editor_font.cget("weight"),
            slant=current_tab.editor_font.cget("slant")
        )
        current_tab.editor.config(font=current_tab.editor_font)
        if current_tab.line_numbers:
            current_tab.line_numbers.font = current_tab.editor_font
            current_tab.line_numbers.redraw()
        perform_heavy_updates()
