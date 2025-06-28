def show_temporary_status_message(message, duration_ms, status_bar, root, clear_func):
    global _temporary_status_active, _temporary_status_timer_id
    if not status_bar or not root:
        return
    if '_temporary_status_timer_id' in globals() and _temporary_status_timer_id:
        root.after_cancel(_temporary_status_timer_id)
    _temporary_status_active = True
    status_bar.config(text=message)
    _temporary_status_timer_id = root.after(duration_ms, clear_func)

def clear_temporary_status_message(status_bar, apply_theme, current_theme):
    global _temporary_status_active, _temporary_status_timer_id
    _temporary_status_active = False
    _temporary_status_timer_id = None
    if status_bar:
        apply_theme(current_theme)
